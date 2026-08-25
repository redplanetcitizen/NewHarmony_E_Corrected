from __future__ import annotations

from pathlib import Path
import argparse
import copy
import csv
import json
import numpy as np

import new_harmony_empirical_c as c
import new_harmony_empirical_d as d
import new_harmony_empirical_e_corrected as ec

SENSITIVITY_GRID = [
    ("baseline", "none", 1.00),
    ("initial_capital_-10pct", "capital", 0.90),
    ("initial_capital_+10pct", "capital", 1.10),
    ("depreciation_-10pct", "depreciation", 0.90),
    ("depreciation_+10pct", "depreciation", 1.10),
    ("labour_-5pct", "labour", 0.95),
    ("labour_+5pct", "labour", 1.05),
    ("targets_-5pct", "targets", 0.95),
    ("targets_+5pct", "targets", 1.05),
    ("import_envelope_-10pct", "imports", 0.90),
    ("import_envelope_+10pct", "imports", 1.10),
]

MAINTENANCE_FLOORS = [0.0, 0.10, 0.20, 0.30]


def observed_depreciation(data: c.ModelData, data_dir: Path) -> np.ndarray:
    return np.array([c.read_vector(data_dir / f"depreciation_real_{y}.csv", data.sectors) for y in data.years])


def fixed_asset_composition_diagnostics(data: c.ModelData, data_dir: Path) -> tuple[list[dict], list[dict]]:
    """Decompose observed fixed-asset flows by ownership and asset class.

    The source CSV is extracted from BEA Fixed Assets Section 3 (private) and
    Section 7 (government).  Each component volume is put on a 2019-price
    reference with its own BEA chain-type quantity index.  Because chain-type
    component indexes are not strictly additive away from the reference year,
    the function reports an explicit reconciliation residual against the
    accepted 71-sector real investment/depreciation totals.
    """
    src = data_dir / "fixed_asset_composition_2019_2023.csv"
    with open(src, encoding="utf-8") as f:
        raw = list(csv.DictReader(f))

    component = {}
    current = {}
    for r in raw:
        key = (r["flow"], r["owner"], r["asset_type"])
        component[key] = component.get(key, 0.0) + float(r["real_2019price_component_musd"])
        current[key] = current.get(key, 0.0) + float(r["current_cost_musd"])

    flow_totals = {}
    for (flow, owner, asset), value in component.items():
        flow_totals[flow] = flow_totals.get(flow, 0.0) + value

    headline = []
    for (flow, owner, asset), value in sorted(component.items()):
        headline.append({
            "flow": flow,
            "owner": owner,
            "asset_type": asset,
            "component_real_2019price_5y_musd": value,
            "component_share_of_component_total": value / flow_totals[flow],
            "current_cost_5y_musd": current[(flow, owner, asset)],
        })

    dep = observed_depreciation(data, data_dir)
    reconciliation = []
    for t, y in enumerate(data.years):
        for flow in ("investment", "depreciation"):
            comp = sum(float(r["real_2019price_component_musd"]) for r in raw
                       if r["flow"] == flow and int(r["year"]) == y)
            if flow == "investment":
                accepted = float(data.observed_investment[y].sum())
            else:
                accepted = float(dep[t].sum())
            reconciliation.append({
                "flow": flow,
                "year": y,
                "component_real_2019price_musd": comp,
                "accepted_71sector_real_musd": accepted,
                "component_minus_accepted_musd": comp - accepted,
                "abs_reconciliation_over_accepted": abs(comp - accepted) / accepted if accepted else np.nan,
            })
    return headline, reconciliation


