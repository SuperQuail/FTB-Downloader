"""发现：搜索 FTB 在线整合包，点卡片加入本地库。"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QScrollArea, QVBoxLayout, QWidget

from ftb_downloader.models.pack import PackInfo, PackSummary
from ftb_downloader.ui.layouts import FlowLayout
from ftb_downloader.ui.widgets.cards import PackTile
from ftb_downloader.ui.widgets.common import Muted, PageTitle


class DiscoverPage(QWidget):
    tile_clicked = Signal(str)

    def __init__(self, window) -> None:
        super().__init__(window)
        self.window = window

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 12)
        root.setSpacing(10)

        root.addWidget(PageTitle("发现整合包"))
        self.hint = Muted("用上面的搜索框搜关键词；输入纯数字（如 134）则直接按整合包 ID 添加。")
        root.addWidget(self.hint)
        self.status = Muted("")
        root.addWidget(self.status)

        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.host = QWidget()
        self.flow = FlowLayout(self.host, 0, 14)
        self.scroll.setWidget(self.host)
        root.addWidget(self.scroll, 1)

        self._loaded_featured = False

    # ------------------------------------------------------------------ 外部
    def set_status(self, text: str) -> None:
        self.status.setText(text)

    def clear(self) -> None:
        while self.flow.count():
            item = self.flow.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    def show_packs(self, packs: list[PackInfo], title: str = "") -> None:
        self._fill([self._summary(pack) for pack in packs], title)

    def show_summaries(self, packs: list[PackSummary], title: str = "") -> None:
        self._fill(packs, title)

    def _fill(self, packs, title: str) -> None:
        self.clear()
        if not packs:
            self.status.setText("没有结果。")
            return
        self.status.setText(title or f"共 {len(packs)} 个结果")
        for pack in packs:
            subtitle = pack.author_text or pack.synopsis
            tile = PackTile(str(pack.id), pack.name, subtitle, pack.icon_url, self.window.image_cache, False, self.host)
            tile.clicked.connect(self.tile_clicked)
            self.flow.addWidget(tile)

    @staticmethod
    def _summary(pack: PackInfo) -> PackSummary:
        return PackSummary(
            id=pack.id,
            name=pack.name,
            synopsis=pack.synopsis,
            authors=pack.authors,
            tags=pack.tags,
            art=pack.art,
        )
