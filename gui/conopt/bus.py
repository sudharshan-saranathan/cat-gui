# Module Name: gui.conopt.bus
# Description: Signal manager for optimization operations with SysClient integration

import logging
from typing import Dict, Any

from PySide6 import QtCore

logger = logging.getLogger(__name__)


class ConOptRelay(QtCore.QObject):
    """Signal manager for conopt module. Owns SysClient and handles client communication."""

    # Signals for optimization operations
    sig_optimization_started = QtCore.Signal()
    sig_optimization_completed = QtCore.Signal(dict)  # Emits results
    sig_optimization_failed = QtCore.Signal(str)  # Emits error message

    _instance = None

    def __init__(self):
        super().__init__()
        self._sys_client = None

    @classmethod
    def instance(cls) -> "ConOptRelay":
        """Get or create singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def set_client(self, client):
        """Set the SysClient instance."""
        self._sys_client = client

    @QtCore.Slot(str, dict)
    def run_optimization(self, template_path: str, parameters: dict) -> None:
        """Run optimization on the specified template with given parameters."""
        if not self._sys_client:
            logger.error("SysClient not initialized")
            self.sig_optimization_failed.emit("Client not available")
            return

        try:
            self.sig_optimization_started.emit()
            logger.info(f"Running optimization on: {template_path}")

            # Placeholder for actual optimization call
            # This would call the appropriate optimization endpoint
            self.sig_optimization_completed.emit({})

        except Exception as e:
            logger.error(f"Error running optimization: {e}")
            self.sig_optimization_failed.emit(str(e))
