"""按站点清单抓取网页正文（仅内存结果，不落库）。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import urlparse

import httpx

from app.dao.models.source_site import SourceSite
from app.rag.loader.probe import _host_allowed
from app.web.config import Settings


class _HTMLTextExtractor(HTMLParser):
    """简易 HTML 正文抽取：去掉 script/style，拼接可见文本。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript"} and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        text = data.strip()
        if text:
            self._chunks.append(text)

    def text(self) -> str:
        joined = " ".join(self._chunks)
        return re.sub(r"\s+", " ", joined).strip()


@dataclass(frozen=True)
class FetchResult:
    """单次抓取结果（不落库）。"""

    site_id: str
    name: str
    crawl_mode: str
    url: str | None
    ok: bool
    status_code: int | None
    title: str | None
    text: str
    error: str | None
    skipped: bool = False


def extract_html_text(html: str) -> tuple[str | None, str]:
    """从 HTML 提取 title 与正文纯文本。"""
    title_match = re.search(
        r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL
    )
    title = None
    if title_match:
        title = re.sub(r"\s+", " ", title_match.group(1)).strip() or None

    parser = _HTMLTextExtractor()
    try:
        parser.feed(html)
        parser.close()
    except Exception:  # noqa: BLE001 — 容错：解析失败仍返回空文本
        return title, ""
    return title, parser.text()


def fetch_site_page(site: SourceSite, settings: Settings) -> FetchResult:
    """
    根据站点清单配置抓取入口页。

    - ``manual`` / ``connector``：本期跳过（需人工或专用适配器）
    - ``single_page`` / ``list_harvest``：抓取 ``entry_url``
      （list 暂只抓入口，不跟列表）
    - 强制校验 ``allowed_domains``；不写库
    """
    mode = (site.crawl_mode or "").strip()
    if mode in {"manual", "connector"}:
        return FetchResult(
            site_id=site.site_id,
            name=site.name,
            crawl_mode=mode,
            url=site.entry_url,
            ok=False,
            status_code=None,
            title=None,
            text="",
            error=f"crawl_mode={mode} 本期不自动抓取",
            skipped=True,
        )

    if not site.entry_url:
        return FetchResult(
            site_id=site.site_id,
            name=site.name,
            crawl_mode=mode,
            url=None,
            ok=False,
            status_code=None,
            title=None,
            text="",
            error="缺少 entry_url",
            skipped=True,
        )

    parsed = urlparse(site.entry_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return FetchResult(
            site_id=site.site_id,
            name=site.name,
            crawl_mode=mode,
            url=site.entry_url,
            ok=False,
            status_code=None,
            title=None,
            text="",
            error="invalid_url",
            skipped=False,
        )

    domains = [str(d) for d in (site.allowed_domains or [])]
    if domains and not _host_allowed(parsed.hostname, domains):
        return FetchResult(
            site_id=site.site_id,
            name=site.name,
            crawl_mode=mode,
            url=site.entry_url,
            ok=False,
            status_code=None,
            title=None,
            text="",
            error="domain_denied",
            skipped=False,
        )

    timeout = settings.fetch_timeout_seconds
    max_bytes = settings.fetch_max_bytes
    try:
        with httpx.Client(
                timeout=timeout,
                follow_redirects=True,
                headers={"User-Agent": settings.fetch_user_agent},
        ) as client:
            response = client.get(site.entry_url)
            raw = response.content[:max_bytes]
            # 最终 URL 也需过白名单（防跳转到外域）
            final_host = urlparse(str(response.url)).hostname
            if domains and final_host and not _host_allowed(final_host, domains):
                return FetchResult(
                    site_id=site.site_id,
                    name=site.name,
                    crawl_mode=mode,
                    url=str(response.url),
                    ok=False,
                    status_code=response.status_code,
                    title=None,
                    text="",
                    error="redirect_domain_denied",
                    skipped=False,
                )

            content_type = (response.headers.get("content-type") or "").lower()
            text_body = raw.decode(response.encoding or "utf-8", errors="replace")
            if "html" in content_type or text_body.lstrip().lower().startswith(
                    ("<!doctype", "<html")
            ):
                title, text = extract_html_text(text_body)
            else:
                title = None
                text = re.sub(r"\s+", " ", text_body).strip()

            ok = 200 <= response.status_code < 400 and bool(text)
            return FetchResult(
                site_id=site.site_id,
                name=site.name,
                crawl_mode=mode,
                url=str(response.url),
                ok=ok,
                status_code=response.status_code,
                title=title,
                text=text,
                error=None if ok else f"http_{response.status_code}_or_empty",
                skipped=False,
            )
    except httpx.HTTPError as exc:
        return FetchResult(
            site_id=site.site_id,
            name=site.name,
            crawl_mode=mode,
            url=site.entry_url,
            ok=False,
            status_code=None,
            title=None,
            text="",
            error=f"error:{exc.__class__.__name__}:{exc}",
            skipped=False,
        )


def print_fetch_result(result: FetchResult, *, preview_chars: int = 800) -> None:
    """将抓取结果打印到控制台（stdout）。"""
    sep = "=" * 72
    print(sep)
    print(f"[站点] {result.site_id} | {result.name}")
    print(f"[模式] {result.crawl_mode}")
    print(f"[URL ] {result.url}")
    if result.skipped:
        print(f"[跳过] {result.error}")
        print(sep)
        return
    print(f"[结果] ok={result.ok} status={result.status_code} error={result.error}")
    if result.title:
        print(f"[标题] {result.title}")
    preview = result.text[:preview_chars]
    print(f"[正文预览] ({len(result.text)} 字符)")
    print(preview + ("…" if len(result.text) > preview_chars else ""))
    print(sep)
