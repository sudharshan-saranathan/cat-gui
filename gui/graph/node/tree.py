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

_PARAM_UNIT_MAP = {
    "SpecificEnergy": ["kWh/ton", "kJ/kg", "MJ/ton"],
    "Energy": ["kWh", "MJ", "GJ"],
    "Quantity": ["", "dimensionless"],
    "SpecificCost": ["$/ton", "$/kg", "$/m3"],
    "Currency": ["$", "EUR", "GBP"],
    "ElectricityTariff": ["$/kWh", "$/MWh"],
    "Density": ["kg/m3", "ton/m3", "g/cm3"],
    "Mass": ["ton", "kg", "g"],
    "EnergyCost": ["$/MWh", "$/kWh"],
    "MassCurrent": ["ton/hr", "kg/hr"],
}


def _parameter_classes() -> list[str]:
    from gui.compat import CLASS_REGISTRY

    return sorted(
        [
            name
            for name, cls in CLASS_REGISTRY.items()
            if cls and name not in ("Composite", "Material", "Electricity", "Fluid", "Fuel")
        ]
    )


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
                iconSize=QtCore.QSize(16, 16),
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
                    # Extract just the stream name (remove the counter-suffix like "Material 1" -> "material")
                    base_name = stream_name.split()[0].lower() if len(stream_name.split()) > 1 else stream_name.lower()
                    result[base_name] = stream_type_name

        return result

    def from_dict(self, data: dict[str, typing.Any]) -> None:

        for key, value in data.items():
            self.create_row(None, key)


class ParamsTree(QtWidgets.QTreeWidget):
    """Structured editor for # parameters."""

    def __init__(self, parent=None):
        super().__init__(parent, columnCount=5)
        super().setEditTriggers(QtWidgets.QTreeWidget.EditTrigger.DoubleClicked)

        self.setHeaderLabels(["Parameter", "Type", "Initial", "f(t)", "Unit"])
        self.setStyleSheet("QTreeWidget::item { height: 28px; padding: 2px;}")
        self.setSelectionMode(QtWidgets.QTreeWidget.SelectionMode.SingleSelection)

        header = self.header()
        header.setDefaultAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setColumnWidth(0, 200)
        self.setColumnWidth(1, 150)
        self.setColumnWidth(2, 150)
        self.setColumnWidth(3, 260)
        self.setColumnWidth(4, 150)

        self._root = QtWidgets.QTreeWidgetItem(self)
        self._root.setText(0, "Parameters")
        self._root.setIcon(0, qta.icon("mdi.sigma", color="gray"))

        toolbar = ToolBar(self, trailing=True)
        add_param = toolbar.addAction(
            qta.icon("mdi.plus", color="gray", color_active="white"), "Add Param"
        )
        add_param.triggered.connect(self._on_add_param)
        self.setItemWidget(self._root, 4, toolbar)

    @QtCore.Slot()
    def _on_add_param(self) -> None:
        param_classes = _parameter_classes()
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

    def add_item(
        self,
        name: str,
        param_type: str,
        value: str = "",
        units: str = "",
        f_t: str = "",
    ) -> None:
        item = QtWidgets.QTreeWidgetItem(self._root)
        item.setText(0, name)
        item.setText(1, param_type)
        item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)

        initial_input = QtWidgets.QLineEdit(self)
        initial_input.setText(value)
        initial_input.setPlaceholderText("e.g., 50")
        self.setItemWidget(item, 2, initial_input)

        f_t_input = QtWidgets.QLineEdit(self)
        f_t_input.setText(f_t or value)
        f_t_input.setPlaceholderText("e.g., 50 + (t-2025)*2")
        self.setItemWidget(item, 3, f_t_input)

        unit_combo = QtWidgets.QComboBox(self)
        unit_combo.setEditable(True)
        unit_combo.addItems(_PARAM_UNIT_MAP.get(param_type, []))
        if units:
            idx = unit_combo.findText(units)
            if idx >= 0:
                unit_combo.setCurrentIndex(idx)
            else:
                unit_combo.setCurrentText(units)
        self.setItemWidget(item, 4, unit_combo)
        self._root.setExpanded(True)

    def to_dict(self) -> dict[str, typing.Any]:
        result = {}
        for idx in range(self._root.childCount()):
            child = self._root.child(idx)
            if not child:
                continue

            name = child.text(0).strip()
            param_type = child.text(1).strip()
            if not name or not param_type:
                continue

            initial_widget = self.itemWidget(child, 2)
            f_t_widget = self.itemWidget(child, 3)
            unit_widget = self.itemWidget(child, 4)

            initial = (
                initial_widget.text().strip()
                if isinstance(initial_widget, QtWidgets.QLineEdit)
                else ""
            )
            f_t = (
                f_t_widget.text().strip()
                if isinstance(f_t_widget, QtWidgets.QLineEdit)
                else ""
            )
            units = (
                unit_widget.currentText().strip()
                if isinstance(unit_widget, QtWidgets.QComboBox)
                else ""
            )

            result[name] = {
                "type": param_type,
                "value": initial,
                "f_t": f_t or initial,
                "units": units,
            }
        return result

    def from_dict(self, data: dict[str, typing.Any]) -> None:
        for name, info in data.items():
            if isinstance(info, dict):
                self.add_item(
                    name,
                    info.get("type", ""),
                    info.get("value", info.get("initial", "")),
                    info.get("units", info.get("unit", "")),
                    info.get("f_t", info.get("f(t)", "")),
                )
            else:
                self.add_item(name, str(info))


