r"""命令行冒烟测试：不启动 GUI，直接把 FTB 接口跑一遍。

    .venv\Scripts\python.exe scripts\smoke_ftb_api.py            # 默认 134 / 最新版
    .venv\Scripts\python.exe scripts\smoke_ftb_api.py 134 100514

输出里会抽查清单中第一条带 curseforge 的文件，确认字符串形式的 ID 被正确解析
（参考项目就是在这里挂掉的）。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ftb_downloader.api.ftb import FTBClient  # noqa: E402
from ftb_downloader.net import system_proxy  # noqa: E402
from ftb_downloader.util import human_size  # noqa: E402


def main() -> int:
    pack_id = int(sys.argv[1]) if len(sys.argv) > 1 else 134
    version_id = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    proxy = system_proxy()
    print(f"代理：{proxy or '直连'}")

    with FTBClient(proxy=proxy) as client:
        client.log = lambda msg: print("  " + msg)

        info = client.info(pack_id)
        print(f"整合包：{info.name}（{info.id}）")
        print(f"作者：{'、'.join(info.authors) or '-'}")
        print(f"标签：{'、'.join(info.tags) or '-'}")

        if version_id:
            version = next((v for v in info.versions if v.id == version_id), None)
        else:
            version = info.latest_version
        if version is None:
            print(f"找不到版本 {version_id}")
            return 1
        print(f"版本：{version.label}")

        manifest = client.manifest(pack_id, version.id)
        loader = manifest.mod_loader
        runtime = "MC " + manifest.game_version
        if loader:
            runtime += f" / {loader.name} {loader.version}"
        if manifest.java_version:
            runtime += f" / Java {manifest.java_version}"

        print(f"清单：{version.id} 「{manifest.name}」共 {len(manifest.files)} 个文件")
        print(f"  {runtime}")
        print(f"  客户端文件 {len(manifest.client_files)} / 服务端文件 {len(manifest.server_files)}")
        print(f"  CurseForge 模组 {len(manifest.curseforge_mods)} / 需要自己下载 {len(manifest.local_files)}")
        print(f"  清单总大小 {human_size(manifest.total_size)}")
        print(f"  推荐内存 {manifest.specs.recommended} MB / 最低 {manifest.specs.minimum} MB")

        first_cf = next((f for f in manifest.files if f.curseforge is not None), None)
        if first_cf is not None:
            print(f"抽查（第 {manifest.files.index(first_cf)} 条）：{first_cf.name}")
            print(f"  project={first_cf.curseforge.project} file={first_cf.curseforge.file}")
            print(f"  FTB 直链  ：{first_cf.url}")
            print(f"  按 ID 拼链：{first_cf.download_url}")

        bad = [f for f in manifest.curseforge_mods if f.curseforge.project <= 0 or f.curseforge.file <= 0]
        print(f"ID 解析异常（<=0）的 CurseForge 条目：{len(bad)}")

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
