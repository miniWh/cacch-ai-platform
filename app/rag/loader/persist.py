"""抓取结果落盘：目录约定与安全文件名。"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlparse

from app.common.timeutil import now_app


def make_run_id(when: datetime | None = None) -> str:
    """生成一次同步 run_id（本地墙钟，便于目录排序）。"""
    ts = when or now_app()
    return ts.strftime("%Y%m%dT%H%M%S")


def site_run_dir(storage_root: Path, kb_id: int, site_id: str, run_id: str) -> Path:
    """``{root}/kb_{kb_id}/{site_id}/{run_id}``。"""
    safe_site = re.sub(r"[^\w.\-]+", "_", site_id).strip("._") or "site"
    return storage_root / f"kb_{kb_id}" / safe_site / run_id


def safe_filename_from_url(url: str, *, default: str = "file.bin") -> str:
    """从 URL path 得到相对安全的文件名；过长或空则用 hash。"""
    path = unquote(urlparse(url).path)
    name = path.rstrip("/").rsplit("/", 1)[-1] if path else ""
    name = re.sub(r"[^\w.\-()+]+", "_", name).strip("._")
    if not name or len(name) > 180:
        digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
        ext = ""
        if "." in (name or ""):
            ext = "." + name.rsplit(".", 1)[-1][:16]
        name = f"{digest}{ext}" if ext else f"{digest}_{default}"
    return name


def content_digest(data: bytes) -> str:
    """内容短 hash，用于去重文件名冲突。"""
    return hashlib.sha1(data).hexdigest()[:10]


@dataclass
class SavedPage:
    """已落盘的页面。"""

    url: str
    html_path: str | None
    text_path: str | None
    title: str | None
    text_length: int
    status_code: int | None
    ok: bool
    error: str | None = None


@dataclass
class SavedFile:
    """已落盘的附件。"""

    url: str
    path: str | None
    bytes: int
    content_type: str | None
    status_code: int | None
    ok: bool
    error: str | None = None


@dataclass
class SyncCrawlManifest:
    """单次站点同步清单（写入 manifest.json，不落业务库）。"""

    kb_id: int
    site_id: str
    name: str
    crawl_mode: str
    run_id: str
    entry_url: str | None
    storage_dir: str
    started_at: str
    finished_at: str | None = None
    ok: bool = False
    skipped: bool = False
    error: str | None = None
    pages: list[SavedPage] = field(default_factory=list)
    files: list[SavedFile] = field(default_factory=list)

    def to_dict(self) -> dict:
        """JSON 可序列化字典。"""
        return asdict(self)


def write_bytes(path: Path, data: bytes) -> None:
    """创建父目录并写入二进制。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def write_text(path: Path, text: str) -> None:
    """创建父目录并写入 UTF-8 文本。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_manifest(run_dir: Path, manifest: SyncCrawlManifest) -> Path:
    """写入 manifest.json，返回路径。"""
    path = run_dir / "manifest.json"
    write_text(path, json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2))
    return path
