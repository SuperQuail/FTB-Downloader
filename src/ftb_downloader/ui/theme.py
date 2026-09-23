"""界面配色与全局样式表。

配色直接从官方 FTB App 的截图里取样得到（取样值见 docs/ui-notes.md）：
    页面底色 #2a2a2a / 左侧图标栏 #313131 / 标题栏 #1d1c1c
    主色（选中项、进度条）#00a63e / 正文 #ffffff / 次要文字 #d4d4d4
    输入框描边 #696969（1px）
"""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette

# ---------------------------------------------------------------- 颜色
BG = "#2a2a2a"          # 页面 / 面板底色
BG_RAIL = "#313131"     # 左侧图标栏
BG_CHROME = "#1d1c1c"   # 标题栏、气泡
BG_HOVER = "#363636"    # 悬停
BG_MENU = "#2f2f2f"     # 下拉菜单
BORDER = "#696969"      # 输入框描边
BORDER_SOFT = "#3d3d3d"  # 分隔线、卡片描边
TRACK = "#3d3d3d"       # 进度条底槽
ACCENT = "#00a63e"      # 主色
ACCENT_HOVER = "#00b344"
TEXT = "#ffffff"
TEXT_DIM = "#d4d4d4"
TEXT_MUTED = "#9a9a9a"
DANGER = "#e5484d"

FONT_FAMILY = '"Microsoft YaHei UI", "Segoe UI", "PingFang SC", sans-serif'

#: 左侧图标栏宽度（对照 FTB App 截图约 54px）
RAIL_WIDTH = 54
#: 输入框 / 下拉框高度
CONTROL_HEIGHT = 34
#: 圆角
RADIUS = 6


