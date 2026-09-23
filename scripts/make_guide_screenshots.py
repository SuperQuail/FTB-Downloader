r"""生成使用指导（docs/usage.md）里的截图 → docs/guide/*.png。

    uv run python scripts\\make_guide_screenshots.py

几点说明：

* **数据是真的**：热门列表、整合包信息、完整文件清单都现场从 FTB 接口拉，
  所以需要能访问外网（会走系统代理），整轮跑下来大约几分钟。
* **不动你的库**：把 LOCALAPPDATA 指到临时目录，不会碰
  %LOCALAPPDATA%\\FTBDownloader\\library.json。
* **不打扰你**：窗口会被挪到屏幕外。用 offscreen 平台的话字体渲染不出来，
  文字会变成方框，所以只能用原生平台。
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

#: 设置页那张截图要显示用户真实的库路径，所以先把真实路径记下来，再去改 LOCALAPPDATA
_REAL_DATA_DIR = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "FTBDownloader"

# 必须在导入 ftb_downloader.services.library 之前改，库才会落到临时目录
_TEMP_HOME = tempfile.mkdtemp(prefix="ftb-guide-")
os.environ["LOCALAPPDATA"] = _TEMP_HOME
os.environ.pop("QT_QPA_PLATFORM", None)  # offscreen 平台没有字体，渲染出来全是方框

from PySide6.QtCore import QEvent, QPoint, QRect, Qt, QTimer  # noqa: E402
from PySide6.QtGui import QColor, QFont, QPainter, QPen  # noqa: E402
from PySide6.QtWidgets import QApplication, QMessageBox  # noqa: E402

from ftb_downloader.ui import theme  # noqa: E402
from ftb_downloader.ui.main_window import MainWindow  # noqa: E402
from ftb_downloader.ui.widgets.cards import PackTile  # noqa: E402

OUT = ROOT / "docs" / "guide"

#: 截图用的窗口逻辑尺寸（屏幕是 150% 缩放，实际出图 1920x1200）
WINDOW_SIZE = (1280, 800)

#: 演示用的整合包（挑的都是 FTB 上真实存在、运行环境各异的）
DEMO_PACKS = [134, 127, 130, 132]
EXTRA_PACK = 120


# --------------------------------------------------------------------------- 工具
def wait_for(app, predicate, timeout: float, label: str, poll: float = 0.03) -> bool:
    """边跑事件循环边等条件成立。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        app.processEvents()
        if predicate():
            return True
        time.sleep(poll)
    print(f"    !! 超时：{label}")
    return False


def settle(app, window, image_timeout: float = 25.0) -> None:
    """等封面下载完，再让 Qt 把布局和绘制都跑一轮。"""
    cache = window.image_cache
    deadline = time.time() + image_timeout
    while time.time() < deadline and cache._pending:  # noqa: SLF001 - 就是等它把封面拉完
        app.processEvents()
        time.sleep(0.05)
    end = time.time() + 0.8
    while time.time() < end:
        app.processEvents()
        time.sleep(0.03)


def widget_rect(window, widget) -> QRect:
    return QRect(widget.mapTo(window, QPoint(0, 0)), widget.size())


def annotate(pixmap, window, marks) -> None:
    """在截图上的控件旁边画编号圈，方便对着文档看。

    marks 里每项是 (编号, 控件或矩形, 角) —— 角取 tl/tr/bl/br，决定编号圈压在方框的哪个角，
    默认 tl。有些地方（比如顶栏）方框上面就是窗口边缘，编号圈放下面才不会盖住文字。
    """
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    font = QFont(painter.font())
    font.setPointSizeF(10.5)
    font.setBold(True)
    painter.setFont(font)

    ratio = pixmap.devicePixelRatio() or 1.0
    width = pixmap.width() / ratio
    height = pixmap.height() / ratio
    radius = 15

    for mark in marks:
        number, target = mark[0], mark[1]
        corner = mark[2] if len(mark) > 2 else "tl"
        rect = QRect(target) if isinstance(target, QRect) else widget_rect(window, target)
        rect = rect.adjusted(-4, -4, 4, 4)
        print(f"      标记 {number} <- {rect.x()},{rect.y()} {rect.width()}x{rect.height()} ({corner})")

        painter.setPen(QPen(QColor(theme.ACCENT), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, 7, 7)

        cx = rect.right() if "r" in corner else rect.left()
        cy = rect.bottom() if "b" in corner else rect.top()
        cx = int(min(max(cx, radius + 2), width - radius - 2))
        cy = int(min(max(cy, radius + 2), height - radius - 2))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(theme.ACCENT))
        painter.drawEllipse(QPoint(cx, cy), radius, radius)
        painter.setPen(QColor("#ffffff"))
        painter.drawText(
            QRect(cx - radius, cy - radius, radius * 2, radius * 2),
            int(Qt.AlignmentFlag.AlignCenter),
            str(number),
        )
    painter.end()


