"""CurseForge 官方接口（可选，用于校验清单里的 fileId 还有没有效）。

对照参考项目：
  * CurseTheBeast/Api/Curseforge/CurseforgeApiClient.cs
  * CurseTheBeast/Services/CurseforgeService.cs

只有「标准包」需要这一步：标准包不下载 CurseForge 模组本体，而是把
projectID / fileID 写进 manifest.json 交给启动器。如果 FTB 清单里的 fileId
已经过期（sha1 对不上），就得把该文件改成自己下载。
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

import requests

CURSEFORGE_API = "https://api.curseforge.com"

#: 参考项目里硬编码的 key（CurseTheBeast/Services/HttpConfigService.cs）。
#: 实测 2026-09 仍可用；如果哪天 403 了，就在设置里换成自己的 key。
DEFAULT_API_KEY = "$2a$10$KauzeIBqTRY2jwkx64A.Cep7cmWFGGYVncpqvfOCOee/90YPgkgfy"

#: CurseForge 哈希算法编号：1 = SHA1
HASH_ALGO_SHA1 = 1

#: 接口一次最多收 50 个 fileId
BATCH_SIZE = 50


class CurseforgeApiError(RuntimeError):
    pass


class CurseforgeClient:
    def __init__(self, api_key: str = DEFAULT_API_KEY, proxy: str | None = None, timeout: float = 30.0) -> None:
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-api-key": api_key,
        })
        if proxy:
            self._session.proxies = {"http": proxy, "https": proxy}

    def get_files(self, file_ids: Sequence[int]) -> list[dict[str, Any]]:
        """批量查文件信息，超过 50 个会自动分批。"""
        result: list[dict[str, Any]] = []
        for start in range(0, len(file_ids), BATCH_SIZE):
            batch = list(file_ids[start : start + BATCH_SIZE])
            rsp = self._session.post(
                f"{CURSEFORGE_API}/v1/mods/files",
                json={"fileIds": batch},
                timeout=self.timeout,
            )
            if rsp.status_code == 403:
                raise CurseforgeApiError("CurseForge 拒绝了这个 API key（403）")
            rsp.raise_for_status()
            result.extend(rsp.json().get("data") or [])
        return result

    def close(self) -> None:
        self._session.close()

    def __enter__(self) -> CurseforgeClient:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


def sha1_of(file_info: dict[str, Any]) -> str | None:
    """从 CurseForge 的文件信息里取 sha1。"""
    for item in file_info.get("hashes") or []:
        if item.get("algo") == HASH_ALGO_SHA1:
            return str(item.get("value") or "").lower() or None
    return None


def find_outdated(file_infos: Iterable[tuple[int, str]], client: CurseforgeClient) -> set[int]:
    """给定 (fileId, sha1) 列表，返回 sha1 对不上的 fileId 集合。"""
    pairs = {file_id: sha1.lower() for file_id, sha1 in file_infos if sha1}
    if not pairs:
        return set()
    outdated = set(pairs)
    for info in client.get_files(list(pairs)):
        file_id = int(info.get("id") or 0)
        expected = pairs.get(file_id)
        if expected is None:
            continue
        if sha1_of(info) == expected:
            outdated.discard(file_id)
    return outdated
