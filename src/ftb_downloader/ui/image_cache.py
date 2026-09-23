"""网络图片（整合包封面）的异步加载 + 内存缓存。

封面在 FTB 的 art[] 里，是普通 https 图片，直接 requests 拉下来丢给 QPixmap。
"""

from __future__ import annotations

import requests
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal
from PySide6.QtGui import QPixmap

from ftb_downloader import __version__

USER_AGENT = f"FTBDownloader/{__version__}"


class _Signals(QObject):
    done = Signal(str, bytes)


class _FetchTask(QRunnable):
    def __init__(self, url: str, signals: _Signals, proxy: str | None) -> None:
        super().__init__()
        self.url = url
        self.signals = signals
        self.proxy = proxy

    def run(self) -> None:
        data = b""
        try:
            proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
            rsp = requests.get(self.url, timeout=20, proxies=proxies, headers={"User-Agent": USER_AGENT})
            if rsp.ok:
                data = rsp.content
        except Exception:  # noqa: BLE001 - 封面加载失败无所谓，用占位图
            data = b""
        self.signals.done.emit(self.url, data)


class ImageCache(QObject):
    """用法：``pm = cache.peek(url)`` —— 没缓存会顺手发起下载并返回 None，
    等 ``loaded`` 信号回来再取一次。
    """

    loaded = Signal(str)

    def __init__(self, proxy: str | None = None, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.proxy = proxy
        self._pixmaps: dict[str, QPixmap] = {}
        self._pending: set[str] = set()
        self._failed: set[str] = set()
        self._pool = QThreadPool.globalInstance()
        self._signals = _Signals()
        self._signals.done.connect(self._on_done)

    def peek(self, url: str | None) -> QPixmap | None:
        if not url:
            return None
        cached = self._pixmaps.get(url)
        if cached is not None:
            return cached
        if url not in self._pending and url not in self._failed:
            self._pending.add(url)
            self._pool.start(_FetchTask(url, self._signals, self.proxy))
        return None

    def _on_done(self, url: str, data: bytes) -> None:
        self._pending.discard(url)
        pixmap = QPixmap()
        if data and pixmap.loadFromData(data) and not pixmap.isNull():
            self._pixmaps[url] = pixmap
        else:
            self._failed.add(url)
        self.loaded.emit(url)
