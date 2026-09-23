"""主页（我的整合包）：正在准备的卡片 + 已添加整合包的网格。"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QScrollArea, QVBoxLayout, QWidget

from ftb_downloader.services.library import LibraryEntry
from ftb_downloader.ui.layouts import FlowLayout
from ftb_downloader.ui.widgets.cards import PackCard, PackTile
from ftb_downloader.ui.widgets.common import HLine, Muted, SectionTitle


class LibraryPage(QWidget):
    card_closed = Signal(str)
    tile_clicked = Signal(str)
    tile_removed = Signal(str)

    def __init__(self, window) -> None:
        super().__init__(window)
        self.window = window
        self._filter = ""
        self._sort = "added"
        self._group = "category"

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 12)
        root.setSpacing(12)

        # ---------------------------------------------------------- 正在准备
        self.preparing_row = QWidget(self)
        preparing_layout = QHBoxLayout(self.preparing_row)
        preparing_layout.setContentsMargins(0, 0, 0, 0)
        self.preparing_title = SectionTitle("正在准备")
        preparing_layout.addWidget(self.preparing_title)
        preparing_layout.addStretch(1)
        self.preparing_hint = Muted("")
        preparing_layout.addWidget(self.preparing_hint)
        root.addWidget(self.preparing_row)

        self.cards_host = QWidget(self)
        self.cards_flow = FlowLayout(self.cards_host, 0, 14)
        root.addWidget(self.cards_host)

        self.separator = HLine()
        root.addWidget(self.separator)

        # ---------------------------------------------------------- 我的整合包
        list_row = QWidget(self)
        list_layout = QHBoxLayout(list_row)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.addWidget(SectionTitle("我的整合包"))
        list_layout.addStretch(1)
        self.count_label = Muted("")
        list_layout.addWidget(self.count_label)
        root.addWidget(list_row)

        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.content_host = QWidget()
        self.content_box = QVBoxLayout(self.content_host)
        self.content_box.setContentsMargins(0, 0, 0, 0)
        self.content_box.setSpacing(14)
        self.scroll.setWidget(self.content_host)
        root.addWidget(self.scroll, 1)

        self.refresh()

    # ------------------------------------------------------------------ 外部
    def set_filter(self, text: str) -> None:
        self._filter = text.strip().lower()
        self.refresh()

    def set_sort(self, key: str) -> None:
        self._sort = key or "added"
        self.refresh()

    def set_group(self, key: str) -> None:
        self._group = key or "category"
        self.refresh()

    # ------------------------------------------------------------------ 刷新
    def refresh(self) -> None:
        entries = self.window.library.all()
        preparing = [e for e in entries if e.status != "ready"]
        ready = self._visible([e for e in entries if e.status == "ready"])

        # 正在准备区
        _clear(self.cards_flow)
        for entry in sorted(preparing, key=lambda e: e.added_at, reverse=True):
            card = PackCard(entry, self.window.image_cache, self.cards_host)
            card.closed.connect(self.card_closed)
            self.cards_flow.addWidget(card)
        has_preparing = bool(preparing)
        self.preparing_row.setVisible(has_preparing)
        self.cards_host.setVisible(has_preparing)
        self.separator.setVisible(has_preparing)
        if has_preparing:
            self.preparing_hint.setText(f"{len(preparing)} 个整合包正在处理")

        # 我的整合包
        self.count_label.setText(f"共 {len(ready)} 个" if ready else "")
        _clear(self.content_box)
        if not entries:
            self.content_box.addWidget(
                Muted("库还是空的：点左侧 ➕ 或「发现」搜一个整合包，也可以直接把整合包 ID 粘到上面的搜索框。")
            )
        elif not ready:
            self.content_box.addWidget(Muted("没有符合筛选条件的整合包。"))
        else:
            for title, group in self._grouped(ready):
                section = QWidget(self.content_host)
                box = QVBoxLayout(section)
                box.setContentsMargins(0, 0, 0, 0)
                box.setSpacing(10)
                if title:
                    box.addWidget(SectionTitle(title))
                grid_host = QWidget(section)
                grid = FlowLayout(grid_host, 0, 14)
                for entry in group:
                    tile = PackTile.from_entry(entry, self.window.image_cache, grid_host)
                    tile.clicked.connect(self.tile_clicked)
                    tile.remove_requested.connect(self.tile_removed)
                    grid.addWidget(tile)
                box.addWidget(grid_host)
                self.content_box.addWidget(section)
        self.content_box.addStretch(1)

    def card(self, key: str) -> PackCard | None:
        """按 key 找「正在准备」的卡片（进度回调要就地更新它）。"""
        for index in range(self.cards_flow.count()):
            widget = self.cards_flow.itemAt(index).widget()
            if isinstance(widget, PackCard) and widget.key == key:
                return widget
        return None

    # ------------------------------------------------------------------ 内部
    def _visible(self, entries: list[LibraryEntry]) -> list[LibraryEntry]:
        if self._filter:
            entries = [
                e
                for e in entries
                if self._filter in (e.name or "").lower()
                or self._filter in (e.version_name or "").lower()
                or self._filter in str(e.pack_id)
            ]
        if self._sort == "name":
            entries.sort(key=lambda e: (e.name or "").lower())
        elif self._sort == "size":
            entries.sort(key=lambda e: e.size, reverse=True)
        else:
            entries.sort(key=lambda e: e.added_at, reverse=True)
        return entries

    def _grouped(self, entries: list[LibraryEntry]) -> list[tuple[str, list[LibraryEntry]]]:
        if self._group == "name":
            return [("", entries)]
        if self._group == "status":
            buckets: dict[str, list[LibraryEntry]] = {}
            for entry in entries:
                buckets.setdefault(entry.status_label, []).append(entry)
            return [(key, value) for key, value in buckets.items()]
        buckets = {}
        for entry in entries:
            key = f"Minecraft {entry.game_version}" if entry.game_version else "未知版本"
            buckets.setdefault(key, []).append(entry)
        return sorted(buckets.items(), key=lambda kv: kv[0], reverse=True)


def _clear(layout) -> None:
    """把布局里的控件全部删掉（refresh 时重建）。"""
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.setParent(None)
            widget.deleteLater()
