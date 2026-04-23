# Module Name: gui.maps.viewer
# Description: QGraphicsView with animated zoom/pan for the India map scene

from __future__ import annotations

import logging
from dataclasses import dataclass

from PySide6 import QtCore, QtGui, QtWidgets

from gui.maps.relay import MapsRelay
from gui.maps.scene import MapsScene

logger = logging.getLogger(__name__)


class MapsViewer(QtWidgets.QGraphicsView):
    """
    Hosts MapsScene with smooth animated zoom and Shift+drag panning.

    On startup it fetches template geo-coordinates from the server
    (via the supplied api_client) and passes them to MapsScene.populate_markers().
    """

    @dataclass
    class ZoomConfig:
        val: float = 1.0
        min: float = 0.2
        max: float = 4.0
        exp: float = 1.4

    def __init__(
        self,
        api_client=None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._api = api_client
        self._zoom = MapsViewer.ZoomConfig()

        # 1. Scene
        self._scene = MapsScene(api_client=api_client)
        self.setScene(self._scene)

        # 2. Rendering hints
        self.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QtGui.QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QtWidgets.QGraphicsView.DragMode.NoDrag)

        # 3. Animated zoom (exponential easing)
        self._zoom_anim = QtCore.QPropertyAnimation(self, b"zoom_level")
        self._zoom_anim.setEasingCurve(QtCore.QEasingCurve.Type.OutExpo)
        self._zoom_anim.setDuration(360)
        self._focus_anim = QtCore.QPropertyAnimation(self, b"center")
        self._focus_anim.setEasingCurve(QtCore.QEasingCurve.Type.InOutCubic)
        self._focus_anim.setDuration(720)

        # 4. Keyboard shortcuts
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+="), self, lambda: self._do_zoom(1.2))
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+-"), self, lambda: self._do_zoom(0.8))

        # 5. Subscribe to relay signals
        bus = MapsRelay.instance()
        bus.sig_map_rendered.connect(self._on_map_rendered)
        bus.sig_open_template.connect(self._on_open_template)

        app = QtWidgets.QApplication.instance()
        if hasattr(app, "view_ctrl"):
            app.view_ctrl.focus_item.connect(self._on_item_focused)

    # ------------------------------------------------------------------
    # Zoom property (used by QPropertyAnimation)
    # ------------------------------------------------------------------

    @QtCore.Property(float)
    def zoom_level(self) -> float:
        return self._zoom.val

    @zoom_level.setter
    def zoom_level(self, value: float) -> None:
        factor = value / self._zoom.val
        self.scale(factor, factor)
        self._zoom.val = value

    @QtCore.Property(QtCore.QPointF)
    def center(self) -> QtCore.QPointF:
        return self.mapToScene(self.viewport().rect().center())

    @center.setter
    def center(self, value: QtCore.QPointF) -> None:
        self.centerOn(value)

    def _do_zoom(self, factor: float, animate: bool = True) -> None:
        if self._zoom_anim.state() == QtCore.QAbstractAnimation.State.Running:
            self._zoom_anim.stop()

        target = max(self._zoom.min, min(self._zoom.max, self._zoom.val * factor))
        if animate:
            self._zoom_anim.setStartValue(self._zoom.val)
            self._zoom_anim.setEndValue(target)
            self._zoom_anim.start()
        else:
            self.zoom_level = target

    # ------------------------------------------------------------------
    # Qt events
    # ------------------------------------------------------------------

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        delta = self._zoom.exp ** (event.angleDelta().y() / 100.0)
        self._do_zoom(
            delta, animate=(event.deviceType() == QtGui.QInputDevice.DeviceType.Mouse)
        )

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.modifiers() == QtCore.Qt.KeyboardModifier.ShiftModifier:
            self.setCursor(QtCore.Qt.CursorShape.OpenHandCursor)
            self.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QtGui.QKeyEvent) -> None:
        self.unsetCursor()
        self.setDragMode(QtWidgets.QGraphicsView.DragMode.NoDrag)
        super().keyReleaseEvent(event)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    @QtCore.Slot()
    def _on_map_rendered(self) -> None:
        """Fetch template markers once the map polygons are ready."""
        self._scene._fetch_and_populate_markers()

    @QtCore.Slot(str, str)
    def _on_open_template(self, template_uid: str, plant_name: str) -> None:
        """Open a canvas tab for the double-clicked plant marker."""
        from gui.bus import Relay
        from gui.widgets.viewer import Viewer

        try:
            viewer = Viewer(graph_uuid=template_uid)
            Relay.instance().sig_open_widget.emit(viewer, plant_name, QtGui.QIcon())
        except Exception as e:
            logger.error(f"MapsViewer: cannot open template {template_uid!r}: {e}")

    @QtCore.Slot(QtWidgets.QGraphicsObject)
    def _on_item_focused(self, item: QtWidgets.QGraphicsObject) -> None:
        item_pos = item.mapToScene(item.boundingRect().center())
        view_pos = self.mapToScene(self.viewport().rect().center())

        self._focus_anim.stop()
        self._focus_anim.setStartValue(view_pos)
        self._focus_anim.setEndValue(item_pos)
        self._focus_anim.start()

    def scene(self) -> MapsScene:
        return self._scene
