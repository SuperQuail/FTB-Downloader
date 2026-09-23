"""主窗口：左侧图标栏 + 顶栏（搜索 / GROUP BY / SORT BY）+ 页面堆栈。

整体布局照着官方 FTB App 来：
    ┌────┬──────────────────────────────────────────────┐
    │ ＋ │  [搜索]                    GROUP BY   SORT BY │
    │ ⬇  ├──────────────────────────────────────────────┤
    │ 🏠 │  正在准备                                     │
    │ ▦  │  ┌─ 大卡片（进度 / 速度）─┐                   │
    │ ⚙  │  我的整合包                                   │
    │ ⓘ  │  ┌─tile─┐ ┌─tile─┐ ┌─tile─┐                  │
    └────┴──────────────────────────────────────────────┘
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ftb_downloader.api.ftb import FTBClient
from ftb_downloader.net import system_proxy
from ftb_downloader.services.library import Library, LibraryEntry
from ftb_downloader.services.tasks import FeaturedTask, PreparedPack, PreparePackTask, SearchTask
from ftb_downloader.ui.image_cache import ImageCache
from ftb_downloader.ui.pages.about import AboutPage
from ftb_downloader.ui.pages.discover import DiscoverPage
from ftb_downloader.ui.pages.downloads import DownloadsPage
from ftb_downloader.ui.pages.library import LibraryPage
from ftb_downloader.ui.pages.settings import SettingsPage
from ftb_downloader.ui.widgets.sidebar import Sidebar
from ftb_downloader.ui.widgets.topbar import TopBar
from ftb_downloader.util import human_size

#: 页面顺序（= QStackedWidget 的下标）
PAGE_ORDER = ["library", "discover", "downloads", "settings", "about"]

#: 左侧栏图标
RAIL_ITEMS = [
    ("add", "plus", "添加整合包（按 ID）"),
    ("downloads", "download", "下载"),
    ("library", "home", "我的整合包"),
    ("discover", "grid", "发现整合包"),
    ("settings", "settings", "设置"),
    ("about", "info", "关于"),
]

SEARCH_PLACEHOLDER = {
    "library": "在库里筛选（名称 / 版本 / ID）",
    "discover": "搜索 FTB 整合包，或直接粘贴整合包 ID",
    "downloads": "搜索 FTB 整合包，或直接粘贴整合包 ID",
    "settings": "搜索 FTB 整合包，或直接粘贴整合包 ID",
    "about": "搜索 FTB 整合包，或直接粘贴整合包 ID",
}


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FTB 整合包下载器")
        self.resize(1180, 760)

        self.proxy = system_proxy()
        self.client = FTBClient(proxy=self.proxy)
        self.library = Library()
        self.image_cache = ImageCache(proxy=self.proxy)

        self._tasks: list = []
        self._preparing: set[int] = set()
        self._featured_loaded = False
        self._current_page = "library"

        self._build_ui()
        self._switch_page("library")
        self.set_status(
            f"代理：{self.proxy}" if self.proxy else "没有检测到代理，直连 FTB 接口"
        )

    # ------------------------------------------------------------- UI 搭建
    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)

        row = QHBoxLayout(central)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)

        self.rail = Sidebar(central)
        for key, icon_name, tooltip in RAIL_ITEMS:
            if key in ("settings",):
                self.rail.add_spacer()
            self.rail.add_item(key, icon_name, tooltip)
        self.rail.selected.connect(self._on_rail)
        row.addWidget(self.rail)

        right = QWidget(central)
        right_box = QVBoxLayout(right)
        right_box.setContentsMargins(0, 0, 0, 0)
        right_box.setSpacing(0)

        self.topbar = TopBar(right)
        self.topbar.search_changed.connect(self._on_search_changed)
        self.topbar.search_submitted.connect(self._on_search_submitted)
        self.topbar.group_changed.connect(self._on_group_changed)
        self.topbar.sort_changed.connect(self._on_sort_changed)
        right_box.addWidget(self.topbar)

        self.stack = QStackedWidget(right)
        right_box.addWidget(self.stack, 1)
        row.addWidget(right, 1)

        self.page_library = LibraryPage(self)
        self.page_discover = DiscoverPage(self)
        self.page_downloads = DownloadsPage(self)
        self.page_settings = SettingsPage(self)
        self.page_about = AboutPage(self)
        for page in (self.page_library, self.page_discover, self.page_downloads, self.page_settings, self.page_about):
            self.stack.addWidget(page)

        self.page_library.card_closed.connect(self.remove_pack)
        self.page_library.tile_clicked.connect(self.show_pack_detail)
        self.page_library.tile_removed.connect(self.remove_pack)
        self.page_downloads.card_closed.connect(self.remove_pack)
        self.page_discover.tile_clicked.connect(self._on_discover_clicked)

        # 下拉框的默认项要跟页面里的默认排序 / 分组一致
        self.page_library.set_group(self.topbar.combo_group.currentData())
        self.page_library.set_sort(self.topbar.combo_sort.currentData())

        self.statusBar().showMessage("就绪")

    # ------------------------------------------------------------- 页面切换
    def _on_rail(self, key: str) -> None:
        if key == "add":
            self._switch_page("discover")
            self.topbar.search.setFocus()
            self.set_status("输入整合包 ID（例如 FTB Skies 2: Aero 是 134）后回车即可添加")
            return
        self._switch_page(key)

    def _switch_page(self, key: str) -> None:
        self._current_page = key
        self.stack.setCurrentIndex(PAGE_ORDER.index(key))
        self.rail.set_current(key)
        self.topbar.set_filters_visible(key == "library")
        self.topbar.set_placeholder(SEARCH_PLACEHOLDER.get(key, ""))
        if key == "library":
            self.page_library.refresh()
        elif key == "downloads":
            self.page_downloads.refresh()
        elif key == "discover":
            self._load_featured()

    # ------------------------------------------------------------- 顶栏行为
    def _on_search_changed(self, text: str) -> None:
        if self._current_page == "library":
            self.page_library.set_filter(text)

    def _on_search_submitted(self, text: str) -> None:
        if not text:
            return
        if text.isdigit():
            self.add_pack(int(text))
            return
        self._switch_page("discover")
        self.page_discover.set_status(f"正在搜索「{text}」……")
        task = SearchTask(self.client, text)
        task.succeeded.connect(lambda packs: self.page_discover.show_summaries(packs, f"「{text}」的搜索结果"))
        task.failed.connect(self._on_task_failed)
        self._track(task)
        task.start()

    def _on_group_changed(self, key: str) -> None:
        self.page_library.set_group(key)

    def _on_sort_changed(self, key: str) -> None:
        self.page_library.set_sort(key)

    # --------------------------------------------------------------- 发现页
    def _load_featured(self) -> None:
        if self._featured_loaded:
            return
        self._featured_loaded = True
        self.page_discover.set_status("正在获取热门整合包……")
        task = FeaturedTask(self.client, 12)
        task.progress.connect(lambda done, total: self.page_discover.set_status(f"正在获取热门整合包 {done}/{total}"))
        task.succeeded.connect(lambda packs: self.page_discover.show_packs(packs, "热门整合包"))
        task.failed.connect(self._on_task_failed)
        self._track(task)
        task.start()

    def _on_discover_clicked(self, key: str) -> None:
        self.add_pack(int(key))

    # --------------------------------------------------------------- 添加包
    def add_pack(self, pack_id: int, version_id: int = 0) -> None:
        if pack_id in self._preparing:
            self.set_status(f"整合包 {pack_id} 已经在处理中了")
            return

        entry = self.library.get(pack_id) or LibraryEntry(pack_id=pack_id)
        entry.status = "preparing"
        entry.message = "获取整合包信息"
        if not entry.name:
            entry.name = f"整合包 {pack_id}"
        self.library.upsert(entry)
        self._refresh_lists()
        self.set_status(f"正在处理「{entry.name}」……")

        task = PreparePackTask(self.client, pack_id, version_id or entry.version_id)
        self._preparing.add(pack_id)
        task.state.connect(lambda text, pid=pack_id: self._on_prepare_state(pid, text))
        task.progress.connect(lambda value, speed, pid=pack_id: self._on_prepare_progress(pid, value, speed))
        task.succeeded.connect(self._on_prepared)
        task.failed.connect(lambda message, pid=pack_id: self._on_prepare_failed(pid, message))
        self._track(task)
        task.start()

    def _refresh_lists(self) -> None:
        self.page_library.refresh()
        self.page_downloads.refresh()

    def _on_prepare_state(self, pack_id: int, text: str) -> None:
        entry = self.library.get(pack_id)
        if entry is not None:
            entry.message = text
            self.library.upsert(entry)
        self._refresh_lists()
        self.set_status(f"{entry.name if entry else pack_id}：{text}")

    def _on_prepare_progress(self, pack_id: int, value: float, speed: str) -> None:
        for page in (self.page_library, self.page_downloads):
            card = page.card(str(pack_id))
            if card is not None:
                card.show_progress(True)
                card.set_progress(value, speed)
                card.set_status(f"下载文件清单 {value * 100:.1f}%")

    def _on_prepared(self, result: PreparedPack) -> None:
        info, version, manifest = result.info, result.version, result.manifest
        entry = self.library.get(info.id) or LibraryEntry(pack_id=info.id)
        loader = manifest.mod_loader
        entry.name = info.name
        entry.version_id = version.id
        entry.version_name = version.name
        entry.icon_url = info.icon_url
        entry.status = "ready"
        entry.message = ""
        entry.files = len(manifest.files)
        entry.cf_mods = len(manifest.curseforge_mods)
        entry.size = manifest.total_size
        entry.game_version = manifest.game_version
        entry.loader = f"{loader.name} {loader.version}" if loader else ""
        entry.java = manifest.java_version
        self.library.upsert(entry)

        self._preparing.discard(info.id)
        self._refresh_lists()
        self.set_status(
            f"「{info.name}」v{version.name} 已就绪：{entry.files:,} 个文件，"
            f"CurseForge 模组 {entry.cf_mods:,} 个，{human_size(entry.size)}"
        )

    def _on_prepare_failed(self, pack_id: int, message: str) -> None:
        entry = self.library.get(pack_id) or LibraryEntry(pack_id=pack_id)
        entry.status = "error"
        entry.message = message
        self.library.upsert(entry)
        self._preparing.discard(pack_id)
        self._refresh_lists()
        self.set_status(f"整合包 {pack_id} 出错：{message}")

    # --------------------------------------------------------------- 其它
    def remove_pack(self, key: str) -> None:
        entry = self.library.entries.get(key)
        if entry is None:
            return
        answer = QMessageBox.question(
            self,
            "移除整合包",
            f"把「{entry.name}」从库里移除？（不会删除已经下载的文件）",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.library.remove(key)
            self._refresh_lists()
            self.set_status(f"已移除「{entry.name}」")

    def show_pack_detail(self, key: str) -> None:
        entry = self.library.entries.get(key)
        if entry is None:
            return
        text = "\n".join(
            [
                f"整合包：{entry.name}（ID {entry.pack_id}）",
                f"版本：{entry.version_name or '-'}（version id {entry.version_id or '-'}）",
                f"运行环境：MC {entry.game_version or '-'} / {entry.loader or '-'} / Java {entry.java or '-'}",
                f"文件：{entry.files:,} 个（其中 CurseForge 模组 {entry.cf_mods:,} 个）",
                f"清单总体积：{human_size(entry.size)}",
                f"状态：{entry.status_label}",
                "",
                "下载与打包还没实现，下一步照参考项目的 FileDownloadService / PackService 来。",
            ]
        )
        QMessageBox.information(self, entry.name or f"整合包 {entry.pack_id}", text)

    def _on_task_failed(self, message: str) -> None:
        self.set_status(f"出错了：{message}")
        QMessageBox.warning(self, "出错了", message)

    def set_status(self, text: str) -> None:
        self.statusBar().showMessage(text)

    def _track(self, task) -> None:
        """留住线程引用，跑完自动清掉（不然会被 GC）。"""
        self._tasks.append(task)

        def _done() -> None:
            if task in self._tasks:
                self._tasks.remove(task)

        task.finished.connect(_done)
