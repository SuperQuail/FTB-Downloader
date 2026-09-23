# FTB 整合包下载器（PySide6）

输入整合包 ID → 选版本 → 选客户端/服务端 + 标准包/完整包 → 下载并打成能直接导入启动器的
CurseForge 格式整合包 zip。数据源是 FTB 官方接口（feed-the-beast.com）。

> **参考项目**：`reference/CTBModifiy-master/`（C# 写的 CurseTheBeast，2024 年后没再更新）。
> 该目录已加进 `.gitignore`，只作为**只读参考**：接口怎么调、字段怎么解析、zip 怎么打，全部照它来。
> 参考项目踩过的坑（尤其是会让整份清单解析失败的字段类型问题）记在 [`docs/ftb-api-notes.md`](docs/ftb-api-notes.md)。

## 目录结构

```
FTB_downloader/
├── main.py                       # 入口：python main.py
├── requirements.txt
├── scripts/
│   └── smoke_ftb_api.py          # 命令行冒烟：不启动 GUI，直接跑一遍 FTB 接口
├── src/ftb_downloader/
│   ├── app.py                    # QApplication 引导（支持 --self-test）
│   ├── net.py                    # 代理探测（系统代理 → 环境变量）
│   ├── util.py                   # human_size 之类
│   ├── api/
│   │   ├── ftb.py                # FTB 官方接口客户端
│   │   └── curseforge.py         # CurseForge 官方接口（校验 fileId 用）
│   ├── models/
│   │   ├── manifest.py           # 文件清单模型（含字符串 ID 兼容）
│   │   └── pack.py               # 整合包信息 / 版本 / 搜索结果
│   └── ui/
│       └── main_window.py        # 主窗口
├── docs/ftb-api-notes.md         # 接口 + 打包格式笔记
└── reference/                    # ← git 忽略，参考项目副本
    └── CTBModifiy-master/
```

## 快速开始

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

PyPI 需要走代理时：

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt --proxy http://127.0.0.1:7897
```

命令行冒烟（不弹窗，直接把接口跑一遍，推荐改完代码先跑它）：

```powershell
.venv\Scripts\python.exe scripts\smoke_ftb_api.py            # 默认 134 的最新版
.venv\Scripts\python.exe scripts\smoke_ftb_api.py 134 100514 # 指定版本
```

## 当前进度

已经能跑通的：

- 代理自动探测（Windows 注册表的系统代理 → `HTTP(S)_PROXY` 环境变量），启动时会打印用的是哪个
- FTB 接口：整合包信息 / 版本列表 / 文件清单（8 MB 级清单放后台线程，界面不卡）
- 清单里「数字」和「数字字符串」两种 ID 形式都能解析（参考项目就是在这里挂的，详见笔记）
- 清单统计：文件总数、客户端/服务端文件数、CurseForge 模组数、需要自己下载的文件数、总大小、运行环境

还没写（下一步按参考项目补）：

| 待做 | 参考项目文件 |
| --- | --- |
| 下载队列：多线程、断点/缓存、sha1 校验 | `Services/FileDownloadService.cs`、`Download/DownloadQueue.cs` |
| 本地缓存目录 + `.sha1` sidecar | `Storage/LocalStorage.cs`、`Storage/FileEntry.cs` |
| CurseForge fileId 有效性校验（sha1 对不上就改成自己下载） | `Services/CurseforgeService.cs` |
| 打包成 CurseForge zip（`manifest.json` / `overrides/` / `modlist.html` / 注释 / 图标） | `Packs/CurseforgeModpackExtensions.cs`、`Services/PackService.cs` |
| 服务端包 + loader 预安装（Forge / NeoForge / Fabric） | `Packs/ServerModpack.cs`、`ServerInstaller/*` |
| 失效文件恢复（`/mod/{sha1}` 重新找源） | `FTBService.TryRecoverUnreachableFiles` |

## 参考项目对照表

| 参考项目（C#） | 本项目（Python） |
| --- | --- |
| `Api/FTB/FTBApiClient.cs` | `src/ftb_downloader/api/ftb.py` |
| `Api/FTB/Model/ModpackManifest.cs` | `src/ftb_downloader/models/manifest.py` |
| `Api/FTB/Model/ModpackInfo.cs` | `src/ftb_downloader/models/pack.py` |
| `Api/Curseforge/CurseforgeApiClient.cs` | `src/ftb_downloader/api/curseforge.py` |
| `Services/HttpConfigService.cs` | `src/ftb_downloader/net.py` |
| `Services/FTBService.cs` | 待实现（下载流程编排） |
| `Utils/CurseforgeUtils.cs` | `models/manifest.py` 里的 `CF_CDN` |

## 环境

- Python 3.14（PySide6 6.11 的 wheel 是 `cp310-abi3`，3.10+ 都能装）
- PySide6 / requests，见 `requirements.txt`
- 参考项目需要 .NET 8 SDK 才能重新编译（`dotnet build CurseTheBeast.sln -c Debug -p:Platform=x64`）；
  `reference/CTBModifiy-master/CurseTheBeast/bin/x64/Debug/net8.0/` 里已经有一份修好清单解析问题的可执行文件

## 小提示

- Windows 控制台默认编码不是 UTF-8，重定向脚本输出时中文可能乱码，先 `chcp 65001`。
- GUI 无显示器自检：`QT_QPA_PLATFORM=offscreen .venv\Scripts\python.exe main.py --self-test`。
