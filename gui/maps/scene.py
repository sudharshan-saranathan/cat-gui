# Module Name: gui.maps.scene
# Description: QGraphicsScene for the India map — renders GeoJSON polygons and template markers

from __future__ import annotations

import json
import logging

import geopandas
from PySide6 import QtCore, QtWidgets

from gui.maps.relay import MapsRelay
from gui.maps.borders import Borders
from gui.maps.markers import Marker

logger = logging.getLogger(__name__)


class MapsScene(QtWidgets.QGraphicsScene):
    """
    Renders the India state map from a static Qt resource and overlays
    plant markers fetched via the /maps/templates REST endpoint.

    Concerns handled here:
    - GeoJSON loading from Qt resource (no HDF5, no backend)
    - Template marker placement via Overlay (REST data passed in from viewer)
    - Coordinate conversion between (lon, lat) and scene (x, y)
    """

    GEO_ZOOM = 250.0

    def __init__(self, api_client=None, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)
        self._api = api_client

        self._minx: float = 0.0
        self._miny: float = 0.0
        self._maxx: float = 1.0
        self._maxy: float = 1.0

        # Marker overlay layer (sits on top of state polygons)
        self._overlay = Marker()
        self._overlay.setPos(0, 0)
        self.addItem(self._overlay)

        self._render_geojson()
        self._init_menu()

        # Subscribe to plants loaded signal
        bus = MapsRelay.instance()
        bus.sig_plants_loaded.connect(self._fetch_and_populate_markers)
        bus.sig_focus_template.connect(self._on_focus_template)

    # ------------------------------------------------------------------
    # Context menu
    # ------------------------------------------------------------------

    def _init_menu(self) -> None:
        self._menu = QtWidgets.QMenu()
        load_action = self._menu.addAction("Load Plants Data")
        load_action.triggered.connect(self._on_load_plants)

    def contextMenuEvent(self, event: QtWidgets.QGraphicsSceneContextMenuEvent) -> None:
        self._menu.exec(event.screenPos())

    def _on_load_plants(self) -> None:
        """File dialog → load CSV/Excel into MapCtrl via REST."""
        from PySide6 import QtWidgets

        if not self._api or not self._api.user_id:
            logger.warning("No API client available for loading plants")
            return

        dialog = QtWidgets.QFileDialog()
        dialog.setFileMode(QtWidgets.QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilters(
            [
                "Excel Files (*.xlsx *.xls)",
                "CSV Files (*.csv)",
                "All Files (*)",
            ]
        )

        if not dialog.exec():
            return

        file_path = dialog.selectedFiles()[0]
        logger.info(f"Loading plants from {file_path}")

        try:
            resp = self._api.session.post(
                f"{self._api.base_URL}/maps/load",
                json={"file": file_path},
                headers={"X-Client-ID": self._api.user_id},
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") == "OK":
                logger.info(f"✓ Loaded plants data: {data.get('info')}")
                # Fetch and populate markers
                self._fetch_and_populate_markers()
            else:
                logger.warning(f"Failed to load plants: {data.get('info')}")
        except Exception as e:
            logger.error(f"Error loading plants: {e}")

    def _fetch_and_populate_markers(self) -> None:
        """Fetch templates from /maps/templates and populate markers."""
        if not self._api or not self._api.user_id:
            return

        try:
            resp = self._api.session.get(
                f"{self._api.base_URL}/maps/templates",
                headers={"X-Client-ID": self._api.user_id},
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()
            templates = data.get("templates", [])
            self.populate_markers(templates)
        except Exception as e:
            logger.error(f"Error fetching templates: {e}")

    @QtCore.Slot(str)
    def _on_focus_template(self, template_uid: str) -> None:
        if not self._overlay.focus_template(template_uid):
            logger.warning(f"Could not focus marker for template {template_uid!r}")

    # ------------------------------------------------------------------
    # Coordinate conversion
    # ------------------------------------------------------------------

    def geo_to_scene(self, lon: float, lat: float) -> QtCore.QPointF:
        x = (lon - self._minx) * self.GEO_ZOOM
        y = (self._maxy - lat) * self.GEO_ZOOM
        return QtCore.QPointF(x, y)

    def scene_to_geo(self, pos: QtCore.QPointF) -> tuple[float, float]:
        lon = (pos.x() / self.GEO_ZOOM) + self._minx
        lat = self._maxy - (pos.y() / self.GEO_ZOOM)
        return lon, lat

    # ------------------------------------------------------------------
    # GeoJSON rendering
    # ------------------------------------------------------------------

    def _render_geojson(self) -> None:

        file = QtCore.QFile(":/maps/india-state.geojson")
        if not file.open(
            QtCore.QFile.OpenModeFlag.ReadOnly | QtCore.QFile.OpenModeFlag.Text
        ):
            logger.error("Cannot open :/maps/india-state.geojson — resource missing")
            return

        raw = file.readAll().data().decode("utf-8")
        obj = json.loads(raw)
        geo = geopandas.GeoDataFrame.from_features(obj.get("features", []))

        bounds = geo.total_bounds  # [minx, miny, maxx, maxy]
        self._minx, self._miny, self._maxx, self._maxy = bounds

        width = (self._maxx - self._minx) * self.GEO_ZOOM
        height = (self._maxy - self._miny) * self.GEO_ZOOM
        self.setSceneRect(QtCore.QRectF(0, 0, width, height))

        for _, row in geo.iterrows():
            geom = getattr(row, "geometry", None)
            if geom is None:
                continue

            state = str(row["NAME_1"]) if "NAME_1" in row.index else ""
            gtype = getattr(geom, "geom_type", "")

            polygons = (
                [geom]
                if gtype == "Polygon"
                else (
                    [p for p in getattr(geom, "geoms", []) if p.geom_type == "Polygon"]
                    if gtype == "MultiPolygon"
                    else []
                )
            )

            for poly in polygons:
                outline = Borders(poly, self._minx, self._maxy, self.GEO_ZOOM, state)
                self.addItem(outline)

        MapsRelay.instance().sig_map_rendered.emit()
        logger.info(
            f"Map rendered: {len(geo)} features, scene {width:.0f}×{height:.0f}"
        )

    # ------------------------------------------------------------------
    # Template markers
    # ------------------------------------------------------------------

    def populate_markers(self, templates: list[dict]) -> None:
        """
        Place markers from template records fetched from the server.

        Each record must have: lat, lon, template_uid, plant_name, capacity, color.
        """
        self._overlay.clear_markers()

        for record in templates:
            try:
                lat = float(record["lat"])
                lon = float(record["lon"])
                pos = self.geo_to_scene(lon, lat)
                self._overlay.add_marker(
                    int(pos.x()),
                    int(pos.y()),
                    template_uid=record.get("template_uid", ""),
                    plant_name=record.get("plant_name", ""),
                    capacity=float(record.get("capacity", 0.0)),
                    color=record.get("color", "#FF4444"),
                )
            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping bad template record {record}: {e}")

        logger.info(f"Populated {len(templates)} template markers")