def investment_gap_diagnostics(data: c.ModelData, trade: d.TradeInventoryData,
                               result: d.DSolveResult, data_dir: Path) -> tuple[dict, list[dict], list[dict], list[dict]]:
    """Quantify the investment gap without fitting the plan to observed GFCF.

    Depreciation is used as an accounting scale benchmark, not as an assertion that
    observed gross investment is literally one-for-one replacement expenditure.
    """
    dep_obs = observed_depreciation(data, data_dir)
    planned_by_year = result.final.investments.sum(axis=(1, 2))
    observed_by_year = np.array([data.observed_investment[y].sum() for y in data.years])
    dep_obs_by_year = dep_obs.sum(axis=1)
    observed_net_proxy = observed_by_year - dep_obs_by_year
    model_dep_by_year = np.array([
        (result.final.stock_start[t] * data.dep_by_year[t]).sum() for t in range(len(data.years))
    ])

    annual = []
    for t, y in enumerate(data.years):
        annual.append({
            "technology_mode": data.mode,
            "year": y,
            "planned_investment_real_musd": float(planned_by_year[t]),
            "observed_investment_real_musd": float(observed_by_year[t]),
            "observed_depreciation_real_musd": float(dep_obs_by_year[t]),
            "observed_investment_minus_depreciation_real_musd": float(observed_net_proxy[t]),
            "model_endogenous_depreciation_real_musd": float(model_dep_by_year[t]),
            "planned_over_observed_investment": float(planned_by_year[t] / observed_by_year[t]) if observed_by_year[t] else np.nan,
        })

    planned_total = float(planned_by_year.sum())
    observed_total = float(observed_by_year.sum())
    dep_obs_total = float(dep_obs_by_year.sum())
    gap = observed_total - planned_total
    net_proxy_total = float(observed_net_proxy.sum())
    model_dep_total = float(model_dep_by_year.sum())
    start_stock = float(data.initial_stock.sum())
    model_end_stock = float(result.final.stock_end[-1].sum())
    observed_end_stock = float(data.observed_stock[data.years[-1]].sum())

    headline = {
        "technology_mode": data.mode,
        "planned_investment_5y_real_musd": planned_total,
        "observed_investment_5y_real_musd": observed_total,
        "planned_over_observed": planned_total / observed_total,
        "investment_gap_real_musd": gap,
        "observed_depreciation_5y_real_musd": dep_obs_total,
        "observed_depreciation_over_observed_investment": dep_obs_total / observed_total,
        "observed_depreciation_over_investment_gap": dep_obs_total / gap,
        "observed_investment_minus_depreciation_5y_real_musd": net_proxy_total,
        "planned_over_observed_net_accumulation_proxy": planned_total / net_proxy_total,
        "model_endogenous_depreciation_5y_real_musd": model_dep_total,
        "initial_stock_real_musd": start_stock,
        "model_2023_end_stock_real_musd": model_end_stock,
        "observed_2023_stock_real_musd": observed_end_stock,
        "model_stock_change_2018_2023_real_musd": model_end_stock - start_stock,
        "observed_stock_change_2018_2023_real_musd": observed_end_stock - start_stock,
        "model_2023_stock_over_observed": model_end_stock / observed_end_stock,
        "final_mean_harmony": result.final.mean_harmony,
        "final_cv_harmony": result.final.cv_harmony,
        "capital_transfers": len(result.capital_transfers),
    }

    # Cumulative sector diagnostics are by user-of-capital sector, matching the accepted
    # comparison convention in Milestones C/D (investment tensor summed over source rows).
    plan_sector = result.final.investments.sum(axis=(0, 1))
    obs_sector = np.sum(np.vstack([data.observed_investment[y] for y in data.years]), axis=0)
    dep_sector = dep_obs.sum(axis=0)
    sector_rows = []
    for j, code in enumerate(data.sectors):
        sector_rows.append({
            "technology_mode": data.mode,
            "bea_code": code,
            "sector_name": data.names[code],
            "planned_investment_5y_real_musd": float(plan_sector[j]),
            "observed_investment_5y_real_musd": float(obs_sector[j]),
            "observed_depreciation_5y_real_musd": float(dep_sector[j]),
            "investment_gap_real_musd": float(obs_sector[j] - plan_sector[j]),
            "planned_over_observed": float(plan_sector[j] / obs_sector[j]) if obs_sector[j] > 0 else np.nan,
        })
    sector_rows.sort(key=lambda r: r["investment_gap_real_musd"], reverse=True)

    stock_rows = []
    for t, y in enumerate(data.years):
        stock_rows.append({
            "technology_mode": data.mode,
            "year": y,
            "model_stock_start_real_musd": float(result.final.stock_start[t].sum()),
            "model_investment_real_musd": float(result.final.investments[t].sum()),
            "model_depreciation_real_musd": float(model_dep_by_year[t]),
            "model_stock_end_real_musd": float(result.final.stock_end[t].sum()),
            "observed_stock_end_real_musd": float(data.observed_stock[y].sum()),
        })
    return headline, annual, sector_rows, stock_rows


