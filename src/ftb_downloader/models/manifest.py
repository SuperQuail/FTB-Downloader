"""FTB 整合包清单（manifest）模型。

对照参考项目：
  * CurseTheBeast/Api/FTB/Model/ModpackManifest.cs  —— 字段定义
  * CurseTheBeast/Services/Model/FTBFileEntry.cs     —— 包内路径、下载直链算法
  * CurseTheBeast/Utils/CurseforgeUtils.cs           —— CurseForge CDN 直链规则

⚠ 已知坑（本项目就是被它坑出来的）：FTB 现在把 CurseForge 的 ID 序列化成字符串
   （"441647"），老数据里是数字。参考项目的 C# 模型写的是 long，于是整份清单在
   第一条带 curseforge 的条目处解析失败，11429 个文件全部报废。
   这里所有整数统一走 as_int()，两种形式都能吃。
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import quote

#: CurseForge CDN 直链规则（CurseforgeUtils.GetDownloadUrl）
CF_CDN = "https://edge.forgecdn.net/files/{a}/{b}/{name}"

#: 官方 CurseForge 项目页
CF_PROJECT_PAGE = "https://www.curseforge.com/projects/{project_id}"


def as_int(value: Any, default: int = 0) -> int:
    """把 JSON 里的数字 / 数字字符串统一转成 int。"""
    if value is None:
        return default
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = str(value).strip()
    if not text:
        return default
    try:
        return int(text)
    except ValueError:
        return int(float(text))


def normalize_entry_name(*parts: str | None) -> str:
    """拼出包内相对路径。算法对照修好之后的 FileEntry.WithArchiveEntryName()：

    统一分隔符 → 把每段按 '/' 拆开 → 丢掉空段和 "." 段。

    ⚠ 两个必须守住的点（本项目就是被它们坑出来的）：
      1. 绝对不能产出空路径段。FTB 清单里 path="./" 的条目（例如
         default-server.properties）会拼出 "overrides//default-server.properties"，
         启动器剥掉 "overrides/" 前缀后拿到的是 "/default-server.properties"，
         在 Java 里这是绝对路径，HMCL 的 zip-slip 检查会直接抛
         IOException: Zip entry is trying to write outside of the destination directory，
         整个整合包装不上。
      2. 不能用 lstrip(".") 去前缀。它会把 ".gitkeep" 改名成 "gitkeep"，
         点号开头的文件/目录全都会走样。
    """
    segments: list[str] = []
    for part in parts:
        if not part or not part.strip():
            continue
        for segment in part.replace("\\", "/").split("/"):
            if segment and segment != ".":
                segments.append(segment)
    return "/".join(segments)


def validate_entry_name(entry_name: str) -> str:
    """校验包内条目名，合法就原样返回，否则抛 ValueError。

    空段、"."/".." 段、首尾斜杠都属于非法：这类条目要么被启动器的 zip-slip
    检查拒绝（HMCL），要么被解压到目标目录之外。写包之前务必过一遍，
    别再把装不上的整合包发出去。
    """
    segments = entry_name.split("/")
    if (
        not entry_name
        or entry_name.startswith("/")
        or entry_name.endswith("/")
        or any(segment in ("", ".", "..") for segment in segments)
    ):
        raise ValueError(f"非法的压缩包条目名：{entry_name!r}")
    return entry_name


@dataclass(slots=True)
class CurseforgeRef:
    """清单里的 curseforge 引用：project = projectId，file = fileId。"""

    project: int = 0
    file: int = 0

    @classmethod
    def from_json(cls, data: Mapping[str, Any] | None) -> CurseforgeRef | None:
        if not data:
            return None
        return cls(project=as_int(data.get("project")), file=as_int(data.get("file")))

    @property
    def page(self) -> str:
        return CF_PROJECT_PAGE.format(project_id=self.project)


@dataclass(slots=True)
class ManifestFile:
    """清单 files[] 里的一项。"""

    id: int
    name: str
    path: str
    type: str
    sha1: str
    size: int
    url: str | None
    client_only: bool
    server_only: bool
    optional: bool
    curseforge: CurseforgeRef | None

    @classmethod
    def from_json(cls, data: Mapping[str, Any]) -> ManifestFile:
        return cls(
            id=as_int(data.get("id")),
            name=str(data.get("name") or ""),
            path=str(data.get("path") or ""),
            type=str(data.get("type") or ""),
            sha1=str(data.get("sha1") or ""),
            size=as_int(data.get("size")),
            url=str(data["url"]) if data.get("url") else None,
            client_only=bool(data.get("clientonly")),
            server_only=bool(data.get("serveronly")),
            optional=bool(data.get("optional")),
            curseforge=CurseforgeRef.from_json(data.get("curseforge")),
        )

    @property
    def archive_entry(self) -> str:
        """包内相对路径，例如 mods/xxx.jar。"""
        entry = normalize_entry_name(self.path, self.name)
        if entry.lower().startswith("mods/") and entry.lower().endswith(".jar.disabled"):
            entry = entry[: -len(".disabled")]
        return entry

    @property
    def download_url(self) -> str:
        """FTB 自带直链优先，没有就按 CurseForge 规则拼。"""
        if self.url:
            return self.url
        if self.curseforge is not None and self.curseforge.file > 0:
            return CF_CDN.format(
                a=self.curseforge.file // 1000,
                b=self.curseforge.file % 1000,
                name=quote(self.name),
            )
        return ""

    @property
    def side(self) -> str:
        """client / server / both（对照 FTBFileEntry.Side）。"""
        if self.server_only:
            return "server"
        if self.client_only:
            return "client"
        return "both"

    @property
    def is_curseforge_mod(self) -> bool:
        """是不是「交给启动器从 CurseForge 下载」的模组。"""
        return self.curseforge is not None and self.archive_entry.lower().startswith("mods/")

    @property
    def target_dir(self) -> str:
        entry = self.archive_entry
        head, _, _ = entry.rpartition("/")
        return head


@dataclass(slots=True)
class Specs:
    minimum: int = 0
    recommended: int = 0

    @classmethod
    def from_json(cls, data: Mapping[str, Any] | None) -> Specs:
        data = data or {}
        return cls(minimum=as_int(data.get("minimum")), recommended=as_int(data.get("recommended")))


@dataclass(slots=True)
class Target:
    name: str
    type: str
    version: str

    @classmethod
    def from_json(cls, data: Mapping[str, Any]) -> Target:
        return cls(
            name=str(data.get("name") or ""),
            type=str(data.get("type") or ""),
            version=str(data.get("version") or ""),
        )


@dataclass(slots=True)
class ModpackManifest:
    """GET /modpack/{packId}/{versionId} 的响应体。"""

    id: int
    name: str
    type: str
    parent: int
    installs: int
    plays: int
    updated: int
    files: list[ManifestFile]
    specs: Specs
    targets: list[Target] = field(default_factory=list)

    @classmethod
    def from_json(cls, data: Mapping[str, Any]) -> ModpackManifest:
        return cls(
            id=as_int(data.get("id")),
            name=str(data.get("name") or ""),
            type=str(data.get("type") or ""),
            parent=as_int(data.get("parent")),
            installs=as_int(data.get("installs")),
            plays=as_int(data.get("plays")),
            updated=as_int(data.get("updated")),
            files=[ManifestFile.from_json(item) for item in data.get("files") or []],
            specs=Specs.from_json(data.get("specs")),
            targets=[Target.from_json(item) for item in data.get("targets") or []],
        )

    # ------------------------------------------------------------------ 分组
    # 对照 FTBService.GetModpackAsync()：客户端/服务端，以及「标准包」要排除的
    # CurseForge 模组（它们由启动器按 manifest.json 自己去下）。

    @property
    def client_files(self) -> list[ManifestFile]:
        return [f for f in self.files if f.side in ("client", "both")]

    @property
    def server_files(self) -> list[ManifestFile]:
        return [f for f in self.files if f.side in ("server", "both")]

    @property
    def curseforge_mods(self) -> list[ManifestFile]:
        return [f for f in self.client_files if f.is_curseforge_mod]

    @property
    def local_files(self) -> list[ManifestFile]:
        """「标准包」里需要打进包里、需要自己下载的文件。"""
        return [f for f in self.client_files if not f.is_curseforge_mod]

    @property
    def total_size(self) -> int:
        return sum(f.size for f in self.files)

    # ------------------------------------------------------------- 运行环境
    def target(self, type_: str) -> Target | None:
        for item in self.targets:
            if item.type.lower() == type_.lower():
                return item
        return None

    @property
    def game_version(self) -> str:
        item = self.target("game")
        return item.version if item else ""

    @property
    def mod_loader(self) -> Target | None:
        return self.target("modloader")

    @property
    def java_version(self) -> str:
        item = self.target("runtime")
        return item.version if item else ""
