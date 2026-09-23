# FTB / CurseForge 接口与打包笔记

来源：参考项目 `reference/CTBModifiy-master`（C# / CurseTheBeast）+ 2026-09 实测。
实测用的样本：**FTB Skies 2: Aero（整合包 134，版本 100514）**，清单 8.2 MB / 11429 个文件 / 1.1 GB。

---

## 1. FTB 官方接口

Base：`https://api.feed-the-beast.com/v1/modpacks/public`　（**不需要 API key**）

| 端点 | 说明 |
| --- | --- |
| `GET /modpack/all` | 所有整合包 id（`packs: int[]`） |
| `GET /modpack/featured/{limit}` | 热门整合包 id |
| `GET /modpack/search/{limit}/detailed?platform=modpacksch&term=关键词` | 搜索（返回 packs[]，字段比 info 少） |
| `GET /modpack/{packId}` | 整合包信息 + 版本列表（`versions[]`） |
| `GET /modpack/{packId}/{versionId}` | 某个版本的完整文件清单（**很大**，8 MB 起步） |
| `GET /mod/{sha1}` | 按 sha1 反查这个文件现在还有哪些下载源（文件失效时用来救） |

约定：

- 所有响应都带 `status` / `message` 字段，`status != "success"` 就是出错。
- 参考项目会拉黑 4 个「伪整合包」id：81 Minecraft、104 Forge、105 Fabric、116 NeoForge。
- 清单请求必须异步：FTB Skies 2 的清单要下载 8.2 MB、解析 11429 个对象。

---

## 2. ⚠ 清单字段类型陷阱（本项目诞生的原因）

`files[]` 里带 CurseForge 引用的条目长这样（**注意 ID 是字符串**）：

```json
{
  "id": 3877222753,
  "path": "./mods",
  "name": "FramedBlocks-10.6.2.jar",
  "type": "mod",
  "url": "https://edge.forgecdn.net/files/8780/141/FramedBlocks-10.6.2.jar",
  "sha1": "c86d546e57a6161e77f4acd651e6939b2d6136d5",
  "size": 4305605,
  "clientonly": false,
  "serveronly": false,
  "optional": false,
  "updated": 1790089775,
  "curseforge": { "project": "441647", "file": "8780141" }
}
```

- **2026-09 实测**：当前所有热门包（134 / 127 / 132 / 130 / 128）的 `curseforge.project` 和
  `curseforge.file` **都是字符串**；老数据里是数字。
- 参考项目把它们声明成 C# 的 `long`，System.Text.Json 默认严格解析数字，于是遇到第一条
  带 curseforge 的条目就抛异常：
  `The JSON value could not be converted to ... Curseforge. Path: $.files[1981].curseforge.project`，
  整份 11429 条的清单全部报废（解析是一个整体）。
- 所以 Python 这边所有整数统一走 `models/manifest.py` 里的 `as_int()`，数字 / 数字字符串都吃。
- 附带一提，同一个接口的 `GET /modpack/{id}`（信息）里 `id` / `installs` / `plays` 现在
  仍然是数字 —— 也就是说 FTB 是**部分字段**字符串化，别赌哪个字段永远是数字。

其它字段：

| 字段 | 说明 |
| --- | --- |
| `path` | 目录，形如 `./mods`、`./config/Advancedperipherals/` |
| `name` | 文件名 |
| `type` | `mod` / `config` / `resource` / `script`（实测分布：480 / 2034 / 8824 / 91） |
| `clientonly` / `serveronly` | 都为 false → 两边都要（参考项目记作 Both） |
| `size` | 字节（本包最大 73 MB） |
| `sha1` | 下载后校验用 |
| `url` | 实测**全部非空**；失效文件要靠 `/mod/{sha1}` 重新找源 |

