# Filename: core/graph/node/__init__.py
# Module Name: core/graph/node
# Description: QGraphicsObject-based graphical representation of a graph-node.


from __future__ import annotations

# Standard
import json
import logging

# Dataclass
from dataclasses import field
from dataclasses import dataclass

# PySide6 (Python/Qt)
from PySide6 import QtGui
from PySide6 import QtCore
from PySide6 import QtWidgets

from gui.graph.node.config import NodeConfigWidget

ItemState = QtWidgets.QStyle.StateFlag


class NodeRepr(QtWidgets.QGraphicsObject):

    # Class logger
    _logger = logging.getLogger("NodeRepr")

    # Signals:
    activate_preview = QtCore.Signal(QtWidgets.QGraphicsObject)
    item_shifted = QtCore.Signal(QtWidgets.QGraphicsObject)
    item_focused = QtCore.Signal(QtWidgets.QGraphicsObject)

    @dataclass
    class Attributes:
        """Default node attributes.

        Attributes:
            label: The node's default name/label.
            image: The node's default qtawesome icon-name.
            color: The node's default qtawesome color.
        """

        label: str
        image: str
        color: str

    @dataclass
    class Appearance:
        """Options for the node's appearance.

        Attributes:
            border: The node's border style.
            background: The node's background style.
        """

        border: dict[ItemState, QtGui.QPen]
        background: dict[ItemState, QtGui.QBrush]

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
        dimensions: QtCore.QRectF

    @dataclass
    class Behavior:
        """Behavioral flags for the node."""

        pass

    @dataclass
    class Connections:
        """Dictionaries to store the node's connections.

        Attributes:
            incoming: The node's incoming connections.
            outgoing: The node's outgoing connections.
        """

        incoming: dict[object, object]
        outgoing: dict[object, object]

    # Constructor
    def __init__(
        self,
        nuid: str,
        parent: QtWidgets.QGraphicsObject | None = None,
        **kwargs,
    ) -> None:

        # 1. Store attributes and config
        self._uid = nuid
        self._enabled = True
        self._ui_config = kwargs.pop("ui_config", {})

        # 2. Initialize defaults
        self._init_defaults()

        # 3. Initialize super-class with appropriate data
        super().__init__(parent, pos=kwargs.pop("pos", QtCore.QPointF()), z=0)

        # 4. Toggle flags
        graphics_item_flag = QtWidgets.QGraphicsItem.GraphicsItemFlag
        self.setFlag(graphics_item_flag.ItemIsMovable)
        self.setFlag(graphics_item_flag.ItemIsSelectable)
        self.setFlag(graphics_item_flag.ItemSendsScenePositionChanges)

        # 5. UI child elements
        self._init_image()
        self._init_label(label_text=nuid)

        # 6. Config dialog (lazy init)
        self._configurator = NodeConfigWidget()

    def _init_defaults(self) -> None:
        """Initialize default values for appearance, geometry, attributes, and connections."""
        self._attributes = NodeRepr.Attributes(
            label="Node",
            image="mdi.function-variant",
            color="#efefef",
        )

        self._appearance = NodeRepr.Appearance(
            border={
                ItemState.State_Enabled: QtGui.QPen(QtGui.QColor(0x232A2E), 1.0),
                ItemState.State_Selected: QtGui.QPen(QtGui.QColor(0xFFCB00), 1.0),
                ItemState.State_MouseOver: QtGui.QPen(QtGui.QColor(0x232A2E), 1.0),
            },
            background={
                ItemState.State_Enabled: QtGui.QBrush(QtGui.QColor(0x232A2E)),
                ItemState.State_Selected: QtGui.QBrush(QtGui.QColor(0xFFCB00)),
                ItemState.State_MouseOver: QtGui.QBrush(QtGui.QColor(0x232A2E)),
            },
        )

        self._geometry = NodeRepr.Geometry(
            border_radius=4,
            padding=4,
            dimensions=QtCore.QRectF(-16, -16, 32, 32),
        )

        self._connections = NodeRepr.Connections(
            incoming={},
            outgoing={},
        )

    def _init_image(self):

        # QtAwesome Icon - choose based on style
        from qtawesome import icon as qta_icon

        style = self._ui_config.get("style", "node") if self._ui_config else "node"

        if style == "inlet":
            icon_name = "mdi.arrow-down-bold"
        elif style == "outlet":
            icon_name = "mdi.arrow-up-bold"
        else:
            icon_name = self._attributes.image

        self._node_icon = qta_icon(
            icon_name,
            color=self._attributes.color,
            color_active="black",
        )

    def _init_label(self, label_text: str = None):

        # Import `Label` from gui.graph.reusable
        from gui.graph.reusable.label import Label

        # Use provided label text or default
        text = label_text or self._attributes.label

        # TODO: Find a better way to locate the situate the label w.r.t the node.
        label = Label(
            text,
            parent=self,
            width=120,
            align=QtCore.Qt.AlignmentFlag.AlignCenter,
            pos=QtCore.QPointF(-60, 18),
        )

        label.sig_text_changed.connect(self.setObjectName)
        self.objectNameChanged.connect(lambda text: label.setPlainText(text))

    # Section: Reimplementation
    # -------------------------

    def boundingRect(self):
        return self._geometry.dimensions.adjusted(
            -self._geometry.padding,
            -self._geometry.padding,
            self._geometry.padding,
            self._geometry.padding,
        )

    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionGraphicsItem,
        /,
        widget: QtWidgets.QWidget | None = None,
    ) -> None:

        pen_dict = self._appearance.border
        brs_dict = self._appearance.background

        if option.state & ItemState.State_Selected:
            painter.setPen(pen_dict[ItemState.State_Selected])
            painter.setBrush(brs_dict[ItemState.State_Selected])

        elif not self._enabled:
            # Disabled nodes: light grey background and border
            painter.setPen(QtGui.QPen(QtGui.QColor(0xCCCCCC), 1.0))
            painter.setBrush(QtGui.QBrush(QtGui.QColor(0xE8E8E8)))

        else:
            # Get style from UI config (default: "node")
            style = self._ui_config.get("style", "node") if self._ui_config else "node"

            # Check if node has custom color in UI config
            if self._ui_config and "color" in self._ui_config:
                color = QtGui.QColor(self._ui_config["color"])
            else:
                # Color by node type - mixed palette
                nuid = self._uid
                if nuid == 'coke_oven':
                    color = QtGui.QColor(0x4DB8FF)
                elif nuid == 'sinter_plant':
                    color = QtGui.QColor(0x00CCFF)
                elif nuid == 'pellet_production':
                    color = QtGui.QColor(0x4DFFFF)
                elif nuid == 'iron_making':
                    # Green for iron making
                    color = QtGui.QColor(0x4DFF4D)
                elif nuid == 'steelmaking':
                    # Orange for steelmaking
                    color = QtGui.QColor(0xFFB84D)
                elif nuid == 'steel_casting':
                    # Purple for casting
                    color = QtGui.QColor(0xD64DFF)
                elif nuid == 'rolling_mill':
                    # Magenta for rolling
                    color = QtGui.QColor(0xFF4DB8)
                elif nuid == 'carbon_capture':
                    # Red for carbon capture
                    color = QtGui.QColor(0xFF6B6B)
                elif nuid == 'waste_heat_recovery':
                    # Yellow for waste heat
                    color = QtGui.QColor(0xFFFF4D)
                else:
                    # Default teal for any other nodes
                    color = QtGui.QColor(0x4DFFBF)

            # Use same color for border (slightly darker shade)
            pen_color = color.darker(120)

            painter.setPen(QtGui.QPen(pen_color, 1.0))
            painter.setBrush(QtGui.QBrush(color))

        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.RenderHint.TextAntialiasing)
        painter.setRenderHint(QtGui.QPainter.RenderHint.SmoothPixmapTransform)

        painter.drawRoundedRect(
            self._geometry.dimensions,
            self._geometry.border_radius,
            self._geometry.border_radius,
        )

        # If an icon is available, paint it on top
        from qtawesome import icon as qta_icon

        if self.isSelected():
            color = "black"
        elif not self._enabled:
            color = "#AAAAAA"  # Light grey icon for disabled nodes
        else:
            color = "black"  # Black icon for enabled nodes

        qta_icon(self._attributes.image, color=color).paint(
            painter,
            self.boundingRect().adjusted(8, 8, -8, -8).toRect(),
        )

    def itemChange(self, change: QtWidgets.QGraphicsItem.GraphicsItemChange, value):

        graphics_item_change = QtWidgets.QGraphicsItem.GraphicsItemChange
        if change == graphics_item_change.ItemScenePositionHasChanged:
            self.item_shifted.emit(self)

        return super().itemChange(change, value)

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:

        mbt = event.button()
        mod = event.modifiers()

        if (
            mbt == QtCore.Qt.MouseButton.LeftButton
            and mod == QtCore.Qt.KeyboardModifier.AltModifier
        ):
            self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            self.activate_preview.emit(self)
            return

        super().mousePressEvent(event)
        if event.isAccepted():
            return

    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:

        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)

        super().mouseReleaseEvent(event)
        if event.isAccepted():
            return

    def mouseDoubleClickEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """Show the NodeConfig dialog on double-click."""

        # Emit item-focused signal to center viewer on this node
        app = QtWidgets.QApplication.instance()
        if app and hasattr(app, "view_ctrl"):
            app.view_ctrl.focus_item.emit(self)

        # Ensure the dialog has a proper parent window for display
        if not self._configurator.parent():
            if app:
                self._configurator.setParent(app.activeWindow())

        # Set node item for commits and fetch server data
        self._configurator._node_item = self
        self._configurator.fetch_and_populate(self)

        self._configurator.raise_()
        self._configurator.show()

    @QtCore.Slot(str, str)
    def _on_show_node_data(self, nuid: str, jstr: str) -> None:

        if nuid != self._uid:
            return

        data = json.loads(jstr)
        self._configurator.from_data(data, node_item=self)
        self._configurator.show()

    @QtCore.Slot(str)
    def _on_config_save(self, jstr: str) -> None:

        cuid = getattr(self.scene(), "uid", None)
        # if cuid:
        #     self._signal_bus.raise_request(
        #         "update_node_data",
        #         cuid,
        #         self.uid,
        #         jstr,
        #     )
        # else:
        #     self._logger.warning(f"Canvas UID not found — cannot save node data.")

    # Section: Public methods
    # -----------------------

    def signals(self) -> dict[str, QtCore.SignalInstance]:
        return {
            "activate_preview": self.activate_preview,
            "item_shifted": self.item_shifted,
            "item_focused": self.item_focused,
        }

    # Properties
    # ----------

    def set_enabled(self, enabled: bool) -> None:
        """Grey out when disabled/bypassed, steelblue when enabled."""
        color = QtGui.QColor(0x2A6496) if enabled else QtGui.QColor(0x555555)
        self._appearance.border[ItemState.State_Enabled]     = QtGui.QPen(color, 1.0)
        self._appearance.background[ItemState.State_Enabled] = QtGui.QBrush(color)
        self.update()

    @property
    def uid(self) -> str:
        return self._uid

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value
        self.update()  # Redraw with new appearance