def grab(window, name: str, marks=None) -> None:
    window.repaint()
    QApplication.processEvents()
    pixmap = window.grab()
    if marks:
        annotate(pixmap, window, marks)
    path = OUT / f"{name}.png"
    pixmap.save(str(path))
    print(f"    {path.relative_to(ROOT)}  {pixmap.width()}x{pixmap.height()}")


def force_layout(app, window) -> None:
    """refresh() 会重建一堆控件，量坐标之前先把布局和延迟删除都跑干净。"""
    QApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    app.processEvents()
    parent = window.page_library.content_host
    if parent.layout() is not None:
        parent.layout().activate()
    app.processEvents()


def first_row_rect(window, widget_type, count: int = 3) -> QRect | None:
    """取某一类控件里第一行的矩形，用来给整排卡片画框。"""
    widgets = [w for w in window.page_library.findChildren(widget_type) if w.isVisible()]
    if not widgets:
        return None
    widgets.sort(key=lambda w: (widget_rect(window, w).y(), widget_rect(window, w).x()))
    top = widget_rect(window, widgets[0]).y()
    row = [w for w in widgets if abs(widget_rect(window, w).y() - top) < 4][:count]
    rect = widget_rect(window, row[0])
    for widget in row[1:]:
        rect = rect.united(widget_rect(window, widget))
    return rect


def add_and_wait(app, window, pack_id: int, timeout: float = 420.0) -> str:
    """走一遍真实的「添加整合包」流程并等它出结果。"""
    window.add_pack(pack_id)
    wait_for(
        app,
        lambda: (entry := window.library.get(pack_id)) is not None and entry.status in ("ready", "error"),
        timeout,
        f"整合包 {pack_id} 准备完成",
    )
    entry = window.library.get(pack_id)
    if entry is None:
        return "missing"
    print(f"    {entry.pack_id} -> {entry.status}  {entry.name} v{entry.version_name}  {entry.files:,} 个文件")
    return entry.status


def grab_dialog(window, app, name: str) -> bool:
    """把弹出的模态对话框叠在主窗口上截下来。"""
    for widget in QApplication.topLevelWidgets():
        if isinstance(widget, QMessageBox) and widget.isVisible():
            app.processEvents()
            dialog = widget.grab()
            base = window.grab()
            painter = QPainter(base)
            painter.fillRect(base.rect(), QColor(0, 0, 0, 120))
            painter.drawPixmap(
                (base.width() - dialog.width()) // 2,
                (base.height() - dialog.height()) // 2,
                dialog,
            )
            painter.end()
            base.save(str(OUT / f"{name}.png"))
            print(f"    docs/guide/{name}.png  {base.width()}x{base.height()}")
            widget.accept()
            return True
    return False


