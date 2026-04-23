# Module Name: gui.main_ui
# Description: The main UI of IITM-Climact.

from __future__ import annotations

# Built-ins
import logging
import json

# PySide6 (Python/Qt)
from PySide6 import QtCore, QtGui
from PySide6 import QtWidgets

# Climact modules
from gui.widgets import ToolBar, TabWidget
from gui.widgets.window import FramelessWindow

logger = logging.getLogger(__name__)


class MainGui(FramelessWindow):
    """
    Main application window with frameless design, docks, and tabs.
    """

    def __init__(self, api_client=None, **kwargs):

        # 1. Initialize base class
        super().__init__()
        self.setObjectName("main-window")
        self.api_client = api_client

        # 2. Initialize SysClient and relay
        from gui.compat import SysClient
        from gui.main_ui.bus import MainGuiRelay

        if api_client:

            SysClient._instance = SysClient(api_client)
            MainGuiRelay.instance().set_client(SysClient._instance)

        # 3. Configure menubar
        self._init_menus()

        # 4. Initialize UI components
        self._init_toolbar()
        self._init_docks()
        self._init_tabs()

        # 5. Load project if provided
        if kwargs.get("project"):
            self._load(kwargs["project"])

    def _init_toolbar(self) -> None:
        """Initialize the toolbar with action buttons."""

        import qtawesome as qta

        toolbar = ToolBar(
            self,
            style="QToolBar QToolButton {margin: 2px 2px 4px 2px;}",
            orientation=QtCore.Qt.Orientation.Vertical,
            iconSize=QtCore.QSize(24, 24),
            trailing=False,
            actions=[
                (
                    qta.icon("ph.layout-fill", color="#fef9ef"),
                    "Dock",
                    self._toggle_docks,
                ),
                (
                    qta.icon("ph.folder-fill", color="#ffcb77"),
                    "Open",
                    self._open_project_dialog,
                ),
                (qta.icon("mdi.function", color="cyan"), "Optimize", self._on_optimize),
                (qta.icon("mdi.chart-box", color="#fe6d73"), "Results", self._on_results),
                (qta.icon("ph.dots-three", color="#efefef"), "More", self._show_about),
            ],
        )

        self.addToolBar(QtCore.Qt.ToolBarArea.LeftToolBarArea, toolbar)

    def _init_menus(self) -> None:
        """Create and wire the main window menus."""

        menubar = self.menuBar()
        menubar.clear()

        file_menu = menubar.addMenu("&File")
        self._add_menu_action(
            file_menu,
            "&Open Project...",
            self._open_project_dialog,
            QtGui.QKeySequence.StandardKey.Open,
        )
        self._add_menu_action(
            file_menu,
            "&Save Graph As...",
            self._save,
            QtGui.QKeySequence.StandardKey.Save,
        )
        file_menu.addSeparator()
        self._add_menu_action(
            file_menu,
            "&New Template Tab",
            self._create_template_tab,
            QtGui.QKeySequence("Ctrl+T"),
        )
        self._add_menu_action(
            file_menu,
            "&Close Current Tab",
            self._close_current_tab,
            QtGui.QKeySequence.StandardKey.Close,
        )
        file_menu.addSeparator()
        self._add_menu_action(
            file_menu,
            "E&xit",
            self.close,
            QtGui.QKeySequence.StandardKey.Quit,
        )

        edit_menu = menubar.addMenu("&Edit")
        self._add_menu_action(
            edit_menu,
            "&Rename Current Tab...",
            self._rename_current_tab,
            QtGui.QKeySequence("Ctrl+R"),
        )
        self._add_menu_action(
            edit_menu,
            "&Find in Current View",
            self._find_in_current_tab,
            QtGui.QKeySequence.StandardKey.Find,
        )

        view_menu = menubar.addMenu("&View")
        self._add_menu_action(view_menu, "Toggle &Docks", self._toggle_docks)
        view_menu.addSeparator()
        self._add_menu_action(view_menu, "&Optimize", self._on_optimize)
        self._add_menu_action(view_menu, "&Results", self._on_results)

        help_menu = menubar.addMenu("&Help")
        self._add_menu_action(help_menu, "&About IITM-Climact", self._show_about)

    def _add_menu_action(
        self,
        menu: QtWidgets.QMenu,
        text: str,
        slot,
        shortcut: QtGui.QKeySequence | QtGui.QKeySequence.StandardKey | str | None = None,
    ) -> QtGui.QAction:
        """Create a QAction, attach it to a menu, and wire its handler."""

        action = menu.addAction(text)
        if shortcut is not None:
            action.setShortcut(shortcut)
        action.triggered.connect(slot)
        return action

    def _init_docks(self):
        """
        Initialize left and right dock widgets.
        """
        from gui.widgets.dock import Dock
        from gui.main_ui.lower_dock import LowerPanel
        from gui.main_ui.upper_dock import UpperPanel

        lower_title = QtWidgets.QFrame()
        upper_title = QtWidgets.QLabel(
            """
		<span style='font-family: Bitcount; font-size: 30pt'>IITM</span>
		<span style='font-family: Bitcount; font-size: 30pt; color: darkcyan'>-Climact</span>
		""",
            alignment=QtCore.Qt.AlignmentFlag.AlignCenter,
        )

        upper_panel = UpperPanel(self)
        lower_panel = LowerPanel(self)

        upper_dock = Dock(upper_title, upper_panel, parent=self)
        lower_dock = Dock(lower_title, lower_panel, parent=self)

        self.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, upper_dock)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, lower_dock)

        # Store dock references
        self._docks = {"upper": upper_dock, "lower": lower_dock}

    def _init_tabs(self) -> None:
        """
        Initialize the central tab widget.
        """

        # 1. Create the tab widget with template mode enabled
        self._tabs = TabWidget(self, template_mode=True)
        self.setCentralWidget(self._tabs)

        # 2. Add the India map as the first tab
        self._add_map_tab()

    def _add_map_tab(self) -> None:
        """Create the default map tab."""

        import qtawesome as qta
        from gui.maps import MapsViewer

        maps_viewer = MapsViewer(api_client=self.api_client, parent=self._tabs)
        self._tabs.addTab(maps_viewer, qta.icon("mdi.map", color="#6ec6ca"), "Map")
        self._tabs.setCurrentWidget(maps_viewer)

    @QtCore.Slot()
    def _execute(self) -> None:
        """
        Handle toolbar action button clicks.
        """
        self._open_project_dialog()

    @QtCore.Slot()
    def _on_optimize(self) -> None:
        """
        Open the optimization setup as a new tab.
        """
        import qtawesome as qta
        from gui.conopt.window import ConOptWindow
        from gui.bus import Relay

        # Create optimization window and emit signal
        window = ConOptWindow(self)
        icon = qta.icon("mdi.function", color="cyan")
        label = "Optimize"

        # Forward the signal to the event-bus
        bus = Relay.instance()
        bus.sig_open_widget.emit(window, label, icon)

    @QtCore.Slot()
    def _on_results(self) -> None:
        """
        Open the results explorer tab.
        """
        import qtawesome as qta
        from gui.conopt.results import ResultsWindow
        from gui.bus import Relay

        window = ResultsWindow(self)
        icon = qta.icon("mdi.chart-box", color="#fe6d73")
        label = "Results"

        bus = Relay.instance()
        bus.sig_open_widget.emit(window, label, icon)

    @QtCore.Slot()
    def _toggle_docks(self) -> None:
        """
        Toggle the visibility of all docks.
        """

        for dock in self._docks.values():

            dock.setVisible(not dock.isVisible())

    @QtCore.Slot()
    def _create_template_tab(self) -> None:
        """Create a new template tab using the tab widget's template flow."""

        self._tabs.create_tab()

    @QtCore.Slot()
    def _close_current_tab(self) -> None:
        """Close the currently active tab."""

        if self._tabs.count() == 0:
            return
        self._tabs.remove_tab(self._tabs.currentIndex())

    @QtCore.Slot()
    def _rename_current_tab(self) -> None:
        """Rename the currently active tab."""

        if self._tabs.count() == 0:
            return
        self._tabs.rename_tab(self._tabs.currentIndex())

    @QtCore.Slot()
    def _find_in_current_tab(self) -> None:
        """Forward find requests to the tab widget's current viewer."""

        self._tabs._find()

    @QtCore.Slot()
    def _show_about(self) -> None:
        """Display a short application about dialog."""

        QtWidgets.QMessageBox.about(
            self,
            "About IITM-Climact",
            "IITM-Climact\n\n"
            "GUI platform for steel-sector decarbonization modelling built with "
            "PySide6 and FastAPI.",
        )

    def _reset_project_state(self) -> None:
        """Clear UI state so a newly opened project starts from a clean slate."""

        from gui.compat import Translator
        from gui.conopt.results import ResultsWindow

        translator = Translator.instance()
        translator._paths.clear()
        translator._canvas_uuid.clear()
        ResultsWindow.clear_runs()

        while self._tabs.count():
            widget = self._tabs.widget(0)
            self._tabs.removeTab(0)
            if widget:
                widget.deleteLater()

        self._add_map_tab()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Handle window close event by logging out and purging server data."""

        # Try: Send logout request to server and purge data
        # Exceptions:
        # - requests.RequestException: Raised if HTTP request fails
        # - Exception: Any error during logout
        try:

            from gui.compat import SysClient as ClimactClient

            if self.api_client:

                client = ClimactClient.instance()
                if client:

                    response = self.api_client.session.post(
                        f"{self.api_client.base_URL}/lan/logout",
                        params={"token": self.api_client.user_id},
                        headers={"X-Client-ID": self.api_client.user_id},
                        timeout=5.0,
                    )
                    logger.info(f"Logout response: {response.status_code}")

        except Exception as e:

            logger.error(f"Error during logout: {e}")

        event.accept()
        super().closeEvent(event)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """
        Handle keyboard shortcuts.
        """

        if (
            event.key() == QtCore.Qt.Key.Key_S
            and event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier
        ):
            self._save()
            event.accept()
            return
        super().keyPressEvent(event)

    def _save(self) -> None:
        """Save the current canvas graph to a JSON file."""

        # 1. Get current tab
        current_widget = self._tabs.currentWidget()
        if not current_widget:

            return

        # 2. Validate tab is a Viewer
        from gui.widgets.viewer import Viewer
        from gui.graph.canvas import Canvas

        if not isinstance(current_widget, Viewer):

            logger.info("No canvas to save (not a graph tab)")
            return

        # 3. Get canvas from viewer
        canvas = current_widget.scene()
        if not isinstance(canvas, Canvas):

            logger.info("No canvas to save")
            return

        # Try: Save canvas data to file
        # Exceptions:
        # - OSError: Raised if file cannot be written
        # - json.JSONDecodeError: Raised if JSON serialization fails
        try:

            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, "Save graph as JSON", "graph_template.json", "JSON Files (*.json)"
            )

            if file_path:

                canvas_data = {
                    "nodes": [],
                    "edges": [],
                }
                with open(file_path, "w") as f:

                    json.dump(canvas_data, f, indent=2)
                logger.info(f"✓ Saved graph to {file_path}")
                QtWidgets.QMessageBox.information(
                    self, "Save Successful", f"Graph saved to:\n{file_path}"
                )

        except Exception as e:

            logger.error(f"Error saving graph: {e}")
            QtWidgets.QMessageBox.warning(self, "Save Failed", f"Error: {e}")

    @QtCore.Slot()
    def _open_project_dialog(self) -> None:
        """Prompt for a server-side project, open it, and load its blueprint."""

        if not self.api_client or not self.api_client.user_id:
            QtWidgets.QMessageBox.warning(
                self,
                "Open Failed",
                "No API client is available for opening a project.",
            )
            return

        projects_response = self.api_client.list_projects()
        if not projects_response or projects_response.get("status") != "OK":
            detail = (
                projects_response.get("detail", "Unknown error")
                if projects_response
                else "No response"
            )
            QtWidgets.QMessageBox.warning(
                self,
                "Open Failed",
                f"Failed to fetch projects:\n{detail}",
            )
            return

        try:
            from gui.maps import MapsRelay

            project_names = []
            for project in projects_response.get("serialized", []):
                if isinstance(project, dict):
                    project_names.append(project.get("name", "Unknown"))
                elif isinstance(project, str):
                    project_names.append(project)

            if not project_names:
                QtWidgets.QMessageBox.information(
                    self,
                    "Open Project",
                    "No projects are available for this user.",
                )
                return

            project_uid, ok = QtWidgets.QInputDialog.getItem(
                self,
                "Open Project",
                "Project:",
                project_names,
                0,
                False,
            )
            if not ok or not project_uid:
                return

            response = self.api_client.open_project(project_uid)
            if not response or response.get("status") not in ("OK", 200):
                detail = (
                    response.get("detail")
                    or response.get("info")
                    or response.get("contents")
                    or "Unknown error"
                ) if response else "No response"
                QtWidgets.QMessageBox.warning(
                    self,
                    "Open Failed",
                    f"Failed to load project:\n{detail}",
                )
                return

            self._reset_project_state()
            self._load(project_uid)
            MapsRelay.instance().sig_plants_loaded.emit()
        except Exception as e:
            logger.error(f"Failed to open project: {e}")
            QtWidgets.QMessageBox.warning(
                self,
                "Open Failed",
                f"Failed to open project:\n{e}",
            )

    def _load(self, project: str) -> None:
        """
        Register a project's blueprint with the UI without opening a canvas tab.

        Args:
            project: Server-side project identifier.
        """

        try:
            from pathlib import Path

            # Extract project identifier from the selected project reference.
            name = Path(project).stem

            # Call the API to get the blueprint from the server
            if not self.api_client:
                logger.error("API client not initialized")
                return

            self.api_client.project_uid = name

            response = self.api_client.session.get(
                f"{self.api_client.base_URL}/projects/{name}/blueprint",
                headers={"X-Client-ID": self.api_client.user_id},
                timeout=10.0,
            )
            response.raise_for_status()

            api_response = response.json()
            if api_response.get("status") != "OK":
                logger.warning(
                    f"Failed to load blueprint: {api_response.get('detail', 'Unknown error')}"
                )
                return

            blueprint = api_response.get("data")
            if not blueprint:
                logger.warning("No blueprint data in response")
                return

            # Emit signal to update project panel
            from gui.bus import Relay

            bus = Relay.instance()
            bus.sig_project_loaded.emit(name)

            logger.info(f"Loaded project blueprint metadata: {name}")

            # Load any previously stored optimization results from the HDF5
            self._load_stored_results(name)

        except Exception as e:
            logger.error(f"Failed to open project blueprint: {e}")
            QtWidgets.QMessageBox.warning(
                self,
                "Open Failed",
                f"Failed to open project blueprint:\n{e}",
            )

    def _load_stored_results(self, project_name: str) -> None:
        """Read results/* from HDF5 and populate ResultsWindow."""
        try:
            resp = self.api_client.session.get(
                f"{self.api_client.base_URL}/projects/{project_name}/results",
                headers={"X-Client-ID": self.api_client.user_id},
                timeout=10.0,
            )
            if resp.status_code != 200:
                return

            api_response = resp.json()
            if api_response.get("status") != "OK":
                return

            scenarios = api_response.get("data", {})
            if not scenarios:
                return

            from gui.conopt.results import ResultsWindow
            for scenario_name, info in scenarios.items():
                ResultsWindow.add_run(scenario_name, info)

            logger.info(f"Loaded {len(scenarios)} stored optimization result(s) from {project_name}")

        except Exception as e:
            logger.warning(f"Could not load stored results: {e}")

    def _load_project_maps(self, project: str) -> None:
        """Load project map markers and refresh the map tab."""

        try:
            map_load_resp = self.api_client.session.post(
                f"{self.api_client.base_URL}/maps/load_project",
                json={"file": project},
                headers={"X-Client-ID": self.api_client.user_id},
                timeout=10.0,
            )
            map_load_resp.raise_for_status()

            from gui.maps import MapsRelay

            MapsRelay.instance().sig_plants_loaded.emit()
        except Exception as e:
            logger.error(f"Error loading maps from project: {e}")
