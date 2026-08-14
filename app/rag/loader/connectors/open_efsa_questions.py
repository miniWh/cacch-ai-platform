"""Open EFSA Questions 连接器：列表 + 详情 + 附件落盘。

该站前端为 SPA；列表来自 ``searchAdvanced``，详情来自 ``question/get``，
附件经 ``study/getEvidence`` POST 下载。请求头需动态 ``x-security``。
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

import httpx

from app.rag.loader.persist import (
    SavedFile,
    SavedPage,
    content_digest,
    safe_filename_from_url,
    write_bytes,
    write_text,
)
from app.web.config import Settings

_HOST = "open.efsa.europa.eu"
_API_BASE = "https://open.efsa.europa.eu/api"
_API_SEARCH = f"{_API_BASE}/question/searchAdvanced"
_API_GET = f"{_API_BASE}/question/get"
_API_TIMELINE = f"{_API_BASE}/question/getTimeline"
_API_STUDY_PREVIEW = f"{_API_BASE}/study/getStudyPreviewForQuestion"
_API_EVIDENCE = f"{_API_BASE}/study/getEvidence"
_TAG_RE = re.compile(r"<[^>]+>")


def matches_open_efsa_questions(entry_url: str | None) -> bool:
    """入口 URL 是否指向 Open EFSA Questions（含详情路径前缀）。"""
    if not entry_url:
        return False
    parsed = urlparse(entry_url)
    host = (parsed.hostname or "").lower()
    if host != _HOST:
        return False
    path = (parsed.path or "/").rstrip("/") or "/"
    return path == "/questions" or path.startswith("/questions/")


def x_security_token(*, now_ts: float | None = None) -> str:
    """与前端一致：``123 * floor(unix_sec) + 369``。"""
    ts = int(now_ts if now_ts is not None else time.time())
    return str(123 * ts + 369)


def _strip_html(value: str | None) -> str:
    if not value:
        return ""
    return _TAG_RE.sub("", value).strip()


def _api_headers(referer: str) -> dict[str, str]:
    return {
        "Accept": "application/json",
        "Referer": referer,
        "x-security": x_security_token(),
    }


def _format_list_question(item: dict) -> str:
    """列表摘要文本。"""
    lines = [
        f"questionNumber: {item.get('questionNumber') or ''}",
        f"foodDomain: {item.get('foodDomainDescription') or ''}",
        f"phase: {item.get('phaseName') or ''}",
        f"type: {item.get('questionTypeDescription') or ''}",
        f"authorisation: {item.get('authorisationTypeDescription') or ''}",
        f"mandate: {item.get('mandateNumber') or ''}",
        f"output: {item.get('outputNumber') or ''}",
        f"lastModified: {item.get('lastModifiedDate') or ''}",
        f"subject: {_strip_html(item.get('subject'))}",
    ]
    substances = item.get("substanceNames") or []
    if substances:
        lines.append("substances: " + "; ".join(str(s) for s in substances))
    applicants = item.get("applicantNames") or []
    if applicants:
        lines.append("applicants: " + "; ".join(str(a) for a in applicants))
    return "\n".join(lines)


def _format_detail(detail: dict, timeline: list | None, studies: list | None) -> str:
    """详情页可读文本（含 dossier / 法规 / 附件元数据）。"""
    output = detail.get("output") or {}
    comment = detail.get("comment") or {}
    out_no = (output.get("outputNumber") if output else None) or detail.get(
        "outputNumber"
    )
    lines = [
        f"questionNumber: {detail.get('questionNumber') or ''}",
        f"subject: {_strip_html(detail.get('subject'))}",
        f"foodDomain: {detail.get('foodDomainDescription') or ''}",
        f"phase: {detail.get('phaseName') or ''}",
        f"dossierNumber: {detail.get('dossierNumber') or ''}",
        f"mandateNumber: {detail.get('mandateNumber') or ''}",
        f"regulation: {detail.get('regulationName') or ''}",
        f"applicationType: {detail.get('applicationTypeDescription') or ''}",
        f"questionType: {detail.get('processTypeDescription') or ''}",
        f"authorisation: {detail.get('authorisationTypeDescription') or ''}",
        f"outputNumber: {out_no or ''}",
        f"outputType: {(output.get('type') if output else None) or ''}",
        "outputPublicationDate: "
        f"{(output.get('publicationDate') if output else None) or ''}",
        "outputLink: "
        f"{(output.get('linkToPublisherOutput') if output else None) or ''}",
        f"comment: {_strip_html(comment.get('comment') if comment else None)}",
        "commentPublished: "
        f"{(comment.get('lastModifiedOn') if comment else None) or ''}",
    ]
    substances = detail.get("substances") or []
    if isinstance(substances, list) and substances:
        names = []
        for s in substances:
            if isinstance(s, dict):
                names.append(
                    f"{s.get('termExtendedName') or ''} (CAS {s.get('cas') or ''})"
                )
        if names:
            lines.append("substances: " + "; ".join(names))
    applicants = detail.get("questionApplicants") or []
    if isinstance(applicants, list) and applicants:
        names = [
            str(a.get("organisationName"))
            for a in applicants
            if isinstance(a, dict) and a.get("organisationName")
        ]
        if names:
            lines.append("applicants: " + "; ".join(names))

    if timeline:
        lines.append("timeline:")
        for item in timeline:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"  - {item.get('dateDisplay') or item.get('date') or ''}: "
                f"{item.get('title') or ''}"
            )

    if studies:
        lines.append("supportingDocuments:")
        for doc in studies:
            if not isinstance(doc, dict):
                continue
            lines.append(
                f"  - {doc.get('title') or doc.get('fileName') or ''} | "
                f"{doc.get('fileName') or ''} | "
                f"published={doc.get('publishedDate') or ''}"
            )
    return "\n".join(lines)


@dataclass
class OpenEfsaSyncResult:
    """连接器同步结果。"""

    pages: list[SavedPage]
    files: list[SavedFile] = field(default_factory=list)
    question_count: int = 0
    detail_count: int = 0
    ok: bool = False
    error: str | None = None


def _get_json(
    http: httpx.Client,
    url: str,
    *,
    params: dict | None,
    referer: str,
    max_bytes: int,
) -> tuple[httpx.Response | None, dict | list | None, str | None]:
    try:
        response = http.get(url, params=params, headers=_api_headers(referer))
    except httpx.HTTPError as exc:
        return None, None, f"error:{exc.__class__.__name__}:{exc}"
    raw = response.content[:max_bytes]
    if not (200 <= response.status_code < 400) or not raw:
        return response, None, f"http_{response.status_code}_or_empty"
    try:
        payload = json.loads(raw.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return response, None, "invalid_json"
    return response, payload.get("data"), None


def _download_evidence(
    *,
    http: httpx.Client,
    run_dir: Path,
    question_number: str,
    doc: dict,
    max_bytes: int,
) -> SavedFile:
    file_key = str(doc.get("fileId") or doc.get("id") or "")
    path = str(doc.get("pathToFile") or "")
    file_name = str(doc.get("fileName") or f"{file_key}.bin")
    url = f"{_API_EVIDENCE}?questionNumber={question_number}&fileKey={file_key}"
    if not file_key:
        return SavedFile(
            url=url,
            path=None,
            bytes=0,
            content_type=None,
            status_code=None,
            ok=False,
            error="missing_file_key",
        )

    headers = {
        **_api_headers(f"https://open.efsa.europa.eu/questions/{question_number}"),
        "Content-Type": "application/json",
        "Accept": "application/octet-stream,*/*",
    }
    payload = {
        "isAdditionalEvidence": bool(doc.get("isAdditionalEvidence")),
        "questionNumber": question_number,
        "fileKey": file_key,
        "path": path,
    }
    try:
        response = http.post(_API_EVIDENCE, headers=headers, json=payload)
    except httpx.HTTPError as exc:
        return SavedFile(
            url=url,
            path=None,
            bytes=0,
            content_type=None,
            status_code=None,
            ok=False,
            error=f"error:{exc.__class__.__name__}:{exc}",
        )

    body = response.content[:max_bytes]
    if not (200 <= response.status_code < 400) or not body:
        return SavedFile(
            url=url,
            path=None,
            bytes=0,
            content_type=response.headers.get("content-type"),
            status_code=response.status_code,
            ok=False,
            error=f"http_{response.status_code}_or_empty",
        )

    safe = safe_filename_from_url(file_name, default="evidence.pdf")
    out_name = f"{content_digest(body)}_{question_number}_{safe}"
    out_path = run_dir / "files" / out_name
    write_bytes(out_path, body)
    rel = str(out_path.relative_to(run_dir)).replace("\\", "/")
    return SavedFile(
        url=url,
        path=rel,
        bytes=len(body),
        content_type=response.headers.get("content-type"),
        status_code=response.status_code,
        ok=True,
        error=None,
    )


def sync_open_efsa_questions(
    *,
    run_dir: Path,
    settings: Settings,
    client: httpx.Client | None = None,
) -> OpenEfsaSyncResult:
    """
    拉取 Questions 列表，并按配置抓取详情与附件，写入本地目录。

    不写业务库 / 向量库。
    """
    page_size = max(1, min(100, settings.crawl_open_efsa_page_size))
    max_pages = max(1, settings.crawl_open_efsa_max_pages)
    fetch_details = settings.crawl_open_efsa_fetch_details
    max_details = max(0, settings.crawl_open_efsa_max_details)
    download_files = settings.crawl_open_efsa_download_files
    max_bytes = settings.fetch_max_bytes

    owns_client = client is None
    http = client or httpx.Client(
        timeout=settings.fetch_timeout_seconds,
        follow_redirects=True,
        headers={"User-Agent": settings.fetch_user_agent},
    )

    pages: list[SavedPage] = []
    files: list[SavedFile] = []
    list_questions: list[dict] = []
    total_questions = 0
    detail_count = 0
    error: str | None = None

    try:
        # --- 列表 ---
        for page_index in range(max_pages):
            offset = page_index * page_size
            response, data, err = _get_json(
                http,
                _API_SEARCH,
                params={"offset": offset, "limit": page_size},
                referer="https://open.efsa.europa.eu/questions",
                max_bytes=max_bytes,
            )
            api_url = (
                str(response.url)
                if response is not None
                else f"{_API_SEARCH}?offset={offset}&limit={page_size}"
            )
            if err or response is None:
                error = err or "no_response"
                pages.append(
                    SavedPage(
                        url=api_url,
                        html_path=None,
                        text_path=None,
                        title=None,
                        text_length=0,
                        status_code=getattr(response, "status_code", None),
                        ok=False,
                        error=error,
                    )
                )
                break

            questions = []
            if isinstance(data, dict):
                questions = data.get("questions") or []
            if not isinstance(questions, list):
                questions = []

            raw = response.content[:max_bytes]
            stem = f"{page_index:03d}_api_searchAdvanced_{offset}"
            json_path = run_dir / "pages" / f"{stem}.json"
            txt_path = run_dir / "pages" / f"{stem}.txt"
            write_bytes(json_path, raw)
            blocks = [
                _format_list_question(q) for q in questions if isinstance(q, dict)
            ]
            text = (
                f"# Open EFSA Questions offset={offset} limit={page_size} "
                f"count={len(blocks)}\n\n" + "\n\n---\n\n".join(blocks)
            )
            write_text(txt_path, text)
            total_questions += len(blocks)
            for q in questions:
                if isinstance(q, dict) and q.get("questionNumber"):
                    list_questions.append(q)
            pages.append(
                SavedPage(
                    url=api_url,
                    html_path=str(json_path.relative_to(run_dir)).replace("\\", "/"),
                    text_path=str(txt_path.relative_to(run_dir)).replace("\\", "/"),
                    title=f"Open EFSA Questions offset={offset}",
                    text_length=len(text),
                    status_code=response.status_code,
                    ok=True,
                    error=None,
                )
            )
            if len(questions) < page_size:
                break
            time.sleep(0.2)

        # --- 详情 ---
        if fetch_details and max_details > 0 and list_questions:
            seen: set[str] = set()
            for item in list_questions:
                if detail_count >= max_details:
                    break
                qid = str(item.get("questionNumber") or "").strip()
                if not qid or qid in seen:
                    continue
                seen.add(qid)
                referer = f"https://open.efsa.europa.eu/questions/{qid}"
                time.sleep(0.15)

                detail_resp, detail_data, detail_err = _get_json(
                    http,
                    _API_GET,
                    params={"questionNumber": qid},
                    referer=referer,
                    max_bytes=max_bytes,
                )
                detail_url = (
                    str(detail_resp.url)
                    if detail_resp is not None
                    else f"{_API_GET}?questionNumber={qid}"
                )
                if detail_err or not isinstance(detail_data, dict):
                    pages.append(
                        SavedPage(
                            url=detail_url,
                            html_path=None,
                            text_path=None,
                            title=qid,
                            text_length=0,
                            status_code=getattr(detail_resp, "status_code", None),
                            ok=False,
                            error=detail_err or "empty_detail",
                        )
                    )
                    continue

                _, timeline_data, _ = _get_json(
                    http,
                    _API_TIMELINE,
                    params={"questionNumber": qid},
                    referer=referer,
                    max_bytes=max_bytes,
                )
                timeline = timeline_data if isinstance(timeline_data, list) else []

                _, study_data, _ = _get_json(
                    http,
                    _API_STUDY_PREVIEW,
                    params={"questionNumber": qid},
                    referer=referer,
                    max_bytes=max_bytes,
                )
                studies = study_data if isinstance(study_data, list) else []

                bundle = {
                    "questionNumber": qid,
                    "detail": detail_data,
                    "timeline": timeline,
                    "supportingDocuments": studies,
                    "listSummary": item,
                }
                stem = f"detail_{qid}"
                json_path = run_dir / "pages" / "details" / f"{stem}.json"
                txt_path = run_dir / "pages" / "details" / f"{stem}.txt"
                raw_json = json.dumps(bundle, ensure_ascii=False, indent=2).encode(
                    "utf-8"
                )
                write_bytes(json_path, raw_json)
                text = _format_detail(detail_data, timeline, studies)
                write_text(txt_path, text)
                pages.append(
                    SavedPage(
                        url=detail_url,
                        html_path=str(json_path.relative_to(run_dir)).replace(
                            "\\", "/"
                        ),
                        text_path=str(txt_path.relative_to(run_dir)).replace("\\", "/"),
                        title=qid,
                        text_length=len(text),
                        status_code=getattr(detail_resp, "status_code", None),
                        ok=True,
                        error=None,
                    )
                )
                detail_count += 1

                if download_files and studies:
                    for doc in studies:
                        if not isinstance(doc, dict):
                            continue
                        time.sleep(0.1)
                        files.append(
                            _download_evidence(
                                http=http,
                                run_dir=run_dir,
                                question_number=qid,
                                doc=doc,
                                max_bytes=max_bytes,
                            )
                        )
    finally:
        if owns_client:
            http.close()

    ok = total_questions > 0 and any(p.ok for p in pages)
    if not ok and error is None:
        error = "empty_crawl"
    return OpenEfsaSyncResult(
        pages=pages,
        files=files,
        question_count=total_questions,
        detail_count=detail_count,
        ok=ok,
        error=error,
    )
