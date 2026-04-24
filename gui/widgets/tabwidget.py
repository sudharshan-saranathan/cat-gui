# Module Name: gui.widgets.tabwidget
# Description: A reusable tab widget with optional template-aware mode.

from __future__ import annotations
from dataclasses import dataclass
import logging

from qtawesome import icon as qta_icon
from PySide6 import QtGui, QtCore, QtWidgets

from gui.widgets.field import Field
from gui.widgets.toolbar import ToolBar


class TabWidget(QtWidgets.QTabWidget):
    """
    Custom tab widget with configurable appearance and keyboard shortcuts.

    Extends QTabWidget with custom styling options and keyboard shortcuts:
    - Ctrl+T: Create new tab
    - Ctrl+W: Close current tab
    - Ctrl+Left: Navigate to previous tab
    - Ctrl+Right: Navigate to the next tab
    - Ctrl+R: Rename current tab

    When template_mode=True, Ctrl+T prompts for a template name and queries/creates
    the template on the server before opening it. When False, creates a blank tab.
    """

    @dataclass
    class Appearance:
        icon_size: QtCore.QSize
        background: QtGui.QBrush

    @dataclass
    class Geometry:
        tab_position: QtWidgets.QTabWidget.TabPosition

    @dataclass
    class Behavior:
        tabs_closable: bool
        movable: bool

    def __init__(self, parent=None, template_mode: bool = False, **kwargs):
        """
        Initialize the tab widget with optional template mode.

        Args:
            parent: Parent widget (optional).
            template_mode: If True, Ctrl+T prompts for template name and queries server.
                          If False, Ctrl+T creates a blank tab (default: False).
            **kwargs: Configuration options (icon_size, tab_position, tabs_closable, movable).
        """

        # 1. Initialize mode and logger
        self._template_mode = template_mode
        self._logger = logging.getLogger("TabWidget")
        self._kwargs = kwargs
        self._new_editor_handler = kwargs.get("new_editor_handler")
        self._push_blueprint_handler = kwargs.get("push_blueprint_handler")

        # 2. Initialize defaults and configure base class
        self._init_defaults()

        super().__init__(
            parent,
            movable=self._behavior.movable,
            iconSize=self._appearance.icon_size,
            tabPosition=self._geometry.tab_position,
            tabsClosable=self._behavior.tabs_closable,
        )

        # 3. Set up keyboard shortcuts for tab management
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+T"), self, self._request_new_editor)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+W"), self, self.remove_tab)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Left"), self, self._go_to_prev_tab)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Right"), self, self._go_to_next_tab)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+R"), self, self.rename_tab)

        # 4. Connect tab close button (X) to remove_tab
        self.tabCloseRequested.connect(self.remove_tab)

        # 4. Configure template mode with event bus connection
        if self._template_mode:
            from gui.bus import Relay

            bus = Relay.instance()
            bus.sig_open_widget.connect(self._on_open_widget)

            self._init_corner_widget()

    def _init_defaults(self) -> None:
        """Initialize default values for appearance, geometry, and behavior."""
        self._appearance = TabWidget.Appearance(
            icon_size=self._kwargs.get("icon_size", QtCore.QSize(16, 16)),
            background=QtGui.QBrush(
                QtGui.QColor(0x393E41), QtCore.Qt.BrushStyle.SolidPattern
            ),
        )
        self._geometry = TabWidget.Geometry(
            tab_position=self._kwargs.get(
                "tab_position", QtWidgets.QTabWidget.TabPosition.North
            ),
        )
        self._behavior = TabWidget.Behavior(
            tabs_closable=self._kwargs.get("tabs_closable", True),
            movable=self._kwargs.get("movable", True),
        )

    def create_tab(
        self,
        widget: QtWidgets.QWidget = None,
        icon: QtGui.QIcon = None,
        label: str = str(),
    ) -> None:
        """
        Create a new tab with the given widget.

        In template mode, prompts for template name, queries/creates on server.
        In generic mode, creates a blank tab if no widget provided.

        Args:
            widget: The widget to display in the new tab.
            icon: The icon to display in the tab (optional).
            label: The label text for the tab (optional).
        """

        count = self.count()

        # 1. Template mode: ask for the template name and query/create on server
        if self._template_mode and not widget:
            from gui.widgets.viewer import Viewer

            # Prompt user for template name
            template_name, ok = QtWidgets.QInputDialog.getText(
                self,
                "Open or Create Template",
                "Template name:",
                QtWidgets.QLineEdit.EchoMode.Normal,
                f"template-{count + 1}",
            )

            if not ok or not template_name.strip():
                self._logger.info("Template dialog cancelled by user")
                return

            template_name = template_name.strip()
            label = label or template_name

            # Check/create template on server
            try:
                from gui.compat import SysClient

                client = SysClient.instance()

                self._logger.info(f"Checking if template exists: {template_name}")
                check_response = client.send(
                    verb="get",
                    path=template_name,
                )

                template_exists = check_response and check_response.get("status") in (
                    "OK",
                    200,
                )

                if not template_exists:
                    self._logger.info(
                        f"Template not found, creating new template: {template_name}"
                    )
                    create_response = client.send(
                        verb="create",
                        path=template_name,
                        meta={},
                    )
                    if create_response and create_response.get("status") in (
                        "OK",
                        200,
                        201,
                    ):
                        self._logger.info(
                            f"Created new template on server: {template_name}"
                        )
                    else:
                        self._logger.warning(
                            f"Failed to create template on server: {create_response.get('info') if create_response else 'no response'} - proceeding with local canvas"
                        )

            except Exception as e:
                self._logger.warning(
                    f"Error checking/creating template on server: {e} - proceeding with local canvas"
                )

            # 2. Create viewer with the template name
            widget = Viewer(
                parent=self,
                graph_uuid=template_name,
                dragMode=QtWidgets.QGraphicsView.DragMode.NoDrag,
                viewportUpdateMode=QtWidgets.QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate,
                renderHints=QtGui.QPainter.RenderHint.Antialiasing,
                backgroundBrush=QtGui.QBrush(QtGui.QColor(0xEFEFEF)),
                sceneRect=QtCore.QRectF(0, 0, 2000, 2000),
            )

        # 3. Generic mode or widget provided: create a blank tab if no widget
        else:
            label = label or f"Tab {count + 1}"
            widget = widget or QtWidgets.QWidget()

        # 4. Add the tab
        self.addTab(widget, icon or QtGui.QIcon(), label)
        self.setCurrentIndex(count)

    def _request_new_editor(self) -> None:
        """Open a new editor tab using the configured handler when available."""
        if callable(self._new_editor_handler):
            self._new_editor_handler()
            return
        self.create_tab()

    def remove_tab(self, index: int = None) -> None:
        """
        Delete the tab at the specified index.

        Args:
            index: The index of the tab to delete (optional, default: current tab).
        """

        if index is None:
            index = self.currentIndex()
        if index < 0 or index >= self.count():
            return
        widget = self.widget(index)
        self.removeTab(index)
        if widget:
            widget.deleteLater()

    def rename_tab(self, index: int = None, label: str = None) -> None:
        """
        Rename the tab at the specified index.

        Args:
            index: The index of the tab to rename (optional, default: current tab).
            label: The new label for the tab (optional, default: prompt user).
        """

        # Validate index
        if index is None:
            index = self.currentIndex()

        if index < 0 or index >= self.count():
            return

        # Get new label from user if not provided
        if label is None:
            current_label = self.tabText(index)
            label, ok = QtWidgets.QInputDialog.getText(
                self,
                "Rename Tab",
                "Enter new tab name:",
                QtWidgets.QLineEdit.EchoMode.Normal,
                current_label,
            )
            if not ok or not label:
                return

        self.setTabText(index, label)

    def _go_to_prev_tab(self) -> None:
        """
        Navigate to the previous tab.
        """

        current = self.currentIndex()
        if current > 0:
            self.setCurrentIndex(current - 1)

    def _go_to_next_tab(self) -> None:
        """
        Navigate to the next tab.
        """

        current = self.currentIndex()
        if current < self.count() - 1:
            self.setCurrentIndex(current + 1)

    def _init_corner_widget(self) -> None:
        """
        Create and configure the corner toolbar (template mode only).
        """

        # 1. Create a toolbar with a new tab action
        actions = [
            (
                qta_icon("mdi.plus", color="gray", color_active="white"),
                "New Tab",
                self._request_new_editor,
            ),
        ]
        if callable(self._push_blueprint_handler):
            actions.append(
                (
                    qta_icon("mdi.upload", color="gray", color_active="white"),
                    "Push Blueprint",
                    self._push_blueprint_handler,
                )
            )

        toolbar = ToolBar(
            parent=self,
            actions=actions,
            trailing=True,
            floatable=False,
            movable=False,
            iconSize=QtCore.QSize(16, 16),
        )

        # 2. Add a finder field to the toolbar
        toolbar.addWidget(
            finder := Field(
                parent=toolbar,
                placeholderText="Find",
                clearButtonEnabled=True,
            )
        )
        finder.setObjectName("finder")
        finder.returnPressed.connect(self._find)

        # 3. Set the toolbar as a corner widget
        self.setCornerWidget(toolbar, QtCore.Qt.Corner.TopRightCorner)

    def _find(self) -> None:
        """
        Find functionality (template mode only).
        """

        from gui.widgets.viewer import Viewer

        # Get the finder field and current viewer
        toolbar = self.cornerWidget()
        finder = toolbar.findChild(Field, "finder") if toolbar else None
        string = finder.text() if finder else ""

        viewer = self.currentWidget()
        if isinstance(viewer, Viewer):
            canvas = viewer.scene()
            canvas.clearSelection()

        if finder:
            finder.clear()

    @QtCore.Slot(QtWidgets.QWidget, str, QtGui.QIcon)
    def _on_open_widget(
        self, widget: QtWidgets.QWidget, label: str, icon: QtGui.QIcon
    ) -> None:
        """
        Handle sig_open_widget signal to create new tabs (template mode only).
        """

        self.create_tab(widget=widget, icon=icon or QtGui.QIcon(), label=label)
