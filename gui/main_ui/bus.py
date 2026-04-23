# Module Name: gui.main_ui
# Description: Signal manager for main_ui operations with SysClient integration

import logging
from typing import Optional, Dict, Any, List

from PySide6 import QtCore

logger = logging.getLogger(__name__)


class MainGuiRelay(QtCore.QObject):
    """
    Signal manager for the `MainGui` instance. Owns SysClient and handles client communication.
    """

    # Signals
    sig_project_load_success = QtCore.Signal(list)  # Emits list of template names
    sig_project_load_failure = QtCore.Signal(str)  # Emits error message

    # Singleton instance
    _instance = None

    def __init__(self):

        # Initialize base-class (QObject)
        super().__init__()

        # Initialize SysClient
        self._sys_client = None

    @classmethod
    def instance(cls) -> "MainGuiRelay":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def set_client(self, client):
        """Set the SysClient instance."""
        self._sys_client = client

    @QtCore.Slot()
    def fetch_templates(self) -> None:
        """Fetch the templates from the server and emit the signal."""

        if not self._sys_client:
            logger.error("SysClient not initialized")
            self.sig_project_load_failure.emit("Client not available")
            return

        try:
            response = self._sys_client.send_command({"verb": "info", "path": ""})

            if response and response.get("status") in ("OK", 200):
                templates = response.get("serialized", [])
                # Filter out reserved templates (those starting with __)
                templates = [t for t in templates if not t.startswith("__")]
                logger.info(f"Loaded {len(templates)} templates")
                self.sig_project_load_success.emit(templates)
            else:
                error_msg = (
                    response.get("info", "Unknown error") if response else "No response"
                )
                logger.warning(f"Failed to load templates: {error_msg}")
                self.sig_project_load_failure.emit(error_msg)

        except Exception as e:
            logger.error(f"Error fetching templates: {e}")
            self.sig_project_load_failure.emit(str(e))
