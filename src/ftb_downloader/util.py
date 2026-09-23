"""零碎小工具。"""

from __future__ import annotations


def human_size(size: int | float) -> str:
    """把字节数格式化成人看的字符串。"""
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(value) < 1024.0 or unit == "TB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024.0
    return f"{value:.1f} TB"
