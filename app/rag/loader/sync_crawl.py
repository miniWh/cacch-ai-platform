"""站点同步爬取：抓取正文与附件并落盘（不写业务库 / 向量库）。"""

from __future__ import annotations

import time
from pathlib import Path
from urllib.parse import urlparse

import httpx

from app.common.timeutil import now_app
from app.dao.models.source_site import SourceSite
from app.rag.loader.connectors.open_efsa_questions import (
    matches_open_efsa_questions,
    sync_open_efsa_questions,
)
from app.rag.loader.fetch import extract_html_text
from app.rag.loader.links import extract_links, is_attachment_url
from app.rag.loader.persist import (
    SavedFile,
    SavedPage,
    SyncCrawlManifest,
    content_digest,
    make_run_id,
    safe_filename_from_url,
    site_run_dir,
    write_bytes,
    write_manifest,
    write_text,
)
from app.rag.loader.probe import _host_allowed
from app.web.config import Settings


def _host_ok(url: str, domains: list[str]) -> bool:
    host = urlparse(url).hostname
    if not host:
        return False
    if not domains:
        return True
    return _host_allowed(host, domains)


def _client(settings: Settings) -> httpx.Client:
    return httpx.Client(
        timeout=settings.fetch_timeout_seconds,
        follow_redirects=True,
        headers={"User-Agent": settings.fetch_user_agent},
    )


def _get(
    client: httpx.Client,
    url: str,
    *,
    domains: list[str],
    max_bytes: int,
) -> tuple[httpx.Response | None, bytes, str | None]:
    """GET 并校验跳转域名；返回 (response, body, error)。"""
    try:
        response = client.get(url)
    except httpx.HTTPError as exc:
        return None, b"", f"error:{exc.__class__.__name__}:{exc}"

    final_host = urlparse(str(response.url)).hostname
    if domains and final_host and not _host_allowed(final_host, domains):
        return response, b"", "redirect_domain_denied"

    body = response.content[:max_bytes]
    return response, body, None


def _looks_like_spa_shell(html: str, text: str) -> bool:
    """粗判：可见文本极少且像前端壳（Angular/React 入口）。"""
    if len(text.strip()) >= 200:
        return False
    lower = html.lower()
    markers = (
        "runtime.",
        'id="root"',
        "id='root'",
        "<app-",
        "ng-version",
        "webpackchunk",
        "main.",
    )
    return any(m in lower for m in markers)


def _save_page(
    *,
    run_dir: Path,
    index: int,
    url: str,
    response: httpx.Response | None,
    body: bytes,
    error: str | None,
) -> SavedPage:
    """将页面 HTML/正文写入 pages/。"""
    if error or response is None:
        return SavedPage(
            url=url,
            html_path=None,
            text_path=None,
            title=None,
            text_length=0,
            status_code=getattr(response, "status_code", None),
            ok=False,
            error=error or "no_response",
        )

    content_type = (response.headers.get("content-type") or "").lower()
    text_body = body.decode(response.encoding or "utf-8", errors="replace")
    is_html = "html" in content_type or text_body.lstrip().lower().startswith(
        ("<!doctype", "<html")
    )
    title: str | None = None
    text = ""
    rel_html: str | None = None
    rel_text: str | None = None

    pages_dir = run_dir / "pages"
    stem = f"{index:03d}_{safe_filename_from_url(url, default='page')}"
    # 去掉已有扩展，统一加 .html / .txt
    if "." in stem:
        stem = stem.rsplit(".", 1)[0]

    if is_html:
        title, text = extract_html_text(text_body)
        html_path = pages_dir / f"{stem}.html"
        write_bytes(html_path, body)
        rel_html = str(html_path.relative_to(run_dir)).replace("\\", "/")
    else:
        text = " ".join(text_body.split())

    text_path = pages_dir / f"{stem}.txt"
    write_text(text_path, text)
    rel_text = str(text_path.relative_to(run_dir)).replace("\\", "/")

    status_ok = 200 <= response.status_code < 400
    if status_ok and is_html and _looks_like_spa_shell(text_body, text):
        return SavedPage(
            url=str(response.url),
            html_path=rel_html,
            text_path=rel_text,
            title=title,
            text_length=len(text),
            status_code=response.status_code,
            ok=False,
            error="spa_shell_empty",
        )

    ok = status_ok and bool(text or body)
    return SavedPage(
        url=str(response.url),
        html_path=rel_html,
        text_path=rel_text,
        title=title,
        text_length=len(text),
        status_code=response.status_code,
        ok=ok,
        error=None if ok else f"http_{response.status_code}_or_empty",
    )


