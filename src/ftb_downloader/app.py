"""QApplication 引导。

    uv run main.py               正常启动 GUI
    uv run main.py --self-test   只创建窗口然后退出（无显示器 / CI 用，配合 QT_QPA_PLATFORM=offscreen）
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from ftb_downloader import __version__
from ftb_downloader.ui import theme
from ftb_downloader.ui.main_window import MainWindow


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv if argv is None else argv)
    self_test = "--self-test" in args
    args = [arg for arg in args if arg != "--self-test"]

    app = QApplication(args)
    app.setApplicationName("FTB 整合包下载器")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("FTBDownloader")
    theme.apply(app)

    window = MainWindow()
    window.show()

    if self_test:
        app.processEvents()
        print(f"自检通过：主窗口「{window.windowTitle()}」创建成功")
        return 0

    return app.exec()
