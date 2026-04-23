# Filename: tree.py
# Module name: config
# Description: Four-column QTreeWidget with category headers and editable stream items.

from __future__ import annotations

import logging

# PySide6 (Python/Qt)
from PySide6 import QtGui
from PySide6 import QtCore
from PySide6 import QtWidgets
import qtawesome as qta
import typing


# core.gui.widgets
from gui.widgets.toolbar import ToolBar
from gui.compat import Composite, Fuel, Fluid, Material, Electricity, MassCurrent, Energy, Cost


class StreamTree(QtWidgets.QTreeWidget):

    def __init__(self, parent=None):
        super().__init__(parent, columnCount=3)
        super().setEditTriggers(QtWidgets.QTreeWidget.EditTrigger.DoubleClicked)

        # Customize appearance and behaviour
        self.setHeaderLabels(["Stream", "Value", ""])
        self.setStyleSheet("QTreeWidget::item { height: 28px; padding: 2px;}")
        self.setSelectionMode(QtWidgets.QTreeWidget.SelectionMode.SingleSelection)

        # Customize header
        header = self.header()
        header.setDefaultAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setColumnWidth(0, 400)
        self.setColumnWidth(1, 200)

        # Primary action group for selecting the node's primary stream
        self._primary_group = QtGui.QActionGroup(self)
        self._tree_data: dict[str, QtWidgets.QWidget] = {}

        # Initialize top-level items
        self._init_top_level([Fuel, Fluid, Material, Electricity, MassCurrent, Energy, Cost])

    def _init_top_level(self, _stream_list: list[type]):

        for _class in _stream_list:

            image = "mdi.arrow-right-bold"
            color = "gray"
            if issubclass(_class, Composite):
                image = _class.image
                color = _class.color

            label = getattr(_class, "_label", _class.__name__)
            item = QtWidgets.QTreeWidgetItem(self)
            item.setText(0, label)
            item.setIcon(0, qta.icon(image, color=color))
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, _class)

            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)

            toolbar = ToolBar(
                self,
                trailing=True,
            )

            add_stream = toolbar.addAction(
                qta.icon("mdi.plus", color="gray", color_active="white"), "Add Stream"
            )
            add_stream.triggered.connect(lambda _, i=item: self.create_row(i))

            self.setItemWidget(item, 2, toolbar)

    def _get_root_from_selection(self) -> QtWidgets.QTreeWidgetItem | None:

        if selected := self.currentItem():
            while selected.parent():
                selected = selected.parent()

            return selected

        return None

    def _add_grouped_attributes(
        self,
        root: QtWidgets.QTreeWidgetItem,
        composite_cls: type,
    ) -> None:

        hierarchy = getattr(composite_cls, "attribute_hierarchy", {})
        for key in hierarchy:

            section = QtWidgets.QTreeWidgetItem([key.capitalize()])
            section.setIcon(0, qta.icon("mdi.minus", color="white"))

            icon = "mdi.format-list-bulleted"
            root.setIcon(0, qta.icon(icon, color="#cbcbcb"))
            root.addChild(section)

            for attr in hierarchy[key]:

                label = hierarchy[key][attr]
                field = QtWidgets.QTreeWidgetItem(section)
                field.setText(0, label)
                field.setTextAlignment(
                    0,
                    QtCore.Qt.AlignmentFlag.AlignVCenter
                    | QtCore.Qt.AlignmentFlag.AlignRight,
                )

                self.setItemWidget(field, 1, QtWidgets.QLineEdit(self))

    @QtCore.Slot()
    def create_row(
        self, root: QtWidgets.QTreeWidgetItem
    ) -> QtWidgets.QTreeWidgetItem | None:

        # Resolve the target root from the current selection if not provided
        root = root or self._get_root_from_selection()
        if root is None:
            return None

        data = root.data(0, QtCore.Qt.ItemDataRole.UserRole)

        item = QtWidgets.QTreeWidgetItem(root)
        item.setText(0, f"{root.text(0)} {root.childCount()}")
        item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)

        self._add_grouped_attributes(item, data)

        # Column 2: Actions toolbar
        toolbar = ToolBar(
            self,
            trailing=True,
            iconSize=QtCore.QSize(18, 18),
        )
        toolbar.addAction(
            qta.icon("mdi.check-all", color="gray", color_active="white"), "Check"
        )
        toolbar.addAction(
            qta.icon("mdi.eraser", color="gray", color_active="white"), "Erase"
        )
        toolbar.addAction(
            qta.icon("mdi.delete", color="red", color_active="white"), "Delete"
        )

        # Set widgets
        self.setItemWidget(item, 2, toolbar)
        self.editItem(item, 0)
        root.setExpanded(True)

        return item

    @QtCore.Slot()
    def delete_row(self, item: QtWidgets.QTreeWidgetItem) -> None:
        parent = item.parent()
        if parent:
            parent.removeChild(item)
            parent.setText(0, f"{parent.text(0)} {parent.childCount()}")

    def add_item(self, name: str, stream_type_name: str) -> None:
        """
        Add a stream item to the tree under the appropriate type category.

        Args:
            name: Stream name (e.g., "coal", "iron")
            stream_type_name: Type name (e.g., "Fuel", "Material", "Electricity")
        """
        logger = logging.getLogger("StreamTree")

        # Find the root item matching this type
        root_item = None
        for idx in range(self.topLevelItemCount()):
            item = self.topLevelItem(idx)
            if item and item.text(0) == stream_type_name:
                root_item = item
                break

        if not root_item:
            logger.warning(f"Could not find stream type '{stream_type_name}' in tree")
            return

        # Create a new child item under the root
        child = QtWidgets.QTreeWidgetItem(root_item)
        child.setText(0, name)
        child.setFlags(child.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
        root_item.setExpanded(True)
        logger.info(f"Added stream '{name}' of type '{stream_type_name}' to tree")

    def to_dict(self) -> dict[str, str]:
        """
        Serialize all stream items in the tree to a dict.

        Returns:
            dict mapping stream name → stream type (e.g., {"iron": "Material", "coal": "Fuel"})
        """
        result = {}

        # Iterate over root items (Fuel, Fluid, Material, Electricity)
        for root_idx in range(self.topLevelItemCount()):
            root = self.topLevelItem(root_idx)
            if not root:
                continue

            # Get the stream type class from this root
            stream_type = root.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if not stream_type:
                continue

            stream_type_name = getattr(stream_type, "_label", stream_type.__name__)

            # Iterate over direct children of the root (actual streams added by user)
            for child_idx in range(root.childCount()):
                child = root.child(child_idx)
                if not child:
                    continue

                stream_name = child.text(0).strip()

                # Collect direct children of root (which are the actual stream items)
                if stream_name:
                    # Extract just the stream name (remove the counter suffix like "Material 1" -> "material")
                    base_name = stream_name.split()[0].lower() if len(stream_name.split()) > 1 else stream_name.lower()
                    result[base_name] = stream_type_name

        return result

    def from_dict(self, data: dict[str, typing.Any]) -> None:

        for key, value in data.items():
            self.create_row(None, key)


class ParamsTree(QtWidgets.QTreeWidget):
    """Simplified tree widget for parameters (not streams)."""

    def __init__(self, parent=None):
        super().__init__(parent, columnCount=4)
        super().setEditTriggers(QtWidgets.QTreeWidget.EditTrigger.DoubleClicked)

        self.setHeaderLabels(["Parameter", "Type", "Value", "Unit"])
        self.setStyleSheet("QTreeWidget::item { height: 28px; padding: 2px;}")
        self.setSelectionMode(QtWidgets.QTreeWidget.SelectionMode.SingleSelection)

        header = self.header()
        header.setDefaultAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setColumnWidth(0, 200)
        self.setColumnWidth(1, 150)
        self.setColumnWidth(2, 150)
        self.setColumnWidth(3, 150)

        # Add param button
        self._root = QtWidgets.QTreeWidgetItem(self)
        self._root.setText(0, "Parameters")
        self._root.setIcon(0, qta.icon("mdi.sigma", color="gray"))

        toolbar = ToolBar(self, trailing=True)
        add_param = toolbar.addAction(
            qta.icon("mdi.plus", color="gray", color_active="white"), "Add Param"
        )
        add_param.triggered.connect(self._on_add_param)
        self.setItemWidget(self._root, 2, toolbar)

    @QtCore.Slot()
    def _on_add_param(self) -> None:
        """Show dialog to add a new parameter."""
        from gui.compat import CLASS_REGISTRY

        param_classes = sorted([
            name for name, cls in CLASS_REGISTRY.items()
            if cls and name not in ('Composite', 'Material', 'Electricity', 'Fluid', 'Fuel')
        ])

        if not param_classes:
            return

        param_name, ok1 = QtWidgets.QInputDialog.getText(
            self, "New Parameter", "Parameter name:"
        )
        if not ok1 or not param_name.strip():
            return

        param_type, ok2 = QtWidgets.QInputDialog.getItem(
            self, "Parameter Type", "Select type:", param_classes, 0, False
        )
        if not ok2:
            return

        self.add_item(param_name.strip(), param_type)

    def add_item(self, name: str, param_type: str, value: str = "", unit: str = "") -> None:
        """Add a parameter to the tree with optional value and unit."""
        item = QtWidgets.QTreeWidgetItem(self._root)
        item.setText(0, name)
        item.setText(1, param_type)
        item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)

        # Add value input field
        value_input = QtWidgets.QLineEdit(self)
        value_input.setText(value)
        value_input.setPlaceholderText("e.g., 50")
        self.setItemWidget(item, 2, value_input)

        # Add unit combobox with common units for this dimension
        unit_combo = QtWidgets.QComboBox(self)
        unit_combo.setEditable(True)  # Allow users to type custom units

        # Map param type to common units for quick selection
        unit_map = {
            "SpecificEnergy": ["kWh/ton", "kJ/kg", "MJ/ton"],
            "Energy": ["kWh", "MJ", "GJ"],
            "Quantity": ["", "dimensionless"],
            "SpecificCost": ["$/ton", "$/kg", "$/m3"],
            "Currency": ["$", "€", "£"],
            "ElectricityTariff": ["$/kWh", "$/MWh"],
            "Density": ["kg/m3", "ton/m3", "g/cm3"],
            "Mass": ["ton", "kg", "g"],
            "EnergyCost": ["$/MWh", "$/kWh"],
            "MassCurrent": ["ton/hr", "kg/hr"],
        }

        common_units = unit_map.get(param_type, [])
        unit_combo.addItems(common_units)

        if unit:
            idx = unit_combo.findText(unit)
            if idx >= 0:
                unit_combo.setCurrentIndex(idx)
            else:
                unit_combo.setCurrentText(unit)

        self.setItemWidget(item, 3, unit_combo)
        self._root.setExpanded(True)

    def to_dict(self) -> dict[str, typing.Any]:
        """Serialize params to dict: {param_name: {"type": type_name, "value": value, "unit": unit}}."""
        result = {}
        for idx in range(self._root.childCount()):
            child = self._root.child(idx)
            if child:
                param_name = child.text(0).strip()
                param_type = child.text(1).strip()

                # Get value from column 2 (QLineEdit)
                value_widget = self.itemWidget(child, 2)
                value = ""
                if isinstance(value_widget, QtWidgets.QLineEdit):
                    value = value_widget.text().strip()

                # Get unit from column 3 (QComboBox)
                unit_widget = self.itemWidget(child, 3)
                unit = ""
                if isinstance(unit_widget, QtWidgets.QComboBox):
                    unit = unit_widget.currentText().strip()

                if param_name and param_type:
                    result[param_name] = {"type": param_type, "value": value, "unit": unit}
        return result

    def from_dict(self, data: dict[str, typing.Any]) -> None:
        """Load params from dict."""
        for name, info in data.items():
            if isinstance(info, dict):
                param_type = info.get("type", "")
                value = info.get("value", "")
                unit = info.get("unit", "")
            else:
                # Fallback for old format (just type string)
                param_type = str(info)
                value = ""
                unit = ""
            self.add_item(name, param_type, value, unit)
