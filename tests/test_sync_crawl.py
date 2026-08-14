"""链接提取与同步落盘单元测试。"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from app.dao.models.source_site import SourceSite
from app.rag.loader.links import extract_links, is_attachment_url, normalize_url
from app.rag.loader.sync_crawl import sync_crawl_site
from app.web.config import Settings


def test_normalize_and_attachment_detect() -> None:
    base = "https://example.com/list/"
    assert normalize_url(base, "report.pdf") == "https://example.com/list/report.pdf"
    assert normalize_url(base, "#top") is None
    assert is_attachment_url("https://example.com/a/b.PDF") is True
    assert is_attachment_url("https://example.com/page") is False


def test_extract_links() -> None:
    html = """
    <html><body>
      <a href="/docs/a.pdf">PDF</a>
      <a href="https://example.com/item/1">Item</a>
      <a href="mailto:x@y.com">mail</a>
    </body></html>
    """
    pages, files = extract_links(html, "https://example.com/list/")
    assert "https://example.com/docs/a.pdf" in files
    assert "https://example.com/item/1" in pages


def test_sync_crawl_saves_page_and_pdf(tmp_path: Path) -> None:
    site = SourceSite(
        site_id="demo_sync",
        kb_id=1,
        name="Demo Sync",
        region="INT",
        category="database",
        entry_url="https://example.com/entry",
        crawl_mode="single_page",
        allowed_domains=["example.com"],
        status="active",
        rate_limit_qps=100.0,
    )
    settings = Settings(
        crawl_storage_dir=str(tmp_path / "crawl"),
        crawl_max_list_pages=0,
        crawl_max_attachments=10,
        fetch_timeout_seconds=5.0,
    )

    entry_html = (
        b"<html><head><title>Entry</title></head>"
        b'<body>Hello <a href="/files/r.pdf">pdf</a></body></html>'
    )
    entry_resp = MagicMock()
    entry_resp.status_code = 200
    entry_resp.url = "https://example.com/entry"
    entry_resp.headers = {"content-type": "text/html; charset=utf-8"}
    entry_resp.encoding = "utf-8"
    entry_resp.content = entry_html

    pdf_resp = MagicMock()
    pdf_resp.status_code = 200
    pdf_resp.url = "https://example.com/files/r.pdf"
    pdf_resp.headers = {"content-type": "application/pdf"}
    pdf_resp.encoding = "utf-8"
    pdf_resp.content = b"%PDF-1.4 demo"

    def _get(url: str) -> MagicMock:
        if url.endswith(".pdf") or "r.pdf" in url:
            return pdf_resp
        return entry_resp

    with patch("app.rag.loader.sync_crawl.httpx.Client") as client_cls:
        instance = client_cls.return_value.__enter__.return_value
        instance.get.side_effect = _get
        manifest = sync_crawl_site(site, settings)

    assert manifest.ok is True
    assert manifest.skipped is False
    assert len(manifest.pages) == 1
    assert manifest.pages[0].ok is True
    assert manifest.pages[0].title == "Entry"
    assert len(manifest.files) == 1
    assert manifest.files[0].ok is True
    assert manifest.files[0].bytes == len(b"%PDF-1.4 demo")

    run_dir = Path(manifest.storage_dir)
    assert (run_dir / "manifest.json").is_file()
    assert manifest.pages[0].text_path is not None
    assert (run_dir / manifest.pages[0].text_path).is_file()
    assert manifest.files[0].path is not None
    assert (run_dir / manifest.files[0].path).read_bytes() == b"%PDF-1.4 demo"


def test_sync_skips_manual(tmp_path: Path) -> None:
    site = SourceSite(
        site_id="manual_x",
        kb_id=1,
        name="Manual",
        region="CN",
        category="standard",
        entry_url="https://example.com",
        crawl_mode="manual",
        allowed_domains=["example.com"],
        status="active",
    )
    settings = Settings(crawl_storage_dir=str(tmp_path / "crawl"))
    manifest = sync_crawl_site(site, settings)
    assert manifest.skipped is True
    assert manifest.ok is False
    assert (Path(manifest.storage_dir) / "manifest.json").is_file()
