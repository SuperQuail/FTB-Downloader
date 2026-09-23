"""顶栏：搜索框 + GROUP BY / SORT BY（对照 FTB App）。"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ftb_downloader.ui.widgets.common import DarkComboBox, SearchEdit

GROUP_OPTIONS = [("分类", "category"), ("状态", "status"), ("名称", "name")]
SORT_OPTIONS = [("添加时间", "added"), ("名称（A-Z）", "name"), ("体积（大到小）", "size")]


class TopBar(QFrame):
    search_changed = Signal(str)
    search_submitted = Signal(str)
    group_changed = Signal(str)
    sort_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("TopBar")
        self.setFixedHeight(74)

        row = QHBoxLayout(self)
        row.setContentsMargins(18, 10, 18, 12)
        row.setSpacing(18)

        self.search = SearchEdit("搜索整合包，或直接粘贴整合包 ID")
        self.search.setMinimumWidth(300)
        self.search.textChanged.connect(self.search_changed)
        self.search.returnPressed.connect(lambda: self.search_submitted.emit(self.search.text().strip()))
        row.addWidget(self.search, 1)

        self.combo_group = DarkComboBox(GROUP_OPTIONS, icon_name="folder")
        self.combo_sort = DarkComboBox(SORT_OPTIONS, icon_name="sort")
        self.combo_group.currentIndexChanged.connect(
            lambda: self.group_changed.emit(self.combo_group.currentData())
        )
        self.combo_sort.currentIndexChanged.connect(
            lambda: self.sort_changed.emit(self.combo_sort.currentData())
        )

        for caption, combo in (("GROUP BY", self.combo_group), ("SORT BY", self.combo_sort)):
            column = QVBoxLayout()
            column.setSpacing(4)
            label = QLabel(caption)
            label.setObjectName("FilterLabel")
            column.addWidget(label)
            column.addWidget(combo)
            row.addLayout(column)

    def text(self) -> str:
        return self.search.text().strip()

    def set_placeholder(self, text: str) -> None:
        self.search.setPlaceholderText(text)

    def set_filters_visible(self, visible: bool) -> None:
        for combo in (self.combo_group, self.combo_sort):
            combo.setVisible(visible)
            parent = combo.parentWidget()
            if parent is not None:
                parent.setVisible(visible)
