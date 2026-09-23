"""FTB 整合包下载器 —— 程序入口。

开发期直接运行：
    .venv\\Scripts\\python.exe main.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# 采用 src 布局，未安装成包时也要能直接运行
_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from ftb_downloader.app import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
