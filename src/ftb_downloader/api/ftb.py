"""FTB 官方接口客户端。

对照参考项目 CurseTheBeast/Api/FTB/FTBApiClient.cs。
接口不需要 key，响应体统一带 status / message 字段。

端点一览（实测）：
    GET /modpack/all                              所有整合包 id
    GET /modpack/featured/{limit}                 热门整合包 id
    GET /modpack/search/{limit}/detailed?platform=modpacksch&term=xxx
    GET /modpack/{packId}                         整合包信息 + 版本列表
    GET /modpack/{packId}/{versionId}             某版本的文件清单（整包 8 MB 起步）
    GET /mod/{sha1}                               按 sha1 查这个文件在哪些源上还有

注意：manifest 响应很大（FTB Skies 2 是 ~8.2 MB / 11429 个文件），
必须放在后台线程里请求，否则 UI 会卡死。
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from typing import Any

import requests

from ftb_downloader import __version__
from ftb_downloader.models.manifest import ModpackManifest
from ftb_downloader.models.pack import PackInfo, PackSummary

API_BASE = "https://api.feed-the-beast.com/v1/modpacks/public"
USER_AGENT = f"FTBDownloader/{__version__}"

#: 参考项目里被拉黑的「伪整合包」（Minecraft / Forge / NeoForge / Fabric 本体）
BLACKLIST = {81, 104, 105, 116}

LogFn = Callable[[str], None]


class FTBApiError(RuntimeError):
    """网络失败，或接口返回 status != success。"""


class FTBClient:
    """同步客户端。GUI 里请放进 QThread 使用。"""

    def __init__(self, proxy: str | None = None, timeout: float = 60.0, retries: int = 3) -> None:
        self.timeout = timeout
        self.retries = retries
        self.proxy = proxy
        self.log: LogFn | None = None
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
        self.set_proxy(proxy)

    def set_proxy(self, proxy: str | None) -> None:
        """换代理（设置页重新探测后调用）。"""
        self.proxy = proxy
        self._session.proxies = {"http": proxy, "https": proxy} if proxy else {}

    # ------------------------------------------------------------------ 基础
    def _emit(self, message: str) -> None:
        if self.log:
            self.log(message)

    def _get_json(self, path: str, on_progress: Callable[[int, int], None] | None = None) -> Any:
        """GET 一个 JSON 端点。

        on_progress 只在需要下载大响应（文件清单，8 MB 起步）时传，
        传了就走流式读取，按块回调 (已接收字节, 总字节)。
        """
        url = API_BASE + path
        last_error: Exception | None = None
        for attempt in range(1, self.retries + 1):
            self._emit(f"GET {url}" + (f"（第 {attempt} 次重试）" if attempt > 1 else ""))
            try:
                if on_progress is None:
                    rsp = self._session.get(url, timeout=self.timeout)
                    rsp.raise_for_status()
                    data = rsp.json()
                else:
                    # 明确不要压缩，这样 Content-Length 就是实际字节数，进度才准
                    rsp = self._session.get(
                        url, timeout=self.timeout, stream=True, headers={"Accept-Encoding": "identity"}
                    )
                    rsp.raise_for_status()
                    total = int(rsp.headers.get("Content-Length") or 0)
                    buffer = bytearray()
                    for chunk in rsp.iter_content(chunk_size=64 * 1024):
                        buffer.extend(chunk)
                        on_progress(len(buffer), total)
                    data = json.loads(bytes(buffer))
            except Exception as exc:  # noqa: BLE001 - 网络异常种类太多，统一重试
                last_error = exc
                if attempt < self.retries:
                    time.sleep(1.5 * attempt)
                continue
            if isinstance(data, dict) and data.get("status") not in (None, "success"):
                raise FTBApiError(f"{data.get('status')}: {data.get('message')}")
            return data
        raise FTBApiError(f"请求失败：{url}（重试 {self.retries} 次）") from last_error

    # ------------------------------------------------------------------ 端点
    def search(self, keyword: str, limit: int = 20) -> list[PackSummary]:
        from urllib.parse import quote

        data = self._get_json(
            f"/modpack/search/{limit}/detailed?platform=modpacksch&term={quote(keyword)}"
        )
        return [PackSummary.from_json(item) for item in data.get("packs") or []]

    def list_ids(self) -> list[int]:
        data = self._get_json("/modpack/all")
        return [int(pid) for pid in data.get("packs") or [] if int(pid) not in BLACKLIST]

    def featured_ids(self, limit: int = 20) -> list[int]:
        data = self._get_json(f"/modpack/featured/{limit}")
        return [int(pid) for pid in data.get("packs") or []]

    def info(self, pack_id: int) -> PackInfo:
        return PackInfo.from_json(self._get_json(f"/modpack/{pack_id}"))

    def manifest(
        self,
        pack_id: int,
        version_id: int,
        on_progress: Callable[[int, int], None] | None = None,
    ) -> ModpackManifest:
        """拉取文件清单（8 MB 级）。这一步就是参考项目崩溃的地方，见 models/manifest.py 顶部注释。"""
        return ModpackManifest.from_json(self._get_json(f"/modpack/{pack_id}/{version_id}", on_progress))

    def mod_info(self, sha1: str) -> list[dict[str, Any]]:
        """按 sha1 找可用的下载源（对照 FTBService.TryRecoverUnreachableFiles）。"""
        data = self._get_json(f"/mod/{sha1}")
        return list(data.get("versions") or [])

    def close(self) -> None:
        self._session.close()

    def __enter__(self) -> FTBClient:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
