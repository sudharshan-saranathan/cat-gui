#  Filename: config.py
#  Module name: config
#  Description: Configuration widget for a graph edge.

from __future__ import annotations

import json
import logging
from dataclasses import field, dataclass

from PySide6 import QtGui, QtCore, QtWidgets

from gui.widgets import Field, HLayout


class EdgeConfigWidget(QtWidgets.QDialog):

    @dataclass
    class Appearance:
        """Appearance options for the edge configuration widget."""

        border: QtGui.QBrush
        background: QtGui.QBrush

    @dataclass
    class Geometry:
        """Geometric options."""

        border_radius: int
        padding: int
        dimensions: QtCore.QSize

    def __init__(self, parent=None):
        super().__init__(parent)

        # 1. Initialize defaults
        self._init_defaults()

        # 2. Apply window attributes
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
        self.setContentsMargins(2, 2, 2, 2)

        # 3. Resize window
        self.resize(
            self._geometry.dimensions.width(),
            self._geometry.dimensions.height(),
        )

    def _init_defaults(self) -> None:
        """Initialize default values for appearance and geometry."""
        self._appearance = EdgeConfigWidget.Appearance(
            border=QtGui.QBrush(QtGui.QColor(0x363E41)),
            background=QtGui.QBrush(QtGui.QColor(0x232A2E)),
        )

        self._geometry = EdgeConfigWidget.Geometry(
            border_radius=4,
            padding=4,
            dimensions=QtCore.QSize(900, 600),
        )

        self._src_path = None
        self._tgt_path = None
        self._src_tech = None
        self._tgt_tech = None
        self._existing_links = {}

        # Left pane: info
        self._info = self._init_dock()

        # Right pane: link checkboxes
        self._links_widget = QtWidgets.QWidget()
        links_layout = QtWidgets.QVBoxLayout(self._links_widget)
        self._links_tree = QtWidgets.QTreeWidget()
        self._links_tree.setHeaderLabels(["Source (+)", "Target (-)", "Active"])
        self._links_tree.setColumnWidth(0, 250)
        self._links_tree.setColumnWidth(1, 250)
        self._links_tree.setColumnWidth(2, 100)
        links_layout.addWidget(self._links_tree)

        # Content layout
        content_layout = HLayout(spacing=4, margins=(0, 0, 0, 0))
        content_layout.addWidget(self._info)
        content_layout.addWidget(self._links_widget)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        self._cancel_btn = QtWidgets.QPushButton("Cancel", self)
        self._confirm_btn = QtWidgets.QPushButton("Confirm", self)
        self._confirm_btn.clicked.connect(self._on_confirm)
        self._cancel_btn.clicked.connect(self.close)
        button_layout.addStretch()
        button_layout.addWidget(self._cancel_btn)
        button_layout.addSpacing(8)
        button_layout.addWidget(self._confirm_btn)
        button_layout.setContentsMargins(12, 12, 12, 12)

        # Main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)
        main_layout.addLayout(content_layout)
        main_layout.addLayout(button_layout)

    def _init_dock(self) -> QtWidgets.QDockWidget:
        frame = QtWidgets.QFrame(self)
        frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)

        form = QtWidgets.QFormLayout(
            frame,
            formAlignment=QtCore.Qt.AlignmentFlag.AlignCenter,
            labelAlignment=QtCore.Qt.AlignmentFlag.AlignRight,
            verticalSpacing=4,
        )

        self._src_field = Field(frame, readOnly=True)
        self._tgt_field = Field(frame, readOnly=True)

        form.addRow("Source:", self._src_field)
        form.addRow("Target:", self._tgt_field)

        dock = QtWidgets.QDockWidget("Edge Config", self, floating=False)
        dock.setTitleBarWidget(QtWidgets.QFrame(self))
        dock.setWidget(frame)
        dock.setFixedWidth(280)

        return dock

    def fetch_and_populate(self, src_path: str, tgt_path: str) -> None:
        """Fetch nodes and existing links, populate tree."""
        logger = logging.getLogger("EdgeConfigWidget")
        from gui.compat import SysClient as ClimactClient

        self._src_path = src_path
        self._tgt_path = tgt_path
        client = ClimactClient.instance()

        # Fetch source node full data
        src_resp = client.send_command({"verb": "export", "path": src_path})
        if not src_resp or src_resp.get("status") != "OK":
            logger.warning(f"Failed to fetch source node: {src_path}")
            return

        # Fetch target node full data
        tgt_resp = client.send_command({"verb": "export", "path": tgt_path})
        if not tgt_resp or tgt_resp.get("status") != "OK":
            logger.warning(f"Failed to fetch target node: {tgt_path}")
            return

        src_data = src_resp.get("serialized", {})
        tgt_data = tgt_resp.get("serialized", {})

        self._src_field.setText(src_path.split("/")[-1])
        self._tgt_field.setText(tgt_path.split("/")[-1])

        # Get outputs from source techs
        src_outputs = set()
        tech_groups = src_data.get("tech", {})
        for tech_id, streams in tech_groups.items():
            for key in streams:
                if key.startswith("+"):
                    src_outputs.add(key[1:])

        # Get inputs from target techs
        tgt_inputs = set()
        tech_groups = tgt_data.get("tech", {})
        for tech_id, streams in tech_groups.items():
            for key in streams:
                if key.startswith("-"):
                    tgt_inputs.add(key[1:])

        # TODO: Fetch existing links from SystemCtrl._connections
        # For now, assume no existing links (all available streams are new)
        self._existing_links = {}

        # Populate tree with matching output/input pairs only
        self._links_tree.clear()
        for src_out in src_outputs:
            if src_out in tgt_inputs:
                pair_key = f"{src_out}→{src_out}"
                is_active = self._existing_links.get(pair_key, False)

                item = QtWidgets.QTreeWidgetItem()
                item.setText(0, f"+{src_out}")
                item.setText(1, f"-{src_out}")
                item.setCheckState(2, QtCore.Qt.CheckState.Checked if is_active else QtCore.Qt.CheckState.Unchecked)
                item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
                self._links_tree.addTopLevelItem(item)

    @QtCore.Slot()
    def _on_confirm(self) -> None:
        """Save checked links to server."""
        logger = logging.getLogger("EdgeConfigWidget")
        from gui.compat import SysClient as ClimactClient

        client = ClimactClient.instance()

        for i in range(self._links_tree.topLevelItemCount()):
            item = self._links_tree.topLevelItem(i)
            stream_name = item.text(0)[1:]  # Remove the '+' prefix
            is_checked = item.checkState(2) == QtCore.Qt.CheckState.Checked

            src_port = f"{self._src_path}/{self._src_tech}/+{stream_name}"
            tgt_port = f"{self._tgt_path}/{self._tgt_tech}/-{stream_name}"

            pair_key = f"{stream_name}→{stream_name}"
            already_exists = self._existing_links.get(pair_key) is not None

            if is_checked and not already_exists:
                payload = json.dumps({"source": src_port, "target": tgt_port})
                resp = client.send_command(f"sysctrl create link {payload}")
                if resp and resp.get("status") == 200:
                    logger.info(f"✓ Link created: {stream_name}")
                else:
                    logger.warning(f"✗ Failed to create link {stream_name}: {resp.get('info') if resp else 'no response'}")
            elif not is_checked and already_exists:
                payload = json.dumps({"source": src_port, "target": tgt_port})
                resp = client.send_command(f"sysctrl delete link {payload}")
                if resp and resp.get("status") == 200:
                    logger.info(f"✓ Link deleted: {stream_name}")
                else:
                    logger.warning(f"✗ Failed to delete link {stream_name}: {resp.get('info') if resp else 'no response'}")

        self.close()

    def paintEvent(self, event, /):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QColor(0x232A2E))
        painter.drawRoundedRect(self.rect(), 8, 8)
        super().paintEvent(event)
