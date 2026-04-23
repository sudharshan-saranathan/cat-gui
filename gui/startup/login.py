# Filename: login.py
# Module name: startup.login
# Description: Login widget for the startup dialog

from PySide6 import QtWidgets, QtCore


class LoginWidget(QtWidgets.QWidget):
    """Login widget for user authentication with server configuration."""

    # Signal emitted when user clicks connect
    connect_clicked = QtCore.Signal(str, str, str)  # user_id, ip, port

    def __init__(self, parent=None):
        super().__init__(parent)

        # Input fields
        self._user_id_field = QtWidgets.QLineEdit()
        self._user_id_field.setPlaceholderText("Enter User ID")

        self._ip_field = QtWidgets.QLineEdit()
        self._ip_field.setPlaceholderText("localhost")
        self._ip_field.setText("localhost")

        self._port_field = QtWidgets.QLineEdit()
        self._port_field.setPlaceholderText("8000")
        self._port_field.setText("8000")

        # Apply field styles
        field_style = (
            "QLineEdit {"
            "  background-color: #1a1f23;"
            "  border: 1px solid #4f4f4f;"
            "  border-radius: 4px;"
            "  color: #ffffff;"
            "  padding: 8px;"
            "}"
            "QLineEdit:focus {"
            "  border: 1px solid #00bcd4;"
            "}"
        )
        self._user_id_field.setStyleSheet(field_style)
        self._ip_field.setStyleSheet(field_style)
        self._port_field.setStyleSheet(field_style)

        # Buttons
        self._connect_button = QtWidgets.QPushButton("Connect")
        self._connect_button.setStyleSheet(
            "QPushButton {"
            "  background-color: #00bcd4;"
            "  color: #000000;"
            "  border: none;"
            "  border-radius: 4px;"
            "  padding: 10px 20px;"
            "  font-weight: bold;"
            "}"
            "QPushButton:hover {"
            "  background-color: #00acc1;"
            "}"
            "QPushButton:pressed {"
            "  background-color: #0097a7;"
            "}"
        )

        self._exit_button = QtWidgets.QPushButton("Exit")
        self._exit_button.setStyleSheet(
            "QPushButton {"
            "  background-color: transparent;"
            "  color: #aaaaaa;"
            "  border: 1px solid #4f4f4f;"
            "  border-radius: 4px;"
            "  padding: 10px 20px;"
            "  font-weight: bold;"
            "}"
            "QPushButton:hover {"
            "  color: #ffffff;"
            "  border: 1px solid #ff6b6b;"
            "}"
            "QPushButton:pressed {"
            "  background-color: rgba(255, 107, 107, 0.1);"
            "}"
        )

        # Layout
        self._init_layout()
        self._init_connections()

    def _init_layout(self):
        """Initialize the layout with vertically centered form."""
        outer_layout = QtWidgets.QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addStretch()

        # Form widget
        form_widget = QtWidgets.QWidget()
        form_layout = QtWidgets.QVBoxLayout(form_widget)
        form_layout.setContentsMargins(12, 16, 12, 16)
        form_layout.setSpacing(12)

        label_style = "color: #ffffff; font-weight: bold;"

        # User ID
        user_id_label = QtWidgets.QLabel("User ID:")
        user_id_label.setStyleSheet(label_style)
        form_layout.addWidget(user_id_label)
        form_layout.addWidget(self._user_id_field)

        form_layout.addSpacing(8)

        # IP and Port on same row
        ip_port_labels_layout = QtWidgets.QHBoxLayout()
        ip_port_labels_layout.setContentsMargins(0, 0, 0, 0)
        ip_port_labels_layout.setSpacing(8)

        ip_label = QtWidgets.QLabel("IP:")
        ip_label.setStyleSheet(label_style)
        ip_port_labels_layout.addWidget(ip_label)

        port_label = QtWidgets.QLabel("Port:")
        port_label.setStyleSheet(label_style)
        ip_port_labels_layout.addWidget(port_label)

        form_layout.addLayout(ip_port_labels_layout)

        ip_port_fields_layout = QtWidgets.QHBoxLayout()
        ip_port_fields_layout.setContentsMargins(0, 0, 0, 0)
        ip_port_fields_layout.setSpacing(8)
        ip_port_fields_layout.addWidget(self._ip_field)
        ip_port_fields_layout.addWidget(self._port_field)

        form_layout.addLayout(ip_port_fields_layout)

        form_layout.addSpacing(16)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)
        button_layout.addWidget(self._connect_button)
        button_layout.addWidget(self._exit_button)

        form_layout.addLayout(button_layout)

        outer_layout.addWidget(form_widget, 0, QtCore.Qt.AlignmentFlag.AlignCenter)
        outer_layout.addStretch()

    def _init_connections(self):
        """Connect button signals."""
        self._connect_button.clicked.connect(self._on_connect)
        self._user_id_field.returnPressed.connect(self._on_connect)
        self._port_field.returnPressed.connect(self._on_connect)

    @QtCore.Slot()
    def _on_connect(self):
        """Handle connect button click."""
        user_id = self._user_id_field.text().strip()
        ip = self._ip_field.text().strip()
        port = self._port_field.text().strip()

        # Validate inputs
        if not user_id:
            QtWidgets.QMessageBox.warning(self, "Invalid Input", "Please enter a User ID")
            return

        if not ip:
            QtWidgets.QMessageBox.warning(self, "Invalid Input", "Please enter an IP address")
            return

        if not port:
            QtWidgets.QMessageBox.warning(self, "Invalid Input", "Please enter a port number")
            return

        try:
            port_int = int(port)
            if port_int < 1 or port_int > 65535:
                raise ValueError
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Invalid Input", "Port must be a number between 1 and 65535")
            return

        # Emit signal with validated inputs
        self.connect_clicked.emit(user_id, ip, port)

    def get_exit_button(self):
        """Return the exit button for external connections."""
        return self._exit_button
