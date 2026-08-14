"""RAG 来源站点 HTTP API 路由。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.dto import ok
from app.dao.database import get_db
from app.service.schemas.source import ProbeRequest, SourceSiteCreate, SourceSiteUpdate
from app.service.site_fetch_service import SiteFetchService
from app.service.source_service import SourceService
from app.web.middleware.auth import require_business_user

router = APIRouter(
    prefix="/api/v1/rag/kb/{kb_id}/sources",
    tags=["rag-sources"],
    dependencies=[Depends(require_business_user)],
)


def _service(db: Session = Depends(get_db)) -> SourceService:
    """FastAPI 依赖：构造 SourceService。"""
    return SourceService(db)


def _fetch_service(db: Session = Depends(get_db)) -> SiteFetchService:
    """FastAPI 依赖：构造 SiteFetchService。"""
    return SiteFetchService(db)


@router.get("")
def list_sources(
        kb_id: int,
        keyword: str | None = Query(default=None),
        region: str | None = Query(default=None),
        category: str | None = Query(default=None),
        status: str | None = Query(default=None),
        service: SourceService = Depends(_service),
) -> dict:
    """列出知识库下的来源站点（支持筛选）。"""
    data = service.list_sources(
        kb_id,
        keyword=keyword,
        region=region,
        category=category,
        status=status,
    )
    return ok(data.model_dump(mode="json"))


@router.post("")
def create_source(
        kb_id: int,
        payload: SourceSiteCreate,
        service: SourceService = Depends(_service),
) -> dict:
    """在知识库下创建来源站点。"""
    data = service.create_source(kb_id, payload)
    return ok(data.model_dump(mode="json"))


@router.post("/probe")
def probe_sources(
        kb_id: int,
        payload: ProbeRequest | None = None,
        service: SourceService = Depends(_service),
) -> dict:
    """批量探测站点入口 URL 可达性。"""
    data = service.probe(kb_id, payload or ProbeRequest())
    return ok(data.model_dump(mode="json"))


@router.post("/fetch")
def fetch_sources(
        kb_id: int,
        site_id: str | None = Query(default=None, description="仅抓取指定站点"),
        status: str | None = Query(default="active", description="状态过滤；空=不过滤"),
        service: SiteFetchService = Depends(_fetch_service),
) -> dict:
    """按站点清单抓取入口页预览（内存/控制台），不落盘、不落库。"""
    results = service.fetch_kb_sites(
        kb_id,
        site_id=site_id,
        status=status if status else None,
        print_console=True,
    )
    items = service.results_as_dicts(results)
    return ok(
        {
            "total": len(items),
            "ok": sum(1 for r in results if r.ok),
            "skipped": sum(1 for r in results if r.skipped),
            "failed": sum(1 for r in results if not r.ok and not r.skipped),
            "items": items,
            "persisted": False,
            "saved_to_disk": False,
        }
    )


@router.post("/sync")
def sync_sources(
        kb_id: int,
        site_id: str | None = Query(
            default=None,
            description="指定站点；不传则同步该 kb 下符合 status 的站点（供 ESB 批量）",
        ),
        status: str | None = Query(
            default="active",
            description="未指定 site_id 时的状态过滤；空=不过滤",
        ),
        service: SiteFetchService = Depends(_fetch_service),
) -> dict:
    """
    同步抓取正文与附件并落盘（不写业务库 / 向量库）。

    定时由 ESB 调用；本服务不内置调度。推荐每次传 ``site_id``。
    """
    manifests = service.sync_kb_sites(
        kb_id,
        site_id=site_id,
        status=status if status else None,
    )
    items = service.manifests_as_dicts(manifests)
    return ok(
        {
            "kb_id": kb_id,
            "total": len(items),
            "ok": sum(1 for m in manifests if m.ok),
            "skipped": sum(1 for m in manifests if m.skipped),
            "failed": sum(1 for m in manifests if not m.ok and not m.skipped),
            "items": items,
            "saved_to_disk": True,
            "persisted_db": False,
        }
    )


@router.post("/{site_id}/sync")
def sync_source(
        kb_id: int,
        site_id: str,
        service: SiteFetchService = Depends(_fetch_service),
) -> dict:
    """
    同步单站：抓取内容与附件落盘（ESB 主入口）。

    不写 document / 向量库；目录见响应 ``storage_dir`` / ``manifest``。
    """
    manifests = service.sync_kb_sites(kb_id, site_id=site_id, status=None)
    items = service.manifests_as_dicts(manifests)
    item = items[0] if items else None
    return ok(
        {
            "kb_id": kb_id,
            "site_id": site_id,
            "saved_to_disk": True,
            "persisted_db": False,
            "item": item,
            "items": items,
        }
    )


@router.get("/{site_id}")
def get_source(
        kb_id: int,
        site_id: str,
        service: SourceService = Depends(_service),
) -> dict:
    """获取单个来源站点详情。"""
    data = service.get_source(kb_id, site_id)
    return ok(data.model_dump(mode="json"))


@router.patch("/{site_id}")
def update_source(
        kb_id: int,
        site_id: str,
        payload: SourceSiteUpdate,
        service: SourceService = Depends(_service),
) -> dict:
    """更新指定来源站点。"""
    data = service.update_source(kb_id, site_id, payload)
    return ok(data.model_dump(mode="json"))


@router.delete("/{site_id}")
def delete_source(
        kb_id: int,
        site_id: str,
        service: SourceService = Depends(_service),
) -> dict:
    """删除指定来源站点。"""
    service.delete_source(kb_id, site_id)
    return ok({"site_id": site_id, "deleted": True})