def apply_sensitivity(data: c.ModelData, trade: d.TradeInventoryData,
                      kind: str, factor: float) -> tuple[c.ModelData, d.TradeInventoryData]:
    md = copy.deepcopy(data)
    tr = copy.deepcopy(trade)
    if kind == "none":
        pass
    elif kind == "capital":
        md.initial_stock *= factor
    elif kind == "depreciation":
        md.dep_by_year = np.clip(md.dep_by_year * factor, 0.0, 0.999999)
    elif kind == "labour":
        md.labour_available *= factor
    elif kind == "targets":
        md.goals *= factor
    elif kind == "imports":
        tr.import_cap_by_year *= factor
    else:
        raise ValueError(f"unknown sensitivity kind: {kind}")
    return md, tr


def run_sensitivity_grid(data: c.ModelData, trade: d.TradeInventoryData,
                         *, legacy_replay: bool = False) -> list[dict]:
    observed_total = float(sum(data.observed_investment[y].sum() for y in data.years))
    rows = []
    for label, kind, factor in SENSITIVITY_GRID:
        md, tr = apply_sensitivity(data, trade, kind, factor)
        # M09 is a zero-transfer module in the accepted backtest. Investment-gap
        # robustness is therefore tested on the M08 capital path to avoid conflating
        # the separate inventory search with the parameter perturbation.
        r = (d.solve_configuration(md, tr, imports_enabled=True, inventories_enabled=False)
             if legacy_replay else
             ec.solve_configuration(md, tr, imports_enabled=True, inventories_enabled=False))
        rows.append({
            "technology_mode": data.mode,
            "scenario": label,
            "parameter": kind,
            "factor": factor,
            "final_mean_harmony": r.final.mean_harmony,
            "final_cv_harmony": r.final.cv_harmony,
            "capital_transfers": len(r.capital_transfers),
            "stop_reason": r.stop_reason_capital,
            "planned_investment_5y_real_musd": float(r.final.investments.sum()),
            "planned_over_observed_investment": float(r.final.investments.sum() / observed_total),
            "stock_2023_over_observed": float(r.final.stock_end[-1].sum() / data.observed_stock[2023].sum()),
            "minimum_production_scale": float(np.min(r.final.production_scale)),
            "max_import_over_cap": float(np.max(np.divide(
                r.final.imported_intermediate_required,
                r.final.imported_intermediate_cap,
                out=np.zeros_like(r.final.imported_intermediate_required),
                where=r.final.imported_intermediate_cap > 1e-12,
            ))),
            "all_transfer_gains_positive": all(x["gain"] > 0 for x in r.capital_transfers),
        })
    return rows


