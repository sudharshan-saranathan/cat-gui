# Filename: ftable.py
# Module name: startup
# Description: A widget for displaying project files in a table format.

"""
File table widget for displaying and managing projects.
Includes action buttons for opening, cloning, and deleting projects.
"""

from __future__ import annotations
from pathlib import Path
from qtawesome import icon as qta_icon
from PySide6 import QtGui, QtCore, QtWidgets
from gui.widgets.layouts import HLayout
from gui.widgets import ToolBar
import dataclasses


# Widget representing a single file/project, added to the FileTable:
class FileTableItem(QtWidgets.QWidget):
    """
    A custom cell-widget representing a single project file.

    Displays buttons for opening, cloning, and deleting the project that are revealed on hover.
    """

    # Signals emitted when the action buttons are clicked:
    sig_open_project = QtCore.Signal(str)
    sig_clone_project = QtCore.Signal(str)
    sig_delete_project = QtCore.Signal(str)

    def __init__(self, name: str, path: str = "", **kwargs):
        """
        Initializes this widget and sets up the UI components.

        Args:
            name: The project name to display.
            path: The project file path (default: empty string).
            **kwargs: Additional keyword arguments (e.g., the buttons-list).
        """

        super().__init__(None)
        super().setMouseTracking(True)
        super().setProperty("project", name)

        self._project_name = name
        self._project_path = path

        self._project_label = QtWidgets.QLabel(name)
        self._project_acts = self._project_actions()
        self._buttons = kwargs.get("buttons", [])

        # Arrange UI components in a horizontal layout:
        HLayout(
            self,
            margins=(4, 4, 4, 4),
            widgets=[self._project_label, self._project_acts],
        )

    def _project_actions(
        self, icon_size: QtCore.QSize = QtCore.QSize(16, 16)
    ) -> ToolBar:
        """
        Creates and returns a toolbar with action buttons.

        Args:
            icon_size: The size of the action icons (default: 16x16).

        Returns:
            A ToolBar with open, safe mode, clone, and delete actions.
        """

        toolbar = ToolBar(
            iconSize=icon_size,
            actions=[
                (
                    qta_icon("ph.upload-simple", color="gray", color_active="white"),
                    "Open Project",
                    lambda path=self._project_path: self.sig_open_project.emit(path),
                ),
                (
                    qta_icon(
                        "ph.shield-check-fill", color="gray", color_active="white"
                    ),
                    "Open Project (Safe Mode)",
                    lambda path=self._project_path: self.sig_open_project.emit(path),
                ),
                (
                    qta_icon(
                        "mdi.plus-circle-multiple-outline",
                        color="gray",
                        color_active="white",
                    ),
                    "Clone Project",
                    lambda path=self._project_path: self.sig_clone_project.emit(path),
                ),
                (
                    qta_icon("mdi.delete", color="gray", color_active="red"),
                    "Delete Project",
                    lambda path=self._project_path: self.sig_delete_project.emit(path),
                ),
            ],
        )

        toolbar.hide()  # Hide all actions by default.
        return toolbar

    def enterEvent(self, event, /) -> None:
        """
        Shows the action buttons when the mouse enters the item.

        Args:
            event: QtGui.QEnterEvent managed by Qt.
        """

        self._project_acts.show()

    def leaveEvent(self, event, /) -> None:
        """
        Hides action buttons when the mouse leaves the item.

        Args:
            event: QtGui.QLeaveEvent managed by Qt.
        """

        self._project_acts.hide()