# --------------------------------------------------------------------------- 主流程
def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    app = QApplication([])
    theme.apply(app)

    window = MainWindow()
    window.resize(*WINDOW_SIZE)
    window.move(-4000, -4000)  # 挪到屏幕外
    window.show()
    app.processEvents()

    print("1) 空库首启")
    window._switch_page("library")  # noqa: SLF001
    settle(app, window, 2)
    grab(window, "01-first-run")

    print("2) 发现页（热门整合包）")
    window._switch_page("discover")  # noqa: SLF001
    wait_for(app, lambda: window.page_discover.flow.count() > 0, 120, "热门列表")
    settle(app, window, 30)
    grab(window, "02-discover")

    print("3) 搜索结果")
    window.topbar.search.setText("Skies")
    window.topbar.search_submitted.emit("Skies")
    wait_for(app, lambda: "搜索结果" in window.page_discover.status.text(), 90, "搜索结果")
    settle(app, window, 30)
    grab(window, "03-search")

    print("4) 添加整合包（抓清单下载中的进度）")
    window.topbar.search.clear()
    window._switch_page("library")  # noqa: SLF001
    window.add_pack(DEMO_PACKS[0])
    window._switch_page("downloads")  # noqa: SLF001
    got = wait_for(
        app,
        lambda: (card := window.page_downloads.card(str(DEMO_PACKS[0]))) is not None
        and card.progress.value() >= 120,
        180,
        "清单下载进度",
        poll=0.005,
    )
    if got:
        QApplication.processEvents()
        grab(window, "04-downloads")
    else:
        print("    !! 没抓到进度，跳过 04-downloads")

    print("5) 主页的「正在准备」大卡片")
    window._switch_page("library")  # noqa: SLF001
    # 切页面会把卡片重建一遍，进度要等下一次回调才画上去，所以这里等一下进度条
    got = wait_for(
        app,
        lambda: (card := window.page_library.card(str(DEMO_PACKS[0]))) is not None and card.progress.value() > 0,
        90,
        "库页的进度条",
        poll=0.005,
    )
    if got:
        QApplication.processEvents()
        grab(window, "05-preparing")
    else:
        print("    !! 任务已结束，跳过 05-preparing")

    print("6) 等演示用整合包全部就绪")
    for pack_id in DEMO_PACKS:
        entry = window.library.get(pack_id)
        if entry is None or entry.status not in ("ready", "error"):
            add_and_wait(app, window, pack_id)

    print("7) 界面速览（带编号，库里有卡片、同时有一个正在准备）")
    window._switch_page("library")  # noqa: SLF001
    window.add_pack(EXTRA_PACK)
    wait_for(
        app,
        lambda: (card := window.page_library.card(str(EXTRA_PACK))) is not None and card.progress.value() > 0,
        180,
        "新任务的进度",
        poll=0.005,
    )
    settle(app, window, 25)

    force_layout(app, window)

    group = window.topbar.combo_group
    sort = window.topbar.combo_sort
    marks = [
        (1, window.rail, "tl"),
        (2, window.topbar.search, "tl"),
        # 顶栏上面就是窗口边缘，编号圈放左下角才不会盖住 GROUP BY 几个字
        (3, widget_rect(window, group).united(widget_rect(window, sort)), "bl"),
    ]
    card = window.page_library.card(str(EXTRA_PACK))
    if card is not None:
        marks.append((4, card, "tl"))
    tiles = first_row_rect(window, PackTile, 3)
    if tiles is not None:
        marks.append((5, tiles, "tl"))
    else:
        print("    !! 没找到卡片，5 号标记改用滚动区")
        marks.append((5, window.page_library.scroll, "tl"))
    grab(window, "06-overview", marks)

    print("8) 等最后一个也完成，再截「我的整合包」")
    wait_for(
        app,
        lambda: (entry := window.library.get(EXTRA_PACK)) is not None and entry.status in ("ready", "error"),
        420,
        f"整合包 {EXTRA_PACK} 准备完成",
    )
    window._refresh_lists()  # noqa: SLF001
    settle(app, window, 25)
    grab(window, "07-library")

    print("9) 整合包详情弹窗")
    QTimer.singleShot(700, lambda: grab_dialog(window, app, "08-detail"))
    window.show_pack_detail(str(DEMO_PACKS[0]))  # noqa: SLF001

    print("10) 设置页")
    window._switch_page("settings")  # noqa: SLF001
    # 本进程的库其实在临时目录里，但截图要给用户看真实路径，别把临时目录截进去
    window.page_settings.edit_dir.setText(str(_REAL_DATA_DIR))  # noqa: SLF001
    QApplication.processEvents()
    grab(window, "09-settings")

    print("11) 关于页")
    window._switch_page("about")  # noqa: SLF001
    QApplication.processEvents()
    grab(window, "10-about")

    window.close()
    print("完成。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    finally:
        shutil.rmtree(_TEMP_HOME, ignore_errors=True)
