#  Filename: config.py
#  Module name: config
#  Description: Configuration widget for a graph node.

from __future__ import annotations

# Standard
import typing

# Dataclass
from dataclasses import field
from dataclasses import dataclass

# PySide6 (Python/Qt)
from PySide6 import QtGui
from PySide6 import QtCore
from PySide6 import QtWidgets

# Climact
from gui.widgets import Field, HLayout
from gui.widgets import ComboBox
from gui.widgets import TabWidget


class NodeConfigWidget(QtWidgets.QDialog):

    @dataclass
    class Appearance:
        """Appearance options for the node configuration widget.

        Attributes:
            border: The widget's border brush.
            background: The widget's background brush.
        """

        border: QtGui.QBrush
        background: QtGui.QBrush

    @dataclass
    class Geometry:
        """Geometric options.

        Attributes:
            border_radius: Radius of the node's rounded corners.
            padding: The node's default padding.
            dimensions: The node's default dimensions when created (fixed).
        """

        border_radius: int
        padding: int
        dimensions: QtCore.QSize

    @dataclass
    class Data:
        """Data storage options.

        Attributes:
            consumed: The node's default consumed streams.
            produced: The node's default produced streams.
            parameters: The node's default parameters.
            decisions: The node's default decision variables.
            equations: The node's default equations.
        """

        consumed: dict[str, typing.Any]
        produced: dict[str, typing.Any]
        parameters: dict[str, typing.Any]
        decisions: dict[str, typing.Any]
        equations: dict[str, typing.Any]

    def __init__(self, parent=None):

        # 1. Initialize base class
        super().__init__(parent)

        # 2. Initialize defaults
        self._init_defaults()

        # 3. Configure window appearance
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
        self.setContentsMargins(2, 2, 2, 2)

        # 4. Set window dimensions
        self.resize(
            self._geometry.dimensions.width(),
            self._geometry.dimensions.height(),
        )

    def _init_defaults(self) -> None:
        """Initialize default values for appearance, geometry, and data."""
        self._appearance = NodeConfigWidget.Appearance(
            border=QtGui.QBrush(QtGui.QColor(0x363E41)),
            background=QtGui.QBrush(QtGui.QColor(0x232A2E)),
        )

        self._geometry = NodeConfigWidget.Geometry(
            border_radius=4,
            padding=4,
            dimensions=QtCore.QSize(1200, 720),
        )

        self._data = NodeConfigWidget.Data(
            consumed={},
            produced={},
            parameters={},
            decisions={},
            equations={},
        )

        # Node context (set by caller via from_data)
        self._node_item = None
        self._node_path = None

        # UI components
        self._info = self._init_dock()
        self._stacked_widget = QtWidgets.QStackedWidget(self)
        self._default_tab = QtWidgets.QLabel(
            "Click + on the top-right corner to define a new technology.",
            self,
            alignment=QtCore.Qt.AlignmentFlag.AlignCenter,
        )
        self._stacked_widget.addWidget(self._default_tab)

        # Right pane: stacked widget with buttons below
        right_pane = QtWidgets.QVBoxLayout()
        right_pane.setContentsMargins(0, 0, 0, 0)
        right_pane.setSpacing(2)
        right_pane.addWidget(self._stacked_widget)

        # Confirm and Cancel buttons (right-aligned with margin)
        button_layout = QtWidgets.QHBoxLayout()
        self._cancel_btn = QtWidgets.QPushButton("Cancel", self)
        self._confirm_btn = QtWidgets.QPushButton("Confirm", self)
        self._confirm_btn.clicked.connect(self._on_confirm)
        self._cancel_btn.clicked.connect(self.close)
        button_layout.addStretch()  # Push buttons to the right
        button_layout.addWidget(self._cancel_btn)
        button_layout.addSpacing(8)  # Spacing between buttons
        button_layout.addWidget(self._confirm_btn)
        button_layout.setContentsMargins(12, 12, 12, 12)  # 12px margin on all sides
        right_pane.addLayout(button_layout)

        # Main layout with left pane (dock) and right pane (stacked + buttons)
        content_layout = HLayout(spacing=4, margins=(0, 0, 0, 0))
        content_layout.addWidget(self._info, 0, QtCore.Qt.AlignmentFlag.AlignVCenter)  # 0 stretch, vcenter aligned
        content_layout.addLayout(right_pane)

        # Main dialog layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)
        main_layout.addLayout(content_layout)

    def _init_dock(self) -> QtWidgets.QDockWidget:

        frame = QtWidgets.QFrame(self)
        frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)

        # Main vertical layout for dock
        main_layout = QtWidgets.QVBoxLayout(frame)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # Top: Form layout with fields (all equal width)
        form = QtWidgets.QFormLayout(
            formAlignment=QtCore.Qt.AlignmentFlag.AlignCenter,
            labelAlignment=QtCore.Qt.AlignmentFlag.AlignRight,
            verticalSpacing=4,
            fieldGrowthPolicy=QtWidgets.QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow,
        )

        name_field = Field(frame, readOnly=True)
        name_field.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        self._type_combo = ComboBox(frame)
        self._type_combo.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        form.addRow("Process:", name_field)
        form.addRow("Tech/Type:", self._type_combo)

        # Add button for new technology
        new_tech_btn = QtWidgets.QPushButton("+ Add Technology", frame)
        new_tech_btn.clicked.connect(self._on_new_tech_clicked)
        form.addRow("", new_tech_btn)

        main_layout.addLayout(form)
        main_layout.addStretch()

        # Connect combo box to page switching
        self._type_combo.currentTextChanged.connect(self._on_tech_selected)

        dock = QtWidgets.QDockWidget("Node Config", self, floating=False)
        dock.setTitleBarWidget(QtWidgets.QFrame(self))
        dock.setWidget(frame)
        dock.setFixedWidth(280)

        return dock

    def add_tech_tab(self, tech_name: str) -> None:
        """Add a new technology tab to the stacked widget."""
        tech_tab_widget = self._create_tab_widget()
        tech_tab_widget.tech_name = tech_name
        self._stacked_widget.addWidget(tech_tab_widget)
        self._type_combo.addItem(tech_name)

    @QtCore.Slot(str)
    def _on_tech_selected(self, tech_name: str) -> None:
        """Handle technology selection from combo box."""
        import logging
        logger = logging.getLogger("NodeConfigWidget")

        if not tech_name:
            return

        # Find and switch to the corresponding tech tab
        for idx in range(self._stacked_widget.count()):
            widget = self._stacked_widget.widget(idx)
            if hasattr(widget, "tech_name") and widget.tech_name == tech_name:
                self._stacked_widget.setCurrentIndex(idx)
                logger.info(f"Switched to tech '{tech_name}' at index {idx}")
                return

        logger.warning(f"Could not find tech '{tech_name}' in stacked widget")

    @QtCore.Slot()
    def _on_new_tech_clicked(self) -> None:
        """Show input dialog to create a new technology."""
        tech_name, ok = QtWidgets.QInputDialog.getText(
            self,
            "New Technology",
            "Technology name:",
            QtWidgets.QLineEdit.EchoMode.Normal,
        )

        if ok and tech_name.strip():
            self.add_tech_tab(tech_name.strip())
            # Switch to the newly created tab
            self._type_combo.setCurrentText(tech_name.strip())

    @QtCore.Slot()
    def _on_confirm(self) -> None:
        """Collect all tech and stream data and commit to server."""
        import logging
        logger = logging.getLogger("NodeConfigWidget")

        if not self._node_item:
            logger.warning("No node item set")
            return

        logger.info("Confirming node config...")

        from gui.compat import Translator
        from gui.compat import SysClient as ClimactClient
        from gui.compat import DatClient

        translator = Translator.instance()
        client = ClimactClient.instance()
        dat_client = DatClient.instance()
        node_path = self._node_path or translator._paths.get(id(self._node_item))
        if not node_path:
            logger.warning("Could not resolve node path for node config commit")
            return

        # Collect data from all tech tabs (excluding default tab)
        all_techs = {}

        for idx in range(self._stacked_widget.count()):
            widget = self._stacked_widget.widget(idx)

            # Skip the default instruction tab
            if widget is self._default_tab:
                continue

            # Get tech name from widget
            if not hasattr(widget, "tech_name"):
                continue

            tech_name = widget.tech_name
            streams = {}

            # Collect input streams (-stream)
            if hasattr(widget, "inp_tree"):
                inp_data = widget.inp_tree.to_dict() if hasattr(widget.inp_tree, "to_dict") else {}
                for key, val in inp_data.items():
                    streams[f"-{key}"] = val

            # Collect output streams (+stream)
            if hasattr(widget, "out_tree"):
                out_data = widget.out_tree.to_dict() if hasattr(widget.out_tree, "to_dict") else {}
                for key, val in out_data.items():
                    streams[f"+{key}"] = val

            # Collect parameters (#param)
            if hasattr(widget, "par_tree"):
                par_data = widget.par_tree.to_dict() if hasattr(widget.par_tree, "to_dict") else {}
                for key, val in par_data.items():
                    streams[f"#{key}"] = val

            # Collect decision variables (?decision)
            if hasattr(widget, "dec_tree"):
                dec_data = widget.dec_tree.to_dict() if hasattr(widget.dec_tree, "to_dict") else {}
                for key, val in dec_data.items():
                    streams[f"?{key}"] = val

            # Collect equations (=eq)
            if hasattr(widget, "eqn_tree"):
                eqn_data = widget.eqn_tree.to_dict() if hasattr(widget.eqn_tree, "to_dict") else {}
                streams.update(eqn_data)

            all_techs[tech_name] = streams

        try:
            for tech_name, streams in all_techs.items():
                logger.info(f"Committing tech '{tech_name}' with {len(streams)} streams")

                tech_path = f"{node_path}/{tech_name}"
                tech_meta = {}
                param_entries = {}

                for key, value in streams.items():
                    if key.startswith("#") and isinstance(value, dict):
                        param_type = value.get("type", "")
                        if param_type:
                            tech_meta[key] = param_type
                            param_entries[key] = value
                    elif isinstance(value, str):
                        tech_meta[key] = value

                check_resp = client.send_command({"verb": "info", "path": tech_path})
                tech_exists = check_resp and check_resp.get("status") in ("OK", 200)

                sync_resp = None
                if tech_exists:
                    export_resp = client.send_command({"verb": "export", "path": tech_path})
                    existing_meta = {}
                    if export_resp and export_resp.get("status") in ("OK", 200):
                        existing_meta = export_resp.get("serialized", {}) or {}

                    removals = {
                        key: None
                        for key in existing_meta
                        if key.startswith(("+", "-", "#", "?", "=")) and key not in tech_meta
                    }
                    sync_resp = client.send_command(
                        {"verb": "update", "path": tech_path, "meta": {**tech_meta, **removals}}
                    )
                else:
                    create_resp = client.send_command({"verb": "create", "path": tech_path, "meta": {}})
                    if not create_resp or create_resp.get("status") not in ("OK", 200):
                        logger.warning(
                            f"✗ Failed to create tech {tech_path}: "
                            f"{create_resp.get('info') if create_resp else 'no response'}"
                        )
                        continue
                    sync_resp = client.send_command(
                        {"verb": "update", "path": tech_path, "meta": tech_meta}
                    )

                if sync_resp and sync_resp.get("status") in ("OK", 200):
                    logger.info(f"✓ Synced tech: {tech_path}")
                else:
                    logger.warning(
                        f"✗ Failed to sync tech {tech_path}: "
                        f"{sync_resp.get('info') if sync_resp else 'no response'}"
                    )
                    continue

                # Write parameter values to datastore for all #param entries
                for stream_key, stream_val in param_entries.items():
                    value = str(stream_val.get("value", "")).strip()
                    f_t = str(stream_val.get("f_t", value)).strip()
                    units = str(stream_val.get("units", "")).strip()
                    if not value and not f_t:
                        continue
                    ds_path = f"{node_path}/{tech_name}/#{stream_key[1:]}"
                    ok = dat_client.upsert(ds_path, value or f_t, units=units, f_t=f_t or value)
                    if ok:
                        logger.info(f"✓ Wrote param {ds_path}")
                    else:
                        logger.warning(f"✗ Failed to write param {ds_path}")

            self.close()
        except Exception as e:
            logger.error(f"Failed to commit tech: {e}", exc_info=True)

    def _create_tab_widget(self) -> QtWidgets.QTabWidget:
        """Create a tab widget for a single technology with structured editors."""
        from gui.graph.node.tree import StreamTree, ParamsTree, DecisionTree, EquationTree
        from qtawesome import icon as qta_icon

        inp = StreamTree()
        out = StreamTree()
        par = ParamsTree()
        dec = DecisionTree()
        eqn = EquationTree()

        tabs = TabWidget(self)
        tabs.setTabsClosable(False)  # Disable closable tabs in NodeConfig
        tabs.addTab(inp, qta_icon("mdi.arrow-down-bold", color="gray"), "In")
        tabs.addTab(out, qta_icon("mdi.arrow-up-bold", color="gray"), "Out")
        tabs.addTab(par, qta_icon("mdi.alpha", color="gray"), "Params")
        tabs.addTab(dec, qta_icon("mdi.help-rhombus-outline", color="gray"), "Decision Vars")
        tabs.addTab(eqn, qta_icon("mdi.equal", color="gray"), "Equations")

        # Store references for data collection
        tabs.inp_tree = inp
        tabs.out_tree = out
        tabs.par_tree = par
        tabs.dec_tree = dec
        tabs.eqn_tree = eqn

        return tabs

    def fetch_and_populate(self, node_item) -> None:

        """Fetch node data from server and populate dialog."""

        import logging

        logger = logging.getLogger("NodeConfigWidget")

        # Get the node path: try Translator first (for newly created nodes),
        # then construct from canvas + NUID (for loaded nodes)
        from gui.compat import Translator
        translator = Translator.instance()
        node_path = translator._paths.get(id(node_item))

        if not node_path:
            # Node wasn't created by Translator (it was loaded from server)
            # Construct path from canvas unit UUID + node NUID
            canvas = node_item.scene()
            if canvas:
                unit_uuid = getattr(canvas, "_graph_guid", None)
                node_nuid = getattr(node_item, "_uid", None)
                if unit_uuid and node_nuid:
                    node_path = f"{unit_uuid}/{node_nuid}"
                else:
                    logger.warning(f"Cannot construct path: unit_uuid={unit_uuid}, node_nuid={node_nuid}")
                    return
            else:
                logger.warning("NodeConfigWidget: Node has no scene")
                return

        # Fetch node info from the server using /sys/export endpoint
        try:
            from gui.compat import SysClient as ClimactClient
            client = ClimactClient.instance()

            response = client.send_command({"verb": "export", "path": node_path})

            if response and response.get("status") in ("OK", 200):
                # Server returns full serialized data in 'serialized' key
                data = response.get("serialized", {})
                self._node_path = node_path
                self._populate_from_server_data(data, node_item)
            else:
                status = response.get("status") if response else None
                info = response.get("info") if response else "no response"
                logger.warning(f"Failed to fetch node data: status={status}, info={info}")
        except Exception as e:
            logger.error(f"Error fetching node data: {e}", exc_info=True)

    def _populate_from_server_data(self, data: dict, node_item) -> None:
        """Populate dialog with server node data and create tech tabs."""
        import logging
        logger = logging.getLogger("NodeConfigWidget")

        # Set node item context
        self._node_item = node_item

        # Set the node label (the node's name IS its NUID)
        node_nuid = node_item._uid if node_item else "Unknown"
        name_field = self._info.findChild(Field)
        if name_field:
            name_field.setText(node_nuid)
        else:
            logger.warning(f"Could not find Field widget in dock widget")

        techs = data.get("tech", {})
        logger.info(f"Loaded {len(techs)} technologies for node {node_nuid}")

        # Clear old tech tabs from the previous dialog session (keep the default tab)
        while self._stacked_widget.count() > 1:
            widget = self._stacked_widget.widget(1)  # Always remove index 1 since default is at 0
            self._stacked_widget.removeWidget(widget)

        self._type_combo.blockSignals(True)
        self._type_combo.clear()

        for tech_name, tech_data in techs.items():
            # Create and populate tech tab (which adds to combo)
            self.add_tech_tab(tech_name)

            # Get the tab widget we just added
            tab_widget = self._stacked_widget.widget(self._stacked_widget.count() - 1)
            if not hasattr(tab_widget, "inp_tree"):
                continue

            streams = tech_data if isinstance(tech_data, dict) else {}

            # Count what we're about to add
            eqs = [k for k in streams.keys() if k.startswith("=")]
            logger.info(f"  Populating {tech_name}: {len(streams)} items ({len(eqs)} equations)")
            for stream_key, stream_type in streams.items():
                if stream_key.startswith("~"):
                    continue

                # stream_type could be string or dict
                if isinstance(stream_type, dict):
                    type_name = stream_type.get("type", "")
                else:
                    type_name = str(stream_type)

                # Route to appropriate tree based on prefix
                if stream_key.startswith("-"):
                    # Input stream
                    key = stream_key[1:]
                    if hasattr(tab_widget.inp_tree, "add_item"):
                        tab_widget.inp_tree.add_item(key, type_name)
                elif stream_key.startswith("+"):
                    # Output stream
                    key = stream_key[1:]
                    if hasattr(tab_widget.out_tree, "add_item"):
                        tab_widget.out_tree.add_item(key, type_name)
                elif stream_key.startswith("#"):
                    # Parameter — fetch value and units from the datastore
                    key = stream_key[1:]
                    if hasattr(tab_widget.par_tree, "add_item"):
                        value, units, f_t = "", "", ""
                        node_path = getattr(self, "_node_path", None)
                        if node_path:
                            from gui.compat import DatClient
                            ds_path = f"{node_path}/{tech_name}/{stream_key}"
                            entry = DatClient.instance().read(ds_path)
                            value = entry.get("initial", "")
                            units = entry.get("units", "")
                            f_t = entry.get("f_t", entry.get("f(t)", ""))
                        tab_widget.par_tree.add_item(key, type_name, value, units, f_t)
                elif stream_key.startswith("?"):
                    key = stream_key[1:]
                    if hasattr(tab_widget, "dec_tree"):
                        tab_widget.dec_tree.add_item(key, type_name)
                elif stream_key.startswith("="):
                    if hasattr(tab_widget, "eqn_tree"):
                        tab_widget.eqn_tree.add_item(stream_key[1:], type_name)

        # Set active technology (server returns "active" singular)
        self._type_combo.blockSignals(False)  # Unblock signals before setting active tech

        if self._type_combo.count() > 0:
            # We have techs - show one of them
            active_tech = data.get("active")
            if active_tech and self._type_combo.findText(active_tech) >= 0:
                self._type_combo.setCurrentText(active_tech)
                self._on_tech_selected(active_tech)  # Explicitly switch to the tech tab
            else:
                # If no active tech specified, use the first one
                self._type_combo.setCurrentIndex(0)
                first_tech = self._type_combo.currentText()
                self._on_tech_selected(first_tech)  # Explicitly switch to the first tech tab
        else:
            # No techs - show the default instruction tab
            self._stacked_widget.setCurrentWidget(self._default_tab)
            logger.info("No techs loaded, showing default instruction tab")

    def from_data(self, data: dict[str, typing.Any], node_item=None) -> None:
        """Populate the widget from server node data.

        Args:
            data: Node data dict
            node_item: The NodeRepr QGraphicsObject for commits
        """
        # Store node item for later commits
        self._node_item = node_item

        # Metadata
        meta = data.get("meta", {})

        # Set the node's label
        name_field = self._info.findChild(Field)
        name_field.setText(meta.get("label", "Process"))
        name_field.clearFocus()

        # Populate available technologies in combo box
        available_techs = data.get("available_techs", [])
        self._type_combo.blockSignals(True)
        self._type_combo.clear()
        for tech_name in available_techs:
            self._type_combo.addItem(tech_name)
        self._type_combo.blockSignals(False)

        # Set the active technology
        active_tech = data.get("active_tech")
        if active_tech and active_tech in available_techs:
            self._type_combo.setCurrentText(active_tech)
            # Ensure the stacked widget is switched to this tech
            self._on_tech_selected(active_tech)

        # Load the node's technical details
        # self._inp_tree.from_dict(data.get("consumed", {}))
        # self._out_tree.from_dict(data.get("produced", {}))

    def paintEvent(self, event, /):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QColor(0x232A2E))
        painter.drawRoundedRect(self.rect(), 8, 8)

        super().paintEvent(event)
