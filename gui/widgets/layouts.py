# Filename: layouts.py
# Module name: widgets
# Description: Layout utilities with configurable spacing and margins.

"""
Custom layout widgets with convenient configuration options.

Provides QGridLayout, QHBoxLayout, and QVBoxLayout subclasses with
simplified configuration through dataclass options and kwargs.
"""

import dataclasses
from PySide6 import QtWidgets


class GLayout(QtWidgets.QGridLayout):
    """
    Grid layout with configurable spacing and margins.

    A QGridLayout subclass that simplifies setup through dataclass options.
    """

    @dataclasses.dataclass
    class Options:
        """
        Grid layout configuration options.

        Attributes:
            spacing: Space in pixels between layout items (default: 0).
            margins: Tuple of (left, top, right, bottom) margin in pixels (default: (0, 0, 0, 0)).
        """

        spacing: int = 0
        margins: tuple[int, int, int, int] = (0, 0, 0, 0)

    def __init__(self, parent=None, **kwargs):
        """
        Initialize the grid layout.

        Args:
            parent: Parent widget (optional).
            **kwargs: Configuration options:
                - spacing: Space between layout items (default: 0)
                - margins: (left, top, right, bottom) margins (default: (0, 0, 0, 0))
        """

        super().__init__(parent)

        self._opts = GLayout.Options(
            spacing=kwargs.get("spacing", 0),
            margins=kwargs.get("margins", (0, 0, 0, 0)),
        )

        self.setSpacing(self._opts.spacing)
        left, top, right, bottom = self._opts.margins
        self.setContentsMargins(left, top, right, bottom)


class HLayout(QtWidgets.QHBoxLayout):
    """
    Horizontal layout with configurable spacing and margins.

    A QHBoxLayout subclass that simplifies setup and can automatically
    add widgets during initialization.
    """

    @dataclasses.dataclass
    class Options:
        """
        Horizontal layout configuration options.

        Attributes:
            spacing: Space in pixels between layout items (default: 0).
            margins: Tuple of (left, top, right, bottom) margin in pixels (default: (0, 0, 0, 0)).
            widgets: List of widgets to add to the layout (default: []).
        """

        spacing: int = 0
        margins: tuple[int, int, int, int] = (0, 0, 0, 0)
        widgets: list[QtWidgets.QWidget] = dataclasses.field(default_factory=list)

    def __init__(self, parent=None, **kwargs):
        """
        Initialize the horizontal layout.

        Args:
            parent: Parent widget (optional).
            **kwargs: Configuration options:
                - spacing: Space between layout items (default: 0)
                - margins: (left, top, right, bottom) margins (default: (0, 0, 0, 0))
                - widgets: List of widgets to add (default: [])
        """

        super().__init__(parent)

        self._opts = HLayout.Options(
            spacing=kwargs.get("spacing", 0),
            margins=kwargs.get("margins", (0, 0, 0, 0)),
            widgets=kwargs.get("widgets", []),
        )

        self.setSpacing(self._opts.spacing)
        left, top, right, bottom = self._opts.margins
        self.setContentsMargins(left, top, right, bottom)

        for widget in self._opts.widgets:
            self.addWidget(widget)


class VLayout(QtWidgets.QVBoxLayout):
    """
    Vertical layout with configurable spacing and margins.

    A QVBoxLayout subclass that simplifies setup and can automatically
    add widgets during initialization.
    """

    @dataclasses.dataclass
    class Options:
        """
        Vertical layout configuration options.

        Attributes:
            spacing: Space in pixels between layout items (default: 0).
            margins: Tuple of (left, top, right, bottom) margin in pixels (default: (0, 0, 0, 0)).
            widgets: List of widgets to add to the layout (default: []).
        """

        spacing: int = 0
        margins: tuple[int, int, int, int] = (0, 0, 0, 0)
        widgets: list[QtWidgets.QWidget] = dataclasses.field(default_factory=list)

    def __init__(self, parent=None, **kwargs):
        """
        Initialize the vertical layout.

        Args:
            parent: Parent widget (optional).
            **kwargs: Configuration options:
                - spacing: Space between layout items (default: 0)
                - margins: (left, top, right, bottom) margins (default: (0, 0, 0, 0))
                - widgets: List of widgets to add (default: [])
        """

        super().__init__(parent)

        self._opts = VLayout.Options(
            spacing=kwargs.get("spacing", 0),
            margins=kwargs.get("margins", (0, 0, 0, 0)),
            widgets=kwargs.get("widgets", []),
        )

        self.setSpacing(self._opts.spacing)
        left, top, right, bottom = self._opts.margins
        self.setContentsMargins(left, top, right, bottom)

        for widget in self._opts.widgets:
            self.addWidget(widget)
