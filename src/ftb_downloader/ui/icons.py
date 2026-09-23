"""线性图标：全部用 QPainter 现画，不依赖任何图片资源，颜色跟着主题走。

风格对齐官方 FTB App 左侧栏那套 2px 圆头线性图标。
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

from ftb_downloader.ui import theme

_CANVAS = 24.0   # 图标按 24x24 的画布设计
_STROKE = 2.0


def _seg(*points: tuple[float, float]) -> QPainterPath:
    path = QPainterPath()
    path.moveTo(*points[0])
    for x, y in points[1:]:
        path.lineTo(x, y)
    return path


def _rounded(x: float, y: float, w: float, h: float, r: float) -> QPainterPath:
    path = QPainterPath()
    path.addRoundedRect(QRectF(x, y, w, h), r, r)
    return path


def _paint(p: QPainter, name: str, color: QColor) -> None:
    pen = QPen(color, _STROKE)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)

    if name == "plus":
        p.drawPath(_seg((12, 5), (12, 19)))
        p.drawPath(_seg((5, 12), (19, 12)))
    elif name == "download":
        p.drawPath(_seg((12, 3), (12, 15)))
        p.drawPath(_seg((7, 10), (12, 15), (17, 10)))
        p.drawPath(_seg((4.5, 20), (19.5, 20)))
    elif name == "home":
        p.drawPath(_seg((3, 11.5), (12, 3.5), (21, 11.5)))
        p.drawPath(_seg((5.5, 9.5), (5.5, 20.5), (18.5, 20.5), (18.5, 9.5)))
    elif name == "grid":
        for x, y in ((4, 4), (13.5, 4), (4, 13.5), (13.5, 13.5)):
            p.drawPath(_rounded(x, y, 6.5, 6.5, 1.8))
    elif name == "search":
        p.drawEllipse(QPointF(10.5, 10.5), 6.5, 6.5)
        p.drawPath(_seg((15.4, 15.4), (20.5, 20.5)))
    elif name == "list":
        for y in (6.0, 12.0, 18.0):
            p.drawPath(_seg((9.5, y), (20.0, y)))
        p.setBrush(color)
        for y in (6.0, 12.0, 18.0):
            p.drawEllipse(QPointF(4.8, y), 1.3, 1.3)
        p.setBrush(Qt.BrushStyle.NoBrush)
    elif name == "box":
        p.drawPath(_seg((12, 3), (20.5, 7.5), (20.5, 16.5), (12, 21), (3.5, 16.5), (3.5, 7.5), (12, 3)))
        p.drawPath(_seg((3.5, 7.5), (12, 12), (20.5, 7.5)))
        p.drawPath(_seg((12, 12), (12, 21)))
    elif name == "info":
        p.drawEllipse(QPointF(12, 12), 9, 9)
        p.drawPath(_seg((12, 11), (12, 16.5)))
        p.setBrush(color)
        p.drawEllipse(QPointF(12, 7.8), 1.15, 1.15)
        p.setBrush(Qt.BrushStyle.NoBrush)
    elif name == "settings":
        for y, knob in ((6.5, 15.0), (12.0, 9.0), (17.5, 13.5)):
            p.drawPath(_seg((3.5, y), (20.5, y)))
            p.drawPath(_seg((knob, y - 3.2), (knob, y + 3.2)))
    elif name == "close":
        p.drawPath(_seg((6.5, 6.5), (17.5, 17.5)))
        p.drawPath(_seg((17.5, 6.5), (6.5, 17.5)))
    elif name == "chevron-down":
        p.drawPath(_seg((6, 9.5), (12, 15.5), (18, 9.5)))
    elif name == "chevron-right":
        p.drawPath(_seg((9.5, 6), (15.5, 12), (9.5, 18)))
    elif name == "sort":
        p.drawPath(_seg((8, 20), (8, 4.5)))
        p.drawPath(_seg((4.5, 8), (8, 4.5), (11.5, 8)))
        p.drawPath(_seg((16, 4), (16, 19.5)))
        p.drawPath(_seg((12.5, 16), (16, 19.5), (19.5, 16)))
    elif name == "folder":
        p.drawPath(_seg((3.5, 19), (3.5, 6), (9.5, 6), (11.5, 8.5), (20.5, 8.5), (20.5, 19), (3.5, 19)))
    elif name == "bolt":
        path = QPainterPath()
        path.moveTo(13.5, 2.5)
        path.lineTo(5, 13.5)
        path.lineTo(11, 13.5)
        path.lineTo(10, 21.5)
        path.lineTo(19, 10.5)
        path.lineTo(12.8, 10.5)
        path.closeSubpath()
        p.setBrush(color)
        p.drawPath(path)
        p.setBrush(Qt.BrushStyle.NoBrush)
    elif name == "refresh":
        path = QPainterPath()
        path.arcMoveTo(QRectF(4, 4, 16, 16), 70)
        path.arcTo(QRectF(4, 4, 16, 16), 70, 285)
        p.drawPath(path)
        p.drawPath(_seg((12.5, 3.0), (17.5, 6.0), (14.5, 10.5)))
    elif name == "check":
        p.drawPath(_seg((5, 12.5), (10, 17.5), (19, 6.5)))
    elif name == "play":
        path = QPainterPath()
        path.moveTo(8, 5)
        path.lineTo(19, 12)
        path.lineTo(8, 19)
        path.closeSubpath()
        p.setBrush(color)
        p.drawPath(path)
        p.setBrush(Qt.BrushStyle.NoBrush)


def pixmap(name: str, color: str = theme.TEXT_DIM, size: int = 24, ratio: int = 2) -> QPixmap:
    """画一张图标位图（按 2 倍渲染，HiDPI 下不糊）。"""
    pm = QPixmap(size * ratio, size * ratio)
    pm.setDevicePixelRatio(float(ratio))
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    # 注意：QPainter 画在带 devicePixelRatio 的 QPixmap 上时已经按 DPR 缩放过一次，
    # 这里只要再按「逻辑尺寸 / 设计画布」缩放即可，别再乘 ratio（否则图标会画大一倍）。
    scale = size / _CANVAS
    painter.scale(scale, scale)
    _paint(painter, name, QColor(color))
    painter.end()
    return pm


def icon(name: str, color: str = theme.TEXT_DIM, size: int = 24) -> QIcon:
    return QIcon(pixmap(name, color, size))


def rounded(source: QPixmap, size: int, radius: int = 8) -> QPixmap:
    """把整合包封面裁成圆角正方形。"""
    scaled = source.scaled(
        size * 2,
        size * 2,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation,
    )
    scaled.setDevicePixelRatio(2.0)
    out = QPixmap(size * 2, size * 2)
    out.setDevicePixelRatio(2.0)
    out.fill(Qt.GlobalColor.transparent)
    painter = QPainter(out)  # 同上：画笔坐标已经是逻辑坐标
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, size, size), radius, radius)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, scaled)
    painter.end()
    return out
