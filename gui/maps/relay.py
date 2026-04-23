# Module Name: gui.maps.bus
# Description: MapsRelay — isolated signal bus for the maps sub-module

from __future__ import annotations

import logging

from PySide6 import QtCore

logger = logging.getLogger(__name__)


class MapsRelay(QtCore.QObject):
    """
    Singleton signal hub for maps-specific events.

    Keeps map signals isolated from the global Relay so other sub-modules
    are not affected by maps lifecycle events.
    """

    _instance: MapsRelay | None = None

    # Emitted once the GeoJSON scene has been rendered
    sig_map_rendered = QtCore.Signal()

    # Emitted when plants are loaded from HDF5 project
    sig_plants_loaded = QtCore.Signal()

    # Emitted when the server returns a list of template records
    sig_templates_received = QtCore.Signal(list)  # list[dict]

    # Emitted when the user clicks a state polygon (state_name)
    sig_state_clicked = QtCore.Signal(str)

    # Emitted to open a template canvas in a new tab (template_uid, label)
    sig_open_template = QtCore.Signal(str, str)

    # Emitted to focus an existing template marker on the map
    sig_focus_template = QtCore.Signal(str)

    def __init__(self) -> None:
        super().__init__()

    @classmethod
    def instance(cls) -> MapsRelay:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
