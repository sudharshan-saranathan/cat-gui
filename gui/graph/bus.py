# Module Name: gui.graph.bus
# Description: Signal manager for graph operations with SysClient integration

import logging
from typing import Dict, Any

from PySide6 import QtCore

logger = logging.getLogger(__name__)


class GraphRelay(QtCore.QObject):
    """Signal manager for graph module. Owns SysClient and handles client communication."""

    # Signals for graph operations
    sig_node_config_updated = QtCore.Signal(dict)  # Emits updated node data
    sig_edge_config_updated = QtCore.Signal(dict)  # Emits updated edge data
    sig_blueprint_loaded = QtCore.Signal(dict)  # Emits blueprint data
    sig_operation_failed = QtCore.Signal(str)  # Emits error message

    _instance = None

    def __init__(self):
        super().__init__()
        self._sys_client = None

    @classmethod
    def instance(cls) -> "GraphRelay":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def set_client(self, client):
        """Set the SysClient instance."""
        self._sys_client = client

    @QtCore.Slot(str, dict)
    def update_node_config(self, node_path: str, config: dict) -> None:
        """Update node configuration on server."""
        if not self._sys_client:
            logger.error("SysClient not initialized")
            self.sig_operation_failed.emit("Client not available")
            return

        try:
            response = self._sys_client.send_command(
                {"verb": "update", "path": node_path, "meta": config}
            )

            if response and response.get("status") == "OK":
                logger.info(f"Updated node config: {node_path}")
                self.sig_node_config_updated.emit(config)
            else:
                error_msg = (
                    response.get("contents", "Unknown error")
                    if response
                    else "No response"
                )
                logger.warning(f"Failed to update node: {error_msg}")
                self.sig_operation_failed.emit(error_msg)

        except Exception as e:
            logger.error(f"Error updating node config: {e}")
            self.sig_operation_failed.emit(str(e))

    @QtCore.Slot(str, dict)
    def update_edge_config(self, edge_path: str, config: dict) -> None:
        """Update edge configuration on server."""
        if not self._sys_client:
            logger.error("SysClient not initialized")
            self.sig_operation_failed.emit("Client not available")
            return

        try:
            response = self._sys_client.send_command(
                {"verb": "update", "path": edge_path, "meta": config}
            )

            if response and response.get("status") == "OK":
                logger.info(f"Updated edge config: {edge_path}")
                self.sig_edge_config_updated.emit(config)
            else:
                error_msg = (
                    response.get("contents", "Unknown error")
                    if response
                    else "No response"
                )
                logger.warning(f"Failed to update edge: {error_msg}")
                self.sig_operation_failed.emit(error_msg)

        except Exception as e:
            logger.error(f"Error updating edge config: {e}")
            self.sig_operation_failed.emit(str(e))
