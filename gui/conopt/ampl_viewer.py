# Filename: ampl_viewer.py
# Module name: conopt.ampl_viewer
# Description: Viewer for generated AMPL scripts

"""
AMPL script viewer widget for displaying the optimization model.
"""

from PySide6 import QtWidgets, QtGui


class AMPLViewer(QtWidgets.QTextEdit):
    """Read-only AMPL script viewer."""

    def __init__(self, ampl_script: str, parent=None):
        """
        Initialize the AMPL viewer.

        Args:
            ampl_script: AMPL script content to display.
            parent: Parent widget (optional).
        """
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QtGui.QFont("Courier", 10))
        self.setPlainText(ampl_script)
