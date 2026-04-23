# Filename: lights.py
# Module name: widgets
# Description: Traffic light window control buttons (minimize, maximize, close).

"""
Traffic light window control widget.

Provides a toolbar with `Minimize`, `Maximize`, and `Close` buttons styled as macOS-style traffic lights.
Emits signals when these buttons are clicked.
"""

# PySide6 (Python/Qt)
from PySide6 import QtCore
from PySide6 import QtWidgets


class TrafficLights(QtWidgets.QToolBar):
    """
    A traffic light-style window control toolbar.

    Displays three buttons styled as macOS-style traffic lights for minimizing, maximizing,
    and closing the window. Each button emits a corresponding signal when clicked.
    """

    # Signals emitted when traffic light buttons are clicked
    minimize_clicked = QtCore.Signal()
    maximize_clicked = QtCore.Signal()
    close_clicked = QtCore.Signal()

    def __init__(self, parent=None):

        super().__init__(
            parent,
            iconSize=QtCore.QSize(18, 18),
            floatable=False,
            movable=False,
        )

        spacer = QtWidgets.QFrame(self)
        spacer.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )

        self.addWidget(spacer)
        self._init_maximize_button()
        self._init_minimize_button()
        self._init_close_button()


    def _init_maximize_button(self):

        # Required
        from qtawesome import icon

        # Maximize button attribute(s):
        default = "ph.circle-fill"
        hovered = "ph.plus-circle-fill"
        color = "green"

        button = self.addAction(icon(default, color=color, active=hovered), "Maximize")
        button.triggered.connect(lambda: self.maximize_clicked.emit())

    def _init_minimize_button(self):

        # Required
        from qtawesome import icon

        # Button attribute(s):
        default = "ph.circle-fill"
        hovered = "ph.minus-circle-fill"
        color = "#ffcb00"

        # Add icon button
        button = self.addAction(icon(default, color=color, active=hovered), "Minimize")
        button.triggered.connect(lambda: self.minimize_clicked.emit())

    def _init_close_button(self):

        # Required
        from qtawesome import icon

        # Button attribute(s):
        default = "ph.circle-fill"
        hovered = "ph.x-circle-fill"
        color = "#ef6f6c"

        # Add icon button
        button = self.addAction(icon(default, color=color, active=hovered), "Close")
        button.triggered.connect(lambda: self.close_clicked.emit())
