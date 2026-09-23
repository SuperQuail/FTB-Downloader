"""整合包信息 / 版本 / 搜索结果。

对照参考项目 CurseTheBeast/Api/FTB/Model/ModpackInfo.cs 与 ModpackSearchResult.cs。
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from ftb_downloader.models.manifest import as_int

#: 版本类型 → 中文（对照 DefaultCommand.selectVersions 的显示逻辑）
TYPE_LABELS = {
    "release": "正式版",
    "beta": "测试版",
    "alpha": "BUG 版",
    "archived": "已归档",
}


@dataclass(slots=True)
class Art:
    """封面图。type 常见值：square（正方形图标）、splash（横幅）。"""

    url: str
    type: str = ""
    width: int = 0
    height: int = 0

    @classmethod
    def from_json(cls, data: Mapping[str, Any]) -> Art:
        return cls(
            url=str(data.get("url") or ""),
            type=str(data.get("type") or ""),
            width=as_int(data.get("width")),
            height=as_int(data.get("height")),
        )


def pick_icon_url(arts: list[Art]) -> str:
    """优先正方形图标，其次任意一张。"""
    for art in arts:
        if art.type == "square" and art.url:
            return art.url
    for art in arts:
        if art.url:
            return art.url
    return ""


@dataclass(slots=True)
class PackVersion:
    id: int
    name: str
    type: str
    updated: int

    @classmethod
    def from_json(cls, data: Mapping[str, Any]) -> PackVersion:
        return cls(
            id=as_int(data.get("id")),
            name=str(data.get("name") or ""),
            type=str(data.get("type") or ""),
            updated=as_int(data.get("updated")),
        )

    @property
    def type_label(self) -> str:
        return TYPE_LABELS.get(self.type.lower(), self.type or "未知")

    @property
    def label(self) -> str:
        return f"{self.name}（{self.type_label}，id={self.id}）"


@dataclass(slots=True)
class PackInfo:
    """GET /modpack/{packId}"""

    id: int
    name: str
    synopsis: str
    description: str
    authors: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    versions: list[PackVersion] = field(default_factory=list)
    art: list[Art] = field(default_factory=list)
    installs: int = 0
    plays: int = 0
    updated: int = 0

    @classmethod
    def from_json(cls, data: Mapping[str, Any]) -> PackInfo:
        return cls(
            id=as_int(data.get("id")),
            name=str(data.get("name") or ""),
            synopsis=str(data.get("synopsis") or ""),
            description=str(data.get("description") or ""),
            authors=[str(a.get("name") or "") for a in data.get("authors") or []],
            tags=[str(t.get("name") or "") for t in data.get("tags") or []],
            art=[Art.from_json(a) for a in data.get("art") or []],
            versions=[PackVersion.from_json(v) for v in data.get("versions") or []],
            installs=as_int(data.get("installs")),
            plays=as_int(data.get("plays")),
            updated=as_int(data.get("updated")),
        )

    @property
    def url(self) -> str:
        return f"https://www.feed-the-beast.com/modpacks/{self.id}"

    @property
    def icon_url(self) -> str:
        return pick_icon_url(self.art)

    @property
    def author_text(self) -> str:
        return "、".join(a for a in self.authors if a)

    @property
    def latest_version(self) -> PackVersion | None:
        return max(self.versions, key=lambda v: v.id, default=None)

    def sorted_versions(self) -> list[PackVersion]:
        """新版本在前（对照 DefaultCommand.selectVersions）。"""
        return sorted(self.versions, key=lambda v: v.id, reverse=True)


@dataclass(slots=True)
class PackSummary:
    """搜索结果里的一项（比 PackInfo 少很多字段）。"""

    id: int
    name: str
    synopsis: str
    authors: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    art: list[Art] = field(default_factory=list)

    @classmethod
    def from_json(cls, data: Mapping[str, Any]) -> PackSummary:
        return cls(
            id=as_int(data.get("id")),
            name=str(data.get("name") or ""),
            synopsis=str(data.get("synopsis") or ""),
            authors=[str(a.get("name") or "") for a in data.get("authors") or []],
            tags=[str(t.get("name") or "") for t in data.get("tags") or []],
            art=[Art.from_json(a) for a in data.get("art") or []],
        )

    @property
    def label(self) -> str:
        return f"{self.name}（{self.id}）"

    @property
    def icon_url(self) -> str:
        return pick_icon_url(self.art)

    @property
    def author_text(self) -> str:
        return "、".join(a for a in self.authors if a)
