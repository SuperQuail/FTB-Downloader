"""主窗口。

界面分三步（对齐参考项目 DefaultCommand 的交互顺序）：
    ① 选整合包（输入 ID）→ ② 选版本 → ③ 选类型（客户端/服务端、标准包/完整包）→ 下载

当前进度：①② 已经能真的调 FTB 接口并把清单读出来；③ 的下载与打包还没写，
   见 README.md 的「下一步」。
"""

from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from ftb_downloader import __version__
from ftb_downloader.api.ftb import FTBClient
from ftb_downloader.models.manifest import ModpackManifest
from ftb_downloader.models.pack import PackInfo
from ftb_downloader.net import system_proxy
from ftb_downloader.util import human_size


class ApiTask(QThread):
    """把可能很慢的接口调用丢到后台线程，避免界面卡死。"""

    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, fn: Callable[[], Any], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._fn = fn

    def run(self) -> None:
        try:
            result = self._fn()
        except Exception as exc:  # noqa: BLE001 - 任何异常都要显示到界面上
            self.failed.emit(f"{type(exc).__name__}: {exc}")
        else:
            self.succeeded.emit(result)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"FTB 整合包下载器 v{__version__}")
        self.resize(900, 680)

        self.proxy = system_proxy()
        self.client = FTBClient(proxy=self.proxy)
        self.client.log = self.log

        self.pack_info: PackInfo | None = None
        self.manifest: ModpackManifest | None = None
        self._task: ApiTask | None = None

        self._build_ui()

        self.log(f"代理：{self.proxy}（来自系统设置/环境变量）" if self.proxy else "代理：未配置，直连")
        self.log("用法：输入整合包 ID（FTB Skies 2: Aero 是 134）→ 获取版本列表 → 选版本 → 读取文件清单")

    # ------------------------------------------------------------- UI 搭建
    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(8)

        # ① 整合包 ID
        box_pack = QGroupBox("① 整合包")
        row_pack = QHBoxLayout(box_pack)
        row_pack.addWidget(QLabel("整合包 ID："))
        self.edit_pack_id = QLineEdit("134")
        self.edit_pack_id.setFixedWidth(110)
        self.edit_pack_id.returnPressed.connect(self.on_fetch_info)
        row_pack.addWidget(self.edit_pack_id)
        self.btn_info = QPushButton("获取版本列表")
        self.btn_info.clicked.connect(self.on_fetch_info)
        row_pack.addWidget(self.btn_info)
        row_pack.addStretch(1)
        root.addWidget(box_pack)

        # 包信息
        self.lbl_pack = QLabel("（还没获取）")
        self.lbl_pack.setWordWrap(True)
        self.lbl_pack.setTextInteractionFlags(Qt.TextSelectableByMouse)
        root.addWidget(self.lbl_pack)

        # ② 版本与类型
        box_ver = QGroupBox("② 版本与类型")
        form = QFormLayout(box_ver)

        self.combo_version = QComboBox()
        self.combo_version.setMinimumWidth(320)
        form.addRow("版本：", self.combo_version)

        type_row = QHBoxLayout()
        self.radio_client = QRadioButton("客户端")
        self.radio_server = QRadioButton("服务端")
        self.radio_client.setChecked(True)
        self.group_side = QButtonGroup(self)
        self.group_side.addButton(self.radio_client)
        self.group_side.addButton(self.radio_server)
        type_row.addWidget(self.radio_client)
        type_row.addWidget(self.radio_server)
        type_row.addSpacing(24)
        self.check_full = QCheckBox("完整包（把 CurseForge 模组也打进 zip）")
        type_row.addWidget(self.check_full)
        type_row.addStretch(1)
        form.addRow("类型：", type_row)

        btn_row = QHBoxLayout()
        self.btn_manifest = QPushButton("读取文件清单")
        self.btn_manifest.clicked.connect(self.on_fetch_manifest)
        btn_row.addWidget(self.btn_manifest)
        self.btn_download = QPushButton("开始下载")
        self.btn_download.setEnabled(False)
        self.btn_download.clicked.connect(self.on_download)
        btn_row.addWidget(self.btn_download)
        btn_row.addStretch(1)
        form.addRow("", btn_row)

        root.addWidget(box_ver)

        # ③ 统计
        box_stats = QGroupBox("③ 清单统计")
        stats_form = QFormLayout(box_stats)
        self.stat_labels: dict[str, QLabel] = {}
        for key, title in (
            ("files", "文件总数"),
            ("client", "客户端文件"),
            ("server", "服务端文件"),
            ("cf_mods", "CurseForge 模组"),
            ("to_download", "需要下载的文件"),
            ("size", "清单总大小"),
            ("runtime", "运行环境"),
        ):
            label = QLabel("-")
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self.stat_labels[key] = label
            stats_form.addRow(f"{title}：", label)
        root.addWidget(box_stats)

        # 日志
        box_log = QGroupBox("日志")
        log_layout = QVBoxLayout(box_log)
        self.text_log = QPlainTextEdit()
        self.text_log.setReadOnly(True)
        self.text_log.setMaximumBlockCount(3000)
        self.text_log.setPlaceholderText("接口调用日志会显示在这里……")
        log_layout.addWidget(self.text_log)
        root.addWidget(box_log, 1)

    # ------------------------------------------------------------- 通用动作
    def log(self, message: str) -> None:
        self.text_log.appendPlainText(message)

    def _set_busy(self, busy: bool) -> None:
        self.btn_info.setEnabled(not busy)
        self.btn_manifest.setEnabled(not busy)
        self.btn_download.setEnabled(not busy and self.manifest is not None)
        _set_busy_cursor(busy)

    def _run(self, fn: Callable[[], Any], on_ok: Callable[[Any], None]) -> None:
        if self._task is not None and self._task.isRunning():
            QMessageBox.information(self, "稍等", "上一个请求还没结束。")
            return
        self._set_busy(True)
        task = ApiTask(fn, self)
        task.succeeded.connect(on_ok)
        task.failed.connect(self._on_failed)
        task.finished.connect(lambda: self._set_busy(False))
        self._task = task
        task.start()

    def _on_failed(self, message: str) -> None:
        self.log(f"[失败] {message}")
        QMessageBox.warning(self, "出错了", message)

    # ------------------------------------------------------------- ① 版本列表
    def on_fetch_info(self) -> None:
        text = self.edit_pack_id.text().strip()
        if not text.isdigit():
            QMessageBox.warning(self, "输入有误", "整合包 ID 必须是数字。")
            return
        pack_id = int(text)

        def work() -> PackInfo:
            return self.client.info(pack_id)

        self._run(work, self._on_info)

    def _on_info(self, info: PackInfo) -> None:
        self.pack_info = info
        self.manifest = None
        self.stat_labels["files"].setText("-")

        authors = "、".join(info.authors) or "未知"
        tags = "、".join(info.tags) or "-"
        self.lbl_pack.setText(
            f"<b>{info.name}</b>（ID {info.id}）<br>"
            f"作者：{authors}　标签：{tags}<br>"
            f"简介：{info.synopsis}<br>"
            f'<a href="{info.url}">{info.url}</a>'
        )
        self.lbl_pack.setOpenExternalLinks(True)

        self.combo_version.clear()
        for version in info.sorted_versions():
            self.combo_version.addItem(version.label, version)
        self.log(f"√ 获取到 {len(info.versions)} 个版本，最新：{info.latest_version.label if info.latest_version else '-'}")

    # ------------------------------------------------------------- ② 文件清单
    def on_fetch_manifest(self) -> None:
        if self.pack_info is None:
            QMessageBox.warning(self, "还没有整合包信息", "先点「获取版本列表」。")
            return
        version = self.combo_version.currentData()
        if version is None:
            QMessageBox.warning(self, "还没有版本", "先点「获取版本列表」。")
            return

        pack_id = self.pack_info.id
        version_id = version.id
        self.log(f"正在拉取清单 {pack_id}/{version_id}（整包几 MB，稍等）……")

        def work() -> ModpackManifest:
            return self.client.manifest(pack_id, version_id)

        self._run(work, self._on_manifest)

    def _on_manifest(self, manifest: ModpackManifest) -> None:
        self.manifest = manifest

        loader = manifest.mod_loader
        runtime = (
            f"MC {manifest.game_version}"
            + (f" / {loader.name} {loader.version}" if loader else "")
            + (f" / Java {manifest.java_version}" if manifest.java_version else "")
        )
        self.stat_labels["files"].setText(f"{len(manifest.files)}")
        self.stat_labels["client"].setText(f"{len(manifest.client_files)}")
        self.stat_labels["server"].setText(f"{len(manifest.server_files)}")
        self.stat_labels["cf_mods"].setText(f"{len(manifest.curseforge_mods)}（标准包交给启动器下载）")
        self.stat_labels["to_download"].setText(f"{len(manifest.local_files)}")
        self.stat_labels["size"].setText(human_size(manifest.total_size))
        self.stat_labels["runtime"].setText(runtime)

        self.log(
            f"√ 清单读取成功：{manifest.name}（{manifest.id}）"
            f"共 {len(manifest.files)} 个文件，其中 CurseForge 模组 {len(manifest.curseforge_mods)} 个"
        )
        self.btn_download.setEnabled(True)

    # ------------------------------------------------------------- ③ 下载
    def on_download(self) -> None:
        QMessageBox.information(
            self,
            "还没实现",
            "下载与打包是下一步的工作。\n\n"
            "要照参考项目补的部分：\n"
            "  • 下载队列 + sha1 校验（FileDownloadService / DownloadQueue）\n"
            "  • CurseForge fileId 校验（CurseforgeService）\n"
            "  • 打成 CurseForge 格式的 zip（PackService / CurseforgeModpackExtensions）",
        )


def _set_busy_cursor(busy: bool) -> None:
    """切换忙碌光标（成对调用，别漏了 restore）。"""
    from PySide6.QtWidgets import QApplication

    if busy:
        QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
    elif QApplication.overrideCursor() is not None:
        QApplication.restoreOverrideCursor()