包内相对路径的算法（对照 `FileEntry.WithArchiveEntryName()`）：
把 `path` 和 `name` 逐段 `\` → `/`、去掉段首的 `.` 和首尾 `/`，再用 `/` 连接。
即 `./mods` + `FramedBlocks-10.6.2.jar` → `mods/FramedBlocks-10.6.2.jar`。
另外：`mods/*.jar.disabled` 会把结尾的 `.disabled` 去掉（禁用状态的 mod 仍然按 jar 放）。

---

## 3. CurseForge 直链规则

参考 `Utils/CurseforgeUtils.cs`：

```
https://edge.forgecdn.net/files/{fileId // 1000}/{fileId % 1000}/{urlencode(文件名)}
```

例：fileId `8780141` + `FramedBlocks-10.6.2.jar` → `https://edge.forgecdn.net/files/8780/141/FramedBlocks-10.6.2.jar`，
与清单里的 `url` 一致。所以即使清单里的 url 挂了，只要 fileId 还有效就能自己拼直链。

实测注意点：本包 484 条 curseforge 条目里，有 7 条 **url 中的 fileId 与 `curseforge.file` 不一致**，
以 `url` 为准（参考项目也是 url 优先）。

---

## 4. CurseForge 官方接口

- `POST https://api.curseforge.com/v1/mods/files`，body `{"fileIds": [8780141, ...]}`，一次最多 50 个
- Header 需要 `x-api-key`；参考项目在一处硬编码了一个 key（`Services/HttpConfigService.cs`），
  2026-09 实测仍然可用
- 返回 `data[]`：`id` / `modId`（= projectID）/ `fileName` / `fileLength` /
  `downloadUrl` / `hashes[{algo, value}]`，其中 **algo=1 是 sha1**，algo=2 是 murmur2
- 用途（只有「标准包」需要）：拿返回的 sha1 和清单里的 sha1 比对，不一致说明这个 fileId 已经过期，
  该文件必须改成自己下载写进 `overrides/`，不能交给启动器。
  参考项目：`Services/CurseforgeService.GetFilesWithIncorrectMetadata()`
- 坑：参考项目把结果塞进 `ToDictionary(f => f.Curseforge.FileId)`，清单里若有重复 fileId 会直接抛异常
  （本包 484 条无重复）
- 文档：https://docs.curseforge.com/

---

## 5. 打包格式（CurseForge modpack zip）

参考 `Packs/CurseforgeModpackExtensions.cs`。zip 结构：

```
manifest.json
modlist.html
overrides/            ← 除 CurseForge 模组以外的所有文件（config/resource/script/...）
overrides/README.md
overrides/icon.png
overrides/unreachable-files.json   （有失效文件时才写）
```

`manifest.json`：

```json
{
  "minecraft": {
    "version": "1.21.1",
    "modLoaders": [{ "id": "neoforge-21.1.250", "primary": true }]
  },
  "manifestType": "minecraftModpack",
  "manifestVersion": 1,
  "name": "FTB Skies 2: Aero",
  "version": "1.12.1",
  "author": "FTB Team",
  "files": [{ "projectID": 441647, "fileID": 8780141, "required": true }],
  "overrides": "overrides"
}
```

- **标准包**：`files[]` 写 CurseForge 模组的 projectID/fileID（启动器自己去下），自己只打包其余文件。
- **完整包**：`files[]` 留空，所有文件（含模组）都塞进 `overrides/`。
- 另外还会把整合包名/版本/简介写进 zip 的 comment。
- 运行环境取自清单的 `targets[]`：`type=game` → MC 版本，`modloader` → `name-version`，
  `runtime` → Java 版本；内存建议取 `specs.minimum` / `specs.recommended`（单位 MB）。
- 服务端包是另一套（`Packs/ServerModpack.cs`）：多一个自造的 `server-manifest.json`，
  再额外塞进 loader 安装文件，可选预安装（`ServerInstaller/*` 支持 Forge / NeoForge / Fabric）。

---

## 6. 代理

参考项目 `Services/HttpConfigService.cs` 的顺序：**系统代理 → `HTTP_PROXY` 环境变量 → 直连**。
Windows 的「系统代理」就是「Internet 选项」里的设置，读注册表：

```
HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings
    ProxyEnable = 1
    ProxyServer = 127.0.0.1:7897          （也可能是 http=host:port;https=host:port 形式）
```

本项目 `src/ftb_downloader/net.py` 复刻了这一套，启动时会打印用的哪个代理。

---

## 7. 其它已知坑 / 备忘

- 清单里 `files[]` 的顺序没有保证，判断「第几条」只能靠自己数；参考项目报错里的下标 1981
  正好是第一条带 curseforge 的条目。
- 有些 mod 作者删库跑路，文件下不下来 → 参考项目把这类文件标记为 unreachable，
  写进 `unreachable-files.json`，并且**不让整包失败**。
- 下载缓存：参考项目在 `%LOCALAPPDATA%\CurseTheBeast` 下按 `{id & 0xFF:x2}/{id:x2}` 分目录缓存文件，
  同目录写一个 `.sha1` sidecar 用于跳过重复校验；清单本身也会以 Brotli 压缩缓存。
- 清单是可以缓存的（内容不变），但**不要**缓存解析失败的中间结果。
- 参考项目是 .NET 8 + `System.Text.Json` 源生成（`JsonSerializerContext`），
  改模型后要重新 `dotnet build CurseTheBeast.sln -c Debug -p:Platform=x64`。
