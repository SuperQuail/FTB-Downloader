"""通用小部件：分节标题、深色下拉框、带放大镜的搜索框、速度胶囊。"""

from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import QComboBox, QFrame, QLabel, QLineEdit, QPushButton, QWidget

from ftb_downloader.ui import icons, theme


class SectionTitle(QLabel):
    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("SectionTitle")


class PageTitle(QLabel):
    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("PageTitle")


class Muted(QLabel):
    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("Muted")
        self.setWordWrap(True)


class SearchEdit(QLineEdit):
    """带放大镜图标的搜索框（图标是子控件，跟着 resize 走）。"""

    def __init__(self, placeholder: str = "搜索", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("SearchEdit")
        self.setPlaceholderText(placeholder)
        self.setFixedHeight(theme.CONTROL_HEIGHT)
        self.setClearButtonEnabled(False)

        self._icon = QLabel(self)
        self._icon.setObjectName("SearchIcon")
        self._icon.setPixmap(icons.pixmap("search", theme.TEXT_MUTED, 16))
        self._icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._icon.adjustSize()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._icon.move(11, (self.height() - self._icon.height()) // 2)


class DarkComboBox(QComboBox):
    """自绘下拉框：``#2a2a2a`` 底 + 1px 描边 + 右侧雪佛龙，样式跟 FTB App 一致。"""

    def __init__(
        self,
        items: list[tuple[str, str]] | None = None,
        icon_name: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._icon_name = icon_name
        self.setFixedHeight(theme.CONTROL_HEIGHT)
        self.setMinimumWidth(150)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        for label, value in items or []:
            self.addItem(label, value)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        painter.setPen(QPen(QColor(theme.BORDER), 1))
        painter.setBrush(QColor(theme.BG))
        painter.drawRoundedRect(rect, theme.RADIUS, theme.RADIUS)

        left = rect.left() + 10
        if self._icon_name:
            painter.drawPixmap(int(left), int(rect.center().y() - 8), icons.pixmap(self._icon_name, theme.TEXT_DIM, 16))
            left += 22

        painter.setPen(QColor(theme.TEXT))
        text_rect = QRectF(left, rect.top(), max(rect.width() - (left - rect.left()) - 28, 10), rect.height())
        painter.drawText(
            text_rect,
            int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
            self.currentText(),
        )

        painter.drawPixmap(
            int(rect.right() - 25),
            int(rect.center().y() - 8),
            icons.pixmap("chevron-down", theme.TEXT_DIM, 16),
        )
        painter.end()


class IconButton(QPushButton):
    """只有图标的扁平按钮。"""

    def __init__(
        self,
        icon_name: str,
        tooltip: str = "",
        color: str = theme.TEXT_MUTED,
        size: int = 16,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("Ghost")
        self.setIcon(icons.icon(icon_name, color, size))
        self.setIconSize(QSize(size, size))
        self.setFixedSize(size + 14, size + 14)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if tooltip:
            self.setToolTip(tooltip)


class SpeedChip(QWidget):
    """深色胶囊：⚡ 1.2 MB/s（自绘，省得跟样式表打架）。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._text = ""
        self.setFixedHeight(22)
        self.setVisible(False)

    def set_text(self, text: str) -> None:
        self._text = text or ""
        self.setVisible(bool(self._text))
        self.updateGeometry()
        self.update()

    def sizeHint(self) -> QSize:  # noqa: N802
        width = 30 + QFontMetrics(self.font()).horizontalAdvance(self._text) + 10
        return QSize(width, 22)

    def paintEvent(self, event) -> None:  # noqa: N802
        if not self._text:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect())
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(theme.BG_HOVER))
        painter.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)
        painter.drawPixmap(8, int(rect.center().y() - 6), icons.pixmap("bolt", theme.TEXT, 12))
        painter.setPen(QColor(theme.TEXT))
        painter.drawText(
            rect.adjusted(24, 0, -10, 0),
            int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
            self._text,
        )
        painter.end()


class HLine(QFrame):
    """一条 1px 分隔线。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(1)
        self.setStyleSheet(f"background-color: {theme.BORDER_SOFT};")
