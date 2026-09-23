"""FTB 整合包下载器（PySide6 GUI，界面参考官方 FTB App）。

参考项目（只读）：仓库根目录 reference/CTBModifiy-master/，即 C# 写的 CurseTheBeast。
本工具的接口调用、清单字段、打包格式都以它为参考，见 docs/ftb-api-notes.md。
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _package_version

try:  # 装成包之后版本号以 pyproject.toml 为准
    __version__ = _package_version("ftb-downloader")
except PackageNotFoundError:  # 没安装（直接跑源码）时的兜底
    __version__ = "0.1.0"

__all__ = ["__version__"]
