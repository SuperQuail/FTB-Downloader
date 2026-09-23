r"""生成界面预览图（docs/ui-preview.png），给 README / 文档用。

    uv run python scripts\make_ui_preview.py

会灌一批假的整合包数据把各个状态都摆出来（准备中 / 出错 / 已就绪 / 分组），
封面走真实网络（FTB CDN），所以第一次跑要等几秒，并且需要能访问外网。
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from PySide6.QtWidgets import QApplication  # noqa: E402

from ftb_downloader.services.library import LibraryEntry  # noqa: E402
from ftb_downloader.ui import theme  # noqa: E402
from ftb_downloader.ui.main_window import MainWindow  # noqa: E402

#: FTB Skies 2: Aero 的方形封面（取自 /modpack/134 的 art[]）
ICON = "https://cdn.feed-the-beast.com/blob/22/225f0af85acc4fa904d3ff5e4e136e1985b94968191548e52ee73073d634c6b1.webp"

READY_PACKS = [
    (127, 100513, "FTB Presents Architect's Exodus", "1.4.2", "1.21.1", "neoforge 21.1.209", 5140, 361, 730144440),
    (130, 100515, "FTB StoneBlock 4", "1.9.0", "1.20.1", "forge 47.3.0", 6895, 423, 966367641),
    (132, 100517, "FTB Unstable 6", "6.2.0", "1.21.1", "neoforge 21.1.250", 4272, 352, 590558003),
    (126, 100500, "FTB NeoTech", "2.4.1", "1.21.1", "neoforge 21.1.201", 3980, 300, 512000000),
    (120, 100460, "FTB Skies", "1.8.2", "1.18.2", "forge 40.2.0", 3100, 260, 430000000),
    (118, 100440, "FTB Inferno", "1.6.0", "1.18.2", "forge 40.1.80", 2950, 240, 410000000),
]


def main() -> int:
    app = QApplication([])
    theme.apply(app)

    window = MainWindow()
    window.resize(1280, 800)

    library = window.library
    library.entries.clear()
    library.upsert(
        LibraryEntry(
            pack_id=134, version_id=100514, name="FTB Skies 2: Aero", version_name="1.12.1",
            icon_url=ICON, status="preparing", message="获取文件清单",
            files=11429, cf_mods=477, size=1181116006,
            game_version="1.21.1", loader="neoforge 21.1.250", java="21.0.10+7-LTS",
        )
    )
    library.upsert(
        LibraryEntry(
            pack_id=128, version_id=100482, name="FTB OceanBlock 2", version_name="1.6.1",
            icon_url=ICON, status="error", message="调用接口失败：超时",
            files=4847, cf_mods=312, size=644245094,
            game_version="1.21.1", loader="neoforge 21.1.190",
        )
    )
    for pack_id, version_id, name, version, mc, loader, files, cf_mods, size in READY_PACKS:
        library.upsert(
            LibraryEntry(
                pack_id=pack_id, version_id=version_id, name=name, version_name=version,
                icon_url=ICON, status="ready", files=files, cf_mods=cf_mods, size=size,
                game_version=mc, loader=loader,
            )
        )
    window._refresh_lists()  # noqa: SLF001 - 预览脚本，直接用内部刷新

    card = window.page_library.card("134")
    if card is not None:
        card.show_progress(True)
        card.set_progress(0.895, "0.20 MB/s")

    # 等封面下载完
    deadline = time.time() + 12
    while time.time() < deadline:
        app.processEvents()
        time.sleep(0.05)

    out = ROOT / "docs" / "ui-preview.png"
    window.show()
    app.processEvents()
    time.sleep(0.5)
    app.processEvents()
    window.grab().save(str(out))
    window.close()
    print(f"预览图已保存：{out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
