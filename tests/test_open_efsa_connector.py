"""Open EFSA Questions 连接器单元测试。"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from app.dao.models.source_site import SourceSite
from app.rag.loader.connectors.open_efsa_questions import (
    matches_open_efsa_questions,
    sync_open_efsa_questions,
    x_security_token,
)
from app.rag.loader.sync_crawl import sync_crawl_site
from app.web.config import Settings


def test_matches_open_efsa_questions() -> None:
    assert matches_open_efsa_questions("https://open.efsa.europa.eu/questions")
    assert matches_open_efsa_questions(
        "https://open.efsa.europa.eu/questions/EFSA-Q-2025-00156"
    )
    assert not matches_open_efsa_questions("https://www.efsa.europa.eu/en/publications")


def test_x_security_token_formula() -> None:
    assert x_security_token(now_ts=1_700_000_000) == str(123 * 1_700_000_000 + 369)


def test_sync_open_efsa_questions_saves(tmp_path: Path) -> None:
    payload = {
        "data": {
            "questions": [
                {
                    "questionNumber": "EFSA-Q-2025-00156",
                    "foodDomainDescription": "Nutrition",
                    "phaseName": "Ongoing Risk Assessment",
                    "subject": "<div>Pine needle extract</div>",
                    "substanceNames": ["Pine"],
                    "applicantNames": ["ACME"],
                }
            ]
        }
    }
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = (
        "https://open.efsa.europa.eu/api/question/searchAdvanced?offset=0&limit=20"
    )
    mock_resp.content = __import__("json").dumps(payload).encode()

    settings = Settings(
        crawl_storage_dir=str(tmp_path / "crawl"),
        crawl_open_efsa_page_size=20,
        crawl_open_efsa_max_pages=1,
    )
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    with patch("app.rag.loader.connectors.open_efsa_questions.httpx.Client") as cls:
        instance = cls.return_value
        instance.get.return_value = mock_resp
        result = sync_open_efsa_questions(run_dir=run_dir, settings=settings)

    assert result.ok is True
    assert result.question_count == 1
    assert result.pages[0].ok is True
    assert result.pages[0].text_path is not None
    text = (run_dir / result.pages[0].text_path).read_text(encoding="utf-8")
    assert "EFSA-Q-2025-00156" in text
    assert "Pine needle extract" in text
    assert "<div>" not in text


def test_sync_crawl_routes_open_efsa(tmp_path: Path) -> None:
    site = SourceSite(
        site_id="test",
        kb_id=1,
        name="测试",
        region="EU",
        category="evaluation",
        entry_url="https://open.efsa.europa.eu/questions",
        crawl_mode="single_page",
        allowed_domains=["open.efsa.europa.eu"],
        status="active",
    )
    settings = Settings(
        crawl_storage_dir=str(tmp_path / "crawl"),
        crawl_open_efsa_max_pages=1,
        crawl_open_efsa_page_size=5,
    )
    payload = {
        "data": {
            "questions": [
                {
                    "questionNumber": "EFSA-Q-1",
                    "subject": "Hello",
                    "phaseName": "Published",
                }
            ]
        }
    }
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = "https://open.efsa.europa.eu/api/question/searchAdvanced"
    mock_resp.content = __import__("json").dumps(payload).encode()

    with patch("app.rag.loader.connectors.open_efsa_questions.httpx.Client") as cls:
        instance = cls.return_value
        instance.get.return_value = mock_resp
        manifest = sync_crawl_site(site, settings)

    assert manifest.ok is True
    assert len(manifest.pages) == 1
    assert "searchAdvanced" in (manifest.pages[0].url or "")
