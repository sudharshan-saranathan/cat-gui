# Module Name: gui.startup.window
# Description: A startup window based on the QDialog class (see Qt docs for more info).

from dataclasses import dataclass

# PySide6 (Python/Qt)
from PySide6 import QtGui
from PySide6 import QtCore
from PySide6 import QtWidgets

# Climact modules: gui.widgets, gui.startup
from gui.startup.choice import StartupChoice
from gui.startup.ftable import StartupFileTable, FileTableItem
from gui.startup.login import LoginWidget
from gui.widgets import GLayout


class StartupWindow(QtWidgets.QDialog):

    @dataclass
    class Appearance:
        borderline: QtGui.QPen
        background: QtGui.QBrush
        texture: QtGui.QPixmap

    @dataclass
    class Geometry:
        border_radius: int
        size: QtCore.QSize

    @dataclass
    class Metadata:

        regex: str

    def __init__(self):

        # Initialize the base-class (QDialog) immediately since there are no parameters to pass to it
        super().__init__(None)

        # Initialize default options, flags, and other necessary attributes
        self._initialize_defaults()

        # UI components
        self._header = self._init_header()
        self._footer = self._init_footer()
        self._ftable = self._init_ftable()

        self._login = LoginWidget()
        self._current_project_file = None
        self._user_id = None
        self._server_url = None
        self._api_client = None

        # Arrange UI components using a grid layout
        self._init_layout()
        self._init_connections()

    def _initialize_defaults(self) -> None:
        """
        Initialize default values for appearance, geometry, and behavior.
        """

        # 1. Create texture for appearance
        texture = QtGui.QPixmap(":/theme/pattern.png")

        # 2. Set up appearance with texture
        background = QtGui.QBrush(QtGui.QColor(0x232A2E))
        background.setTexture(texture)

        self._appearance = StartupWindow.Appearance(
            borderline=QtGui.QPen(QtGui.QColor(0x363E41), 1.0),
            background=background,
            texture=texture,
        )

        # 3. Configure the window geometry
        self._geometry = StartupWindow.Geometry(
            border_radius=8,
            size=QtCore.QSize(900, 640),
        )

        # 4. Configure behavior
        self._behavior = StartupWindow.Metadata(
            regex="*.h5",
        )

        # 5. Apply window attributes
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
        self.resize(self._geometry.size)

    def _init_header(self) -> QtWidgets.QLabel:
        """
        Create and configure the window header with title and subtitle.

        Returns:
            A QLabel displaying the application title and tagline with centered alignment.
        """
        header = QtWidgets.QLabel(
            '<span style="color:white; font-family: Bitcount; font-size: 26pt">IITM</span>'
            '<span style="color:darkcyan; font-family: Bitcount; font-size: 26pt">-Climact</span><br>'
            '<span style="color:gray; font-weight: bold; font-size: 12pt">Climate Action Tool v0.1.0</span>',
            self,
            alignment=QtCore.Qt.AlignmentFlag.AlignCenter,
        )

        header.setContentsMargins(48, 0, 0, 0)
        header.setOpenExternalLinks(True)
        header.setFont(QtGui.QFont("Bitcount"))
        return header

    def _init_h_line(self) -> QtWidgets.QFrame:
        """
        Create a horizontal separator line.

        Returns:
            A QFrame configured as a horizontal line with dark gray color.
        """
        h_line = QtWidgets.QFrame(self)
        h_line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        h_line.setStyleSheet("QFrame {background:#4f4f4f; margin-left: 48px;}")
        h_line.setLineWidth(2)
        return h_line

    def _init_footer(self) -> QtWidgets.QToolBar:
        """
        Create the footer toolbar with project links and license information.

        The footer contains clickable buttons for GitHub and the project website, along
        with a license link. A spacer separates the links from the license text.

        Returns:
            A QToolBar configured with footer elements.
        """

        import webbrowser

        def _init_link_button(
            icon: str, tooltip: str, url: str
        ) -> QtWidgets.QToolButton:
            """
            Create a clickable tool button that opens a URL in the default browser.

            Args:
                icon: QtAwesome icon name (e.g., "mdi.github").
                tooltip: Tooltip text shown on hover.
                url: URL to open when the button is clicked.

            Returns:
                A configured QToolButton.
            """
            from qtawesome import icon as qta_icon

            link = QtWidgets.QToolButton(self)
            link.setIcon(qta_icon(icon, color="gray", color_active="white"))
            link.setToolTip(tooltip)
            link.clicked.connect(lambda: webbrowser.open(url))
            return link

        git_link = _init_link_button(
            "mdi.github",
            "GitHub Repository",
            "https://github.com/sudharshan-saranathan/iitm-climact.git",
        )

        web_link = _init_link_button(
            "mdi.web", "Project Website", "https://example.com/iitm-climact"
        )

        # Add spacing between buttons and license
        spacer = QtWidgets.QWidget(self)
        spacer.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )

        license_label = QtWidgets.QLabel(
            '<a href="https://opensource.org/licenses/GPL-3.0" style="color: #4f4f4f;">'
            "© 2025 GPLv3.0"
            "</a>",
            self,
            openExternalLinks=True,
        )

        # Arrange footer components in a toolbar:
        footer = QtWidgets.QToolBar(self, iconSize=QtCore.QSize(18, 18))
        footer.addWidget(git_link)
        footer.addWidget(web_link)
        footer.addWidget(spacer)
        footer.addWidget(license_label)
        return footer

    def _init_ftable(self) -> StartupFileTable:
        """
        Initialize the file table widget displaying project files

        Returns:
            StartupFileTable: The file table widget
        """

        ftable = StartupFileTable()
        ftable.populate("library", self._behavior.regex)
        return ftable

    def _init_layout(self):

        # Create stacked widget for the right side (switches between login and table)
        # ========== RIGHT SIDE PAGE 0: Login Widget ==========
        self._right_stacked_widget = QtWidgets.QStackedWidget()
        self._right_stacked_widget.addWidget(self._login)

        # ========== RIGHT SIDE PAGE 1: File Table with Back Button ==========
        table_widget = QtWidgets.QWidget()
        table_layout = QtWidgets.QGridLayout(table_widget)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)

        # Back button at top-left corner
        back_button = QtWidgets.QPushButton()
        back_button.setText(" Back")
        back_button.setMaximumWidth(100)
        back_button.setMaximumHeight(32)
        back_button.setStyleSheet(
            "QPushButton {"
            "   padding: 4px 0px 4px 0px;"
            "   color: #aaaaaa;"
            "   text-align: right;"
            "   border-radius: 0px;"
            "   background-color: transparent;"
            "}"
            "QPushButton:hover {"
            "   color: #efefef;"
            "}"
            "QPushButton:checked {"
            "   color: white;"
            "   font-weight: bold;"
            "}"
        )
        back_button.clicked.connect(self._on_back)

        self._new_project_btn = QtWidgets.QPushButton(" New Project")
        self._new_project_btn.setMaximumWidth(160)
        self._new_project_btn.setMaximumHeight(32)
        self._new_project_btn.setStyleSheet(back_button.styleSheet())

        try:
            # Use qtawesome for the back arrow icon
            from qtawesome import icon as qta_icon

            # Set the button's icon
            back_button.setIcon(
                qta_icon(
                    "mdi.arrow-left",
                    color="gray",
                    color_active="white",
                )
            )
            self._new_project_btn.setIcon(
                qta_icon(
                    "mdi.folder-plus",
                    color="#ffcb00",
                    color_active="white",
                )
            )
        except ImportError:
            pass

        # Create corner widget container that aligns with table header
        corner_widget = QtWidgets.QWidget()
        corner_layout = QtWidgets.QVBoxLayout(corner_widget)
        corner_layout.setContentsMargins(0, 0, 0, 4)
        corner_layout.setSpacing(0)
        corner_layout.addWidget(
            back_button,
            0,
            QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignLeft,
        )
        corner_layout.addWidget(
            self._new_project_btn,
            0,
            QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignLeft,
        )
        corner_layout.addStretch()

        # Grid layout: button in corner (0,0), spacer (0,1), table below (1,0-1)
        table_layout.addWidget(corner_widget, 0, 0)

        # Spacer to push content to the right in the header row
        spacer = QtWidgets.QWidget()
        table_layout.addWidget(spacer, 0, 1)
        table_layout.setColumnStretch(1, 1)

        # Table spans both columns on second row
        table_layout.addWidget(self._ftable, 1, 0, 1, 2)
        table_layout.setRowStretch(1, 1)

        self._right_stacked_widget.addWidget(table_widget)

        # ========== MAIN LAYOUT: Header, title, buttons on left; stacked widget on right ==========
        layout = GLayout(
            self,
            spacing=8,
            margins=(4, 4, 4, 4),
        )
        layout.setVerticalSpacing(8)
        layout.setRowStretch(0, 5)
        layout.addWidget(self._header, 1, 0)

        layout.addWidget(self._footer, 5, 0)
        layout.addWidget(self._right_stacked_widget, 0, 1, 6, 1)
        layout.setRowStretch(4, 4)
        layout.setColumnStretch(1, 2)

    def _init_connections(self) -> None:
        """
        Connect UI signals to their respective handler slots.

        Connects buttons and file table signals to manage project creation,
        selection, and application lifecycle.
        """

        # Connect login widget signals
        self._login.connect_clicked.connect(self._on_connect)
        self._login.get_exit_button().clicked.connect(self._on_exit)
        self._new_project_btn.clicked.connect(self._on_new_project)

        # Connect file table double-click signal
        self._ftable.sig_row_double_clicked.connect(self._on_open_project)

        # Connect file table items
        for row in range(self._ftable.rowCount()):
            item = self._ftable.cellWidget(row, 0)
            if isinstance(item, FileTableItem):
                item.sig_open_project.connect(self._on_open_project)
                item.sig_clone_project.connect(self._on_clone_project)
                item.sig_delete_project.connect(self._on_delete_project)

    @QtCore.Slot()
    def _on_new_project(self) -> None:
        """
        Handle new project creation button click.

        Create a blank server-side project and open it immediately.
        """
        if not self._api_client or not self._api_client.user_id:
            QtWidgets.QMessageBox.warning(
                self,
                "New Project",
                "Connect to the server before creating a project.",
            )
            return

        project_uid, ok = QtWidgets.QInputDialog.getText(
            self,
            "New Project",
            "Project name:",
        )
        if not ok:
            return

        project_uid = project_uid.strip()
        if not project_uid:
            QtWidgets.QMessageBox.warning(
                self,
                "New Project",
                "Project name cannot be empty.",
            )
            return

        response = self._api_client.create_project(project_uid)
        if not response or response.get("status") not in ("OK", 200):
            detail = (
                response.get("detail")
                or response.get("info")
                or response.get("contents")
                or "Unknown error"
            ) if response else "No response"
            QtWidgets.QMessageBox.warning(
                self,
                "New Project",
                f"Failed to create project:\n{detail}",
            )
            return

        self._refresh_projects()
        self._current_project_file = response.get("project", project_uid)
        self.accept()

    @QtCore.Slot()
    def _on_library_clicked(self) -> None:
        """
        Handle library button click.

        The file table is already visible by default, so no action is needed.
        """
        pass

    @QtCore.Slot(str)
    def _on_open_project(self, project_path: str) -> None:
        """
        Handle project selection from the file table.

        Stores the selected server-side project identifier and accepts the dialog.

        Args:
            project_path: Identifier of the selected project.
        """
        self._current_project_file = project_path
        self.accept()

    @QtCore.Slot(str)
    def _on_clone_project(self, project_path: str) -> None:
        """
        Handle project cloning request.

        TODO: Implement project cloning logic.

        Args:
            project_path: Path to the project to clone.
        """
        pass

    @QtCore.Slot(str)
    def _on_delete_project(self, project_path: str) -> None:
        """
        Handle project deletion request.

        TODO: Implement project deletion logic.

        Args:
            project_path: Path to the project to delete.
        """
        if not self._api_client or not self._api_client.user_id:
            return

        project_uid = str(project_path).strip()
        answer = QtWidgets.QMessageBox.question(
            self,
            "Delete Project",
            f"Delete project '{project_uid}'?",
        )
        if answer != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        response = self._api_client.delete_project(project_uid)
        if not response or response.get("status") not in ("OK", 200):
            detail = (
                response.get("detail")
                or response.get("info")
                or response.get("contents")
                or "Unknown error"
            ) if response else "No response"
            QtWidgets.QMessageBox.warning(
                self,
                "Delete Project",
                f"Failed to delete project:\n{detail}",
            )
            return

        self._refresh_projects()

    @QtCore.Slot()
    def _on_quit(self) -> None:
        self.reject()

    @QtCore.Slot()
    def _on_back(self) -> None:
        """
        Handle back button click.

        Switches back to the login page and hides the choice buttons.
        """
        self._right_stacked_widget.setCurrentIndex(0)

    @QtCore.Slot(str, str, str)
    def _on_connect(self, user_id: str, ip: str, port: str) -> None:
        """
        Handle connect button click from the login widget.

        Args:
            user_id: The user ID
            ip: The server IP address
            port: The server port number
        """
        from gui.api_client import APIClient
        self._user_id = user_id
        self._server_url = f"http://{ip}:{port}"

        # Create API client and register user
        api_client = APIClient(base_url=self._server_url)
        if not api_client.login(user_id):
            QtWidgets.QMessageBox.warning(
                self,
                "Login Error",
                api_client.last_error
                or f"Failed to connect to server at {self._server_url}",
            )
            return

        self._api_client = api_client
        if not self._refresh_projects():
            return
        self._right_stacked_widget.setCurrentIndex(1)

    @QtCore.Slot()
    def _on_exit(self) -> None:
        """
        Handle exit button click.

        Closes the application.
        """
        self.reject()

    def get_user_id(self) -> str:
        """
        Get the entered user ID.

        Returns:
            The user ID entered in the dialog.
        """
        return self._user_id

    def get_server_url(self) -> str:
        """
        Get the server URL (IP and port).

        Returns:
            The server URL (e.g., http://localhost:8000).
        """
        return self._server_url

    def get_current_project_file(self) -> str:
        """
        Get the selected project identifier.

        Returns:
            The selected project identifier, or None if no project was selected.
        """
        return self._current_project_file

    def get_api_client(self):
        """Return the authenticated API client created during startup."""
        return self._api_client

    def _refresh_projects(self) -> bool:
        """Reload the server-side project list into the table."""
        from datetime import datetime

        if not self._api_client:
            return False

        projects_response = self._api_client.list_projects()
        if not projects_response:
            QtWidgets.QMessageBox.warning(
                self, "Load Error", "No response from server when fetching projects"
            )
            return False

        if projects_response.get("status") != "OK":
            error_msg = projects_response.get("detail", "Unknown error")
            QtWidgets.QMessageBox.warning(
                self, "Load Error", f"Failed to load projects: {error_msg}"
            )
            return False

        self._ftable.clearContents()
        self._ftable.setRowCount(0)
        self._ftable.setHorizontalHeaderLabels(self._ftable._opts.columns)

        for project in projects_response.get("serialized", []):
            if isinstance(project, dict):
                project_ref = project.get("name", "Unknown")
                project_time = project.get(
                    "modified", datetime.now().strftime("%Y-%m-%d")
                )
            elif isinstance(project, str):
                project_ref = project
                project_time = datetime.now().strftime("%Y-%m-%d")
            else:
                continue

            self._ftable.add_item(project_ref, project_time)

        for row in range(self._ftable.rowCount()):
            item = self._ftable.cellWidget(row, 0)
            if isinstance(item, FileTableItem):
                item.sig_open_project.connect(self._on_open_project)
                item.sig_clone_project.connect(self._on_clone_project)
                item.sig_delete_project.connect(self._on_delete_project)

        return True

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:

        painter = QtGui.QPainter(self)
        painter.setPen(self._appearance.borderline)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        painter.setBrush(self._appearance.background)
        painter.drawRoundedRect(
            self.rect(),
            self._geometry.border_radius,
            self._geometry.border_radius,
        )
