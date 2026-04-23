# Encoding: utf-8
# Module name: table
# Description: A QTableWidget wrapper for displaying tabular data in the Climact application

# Imports (standard)
from __future__ import annotations
import pandas


# Imports (third party)
from PySide6 import QtCore, QtWidgets


# Class definition
class Table(QtWidgets.QTableWidget):

    # Constructor:
    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent)

        self.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )

        self.verticalHeader().setVisible(False)
        self.setShowGrid(True)

    def load_data(self, data: pandas.DataFrame):

        self.clear()
        self.setRowCount(data.shape[0])
        self.setColumnCount(data.shape[1])
        self.setHorizontalHeaderLabels(data.columns.tolist())

        for row in range(data.shape[0]):
            for col in range(data.shape[1]):
                item = QtWidgets.QTableWidgetItem(str(data.iat[row, col]))
                self.setItem(row, col, item)
