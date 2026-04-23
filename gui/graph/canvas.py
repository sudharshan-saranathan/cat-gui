# Filename: canvas.py
# Module name: graph
# Description: Graphics scene for displaying node graphs.

from __future__ import annotations

# Built-ins
import logging
import typing
import types
import uuid
import json

# Dataclass
from dataclasses import field
from dataclasses import dataclass

# Standard
import qtawesome as qta

# PySide6 (Python/Qt)
from PySide6 import QtGui
from PySide6 import QtCore
from PySide6 import QtWidgets

# Climact
from gui.graph.node import NodeRepr
from gui.graph.edge import EdgeRepr
from gui.compat import SysClient as ClimactClient
from gui.bus import Relay


class Canvas(QtWidgets.QGraphicsScene):

    # Logger
    _logger = logging.getLogger("Canvas")

    @dataclass
    class Appearance:
        brush: QtGui.QBrush

    @dataclass
    class Geometry:
        bounds: QtCore.QRectF

    @dataclass
    class Behavior:
        pass

    def __init__(self, parent=None):

        # 1. Store canvas ID
        self._uid = uuid.uuid4().hex

        # 2. Initialize super-class first (required before addItem can be called)
        super().__init__(
            QtCore.QRectF(0, 0, 2000, 2000),
            parent=parent,
            backgroundBrush=QtGui.QBrush(
                QtGui.QColor("#ffffff"),
                QtCore.Qt.BrushStyle.SolidPattern,
            ),
        )

        # 3. Initialize defaults (after super init)
        self._init_defaults()

    def _init_defaults(self) -> None:

        # 1. Initialize appearance and geometry
        self._appearance = Canvas.Appearance(
            brush=self.backgroundBrush(),
        )
        self._geometry = Canvas.Geometry(
            bounds=self.sceneRect(),
        )

        # 2. Initialize preview edge and context menu
        self._rmb_coordinate = QtCore.QPoint()
        self._menu = self._init_menu()
        self._preview = types.SimpleNamespace(
            active=False,
            origin=None,
            vector=EdgeRepr(uuid.uuid4().hex),
        )
        self.addItem(self._preview.vector)

        # 3. Initialize server client and graph reference
        self._client = ClimactClient.instance()
        self._graph_guid = None

        # 4. Connect to the graph relay for blueprint loading
        from gui.graph.bus import GraphRelay

        graph_relay = GraphRelay.instance()
        graph_relay.sig_blueprint_loaded.connect(self._on_load_blueprint)

    def _init_menu(self) -> QtWidgets.QMenu:
        """
        Initialize the context menu with graph editing actions.
        """

        cxt_menu = QtWidgets.QMenu()
        obj_menu = cxt_menu.addMenu(qta.icon("mdi.plus", color="cyan"), "Create")

        # Undo/Redo operations
        undo_action = QtGui.QAction(
            "Undo",
            parent=cxt_menu,
            icon=qta.icon("mdi.undo", color="#efefef"),
            toolTip="Undo the last action",
            iconVisibleInMenu=True,
            shortcutVisibleInContextMenu=False,
            shortcut=QtGui.QKeySequence(QtGui.QKeySequence.StandardKey.Undo),
        )
        cxt_menu.addAction(undo_action)

        redo_action = QtGui.QAction(
            "Redo",
            parent=cxt_menu,
            icon=qta.icon("mdi.redo", color="#efefef"),
            toolTip="Redo the last undone action",
            iconVisibleInMenu=True,
            shortcutVisibleInContextMenu=False,
            shortcut=QtGui.QKeySequence(QtGui.QKeySequence.StandardKey.Redo),
        )
        cxt_menu.addAction(redo_action)
        cxt_menu.addSeparator()

        # Copy/Paste/Delete operations
        copy_action = QtGui.QAction(
            "Copy",
            parent=cxt_menu,
            icon=qta.icon("mdi.content-copy", color="#efefef"),
            toolTip="Copy selected items",
            iconVisibleInMenu=True,
            shortcutVisibleInContextMenu=False,
            shortcut=QtGui.QKeySequence(QtGui.QKeySequence.StandardKey.Copy),
        )
        cxt_menu.addAction(copy_action)

        paste_action = QtGui.QAction(
            "Paste",
            parent=cxt_menu,
            icon=qta.icon("mdi.content-paste", color="#efefef"),
            toolTip="Paste items from clipboard",
            iconVisibleInMenu=True,
            shortcutVisibleInContextMenu=False,
            shortcut=QtGui.QKeySequence(QtGui.QKeySequence.StandardKey.Paste),
        )
        cxt_menu.addAction(paste_action)

        delete_action = QtGui.QAction(
            "Delete",
            parent=cxt_menu,
            icon=qta.icon("mdi.delete", color="red"),
            toolTip="Delete selected items",
            iconVisibleInMenu=True,
            shortcutVisibleInContextMenu=False,
            shortcut=QtGui.QKeySequence(QtGui.QKeySequence.StandardKey.Delete),
        )
        cxt_menu.addAction(delete_action)
        cxt_menu.addSeparator()

        # Create submenu actions
        node_action = QtGui.QAction(
            "Node",
            parent=obj_menu,
            icon=qta.icon("ph.browser-fill", color="darkcyan"),
            toolTip="Create a new node",
            iconVisibleInMenu=True,
            shortcutVisibleInContextMenu=False,
            shortcut=QtGui.QKeySequence("Alt+N"),
        )
        node_action.triggered.connect(self._raise_create_node_request)
        obj_menu.addAction(node_action)

        source_action = QtGui.QAction(
            "Source",
            parent=obj_menu,
            icon=qta.icon("mdi.arrow-down-bold"),
            toolTip="Create a new inlet port",
            iconVisibleInMenu=True,
            shortcutVisibleInContextMenu=False,
            shortcut=QtGui.QKeySequence("Alt+I"),
        )
        source_action.triggered.connect(self._raise_create_node_request)
        obj_menu.addAction(source_action)

        sink_action = QtGui.QAction(
            "Sink",
            parent=obj_menu,
            icon=qta.icon("mdi.arrow-up-bold"),
            toolTip="Create a new outlet port",
            iconVisibleInMenu=True,
            shortcutVisibleInContextMenu=False,
            shortcut=QtGui.QKeySequence("Alt+O"),
        )
        sink_action.triggered.connect(self._raise_create_node_request)
        obj_menu.addAction(sink_action)

        return cxt_menu

    def contextMenuEvent(self, event: QtWidgets.QGraphicsSceneContextMenuEvent) -> None:
        """
        Display the context menu at the location of the right-click event.
        :param event: The right-click event, forwarded by Qt.
        """

        super().contextMenuEvent(event)
        if event.isAccepted():
            return

        self._rmb_coordinate = event.scenePos()
        self._menu.exec_(event.screenPos())

    def mouseMoveEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:

        if self._preview.active:

            origin = self._preview.origin.scenePos()
            target = event.scenePos()
            self._preview.vector.update_path(origin, target)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:

        if self._preview.active:

            origin = self._preview.origin
            target = self.itemAt(event.scenePos(), QtGui.QTransform())

            if isinstance(target, NodeRepr) and origin is not target:

                jstr = json.dumps({"source_uid": origin.uid, "target_uid": target.uid})
                self.create_edge_repr(self._uid, uuid.uuid4().hex, jstr)

        self._preview_off()
        super().mouseReleaseEvent(event)

    def addItem(
        self,
        item: QtWidgets.QGraphicsItem,
    ) -> None:

        if isinstance(item, NodeRepr):
            self._register_item_signals(item)

        super().addItem(item)

    def _preview_on(self, vertex: QtWidgets.QGraphicsObject):

        if self._preview.active:
            return  # Do nothing if the preview is already active.

        self._preview.active = True
        self._preview.origin = vertex
        self._preview.vector.show()

    def _preview_off(self):
        self._preview.active = False
        self._preview.origin = None
        self._preview.vector.clear()
        self._preview.vector.hide()

    def _register_item_signals(self, item: QtWidgets.QGraphicsObject):
        """Connects the item's signals to appropriate slots."""

        if callable(signals := getattr(item, "signals", None)):

            sig_dictionary = typing.cast(dict, signals())
            for name, instance in sig_dictionary.items():
                if method := getattr(self, f"_on_{name}", None):
                    instance.connect(method, QtCore.Qt.ConnectionType.QueuedConnection)

        else:
            self._logger.warning(f"Item {item} has no signals defined.")

    @QtCore.Slot()
    def _raise_create_node_request(self) -> None:

        # 1. Check client and graph are available
        if not self._client or not self._graph_guid:

            self._logger.warning("Client not connected to server")
            return

        # 2. Prompt user for node name
        node_name, ok = QtWidgets.QInputDialog.getText(
            None,
            "Create Node",
            "Node name (NUID):",
            QtWidgets.QLineEdit.EchoMode.Normal,
            "Node",
        )

        if not ok or not node_name.strip():

            return

        node_name = node_name.strip()

        # 3. Prepare node data with position
        data = {
            "name": node_name,
            "x": self._rmb_coordinate.x(),
            "y": self._rmb_coordinate.y(),
        }

        # 4. Create visual node representation
        jstr = json.dumps(data)
        self.create_node_repr(self._uid, node_name, jstr)
        self._logger.info(
            f"Created NodeRepr for {node_name} — Translator will sync to server"
        )

    @QtCore.Slot(str)
    def _raise_delete_node_request(self, nuid: str) -> None:
        pass
        # manager = SignalBus()  # Get the singleton instance
        # manager.raise_request("delete_node_item", self._uid, nuid)

    @QtCore.Slot()
    def _raise_create_edge_request(self, suid: str, tuid: str) -> None:
        # TODO: Implement edge/link creation via sysctrl when stream mapping dialog is ready
        # Currently edges are visual-only placeholders
        pass

    @QtCore.Slot(str, str)
    def _raise_delete_edge_request(self, euid: str) -> None:
        pass
        # manager = SignalBus()  # Get the singleton instance
        # manager.data.delete_edge_item.emit(self._uid, euid)

    @QtCore.Slot(NodeRepr)
    def _on_activate_preview(self, item: NodeRepr):

        if not isinstance(item, NodeRepr):
            return

        self._preview_on(item)

    @QtCore.Slot(NodeRepr)
    def _on_item_shifted(self, item: NodeRepr):
        """Save node position to server when it's moved."""

        if not isinstance(item, NodeRepr):

            return

        pos = item.scenePos()
        x = pos.x()
        y = pos.y()

        # Try: Update node position on server
        # Exceptions:
        # - KeyError: Raised if node path not found in Translator
        # - Exception: Any error during server communication
        try:
            from gui.compat import Translator

            translator = Translator.instance()
            node_path = translator._paths.get(id(item))

            if node_path:

                metadata = {"x": str(x), "y": str(y)}
                resp = self._client.send_command(
                    {"verb": "update", "path": node_path, "meta": metadata}
                )
                if resp and resp.get("status") in ("OK", 200):

                    self._logger.info(f"✓ Saved position for {node_path}: ({x}, {y})")
                else:

                    self._logger.warning(f"Failed to save position for {node_path}")

        except Exception as e:

            self._logger.error(f"Error saving node position: {e}", exc_info=True)

    @QtCore.Slot(str, str)
    def _on_notification_received(self, cuid: str, message: str) -> None:

        if self._uid != cuid:
            return

        self._logger.info(f"Received notification: {message}")
        QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Icon.Information,
            "Notification",
            message,
            QtWidgets.QMessageBox.StandardButton.Ok,
            parent=None,
        ).exec()

    @QtCore.Slot(dict)
    def _on_load_blueprint(self, blueprint: dict) -> None:

        """Load a blueprint into the canvas."""

        # Try: Parse blueprint and create nodes and edges
        # Exceptions:
        # - KeyError: Raised if blueprint structure is invalid
        # - ValueError: Raised if position coordinates cannot be converted to float
        # - TypeError: Raised if position data is invalid type
        try:
            nodes_by_id = {}

            # 1. Create nodes from blueprint
            nodes_dict = blueprint.get("nodes", {})
            for node_id, node_data in nodes_dict.items():

                meta = node_data.get("meta", {})

                try:

                    x = float(meta.get("x", None))
                    y = float(meta.get("y", None))
                    pos_source = "metadata"

                except (ValueError, TypeError):

                    self._logger.warning(
                        f"No position data for node {node_id}, skipping"
                    )
                    continue

                ui_config = meta.get("ui", {})
                node = NodeRepr(node_id, pos=QtCore.QPointF(x, y), ui_config=ui_config)
                self.addItem(node)
                nodes_by_id[node_id] = node
                self._logger.info(
                    f"Created node {node_id} at ({x}, {y}) from {pos_source}"
                )

            # 2. Create edges from blueprint links
            links_list = blueprint.get("links", [])
            edges_by_pair = {}

            for link_data in links_list:

                source_path = link_data.get("source", "")
                target_path = link_data.get("target", "")

                source_node_id = (
                    source_path.split("/")[0] if "/" in source_path else source_path
                )
                target_node_id = (
                    target_path.split("/")[0] if "/" in target_path else target_path
                )

                pair = (source_node_id, target_node_id)
                if pair in edges_by_pair:

                    continue

                source_node = nodes_by_id.get(source_node_id)
                target_node = nodes_by_id.get(target_node_id)

                if source_node and target_node:

                    edge = EdgeRepr(
                        uuid.uuid4().hex, origin=source_node, target=target_node
                    )
                    self.addItem(edge)
                    edges_by_pair[pair] = edge
                    self._logger.info(
                        f"Created edge: {source_node_id} → {target_node_id}"
                    )

                else:

                    self._logger.warning(
                        f"Could not find nodes for link: {source_node_id} → {target_node_id}"
                    )

        except Exception as e:

            self._logger.error(f"Error loading blueprint: {e}", exc_info=True)

    # Public methods
    # --------------

    def create_node_repr(
        self,
        cuid: str,
        nuid: str,
        jstr: str,
    ) -> NodeRepr | None:
        """Create a new node representation."""

        # Check if the canvas ID matches
        if self._uid != cuid:
            return None

        # Prepare data for item instantiation
        data = json.loads(jstr) or {}
        cpos = QtCore.QPointF(data.get("x", 0), data.get("y", 0))

        node = NodeRepr(nuid, pos=cpos)
        self.addItem(node)

        # Emit signal to register node with Translator
        bus = Relay.instance()
        bus.sig_item_created.emit(node)

        return node

    def create_edge_repr(
        self, cuid: str, euid: str, jstr: str = None
    ) -> EdgeRepr | None:
        """Create a new edge representation."""

        if self._uid != cuid:
            return None

        data = json.loads(jstr) or {}
        source_uid = data.get("source_uid")
        target_uid = data.get("target_uid")

        source = self.find_item_by_uid(source_uid)
        target = self.find_item_by_uid(target_uid)

        if not (source and target):
            return None

        edge = EdgeRepr(euid, origin=source, target=target)
        self.addItem(edge)

        # Emit signal for consistency (Translator ignores EdgeRepr)
        bus = Relay.instance()
        bus.sig_item_created.emit(edge)

        return edge

    def delete_node_repr(self, cuid: str, nuid: str) -> None:

        if self._uid != cuid:
            return

        item = self.find_item_by_uid(nuid)
        if item:
            self.removeItem(item)

    def delete_edge_repr(self, cuid: str, euid: str) -> None:
        """Delete an edge representation."""

        if self._uid != cuid:
            return

        item = self.find_item_by_uid(euid)
        if item:
            self.removeItem(item)

    def refresh_visual_state(self) -> None:
        """
        Fetch node/link states from the server and update NodeRepr/EdgeRepr colours.
        Call after connect_unit or any bulk state change.
        """
        from gui.compat import Translator
        from gui.compat import SysClient as ClimactClient

        unit_uuid = Translator.instance()._canvas_uuid.get(id(self))
        if not unit_uuid:
            return

        resp = ClimactClient.instance().send_command(
            {"verb": "info", "path": unit_uuid}
        )
        if not resp or resp.get("status") not in ("OK", 200):
            return

        data = resp.get("info", {})
        nodes_data = data.get("nodes", {})
        links_data = data.get("links", [])

        # Build set of (src_nuid, tgt_nuid) pairs that have at least one active link
        active_pairs: set[tuple[str, str]] = set()
        for link in links_data:
            if link.get("active"):
                src_nuid = link["source"].split("/")[0]
                tgt_nuid = link["target"].split("/")[0]
                active_pairs.add((src_nuid, tgt_nuid))

        for item in self.items():
            if isinstance(item, NodeRepr):
                item.set_enabled(nodes_data.get(item.uid, {}).get("enabled", True))
            elif isinstance(item, EdgeRepr):
                o = item._origin() if item._origin else None
                t = item._target() if item._target else None
                if o and t:
                    item.set_active((o.uid, t.uid) in active_pairs)

    def find_item_by_uid(self, uid: str) -> QtWidgets.QGraphicsItem | None:
        """Find an item in the canvas by its unique identifier."""

        return next(
            (
                item
                for item in self.items()
                if isinstance(item, (NodeRepr, EdgeRepr)) and item.uid == uid
            ),
            None,
        )

    def load_graph(self, guid: str) -> bool:
        """
        Load a graph from the server and initialize the client.

        Args:
            guid: The unique identifier for the graph (instance name)

        Returns:
            True if successful, False otherwise
        """
        self._graph_guid = guid

        self._logger.info(f"Loaded graph {guid}")

        # Register canvas with Translator via Relay (after _graph_guid is set)
        bus = Relay.instance()
        bus.sig_canvas_created.emit(self, guid)

        # Load existing nodes from the unit
        self._load_unit_nodes(guid)

        return True

    def _load_unit_nodes(self, guid: str) -> None:
        """Fetch unit data from server and create NodeRepr and EdgeRepr."""

        # Try: Query unit, create nodes and links, register with Translator
        # Exceptions:
        # - ValueError: Raised if position coordinates cannot be converted to float
        # - TypeError: Raised if metadata structure is invalid
        # - Exception: Any error during server communication or node creation
        try:

            # 1. Fetch full template data from server
            resp = self._client.send_command({"verb": "export", "path": guid})
            if not resp or resp.get("status") not in ("OK", 200):

                self._logger.warning(f"Failed to fetch unit data for {guid}")
                return

            unit_data = resp.get("serialized", {})
            nodes_dict = unit_data.get("nodes", {})
            links_list = unit_data.get("links", [])

            self._logger.info(
                f"Loading {len(nodes_dict)} nodes and {len(links_list)} links for unit {guid}"
            )

            # 2. Create NodeRepr for each node and register with Translator
            from gui.compat import Translator

            translator = Translator.instance()
            nodes_by_nuid = {}

            for idx, nuid in enumerate(nodes_dict.keys()):

                node_data = nodes_dict[nuid]
                meta = node_data.get("meta", {})

                try:

                    x = float(meta.get("x", None))
                    y = float(meta.get("y", None))
                    pos_source = "metadata"

                except (ValueError, TypeError):

                    col = idx % 5
                    row = idx // 5
                    x = col * 150
                    y = row * 150
                    pos_source = "grid"

                ui_config = meta.get("ui", {})
                node = NodeRepr(nuid, pos=QtCore.QPointF(x, y), ui_config=ui_config)

                is_enabled = node_data.get("enabled", True)
                node.enabled = is_enabled

                self.addItem(node)
                nodes_by_nuid[nuid] = node

                node_path = f"{guid}/{nuid}"
                translator._paths[id(node)] = node_path
                self._logger.info(
                    f"Created NodeRepr for {nuid} at ({x}, {y}) from {pos_source} (enabled: {is_enabled}) — registered with Translator"
                )

            # 3. Create EdgeRepr for each link
            for link_data in links_list:

                source_path = link_data.get("source", "")
                target_path = link_data.get("target", "")

                source_nuid = (
                    source_path.split("/")[0] if "/" in source_path else source_path
                )
                target_nuid = (
                    target_path.split("/")[0] if "/" in target_path else target_path
                )

                source_node = nodes_by_nuid.get(source_nuid)
                target_node = nodes_by_nuid.get(target_nuid)

                if source_node and target_node:

                    edge = EdgeRepr(
                        uuid.uuid4().hex, origin=source_node, target=target_node
                    )
                    self.addItem(edge)
                    self._logger.info(
                        f"Created EdgeRepr: {source_nuid} → {target_nuid}"
                    )

                else:

                    self._logger.warning(
                        f"Could not find nodes for link: {source_nuid} → {target_nuid}"
                    )

        except Exception as e:

            self._logger.error(f"Error loading unit nodes: {e}", exc_info=True)

    def export_graph(self) -> dict:
        """
        Export the current graph as a dict representation suitable for optimization.

        Returns
        -------
        dict : {
            "unit_guid": str (the unit identifier),
            "nodes": [
                {
                    "uid": str,
                    "label": str,
                    "x": float,
                    "y": float,
                },
                ...
            ],
            "edges": [
                {
                    "uid": str,
                    "source_uid": str,
                    "target_uid": str,
                },
                ...
            ],
        }
        """
        nodes = []
        edges = []

        # Collect all nodes
        for item in self.items():
            if isinstance(item, NodeRepr):
                pos = item.scenePos()
                nodes.append(
                    {
                        "uid": item.uid,
                        "label": item._uid,  # Node's display name
                        "x": pos.x(),
                        "y": pos.y(),
                    }
                )

        # Collect all edges
        for item in self.items():
            if isinstance(item, EdgeRepr):
                source = item._origin() if item._origin else None
                target = item._target() if item._target else None

                if source and target:
                    edges.append(
                        {
                            "uid": item.uid,
                            "source_uid": source.uid,
                            "target_uid": target.uid,
                        }
                    )

        return {
            "unit_guid": self._graph_guid,
            "nodes": nodes,
            "edges": edges,
        }

    @property
    def uid(self) -> str:
        return self._uid
