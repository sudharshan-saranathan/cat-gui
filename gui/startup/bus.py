# Module Name: gui.startup.bus
# Description: Signal manager for startup operations with APIClient integration

import logging
from typing import Optional

from PySide6 import QtCore

logger = logging.getLogger(__name__)


class StartupRelay(QtCore.QObject):
    """Signal manager for startup module. Owns APIClient and handles client communication."""

    # Signals for startup operations
    sig_login_success = QtCore.Signal(str)  # Emits user_id
    sig_login_failed = QtCore.Signal(str)  # Emits error message
    sig_projects_loaded = QtCore.Signal(list)  # Emits list of projects
    sig_projects_load_failed = QtCore.Signal(str)  # Emits error message

    _instance = None

    def __init__(self):
        super().__init__()
        self._api_client = None

    @classmethod
    def instance(cls) -> "StartupRelay":
        """Get or create singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def set_client(self, client):
        """Set the APIClient instance."""
        self._api_client = client

    @QtCore.Slot(str)
    def login(self, user_id: str) -> None:
        """Attempt to login user."""
        if not self._api_client:
            logger.error("APIClient not initialized")
            self.sig_login_failed.emit("Client not available")
            return

        try:
            success = self._api_client.login(user_id)
            if success:
                logger.info(f"Login successful: {user_id}")
                self.sig_login_success.emit(user_id)
            else:
                logger.warning(f"Login failed for user: {user_id}")
                self.sig_login_failed.emit("Login failed")

        except Exception as e:
            logger.error(f"Error during login: {e}")
            self.sig_login_failed.emit(str(e))

    @QtCore.Slot(str)
    def fetch_projects(self, user_id: str) -> None:
        """Fetch projects for the given user."""
        if not self._api_client:
            logger.error("APIClient not initialized")
            self.sig_projects_load_failed.emit("Client not available")
            return

        try:
            # This would call an API endpoint to get projects
            # For now, placeholder implementation
            logger.info(f"Fetching projects for user: {user_id}")
            self.sig_projects_loaded.emit([])

        except Exception as e:
            logger.error(f"Error fetching projects: {e}")
            self.sig_projects_load_failed.emit(str(e))
