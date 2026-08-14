"""按站点清单批量抓取（结果打印控制台，不落库）。"""

from __future__ import annotations

import time
from dataclasses import asdict

from sqlalchemy.orm import Session

from app.common.exceptions import NotFoundError
from app.dao.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.dao.repositories.source_site_repository import SourceSiteRepository
from app.rag.loader.fetch import FetchResult, fetch_site_page, print_fetch_result
from app.web.config import Settings, get_settings


class SiteFetchService:
    """读取站点清单并抓取入口页，仅输出到控制台，不写入业务表。"""

    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self._session = session
        self._settings = settings or get_settings()
        self._sources = SourceSiteRepository(session)
        self._kbs = KnowledgeBaseRepository(session)

    def fetch_kb_sites(
        self,
        kb_id: int,
        *,
        site_id: str | None = None,
        status: str | None = "active",
        print_console: bool = True,
        preview_chars: int = 800,
    ) -> list[FetchResult]:
        """
        抓取指定知识库下的站点。

        :param site_id: 若指定则只抓该站；否则按清单批量
        :param status: 默认仅 active；传 None 表示不过滤状态
        :param print_console: 是否 print 到控制台
        """
        if self._kbs.get(kb_id) is None:
            raise NotFoundError(f"knowledge base {kb_id} not found")

        if site_id:
            entity = self._sources.get(kb_id, site_id)
            if entity is None:
                raise NotFoundError(f"site not found: {site_id}")
            sites = [entity]
        else:
            sites = self._sources.list(kb_id, status=status)

        results: list[FetchResult] = []
        for index, site in enumerate(sites):
            if index > 0:
                delay = self._delay_seconds(site.rate_limit_qps)
                if delay > 0:
                    time.sleep(delay)
            result = fetch_site_page(site, self._settings)
            results.append(result)
            if print_console:
                print_fetch_result(result, preview_chars=preview_chars)
        return results

    def results_as_dicts(self, results: list[FetchResult]) -> list[dict]:
        """转为可 JSON 序列化的摘要（正文截断，避免响应过大）。"""
        rows: list[dict] = []
        for item in results:
            data = asdict(item)
            text = data.get("text") or ""
            data["text_length"] = len(text)
            data["text_preview"] = text[:500]
            del data["text"]
            rows.append(data)
        return rows

    @staticmethod
    def _delay_seconds(rate_limit_qps: float | None) -> float:
        if rate_limit_qps is None or rate_limit_qps <= 0:
            return 0.5
        return max(0.1, 1.0 / float(rate_limit_qps))
