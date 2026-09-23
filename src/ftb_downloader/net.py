r"""代理探测。

探测顺序对照参考项目 CurseTheBeast/Services/HttpConfigService.cs：
系统代理（Windows「Internet 选项」，注册表 HKCU\...\Internet Settings）→ 环境变量。
参考项目启动时会打印「（正在使用系统代理）」，就是这里读到的同一份设置。
"""

from __future__ import annotations

import os
import sys

_ENV_KEYS = ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy")

_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"


def system_proxy() -> str | None:
    """返回 'http://host:port' 形式的代理地址；没有配置代理时返回 None。"""
    if sys.platform == "win32":
        proxy = _windows_proxy()
        if proxy:
            return proxy
    for key in _ENV_KEYS:
        value = os.environ.get(key)
        if value:
            return _normalize(value)
    return None


def _windows_proxy() -> str | None:
    try:
        import winreg
    except ImportError:
        return None
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_PATH) as key:
            enabled, _ = winreg.QueryValueEx(key, "ProxyEnable")
            if not enabled:
                return None
            server, _ = winreg.QueryValueEx(key, "ProxyServer")
    except OSError:
        return None
    return _normalize(server)


def _normalize(server: object) -> str | None:
    """ProxyServer 可能是 '127.0.0.1:7897'，也可能是 'http=host:port;https=host:port'。"""
    text = str(server or "").strip()
    if not text:
        return None
    if "=" in text:
        mapping = dict(part.split("=", 1) for part in text.split(";") if "=" in part)
        text = (mapping.get("https") or mapping.get("http") or "").strip()
        if not text:
            return None
    if "://" not in text:
        text = "http://" + text
    return text.rstrip("/")
