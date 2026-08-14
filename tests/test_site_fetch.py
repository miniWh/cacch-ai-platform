"""站点入口页抓取（不落库）单元测试。"""

from unittest.mock import MagicMock, patch

from app.dao.models.source_site import SourceSite
from app.rag.loader.fetch import extract_html_text, fetch_site_page
from app.web.config import Settings


def test_extract_html_text() -> None:
    html = """
    <html><head><title> Hello </title>
    <script>var a=1;</script></head>
    <body><p>第一段</p><style>.x{}</style><p>第二段</p></body></html>
    """
    title, text = extract_html_text(html)
    assert title == "Hello"
    assert "第一段" in text
    assert "第二段" in text
    assert "var a" not in text


def test_fetch_skips_manual() -> None:
    site = SourceSite(
        site_id="manual_site",
        kb_id=1,
        name="人工站",
        region="CN",
        category="standard",
        entry_url="https://example.com",
        crawl_mode="manual",
        allowed_domains=["example.com"],
        status="active",
    )
    result = fetch_site_page(site, Settings())
    assert result.skipped is True
    assert result.ok is False


def test_fetch_single_page_ok() -> None:
    site = SourceSite(
        site_id="demo",
        kb_id=1,
        name="Demo",
        region="INT",
        category="database",
        entry_url="https://example.com/page",
        crawl_mode="single_page",
        allowed_domains=["example.com"],
        status="active",
    )
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = "https://example.com/page"
    mock_resp.headers = {"content-type": "text/html; charset=utf-8"}
    mock_resp.encoding = "utf-8"
    mock_resp.content = (
        "<html><head><title>T</title></head><body>正文ABC</body></html>".encode()
    )

    with patch("app.rag.loader.fetch.httpx.Client") as client_cls:
        instance = client_cls.return_value.__enter__.return_value
        instance.get.return_value = mock_resp
        result = fetch_site_page(site, Settings())

    assert result.ok is True
    assert result.title == "T"
    assert "正文ABC" in result.text
    assert result.error is None


def test_fetch_domain_denied() -> None:
    site = SourceSite(
        site_id="deny",
        kb_id=1,
        name="Deny",
        region="US",
        category="registration",
        entry_url="https://evil.com/",
        crawl_mode="single_page",
        allowed_domains=["example.com"],
        status="active",
    )
    result = fetch_site_page(site, Settings())
    assert result.ok is False
    assert result.error == "domain_denied"
