"""设置：代理、数据目录、接口参数。"""

from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ftb_downloader.net import system_proxy
from ftb_downloader.services.library import data_dir
from ftb_downloader.ui.widgets.common import Muted, PageTitle


class SettingsPage(QWidget):
    def __init__(self, window) -> None:
        super().__init__(window)
        self.window = window

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 12)
        root.setSpacing(14)
        root.addWidget(PageTitle("设置"))

        form = QFormLayout()
        form.setLabelAlignment(form.labelAlignment())
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(12)

        # 代理
        self.edit_proxy = QLineEdit(self.window.proxy or "")
        self.edit_proxy.setReadOnly(True)
        self.edit_proxy.setPlaceholderText("没有检测到代理（直连）")
        self.edit_proxy.setMinimumWidth(260)
        button_probe = QPushButton("重新探测")
        button_probe.clicked.connect(self._probe)
        proxy_row = QHBoxLayout()
        proxy_row.addWidget(self.edit_proxy, 1)
        proxy_row.addWidget(button_probe)
        form.addRow("系统代理", _wrap(proxy_row))

        # 数据目录
        self.edit_dir = QLineEdit(str(data_dir()))
        self.edit_dir.setReadOnly(True)
        button_open = QPushButton("打开目录")
        button_open.clicked.connect(self._open_dir)
        dir_row = QHBoxLayout()
        dir_row.addWidget(self.edit_dir, 1)
        dir_row.addWidget(button_open)
        form.addRow("数据目录", _wrap(dir_row))

        # 并行下载数（留给下一步的下载器）
        self.spin_threads = QSpinBox()
        self.spin_threads.setRange(1, 32)
        self.spin_threads.setValue(8)
        form.addRow("并行下载数", self.spin_threads)

        root.addLayout(form)
        root.addWidget(
            Muted("代理来自 Windows「Internet 选项」或 HTTP(S)_PROXY 环境变量，跟参考项目 CurseTheBeast 的顺序一致。")
        )
        root.addStretch(1)

    # ------------------------------------------------------------------ 动作
    def _probe(self) -> None:
        proxy = system_proxy()
        self.window.proxy = proxy
        self.window.client.set_proxy(proxy)
        self.edit_proxy.setText(proxy or "")
        self.window.set_status(f"代理：{proxy}" if proxy else "没有检测到代理，直连")

    def _open_dir(self) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(data_dir())))


def _wrap(layout) -> QWidget:
    host = QWidget()
    host.setLayout(layout)
    layout.setContentsMargins(0, 0, 0, 0)
    return host
