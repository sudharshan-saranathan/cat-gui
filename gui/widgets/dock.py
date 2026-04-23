# Module Name: gui.widgets.dock
# Description: A QDockWidget subclass.


# Dataclass
from dataclasses import dataclass

# PySide6 (Python/Qt)
from PySide6 import QtCore
from PySide6 import QtWidgets


class Dock(QtWidgets.QDockWidget):

    @dataclass
    class Appearance:
        pass

    @dataclass
    class Geometry:
        minimum_size: QtCore.QSize

    @dataclass
    class Behavior:
        floating: bool
        features: QtWidgets.QDockWidget.DockWidgetFeature

    def __init__(
        self,
        title: QtWidgets.QWidget = None,
        widget: QtWidgets.QWidget = None,
        parent=None,
    ):

        """
        Initialize the sidebar dock widget.
        """

        # 1. Initialize defaults
        self._init_defaults()

        # 2. Initialize base class with attributes
        super().__init__(
            parent,
            floating=self._behavior.floating,
            features=self._behavior.features,
        )

        # 3. Customize appearance and add UI components
        self.setMinimumSize(self._geometry.minimum_size)

        self.setTitleBarWidget(title)
        self.setWidget(widget)

    def _init_defaults(self) -> None:
        """Initialize default values for appearance, geometry, and behavior."""
        self._appearance = Dock.Appearance()
        self._geometry = Dock.Geometry(
            minimum_size=QtCore.QSize(360, 360),
        )
        self._behavior = Dock.Behavior(
            floating=False,
            features=QtWidgets.QDockWidget.DockWidgetFeature.NoDockWidgetFeatures,
        )