STYLESHEET = f"""
* {{
    font-family: {FONT_FAMILY};
    font-size: 13px;
}}
QWidget {{
    background-color: {BG};
    color: {TEXT_DIM};
}}
QMainWindow, QDialog {{ background-color: {BG}; }}

/* ---------------------------------------------------------- 左侧图标栏 */
#Rail {{
    background-color: {BG_RAIL};
    border: none;
    border-right: 1px solid {BG_CHROME};
}}
#RailButton {{
    background-color: transparent;
    border: none;
    border-radius: 8px;
}}
#RailButton:hover {{ background-color: {BG_HOVER}; }}
#RailButton:checked {{ background-color: {ACCENT}; }}

/* ---------------------------------------------------------------- 顶栏 */
#TopBar {{
    background-color: {BG};
    border-bottom: 1px solid {BORDER_SOFT};
}}
#FilterLabel {{
    color: {TEXT_DIM};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    background: transparent;
}}
#SearchEdit {{
    background-color: {BG};
    border: 1px solid {BORDER};
    border-radius: {RADIUS}px;
    padding-left: 34px;
    padding-right: 10px;
    color: {TEXT};
    selection-background-color: {ACCENT};
    selection-color: #ffffff;
}}
#SearchEdit:focus {{ border: 1px solid {ACCENT}; }}
#SearchIcon {{ background: transparent; }}

/* ------------------------------------------------------------ 文字层级 */
#PageTitle {{ color: {TEXT}; font-size: 20px; font-weight: 700; background: transparent; }}
#SectionTitle {{ color: {TEXT}; font-size: 15px; font-weight: 700; background: transparent; }}
#PackTitle {{ color: {TEXT}; font-size: 14px; font-weight: 600; background: transparent; }}
#PackStatus {{ color: {TEXT_DIM}; font-size: 12px; background: transparent; }}
#PackPercent {{ color: {TEXT}; font-size: 22px; font-weight: 700; background: transparent; }}
#TileTitle {{ color: {TEXT}; font-size: 13px; font-weight: 600; background: transparent; }}
#Muted {{ color: {TEXT_MUTED}; font-size: 12px; background: transparent; }}
#Chip {{
    background-color: {BG_HOVER};
    border-radius: 9px;
    padding: 2px 8px;
    color: {TEXT_DIM};
    font-size: 11px;
}}
#SpeedChip {{
    background-color: {BG_HOVER};
    border-radius: 10px;
    padding: 3px 10px;
    color: {TEXT};
    font-size: 12px;
}}

/* ---------------------------------------------------------------- 卡片 */
#PackCard, #PackTile {{
    background-color: {BG};
    border: 1px solid {BORDER_SOFT};
    border-radius: 8px;
}}
#PackCard:hover, #PackTile:hover {{ border: 1px solid {BORDER}; }}
#PackTile[selected="true"] {{ border: 1px solid {ACCENT}; }}

/* -------------------------------------------------------------- 进度条 */
QProgressBar#PackProgress {{
    background-color: {TRACK};
    border: none;
    border-radius: 5px;
    height: 10px;
    text-align: center;
    color: transparent;
}}
QProgressBar#PackProgress::chunk {{ background-color: {ACCENT}; border-radius: 5px; }}

/* ---------------------------------------------------------------- 按钮 */
QPushButton {{
    background-color: {BG_HOVER};
    border: 1px solid {BORDER};
    border-radius: {RADIUS}px;
    padding: 6px 14px;
    color: {TEXT};
}}
QPushButton:hover {{ border-color: {ACCENT}; }}
QPushButton:pressed {{ background-color: {BG_RAIL}; }}
QPushButton:disabled {{ color: {TEXT_MUTED}; border-color: {BORDER_SOFT}; background-color: transparent; }}
QPushButton#Primary {{
    background-color: {ACCENT};
    border: none;
    color: #ffffff;
    font-weight: 600;
    padding: 7px 16px;
}}
QPushButton#Primary:hover {{ background-color: {ACCENT_HOVER}; }}
QPushButton#Primary:disabled {{ background-color: {TRACK}; color: {TEXT_MUTED}; }}
QPushButton#Ghost {{ background-color: transparent; border: none; color: {TEXT_DIM}; padding: 4px 6px; }}
QPushButton#Ghost:hover {{ color: {TEXT}; background-color: {BG_HOVER}; border-radius: 4px; }}

/* -------------------------------------------------------------- 下拉框 */
QComboBox QAbstractItemView {{
    background-color: {BG_MENU};
    border: 1px solid {BORDER};
    color: {TEXT_DIM};
    selection-background-color: {ACCENT};
    selection-color: #ffffff;
    outline: none;
    padding: 4px;
}}

/* ------------------------------------------------------------ 滚动条 */
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 0; }}
QScrollBar::handle:vertical {{ background: #4a4a4a; border-radius: 5px; min-height: 32px; }}
QScrollBar::handle:vertical:hover {{ background: #5c5c5c; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 0; }}
QScrollBar::handle:horizontal {{ background: #4a4a4a; border-radius: 5px; min-width: 32px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

/* ---------------------------------------------------------------- 其它 */
QToolTip {{
    background-color: {BG_CHROME};
    color: {TEXT};
    border: 1px solid {BORDER};
    padding: 4px 8px;
}}
QLineEdit {{
    background-color: {BG};
    border: 1px solid {BORDER};
    border-radius: {RADIUS}px;
    padding: 6px 10px;
    color: {TEXT};
    selection-background-color: {ACCENT};
    selection-color: #ffffff;
}}
QLineEdit:focus {{ border: 1px solid {ACCENT}; }}
QLineEdit[readOnly="true"] {{ color: {TEXT_MUTED}; }}
QSpinBox {{
    background-color: {BG};
    border: 1px solid {BORDER};
    border-radius: {RADIUS}px;
    padding: 6px 8px;
    color: {TEXT};
}}
QStatusBar {{ background-color: {BG_CHROME}; color: {TEXT_MUTED}; }}
QStatusBar::item {{ border: none; }}
QSplitter::handle {{ background-color: {BORDER_SOFT}; }}
QCheckBox {{ background: transparent; spacing: 8px; }}
QCheckBox::indicator {{ width: 16px; height: 16px; border: 1px solid {BORDER}; border-radius: 4px; background: {BG}; }}
QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}
"""


def apply(app) -> None:
    """给 QApplication 装上深色配色 + 样式表。

    用 Fusion 风格打底：Windows 原生风格对样式表支持不全，
    换掉之后各控件（下拉、滚动条、按钮）都能按我们的颜色画。
    """
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(BG))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(TEXT_DIM))
    palette.setColor(QPalette.ColorRole.Base, QColor(BG))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(BG_HOVER))
    palette.setColor(QPalette.ColorRole.Text, QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Button, QColor(BG_HOVER))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(TEXT))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(BG_CHROME))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(TEXT))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(TEXT_MUTED))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(ACCENT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Link, QColor(ACCENT_HOVER))
    app.setPalette(palette)
    app.setStyleSheet(STYLESHEET)
