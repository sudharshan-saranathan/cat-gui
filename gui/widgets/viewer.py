# Module Name: gui.widgets.viewer
# Description: QGraphicsView-based graph viewer widget.

from __future__ import annotations

# PySide6 (Python/Qt)
from PySide6 import QtGui
from PySide6 import QtCore
from PySide6 import QtWidgets
from PySide6 import QtOpenGLWidgets


class Viewer(QtWidgets.QGraphicsView):

    """
    A QGraphicsView-based viewer for displaying graphics scenes.

    Features:
    - Smooth zooming and panning animations
    - OpenGL viewport for hardware acceleration
    - Keyboard and mouse event handling for intuitive navigation
    - Standard shortcuts (Undo, Redo, Copy, Paste) passed to the scene
    """

    def __init__(self, **kwargs):

        # 1. Extract custom parameters and initialize zoom attributes
        graph_uuid = kwargs.pop("graph_uuid", None)

        self._zooming_attrs = {
            "val": 1.0,
            "max": 2.0,
            "min": 0.2,
            "exp": 1.4,
        }
        self._auto_fit_pending = True

        # 2. Initialize base class and animations
        super().__init__(**kwargs)

        self._zoom_anim = QtCore.QPropertyAnimation(self, b"zoom")
        self._zoom_anim.setEasingCurve(QtCore.QEasingCurve.Type.OutExpo)
        self._zoom_anim.setDuration(360)

        self._focus_anim = QtCore.QPropertyAnimation(self, b"center")
        self._focus_anim.setEasingCurve(QtCore.QEasingCurve.Type.InOutCubic)
        self._focus_anim.setDuration(720)

        # 3. Configure OpenGL viewport for hardware acceleration
        if kwargs.get("opengl", True):
            self._setup_opengl_viewport()

        # 4. Create canvas and load graph
        from gui.graph import Canvas

        canvas = Canvas()
        self.setScene(canvas)

        if not graph_uuid:
            import uuid

            graph_uuid = uuid.uuid4().hex
        canvas.load_graph(graph_uuid)

        # 5. Register keyboard shortcuts for navigation and editing
        QtGui.QShortcut(
            QtGui.QKeySequence("Ctrl+="), self, lambda: self.execute_zoom(1.2, True)
        )
        QtGui.QShortcut(
            QtGui.QKeySequence("Ctrl+-"), self, lambda: self.execute_zoom(0.8, True)
        )
        QtGui.QShortcut(
            QtGui.QKeySequence.StandardKey.Undo, self, self._shortcut_handler
        )
        QtGui.QShortcut(
            QtGui.QKeySequence.StandardKey.Redo, self, self._shortcut_handler
        )
        QtGui.QShortcut(
            QtGui.QKeySequence.StandardKey.Copy, self, self._shortcut_handler
        )
        QtGui.QShortcut(
            QtGui.QKeySequence.StandardKey.Paste, self, self._shortcut_handler
        )
        QtGui.QShortcut(
            QtGui.QKeySequence.StandardKey.Delete, self, self._shortcut_handler
        )

        # 6. Connect to application's viewer control signals
        app = QtWidgets.QApplication.instance()
        if hasattr(app, "view_ctrl"):
            app.view_ctrl.focus_item.connect(self._on_item_focused)

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        """Auto-fit freshly opened graph tabs once the view has a real size."""

        super().showEvent(event)
        if self._auto_fit_pending:
            self._auto_fit_pending = False
            QtCore.QTimer.singleShot(0, self.fit_scene_contents)

    @QtCore.Slot()
    def _setup_opengl_viewport(self) -> None:

        """
        Configure OpenGL viewport with MSAA for hardware acceleration.
        """

        # Configure 4x MSAA surface format
        self._format = QtGui.QSurfaceFormat()
        self._format.setSamples(4)

        # Create and configure OpenGL widget
        self._openGL_viewport = QtOpenGLWidgets.QOpenGLWidget(self)
        self._openGL_viewport.setFormat(self._format)
        self._openGL_viewport.setMouseTracking(True)
        self.setViewport(self._openGL_viewport)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:

        """
        Handle keyboard press events for view manipulation.
        """

        # Configure drag mode and cursor based on modifier keys
        if event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier:
            self.setDragMode(QtWidgets.QGraphicsView.DragMode.RubberBandDrag)
            self.setCursor(QtCore.Qt.CursorShape.CrossCursor)

        if event.modifiers() == QtCore.Qt.KeyboardModifier.ShiftModifier:
            self.setCursor(QtCore.Qt.CursorShape.OpenHandCursor)
            self.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)

        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QtGui.QKeyEvent) -> None:

        """
        Handle keyboard release events.
        """

        # Reset cursor and drag mode
        self.unsetCursor()
        self.setDragMode(QtWidgets.QGraphicsView.DragMode.NoDrag)
        super().keyReleaseEvent(event)

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:

        """
        Handle mouse wheel events for zooming.
        """

        # Calculate zoom factor from wheel delta
        delta = event.angleDelta().y()
        delta = self._zooming_attrs["exp"] ** (delta / 100.0)

        self.execute_zoom(
            delta, event.deviceType() == QtGui.QInputDevice.DeviceType.Mouse
        )

    @QtCore.Slot()
    def _shortcut_handler(self) -> None:

        """
        Route standard shortcuts to the scene.
        """

        sender = self.sender()
        if not isinstance(sender, QtGui.QShortcut):
            return

        key_seq = sender.key().toString()
        scene = self.scene()
        if scene is None:
            return

        # Route shortcuts to scene methods based on key sequence
        if key_seq == QtGui.QKeySequence(
            QtGui.QKeySequence.StandardKey.Copy
        ).toString() and hasattr(scene, "clone_items"):
            scene.clone_items()

        if key_seq == QtGui.QKeySequence(
            QtGui.QKeySequence.StandardKey.Paste
        ).toString() and hasattr(scene, "paste_items"):
            scene.paste_items()

        elif key_seq == QtGui.QKeySequence(
            QtGui.QKeySequence.StandardKey.Undo
        ).toString() and hasattr(scene, "undo"):
            scene.undo()

        elif key_seq == QtGui.QKeySequence(
            QtGui.QKeySequence.StandardKey.Redo
        ).toString() and hasattr(scene, "redo"):
            scene.redo()

        elif key_seq == QtGui.QKeySequence(
            QtGui.QKeySequence.StandardKey.Delete
        ).toString() and hasattr(scene, "delete_items"):
            scene.delete_items()

    @QtCore.Property(float)
    def zoom(self) -> float:

        """
        Get the current zoom level (read-only property).
        """

        return self._zooming_attrs["val"]

    @zoom.setter
    def zoom(self, value: float) -> None:

        """
        Set the zoom level and apply scale transformation.

        Args:
            value: Target zoom level to apply.
        """

        # Calculate scale factor and apply transformation
        factor = value / self._zooming_attrs["val"]
        self.scale(factor, factor)
        self._zooming_attrs["val"] = value

    def execute_zoom(self, factor: float, animate: bool = True, /) -> None:

        """
        Execute a zoom operation with optional animation.

        Clamps the resulting zoom level to the configured min/max bounds before applying.

        Args:
            factor: Zoom multiplication factor to apply.
            animate: Whether to animate the zoom transition (default: True).
        """

        # Cancel ongoing zoom animation to prevent conflicts
        if self._zoom_anim.state() == QtCore.QPropertyAnimation.State.Running:
            self._zoom_anim.stop()

        # Calculate target zoom level and clamp to allowed range
        target = self._zooming_attrs["val"] * factor
        target = max(
            self._zooming_attrs["min"], min(self._zooming_attrs["max"], target)
        )

        # Apply zoom with or without animation
        if animate:
            self._zoom_anim.setStartValue(self._zooming_attrs["val"])
            self._zoom_anim.setEndValue(target)
            self._zoom_anim.start()
        else:
            self.zoom = target

    @QtCore.Slot()
    def fit_scene_contents(self) -> None:
        """Fit all visible scene contents into the viewport."""

        scene = self.scene()
        if scene is None:
            return

        rect = scene.itemsBoundingRect()
        if rect.isNull() or rect.isEmpty():
            return

        padded = rect.adjusted(-40, -40, 40, 40)
        self.resetTransform()
        self._zooming_attrs["val"] = 1.0
        self.fitInView(padded, QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        self._zooming_attrs["val"] = self.transform().m11()

    @QtCore.Property(QtCore.QPointF)
    def center(self) -> QtCore.QPointF:

        """
        Get the center point of the current view (read-only property).
        """

        return self.mapToScene(self.viewport().rect().center())

    @center.setter
    def center(self, value: QtCore.QPointF) -> None:

        """
        Set the center point of the view.
        """

        self.centerOn(value)

    def _on_item_focused(self, item: QtWidgets.QGraphicsObject) -> None:

        """
        Handle item focus signal by animating the view to center on the item.
        """

        # Get current and target positions
        item_pos = item.mapToScene(item.boundingRect().center())
        view_pos = self.mapToScene(self.viewport().rect().center())

        # Animate view to center on item
        self._focus_anim.stop()
        self._focus_anim.setStartValue(view_pos)
        self._focus_anim.setEndValue(item_pos)
        self._focus_anim.start()