def extend_with_stationary_terminal_year(data: c.ModelData, trade: d.TradeInventoryData,
                                         terminal_year: int = 2024) -> tuple[c.ModelData, d.TradeInventoryData]:
    """Add one diagnostic continuation year by repeating the final observed structure.

    This is deliberately a sensitivity experiment, not a claim about actual 2024 data.
    It detects finite-horizon liquidation pressure: 2023 investment can now benefit the
    shadow continuation year.
    """
    md = copy.deepcopy(data)
    tr = copy.deepcopy(trade)
    md.years = list(md.years) + [terminal_year]
    for attr in ("A_by_year", "L_by_year", "dep_by_year", "goals", "labour_coeff_by_year"):
        arr = getattr(md, attr)
        setattr(md, attr, np.concatenate([arr, arr[-1:]], axis=0))
    md.labour_available = np.r_[md.labour_available, md.labour_available[-1]]
    md.observed_gross[terminal_year] = md.observed_gross[data.years[-1]].copy()
    md.observed_stock[terminal_year] = md.observed_stock[data.years[-1]].copy()
    md.observed_investment[terminal_year] = np.zeros_like(md.observed_investment[data.years[-1]])
    tr.import_A_by_year = np.concatenate([tr.import_A_by_year, tr.import_A_by_year[-1:]], axis=0)
    tr.import_cap_by_year = np.concatenate([tr.import_cap_by_year, tr.import_cap_by_year[-1:]], axis=0)
    z = np.zeros_like(tr.inventory_change_real[-1:])
    tr.inventory_change_real = np.concatenate([tr.inventory_change_real, z], axis=0)
    tr.inventory_flow_envelope = np.concatenate([tr.inventory_flow_envelope, z], axis=0)
    return md, tr


def solve_with_terminal_continuation(data: c.ModelData, trade: d.TradeInventoryData,
                                     *, legacy_replay: bool = False):
    """Prospective boundary rule accepted at Milestone E.

    Add one stationary shadow year so investment in the last reported plan year has a
    productive continuation value. The shadow year is a boundary condition and is not
    reported as an observed historical year.
    """
    md, tr = extend_with_stationary_terminal_year(data, trade)
    result = (d.solve_configuration(md, tr, imports_enabled=True, inventories_enabled=False)
              if legacy_replay else
              ec.solve_configuration(md, tr, imports_enabled=True, inventories_enabled=False))
    return md, tr, result


def terminal_horizon_diagnostic(data: c.ModelData, trade: d.TradeInventoryData,
                                *, legacy_replay: bool = False) -> dict:
    md, tr, r = solve_with_terminal_continuation(data, trade, legacy_replay=legacy_replay)
    observed_total = float(sum(data.observed_investment[y].sum() for y in data.years))
    first5 = float(r.final.investments[:5].sum())
    return {
        "technology_mode": data.mode,
        "diagnostic": "stationary_2024_shadow_year",
        "shadow_year": 2024,
        "shadow_assumption": "repeat 2023 target, technology, labour and import envelope; no claim of observed 2024",
        "six_year_mean_harmony": r.final.mean_harmony,
        "six_year_cv_harmony": r.final.cv_harmony,
        "capital_transfers": len(r.capital_transfers),
        "planned_investment_2019_2023_real_musd": first5,
        "planned_over_observed_2019_2023": first5 / observed_total,
        "investment_2023_real_musd": float(r.final.investments[4].sum()),
        "investment_shadow_2024_real_musd": float(r.final.investments[5].sum()),
        "shadow_2024_fulfillment": float(r.final.feasible_ratio[5]),
        "stock_2023_over_observed": float(r.final.stock_end[4].sum() / data.observed_stock[2023].sum()),
        "all_transfer_gains_positive": all(x["gain"] > 0 for x in r.capital_transfers),
    }


def maintenance_floor_investments(data: c.ModelData, fraction: float) -> np.ndarray:
    """Internal diagnostic: replace a fixed fraction of each modeled depreciation flow.

    This is not the accepted planner policy. It is a controlled experiment that asks
    how a broad, non-targeted replacement rule competes with the Harmony-directed rule.
    """
    T, N = data.goals.shape
    inv = np.zeros((T, N, N), dtype=float)
    stock = data.initial_stock.copy()
    for t in range(T):
        inv[t] = fraction * stock * data.dep_by_year[t]
        stock = stock * (1.0 - data.dep_by_year[t]) + inv[t]
    return inv


