# Module Name: gui.widgets.window
# Description: Provides a custom, frameless, draggable QMainWindow for the GUI

from dataclasses import dataclass

# PySide6 (Python/Qt)
from PySide6 import QtGui
from PySide6 import QtCore
from PySide6 import QtWidgets

# gui.widgets
from gui.widgets.traffic import TrafficLights


class FramelessWindow(QtWidgets.QMainWindow):

    @dataclass
    class Appearance:
        borderline: QtGui.QPen
        background: QtGui.QBrush

    @dataclass
    class Geometry:
        border_radius: int
        size: QtCore.QSize

    @dataclass
    class Behavior:
        pass

    def __init__(self, **kwargs):

        # 1. Initialize base class
        super().__init__()
        super().setObjectName("window")

        # 2. Initialize default options, flags, and other necessary attributes
        self._initialize_defaults()

        # 3. Initialize UI components
        self._init_menubar()
        self._init_status()

    def _initialize_defaults(self) -> None:

        # 1. Set appearance
        self._appearance = FramelessWindow.Appearance(
            borderline=QtGui.QPen(QtGui.QColor(0x363E41), 1.0),
            background=QtGui.QBrush(QtGui.QColor(0x232A2E)),
        )

        # 2. Set geometry
        self._geometry = FramelessWindow.Geometry(
            border_radius=10,
            size=QtCore.QSize(1200, 900),
        )

        # 3. Set behavior
        self._behavior = FramelessWindow.Behavior()

        # 4. Configure window attributes and flags
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
        self.setProperty("dragged_via_menubar", False)
        self.setProperty("mouse_press_pos", QtCore.QPointF())

    def _init_menubar(self) -> None:

        # 1. Create and configure traffic lights widget
        self._traffic = TrafficLights(self)
        self._traffic.minimize_clicked.connect(self.showMinimized)
        self._traffic.maximize_clicked.connect(self._on_maximize)
        self._traffic.close_clicked.connect(self.close)

        # 2. Configure menubar and set corner widget
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        menubar.setCornerWidget(self._traffic)

        # 3. Install event filters for window dragging via menubar
        menubar.installEventFilter(self)
        self._traffic.installEventFilter(self)

    def _init_status(self) -> None:

        # Create and set status bar
        self._status = QtWidgets.QStatusBar()
        self.setStatusBar(self._status)

    @QtCore.Slot()
    def _execute(self) -> None:

        """
        Handle toolbar action button clicks.

        This slot is invoked when an action from the toolbar is triggered either programmatically
        or by user interaction. Implement specific behavior based on the triggered action.
        """

        pass

    @QtCore.Slot()
    def _on_maximize(self) -> None:

        """
        Toggle the window between normal and maximized states.
        """

        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:

        """
        Handle mouse press events for window dragging.

        Stores the initial left-button click position for use in window dragging via the menubar.

        Args:
            event: The mouse press event.
        """

        super().mousePressEvent(event)
        if event.isAccepted():
            return

        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.setProperty("mouse_press_pos", event.position())

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:

        """
        Handle mouse move events for window dragging.

        Moves the window by calculating the delta between the current and initial mouse positions
        when dragged via the menubar with the left button pressed.

        Args:
            event: The mouse move event.
        """

        if event.buttons() & QtCore.Qt.MouseButton.LeftButton and self.property(
            "dragged_via_menubar"
        ):
            if click_position := self.property("mouse_press_pos"):
                delta = event.position() - click_position
                delta_point = delta.toPoint()
                self.move(self.pos() + delta_point)

        super().mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent) -> None:

        """
        Handle double-click events on the menubar to toggle maximize.

        Double-clicking a blank area of the menubar toggles the window between normal and
        maximized states, similar to native window manager behavior.

        Args:
            event: The double-click event.
        """

        if event.button() != QtCore.Qt.MouseButton.LeftButton:
            return super().mouseDoubleClickEvent(event)

        self._on_maximize()
        return super().mouseDoubleClickEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:

        """
        Handle mouse release events to end window dragging.

        Clears the window dragging state when the left mouse button is released, stopping
        any active window drag operation.

        Args:
            event: The mouse release event.
        """

        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.setProperty("dragged_via_menubar", False)
            self.setProperty("mouse_press_pos", None)

        super().mouseReleaseEvent(event)

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:

        """
        Filter events from the menubar to enable window dragging.

        Intercepts mouse events on blank areas of the menubar to allow window dragging and
        maximize toggling. Events that occur over menu items are allowed to pass through normally.

        Args:
            watched: The object being watched.
            event: The event to filter.

        Returns:
            True if the event was handled, False otherwise.
        """

        # 1. Validate event type
        if not isinstance(event, QtGui.QMouseEvent):
            return super().eventFilter(watched, event)

        event_type = event.type()
        if event_type not in (
            QtCore.QEvent.Type.MouseButtonPress,
            QtCore.QEvent.Type.MouseMove,
            QtCore.QEvent.Type.MouseButtonDblClick,
            QtCore.QEvent.Type.MouseButtonRelease,
        ):
            return super().eventFilter(watched, event)

        menubar = self.menuBar()
        if menubar is None:
            return super().eventFilter(watched, event)

        # 2. Get global position for hit-testing
        global_pos_f = event.globalPosition()
        global_pos = global_pos_f.toPoint()

        # 3. Handle release event - always clear drag state
        if event_type == QtCore.QEvent.Type.MouseButtonRelease and self.property(
            "dragged_via_menubar"
        ):
            local_window = QtCore.QPointF(self.mapFromGlobal(global_pos))
            forwarded = QtGui.QMouseEvent(
                event_type,
                local_window,
                local_window,
                global_pos_f,
                event.button(),
                event.buttons(),
                event.modifiers(),
            )
            self.mouseReleaseEvent(forwarded)
            self.setProperty("dragged_via_menubar", False)
            self.setProperty("mouse_press_pos", None)
            return True

        # 4. Handle events over blank menubar areas
        action = menubar.actionAt(menubar.mapFromGlobal(global_pos))
        if action is None:
            local_window = QtCore.QPointF(self.mapFromGlobal(global_pos))
            forwarded = QtGui.QMouseEvent(
                event_type,
                local_window,
                local_window,
                global_pos_f,
                event.button(),
                event.buttons(),
                event.modifiers(),
            )

            if event_type == QtCore.QEvent.Type.MouseButtonPress:
                self.setProperty("dragged_via_menubar", True)
                self.setProperty("mouse_press_pos", local_window)
                self.mousePressEvent(forwarded)
                return True

            if event_type == QtCore.QEvent.Type.MouseMove:
                if self.property("dragged_via_menubar"):
                    self.mouseMoveEvent(forwarded)
                    return True
                return super().eventFilter(watched, event)

            if event_type == QtCore.QEvent.Type.MouseButtonDblClick:
                self.mouseDoubleClickEvent(forwarded)

        return super().eventFilter(watched, event)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:

        """Paint the main window with a rounded rectangle background."""

        painter = QtGui.QPainter(self)
        painter.setBrush(self._appearance.background)
        painter.setPen(self._appearance.borderline)

        painter.drawRoundedRect(
            self.rect(),
            self._geometry.border_radius,
            self._geometry.border_radius,
        )

        super().paintEvent(event)
