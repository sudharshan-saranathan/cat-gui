# Module Name: gui.main_ui.upper
# Description: Upper panel to be shown within a dock

# PySide6 (Python/Qt)
from PySide6 import QtGui
from PySide6 import QtCore
from PySide6 import QtWidgets

# Dataclass
from dataclasses import field
from dataclasses import dataclass

# Relay
from gui.main_ui.bus import MainGuiRelay


class UpperPanel(QtWidgets.QFrame):

    @dataclass
    class Appearance:
        border_color: QtGui.QColor
        border_width: float
        background_color: QtGui.QColor
        background_pattern: QtCore.Qt.BrushStyle

    @dataclass
    class Geometry:
        margins: tuple  # (left, top, right, bottom)

    @dataclass
    class Behavior:
        frameless: bool
        translucent: bool

    def __init__(self, parent=None):

        # 1. Initialize base class
        super().__init__(parent)

        # 2. Initialize defaults
        self._init_defaults()

        # 3. Apply appearance and geometry
        self.setContentsMargins(*self._geometry.margins)
        if self._behavior.frameless:
            self.setWindowFlag(QtCore.Qt.WindowType.FramelessWindowHint)
        if self._behavior.translucent:
            self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)

        # 4. Initialize UI components
        self._init_form()

        # 5. Connect to signals
        from gui.bus import Relay
        from gui.main_ui.bus import MainGuiRelay

        events_bus = Relay.instance()
        events_bus.sig_project_loaded.connect(self._on_project_loaded)

        main_ui_bus = MainGuiRelay.instance()
        main_ui_bus.sig_project_load_success.connect(self._on_templates_loaded)
        main_ui_bus.sig_project_load_failure.connect(self._on_templates_load_failed)

    def _init_defaults(self) -> None:
        """Initialize default values for appearance, geometry, and behavior."""
        self._appearance = UpperPanel.Appearance(
            border_color=QtGui.QColor(0x40474D),
            border_width=1.0,
            background_color=QtGui.QColor(0x40474D),
            background_pattern=QtCore.Qt.BrushStyle.SolidPattern,
        )
        self._geometry = UpperPanel.Geometry(
            margins=(8, 8, 8, 8),
        )
        self._behavior = UpperPanel.Behavior(
            frameless=True,
            translucent=True,
        )

    def _init_form(self):

        # 1. Create form field widgets
        self._prj_field = QtWidgets.QLineEdit()
        self._prj_field.setEnabled(False)
        self._prj_field.setPlaceholderText("No project loaded")

        self._tmp_field = QtWidgets.QListWidget()

        # 2. Configure form layout
        growth_policy = QtWidgets.QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        self._form = QtWidgets.QFormLayout(self)
        self._form.setFieldGrowthPolicy(growth_policy)
        self._form.setContentsMargins(0, 0, 0, 0)
        self._form.setSpacing(4)

        # 3. Arrange the widget(s) in the form
        self._form.addRow("Project:", self._prj_field)
        self._form.addRow("Markers:", self._tmp_field)
        self._form.addRow("", QtWidgets.QFrame())

        self._tmp_field.currentTextChanged.connect(self._on_template_selected)

    @QtCore.Slot(str)
    def _on_project_loaded(self, project_name: str) -> None:

        # Update project field
        self._prj_field.setText(project_name)

        bus = MainGuiRelay.instance()
        bus.fetch_templates()

    @QtCore.Slot(list)
    def _on_templates_loaded(self, templates: list) -> None:

        # Populate list widget
        self._tmp_field.clear()
        self._tmp_field.addItems(templates)

    @QtCore.Slot(str)
    def _on_templates_load_failed(self, error_msg: str) -> None:

        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Failed to load templates: {error_msg}")

    @QtCore.Slot(str)
    def _on_template_selected(self, template_uid: str) -> None:
        if not template_uid:
            return

        from gui.maps import MapsRelay

        MapsRelay.instance().sig_focus_template.emit(template_uid)

    def paintEvent(self, event):

        # Configure painter and draw background
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        pen = QtGui.QPen(self._appearance.border_color, self._appearance.border_width)
        brs = QtGui.QBrush(
            self._appearance.background_color, self._appearance.background_pattern
        )

        painter.setPen(pen)
        painter.setBrush(brs)
        painter.drawRoundedRect(self.rect(), 6, 6)
        painter.end()

        # Call parent class implementation
        super().paintEvent(event)
