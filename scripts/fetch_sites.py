#!/usr/bin/env python
"""按知识库站点清单抓取入口页，结果打印到控制台（不落库）。

用法（仓库根目录，已激活 .venv）::

    python scripts/fetch_sites.py --kb-id 1
    python scripts/fetch_sites.py --kb-id 1 --site-id eu_efsa_publications
    python scripts/fetch_sites.py --kb-id 1 --status active --preview 1200
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 保证仓库根在 sys.path
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.dao.database import get_session_factory, init_db  # noqa: E402
from app.service.site_fetch_service import SiteFetchService  # noqa: E402
from app.web.config import get_settings  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="抓取站点清单入口页并打印（不落库）")
    parser.add_argument("--kb-id", type=int, required=True, help="知识库 ID")
    parser.add_argument("--site-id", type=str, default=None, help="仅抓取指定站点")
    parser.add_argument(
        "--status",
        type=str,
        default="active",
        help="站点状态过滤；传 all 表示不过滤",
    )
    parser.add_argument(
        "--preview",
        type=int,
        default=800,
        help="控制台正文预览字符数",
    )
    args = parser.parse_args()

    status = None if args.status.lower() == "all" else args.status

    get_settings.cache_clear()
    init_db()
    session = get_session_factory()()
    try:
        service = SiteFetchService(session)
        results = service.fetch_kb_sites(
            args.kb_id,
            site_id=args.site_id,
            status=status,
            print_console=True,
            preview_chars=args.preview,
        )
        ok_n = sum(1 for r in results if r.ok)
        skip_n = sum(1 for r in results if r.skipped)
        fail_n = len(results) - ok_n - skip_n
        print(
            f"\n汇总: 共 {len(results)} 站 | 成功 {ok_n} | 跳过 {skip_n} | 失败 {fail_n}"
        )
        return 0 if fail_n == 0 else 2
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
