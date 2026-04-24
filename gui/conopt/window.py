# Filename: window.py
# Module name: conopt
# Description: Optimization window.

import logging

from PySide6 import QtWidgets, QtCore
from qtawesome import icon as qta_icon

from gui.conopt.objective import ObjectiveSetup
from gui.widgets import VLayout

logger = logging.getLogger(__name__)


class ConOptWindow(QtWidgets.QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = VLayout(self, spacing=4)

        # Objective setup
        self._obj_setup = ObjectiveSetup(self)
        layout.addWidget(self._obj_setup, 1)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)

        gen_btn = QtWidgets.QPushButton("Generate Model")
        gen_btn.setIcon(qta_icon("mdi.function", color="cyan"))
        gen_btn.clicked.connect(self._on_generate)
        button_layout.addWidget(gen_btn)

        run_btn = QtWidgets.QPushButton("Run Optimization")
        run_btn.setIcon(qta_icon("mdi.play", color="lightgreen"))
        run_btn.clicked.connect(self._on_run)
        button_layout.addWidget(run_btn)

        pareto_btn = QtWidgets.QPushButton("Pareto Frontier")
        pareto_btn.setIcon(qta_icon("mdi.chart-scatter-plot", color="gold"))
        pareto_btn.clicked.connect(self._on_pareto)
        button_layout.addWidget(pareto_btn)

        layout.addLayout(button_layout)

    # ------------------------------------------------------------------

    def _solver(self) -> str:
        return self._obj_setup.selected_solver()

    def _objective(self) -> str:
        return self._obj_setup.selected_objective()

    def _alpha(self) -> float:
        return self._obj_setup.alpha()

    def _ramp_up(self) -> int:
        return self._obj_setup.ramp_up()

    def _ramp_down(self) -> int:
        return self._obj_setup.ramp_down()

    def _ramp_ccus(self) -> int:
        return self._obj_setup.ramp_ccus()

    def _inflation_rate(self) -> float:
        return self._obj_setup.inflation_rate()

    def _emissions_factor(self) -> float:
        return self._obj_setup.emissions_factor()

    def _enable_inflation(self) -> bool:
        return self._obj_setup.enable_inflation()

    def _enable_payback(self) -> bool:
        return self._obj_setup.enable_payback()

    def _enable_ramp(self) -> bool:
        return self._obj_setup.enable_ramp()

    def _enable_emissions_cap(self) -> bool:
        return self._obj_setup.enable_emissions_cap()

    def _min_plant_lifetime(self) -> int:
        return self._obj_setup.min_plant_lifetime()

    def _h2dri_learning_rate(self) -> float:
        return self._obj_setup.h2dri_learning_rate()

    def _ccus_learning_rate(self) -> float:
        return self._obj_setup.ccus_learning_rate()

    # ------------------------------------------------------------------

    @QtCore.Slot()
    def _on_generate(self):
        try:
            from gui.compat import SysClient

            api = SysClient.instance()._api
            uid = api.user_id

            resp = api.session.post(
                f"{api.base_URL}/opt/preview",
                json={"objective": self._objective(), "alpha": self._alpha()},
                headers={"X-Client-ID": uid, "Content-Type": "application/json"},
                timeout=30,
            )

            if resp.status_code != 200:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Error",
                    f"Server returned {resp.status_code}:\n{resp.text[:300]}",
                )
                return

            data = resp.json()
            if data.get("status") != "OK":
                QtWidgets.QMessageBox.warning(
                    self, "Error", str(data.get("info", "Unknown error"))
                )
                return

            info = data["info"]
            self._show_preview(info)

        except Exception as exc:
            logger.error(f"Preview failed: {exc}", exc_info=True)
            QtWidgets.QMessageBox.warning(self, "Error", str(exc))

    def _show_preview(self, info: dict):
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Fleet Model Preview")
        dlg.resize(700, 500)
        layout = QtWidgets.QVBoxLayout(dlg)

        # Header stats
        header = (
            f"Objective  : {info['objective']}"
            + (
                f"  (α = {info['alpha']:.2f})"
                if "weighted" in info["objective"]
                else ""
            )
            + f"\nInstances  : {info['instances']}"
            f"\nYears      : {info['years'][0]} – {info['years'][1]}"
            f"\nVariables  : {info['variables']:,}"
            f"\nConstraints: {info['constraints']:,}"
        )
        hdr_label = QtWidgets.QLabel(header)
        hdr_label.setStyleSheet("font-family: monospace; font-size: 12px;")
        layout.addWidget(hdr_label)

        # Instance table
        table = QtWidgets.QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(
            [
                "Instance",
                "Capacity (MTPa)",
                "LCOP (INR/t)",
                "CO₂ w/o CCUS (t/t)",
                "CO₂ w/ CCUS (t/t)",
            ]
        )
        table.horizontalHeader().setStretchLastSection(True)
        table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )

        summary = info.get("summary", [])
        table.setRowCount(len(summary))
        for row, entry in enumerate(summary):
            table.setItem(row, 0, QtWidgets.QTableWidgetItem(entry["instance"]))
            table.setItem(
                row, 1, QtWidgets.QTableWidgetItem(f"{entry['capacity_mtpa']:.0f}")
            )
            table.setItem(
                row, 2, QtWidgets.QTableWidgetItem(f"{entry['lcop_inr_per_t']:,.0f}")
            )
            table.setItem(
                row, 3, QtWidgets.QTableWidgetItem(f"{entry['co2_no_ccus']:.2f}")
            )
            table.setItem(
                row, 4, QtWidgets.QTableWidgetItem(f"{entry['co2_ccus']:.2f}")
            )

        table.resizeColumnsToContents()
        layout.addWidget(table)

        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn)

        dlg.exec()

    @QtCore.Slot()
    def _on_run(self):
        try:
            # 1. Prompt for scenario name
            name, ok = QtWidgets.QInputDialog.getText(
                self,
                "Scenario Name",
                "Enter a label for this optimization:",
            )
            if not ok or not name.strip():
                return

            # 2. Run optimization
            from gui.compat import OptClient

            client = OptClient.instance()

            response = client.solve(
                scenario_name=name.strip(),
                objective=self._objective(),
                solver=self._solver(),
                alpha=self._alpha(),
                ramp_up=self._ramp_up(),
                ramp_down=self._ramp_down(),
                ramp_ccus=self._ramp_ccus(),
                min_plant_lifetime=self._min_plant_lifetime(),
                inflation_rate=self._inflation_rate(),
                emissions_factor=self._emissions_factor(),
                enable_inflation=self._enable_inflation(),
                enable_payback=self._enable_payback(),
                enable_ramp=self._enable_ramp(),
                enable_emissions_cap=self._enable_emissions_cap(),
                h2dri_learning_rate=self._h2dri_learning_rate(),
                ccus_learning_rate=self._ccus_learning_rate(),
            )

            # 3. Handle result
            if response and response.get("status") == "OK":
                info = response.get("info", {})
                logger.info(f"Optimization complete: objective={info.get('objective_value'):.4f}, cost=₹{info.get('total_cost',0)/1e12:.1f}T, emissions={info.get('total_emissions',0):.0f} Mt")

                # Store run and open/reuse Results tab
                from gui.conopt.results import ResultsWindow
                from gui.bus import Relay
                import qtawesome as qta

                ResultsWindow.add_run(name.strip(), info)

                # Check if Results tab already exists; if not, create it
                results_tab = None

                # Walk up widget hierarchy to find TabWidget
                parent = self.parent()
                while parent and not isinstance(parent, QtWidgets.QTabWidget):
                    parent = parent.parent()

                if parent and isinstance(parent, QtWidgets.QTabWidget):
                    # Search for existing Results tab
                    for i in range(parent.count()):
                        if parent.tabText(i) == "Results":
                            results_tab = parent.widget(i)
                            if isinstance(results_tab, ResultsWindow):
                                results_tab._refresh_table()
                                parent.setCurrentWidget(results_tab)
                                break

                if not results_tab:
                    results_win = ResultsWindow(self)
                    icon = qta.icon("mdi.chart-box", color="#fe6d73")
                    bus = Relay.instance()
                    bus.sig_open_widget.emit(results_win, "Results", icon)

                QtWidgets.QMessageBox.information(
                    self,
                    "Optimization Complete",
                    f"Scenario: {name}\n"
                    f"Objective: {info.get('objective_value', 'N/A')}",
                )
            else:
                detail = (
                    response.get("info", "Unknown error") if response else "No response"
                )
                QtWidgets.QMessageBox.warning(self, "Optimization Failed", str(detail))

        except Exception as exc:
            logger.error(f"Optimization failed: {exc}", exc_info=True)
            QtWidgets.QMessageBox.warning(self, "Error", str(exc))

    @QtCore.Slot()
    def _on_pareto(self):
        try:
            from gui.compat import OptClient

            # Confirmation dialog with relax_integers option
            confirm_dlg = QtWidgets.QDialog(self)
            confirm_dlg.setWindowTitle("Pareto Frontier")
            confirm_layout = QtWidgets.QVBoxLayout(confirm_dlg)
            confirm_layout.addWidget(QtWidgets.QLabel(
                "This will run 13 optimization solves (2 anchors + 11 ε-sweep).\n"
                "It may take several minutes."
            ))
            relax_cb = QtWidgets.QCheckBox("Relax integer constraints (LP relaxation — diagnostic)")
            confirm_layout.addWidget(relax_cb)
            btn_box = QtWidgets.QDialogButtonBox(
                QtWidgets.QDialogButtonBox.StandardButton.Ok |
                QtWidgets.QDialogButtonBox.StandardButton.Cancel
            )
            btn_box.accepted.connect(confirm_dlg.accept)
            btn_box.rejected.connect(confirm_dlg.reject)
            confirm_layout.addWidget(btn_box)
            if confirm_dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
                return

            relax_integers = relax_cb.isChecked()

            client = OptClient.instance()
            response = client.pareto(
                solver=self._solver(),
                n_points=31,
                ramp_up=self._ramp_up(),
                ramp_down=self._ramp_down(),
                ramp_ccus=self._ramp_ccus(),
                min_plant_lifetime=self._min_plant_lifetime(),
                inflation_rate=self._inflation_rate(),
                emissions_factor=self._emissions_factor(),
                enable_inflation=self._enable_inflation(),
                enable_payback=self._enable_payback(),
                enable_ramp=self._enable_ramp(),
                enable_emissions_cap=self._enable_emissions_cap(),
                relax_integers=relax_integers,
                h2dri_learning_rate=self._h2dri_learning_rate(),
                ccus_learning_rate=self._ccus_learning_rate(),
            )

            if not response or response.get("status") != "OK":
                detail = response.get("info", "Unknown error") if response else "No response"
                QtWidgets.QMessageBox.warning(self, "Pareto Failed", str(detail))
                return

            self._show_pareto(response["info"])

        except Exception as exc:
            logger.error(f"Pareto frontier failed: {exc}", exc_info=True)
            QtWidgets.QMessageBox.warning(self, "Error", str(exc))

    def _show_pareto(self, info: dict):
        frontier = info.get("frontier", [])
        if not frontier:
            QtWidgets.QMessageBox.information(self, "Pareto", "No feasible points returned.")
            return

        try:
            import pyqtgraph as pg
        except ImportError:
            QtWidgets.QMessageBox.warning(
                self, "Missing Dependency",
                "pyqtgraph is required for Pareto plots.\nInstall with: pip install pyqtgraph",
            )
            return

        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Pareto Frontier — Cost vs. Emissions")
        dlg.resize(720, 540)
        layout = QtWidgets.QVBoxLayout(dlg)

        plot = pg.PlotWidget(background="#2b2b2b")
        plot.setLabel("bottom", "Total Cost (₹ Trillion)")
        plot.setLabel("left", "Cumulative Emissions (Mt CO₂)")
        plot.showGrid(x=True, y=True, alpha=0.3)

        costs = [p["cost"] / 1e12 for p in frontier]
        emissions = [p["emissions"] for p in frontier]

        # Baseline cumulative emissions: 221 Mt/yr × 26 years (no-decarbonization reference)
        baseline_cumulative = 221.0 * 26
        baseline_line = pg.InfiniteLine(
            pos=baseline_cumulative,
            angle=0,
            pen=pg.mkPen(color="white", width=1, style=QtCore.Qt.PenStyle.DashLine),
            label=f"2025 baseline ({baseline_cumulative:.0f} Mt)",
            labelOpts={"color": "white", "position": 0.05},
        )
        plot.addItem(baseline_line)

        # Line connecting frontier points (sorted low-emission → high-emission)
        plot.plot(costs, emissions, pen=pg.mkPen(color="gold", width=2))

        # Scatter points
        scatter = pg.ScatterPlotItem(
            x=costs, y=emissions,
            size=11,
            pen=pg.mkPen("white", width=1),
            brush=pg.mkBrush(100, 180, 255, 200),
        )
        plot.addItem(scatter)

        # ε labels
        for i, pt in enumerate(frontier):
            label = pg.TextItem(f"{pt['emissions']:.0f} Mt", color=(220, 220, 180), anchor=(0.5, 1.3))
            label.setPos(costs[i], emissions[i])
            plot.addItem(label)

        layout.addWidget(plot)

        # Summary table
        table = QtWidgets.QTableWidget(len(frontier), 3)
        table.setHorizontalHeaderLabels(["ε (Mt CO₂ cap)", "Cost (₹T)", "Actual Emissions (Mt)"])
        table.horizontalHeader().setStretchLastSection(True)
        table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setMaximumHeight(160)
        for row, pt in enumerate(frontier):
            table.setItem(row, 0, QtWidgets.QTableWidgetItem(f"{pt['epsilon']:.1f}"))
            table.setItem(row, 1, QtWidgets.QTableWidgetItem(f"{pt['cost']/1e12:.2f}"))
            table.setItem(row, 2, QtWidgets.QTableWidgetItem(f"{pt['emissions']:.1f}"))
        layout.addWidget(table)

        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn)

        dlg.exec()
