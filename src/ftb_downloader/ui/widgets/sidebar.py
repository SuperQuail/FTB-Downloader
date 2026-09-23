"""左侧图标栏（对照 FTB App 截图：54px 宽、#313131 底、选中项绿底白图标）。"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import QFrame, QToolButton, QVBoxLayout, QWidget

from ftb_downloader.ui import icons, theme


class Sidebar(QFrame):
    selected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Rail")
        self.setFixedWidth(theme.RAIL_WIDTH)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 10, 0, 10)
        self._layout.setSpacing(6)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self._items: dict[str, tuple[QToolButton, str]] = {}

    def add_item(self, key: str, icon_name: str, tooltip: str) -> QToolButton:
        button = QToolButton(self)
        button.setObjectName("RailButton")
        button.setCheckable(True)
        button.setAutoExclusive(True)
        button.setFixedSize(38, 38)
        button.setIconSize(QSize(22, 22))
        button.setIcon(icons.icon(icon_name, theme.TEXT_DIM, 22))
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        if tooltip:
            button.setToolTip(tooltip)
        button.clicked.connect(lambda _checked=False, k=key: self._choose(k))
        self._layout.addWidget(button, 0, Qt.AlignmentFlag.AlignHCenter)
        self._items[key] = (button, icon_name)
        return button

    def add_spacer(self) -> None:
        self._layout.addStretch(1)

    def _choose(self, key: str) -> None:
        self.set_current(key)
        self.selected.emit(key)

    def set_current(self, key: str) -> None:
        for item_key, (button, icon_name) in self._items.items():
            active = item_key == key
            button.setChecked(active)
            button.setIcon(icons.icon(icon_name, theme.TEXT if active else theme.TEXT_DIM, 22))
