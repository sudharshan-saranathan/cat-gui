# Filename: choice.py
# Module name: startup
# Description: Button widgets for startup actions.

import dataclasses
from qtawesome import icon as qta_icon
from PySide6 import QtWidgets, QtCore
from gui.widgets import VLayout


class StartupChoice(QtWidgets.QWidget):

    @dataclasses.dataclass
    class Options:

        style: str = (
            "QPushButton {"
            "   padding: 4px 0px 4px 0px;"
            "   color: #aaaaaa;"
            "   width: 200px;"
            "   text-align: right;"
            "   border-radius: 0px;"
            "   background-color: transparent;"
            "}"
            "QPushButton:hover {"
            "   color: #efefef;"
            "}"
            "QPushButton:checked {"
            "   color: white;"
            "   font-weight: bold;"
            "}"
        )

        actions: list[str] = dataclasses.field(
            default_factory=lambda: list(
                [
                    "New Project",  # Button to create a new project.
                    "Quit",  # Abort startup and quit the application.
                ]
            )
        )

    # Signals triggered by the buttons
    sig_button_new_clicked = QtCore.Signal()
    sig_button_quit_clicked = QtCore.Signal()

    def __init__(self, parent=None):
        """
        Initialize the startup choice widget.

        Args:
            parent: Parent widget (optional).
        """

        super().__init__(parent)

        self._opts = StartupChoice.Options()
        self._group = QtWidgets.QButtonGroup(self, exclusive=True)

        self._setup_ui()

    def _setup_ui(self) -> None:

        # Create the buttons defined in `self._opts`
        button_new = self._create_button(
            self._opts.actions[0],
            attr={"label": "mdi.folder-plus", "color": "#ffcb00"},
            style=self._opts.style,
        )

        button_quit = self._create_button(
            self._opts.actions[1],
            attr={"label": "mdi.exit-run", "color": "#efefef"},
            style=self._opts.style,
        )

        # Connect button signals to widget signals:
        button_new.clicked.connect(self.sig_button_new_clicked)
        button_quit.clicked.connect(self.sig_button_quit_clicked)

        # Add buttons to the exclusive button group:
        self._group.addButton(button_new)
        self._group.addButton(button_quit)

        # Arrange buttons in a vertical layout with stretching:
        layout = VLayout(self)
        layout.addStretch(5)
        layout.addWidget(button_new)
        layout.addWidget(button_quit)
        layout.addStretch(5)

    @staticmethod
    def _create_button(
        text: str,  # Button label.
        attr: dict[str, str],  # Icon attributes.
        checkable=False,  # Checkable flag.
        style: str = str(),  # Custom stylesheet.
    ) -> QtWidgets.QPushButton:
        """
        Create a styled push button with a QtAwesome icon.

        Args:
            text: The button text label.
            attr: Dictionary with 'label' (icon name) and 'color' keys.
            checkable: Whether the button is checkable (default: False).
            style: QSS stylesheet to apply (default: empty).

        Returns:
            A configured QPushButton instance.
        """

        # Extract label and color from the provided attribute-dictionary
        label = attr.get("label", "Button")
        color = attr.get("color", "#40474d")

        # Create the button and set style, icon, ...
        button = QtWidgets.QPushButton(text)
        button.setIcon(qta_icon(label, color=color))
        button.setCheckable(checkable)
        button.setStyleSheet(style)

        return button
