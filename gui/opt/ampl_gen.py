# Filename: gui/opt/ampl_gen.py
# Module: gui.opt.ampl_gen
# Description: Generate AMPL optimization model text from a graph structure

"""
Generate an AMPL optimization model from the exported graph.

This module provides a simplified model generator suitable for testing.
For full production use, port CAT's core/opt/compiler.py (Pyomo-based).
"""

from __future__ import annotations
import typing


def generate_ampl_model(graph: dict) -> str:
    """
    Generate AMPL model text from an exported graph.

    This is a simplified generator that creates a basic linear optimization model
    suitable for material/energy balance problems (e.g., steel pathways).

    Parameters
    ----------
    graph : dict
        Exported graph from Canvas.export_graph() containing:
        - unit_guid: str (unit identifier)
        - nodes: list[dict] with uid, label, x, y
        - edges: list[dict] with uid, source_uid, target_uid

    Returns
    -------
    str : AMPL model text (syntax suitable for solver input)
    """

    nodes = {n["uid"]: n for n in graph.get("nodes", [])}
    edges = graph.get("edges", [])

    # Build AMPL model text
    lines = [
        "# AMPL Model - Generated from iitm-climact graph",
        f"# Unit: {graph.get('unit_guid', 'unknown')}",
        "",
        "# ============================================================",
        "# Sets",
        "# ============================================================",
        "",
        f"set NODES := {' '.join(repr(n['uid']) for n in graph.get('nodes', []))} ;",
        f"set EDGES := {' '.join(repr(e['uid'] for e in edges))} ;",
        "",
        "# ============================================================",
        "# Parameters (Placeholder — would be loaded from DataStore)",
        "# ============================================================",
        "",
        "param node_type {{ node in NODES }} ;  # Type of node (source, process, sink)",
        "param edge_capacity {{ edge in EDGES }} >= 0 ;  # Max flow on edge",
        "param edge_cost {{ edge in EDGES }} >= 0 ;  # Cost per unit flow",
        "",
        "# ============================================================",
        "# Variables",
        "# ============================================================",
        "",
        "var flow {{e in EDGES}} >= 0 ;  # Flow on each edge",
        "var cost ;  # Total cost",
        "",
        "# ============================================================",
        "# Constraints",
        "# ============================================================",
        "",
        "# Mass balance at each node",
        "subject to mass_balance {{n in NODES}} :",
        "    sum {{e in EDGES : e = n}} flow[e]",
        "    = sum {{e in EDGES : e = n}} flow[e] ;  # Placeholder",
        "",
        "# Capacity constraints",
        "subject to edge_capacity_limit {{e in EDGES}} :",
        "    flow[e] <= edge_capacity[e] ;",
        "",
        "# Total cost definition",
        "subject to cost_def :",
        "    cost = sum {{e in EDGES}} edge_cost[e] * flow[e] ;",
        "",
        "# ============================================================",
        "# Objective",
        "# ============================================================",
        "",
        "minimize total_cost : cost ;",
        "",
        "# ============================================================",
        "# Data (empty — must be provided separately or from server)",
        "# ============================================================",
        "",
        "data ;",
        "",
        "# Placeholder: param edge_capacity : .... ;",
        "# Placeholder: param edge_cost : .... ;",
        "",
        "end ;",
    ]

    return "\n".join(lines)


def generate_pyomo_model(graph: dict) -> typing.Any:
    """
    Generate a Pyomo ConcreteModel from an exported graph.

    Supports both single-period (default) and multi-period (time-series) models.
    If parameters with f(t) are provided, creates a time-indexed model.

    Parameters
    ----------
    graph : dict
        Exported graph containing:
        - unit_guid: str
        - nodes: list[dict]
        - edges: list[dict]
        - parameters: dict (optional) — time-series parameters with f(t) lambdas
        - time_range: tuple (optional) — (start_year, end_year) for multi-period

    Returns
    -------
    pyomo.environ.ConcreteModel : Ready to solve
    """

    try:
        import pyomo.environ as pyo
    except ImportError:
        raise ImportError(
            "Pyomo is required for generate_pyomo_model(). "
            "Install with: pip install pyomo[extras]"
        )

    nodes = {n["uid"]: n for n in graph.get("nodes", [])}
    edges = graph.get("edges", [])
    parameters = graph.get("parameters", {})
    time_range = graph.get("time_range", (2025, 2050))

    model = pyo.ConcreteModel(name=graph.get("unit_guid", "optimization"))

    # Sets
    model.NODES = pyo.Set(initialize=list(nodes.keys()))
    model.EDGES = pyo.Set(initialize=[e["uid"] for e in edges])

    # TIME set for multi-period optimization
    start_year, end_year = time_range
    model.TIME = pyo.Set(initialize=list(range(start_year, end_year + 1)))

    # Evaluate all parameters at each time point
    param_values = {}  # {param_path: {time: value}}
    if parameters:
        for param_path, param_def in parameters.items():
            f_t = param_def.get("f_t")
            if callable(f_t):
                param_values[param_path] = {}
                for t in model.TIME:
                    try:
                        param_values[param_path][t] = f_t(t)
                    except Exception:
                        param_values[param_path][t] = 0.0

    # Time-indexed parameters
    if parameters:
        # Capacity: indexed by (time, edge)
        def capacity_init_rule(m, t, e):
            # Find first capacity parameter (heuristic: any path with /+capacity)
            for param_path in param_values:
                if "/+capacity" in param_path:
                    return param_values[param_path].get(t, 100.0)
            return 100.0

        model.capacity = pyo.Param(model.TIME, model.EDGES, initialize=capacity_init_rule, mutable=True)

        # Cost: indexed by (time, edge)
        def cost_init_rule(m, t, e):
            # Find first cost parameter (heuristic: any path with /+cost)
            for param_path in param_values:
                if "/+cost" in param_path:
                    return param_values[param_path].get(t, 1.0)
            return 1.0

        model.cost = pyo.Param(model.TIME, model.EDGES, initialize=cost_init_rule, mutable=True)

        # Variables: time-indexed
        model.flow = pyo.Var(model.TIME, model.EDGES, bounds=(0, None))

        # Objective: minimize total cost over all time periods
        def objective_rule(m):
            return pyo.summation(m.cost, m.flow)

        model.obj = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

        # Constraints: capacity limits for each time period
        def capacity_rule(m, t, e):
            return m.flow[t, e] <= m.capacity[t, e]

        model.capacity_constraint = pyo.Constraint(model.TIME, model.EDGES, rule=capacity_rule)

    else:
        # Single-period model (fallback)
        model.capacity = pyo.Param(model.EDGES, initialize={e["uid"]: 100.0 for e in edges}, mutable=True)
        model.cost = pyo.Param(model.EDGES, initialize={e["uid"]: 1.0 for e in edges}, mutable=True)

        model.flow = pyo.Var(model.EDGES, bounds=(0, None))

        def objective_rule(m):
            return pyo.sum_product(m.cost, m.flow)

        model.obj = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

        def capacity_rule(m, e):
            return m.flow[e] <= m.capacity[e]

        model.capacity_constraint = pyo.Constraint(model.EDGES, rule=capacity_rule)

    return model