def _save_attachment(
    *,
    run_dir: Path,
    client: httpx.Client,
    url: str,
    domains: list[str],
    max_bytes: int,
    delay_seconds: float,
) -> SavedFile:
    """下载附件到 files/。"""
    if delay_seconds > 0:
        time.sleep(delay_seconds)
    if not _host_ok(url, domains):
        return SavedFile(
            url=url,
            path=None,
            bytes=0,
            content_type=None,
            status_code=None,
            ok=False,
            error="domain_denied",
        )

    response, body, error = _get(client, url, domains=domains, max_bytes=max_bytes)
    if error or response is None:
        return SavedFile(
            url=url,
            path=None,
            bytes=0,
            content_type=None,
            status_code=getattr(response, "status_code", None),
            ok=False,
            error=error or "no_response",
        )

    if not (200 <= response.status_code < 400) or not body:
        return SavedFile(
            url=str(response.url),
            path=None,
            bytes=0,
            content_type=response.headers.get("content-type"),
            status_code=response.status_code,
            ok=False,
            error=f"http_{response.status_code}_or_empty",
        )

    name = safe_filename_from_url(str(response.url))
    digest = content_digest(body)
    # 同名不同内容：加短 hash 前缀
    out_name = f"{digest}_{name}"
    out_path = run_dir / "files" / out_name
    write_bytes(out_path, body)
    rel = str(out_path.relative_to(run_dir)).replace("\\", "/")
    return SavedFile(
        url=str(response.url),
        path=rel,
        bytes=len(body),
        content_type=response.headers.get("content-type"),
        status_code=response.status_code,
        ok=True,
        error=None,
    )


