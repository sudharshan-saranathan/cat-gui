# Module Name: main
# Description: Entry point for IITM-Climact

# Built-ins
import platform
import argparse
import logging
import sys

# Dataclass
from dataclasses import field
from dataclasses import dataclass

# PySide6 (Python/Qt)
from PySide6 import QtGui
from PySide6 import QtCore
from PySide6 import QtWidgets

# Climact Module(s): gui.main_ui, core.system
import rsrc  # noqa: F401 - Initializes Qt resources (QSS, fonts, images) on import

# Climact Submodule(s): gui.main_ui.main_ui, gui.startup.window
from gui.main_ui.main_ui import MainGui
from gui.api_client import APIClient

# Configure logging
logging.basicConfig(
    encoding="utf-8",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] - (%(module)s) %(message)s",
)


class ViewController(QtCore.QObject):
    focus_item = QtCore.Signal(QtWidgets.QGraphicsObject)


# IITMClimact: Main application class
class Climact(QtWidgets.QApplication):

    # Class logger
    _logger = logging.getLogger("IITM-Climact")

    @dataclass(frozen=True)
    class Resources:
        """Resource paths.

        Attributes:
            image: Path to the application's taskbar icon (PNG).
            theme: Path to the application's QSS stylesheet.
            fonts: Path to the application's font directory.
        """

        image: str = ":/logo/logo.png"
        theme: str = ":/theme/dark.qss"
        fonts: str = ":/fonts"

    @dataclass(frozen=True)
    class Geometric:
        """Geometric attribute(s).

        Attributes:
            margin: The application's default margin (on all sides)
            normal: The application's geometry when shown normally.
        """

        margin: int = 64
        normal: QtCore.QRect = field(default_factory=QtCore.QRect)

    # Initialize Qt application and set default attribute(s)
    def __init__(self, startup: bool = True, project_file: str = None):

        # 1. Initialize the base-class and set an object name
        super().__init__(sys.argv)
        super().setObjectName("IITM-climact")

        # 2. Initialize the API client to None (set later in _show_startup)
        self._api_client = None
        self.view_ctrl = ViewController()

        # 3. Initialize the `Climact.Resources` and `Climact.Geometric` data-structures
        self._rsrc = Climact.Resources()
        self._geom = Climact.Geometric()

        image = self._rsrc.image
        theme = self._rsrc.theme
        bezel = self._geom.margin
        fonts = QtCore.QDir(self._rsrc.fonts)
        psize = 11 if platform.system() == "Darwin" else 8

        print(platform.system())
        # 4. Set the theme, fonts, window-icon. Then adjust the application's geometry.
        self._init_theme(theme)
        self._init_fonts(fonts)

        self.setFont(QtGui.QFont("Fira Code", psize))
        self.setWindowIcon(QtGui.QIcon(image))

        screen = QtWidgets.QApplication.primaryScreen()
        bounds = screen.availableGeometry()
        padded = bounds.adjusted(bezel, bezel, -bezel, -bezel)

        # 5. Get the user ID and project file (if selected) from the startup window
        user_id, project = self._show_startup()
        self._logger.info(f"User {user_id} registered successfully")

        # 6. Initialize SysClient with APIClient and open the selected server-side project
        from gui.compat import SysClient

        SysClient._instance = SysClient(self._api_client)
        if project:
            try:
                self._logger.info(f"Opening project: {project}")
                open_resp = self._api_client.open_project(project)
                if not open_resp or open_resp.get("status") not in ("OK", 200):
                    detail = (
                        open_resp.get("detail")
                        or open_resp.get("info")
                        or open_resp.get("contents")
                        or "Unknown error"
                    ) if open_resp else "No response"
                    raise RuntimeError(detail)
            except Exception as e:
                self._logger.error(f"Error opening project: {e}")

        # Create and show the main window
        self._win = MainGui(api_client=self._api_client, project=project)
        self._win.setWindowTitle("IITM-Climact")
        self._win.setGeometry(padded)

        # Display the main window
        self._win.show()

        # Refresh maps from the project AFTER GUI is initialized
        if project:
            try:
                from gui.maps import MapsRelay

                MapsRelay.instance().sig_plants_loaded.emit()
            except Exception as e:
                self._logger.error(f"Error refreshing maps from project: {e}")

        # Connect cleanup on application quit
        self.aboutToQuit.connect(self._cleanup)

    def _init_args(self) -> None:
        """Parse command-line arguments and update application flags.

        Supported flags:
        - --version: Display the application version and exit.
        - --no-startup: Skip the startup dialog.
        - --no-backend: Disable the backend optimization module.
        """

        parser = argparse.ArgumentParser()
        parser.add_argument("--version", action="version", version="%(prog)s 1.0")
        parser.add_argument("--no-startup", action="store_false", dest="startup")
        parser.add_argument("--no-backend", action="store_false", dest="backend")
        args = parser.parse_args()

        self.backend_flag = args.backend
        self.startup_flag = args.startup
        self.startup_code = 1

    @staticmethod
    def _init_fonts(path: QtCore.QDir) -> None:
        """Install custom fonts from QRC resources.

        :param path: Path to the 'fonts' directory (unused but kept for compatibility)
        :return None
        """

        # Load all TTF fonts from QRC resources
        font_paths = [
            ":/fonts/Bitcount-Regular.ttf",
            ":/fonts/FiraCode-Regular.ttf",
            ":/fonts/MarckScript-Regular.ttf",
            ":/fonts/Marmelad-Regular.ttf",
            ":/fonts/Bilbo-Regular.ttf",
        ]
        for font_path in font_paths:
            font_id = QtGui.QFontDatabase.addApplicationFont(font_path)
            if font_id == -1:
                logging.warning(f"Failed to load font: {font_path}")

    def _init_theme(self, path: str) -> None:
        """Set the application's theme based on the specified QSS stylesheet.

        :param path: Path to the QSS stylesheet file.
        :return: None
        """

        theme = QtCore.QFile(path)
        state = theme.open(QtCore.QFile.OpenModeFlag.ReadOnly)

        if state:
            stream = QtCore.QTextStream(theme)
            string = stream.readAll()
            self.setStyleSheet(string)

    def _show_startup(self):

        # Import the startup-window
        from gui.startup.window import StartupWindow

        # 1. Show the startup dialog and exit cleanly if the user cancels
        startup = StartupWindow()
        if startup.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            self._cleanup()
            sys.exit(0)

        # 2. Get the user ID and project file (if selected) from the startup window
        uid = startup.get_user_id()
        url = startup.get_server_url()
        prj = startup.get_current_project_file()
        self._api_client = startup.get_api_client()
        self._logger.info(f"User ID: {uid}, Server: {url}")

        # 3. Reuse the authenticated API client from startup
        if self._api_client is None:
            QtWidgets.QMessageBox.critical(
                None,
                "Connection Error",
                "Startup completed without a valid authenticated session.",
            )

            self._cleanup()
            sys.exit(1)

        # 4. Return the user ID and project file
        return uid, prj

    def _cleanup(self) -> None:
        if self._api_client:
            self._api_client.close()

    def resources(self):
        return self._rsrc


def main() -> None:
    """
    Parse command-line arguments and launch the application.

    Supported flags:
    - --version: Display the application version and exit.
    - --no-startup: Skip the startup dialog.
    - --no-backend: Disable the backend optimization module.

    Positional arguments:
    - project_file: Optional path to a project file to open.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("--version", action="version", version="%(prog)s 1.0")
    parser.add_argument("--no-startup", action="store_false", dest="startup")
    parser.add_argument("--no-backend", action="store_false", dest="backend")
    parser.add_argument(
        "project_file", nargs="?", default=None, help="Project file to open"
    )
    args = parser.parse_args()

    # Enable OpenGL rendering globally for better graphics performance
    fmt = QtGui.QSurfaceFormat()
    fmt.setRenderableType(QtGui.QSurfaceFormat.RenderableType.OpenGL)
    fmt.setProfile(QtGui.QSurfaceFormat.CoreProfile)
    QtGui.QSurfaceFormat.setDefaultFormat(fmt)

    application = Climact(project_file=args.project_file)
    application.exec()  # This call is blocking by default.
    sys.exit(0)


if __name__ == "__main__":
    main()
