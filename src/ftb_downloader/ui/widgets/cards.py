"""整合包卡片：大卡片（准备中/下载中）与网格卡片（库 / 搜索结果）。"""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QAction, QColor, QFontMetrics, QPainter, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from ftb_downloader.services.library import LibraryEntry
from ftb_downloader.ui import icons, theme
from ftb_downloader.ui.image_cache import ImageCache
from ftb_downloader.ui.widgets.common import IconButton, Muted, SpeedChip


def make_placeholder(size: int, radius: int = 8) -> QPixmap:
    """没有封面时用的占位图：深灰圆角块 + 中间的箱子图标。"""
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(theme.BG_HOVER))
    painter.drawRoundedRect(QRectF(0, 0, size, size), radius, radius)
    inner = int(size * 0.55)
    painter.drawPixmap(int((size - inner) / 2), int((size - inner) / 2), icons.pixmap("box", theme.TEXT_MUTED, inner))
    painter.end()
    return pixmap


class _CoverLabel(QLabel):
    """会自己找封面、找不到先用占位图的方形封面。"""

    def __init__(self, size: int, radius: int, cache: ImageCache, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._size = size
        self._radius = radius
        self._cache = cache
        self._url = ""
        self._placeholder = make_placeholder(size, radius)
        self.setFixedSize(size, size)
        self.setPixmap(self._placeholder)
        cache.loaded.connect(self._on_loaded)

    def set_url(self, url: str) -> None:
        if url == self._url:
            return
        self._url = url
        self._refresh()

    def _refresh(self) -> None:
        pixmap = self._cache.peek(self._url)
        self.setPixmap(self._placeholder if pixmap is None else icons.rounded(pixmap, self._size, self._radius))

    def _on_loaded(self, url: str) -> None:
        if url == self._url:
            self._refresh()


class PackCard(QFrame):
    """「准备中 / 下载中」用的大卡片：封面 + 名称 + 状态 + 百分比 + 进度条 + 速度。"""

    closed = Signal(str)

    def __init__(self, entry: LibraryEntry, cache: ImageCache, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("PackCard")
        self.key = entry.key
        self.setMinimumWidth(360)
        self.setFixedHeight(150)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 14)
        root.setSpacing(10)

        head = QHBoxLayout()
        head.setSpacing(12)
        self.cover = _CoverLabel(46, 8, cache)
        head.addWidget(self.cover)

        titles = QVBoxLayout()
        titles.setSpacing(2)
        self.title = QLabel(entry.name or f"整合包 {entry.pack_id}")
        self.title.setObjectName("PackTitle")
        self.status = QLabel(entry.status_label)
        self.status.setObjectName("PackStatus")
        titles.addWidget(self.title)
        titles.addWidget(self.status)
        head.addLayout(titles, 1)

        self.close_button = IconButton("close", "移除", theme.TEXT_MUTED, 14)
        self.close_button.clicked.connect(lambda: self.closed.emit(self.key))
        head.addWidget(self.close_button, 0, Qt.AlignmentFlag.AlignTop)
        root.addLayout(head)

        foot = QHBoxLayout()
        foot.setSpacing(10)
        self.percent = QLabel("")
        self.percent.setObjectName("PackPercent")
        foot.addWidget(self.percent)
        foot.addStretch(1)
        self.speed = SpeedChip()
        foot.addWidget(self.speed)
        root.addLayout(foot)

        self.progress = QProgressBar()
        self.progress.setObjectName("PackProgress")
        self.progress.setRange(0, 1000)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        root.addWidget(self.progress)
        # 进度条隐藏时（出错 / 就绪）让多出来的空间留到底部，内容保持顶对齐
        root.addStretch(1)

        self.update_from(entry)

    # ------------------------------------------------------------------ 更新
    def update_from(self, entry: LibraryEntry) -> None:
        self.title.setText(entry.name or f"整合包 {entry.pack_id}")
        self.status.setText(entry.status_label)
        color = theme.DANGER if entry.status == "error" else theme.TEXT_DIM
        self.status.setStyleSheet(f"color: {color}; background: transparent;")
        self.cover.set_url(entry.icon_url)
        # 只有「准备中」才显示百分比 + 进度条，出错 / 就绪时别摆一个空槽
        self.show_progress(entry.status == "preparing")

    def set_progress(self, value: float, speed: str = "") -> None:
        self.progress.setValue(int(max(0.0, min(value, 1.0)) * 1000))
        self.percent.setText(f"{value * 100:.1f} %")
        self.speed.set_text(speed)

    def set_status(self, text: str) -> None:
        self.status.setText(text)

    def show_progress(self, visible: bool) -> None:
        self.percent.setVisible(visible)
        self.progress.setVisible(visible)
        if not visible:
            self.speed.set_text("")


class PackTile(QFrame):
    """网格卡片：封面 + 名称 + 一行摘要。可点击；``removable`` 时右键能移除。"""

    clicked = Signal(str)
    remove_requested = Signal(str)

    WIDTH = 172
    HEIGHT = 200

    def __init__(
        self,
        key: str,
        name: str,
        subtitle: str,
        icon_url: str,
        cache: ImageCache,
        removable: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("PackTile")
        self.key = key
        self._removable = removable
        self._tooltip = f"{name}\n{subtitle}"
        self.setFixedSize(self.WIDTH, self.HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(self._tooltip)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        self.cover = _CoverLabel(96, 10, cache)
        root.addWidget(self.cover, 0, Qt.AlignmentFlag.AlignHCenter)

        self.title = QLabel()
        self.title.setObjectName("TileTitle")
        root.addWidget(self.title)

        self.subtitle = Muted()
        self.subtitle.setWordWrap(False)
        root.addWidget(self.subtitle)
        root.addStretch(1)

        self.set_text(name, subtitle, icon_url)

    def set_text(self, name: str, subtitle: str, icon_url: str) -> None:
        self.title.setText(QFontMetrics(self.title.font()).elidedText(name, Qt.TextElideMode.ElideRight, self.WIDTH - 34))
        self.subtitle.setText(
            QFontMetrics(self.subtitle.font()).elidedText(subtitle, Qt.TextElideMode.ElideRight, self.WIDTH - 26)
        )
        self.cover.set_url(icon_url)
        self.setToolTip(f"{name}\n{subtitle}")

    @classmethod
    def from_entry(cls, entry: LibraryEntry, cache: ImageCache, parent: QWidget | None = None) -> PackTile:
        tile = cls(entry.key, entry.name or f"整合包 {entry.pack_id}", entry.subtitle, entry.icon_url, cache, True, parent)
        tile._tooltip = f"{entry.name}\n{entry.subtitle}\n状态：{entry.status_label}"
        tile.setToolTip(tile._tooltip)
        return tile

    # ------------------------------------------------------------------ 交互
    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
            self.clicked.emit(self.key)
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event) -> None:  # noqa: N802
        if not self._removable:
            return
        menu = QMenu(self)
        menu.setStyleSheet(
            f"QMenu {{ background-color: {theme.BG_MENU}; color: {theme.TEXT_DIM}; border: 1px solid {theme.BORDER}; }}"
            f"QMenu::item {{ padding: 6px 18px; }}"
            f"QMenu::item:selected {{ background-color: {theme.ACCENT}; color: #ffffff; }}"
        )
        action = QAction("从库中移除", menu)
        action.triggered.connect(lambda: self.remove_requested.emit(self.key))
        menu.addAction(action)
        menu.exec(event.globalPos())
