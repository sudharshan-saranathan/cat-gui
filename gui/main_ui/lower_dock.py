# Module Name: gui.main_ui.lower
# Description: Lower panel to be shown within a dock

# Dataclass
from dataclasses import field
from dataclasses import dataclass

# Pyside6 (Python/Qt)
from PySide6 import QtGui
from PySide6 import QtCore
from PySide6 import QtWidgets

# Climact
from qtawesome import icon as qta_icon


class LowerPanel(QtWidgets.QListWidget):

    @dataclass
    class Appearance:
        border_color: QtGui.QColor
        border_width: float
        background_color: QtGui.QColor
        background_pattern: QtCore.Qt.BrushStyle

    @dataclass
    class Geometry:
        item_size: tuple  # (width, height)

    @dataclass
    class Behavior:
        pass

    def __init__(self, parent=None):

        # 1. Initialize base class and defaults
        super().__init__(parent)

        self._init_defaults()

        # 2. Create first header with built-in streams
        self._first_header = self._create_first_header_item()

        self._add_builtin_streams()

        # 3. Create second header for user-defined streams
        self._second_header = self._create_second_header_item()

    def _init_defaults(self) -> None:
        """Initialize default values for appearance, geometry, and behavior."""
        self._appearance = LowerPanel.Appearance(
            border_color=QtGui.QColor(0x40474D),
            border_width=1.0,
            background_color=QtGui.QColor(0x40474D),
            background_pattern=QtCore.Qt.BrushStyle.SolidPattern,
        )
        self._geometry = LowerPanel.Geometry(
            item_size=(0, 32),
        )
        self._behavior = LowerPanel.Behavior()

    def _execute(self):

        pass

    def _add_builtin_streams(self):
        """
        Add built-in stream classes to the list.
        """

        # Stream class definitions with icons and colors
        streams = [
            ("Electricity", "mdi.lightning-bolt", "#FFEB3B"),
            ("Fuel", "mdi.fire", "#FF6F00"),
            ("Material", "mdi.cube", "#4FC3F7"),
            ("Fluid", "mdi.water", "#26C6DA"),
            ("Composite", "mdi.sitemap", "#9C27B0"),
        ]

        for stream_name, icon_name, color in streams:

            icon = qta_icon(icon_name, color=color)
            item = QtWidgets.QListWidgetItem(icon, stream_name, self)
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsSelectable)
            item.setSizeHint(QtCore.QSize(0, 32))

    def _create_first_header_item(self):

        # Create and configure first header item
        icon = qta_icon("ph.list-fill", color="white")
        header_item = QtWidgets.QListWidgetItem(icon, "Built-in Resources", self)
        header_item.setFlags(header_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        header_item.setFlags(header_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsSelectable)
        header_item.setSizeHint(QtCore.QSize(0, 28))

        return header_item

    def _create_second_header_item(self):

        # Import toolbar widget
        from gui.widgets.toolbar import ToolBar

        # Create and configure second header item
        icon = qta_icon("ph.list-fill", color="white")
        header_item = QtWidgets.QListWidgetItem(icon, "Custom Resources", self)
        header_item.setFlags(header_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        header_item.setFlags(header_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsSelectable)
        header_item.setSizeHint(QtCore.QSize(0, 28))

        # Create toolbar with add/delete actions
        toolbar = ToolBar(
            self,
            trailing=True,
            actions=[
                (
                    qta_icon("mdi.minus", color="gray", active_color="white"),
                    "Delete",
                    self._execute,
                ),
                (
                    qta_icon("mdi.plus", color="gray", active_color="white"),
                    "Add",
                    self._execute,
                ),
            ],
        )

        self.setItemWidget(header_item, toolbar)
        return header_item

    def add_items(self, flows: dict, editable=False, selectable=False):

        # Add custom flow items with configured flags
        for flow, _class in flows.items():

            item = QtWidgets.QListWidgetItem(
                _class.Attrs.image, _class.Attrs._name, self
            )
            item.setSizeHint(QtCore.QSize(0, 28))

            if not editable:
                item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)

            if not selectable:
                item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsSelectable)

    def paintEvent(self, event):

        # Draw separator lines between sections
        painter = QtGui.QPainter(self.viewport())
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        first_section_bl = self.visualItemRect(self._first_header).bottomLeft()
        first_section_br = self.visualItemRect(self._first_header).bottomRight()
        second_section_tl = self.visualItemRect(self._second_header).topLeft()
        second_section_tr = self.visualItemRect(self._second_header).topRight()

        separator_pen = QtGui.QPen(QtGui.QColor(0xFFFFFF), 1.0)
        painter.setPen(separator_pen)
        painter.drawLine(first_section_bl, first_section_br)
        painter.drawLine(second_section_tl, second_section_tr)
        painter.end()

        super().paintEvent(event)
