# Module Name: gui.compat
# Description: Compatibility shim adapting CAT's TCP ClimactClient/Translator to iitm-climact's REST API

from __future__ import annotations

import json
import logging
import uuid
from typing import Optional, Any, Dict, TYPE_CHECKING

from PySide6 import QtCore, QtWidgets

from gui.api_client import APIClient
from gui.bus import Relay

if TYPE_CHECKING:
    from gui.graph.node import NodeRepr

logger = logging.getLogger(__name__)


class SysClient:
    """
    REST-based system client. Wraps APIClient and provides a .send() method
    compatible with CAT's ClimactClient.send_command(verb, path, data) interface.
    Converts REST calls to /sys/* endpoints.

    Requires X-Client-ID header (user_id) for server session validation.
    """

    _instance = None

    def __init__(self, api_client: Optional[APIClient] = None):
        """Initialize with an optional APIClient instance."""
        self._api = api_client or APIClient()
        self._logger = logging.getLogger(__name__)
        self._user_id = self._api.user_id  # Will be set by register_user()

    @classmethod
    def instance(cls) -> SysClient:
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def send_command(self, command: dict) -> Optional[Dict[str, Any]]:
        """
        Send a command dictionary to the server
        """

        # Already JSON format
        return self.send(
            command.get("verb", ""),
            command.get("path", ""),
            command.get("meta") or command,
        )

    def send(
        self,
        verb: str,
        path: str,
        data: dict[str, Any] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Send a system command via REST API.

        Args:
                verb: sysctrl verb (create, get, update, delete, info, link, etc.)
                path: System path (e.g., "unit/my-unit/node/my-node")
                data: Optional payload dict

        Returns:
                Response dict or None on error
        """
        try:
            verb = verb.lower()
            if verb == "create":

                # RequestModel expects: verb, path, meta (dict)
                meta = data or {}
                return self._api_post(
                    "/sys/",
                    {
                        "verb": "create",
                        "path": path,
                        "meta": meta,
                    },
                )
            elif verb == "get":
                return self._api_get(f"/sys/?path={path}")
            elif verb == "update":
                # RequestModel expects: verb, path, meta (dict)
                return self._api_patch(
                    "/sys/",
                    {
                        "verb": "update",
                        "path": path,
                        "meta": data or {},
                    },
                )
            elif verb == "delete":
                return self._api_delete(f"/sys/?path={path}")
            elif verb == "info":
                return self._api_get(f"/sys/info?path={path}")
            elif verb == "export":
                return self._api_get(f"/sys/export?path={path}")
            elif verb == "link":
                return self._api_post("/sys/link", data or {})
            elif verb == "snap":
                return self._api_post("/sys/snap", data or {})
            elif verb == "clone":
                return self._api_post("/sys/clone", data or {})
            elif verb == "instantiate":
                return self._api_post(
                    "/sys/instantiate",
                    {"verb": "instantiate", "path": path, "meta": data or {}},
                )
            elif verb == "load":
                return self._api_post(
                    "/sys/",
                    {
                        "verb": "load",
                        "path": path,
                        "meta": data or {},
                    },
                )
            else:
                self._logger.warning(f"Unknown verb: {verb}")
                return {"status": 400, "info": f"Unknown verb: {verb}"}
        except Exception as e:
            self._logger.error(f"SysClient.send({verb}, {path}) failed: {e}")
            return {"status": 500, "info": str(e)}

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests (include X-Client-ID for session validation)."""
        headers = {}
        user_id = self._api.user_id or self._user_id
        if user_id:
            headers["X-Client-ID"] = user_id
        return headers

    def _api_get(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Make a GET request to the API."""
        try:
            response = self._api.session.get(
                f"{self._api.base_URL}{endpoint}", headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self._logger.error(f"GET {endpoint} failed: {e}")
            return {"status": 500, "info": str(e)}

    def _api_post(
        self, endpoint: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Make a POST request to the API."""
        try:
            response = self._api.session.post(
                f"{self._api.base_URL}{endpoint}",
                json=data,
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self._logger.error(f"POST {endpoint} failed: {e}")
            return {"status": 500, "info": str(e)}

    def _api_patch(
        self, endpoint: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Make a PATCH request to the API."""
        try:
            response = self._api.session.patch(
                f"{self._api.base_URL}{endpoint}",
                json=data,
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self._logger.error(f"PATCH {endpoint} failed: {e}")
            return {"status": 500, "info": str(e)}

    def _api_delete(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Make a DELETE request to the API."""
        try:
            response = self._api.session.delete(
                f"{self._api.base_URL}{endpoint}", headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self._logger.error(f"DELETE {endpoint} failed: {e}")
            return {"status": 500, "info": str(e)}


class DatClient:
    """
    REST client for the /data endpoints. Shares SysClient's APIClient so the
    X-Client-ID header is always correct.
    """

    def read(self, path: str) -> dict:
        """Fetch a single parameter entry. Returns {} on miss or error."""
        api = SysClient.instance()._api
        try:
            uid = api.user_id
            resp = api.session.get(
                f"{api.base_URL}/data/read",
                params={"path": path},
                headers={"X-Client-ID": uid} if uid else {},
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logging.getLogger(__name__).warning(f"DatClient.read({path!r}) failed: {e}")
        return {}

    def write(self, path: str, value: str, units: str = "", f_t: str = "") -> bool:
        """Write a parameter to the datastore. Returns True on success."""
        api = SysClient.instance()._api
        try:
            uid = api.user_id
            payload = {"initial": value, "f_t": f_t or value, "units": units, "binary": 0}
            resp = api.session.post(
                f"{api.base_URL}/data/write",
                params={"path": path},
                json=payload,
                headers={"X-Client-ID": uid} if uid else {},
            )
            return resp.status_code == 200
        except Exception as e:
            logging.getLogger(__name__).warning(f"DatClient.write({path!r}) failed: {e}")
        return False

    def update(self, path: str, value: str, units: str = "", f_t: str = "") -> bool:
        """Update a parameter in the datastore. Returns True on success."""
        api = SysClient.instance()._api
        try:
            uid = api.user_id
            payload = {"initial": value, "f_t": f_t or value, "units": units, "binary": 0}
            resp = api.session.post(
                f"{api.base_URL}/data/update",
                params={"path": path},
                json=payload,
                headers={"X-Client-ID": uid} if uid else {},
            )
            return resp.status_code == 200
        except Exception as e:
            logging.getLogger(__name__).warning(f"DatClient.update({path!r}) failed: {e}")
        return False

    def upsert(self, path: str, value: str, units: str = "", f_t: str = "") -> bool:
        """Update a parameter if it exists, otherwise create it."""
        existing = self.read(path)
        if existing:
            return self.update(path, value, units=units, f_t=f_t)
        return self.write(path, value, units=units, f_t=f_t)

    @classmethod
    def instance(cls) -> "DatClient":
        # Lightweight — no state, so a fresh instance is fine.
        return cls()


class Translator(QtCore.QObject):
    """
    REST-based event translator. Subscribes to Relay signals and converts them
    into /sys/* REST API calls via SysClient. Replaces CAT's TCP-based Translator.

    Path Registry
    -------------
    _paths        : id(item)          → server path string (e.g., "unit/my-unit/node/nuid")
    _canvas_uuid  : id(canvas)        → unit identifier from canvas._graph_guid
    """

    _instance: Optional["Translator"] = None

    @classmethod
    def instance(cls) -> "Translator":
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        super().__init__()
        self._paths: Dict[int, str] = {}
        self._canvas_uuid: Dict[int, str] = {}
        self._sys_client = SysClient.instance()
        self._logger = logging.getLogger(__name__)
        self._subscribe()
        self._logger.debug("Translator: initialized")

    def _subscribe(self):
        """Subscribe to Relay signals."""
        bus = Relay.instance()
        bus.sig_canvas_created.connect(self._on_canvas_created)
        bus.sig_item_created.connect(self._on_item_created)
        bus.sig_item_deleted.connect(self._on_item_deleted)
        bus.sig_item_updated.connect(self._on_item_updated)

    @QtCore.Slot(QtWidgets.QGraphicsScene, str)
    def _on_canvas_created(self, canvas: QtWidgets.QGraphicsScene, label: str):
        """Register a new canvas with its unit UUID."""
        unit_uuid = getattr(canvas, "_graph_guid", None)
        if not unit_uuid:
            unit_uuid = str(uuid.uuid4())
            self._logger.warning(f"Canvas has no _graph_guid, using UUID: {unit_uuid}")

        self._canvas_uuid[id(canvas)] = unit_uuid
        self._paths[id(canvas)] = unit_uuid
        self._logger.info(f"✓ Registered canvas with unit: {unit_uuid} ({label})")

    @QtCore.Slot(QtWidgets.QGraphicsObject)
    def _on_item_created(self, item: QtWidgets.QGraphicsObject):
        """Handle item creation (nodes only; edges are visual)."""
        from gui.graph.node import NodeRepr

        if type(item).__name__ == "NodeRepr":
            self._create_node(item)

    @QtCore.Slot(QtWidgets.QGraphicsObject)
    def _on_item_deleted(self, item: QtWidgets.QGraphicsObject):
        """Handle item deletion."""
        from gui.graph.node import NodeRepr

        if type(item).__name__ == "NodeRepr":
            self._delete_node(item)
        self._paths.pop(id(item), None)

    @QtCore.Slot(QtWidgets.QGraphicsObject)
    def _on_item_updated(self, item: QtWidgets.QGraphicsObject):
        """Handle item updates (label renames)."""
        from gui.graph.node import NodeRepr

        if type(item).__name__ != "NodeRepr":
            return

        path = self._paths.get(id(item))
        if not path:
            return

        label = getattr(item, "_uid", "Unknown")
        resp = self._sys_client.send("update", path, {"label": label})
        if resp and resp.get("status") == 200:
            self._logger.info(f"⟳ Updated node: {path} → {label}")
        else:
            self._logger.error(f"✗ Failed to update {path}: {resp}")

    def _create_node(self, node: "NodeRepr"):
        """Create a node on the server."""
        canvas = node.scene()
        unit_uuid = self._canvas_uuid.get(id(canvas))
        if not unit_uuid:
            self._logger.warning("Translator: NodeRepr on unregistered canvas")
            return

        nuid = getattr(node, "_uid", f"node-{uuid.uuid4().hex[:8]}")
        node_path = f"{unit_uuid}/{nuid}"
        self._paths[id(node)] = node_path

        pos = node.scenePos()
        metadata = {"label": nuid, "x": str(pos.x()), "y": str(pos.y())}

        resp = self._sys_client.send("create", node_path, metadata, "node")
        if resp and resp.get("status") in (200, 201):
            self._logger.info(f"✓ Created node: {node_path}")
        else:
            self._logger.error(f"✗ Failed to create node {node_path}")

    def _delete_node(self, node: "NodeRepr"):
        """Delete a node from the server."""
        path = self._paths.get(id(node))
        if not path:
            return

        resp = self._sys_client.send("delete", path)
        if resp and resp.get("status") == 200:
            self._logger.info(f"✗ Deleted node: {path}")
        else:
            self._logger.error(f"✗ Failed to delete {path}")

    def commit_tech(
        self, node: "NodeRepr", tech_name: str, streams: Dict[str, str]
    ) -> bool:
        """
        Commit technology and streams to server.
        Called by NodeConfigWidget on confirm.

        streams: { "+name": "TypeName", "-name": "TypeName", ... }
        """
        node_path = self._paths.get(id(node))
        if not node_path:
            self._logger.warning("Translator.commit_tech: node not registered")
            return False

        tech_path = f"{node_path}/{tech_name}"
        resp = self._sys_client.send("create", tech_path, {}, "tech")
        if not resp or resp.get("status") not in (200, 201):
            self._logger.error(f"✗ Failed to create tech {tech_path}")
            return False

        self._logger.info(f"✓ Created tech: {tech_path}")

        for stream_key, type_name in streams.items():
            stream_path = f"{tech_path}/{stream_key}"
            resp = self._sys_client.send(
                "create", stream_path, {"type": type_name}, "stream"
            )
            if resp and resp.get("status") in (200, 201):
                self._logger.info(f"✓ Created stream: {stream_path} ({type_name})")
            else:
                self._logger.error(f"✗ Failed to create stream {stream_path}")

        return True

    def commit_links(self, mappings: list[tuple[str, str]]) -> None:
        """
        Commit link mappings to server.
        Called by EdgeConfigWidget on confirm.

        mappings: [(src_stream_path, tgt_stream_path), ...]
        """
        for src, tgt in mappings:
            payload = {"source": src, "target": tgt}
            resp = self._sys_client.send("link", "", payload)
            if resp and resp.get("status") in (200, 201):
                self._logger.info(f"✓ Created link: {src} → {tgt}")
            else:
                self._logger.error(f"✗ Failed to create link: {src} → {tgt}")


# Stub quantity classes for gui/graph/node/tree.py to import
# These are minimal implementations to allow tree rendering without core.numeric
class Quantity:
    """Base class for physical quantities."""

    def __init__(self, name: str, role: str = "", icon: str = ""):
        self.name = name
        self.role = role
        self.icon = icon

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name})"


class Composite(Quantity):
    """Composite stream type."""

    pass


class Fuel(Quantity):
    """Fuel stream type."""

    def __init__(self, name: str = "Fuel", role: str = "", icon: str = "mdi.fuel"):
        super().__init__(name, role, icon)


class Fluid(Quantity):
    """Fluid stream type."""

    def __init__(self, name: str = "Fluid", role: str = "", icon: str = "mdi.water"):
        super().__init__(name, role, icon)


class Material(Quantity):
    """Material stream type."""

    def __init__(
        self, name: str = "Material", role: str = "", icon: str = "mdi.package"
    ):
        super().__init__(name, role, icon)


class Electricity(Quantity):
    """Electricity stream type."""

    def __init__(
        self,
        name: str = "Electricity",
        role: str = "",
        icon: str = "mdi.lightning-bolt",
    ):
        super().__init__(name, role, icon)


class MassCurrent(Quantity):
    """Mass flow-rate stream type (t/hr, kg/s, etc.)."""

    def __init__(
        self,
        name: str = "MassCurrent",
        role: str = "",
        icon: str = "mdi.arrow-right-circle",
    ):
        super().__init__(name, role, icon)


class Energy(Quantity):
    """Thermal/process energy stream type (GJ, kWh, etc.)."""

    def __init__(
        self,
        name: str = "Energy",
        role: str = "",
        icon: str = "mdi.fire",
    ):
        super().__init__(name, role, icon)


class Cost(Quantity):
    """Levelized cost stream type (INR/t, USD/t, etc.)."""

    def __init__(
        self,
        name: str = "Cost",
        role: str = "",
        icon: str = "mdi.currency-inr",
    ):
        super().__init__(name, role, icon)


# Class registry for type name → class lookup
CLASS_REGISTRY = {
    "Composite":   Composite,
    "Fuel":        Fuel,
    "Fluid":       Fluid,
    "Material":    Material,
    "Electricity": Electricity,
    "MassCurrent": MassCurrent,
    "Energy":      Energy,
    "Cost":        Cost,
}


class OptClient:
    """
    REST-based optimization client. Wraps APIClient and provides optimization
    operations via /opt/* endpoints.

    Requires X-Client-ID header (user_id) for server session validation.
    """

    _instance = None

    def __init__(self, api_client: Optional[APIClient] = None):
        """Initialize with an optional APIClient instance."""

        self._api = api_client or APIClient()
        self._logger = logging.getLogger(__name__)
        self._user_id = self._api.user_id

    @classmethod
    def instance(cls) -> OptClient:
        """Get or create the singleton instance, sharing SysClient's authenticated API."""

        if cls._instance is None:
            sys = SysClient.instance()
            cls._instance = cls(sys._api if sys else None)
        return cls._instance

    def solve(
        self,
        scenario_name: str = "run",
        objective: str = "minimize cost",
        solver: str = "highs",
        alpha: float = 0.5,
        ramp_up: int = 3,
        ramp_down: int = 2,
        ramp_ccus: int = 2,
        min_plant_lifetime: int = 20,
        inflation_rate: float = None,
        emissions_factor: float = None,
        enable_inflation: bool = True,
        enable_payback: bool = True,
        enable_ramp: bool = True,
        enable_emissions_cap: bool = True,
        h2dri_learning_rate: float = 0.028,
        ccus_learning_rate: float = 0.014,
    ) -> Optional[Dict[str, Any]]:

        try:
            payload = {
                "path": "",
                "scenario_name": scenario_name,
                "objective": objective,
                "solver": solver,
                "alpha": alpha,
                "ramp_up": ramp_up,
                "ramp_down": ramp_down,
                "ramp_ccus": ramp_ccus,
                "min_plant_lifetime": min_plant_lifetime,
                "enable_inflation": enable_inflation,
                "enable_payback": enable_payback,
                "enable_ramp": enable_ramp,
                "enable_emissions_cap": enable_emissions_cap,
                "h2dri_learning_rate": h2dri_learning_rate,
                "ccus_learning_rate": ccus_learning_rate,
            }
            if inflation_rate is not None:
                payload["inflation_rate"] = inflation_rate
            if emissions_factor is not None:
                payload["emissions_factor"] = emissions_factor
            return self._api_post("/opt/solve", payload)

        except Exception as e:
            self._logger.error(f"Optimization request failed: {e}")
            return None

    def pareto(
        self,
        solver: str = "highs",
        n_points: int = 31,
        ramp_up: int = 3,
        ramp_down: int = 2,
        ramp_ccus: int = 2,
        min_plant_lifetime: int = 20,
        inflation_rate: float = None,
        emissions_factor: float = None,
        enable_inflation: bool = True,
        enable_payback: bool = True,
        enable_ramp: bool = True,
        enable_emissions_cap: bool = True,
        relax_integers: bool = False,
        h2dri_learning_rate: float = 0.028,
        ccus_learning_rate: float = 0.014,
    ) -> Optional[Dict[str, Any]]:

        try:
            payload = {
                "solver": solver,
                "n_points": n_points,
                "ramp_up": ramp_up,
                "ramp_down": ramp_down,
                "ramp_ccus": ramp_ccus,
                "min_plant_lifetime": min_plant_lifetime,
                "enable_inflation": enable_inflation,
                "enable_payback": enable_payback,
                "enable_ramp": enable_ramp,
                "enable_emissions_cap": enable_emissions_cap,
                "relax_integers": relax_integers,
                "h2dri_learning_rate": h2dri_learning_rate,
                "ccus_learning_rate": ccus_learning_rate,
            }
            if inflation_rate is not None:
                payload["inflation_rate"] = inflation_rate
            if emissions_factor is not None:
                payload["emissions_factor"] = emissions_factor
            return self._api_post("/opt/pareto", payload, timeout=900.0)

        except Exception as e:
            self._logger.error(f"Pareto request failed: {e}")
            return None

    def _api_post(self, endpoint: str, payload: dict, timeout: float = 30.0) -> Optional[Dict[str, Any]]:
        """Send a POST request to the API."""

        try:
            url = f"{self._api.base_URL}{endpoint}"
            headers = {
                "X-Client-ID": self._api.user_id or self._user_id,
                "Content-Type": "application/json",
            }

            response = self._api.session.post(
                url, json=payload, headers=headers, timeout=timeout
            )
            response.raise_for_status()

            return response.json()

        except Exception as e:
            self._logger.error(f"API POST request failed: {e}")
            return None
