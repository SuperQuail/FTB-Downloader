"""本地整合包库。

记录用户添加过哪些整合包 / 版本，以及「准备」到哪一步了。
存放位置：%LOCALAPPDATA%\\FTBDownloader\\library.json
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path


def data_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    path = Path(base) / "FTBDownloader"
    path.mkdir(parents=True, exist_ok=True)
    return path


#: 状态 → 中文说明（卡片上显示）
STATUS_LABELS = {
    "preparing": "准备中",
    "ready": "已就绪",
    "error": "出错",
}


@dataclass
class LibraryEntry:
    pack_id: int
    version_id: int = 0
    name: str = ""
    version_name: str = ""
    icon_url: str = ""
    status: str = "preparing"
    message: str = ""
    files: int = 0
    cf_mods: int = 0
    size: int = 0
    game_version: str = ""
    loader: str = ""
    java: str = ""
    added_at: float = field(default_factory=time.time)

    @property
    def key(self) -> str:
        """一个整合包在库里只保留一条记录（换版本就覆盖）。"""
        return str(self.pack_id)

    @property
    def status_label(self) -> str:
        if self.status == "error":
            return f"出错：{self.message}" if self.message else "出错"
        if self.status == "preparing" and self.message:
            return self.message
        return STATUS_LABELS.get(self.status, self.status)

    @property
    def subtitle(self) -> str:
        bits = [f"v{self.version_name}"] if self.version_name else []
        if self.game_version:
            bits.append(f"MC {self.game_version}")
        if self.loader:
            bits.append(self.loader)
        if self.files:
            bits.append(f"{self.files:,} 个文件")
        return " · ".join(bits)


class Library:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (data_dir() / "library.json")
        self.entries: dict[str, LibraryEntry] = {}
        self.load()

    # ------------------------------------------------------------------ 读写
    def load(self) -> None:
        self.entries.clear()
        try:
            raw = json.loads(self.path.read_text("utf-8"))
        except (OSError, ValueError):
            return
        for item in raw.get("packs", []):
            try:
                entry = LibraryEntry(**item)
            except TypeError:
                continue
            self.entries[entry.key] = entry

    def save(self) -> None:
        payload = {"packs": [asdict(entry) for entry in self.entries.values()]}
        try:
            self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), "utf-8")
        except OSError:
            pass

    # ------------------------------------------------------------------ 操作
    def get(self, pack_id: int) -> LibraryEntry | None:
        return self.entries.get(str(pack_id))

    def upsert(self, entry: LibraryEntry) -> LibraryEntry:
        self.entries[entry.key] = entry
        self.save()
        return entry

    def remove(self, key: str) -> None:
        if self.entries.pop(key, None) is not None:
            self.save()

    def all(self) -> list[LibraryEntry]:
        return list(self.entries.values())
