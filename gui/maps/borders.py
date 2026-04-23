# Module Name: gui.maps.outline
# Description: QGraphicsObject wrapping a shapely Polygon as a state border

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets


class Borders(QtWidgets.QGraphicsObject):
    """
    Renders one shapely Polygon as a filled path on the map scene.

    Non-interactive; user interactions are handled by the Overlay markers instead.
    """

    def __init__(
        self,
        poly,
        minx: float,
        maxy: float,
        zoom: float = 10.0,
        state_name: str = "",
    ) -> None:

        # Initialize the base-class (QGraphicsObject)
        super().__init__()
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setAcceptHoverEvents(False)
        self.setZValue(-10)

        self._minx = minx
        self._maxy = maxy
        self._zoom = zoom
        self._state_name = state_name
        self.setObjectName(state_name)

        # Simplify polygon geometry for rendering performance
        self._poly = poly.simplify(0.001, preserve_topology=True)
        self._path = QtGui.QPainterPath()
        self._bounds: QtCore.QRectF | None = None

        # Cached brush
        self._pen = QtGui.QPen(QtGui.QColor(0xFFFFFF), 1.5)
        self._brush = QtGui.QBrush(QtGui.QColor(0x333E41))

        self._build_path()

    def _coord_to_scene(self, lon: float, lat: float) -> tuple[float, float]:
        x = (lon - self._minx) * self._zoom
        y = (self._maxy - lat) * self._zoom
        return x, y

    def _build_path(self) -> None:
        coords = list(self._poly.exterior.coords)
        if not coords:
            return

        x0, y0 = self._coord_to_scene(coords[0][0], coords[0][1])
        self._path.moveTo(x0, y0)
        for lon, lat in coords[1:]:
            x, y = self._coord_to_scene(lon, lat)
            self._path.lineTo(x, y)
        self._path.setFillRule(QtCore.Qt.FillRule.OddEvenFill)
        self._path.closeSubpath()

    # ------------------------------------------------------------------
    # QGraphicsObject interface
    # ------------------------------------------------------------------

    def boundingRect(self) -> QtCore.QRectF:

        return self._bounds or (
            self._path.boundingRect().adjusted(-0.5, -0.5, 0.5, 0.5)
            if not self._path.isEmpty()
            else QtCore.QRectF()
        )

    def shape(self) -> QtGui.QPainterPath:
        return self._path

    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionGraphicsItem,
        widget=None,
    ) -> None:

        painter.setPen(self._pen)
        painter.setBrush(self._brush)
        painter.drawPath(self._path)

