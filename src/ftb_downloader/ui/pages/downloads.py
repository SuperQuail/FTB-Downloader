"""下载中：正在准备 / 下载的整合包（跟主页上半部分是同一批数据）。"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QScrollArea, QVBoxLayout, QWidget

from ftb_downloader.ui.layouts import FlowLayout
from ftb_downloader.ui.widgets.cards import PackCard
from ftb_downloader.ui.widgets.common import Muted, PageTitle


class DownloadsPage(QWidget):
    card_closed = Signal(str)

    def __init__(self, window) -> None:
        super().__init__(window)
        self.window = window

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 12)
        root.setSpacing(10)

        root.addWidget(PageTitle("下载"))
        self.hint = Muted("这里显示正在获取信息 / 清单的整合包。真正的模组下载与打包是下一步的工作。")
        root.addWidget(self.hint)

        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.host = QWidget()
        self.flow = FlowLayout(self.host, 0, 14)
        self.scroll.setWidget(self.host)
        root.addWidget(self.scroll, 1)

        self.refresh()

    def card(self, key: str) -> PackCard | None:
        for index in range(self.flow.count()):
            widget = self.flow.itemAt(index).widget()
            if isinstance(widget, PackCard) and widget.key == key:
                return widget
        return None

    def refresh(self) -> None:
        while self.flow.count():
            item = self.flow.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

        active = [e for e in self.window.library.all() if e.status != "ready"]
        if not active:
            self.flow.addWidget(Muted("现在没有进行中的任务。"))
            return
        for entry in sorted(active, key=lambda e: e.added_at, reverse=True):
            card = PackCard(entry, self.window.image_cache, self.host)
            card.closed.connect(self.card_closed)
            self.flow.addWidget(card)