def solve_capital_from_initial(data: c.ModelData, trade: d.TradeInventoryData,
                               initial_investments: np.ndarray,
                               *, maxiter: int = 1500,
                               legacy_replay: bool = False):
    if not legacy_replay:
        return ec.solve_capital_from_initial(
            data,
            trade,
            initial_investments,
            config=ec.SolverConfig(max_iterations=maxiter),
        )
    T, N = data.goals.shape
    q = np.zeros((T, T, N), dtype=float)
    current = d.evaluate_d(data, trade, initial_investments, q,
                           imports_enabled=True, inventories_enabled=False)
    for _ in range(maxiter):
        dest = int(np.argmin(current.annual_harmony))
        if dest == 0:
            return current
        desired, current_f, step, _, gap = d.capital_gap_for_harmony_step(
            data, current, dest, d.DEFAULT_EPSILON
        )
        if step <= d.GAIN_TOL or not np.isfinite(gap).all() or gap.sum() <= d.GAIN_TOL:
            return current
        best = None
        for src in range(dest):
            cand = d.inverse_depreciate_gap(gap, data, src, dest)
            if not np.isfinite(cand).all():
                continue
            inv2 = current.investments.copy()
            inv2[src] += cand
            v = d.evaluate_d(data, trade, inv2, q, imports_enabled=True, inventories_enabled=False)
            if np.any(v.imported_intermediate_required - v.imported_intermediate_cap > 1e-7):
                continue
            gain = v.mean_harmony - current.mean_harmony
            if gain > d.GAIN_TOL and (best is None or gain > best[0]):
                best = (gain, v)
        if best is None:
            return current
        current = best[1]
    return current


def maintenance_floor_diagnostic(data: c.ModelData, trade: d.TradeInventoryData,
                                 *, legacy_replay: bool = False) -> list[dict]:
    observed_total = float(sum(data.observed_investment[y].sum() for y in data.years))
    rows = []
    for fraction in MAINTENANCE_FLOORS:
        floor_inv = maintenance_floor_investments(data, fraction)
        if not legacy_replay:
            # The corrected terminal equation determines the last-year replacement.
            # A diagnostic maintenance floor applies only to preceding years, so it
            # cannot double count or override that boundary condition.
            floor_inv[-1] = 0.0
        initial = (d.evaluate_d(data, trade, floor_inv, imports_enabled=True, inventories_enabled=False)
                   if legacy_replay else
                   ec.evaluate(data, trade, floor_inv, imports_enabled=True,
                               inventories_enabled=False, config=ec.SolverConfig()))
        final = solve_capital_from_initial(data, trade, floor_inv, legacy_replay=legacy_replay)
        rows.append({
            "technology_mode": data.mode,
            "replacement_fraction_of_modeled_depreciation": fraction,
            "floor_investment_5y_real_musd": float(initial.investments.sum()),
            "initial_floor_mean_harmony": initial.mean_harmony,
            "final_mean_harmony_after_targeted_additions": final.mean_harmony,
            "final_cv_harmony": final.cv_harmony,
            "total_investment_5y_real_musd": float(final.investments.sum()),
            "total_investment_over_observed": float(final.investments.sum() / observed_total),
            "stock_2023_over_observed": float(final.stock_end[-1].sum() / data.observed_stock[2023].sum()),
            "minimum_production_scale": float(np.min(final.production_scale)),
        })
    return rows


