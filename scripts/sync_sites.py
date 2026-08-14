#!/usr/bin/env python
"""按知识库站点清单同步抓取并落盘（正文+附件，不写业务库）。

用法（仓库根目录，已激活 .venv）::

    python scripts/sync_sites.py --kb-id 1 --site-id eu_efsa_publications
    python scripts/sync_sites.py --kb-id 1
    python scripts/sync_sites.py --kb-id 1 --status all
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.dao.database import get_session_factory, init_db  # noqa: E402
from app.service.site_fetch_service import SiteFetchService  # noqa: E402
from app.web.config import get_settings  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="同步站点抓取并落盘（不落库）")
    parser.add_argument("--kb-id", type=int, required=True, help="知识库 ID")
    parser.add_argument("--site-id", type=str, default=None, help="仅同步指定站点")
    parser.add_argument(
        "--status",
        type=str,
        default="active",
        help="站点状态过滤；传 all 表示不过滤",
    )
    args = parser.parse_args()

    status = None if args.status.lower() == "all" else args.status

    get_settings.cache_clear()
    init_db()
    session = get_session_factory()()
    try:
        service = SiteFetchService(session)
        manifests = service.sync_kb_sites(
            args.kb_id,
            site_id=args.site_id,
            status=status,
        )
        ok_n = sum(1 for m in manifests if m.ok)
        skip_n = sum(1 for m in manifests if m.skipped)
        fail_n = len(manifests) - ok_n - skip_n
        for m in manifests:
            print(
                f"[{m.site_id}] ok={m.ok} skipped={m.skipped} "
                f"pages={len(m.pages)} files={len(m.files)} "
                f"dir={m.storage_dir} error={m.error}"
            )
        print(
            f"\n汇总: 共 {len(manifests)} 站 | 成功 {ok_n} | 跳过 {skip_n} | 失败 {fail_n}"
        )
        return 0 if fail_n == 0 else 2
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
