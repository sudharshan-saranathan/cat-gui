# Filename: __init__.py
# Module name: graph
# Description: Edge item for displaying graph connections.

"""Edge item for displaying graph connections."""

from PySide6 import QtCore, QtGui, QtWidgets
from gui.graph.reusable.image import Image
from dataclasses import dataclass
import weakref

ItemState = QtWidgets.QStyle.StateFlag


class EdgeRepr(QtWidgets.QGraphicsObject):
    """Edge item for displaying graph connections."""

    @dataclass
    class Appearance:
        """Edge styling options.

        Attributes:
            width: Line width in pixels.
            slack: The Bézier curve's slack factor.
            pen: The vector's pen style.
        """

        width: float
        slack: float
        pen: dict[ItemState, QtGui.QPen]

    @dataclass
    class Geometry:
        """Geometric options for the edge."""

        pass

    @dataclass
    class Behavior:
        """Behavioral flags for the edge."""

        pass

    def __init__(
        self,
        euid: str,
        origin=None,
        target=None,
        source_tech_id: str = None,
        target_tech_id: str = None,
    ):
        super().__init__(None)

        # 1. Initialize class members
        self._uid = euid
        self._path = QtGui.QPainterPath()
        self._arrow = Image(":/svg/arrow.svg", parent=self)
        self._source_tech_id = source_tech_id
        self._target_tech_id = target_tech_id

        # 2. Initialize defaults
        self._init_defaults()

        # 3. Initialize properties and animations
        self._init_attr()
        self._init_anim()
        self._init_endpoints(origin, target)

        # 4. Toggle flags
        graphics_item_flag = QtWidgets.QGraphicsItem.GraphicsItemFlag
        self.setFlag(graphics_item_flag.ItemIsSelectable)

        # 5. Config dialog (lazy init)
        from gui.graph.edge.config import EdgeConfigWidget

        self._configurator = EdgeConfigWidget()

    def _init_defaults(self) -> None:
        """Initialize default values for appearance."""
        self._appearance = EdgeRepr.Appearance(
            width=3.0,
            slack=0.4,
            pen={
                ItemState.State_Enabled: QtGui.QPen(QtGui.QColor(0xBEBEBE)),
                ItemState.State_Selected: QtGui.QPen(QtGui.QColor(0xFFCB00)),
            },
        )

    def _init_attr(self):

        self.setZValue(-10)
        self.setPos(QtCore.QPointF(0, 0))
        self.setAcceptHoverEvents(True)
        self.setProperty("linewidth", self._appearance.width)

    def _init_anim(self):
        """Initializes hover animation."""

        self._anim = QtCore.QPropertyAnimation(self, b"thickness")
        self._anim.setEasingCurve(QtCore.QEasingCurve.Type.OutQuad)
        self._anim.setDuration(360)

    def _init_endpoints(self, origin, target):
        """
        Initialize the vector's endpoints.

        Args:
            origin: Reference to the origin vertex.
            target: Reference to the target vertex.
        """
        self._origin = weakref.ref(origin) if origin else None
        self._target = weakref.ref(target) if target else None

        if self._origin and self._target:
            self._origin().item_shifted.connect(self._on_endpoint_shifted)
            self._target().item_shifted.connect(self._on_endpoint_shifted)

            # Get endpoint positions, using tech handles if available
            origin_pos = self._origin().scenePos()
            target_pos = self._target().scenePos()
            self.update_path(origin_pos, target_pos)

    def boundingRect(self) -> QtCore.QRectF:
        return self._path.boundingRect().adjusted(-4, -4, 4, 4)

    def shape(self):
        stroker = QtGui.QPainterPathStroker()
        current_width = self.property("linewidth") or self._appearance.width
        stroker.setWidth(current_width + 12)
        return stroker.createStroke(self._path)

    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionGraphicsItem,
        widget: QtWidgets.QWidget | None = None,
    ) -> None:

        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.RenderHint.SmoothPixmapTransform)

        pen = self._appearance.pen[
            ItemState.State_Selected if self.isSelected() else ItemState.State_Enabled
        ]
        pen.setWidthF(self.property("linewidth") or self._appearance.width)
        painter.setPen(pen)
        painter.drawPath(self._path)

    def hoverEnterEvent(self, event, /):
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._anim.stop()
        self._anim.setStartValue(self._appearance.width)
        self._anim.setEndValue(self._appearance.width + 1.0)
        self._anim.start()

    def hoverLeaveEvent(self, event, /):
        self.unsetCursor()
        self._anim.stop()
        self._anim.setStartValue(self._appearance.width + 1.0)
        self._anim.setEndValue(self._appearance.width)
        self._anim.start()

    @staticmethod
    def _compute(
        origin: QtCore.QPointF,
        target: QtCore.QPointF,
    ) -> QtGui.QPainterPath:

        path = QtGui.QPainterPath()
        path.moveTo(origin)

        # Calculate control points for a quadratic curve
        ctrl_ptx = origin.x() + (target.x() - origin.x()) * 0.5
        ctrl_pty = origin.y() + (target.y() - origin.y()) * 0.5
        # ctrl_pty -= 20 if target.x() > origin.x() else -20
        path.quadTo(ctrl_ptx, ctrl_pty, target.x(), target.y())

        return path

    def update_path(self, origin: QtCore.QPointF, target: QtCore.QPointF):
        """
        Update the path between two points.

        When the origin/target vertex references are available, the method automatically
        determines the correct flow direction by comparing provided coordinates
        with stored vertex positions.

        Args:
            origin: Origin point coordinate
            target: Target point coordinate
        """
        self.prepareGeometryChange()

        # If we have stored vertex references, check if coordinates are swapped:
        if self._origin is not None and self._target is not None:
            true_origin_pos = self._origin().scenePos()
            true_target_pos = self._target().scenePos()

            # Convert to QPoint (integers) to avoid floating point comparison issues:
            origin_int = origin.toPoint()
            target_int = target.toPoint()
            true_origin_int = true_origin_pos.toPoint()
            true_target_int = true_target_pos.toPoint()

            # If origin matches target and target matches origin, they're swapped:
            if origin_int == true_target_int and target_int == true_origin_int:
                origin, target = target, origin  # Swap to correct order

        self._path.clear()
        self._path = self._compute(origin, target)

        # Position arrow at 50% along the path
        self._arrow.setPos(self._path.pointAtPercent(0.50))

        # Arrow always points in the origin -> target direction
        angle = -self._path.angleAtPercent(0.5)
        self._arrow.setRotation(angle)
        self.update()

    def clear(self):
        self._arrow.setPos(QtCore.QPointF())
        self._path.clear()

    @QtCore.Slot(QtCore.QPointF)
    def _on_endpoint_shifted(self, pos: QtCore.QPointF) -> None:

        if self._origin and self._target:
            origin = self._origin().scenePos()
            target = self._target().scenePos()
            self.update_path(origin, target)

    @QtCore.Property(float)
    def thickness(self) -> float:
        return self.property("linewidth")

    @thickness.setter
    def thickness(self, value: float) -> None:
        self.setProperty("linewidth", value)
        self.prepareGeometryChange()
        self.update()

    def mouseDoubleClickEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """Show EdgeConfig dialog on double-click."""
        if not self._origin or not self._target:
            return

        src_node = self._origin()
        tgt_node = self._target()

        if not src_node or not tgt_node:
            return

        # Emit item-focused signal to center viewer on this edge's midpoint
        app = QtWidgets.QApplication.instance()
        if app and hasattr(app, "view_ctrl"):
            app.view_ctrl.focus_item.emit(self)

        # Get canvas and unit uuid
        scene = self.scene()
        if not scene:
            return

        unit_uuid = getattr(scene, "_graph_guid", None)
        if not unit_uuid:
            return

        src_nuid = src_node._uid
        tgt_nuid = tgt_node._uid

        src_path = f"{unit_uuid}/{src_nuid}"
        tgt_path = f"{unit_uuid}/{tgt_nuid}"

        # Set parent and fetch data
        if not self._configurator.parent():
            if app:
                self._configurator.setParent(app.activeWindow())

        self._configurator.fetch_and_populate(src_path, tgt_path)
        self._configurator.raise_()
        self._configurator.show()

    def set_active(self, active: bool) -> None:
        """Solid black when the active link, solid light grey when no link."""
        if active:
            pen = QtGui.QPen(QtGui.QColor(0x000000), self._appearance.width)  # black
            pen.setStyle(QtCore.Qt.PenStyle.SolidLine)
        else:
            pen = QtGui.QPen(QtGui.QColor(0xCCCCCC), self._appearance.width)  # light grey
            pen.setStyle(QtCore.Qt.PenStyle.SolidLine)
            pen.setOpacity(0.5)

        self._appearance.pen[ItemState.State_Enabled] = pen
        self.update()

    @property
    def uid(self) -> str:
        return self._uid
