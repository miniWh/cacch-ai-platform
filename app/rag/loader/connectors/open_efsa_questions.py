"""Open EFSA Questions 连接器：经官方 JSON API 拉列表并落盘。

该站前端为 SPA，``https://open.efsa.europa.eu/questions`` 的 HTML 几乎无正文；
真实数据来自 ``/api/question/searchAdvanced``，请求头需动态 ``x-security``。
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import httpx

from app.rag.loader.persist import SavedPage, write_bytes, write_text
from app.web.config import Settings

_HOST = "open.efsa.europa.eu"
_API_SEARCH = "https://open.efsa.europa.eu/api/question/searchAdvanced"
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


def _format_question(item: dict) -> str:
    """将单条 question JSON 格式化为可读纯文本。"""
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


@dataclass
class OpenEfsaSyncResult:
    """连接器同步结果。"""

    pages: list[SavedPage]
    question_count: int
    ok: bool
    error: str | None


def sync_open_efsa_questions(
        *,
        run_dir: Path,
        settings: Settings,
        client: httpx.Client | None = None,
) -> OpenEfsaSyncResult:
    """
    分页拉取 Questions 列表，写入 ``pages/`` 下 JSON/TXT（不落业务库）。

    默认 ``limit`` / 最大页数来自 Settings，避免一次拉完全部 2 万+ 条。
    """
    page_size = max(1, min(100, settings.crawl_open_efsa_page_size))
    max_pages = max(1, settings.crawl_open_efsa_max_pages)
    owns_client = client is None
    http = client or httpx.Client(
        timeout=settings.fetch_timeout_seconds,
        follow_redirects=True,
        headers={"User-Agent": settings.fetch_user_agent},
    )

    pages: list[SavedPage] = []
    total_questions = 0
    error: str | None = None

    try:
        for page_index in range(max_pages):
            offset = page_index * page_size
            headers = {
                "Accept": "application/json",
                "Referer": "https://open.efsa.europa.eu/questions",
                "x-security": x_security_token(),
            }
            try:
                response = http.get(
                    _API_SEARCH,
                    params={"offset": offset, "limit": page_size},
                    headers=headers,
                )
            except httpx.HTTPError as exc:
                error = f"error:{exc.__class__.__name__}:{exc}"
                pages.append(
                    SavedPage(
                        url=f"{_API_SEARCH}?offset={offset}&limit={page_size}",
                        html_path=None,
                        text_path=None,
                        title=None,
                        text_length=0,
                        status_code=None,
                        ok=False,
                        error=error,
                    )
                )
                break

            raw = response.content[: settings.fetch_max_bytes]
            api_url = str(response.url)
            if not (200 <= response.status_code < 400) or not raw:
                error = f"http_{response.status_code}_or_empty"
                pages.append(
                    SavedPage(
                        url=api_url,
                        html_path=None,
                        text_path=None,
                        title=None,
                        text_length=0,
                        status_code=response.status_code,
                        ok=False,
                        error=error,
                    )
                )
                break

            try:
                payload = json.loads(raw.decode("utf-8", errors="replace"))
            except json.JSONDecodeError:
                error = "invalid_json"
                pages.append(
                    SavedPage(
                        url=api_url,
                        html_path=None,
                        text_path=None,
                        title=None,
                        text_length=0,
                        status_code=response.status_code,
                        ok=False,
                        error=error,
                    )
                )
                break

            questions = (payload.get("data") or {}).get("questions") or []
            if not isinstance(questions, list):
                questions = []

            stem = f"{page_index:03d}_api_searchAdvanced_{offset}"
            json_path = run_dir / "pages" / f"{stem}.json"
            txt_path = run_dir / "pages" / f"{stem}.txt"
            write_bytes(json_path, raw)
            blocks = [_format_question(q) for q in questions if isinstance(q, dict)]
            text = (
                    f"# Open EFSA Questions offset={offset} limit={page_size} "
                    f"count={len(blocks)}\n\n" + "\n\n---\n\n".join(blocks)
            )
            write_text(txt_path, text)
            total_questions += len(blocks)
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
            # 轻限速，避免打爆接口
            time.sleep(0.2)
    finally:
        if owns_client:
            http.close()

    ok = total_questions > 0 and any(p.ok for p in pages)
    if not ok and error is None:
        error = "empty_crawl"
    return OpenEfsaSyncResult(
        pages=pages,
        question_count=total_questions,
        ok=ok,
        error=error,
    )
