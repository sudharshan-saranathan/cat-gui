# Encoding: utf-8
# Module name: buses
# Description: Widget and graph buses for inter-component communication.

# Imports (standard):
from __future__ import annotations


# Imports (third party):
from PySide6 import QtGui
from PySide6 import QtCore
from PySide6 import QtWidgets


# Imports (local): none


# Event relay class:
class Relay(QtCore.QObject):
	"""
	Application-wide relay for inter-component communication.
	Implements the singleton pattern to ensure a single instance.
	"""

	# Singleton instance
	_instance = None

	# Signals for widget lifecycle events:
	sig_show_status = QtCore.Signal(str)
	sig_open_widget = QtCore.Signal(QtWidgets.QWidget, str, QtGui.QIcon)
	sig_project_loaded = QtCore.Signal(str)  # project_name

	# Signals for graphics object lifecycle events:
	sig_canvas_created = QtCore.Signal(QtWidgets.QGraphicsScene, str)  # scene, label
	sig_load_blueprint = QtCore.Signal(QtWidgets.QGraphicsScene, dict)  # scene, blueprint
	sig_item_created = QtCore.Signal(QtWidgets.QGraphicsObject)
	sig_item_clicked = QtCore.Signal(QtWidgets.QGraphicsObject)
	sig_item_deleted = QtCore.Signal(QtWidgets.QGraphicsObject)
	sig_item_updated = QtCore.Signal(QtWidgets.QGraphicsObject)
	sig_item_focused = QtCore.Signal(QtWidgets.QGraphicsObject)

	# Default constructor:
	def __init__(self):
		super().__init__()

		# Initialize database:
		self._database: dict[int, dict] = dict()

	@classmethod
	def instance(cls) -> "Relay":
		if cls._instance is None:
			cls._instance = cls()
		return cls._instance


# Instantiate the global relay:
relay = Relay.instance()
