"""RAG 文档/站点加载器包：探活、入口页抓取等。"""

from app.rag.loader.fetch import FetchResult, fetch_site_page, print_fetch_result
from app.rag.loader.probe import apply_probe_result, probe_site

__all__ = [
    "FetchResult",
    "apply_probe_result",
    "fetch_site_page",
    "print_fetch_result",
    "probe_site",
]
