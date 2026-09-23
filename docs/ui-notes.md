# 界面笔记：照官方 FTB App 复刻

## 1. 配色（从 FTB App 截图逐像素取样）

取样方法：`QImage` 读入截图，按行 / 列扫描颜色运行区间，取出现次数最多的值。

| 用途 | 颜色 | 取样位置 |
| --- | --- | --- |
| 页面 / 卡片底色 | `#2a2a2a` | 内容区、卡片内部（整屏几乎都是它） |
| 左侧图标栏 | `#313131` | x=27 纵向整列 |
| 标题栏（自绘窗口时） | `#1d1c1c` | 顶部 24px |
| 主色（选中项底、进度条） | `#00a63e` | 选中图标底色、进度条填充 |
| 输入框 / 下拉框描边 | 约 `#696969`，1px | 搜索框上边缘 |
| 正文 | `#ffffff` | 卡片标题、区块标题 |
| 次要文字 | `#d4d4d4` | 状态文字、GROUP BY / SORT BY 小标签 |

整体非常「平」：卡片不换底色，只靠 1px 描边 + 间距分层次；主色只用在**选中项**和**进度条**上。
对应实现都在 `src/ftb_downloader/ui/theme.py`。

## 2. 结构对照

| FTB App 里的东西 | 本项目实现 |
| --- | --- |
| 左侧 54px 图标栏、选中项绿底圆角 | `ui/widgets/sidebar.py` + `#RailButton:checked` |
| 顶部搜索框（带放大镜、深色描边） | `ui/widgets/common.py:SearchEdit` |
| GROUP BY / SORT BY（小标签 + 下拉） | `ui/widgets/topbar.py` + `DarkComboBox` |
| "Installing" 区的大卡片（百分比 / 进度条 / ⚡速度） | `ui/widgets/cards.py:PackCard` |
| 整合包网格卡片 | `ui/widgets/cards.py:PackTile` + `ui/layouts.py:FlowLayout` |
| 底部状态条 | `QStatusBar`（MainWindow） |

## 3. 实现要点 / 踩坑

- **自绘优先**：下拉框、速度胶囊、进度条、全部图标都是自绘，只把配色交给 QSS。
  Windows 原生样式对 QSS 支持不全，所以 `theme.apply()` 里把 app style 固定成 `Fusion`。
- **图标零资源**：`ui/icons.py` 用 `QPainterPath` 在 24x24 画布上画 2px 圆头线性图标，
  按 2 倍渲染后设 `devicePixelRatio`，HiDPI 下不糊。
- ⚠ **devicePixelRatio 只能算一次**：QPainter 画在设了 DPR 的 QPixmap 上时 Qt 已经按 DPR 缩放过，
  代码里再乘一次 ratio 会把图标画大一倍（现象：只看到图标左上角那一小块）。踩过一次，已修。
- **流式进度**：清单 8 MB，`FTBClient.manifest(on_progress=...)` 用 `stream=True` 按 64 KB 回调；
  并且显式 `Accept-Encoding: identity`，否则 gzip 解压后的字节数会超过 Content-Length，进度会飙过 100%。
- **进度就地更新**：进度回调不重建卡片（会闪），而是 `page.card(key)` 找到现有卡片改数值。
- **列表重建**：库内容变化（加包 / 状态变化）才整体重建，重建时 `_clear()` 要 `setParent(None)` + `deleteLater()`，
  否则旧控件会一直挂在布局里。

## 4. 预览图怎么来的

`scripts/make_ui_preview.py` 会起一个真实窗口、灌一批假数据（准备中 / 出错 / 已就绪 / 分组），
等封面从 FTB CDN 下载完，然后 `window.grab()` 存成 `docs/ui-preview.png`：

```powershell
uv run python scriptsmake_ui_preview.py
```

改了 UI 记得重新生成，README 里引用的是它。
