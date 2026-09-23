"""零碎小工具。"""

from __future__ import annotations


def human_size(size: int | float) -> str:
    """把字节数格式化成人看的字符串。"""
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(value) < 1024.0 or unit == "TB":
            return f"{int(value)} B" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} TB"


def human_rate(bytes_per_second: float) -> str:
    """下载速度，例如 1.2 MB/s。"""
    if bytes_per_second <= 0:
        return ""
    return f"{human_size(bytes_per_second)}/s"


def human_count(value: int) -> str:
    return f"{value:,}"
