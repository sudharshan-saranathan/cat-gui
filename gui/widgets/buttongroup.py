# Filename: buttongroup.py
# Module name: widgets
# Description: Custom button group widget.

"""
Custom button group widget that arranges radio buttons horizontally.

Provides a QFrame subclass that holds a group of mutually exclusive buttons.
"""

from PySide6 import QtWidgets
from gui.widgets.layouts import HLayout


class ButtonGroup(QtWidgets.QFrame):
    """
    Custom button group widget for arranging radio buttons.

    Arranges provided radio buttons horizontally and manages their exclusivity.
    """

    def __init__(self, parent=None, **kwargs):
        """
        Initialize the button group widget.

        Args:
            parent: Parent widget (optional).
            **kwargs: Configuration options:
                - widgets: List of radio buttons to add (default: []).
                - spacing: Space between buttons (default: 8).
                - margins: (left, top, right, bottom) margins (default: (0, 0, 0, 0)).
                - exclusive: Whether only one button can be checked (default: True).
        """
        super().__init__(parent)

        self.layout = HLayout(
            self,
            spacing=kwargs.get("spacing", 8),
            margins=kwargs.get("margins", (0, 0, 0, 0)),
        )

        self.widgets = kwargs.get("widgets", [])
        self.group = QtWidgets.QButtonGroup(self, exclusive=kwargs.get("exclusive", True))

        for widget in self.widgets:
            self.layout.addWidget(widget)
            self.group.addButton(widget)
