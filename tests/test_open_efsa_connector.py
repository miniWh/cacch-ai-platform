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


def _json_resp(payload: dict, url: str) -> MagicMock:
    mock = MagicMock()
    mock.status_code = 200
    mock.url = url
    mock.content = __import__("json").dumps(payload).encode()
    mock.headers = {"content-type": "application/json"}
    return mock


def test_sync_open_efsa_list_and_detail(tmp_path: Path) -> None:
    list_payload = {
        "data": {
            "questions": [
                {
                    "questionNumber": "EFSA-Q-2024-00532",
                    "foodDomainDescription": "Feed Products",
                    "phaseName": "Application Withdrawn",
                    "subject": "<div>Zinc lysinate sulfate</div>",
                    "substanceNames": ["Zinc lysinate sulfate"],
                }
            ]
        }
    }
    detail_payload = {
        "data": {
            "questionNumber": "EFSA-Q-2024-00532",
            "dossierNumber": "FEED-2024-27330",
            "regulationName": "Regulation (EC) No 1831/2003",
            "applicationTypeDescription": "Application for authorisation...",
            "subject": "<div>Zinc lysinate sulfate</div>",
            "phaseName": "Application Withdrawn",
            "comment": {"comment": "<div>withdrawn notice</div>"},
            "output": {
                "outputNumber": "ON-9927",
                "type": "Scientific Panel or Committee",
            },
            "substances": [
                {"termExtendedName": "Zinc lysinate sulfate", "cas": "1007631-69-7"}
            ],
            "questionApplicants": [
                {"organisationName": "Phytobiotics Futterzusatzstoffe GmbH"}
            ],
        }
    }
    timeline_payload = {
        "data": [
            {
                "title": "Application Withdrawn",
                "dateDisplay": "13-08-2026",
                "date": "2026-08-13",
            }
        ]
    }
    study_payload = {
        "data": [
            {
                "id": "a4bdb621-f6fd-4bb8-bcee-d621a450839b",
                "fileId": "a4bdb621-f6fd-4bb8-bcee-d621a450839b",
                "title": "Overarching Mandate",
                "fileName": "mandate.pdf",
                "pathToFile": "/EFSA/path/",
                "isAdditionalEvidence": False,
                "publishedDate": "2026-02-03",
                "fileSizeBytes": 10,
            }
        ]
    }

    pdf_resp = MagicMock()
    pdf_resp.status_code = 200
    pdf_resp.content = b"%PDF-1.4 demo"
    pdf_resp.headers = {"content-type": "application/octet-stream"}

    def _get(url: str, params=None, headers=None):  # noqa: ANN001
        u = str(url)
        if "searchAdvanced" in u:
            return _json_resp(list_payload, u)
        if u.endswith("/question/get") or "/question/get?" in u or "question/get" in u:
            return _json_resp(detail_payload, u)
        if "getTimeline" in u:
            return _json_resp(timeline_payload, u)
        if "getStudyPreviewForQuestion" in u:
            return _json_resp(study_payload, u)
        raise AssertionError(f"unexpected GET {u}")

    settings = Settings(
        crawl_storage_dir=str(tmp_path / "crawl"),
        crawl_open_efsa_page_size=20,
        crawl_open_efsa_max_pages=1,
        crawl_open_efsa_fetch_details=True,
        crawl_open_efsa_max_details=5,
        crawl_open_efsa_download_files=True,
    )
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    with patch("app.rag.loader.connectors.open_efsa_questions.httpx.Client") as cls:
        instance = cls.return_value
        instance.get.side_effect = _get
        instance.post.return_value = pdf_resp
        result = sync_open_efsa_questions(run_dir=run_dir, settings=settings)

    assert result.ok is True
    assert result.question_count == 1
    assert result.detail_count == 1
    assert any("detail_EFSA-Q-2024-00532" in (p.html_path or "") for p in result.pages)
    detail_txt = next(
        p for p in result.pages if p.title == "EFSA-Q-2024-00532" and p.ok
    )
    text = (run_dir / (detail_txt.text_path or "")).read_text(encoding="utf-8")
    assert "FEED-2024-27330" in text
    assert "Regulation (EC) No 1831/2003" in text
    assert "withdrawn notice" in text
    assert result.files and result.files[0].ok is True
    assert (run_dir / (result.files[0].path or "")).read_bytes().startswith(b"%PDF")


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
        crawl_open_efsa_fetch_details=False,
        crawl_open_efsa_download_files=False,
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
    mock_resp = _json_resp(
        payload, "https://open.efsa.europa.eu/api/question/searchAdvanced"
    )

    with patch("app.rag.loader.connectors.open_efsa_questions.httpx.Client") as cls:
        instance = cls.return_value
        instance.get.return_value = mock_resp
        manifest = sync_crawl_site(site, settings)

    assert manifest.ok is True
    assert len(manifest.pages) == 1
    assert "searchAdvanced" in (manifest.pages[0].url or "")
