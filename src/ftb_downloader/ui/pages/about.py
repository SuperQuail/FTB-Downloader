"""关于。"""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from ftb_downloader import __version__
from ftb_downloader.ui.widgets.common import HLine, Muted, PageTitle


class AboutPage(QWidget):
    def __init__(self, window) -> None:
        super().__init__(window)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 12)
        root.setSpacing(12)

        root.addWidget(PageTitle("关于"))
        root.addWidget(_text(f"FTB 整合包下载器 v{__version__}"))
        root.addWidget(_text(f"Python {sys.version.split()[0]} · {_qt_version()}"))
        root.addWidget(HLine())
        root.addWidget(_text("界面参考官方 FTB App：左侧图标栏 + 搜索 / GROUP BY / SORT BY + 卡片列表。"))
        root.addWidget(_text("接口与打包逻辑参考 C# 项目 CurseTheBeast（已放在仓库的 reference/ 目录，git 忽略）。"))
        root.addWidget(_text("整合包数据来自 api.feed-the-beast.com，模组直链来自 CurseForge CDN。"))
        root.addWidget(HLine())
        root.addWidget(Muted("注意：FTB 现在会把 CurseForge 的 ID 序列化成字符串（\"441647\"），"
                             "本项目所有整数都做了兼容，详见 docs/ftb-api-notes.md。"))
        root.addStretch(1)


def _text(value: str) -> QLabel:
    label = QLabel(value)
    label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    label.setWordWrap(True)
    return label


def _qt_version() -> str:
    from PySide6 import __version__ as pyside_version

    return f"PySide6 {pyside_version}"
