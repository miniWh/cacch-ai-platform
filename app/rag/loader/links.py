"""从 HTML 中提取页面链接与附件链接。"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse, urlunparse

# 视为附件下载的扩展名（小写，含点）
ATTACHMENT_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".zip",
        ".rar",
        ".7z",
        ".txt",
        ".csv",
        ".rtf",
        ".odt",
    }
)


class _HrefCollector(HTMLParser):
    """收集 a[href] 与常见资源链接。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() not in {"a", "area", "link"}:
            return
        for key, value in attrs:
            if key.lower() == "href" and value:
                self.hrefs.append(value.strip())


def normalize_url(base_url: str, href: str) -> str | None:
    """将相对/绝对 href 解析为可请求的 http(s) URL；过滤锚点与非 http。"""
    raw = href.strip()
    if not raw or raw.startswith(("#", "javascript:", "mailto:", "tel:", "data:")):
        return None
    absolute = urljoin(base_url, raw)
    parsed = urlparse(absolute)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    # 去掉 fragment，保留 query（部分附件依赖 query）
    cleaned = parsed._replace(fragment="")
    return urlunparse(cleaned)


def path_extension(url: str) -> str:
    """取 URL path 的小写扩展名（含点）；无扩展名返回空串。"""
    path = urlparse(url).path
    # 去掉末尾斜杠后再取后缀
    name = path.rstrip("/").rsplit("/", 1)[-1]
    if "." not in name:
        return ""
    return "." + name.rsplit(".", 1)[-1].lower()


def is_attachment_url(url: str) -> bool:
    """根据 path 扩展名判断是否像附件。"""
    return path_extension(url) in ATTACHMENT_EXTENSIONS


def extract_links(html: str, base_url: str) -> tuple[list[str], list[str]]:
    """
    从 HTML 提取去重后的链接。

    :return: (page_urls, attachment_urls)
    """
    collector = _HrefCollector()
    try:
        collector.feed(html)
        collector.close()
    except Exception:  # noqa: BLE001 — 容错：坏 HTML 仍尽量用正则兜底
        collector.hrefs.extend(
            re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.I)
        )

    pages: list[str] = []
    attachments: list[str] = []
    seen: set[str] = set()
    for href in collector.hrefs:
        url = normalize_url(base_url, href)
        if url is None or url in seen:
            continue
        seen.add(url)
        if is_attachment_url(url):
            attachments.append(url)
        else:
            pages.append(url)
    return pages, attachments
