"""后台任务：所有网络请求都丢到这里，别阻塞 UI 线程。"""

from __future__ import annotations

import time
from dataclasses import dataclass

from PySide6.QtCore import QThread, Signal

from ftb_downloader.api.ftb import FTBClient
from ftb_downloader.models.manifest import ModpackManifest
from ftb_downloader.models.pack import PackInfo, PackVersion
from ftb_downloader.util import human_rate


class Task(QThread):
    """跑一个函数，把结果 / 异常发回 UI 线程。"""

    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, fn, parent=None) -> None:
        super().__init__(parent)
        self._fn = fn

    def run(self) -> None:
        try:
            result = self._fn()
        except Exception as exc:  # noqa: BLE001 - 统一显示到界面上
            self.failed.emit(f"{type(exc).__name__}: {exc}")
        else:
            self.succeeded.emit(result)


class SearchTask(Task):
    def __init__(self, client: FTBClient, keyword: str, limit: int = 20, parent=None) -> None:
        super().__init__(lambda: client.search(keyword, limit), parent)


class FeaturedTask(QThread):
    """热门整合包：先拿 id 列表，再逐个查信息（参考项目 FTBService.GetFeaturedModpacksAsync 同样做法）。"""

    progress = Signal(int, int)          # 已完成, 总数
    succeeded = Signal(object)           # list[PackInfo]
    failed = Signal(str)

    def __init__(self, client: FTBClient, limit: int = 12, parent=None) -> None:
        super().__init__(parent)
        self.client = client
        self.limit = limit

    def run(self) -> None:
        try:
            ids = self.client.featured_ids(self.limit)[: self.limit]
            packs: list[PackInfo] = []
            for index, pack_id in enumerate(ids, start=1):
                self.progress.emit(index, len(ids))
                packs.append(self.client.info(pack_id))
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(f"{type(exc).__name__}: {exc}")
        else:
            self.succeeded.emit(packs)


@dataclass
class PreparedPack:
    """「准备」完成后的结果：整合包信息 + 选中的版本 + 文件清单。"""

    info: PackInfo
    version: PackVersion
    manifest: ModpackManifest


class PreparePackTask(QThread):
    """拉取整合包信息 + 文件清单。清单有好几 MB，所以汇报进度和速度。"""

    state = Signal(str)                  # 现在在干嘛
    progress = Signal(float, str)        # 0..1, 速度文本（可能为空）
    succeeded = Signal(object)           # PreparedPack
    failed = Signal(str)

    def __init__(self, client: FTBClient, pack_id: int, version_id: int = 0, parent=None) -> None:
        super().__init__(parent)
        self.client = client
        self.pack_id = pack_id
        self.version_id = version_id

    def run(self) -> None:
        try:
            self.state.emit("获取整合包信息")
            info = self.client.info(self.pack_id)
            version = self._pick_version(info)
            if version is None:
                self.failed.emit(f"整合包 {self.pack_id} 没有版本 {self.version_id}")
                return

            self.state.emit("获取文件清单")
            manifest = self.client.manifest(self.pack_id, version.id, on_progress=self._on_progress)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(f"{type(exc).__name__}: {exc}")
            return

        self.succeeded.emit(PreparedPack(info=info, version=version, manifest=manifest))

    def _pick_version(self, info: PackInfo) -> PackVersion | None:
        if self.version_id:
            return next((v for v in info.versions if v.id == self.version_id), None)
        return info.latest_version

    def _on_progress(self, received: int, total: int) -> None:
        now = time.monotonic()
        if not hasattr(self, "_mark"):
            self._mark = (0, now)
            self._rate = ""
        last_bytes, last_time = self._mark
        elapsed = now - last_time
        if elapsed >= 0.5:
            self._rate = human_rate((received - last_bytes) / elapsed)
            self._mark = (received, now)
        ratio = received / total if total else 0.0
        self.progress.emit(min(ratio, 1.0), self._rate)