class DecisionTree(QtWidgets.QTreeWidget):
    """Structured editor for ? decision variables."""

    def __init__(self, parent=None):
        super().__init__(parent, columnCount=2)
        super().setEditTriggers(QtWidgets.QTreeWidget.EditTrigger.DoubleClicked)

        self.setHeaderLabels(["Decision Variable", "Type"])
        self.setStyleSheet("QTreeWidget::item { height: 28px; padding: 2px;}")
        self.setSelectionMode(QtWidgets.QTreeWidget.SelectionMode.SingleSelection)

        header = self.header()
        header.setDefaultAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setColumnWidth(0, 240)
        self.setColumnWidth(1, 180)

        self._root = QtWidgets.QTreeWidgetItem(self)
        self._root.setText(0, "Decision Variables")
        self._root.setIcon(0, qta.icon("mdi.help-rhombus", color="gray"))

        toolbar = ToolBar(self, trailing=True)
        add_decision = toolbar.addAction(
            qta.icon("mdi.plus", color="gray", color_active="white"), "Add Decision"
        )
        add_decision.triggered.connect(self._on_add_decision)
        self.setItemWidget(self._root, 1, toolbar)

    @QtCore.Slot()
    def _on_add_decision(self) -> None:
        decision_classes = _parameter_classes()
        if not decision_classes:
            return

        decision_name, ok1 = QtWidgets.QInputDialog.getText(
            self, "New Decision Variable", "Decision variable name:"
        )
        if not ok1 or not decision_name.strip():
            return

        decision_type, ok2 = QtWidgets.QInputDialog.getItem(
            self, "Decision Variable Type", "Select type:", decision_classes, 0, False
        )
        if not ok2:
            return

        self.add_item(decision_name.strip(), decision_type)

    def add_item(self, name: str, decision_type: str) -> None:
        item = QtWidgets.QTreeWidgetItem(self._root)
        item.setText(0, name)
        item.setText(1, decision_type)
        item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
        self._root.setExpanded(True)

    def to_dict(self) -> dict[str, str]:
        result: dict[str, str] = {}
        for idx in range(self._root.childCount()):
            child = self._root.child(idx)
            if not child:
                continue
            name = child.text(0).strip()
            decision_type = child.text(1).strip()
            if name and decision_type:
                result[name] = decision_type
        return result

    def from_dict(self, data: dict[str, typing.Any]) -> None:
        for name, info in data.items():
            self.add_item(name, str(info))


class EquationTree(QtWidgets.QTreeWidget):
    """Structured editor for = equations."""

    def __init__(self, parent=None):
        super().__init__(parent, columnCount=2)
        super().setEditTriggers(QtWidgets.QTreeWidget.EditTrigger.DoubleClicked)

        self.setHeaderLabels(["Equation", "Expression"])
        self.setStyleSheet("QTreeWidget::item { height: 28px; padding: 2px;}")
        self.setSelectionMode(QtWidgets.QTreeWidget.SelectionMode.SingleSelection)

        header = self.header()
        header.setDefaultAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setColumnWidth(0, 220)
        self.setColumnWidth(1, 520)

        self._root = QtWidgets.QTreeWidgetItem(self)
        self._root.setText(0, "Equations")
        self._root.setIcon(0, qta.icon("mdi.equal-box", color="gray"))

        toolbar = ToolBar(self, trailing=True)
        add_equation = toolbar.addAction(
            qta.icon("mdi.plus", color="gray", color_active="white"), "Add Equation"
        )
        add_equation.triggered.connect(self._on_add_equation)
        self.setItemWidget(self._root, 1, toolbar)

    @QtCore.Slot()
    def _on_add_equation(self) -> None:
        equation_name, ok = QtWidgets.QInputDialog.getText(
            self, "New Equation", "Equation name:"
        )
        if not ok or not equation_name.strip():
            return
        self.add_item(equation_name.strip(), "")

    def add_item(self, name: str, expression: str) -> None:
        item = QtWidgets.QTreeWidgetItem(self._root)
        item.setText(0, name)
        item.setText(1, expression)
        item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
        self._root.setExpanded(True)

    def to_dict(self) -> dict[str, str]:
        result: dict[str, str] = {}
        for idx in range(self._root.childCount()):
            child = self._root.child(idx)
            if not child:
                continue
            name = child.text(0).strip()
            expression = child.text(1).strip()
            if name and expression:
                result[name if name.startswith("=") else f"={name}"] = expression
        return result

    def from_dict(self, data: dict[str, typing.Any]) -> None:
        for key, value in data.items():
            name = key[1:] if key.startswith("=") else key
            self.add_item(name, str(value))