class StartupFileTable(QtWidgets.QTableWidget):
    """
    A table widget for displaying and managing project files.

    Displays files along with their last modified dates.
    Supports filtering by file pattern and automatically populates from a directory.
    Emits sig_row_double_clicked when a row is double-clicked.
    """

    # Signal emitted when a row is double-clicked
    sig_row_double_clicked = QtCore.Signal(str)  # Emits project path

    # TODO: Split this dataclass into `Style` and `Attrs` classes.
    @dataclasses.dataclass
    class Options:
        """Configuration options for the file table widget."""

        row_height: int = 36
        icon_size: QtCore.QSize = dataclasses.field(
            default_factory=lambda: QtCore.QSize(16, 16)
        )
        empty_icon_opacity: float = 0.2
        columns: list[str] = dataclasses.field(
            default_factory=lambda: ["Projects", "Last Modified"]
        )

    def __init__(self, parent=None):
        """
        Initialize the file table widget.

        Args:
            parent: Parent widget (optional).
        """

        # Initialize options:
        self._opts = StartupFileTable.Options()

        # Initialize parent class:
        super().__init__(parent, columnCount=len(self._opts.columns))

        # Configure table appearance and behavior:
        self.setShowGrid(False)
        self.setIconSize(self._opts.icon_size)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)

        self.setColumnWidth(1, 160)
        self.setHorizontalHeaderLabels(self._opts.columns)
        self.verticalHeader().setVisible(False)

        # Configure column resizing:
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)

        # Connect double-click signal to emit our custom signal with project path
        self.itemDoubleClicked.connect(self._on_item_double_clicked)

    def paintEvent(self, event) -> None:
        """
        Paint the table and display an empty state message if no rows exist.

        Args:
            event: The paint event.
        """

        super().paintEvent(event)  # Call base-class implementation

        # Paint an empty indicator if the table is empty:
        if self.rowCount() == 0:

            painter = QtGui.QPainter(self.viewport())
            painter.setOpacity(self._opts.empty_icon_opacity)
            icon = QtGui.QIcon(":/png/empty.png")
            icon.paint(painter, self.viewport().rect())

            painter.drawText(
                self.viewport().rect(),
                QtCore.Qt.AlignmentFlag.AlignCenter,
                "No items found",
            )
            painter.end()

    def mousePressEvent(self, event) -> None:
        """
        Handle mouse press events and clear selection when clicking empty space.

        Args:
            event: The mouse press event.
        """

        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            item = self.itemAt(event.pos())
            if item is None:
                self.clearSelection()  # Clear selection to re-disable the "Open" button

        super().mousePressEvent(event)  # Call base-class implementation

    def add_item(self, path: Path | str, time: str) -> None:
        """
        Add a new project row to the table.

        Args:
            path: The project identifier or a path-like reference.
            time: The last modified time as a string.
        """
        project_ref = str(path)
        project_name = Path(project_ref).stem

        row = self.rowCount()  # Get the current row count
        self.insertRow(self.rowCount())  # Insert a new row at the end

        # The second column displays the last modified time:
        item_second_column = QtWidgets.QTableWidgetItem(time)
        item_second_column.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        item_second_column.setFlags(
            item_second_column.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable
        )

        # Change the icon based on whether the item is a directory or not:
        item_first_column = QtWidgets.QTableWidgetItem(
            QtGui.QIcon(":/logo/logo.png"), str()
        )

        self.setRowHeight(row, self._opts.row_height)
        file_item = FileTableItem(project_name, path=project_ref)
        self.setCellWidget(row, 0, file_item)
        self.setItem(row, 1, item_second_column)
        self.setItem(row, 0, item_first_column)

    def _on_item_double_clicked(self, item: QtWidgets.QTableWidgetItem) -> None:
        """
        Handle double-click on a table item.

        Retrieves the project path from the FileTableItem widget in the same row
        and emits the sig_row_double_clicked signal.

        Args:
            item: The clicked table item.
        """
        row = self.row(item)
        file_item = self.cellWidget(row, 0)
        if isinstance(file_item, FileTableItem):
            self.sig_row_double_clicked.emit(file_item._project_path)

    def populate(self, directory: str, pattern: str) -> None:
        """
        Populate the table with project files from a directory.

        Args:
            directory: The directory path to search for files.
            pattern: A glob pattern to match files (e.g., "*.h5").
        """

        # Import required modules:
        from pathlib import Path
        from datetime import datetime

        # Check validity of directory:
        base = Path(directory)
        if not base.is_dir():
            return

        self.clearContents()
        self.setRowCount(0)

        stem = Path(directory).stem  # Extract the directory name
        stem = stem.capitalize()  # Capitalize the first letter

        self.setHorizontalHeaderLabels([stem, self._opts.columns[1]])
        for item in Path(directory).glob(pattern):
            stat = item.stat().st_mtime  # Get last modified time
            date = datetime.fromtimestamp(stat)  # Convert to datetime object
            time = date.strftime("%Y-%m-%d")  # Format as string

            self.add_item(item, time)
