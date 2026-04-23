# Module Name: gui.maps.overlay
# Description: Overlay layer for template markers with O(1) spatial hover detection

from __future__ import annotations

from collections import defaultdict

from PySide6 import QtCore, QtGui, QtWidgets

from gui.graph.reusable.icon import QtaItem
from gui.maps.relay import MapsRelay


class _FocusTarget(QtWidgets.QGraphicsObject):
    def boundingRect(self) -> QtCore.QRectF:
        return QtCore.QRectF(-1, -1, 2, 2)

    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionGraphicsItem,
        widget=None,
    ) -> None:
        return


class Marker(QtWidgets.QGraphicsObject):

    GRID_CELL = 16  # pixels per grid cell
    HOVER_R = 6  # hover detection radius in pixels
    ICON_NAME = "mdi.map-marker"
    ICON_SIZE = 28

    def __init__(self, parent: QtWidgets.QGraphicsObject | None = None) -> None:

        super().__init__(parent)
        self.setAcceptHoverEvents(True)
        self.setCacheMode(QtWidgets.QGraphicsItem.CacheMode.NoCache)
        self.setFlag(
            QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemUsesExtendedStyleOption
        )
        self.setZValue(10)

        # {(x, y): [{"template_uid": str, "plant_name": str, "capacity": float, "color": str}, ...]}
        self._markers: dict[tuple[int, int], list[dict]] = {}
        self._grid: dict[tuple[int, int], set[tuple[int, int]]] = defaultdict(set)
        self._template_keys: dict[str, tuple[int, int]] = {}
        self._marker_items: dict[tuple[int, int], QtaItem] = {}
        self._hovered: tuple[int, int] | None = None
        self._bounds = QtCore.QRectF()
        self._focus_target = _FocusTarget(self)
        self._focus_target.hide()

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def _get_bubble_color(self, marker: dict) -> QtGui.QColor:
        """Get bubble color from instance metadata (same for all instances of same pathway)."""
        color_hex = marker.get("color", "#FF4444")
        return QtGui.QColor(color_hex)

    def _create_abbreviation(self, marker: dict) -> str:
        """Create short abbreviation from template_uid.

        Format: State_CapacityMTPa_Pathway_CCUS
        Example: TamilNadu_15MTPa_BFBOF_NoCCUS → TN/BF/15
        """
        template_uid = marker.get("template_uid", "")
        parts = template_uid.split("_")

        if len(parts) >= 3:
            # State: first word, take first 2 chars
            state_abbr = parts[0][:2].upper()
            # Pathway: third word (parts[2]), take first 2-3 chars
            pathway = parts[2] if len(parts) > 2 else ""
            pathway_abbr = pathway[:2].upper() if pathway else ""
            # Capacity: second word (parts[1]), extract number
            capacity_str = parts[1] if len(parts) > 1 else ""
            cap_num = "".join(c for c in capacity_str if c.isdigit())
            return f"{state_abbr}/{pathway_abbr}/{cap_num}"

        return template_uid[:8]

    def _set_marker_icon_style(self, key: tuple[int, int], is_hovered: bool) -> None:
        item = self._marker_items.get(key)
        markers_at_pos = self._markers.get(key, [])
        if item is None or not markers_at_pos:
            return

        marker_color = self._get_bubble_color(markers_at_pos[0])
        icon_color = QtGui.QColor(0xFFCB00) if is_hovered else marker_color
        item.render_icon(self.ICON_NAME, icon_color.name())
        item.setScale((self.ICON_SIZE + 4) / self.ICON_SIZE if is_hovered else 1.0)
        item.setZValue(1 if is_hovered else 0)

    # ------------------------------------------------------------------
    # Spatial grid helpers
    # ------------------------------------------------------------------

    def _cell(self, x: int, y: int) -> tuple[int, int]:
        return x // self.GRID_CELL, y // self.GRID_CELL

    def _cells_in_rect(self, rect: QtCore.QRectF) -> list[tuple[int, int]]:
        x0 = int(rect.left()) // self.GRID_CELL
        y0 = int(rect.top()) // self.GRID_CELL
        x1 = int(rect.right()) // self.GRID_CELL + 1
        y1 = int(rect.bottom()) // self.GRID_CELL + 1
        return [(x, y) for x in range(x0, x1) for y in range(y0, y1)]

    def _find_near(self, x: int, y: int) -> tuple[int, int] | None:
        cell = self._cell(x, y)
        r2 = self.HOVER_R**2
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for key in self._grid.get((cell[0] + dx, cell[1] + dy), ()):
                    mx, my = key
                    if (mx - x) ** 2 + (my - y) ** 2 <= r2:
                        return key
        return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_marker(
        self,
        x: int,
        y: int,
        template_uid: str,
        plant_name: str,
        capacity: float = 0.0,
        color: str = "#FF4444",
    ) -> None:
        key = (x, y)
        if key not in self._markers:
            self._markers[key] = []
            item = QtaItem(self.ICON_NAME, width=self.ICON_SIZE, parent=self)
            item.setAcceptHoverEvents(False)
            item.setAcceptedMouseButtons(QtCore.Qt.MouseButton.NoButton)
            item.setPos(x, y)
            self._marker_items[key] = item

        self._markers[key].append(
            {
                "template_uid": template_uid,
                "plant_name": plant_name,
                "capacity": capacity,
                "color": color,
            }
        )
        self._template_keys[template_uid] = key
        self._grid[self._cell(x, y)].add(key)

        # Expand bounding rect
        m = self.ICON_SIZE + 6
        self.prepareGeometryChange()
        pt_rect = QtCore.QRectF(x - m, y - m, m * 2, m * 2)
        self._bounds = (
            self._bounds.united(pt_rect) if not self._bounds.isNull() else pt_rect
        )
        self._set_marker_icon_style(key, key == self._hovered)

    def clear_markers(self) -> None:
        self.prepareGeometryChange()
        self._markers.clear()
        self._grid.clear()
        self._template_keys.clear()
        for item in self._marker_items.values():
            scene = item.scene()
            item.setParentItem(None)
            if scene is not None:
                scene.removeItem(item)
        self._marker_items.clear()
        self._hovered = None
        self._bounds = QtCore.QRectF()
        self.update()

    def focus_template(self, template_uid: str) -> bool:
        key = self._template_keys.get(template_uid)
        if key is None:
            return False

        if self._hovered is not None and self._hovered != key:
            self._set_marker_icon_style(self._hovered, False)
        self._hovered = key
        self._set_marker_icon_style(key, True)
        self._focus_target.setPos(*key)
        self.update()

        app = QtWidgets.QApplication.instance()
        if app and hasattr(app, "view_ctrl"):
            app.view_ctrl.focus_item.emit(self._focus_target)
            return True
        return False

    # ------------------------------------------------------------------
    # QGraphicsObject interface
    # ------------------------------------------------------------------

    def boundingRect(self) -> QtCore.QRectF:
        return self._bounds.adjusted(-4, -4, 4, 4)

    def shape(self) -> QtGui.QPainterPath:
        # Shape includes all markers for hover/click detection
        path = QtGui.QPainterPath()
        size = 40
        margin = 15  # Click tolerance around markers

        for x, y in self._markers.keys():
            # Create a square around each marker for hit detection
            rect = QtCore.QRectF(
                x - size - margin,
                y - size - margin,
                (size + margin) * 2,
                (size + margin) * 2,
            )
            path.addRect(rect)

        return path

    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionGraphicsItem,
        widget=None,
    ) -> None:
        return

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def hoverMoveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        x, y = int(event.pos().x()), int(event.pos().y())
        new_hovered = self._find_near(x, y)
        if new_hovered != self._hovered:
            if self._hovered is not None:
                self._set_marker_icon_style(self._hovered, False)
            self._hovered = new_hovered
            if self._hovered is not None:
                self._set_marker_icon_style(self._hovered, True)
        super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        if self._hovered is not None:
            self._set_marker_icon_style(self._hovered, False)
        self._hovered = None
        super().hoverLeaveEvent(event)

    def mouseDoubleClickEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:

        if self._hovered:

            markers_at_pos = self._markers.get(self._hovered, [])
            if markers_at_pos:
                # If multiple markers, open the one with highest capacity
                marker = max(markers_at_pos, key=lambda m: m.get("capacity", 0))
                MapsRelay.instance().sig_open_template.emit(
                    marker["template_uid"],
                    marker["plant_name"],
                )

        # super().mouseDoubleClickEvent(event)  # Don't call base to prevent default behavior
