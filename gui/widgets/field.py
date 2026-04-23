#  Filename: gui/widgets/field.py
#  Module name: gui.widgets
#  Description: Custom widgets for the GUI

from __future__ import annotations

# Standard Library
from typing import Any


# PySide6 (Python/Qt)
from PySide6 import QtGui
from PySide6 import QtCore
from PySide6 import QtWidgets
from qtawesome import icon


class Field(QtWidgets.QLineEdit):
    def __init__(self, parent: QtWidgets.QWidget | None = None, **kwargs) -> None:
        super().__init__(parent, **kwargs)

        self.returnPressed.connect(self._on_return_pressed)
        self._tick = self.addAction(
            icon("mdi.check-bold", color="cyan"),
            QtWidgets.QLineEdit.ActionPosition.TrailingPosition,
        )
        self._tick.setVisible(False)

    def _on_return_pressed(self) -> None:
        QtCore.QTimer.singleShot(0, self.clearFocus)
        QtCore.QTimer.singleShot(0, lambda: self.show_tick(True))
        QtCore.QTimer.singleShot(1000, lambda: self.show_tick(False))

    def show_tick(self, flag: bool) -> None:
        self._tick.setVisible(flag)