def _write_rows(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def run_all(root: Path, *, legacy_replay: bool = False) -> dict:
    data_dir = root / "data"
    results = root / "results"
    gap_head, gap_annual, gap_sector, stock_path = [], [], [], []
    sensitivity, terminal, maintenance = [], [], []
    baseline = []
    asset_headline = asset_reconciliation = None

    for mode in ("frozen", "historical"):
        data = c.load_model_data(data_dir, mode)
        trade = d.load_trade_inventory(data, data_dir)
        result = (d.solve_configuration(data, trade, imports_enabled=True, inventories_enabled=False)
                  if legacy_replay else
                  ec.solve_configuration(data, trade, imports_enabled=True, inventories_enabled=False))
        output_branch = "legacy_replay" if legacy_replay else "corrected"
        if legacy_replay:
            d.export_result(data, trade, result, results / output_branch / mode,
                            imports_enabled=True, inventories_enabled=False)
        else:
            ec.export_result(data, trade, result, results / output_branch / mode,
                             imports_enabled=True, inventories_enabled=False)

        if asset_headline is None:
            asset_headline, asset_reconciliation = fixed_asset_composition_diagnostics(data, data_dir)

        h, a, s, st = investment_gap_diagnostics(data, trade, result, data_dir)
        gap_head.append(h); gap_annual.extend(a); gap_sector.extend(s); stock_path.extend(st)
        sensitivity.extend(run_sensitivity_grid(data, trade, legacy_replay=legacy_replay))
        terminal.append(terminal_horizon_diagnostic(data, trade, legacy_replay=legacy_replay))
        maintenance.extend(maintenance_floor_diagnostic(data, trade, legacy_replay=legacy_replay))
        baseline.append({
            "technology_mode": mode,
            "final_mean_harmony": result.final.mean_harmony,
            "final_cv_harmony": result.final.cv_harmony,
            "capital_transfers": len(result.capital_transfers),
            "inventory_transfers": len(result.inventory_transfers_log),
            "planned_investment_5y_real_musd": float(result.final.investments.sum()),
            "planned_over_observed_investment": h["planned_over_observed"],
            "stock_2023_over_observed": h["model_2023_stock_over_observed"],
        })

    _write_rows(results / "investment_gap" / "INVESTMENT_GAP_HEADLINE.csv", gap_head)
    _write_rows(results / "investment_gap" / "INVESTMENT_GAP_ANNUAL.csv", gap_annual)
    _write_rows(results / "investment_gap" / "INVESTMENT_GAP_BY_SECTOR.csv", gap_sector)
    _write_rows(results / "investment_gap" / "CAPITAL_STOCK_PATH.csv", stock_path)
    _write_rows(results / "investment_gap" / "ASSET_COMPOSITION_HEADLINE.csv", asset_headline)
    _write_rows(results / "investment_gap" / "ASSET_COMPOSITION_RECONCILIATION.csv", asset_reconciliation)
    _write_rows(results / "robustness" / "SENSITIVITY_RESULTS.csv", sensitivity)
    _write_rows(results / "robustness" / "TERMINAL_HORIZON_DIAGNOSTIC.csv", terminal)
    _write_rows(results / "robustness" / "MAINTENANCE_FLOOR_DIAGNOSTIC.csv", maintenance)
    _write_rows(results / "FINAL_BASELINE.csv", baseline)

    summary = {
        "milestone": "E",
        "solver": "legacy_replay" if legacy_replay else "new_harmony_empirical_e_corrected",
        "replacement_floor": 0.0,
        "status": "ACCEPTED after corrected 18/18 tests and predecessor 25/25 replay",
        "baseline": baseline,
        "investment_gap": gap_head,
        "fixed_asset_composition": asset_headline,
        "fixed_asset_component_reconciliation_max_abs_ratio": max(r["abs_reconciliation_over_accepted"] for r in asset_reconciliation),
        "terminal_horizon": terminal,
        "sensitivity_investment_ratio_range": {
            mode: [
                min(r["planned_over_observed_investment"] for r in sensitivity if r["technology_mode"] == mode),
                max(r["planned_over_observed_investment"] for r in sensitivity if r["technology_mode"] == mode),
            ] for mode in ("frozen", "historical")
        },
        "interpretation": (
            "The Milestone E investment rule remains a marginal capacity-relief rule with no "
            "general 70-percent replacement floor. Numerical conclusions must be read from "
            "the regenerated corrected outputs and acceptance tests."
        ),
    }
    (results / "MILESTONE_E_SUMMARY.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--legacy-replay", action="store_true",
                        help="run the preserved Milestone D/E solver instead of the corrected engine")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    print(json.dumps(run_all(root, legacy_replay=args.legacy_replay), indent=2))
