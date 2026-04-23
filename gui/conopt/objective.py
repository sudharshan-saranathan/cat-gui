# Filename: objective.py
# Module name: conopt
# Description: Structured objective selector for fleet-level optimization.

from PySide6 import QtWidgets, QtCore
from qtawesome import icon as qta_icon
from gui.widgets import ComboBox, GLayout

# Predefined objectives — keys sent to backend, labels shown to user
OBJECTIVES = {
    "minimize cost": (
        "mdi.currency-usd",
        "lightgreen",
        "Minimize total production cost across all instances and years",
    ),
    "minimize emissions": (
        "mdi.molecule-co2",
        "tomato",
        "Minimize cumulative CO₂ emissions across all instances and years",
    ),
    "minimize weighted": (
        "mdi.scale-balance",
        "gold",
        "Weighted combination of cost and emissions (set α below)",
    ),
}


class ObjectiveSetup(QtWidgets.QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setStyleSheet("background-color: #40474d;")

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(360, 0, 360, 0)
        layout.setSpacing(16)
        layout.addStretch()

        # === 1. OBJECTIVE ===
        obj_label = QtWidgets.QLabel("Objective")
        obj_label.setStyleSheet("font-weight: bold; font-size: 13px; color: white;")
        layout.addWidget(obj_label)
        obj_line = QtWidgets.QFrame()
        obj_line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        obj_line.setStyleSheet("background-color: white; max-height: 1px;")
        layout.addWidget(obj_line)

        self._obj_group = QtWidgets.QButtonGroup(self)
        self._obj_buttons = {}

        for key, (ico, color, tooltip) in OBJECTIVES.items():
            btn = QtWidgets.QRadioButton(
                key.replace("minimize ", "Minimize ")
                .replace("emissions", "Emissions")
                .replace("cost", "Cost")
                .replace("weighted", "Weighted (α·Cost + (1-α)·CO₂)")
            )
            btn.setIcon(qta_icon(ico, color=color))
            btn.setToolTip(tooltip)
            btn.setProperty("objective_key", key)
            self._obj_group.addButton(btn)
            self._obj_buttons[key] = btn
            layout.addWidget(btn)

        self._obj_buttons["minimize cost"].setChecked(True)

        self._weight_frame = QtWidgets.QFrame()
        weight_layout = QtWidgets.QHBoxLayout(self._weight_frame)
        weight_layout.setContentsMargins(24, 0, 0, 0)
        weight_layout.setSpacing(8)

        weight_layout.addWidget(QtWidgets.QLabel("CO₂"))
        self._slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self._slider.setRange(0, 100)
        self._slider.setValue(50)
        self._slider.setFixedWidth(200)
        weight_layout.addWidget(self._slider)
        weight_layout.addWidget(QtWidgets.QLabel("Cost"))

        self._alpha_label = QtWidgets.QLabel("α = 0.50")
        self._alpha_label.setStyleSheet("color: gold;")
        weight_layout.addWidget(self._alpha_label)
        weight_layout.addStretch()

        self._slider.valueChanged.connect(
            lambda v: self._alpha_label.setText(f"α = {v/100:.2f}")
        )
        self._weight_frame.setVisible(False)
        layout.addWidget(self._weight_frame)

        self._obj_buttons["minimize weighted"].toggled.connect(
            self._weight_frame.setVisible
        )

        # === 2. SCENARIO SETTINGS ===
        layout.addSpacing(8)
        scenario_label = QtWidgets.QLabel("Scenario Settings")
        scenario_label.setStyleSheet("font-weight: bold; font-size: 13px; color: white;")
        layout.addWidget(scenario_label)
        scenario_line = QtWidgets.QFrame()
        scenario_line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        scenario_line.setStyleSheet("color: white;")
        layout.addWidget(scenario_line)

        # Feature 1: Inflation trajectory
        inflation_frame = QtWidgets.QFrame()
        inflation_layout = QtWidgets.QHBoxLayout(inflation_frame)
        inflation_layout.setContentsMargins(24, 0, 0, 0)
        inflation_layout.setSpacing(8)
        self._inflation_checkbox = QtWidgets.QCheckBox(
            "Inflation trajectory (Gaussian + box filter)"
        )
        self._inflation_checkbox.setChecked(True)
        inflation_layout.addWidget(self._inflation_checkbox)
        inflation_layout.addStretch()
        inflation_layout.addWidget(QtWidgets.QLabel("Target:"))
        self._inflation_spin = QtWidgets.QDoubleSpinBox()
        self._inflation_spin.setRange(0.0, 15.0)
        self._inflation_spin.setValue(6.0)
        self._inflation_spin.setSuffix("%")
        self._inflation_spin.setDecimals(1)
        self._inflation_spin.setFixedWidth(80)
        inflation_layout.addWidget(self._inflation_spin)
        layout.addWidget(inflation_frame)

        self._inflation_checkbox.toggled.connect(self._inflation_spin.setEnabled)

        # Feature 2: CCUS payback period
        payback_frame = QtWidgets.QFrame()
        payback_layout = QtWidgets.QHBoxLayout(payback_frame)
        payback_layout.setContentsMargins(24, 0, 0, 0)
        payback_layout.setSpacing(8)
        self._payback_checkbox = QtWidgets.QCheckBox("CCUS payback period enforcement")
        self._payback_checkbox.setChecked(True)
        payback_layout.addWidget(self._payback_checkbox)
        payback_layout.addStretch()
        payback_layout.addWidget(QtWidgets.QLabel("(LCOP-based, auto-calculated)"))
        layout.addWidget(payback_frame)

        # Feature 3: Ramp constraints
        ramp_frame = QtWidgets.QFrame()
        ramp_frame_layout = QtWidgets.QVBoxLayout(ramp_frame)
        ramp_frame_layout.setContentsMargins(24, 4, 0, 4)
        ramp_frame_layout.setSpacing(6)
        self._ramp_checkbox = QtWidgets.QCheckBox(
            "Ramp constraints (build/decommission limits)"
        )
        self._ramp_checkbox.setChecked(True)
        ramp_frame_layout.addWidget(self._ramp_checkbox)

        ramp_row1 = QtWidgets.QHBoxLayout()
        ramp_row1.setContentsMargins(24, 0, 0, 0)
        ramp_row1.setSpacing(8)
        ramp_row1.addWidget(QtWidgets.QLabel("Max new plants/year:"))
        self._ramp_up_spin = QtWidgets.QDoubleSpinBox()
        self._ramp_up_spin.setRange(1.0, 20.0)
        self._ramp_up_spin.setValue(3.0)
        self._ramp_up_spin.setDecimals(0)
        self._ramp_up_spin.setFixedWidth(60)
        ramp_row1.addWidget(self._ramp_up_spin)
        ramp_row1.addStretch()
        ramp_frame_layout.addLayout(ramp_row1)

        ramp_row2 = QtWidgets.QHBoxLayout()
        ramp_row2.setContentsMargins(24, 0, 0, 0)
        ramp_row2.setSpacing(8)
        ramp_row2.addWidget(QtWidgets.QLabel("Max decommissions/year:"))
        self._ramp_down_spin = QtWidgets.QDoubleSpinBox()
        self._ramp_down_spin.setRange(1.0, 20.0)
        self._ramp_down_spin.setValue(2.0)
        self._ramp_down_spin.setDecimals(0)
        self._ramp_down_spin.setFixedWidth(60)
        ramp_row2.addWidget(self._ramp_down_spin)
        ramp_row2.addStretch()
        ramp_frame_layout.addLayout(ramp_row2)

        ramp_row3 = QtWidgets.QHBoxLayout()
        ramp_row3.setContentsMargins(24, 0, 0, 0)
        ramp_row3.setSpacing(8)
        ramp_row3.addWidget(QtWidgets.QLabel("Max CCUS retrofits/year:"))
        self._ramp_ccus_spin = QtWidgets.QDoubleSpinBox()
        self._ramp_ccus_spin.setRange(1.0, 20.0)
        self._ramp_ccus_spin.setValue(2.0)
        self._ramp_ccus_spin.setDecimals(0)
        self._ramp_ccus_spin.setFixedWidth(60)
        ramp_row3.addWidget(self._ramp_ccus_spin)
        ramp_row3.addStretch()
        ramp_frame_layout.addLayout(ramp_row3)

        ramp_row4 = QtWidgets.QHBoxLayout()
        ramp_row4.setContentsMargins(24, 0, 0, 0)
        ramp_row4.setSpacing(8)
        ramp_row4.addWidget(QtWidgets.QLabel("Min plant operating lifetime:"))
        self._min_lifetime_spin = QtWidgets.QSpinBox()
        self._min_lifetime_spin.setRange(1, 40)
        self._min_lifetime_spin.setValue(20)
        self._min_lifetime_spin.setSuffix(" yr")
        self._min_lifetime_spin.setFixedWidth(70)
        ramp_row4.addWidget(self._min_lifetime_spin)
        ramp_row4.addStretch()
        ramp_frame_layout.addLayout(ramp_row4)

        layout.addWidget(ramp_frame)

        self._ramp_checkbox.toggled.connect(self._ramp_up_spin.setEnabled)
        self._ramp_checkbox.toggled.connect(self._ramp_down_spin.setEnabled)
        self._ramp_checkbox.toggled.connect(self._ramp_ccus_spin.setEnabled)
        self._ramp_checkbox.toggled.connect(self._min_lifetime_spin.setEnabled)

        # Feature 4: Cumulative emissions cap
        emissions_frame = QtWidgets.QFrame()
        emissions_layout = QtWidgets.QHBoxLayout(emissions_frame)
        emissions_layout.setContentsMargins(24, 0, 0, 0)
        emissions_layout.setSpacing(8)
        self._emissions_cap_checkbox = QtWidgets.QCheckBox("Cumulative emissions cap")
        self._emissions_cap_checkbox.setChecked(True)
        emissions_layout.addWidget(self._emissions_cap_checkbox)
        emissions_layout.addStretch()
        emissions_layout.addWidget(QtWidgets.QLabel("Cumulative cap:"))
        self._emissions_factor_spin = QtWidgets.QDoubleSpinBox()
        self._emissions_factor_spin.setRange(0.1, 2.0)
        self._emissions_factor_spin.setValue(1.2)
        self._emissions_factor_spin.setSingleStep(0.1)
        self._emissions_factor_spin.setDecimals(1)
        self._emissions_factor_spin.setFixedWidth(80)
        emissions_layout.addWidget(self._emissions_factor_spin)
        emissions_layout.addWidget(QtWidgets.QLabel("× baseline"))
        layout.addWidget(emissions_frame)

        self._emissions_cap_checkbox.toggled.connect(self._emissions_factor_spin.setEnabled)

        # === 3. ABATEMENT COST CURVES ===
        layout.addSpacing(8)
        curves_label = QtWidgets.QLabel("Abatement Cost Curves")
        curves_label.setStyleSheet("font-weight: bold; font-size: 13px; color: white;")
        layout.addWidget(curves_label)
        curves_line = QtWidgets.QFrame()
        curves_line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        curves_line.setStyleSheet("color: white;")
        layout.addWidget(curves_line)

        # H2DRI learning rate
        h2_frame = QtWidgets.QFrame()
        h2_layout = QtWidgets.QHBoxLayout(h2_frame)
        h2_layout.setContentsMargins(24, 0, 0, 0)
        h2_layout.setSpacing(8)
        self._h2dri_checkbox = QtWidgets.QCheckBox("H₂DRI cost learning curve")
        self._h2dri_checkbox.setChecked(True)
        self._h2dri_checkbox.setToolTip("Annual decline in H₂DRI LCOP (green hydrogen learning rate)")
        h2_layout.addWidget(self._h2dri_checkbox)
        h2_layout.addStretch()
        h2_layout.addWidget(QtWidgets.QLabel("Rate:"))
        self._h2dri_rate_spin = QtWidgets.QDoubleSpinBox()
        self._h2dri_rate_spin.setRange(0.0, 10.0)
        self._h2dri_rate_spin.setValue(2.8)
        self._h2dri_rate_spin.setSuffix("%/yr")
        self._h2dri_rate_spin.setDecimals(1)
        self._h2dri_rate_spin.setFixedWidth(90)
        self._h2dri_rate_spin.setToolTip("~2.8%/yr → costs halve by 2050")
        h2_layout.addWidget(self._h2dri_rate_spin)
        layout.addWidget(h2_frame)
        self._h2dri_checkbox.toggled.connect(self._h2dri_rate_spin.setEnabled)

        # CCUS learning rate
        ccus_curve_frame = QtWidgets.QFrame()
        ccus_curve_layout = QtWidgets.QHBoxLayout(ccus_curve_frame)
        ccus_curve_layout.setContentsMargins(24, 0, 0, 0)
        ccus_curve_layout.setSpacing(8)
        self._ccus_curve_checkbox = QtWidgets.QCheckBox("CCUS cost learning curve")
        self._ccus_curve_checkbox.setChecked(True)
        self._ccus_curve_checkbox.setToolTip("Annual decline in CCUS retrofit cost (MEA capture learning rate)")
        ccus_curve_layout.addWidget(self._ccus_curve_checkbox)
        ccus_curve_layout.addStretch()
        ccus_curve_layout.addWidget(QtWidgets.QLabel("Rate:"))
        self._ccus_rate_spin = QtWidgets.QDoubleSpinBox()
        self._ccus_rate_spin.setRange(0.0, 10.0)
        self._ccus_rate_spin.setValue(1.4)
        self._ccus_rate_spin.setSuffix("%/yr")
        self._ccus_rate_spin.setDecimals(1)
        self._ccus_rate_spin.setFixedWidth(90)
        self._ccus_rate_spin.setToolTip("~1.4%/yr → costs fall ~30% by 2050")
        ccus_curve_layout.addWidget(self._ccus_rate_spin)
        layout.addWidget(ccus_curve_frame)
        self._ccus_curve_checkbox.toggled.connect(self._ccus_rate_spin.setEnabled)

        # === 4. SOLVER ===
        layout.addSpacing(8)
        solver_label = QtWidgets.QLabel("Solver")
        solver_label.setStyleSheet("font-weight: bold; font-size: 13px; color: white;")
        layout.addWidget(solver_label)
        solver_line = QtWidgets.QFrame()
        solver_line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        solver_line.setStyleSheet("color: white;")
        layout.addWidget(solver_line)

        self.solver_combo = ComboBox(None, editable=False)
        self.solver_combo.addItem(qta_icon("mdi.chart-line"), "HiGHS (Linear/Mixed)")
        self.solver_combo.addItem(qta_icon("mdi.calculator"), "IPOPT (Nonlinear)")
        self.solver_combo.addItem(qta_icon("mdi.alpha-c-box"), "CPLEX (Commercial)")
        self.solver_combo.addItem(qta_icon("mdi.alpha-g-box"), "Gurobi (Commercial)")
        self.solver_combo.setFixedWidth(240)
        layout.addWidget(self.solver_combo)

        layout.addStretch()

    def selected_objective(self) -> str:
        """Return the objective key, e.g. 'minimize cost'."""
        for key, btn in self._obj_buttons.items():
            if btn.isChecked():
                return key
        return "minimize cost"

    def alpha(self) -> float:
        """Return α weight (only meaningful for weighted objective)."""
        return self._slider.value() / 100.0

    def ramp_up(self) -> int:
        """Return max new plants per instance per year."""
        return int(self._ramp_up_spin.value())

    def ramp_down(self) -> int:
        """Return max decommissions per instance per year."""
        return int(self._ramp_down_spin.value())

    def ramp_ccus(self) -> int:
        """Return max CCUS retrofits per instance per year."""
        return int(self._ramp_ccus_spin.value())

    def inflation_rate(self) -> float:
        """Return target inflation rate (as fraction, e.g., 0.06 for 6%)."""
        return self._inflation_spin.value() / 100.0

    def emissions_factor(self) -> float:
        """Return cumulative emissions cap as multiple of baseline (e.g., 1.2)."""
        return self._emissions_factor_spin.value()

    def enable_inflation(self) -> bool:
        """Return whether inflation trajectory is enabled."""
        return self._inflation_checkbox.isChecked()

    def enable_payback(self) -> bool:
        """Return whether CCUS payback period enforcement is enabled."""
        return self._payback_checkbox.isChecked()

    def enable_ramp(self) -> bool:
        """Return whether ramp constraints are enabled."""
        return self._ramp_checkbox.isChecked()

    def enable_emissions_cap(self) -> bool:
        """Return whether cumulative emissions cap is enabled."""
        return self._emissions_cap_checkbox.isChecked()

    def h2dri_learning_rate(self) -> float:
        """Return H2DRI annual cost learning rate as fraction (e.g. 0.028)."""
        if not self._h2dri_checkbox.isChecked():
            return 0.0
        return self._h2dri_rate_spin.value() / 100.0

    def ccus_learning_rate(self) -> float:
        """Return CCUS annual cost learning rate as fraction (e.g. 0.014)."""
        if not self._ccus_curve_checkbox.isChecked():
            return 0.0
        return self._ccus_rate_spin.value() / 100.0

    def min_plant_lifetime(self) -> int:
        """Return minimum contiguous plant operating lifetime in years."""
        return self._min_lifetime_spin.value()

    def selected_solver(self) -> str:
        solver_map = {
            "HiGHS (Linear/Mixed)": "highs",
            "IPOPT (Nonlinear)": "ipopt",
            "CPLEX (Commercial)": "cplex",
            "Gurobi (Commercial)": "gurobi",
        }
        return solver_map.get(self.solver_combo.currentText(), "highs")