def sync_crawl_site(site: SourceSite, settings: Settings) -> SyncCrawlManifest:
    """
    同步抓取单个站点并落盘。

    - ``manual``：跳过
    - Open EFSA Questions：走专用 API 连接器（SPA，HTML 无正文）
    - 其它 ``connector``：无适配器则跳过
    - ``single_page``：入口页 + 页内附件
    - ``list_harvest``：入口页 + 同域列表页（有上限）+ 各页附件
    - 仅写本地目录，不写 document / 向量库
    """
    run_id = make_run_id()
    storage_root = Path(settings.crawl_storage_dir)
    run_dir = site_run_dir(storage_root, site.kb_id, site.site_id, run_id)
    run_dir.mkdir(parents=True, exist_ok=True)

    started = now_app_iso()
    manifest = SyncCrawlManifest(
        kb_id=site.kb_id,
        site_id=site.site_id,
        name=site.name,
        crawl_mode=site.crawl_mode or "",
        run_id=run_id,
        entry_url=site.entry_url,
        storage_dir=str(run_dir.resolve()),
        started_at=started,
    )

    mode = (site.crawl_mode or "").strip()
    if mode == "manual":
        manifest.skipped = True
        manifest.error = "crawl_mode=manual 本期不自动抓取"
        manifest.finished_at = now_app_iso()
        write_manifest(run_dir, manifest)
        return manifest

    if not site.entry_url:
        manifest.error = "缺少 entry_url"
        manifest.skipped = True
        manifest.finished_at = now_app_iso()
        write_manifest(run_dir, manifest)
        return manifest

    domains = [str(d) for d in (site.allowed_domains or [])]
    if not _host_ok(site.entry_url, domains):
        manifest.error = "domain_denied"
        manifest.finished_at = now_app_iso()
        write_manifest(run_dir, manifest)
        return manifest

    # Open EFSA：HTML 为 SPA 空壳，改走 JSON API
    if matches_open_efsa_questions(site.entry_url):
        result = sync_open_efsa_questions(run_dir=run_dir, settings=settings)
        manifest.pages.extend(result.pages)
        manifest.ok = result.ok
        manifest.error = result.error
        if result.ok:
            # 备注写入 notes 不合适；error 留空，页数在 pages 中
            manifest.error = None
        manifest.finished_at = now_app_iso()
        write_manifest(run_dir, manifest)
        return manifest

    if mode == "connector":
        manifest.skipped = True
        manifest.error = "crawl_mode=connector 无匹配的站点适配器"
        manifest.finished_at = now_app_iso()
        write_manifest(run_dir, manifest)
        return manifest

    delay = _delay_seconds(site.rate_limit_qps)
    max_bytes = settings.fetch_max_bytes
    max_list = max(0, settings.crawl_max_list_pages)
    max_files = max(0, settings.crawl_max_attachments)
    attachment_urls: list[str] = []
    seen_pages: set[str] = set()
    seen_files: set[str] = set()

    with _client(settings) as client:
        # 1) 入口页
        response, body, error = _get(
            client, site.entry_url, domains=domains, max_bytes=max_bytes
        )
        page = _save_page(
            run_dir=run_dir,
            index=0,
            url=site.entry_url,
            response=response,
            body=body,
            error=error,
        )
        manifest.pages.append(page)
        seen_pages.add(site.entry_url)

        list_candidates: list[str] = []
        if page.ok and response is not None and body:
            text_body = body.decode(response.encoding or "utf-8", errors="replace")
            page_links, file_links = extract_links(text_body, str(response.url))
            for fu in file_links:
                if fu not in seen_files and _host_ok(fu, domains):
                    seen_files.add(fu)
                    attachment_urls.append(fu)
            if mode == "list_harvest":
                for pu in page_links:
                    if (
                        pu not in seen_pages
                        and _host_ok(pu, domains)
                        and not is_attachment_url(pu)
                    ):
                        list_candidates.append(pu)

        # 2) list_harvest：浅层同域列表页
        if mode == "list_harvest" and max_list > 0:
            for offset, link in enumerate(list_candidates[:max_list], start=1):
                if delay > 0:
                    time.sleep(delay)
                seen_pages.add(link)
                resp2, body2, err2 = _get(
                    client, link, domains=domains, max_bytes=max_bytes
                )
                sub = _save_page(
                    run_dir=run_dir,
                    index=offset,
                    url=link,
                    response=resp2,
                    body=body2,
                    error=err2,
                )
                manifest.pages.append(sub)
                if sub.ok and resp2 is not None and body2:
                    tb = body2.decode(resp2.encoding or "utf-8", errors="replace")
                    _, more_files = extract_links(tb, str(resp2.url))
                    for fu in more_files:
                        if fu not in seen_files and _host_ok(fu, domains):
                            seen_files.add(fu)
                            attachment_urls.append(fu)

        # 3) 附件下载
        for file_url in attachment_urls[:max_files]:
            saved = _save_attachment(
                run_dir=run_dir,
                client=client,
                url=file_url,
                domains=domains,
                max_bytes=max_bytes,
                delay_seconds=delay,
            )
            manifest.files.append(saved)

    pages_ok = any(p.ok for p in manifest.pages)
    files_ok = any(f.ok for f in manifest.files)
    manifest.ok = pages_ok or files_ok
    if not manifest.ok and not manifest.error:
        failed_page = next((p for p in manifest.pages if p.error), None)
        manifest.error = (failed_page.error if failed_page else None) or "empty_crawl"
    manifest.finished_at = now_app_iso()
    write_manifest(run_dir, manifest)
    return manifest


def now_app_iso() -> str:
    """应用墙钟 ISO 字符串（无时区后缀）。"""
    return now_app().isoformat(timespec="seconds")


def _delay_seconds(rate_limit_qps: float | None) -> float:
    if rate_limit_qps is None or rate_limit_qps <= 0:
        return 0.5
    return max(0.1, 1.0 / float(rate_limit_qps))
