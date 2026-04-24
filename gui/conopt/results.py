# Module Name: gui.conopt.results
# Description: Results explorer for optimization runs — table of scenarios with plot viewer.

import json
import re
from PySide6 import QtWidgets, QtCore, QtGui
from gui.widgets import VLayout, GLayout

try:
    import pyqtgraph as pg

    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False


class ResultsWindow(QtWidgets.QFrame):
    """Results explorer with scenario table and decision variable plotter."""

    _runs = []  # class-level: list of {name, info} dicts
    _PATHWAYS = ("BFBOF", "CoalDRI", "NGDRI", "H2DRI")

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = VLayout(self, spacing=0)

        # Create splitter to divide table and explore panel
        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)

        # 1. Scenario table (top pane)
        table = self._init_table()
        splitter.addWidget(table)

        # 2. Explore panel (bottom pane, hidden initially)
        self._explore_panel = self._init_explore_panel()
        self._explore_panel.setVisible(False)
        splitter.addWidget(self._explore_panel)

        # Set splitter proportions: 60% table, 40% explore
        splitter.setSizes([600, 400])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

        self._current_scenario_idx = None

    def _init_table(self) -> QtWidgets.QTableWidget:
        """Create scenario table: [Name | Details | Results | Actions]."""
        table = QtWidgets.QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Scenario Name", "Details", "Results", "Actions"])
        table.horizontalHeader().setStretchLastSection(False)
        table.setColumnWidth(0, 180)
        table.setColumnWidth(2, 200)
        table.setColumnWidth(3, 220)
        table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setWordWrap(True)
        table.verticalHeader().setDefaultSectionSize(60)

        # Make columns resizable (Interactive), Details stretches
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Fixed)

        self._table = table
        self._refresh_table()
        return table

    def _init_explore_panel(self) -> QtWidgets.QFrame:

        panel = QtWidgets.QFrame()
        layout = VLayout(panel, spacing=4)

        # Control bar
        control_bar = QtWidgets.QFrame()
        bar_layout = QtWidgets.QHBoxLayout(control_bar)
        bar_layout.setSpacing(8)
        bar_layout.setContentsMargins(0, 0, 0, 0)

        bar_layout.addWidget(QtWidgets.QLabel("Instance:"))
        self._instance_combo = QtWidgets.QComboBox()
        self._instance_combo.setFixedWidth(200)
        bar_layout.addWidget(self._instance_combo)

        bar_layout.addWidget(QtWidgets.QLabel("Variables:"))
        self._var_combo = QtWidgets.QComboBox()
        self._var_combo.addItems(
            [
                "no_ccus",
                "ccus",
                "total_count",
                "total_steel",
                "total_emissions",
                "total_cost",
                "ccus_penetration",
                "co2_intensity",
                "cost_per_tonne",
            ]
        )
        self._var_combo.setFixedWidth(200)
        bar_layout.addWidget(self._var_combo)

        plot_btn = QtWidgets.QPushButton("Plot")
        plot_btn.clicked.connect(self._on_plot)
        bar_layout.addWidget(plot_btn)

        tabulate_btn = QtWidgets.QPushButton("Tabulate")
        tabulate_btn.clicked.connect(self._on_tabulate)
        bar_layout.addWidget(tabulate_btn)
        bar_layout.addStretch()

        layout.addWidget(control_bar)

        # Plot widget
        if PYQTGRAPH_AVAILABLE:
            self._plot_widget = pg.PlotWidget(title="Decision Variables")
            self._plot_widget.setLabel("left", "Count (plants)")
            self._plot_widget.setLabel("bottom", "Year")
            self._plot_widget.addLegend()
        else:
            self._plot_widget = QtWidgets.QLabel(
                "PyQtGraph not installed. Install with: pip install pyqtgraph"
            )
            self._plot_widget.setStyleSheet("color: red;")

        layout.addWidget(self._plot_widget)

        return panel

    def _refresh_table(self) -> None:
        """Populate table with current runs."""
        self._table.setRowCount(len(self._runs))

        for row, run in enumerate(self._runs):
            # Name column
            name_item = QtWidgets.QTableWidgetItem(run["name"])
            self._table.setItem(row, 0, name_item)

            # Details column (Features enabled/disabled)
            features = run["info"].get("features", {})
            details_text = self._format_details(features)
            details_item = QtWidgets.QTableWidgetItem(details_text)
            details_item.setToolTip(details_text)
            details_item.setTextAlignment(
                QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignLeft
            )
            self._table.setItem(row, 1, details_item)

            # Results column
            info = run["info"]
            total_cost = info.get("total_cost", 0)
            total_emissions = info.get("total_emissions", 0)
            obj_value = info.get("objective_value", 0)
            results_text = (
                f"• Cost:       ₹{total_cost / 1e12:.1f} T\n"
                f"• Emissions:  {total_emissions:.0f} Mt CO₂\n"
                f"• Objective:  {obj_value:.4f}"
            )
            results_item = QtWidgets.QTableWidgetItem(results_text)
            results_item.setTextAlignment(
                QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignLeft
            )
            self._table.setItem(row, 2, results_item)

            # Actions column
            actions_widget = QtWidgets.QFrame()
            actions_layout = QtWidgets.QHBoxLayout(actions_widget)
            actions_layout.setSpacing(4)
            actions_layout.setContentsMargins(0, 0, 0, 0)

            explore_btn = QtWidgets.QPushButton("Explore")
            explore_btn.setFixedWidth(70)
            explore_btn.clicked.connect(lambda checked, r=row: self._on_explore(r))
            actions_layout.addWidget(explore_btn)

            save_btn = QtWidgets.QPushButton("Save")
            save_btn.setFixedWidth(60)
            save_btn.clicked.connect(lambda checked, r=row: self._on_save(r))
            actions_layout.addWidget(save_btn)

            delete_btn = QtWidgets.QPushButton("Delete")
            delete_btn.setFixedWidth(60)
            delete_btn.clicked.connect(lambda checked, r=row: self._on_delete(r))
            actions_layout.addWidget(delete_btn)

            actions_layout.addStretch()
            self._table.setCellWidget(row, 3, actions_widget)

    def _format_details(self, features: dict) -> str:
        """Format feature flags as bullet-point string."""
        if not features:
            return ""

        lines = []
        feature_names = {
            "inflation": "Inflation trajectory",
            "payback": "CCUS payback period",
            "ramp": "Ramp constraints",
            "emissions_cap": "Emissions cap",
        }

        for key, label in feature_names.items():
            enabled = features.get(key, True)
            symbol = "✓" if enabled else "✗"
            lines.append(f"{symbol} {label}")

        return "\n".join(lines)

    def _on_explore(self, row: int) -> None:
        """Show explore panel for a scenario."""
        self._current_scenario_idx = row
        run = self._runs[row]
        counts = run["info"].get("counts", {})

        # Populate instance combobox — use full instance list from server so
        # zero-count instances (e.g. H2DRI) are still available for plotting
        instances = sorted(run["info"].get("instance_names", []))
        if not instances:
            # Fallback: derive from non-zero counts
            for year_data in counts.values():
                instances = sorted(set(instances) | set(year_data.keys()))

        self._instance_combo.clear()
        self._instance_combo.addItem("Global")  # Add fleet-wide pseudo-instance
        self._instance_combo.addItems(instances)

        self._explore_panel.setVisible(True)

    def _ensure_plot_widget(self) -> None:
        """Ensure plot widget exists and replace table if needed."""
        if not isinstance(self._plot_widget, pg.PlotWidget):
            # Replace table with fresh plot widget
            old_widget = self._plot_widget
            self._plot_widget = pg.PlotWidget(title="Decision Variables")
            self._plot_widget.setLabel("left", "Count (plants)")
            self._plot_widget.setLabel("bottom", "Year")
            self._plot_widget.addLegend()
            layout = self._explore_panel.layout()
            layout.removeWidget(old_widget)
            layout.addWidget(self._plot_widget)
            old_widget.setParent(None)
            old_widget.deleteLater()

    def _on_plot(self) -> None:
        """Plot the selected variable (instance counts or aggregates)."""
        if not PYQTGRAPH_AVAILABLE or self._current_scenario_idx is None:
            return

        self._ensure_plot_widget()

        run = self._runs[self._current_scenario_idx]
        variable = self._var_combo.currentText()

        years = []
        values = []

        # Plot aggregate totals or instance-specific counts
        if variable == "total_steel":
            steel = run["info"].get("annual_steel", {})
            for year_str in sorted(steel.keys(), key=lambda x: int(x)):
                years.append(int(year_str))
                values.append(steel[year_str])
            label = "Steel Production (MTPa)"
            color = "steelblue"
        elif variable == "total_emissions":
            emissions = run["info"].get("annual_emissions", {})
            for year_str in sorted(emissions.keys(), key=lambda x: int(x)):
                years.append(int(year_str))
                values.append(emissions[year_str])
            label = "CO₂ (Mt/year)"
            color = "red"
        elif variable == "total_cost":
            cost = run["info"].get("annual_cost", {})
            for year_str in sorted(cost.keys(), key=lambda x: int(x)):
                years.append(int(year_str))
                values.append(cost[year_str])
            label = "Cost (₹ Trillion/year)"
            color = "gold"
        elif variable == "ccus_penetration":
            ccus = run["info"].get("ccus_penetration", {})
            for year_str in sorted(ccus.keys(), key=lambda x: int(x)):
                years.append(int(year_str))
                values.append(ccus[year_str])
            label = "CCUS Penetration (%)"
            color = "purple"
        elif variable == "co2_intensity":
            intensity = run["info"].get("co2_intensity", {})
            for year_str in sorted(intensity.keys(), key=lambda x: int(x)):
                years.append(int(year_str))
                values.append(intensity[year_str])
            label = "CO₂ Intensity (t-CO₂/t-steel)"
            color = "orange"
        elif variable == "cost_per_tonne":
            cpp = run["info"].get("cost_per_tonne", {})
            for year_str in sorted(cpp.keys(), key=lambda x: int(x)):
                years.append(int(year_str))
                values.append(cpp[year_str])
            label = "Cost per Tonne (₹/t-steel)"
            color = "darkgreen"
        elif variable == "total_count":
            counts = run["info"].get("total_count", {})
            for year_str in sorted(counts.keys(), key=lambda x: int(x)):
                years.append(int(year_str))
                values.append(counts[year_str])
            label = "Total Plant Count"
            color = "brown"
        else:
            # Plot instance-specific counts
            instance = self._instance_combo.currentText()
            counts = run["info"].get("counts", {})
            for year_str in sorted(counts.keys(), key=lambda x: int(x)):
                year_data = counts[year_str]
                if instance in year_data:
                    years.append(int(year_str))
                    values.append(year_data[instance].get(variable, 0))
            label = f"{variable} (plants)"
            color = "cyan" if variable == "ccus" else "lime"

        # Clear and plot
        self._plot_widget.clear()
        if years:
            self._plot_widget.plot(
                years, values, pen=pg.mkPen(color, width=2), symbol="o", name=variable
            )
            self._plot_widget.setLabel("bottom", "Year")
            self._plot_widget.setLabel("left", label)

    def _on_tabulate(self) -> None:
        """Show data as a table instead of a plot."""
        if self._current_scenario_idx is None:
            return

        run = self._runs[self._current_scenario_idx]
        variable = self._var_combo.currentText()

        # Determine table headers and rows based on variable type
        headers = []
        rows = []

        if variable == "total_steel":
            headers = ["Year", "Steel Production (MTPa)"]
            steel = run["info"].get("annual_steel", {})
            for year_str in sorted(steel.keys(), key=lambda x: int(x)):
                rows.append([year_str, f"{steel[year_str]:.1f}"])

        elif variable == "total_emissions":
            headers = ["Year", "CO₂ (Mt/year)"]
            emissions = run["info"].get("annual_emissions", {})
            for year_str in sorted(emissions.keys(), key=lambda x: int(x)):
                rows.append([year_str, f"{emissions[year_str]:.2f}"])

        elif variable == "total_cost":
            headers = ["Year", "Cost (₹ Trillion/year)"]
            cost = run["info"].get("annual_cost", {})
            for year_str in sorted(cost.keys(), key=lambda x: int(x)):
                rows.append([year_str, f"{cost[year_str]:.3f}"])

        elif variable == "ccus_penetration":
            headers = ["Year", "CCUS Penetration (%)"]
            ccus = run["info"].get("ccus_penetration", {})
            for year_str in sorted(ccus.keys(), key=lambda x: int(x)):
                rows.append([year_str, f"{ccus[year_str]:.1f}"])

        elif variable == "co2_intensity":
            headers = ["Year", "CO₂ Intensity (t-CO₂/t-steel)"]
            intensity = run["info"].get("co2_intensity", {})
            for year_str in sorted(intensity.keys(), key=lambda x: int(x)):
                rows.append([year_str, f"{intensity[year_str]:.4f}"])

        elif variable == "cost_per_tonne":
            headers = ["Year", "Cost per Tonne (₹/t-steel)"]
            cpp = run["info"].get("cost_per_tonne", {})
            for year_str in sorted(cpp.keys(), key=lambda x: int(x)):
                rows.append([year_str, f"{cpp[year_str]:.0f}"])

        elif variable == "total_count":
            headers = ["Year", "Total Plant Count"]
            counts = run["info"].get("total_count", {})
            for year_str in sorted(counts.keys(), key=lambda x: int(x)):
                rows.append([year_str, f"{counts[year_str]:.0f}"])

        else:
            # Instance-specific or Global data
            instance = self._instance_combo.currentText()

            if instance == "Global":
                # Fleet-wide aggregated metrics - all variables from dropdown
                headers = [
                    "Year",
                    "No-CCUS Plants",
                    "CCUS Plants",
                    "Total Plants",
                    "Steel Production (MTPa)",
                    "BFBOF Share (%)",
                    "CoalDRI Share (%)",
                    "NGDRI Share (%)",
                    "H2DRI Share (%)",
                    "CO₂ Emissions (Mt/yr)",
                    "CO₂ Intensity (t/t)",
                    "Total Cost (₹T/yr)",
                    "Cost per Tonne (₹/t)",
                    "CCUS Penetration (%)",
                ]

                # Get all datasets
                counts_dict = run["info"].get("total_count", {})
                no_ccus_dict = {}
                ccus_dict = {}
                steel = run["info"].get("annual_steel", {})
                emissions = run["info"].get("annual_emissions", {})
                cost = run["info"].get("annual_cost", {})
                intensity = run["info"].get("co2_intensity", {})
                cpp = run["info"].get("cost_per_tonne", {})
                ccus_pct = run["info"].get("ccus_penetration", {})
                pathway_shares = self._pathway_shares_by_year(run["info"])

                # Calculate fleet-wide no_ccus and ccus from counts
                counts_data = run["info"].get("counts", {})
                for year_str, year_data in counts_data.items():
                    fleet_no_ccus = sum(
                        inst.get("no_ccus", 0) for inst in year_data.values()
                    )
                    fleet_ccus = sum(inst.get("ccus", 0) for inst in year_data.values())
                    no_ccus_dict[year_str] = fleet_no_ccus
                    ccus_dict[year_str] = fleet_ccus

                for year_str in sorted(steel.keys(), key=lambda x: int(x)):
                    rows.append(
                        [
                            year_str,
                            f"{no_ccus_dict.get(year_str, 0):.0f}",
                            f"{ccus_dict.get(year_str, 0):.0f}",
                            f"{counts_dict.get(year_str, 0):.0f}",
                            f"{steel.get(year_str, 0):.1f}",
                            f"{pathway_shares.get(year_str, {}).get('BFBOF', 0):.1f}",
                            f"{pathway_shares.get(year_str, {}).get('CoalDRI', 0):.1f}",
                            f"{pathway_shares.get(year_str, {}).get('NGDRI', 0):.1f}",
                            f"{pathway_shares.get(year_str, {}).get('H2DRI', 0):.1f}",
                            f"{emissions.get(year_str, 0):.2f}",
                            f"{intensity.get(year_str, 0):.4f}",
                            f"{cost.get(year_str, 0):.3f}",
                            f"{cpp.get(year_str, 0):.0f}",
                            f"{ccus_pct.get(year_str, 0):.1f}",
                        ]
                    )
            else:
                # Instance-specific: plant counts + calculated metrics
                headers = [
                    "Year",
                    "No-CCUS",
                    "CCUS",
                    "Total",
                    "Steel (MTPa)",
                    "CO₂ (Mt/yr)",
                    "CO₂ Intensity (t/t)",
                    "Cost (₹T/yr)",
                    "Cost/t (₹/t)",
                    "CCUS Pct (%)",
                ]
                counts = run["info"].get("counts", {})

                # Get fleet-level metrics for this instance view
                steel = run["info"].get("annual_steel", {})
                emissions = run["info"].get("annual_emissions", {})
                cost = run["info"].get("annual_cost", {})
                intensity = run["info"].get("co2_intensity", {})
                cpp = run["info"].get("cost_per_tonne", {})

                for year_str in sorted(counts.keys(), key=lambda x: int(x)):
                    year_data = counts[year_str]
                    if instance in year_data:
                        no_ccus = year_data[instance].get("no_ccus", 0)
                        ccus = year_data[instance].get("ccus", 0)
                        total = no_ccus + ccus
                        penetration = (ccus / total * 100) if total > 0 else 0

                        rows.append(
                            [
                                year_str,
                                f"{no_ccus:.1f}",
                                f"{ccus:.1f}",
                                f"{total:.1f}",
                                f"{steel.get(year_str, 0):.1f}",
                                f"{emissions.get(year_str, 0):.2f}",
                                f"{intensity.get(year_str, 0):.4f}",
                                f"{cost.get(year_str, 0):.3f}",
                                f"{cpp.get(year_str, 0):.0f}",
                                f"{penetration:.1f}",
                            ]
                        )

        # Create and populate table widget
        table = QtWidgets.QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(rows))
        table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setStretchLastSection(True)

        for row_idx, row_data in enumerate(rows):
            for col_idx, value in enumerate(row_data):
                item = QtWidgets.QTableWidgetItem(str(value))
                item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                table.setItem(row_idx, col_idx, item)

        table.resizeColumnsToContents()

        # Replace plot widget with table
        old_widget = self._plot_widget
        self._plot_widget = table
        layout = self._explore_panel.layout()
        layout.removeWidget(old_widget)
        layout.addWidget(self._plot_widget)
        old_widget.setParent(None)
        old_widget.deleteLater()

    @classmethod
    def _instance_capacity_mtpa(cls, instance_name: str) -> float:
        match = re.search(r"_(\d+)MTPa_", instance_name)
        return float(match.group(1)) if match else 0.0

    @classmethod
    def _instance_pathway(cls, instance_name: str) -> str | None:
        for pathway in cls._PATHWAYS:
            if pathway.lower() in instance_name.lower():
                return pathway
        return None

    @classmethod
    def _pathway_shares_by_year(cls, info: dict) -> dict[str, dict[str, float]]:
        counts = info.get("counts", {})
        annual_steel = info.get("annual_steel", {})
        shares = {}

        for year_str in annual_steel.keys():
            pathway_steel = {pathway: 0.0 for pathway in cls._PATHWAYS}
            year_data = counts.get(year_str, {})

            for instance_name, instance_data in year_data.items():
                pathway = cls._instance_pathway(instance_name)
                if not pathway:
                    continue

                total_plants = (
                    float(instance_data.get("no_ccus", 0))
                    + float(instance_data.get("ccus", 0))
                )
                pathway_steel[pathway] += (
                    total_plants * cls._instance_capacity_mtpa(instance_name)
                )

            total_steel = sum(pathway_steel.values())
            shares[year_str] = {
                pathway: (value / total_steel * 100) if total_steel > 0 else 0.0
                for pathway, value in pathway_steel.items()
            }

        return shares

    def _on_save(self, row: int) -> None:
        """Save scenario to HDF5 via server."""
        from gui.compat import SysClient
        run = self._runs[row]
        name = run["name"]
        info = run["info"]

        api = SysClient.instance()._api
        project_uid = getattr(api, "project_uid", None)

        if not project_uid:
            QtWidgets.QMessageBox.warning(self, "Save Failed", "No project loaded.")
            return

        try:
            safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in name).strip()
            resp = api.session.post(
                f"{api.base_URL}/projects/{project_uid}/results/{safe_name}",
                json=info,
                headers={"X-Client-ID": api.user_id} if api.user_id else {},
            )
            if resp.status_code == 200:
                QtWidgets.QMessageBox.information(
                    self, "Saved", f"Result '{name}' saved to project."
                )
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Save Failed", f"Server returned {resp.status_code}"
                )
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Save Failed", str(e))

    def _on_delete(self, row: int) -> None:
        """Delete scenario."""
        self._runs.pop(row)
        if self._current_scenario_idx == row:
            self._explore_panel.setVisible(False)
            self._current_scenario_idx = None
        self._refresh_table()

    @classmethod
    def add_run(cls, name: str, info: dict) -> None:
        """Store a new optimization run."""
        cls._runs.append({"name": name, "info": info})

    @classmethod
    def clear_runs(cls) -> None:
        """Clear all cached optimization runs."""
        cls._runs.clear()
