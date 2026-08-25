"""M08/M09 overlay primitives for New Harmony Milestone D.

The module is intentionally additive: when imports and inventories are disabled,
callers keep the Milestone-C domestic accounting unchanged.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence
import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]
TOL = 1e-12


def _array(value: object, ndim: int, name: str) -> FloatArray:
    out = np.asarray(value, dtype=np.float64)
    if out.ndim != ndim or not np.all(np.isfinite(out)):
        raise ValueError(f"{name} must be finite and {ndim}D")
    return out


def import_coefficients_from_domestic(
    domestic_A_real: Sequence[Sequence[float]] | FloatArray,
    import_to_domestic_ratio: Sequence[Sequence[float]] | FloatArray,
) -> FloatArray:
    """Create imported-input coefficients compatible with a real domestic A matrix.

    The ratio is dimensionless and comes from same-year nominal BEA Use/Import cells.
    If the same commodity price conversion is applied to imported and domestic use,
    the ratio carries to Milestone C's 2019-price coefficient basis.
    """
    A = _array(domestic_A_real, 2, "domestic_A_real")
    R = _array(import_to_domestic_ratio, 2, "import_to_domestic_ratio")
    if A.shape != R.shape:
        raise ValueError("domestic A and import ratio must have identical shape")
    if np.any(A < -TOL) or np.any(R < -TOL):
        raise ValueError("productive/import coefficients cannot be negative")
    return np.maximum(A, 0.0) * np.maximum(R, 0.0)


def required_imported_intermediates(import_A: FloatArray, domestic_gross_output: Sequence[float] | FloatArray) -> FloatArray:
    A = _array(import_A, 2, "import_A")
    x = _array(domestic_gross_output, 1, "domestic_gross_output")
    if A.shape != (x.size, x.size):
        raise ValueError("import_A must be square and compatible with gross output")
    if np.any(A < -TOL) or np.any(x < -TOL):
        raise ValueError("imports/gross output cannot be negative")
    return A @ x


def final_imports_from_domestic_target(domestic_target_real: Sequence[float] | FloatArray, import_to_domestic_ratio: Sequence[float] | FloatArray) -> FloatArray:
    g = _array(domestic_target_real, 1, "domestic_target_real")
    r = _array(import_to_domestic_ratio, 1, "import_to_domestic_ratio")
    if g.shape != r.shape:
        raise ValueError("target and ratio must have same shape")
    # Final-use import ratios may be signed in national-account adjustments; M08
    # preserves the observed sign rather than clipping it silently.
    return g * r


@dataclass(frozen=True)
class ImportFeasibility:
    required: FloatArray
    available: FloatArray
    slack: FloatArray
    feasible: bool


def check_import_availability(required: Sequence[float] | FloatArray, available: Sequence[float] | FloatArray, tol: float = 1e-10) -> ImportFeasibility:
    req = _array(required, 1, "required")
    cap = _array(available, 1, "available")
    if req.shape != cap.shape:
        raise ValueError("required and available imports must have same shape")
    if np.any(req < -tol) or np.any(cap < -tol):
        raise ValueError("import requirements/caps must be nonnegative")
    slack = cap - req
    return ImportFeasibility(req.copy(), cap.copy(), slack, bool(np.all(slack >= -tol)))


def total_final_availability(domestic_final: Sequence[float] | FloatArray, direct_final_imports: Sequence[float] | FloatArray, inventory_release: Sequence[float] | FloatArray | None = None, inventory_accumulation: Sequence[float] | FloatArray | None = None) -> FloatArray:
    d = _array(domestic_final, 1, "domestic_final")
    m = _array(direct_final_imports, 1, "direct_final_imports")
    if d.shape != m.shape:
        raise ValueError("domestic final and direct imports must have same shape")
    out = d + m
    if inventory_release is not None:
        rel = _array(inventory_release, 1, "inventory_release")
        if rel.shape != d.shape or np.any(rel < -TOL):
            raise ValueError("invalid inventory release")
        out = out + rel
    if inventory_accumulation is not None:
        acc = _array(inventory_accumulation, 1, "inventory_accumulation")
        if acc.shape != d.shape or np.any(acc < -TOL):
            raise ValueError("invalid inventory accumulation")
        out = out - acc
    return out



def inventory_changes_to_base_prices(
    nominal_changes: Sequence[Sequence[float]] | FloatArray,
    price_relatives: Sequence[Sequence[float]] | FloatArray,
) -> FloatArray:
    """Convert F030 flows to a common price basis before constructing a state.

    ``price_relatives[t,i]`` is P[t,i] / P[base,i]. A value of 1 in 2019 and
    1.10 later therefore divides a nominal flow by 1.10 to express it in
    base-year price-volume equivalents.
    """
    d = _array(nominal_changes, 2, "nominal_changes")
    p = _array(price_relatives, 2, "price_relatives")
    if d.shape != p.shape or np.any(p <= 0.0):
        raise ValueError("inventory changes and positive price relatives must have same shape")
    return d / p


def inventory_deviation_path(changes: Sequence[Sequence[float]] | FloatArray, initial: Sequence[float] | FloatArray | None = None) -> FloatArray:
    """M09 observed-flow state: Q[t+1] = Q[t] + DeltaQ[t].

    Q is a deviation from the unknown pre-2019 absolute stock. Negative Q is valid
    in this diagnostic mode; it means cumulative drawdown relative to the baseline.
    """
    delta = _array(changes, 2, "changes")
    q0 = np.zeros(delta.shape[1], dtype=np.float64) if initial is None else _array(initial, 1, "initial")
    if q0.shape != (delta.shape[1],):
        raise ValueError("initial inventory has wrong shape")
    states = np.empty((delta.shape[0] + 1, delta.shape[1]), dtype=np.float64)
    states[0] = q0
    for t in range(delta.shape[0]):
        states[t + 1] = states[t] + delta[t]
    return states


def propagate_endogenous_inventory(accumulation: Sequence[Sequence[float]] | FloatArray, release: Sequence[Sequence[float]] | FloatArray, initial: Sequence[float] | FloatArray | None = None, storage_loss: float = 0.0, tol: float = 1e-10) -> FloatArray:
    """Planner-mode inventory with no borrowing from unknown pre-plan stocks.

    Q[t+1] = (1-loss) Q[t] + accumulation[t] - release[t].
    A negative state is infeasible and raises ValueError.
    """
    a = _array(accumulation, 2, "accumulation")
    r = _array(release, 2, "release")
    if a.shape != r.shape or np.any(a < -tol) or np.any(r < -tol):
        raise ValueError("accumulation/release must be nonnegative and same shape")
    if not 0.0 <= storage_loss < 1.0:
        raise ValueError("storage_loss must be in [0,1)")
    q0 = np.zeros(a.shape[1]) if initial is None else _array(initial, 1, "initial")
    if q0.shape != (a.shape[1],) or np.any(q0 < -tol):
        raise ValueError("invalid initial inventory")
    states = np.empty((a.shape[0] + 1, a.shape[1]), dtype=np.float64)
    states[0] = q0
    for t in range(a.shape[0]):
        states[t + 1] = (1.0-storage_loss)*states[t] + a[t] - r[t]
        if np.any(states[t + 1] < -tol):
            raise ValueError(f"inventory withdrawal exceeds modeled stock at period {t}")
        states[t + 1] = np.maximum(states[t + 1], 0.0)
    return states



@dataclass(frozen=True)
class ExternalSupplyResult:
    domestic_final: FloatArray
    total_final: FloatArray
    imported_final: FloatArray
    imported_intermediate_required: FloatArray


def apply_import_overlay(
    domestic_final: Sequence[float] | FloatArray,
    domestic_gross_output: Sequence[float] | FloatArray,
    import_A: Sequence[Sequence[float]] | FloatArray | None = None,
    direct_final_imports: Sequence[float] | FloatArray | None = None,
    *,
    enabled: bool = True,
) -> ExternalSupplyResult:
    """Apply M08 while guaranteeing an exact no-op when disabled."""
    d = _array(domestic_final, 1, "domestic_final")
    x = _array(domestic_gross_output, 1, "domestic_gross_output")
    if d.shape != x.shape:
        raise ValueError("domestic final and gross output must have same product dimension")
    zeros = np.zeros_like(d)
    if not enabled:
        return ExternalSupplyResult(d.copy(), d.copy(), zeros.copy(), zeros.copy())
    if import_A is None:
        im_req = zeros.copy()
    else:
        im_req = required_imported_intermediates(_array(import_A, 2, "import_A"), x)
    if direct_final_imports is None:
        im_final = zeros.copy()
    else:
        im_final = _array(direct_final_imports, 1, "direct_final_imports")
        if im_final.shape != d.shape:
            raise ValueError("direct final imports have wrong shape")
    return ExternalSupplyResult(d.copy(), d + im_final, im_final.copy(), im_req.copy())


def apply_inventory_overlay(
    base_final: Sequence[float] | FloatArray,
    accumulation: Sequence[float] | FloatArray | None = None,
    release: Sequence[float] | FloatArray | None = None,
    *,
    enabled: bool = True,
) -> FloatArray:
    """Apply one-period M09 final-use effect; disabled mode is an exact no-op."""
    f = _array(base_final, 1, "base_final")
    if not enabled:
        return f.copy()
    a = np.zeros_like(f) if accumulation is None else _array(accumulation, 1, "accumulation")
    r = np.zeros_like(f) if release is None else _array(release, 1, "release")
    if a.shape != f.shape or r.shape != f.shape or np.any(a < -TOL) or np.any(r < -TOL):
        raise ValueError("invalid inventory flow")
    return f - a + r


def projection_fulfillment(final: Sequence[float] | FloatArray, target: Sequence[float] | FloatArray) -> float:
    f = _array(final, 1, "final")
    g = _array(target, 1, "target")
    if f.shape != g.shape or np.any(g < -TOL):
        raise ValueError("invalid final/target")
    den = float(g @ g)
    if den <= 0.0:
        raise ValueError("target ray is zero")
    return float((f @ g) / den)


def harmony_2020(x: float) -> float:
    if not np.isfinite(x) or x <= -1.1:
        raise ValueError("fulfillment outside Harmony domain")
    return float(x / (1.1 + x))


@dataclass(frozen=True)
class InventoryTransfer:
    source_year: int
    destination_year: int
    commodity: int
    amount_at_source: float
    amount_at_destination: float
    mean_harmony_before: float
    mean_harmony_after: float


def best_forward_inventory_transfer(final_by_year: Sequence[Sequence[float]] | FloatArray, targets: Sequence[Sequence[float]] | FloatArray, max_fraction: float = 0.02, storage_loss: float = 0.0, min_gain: float = 1e-12) -> InventoryTransfer | None:
    """One conservative M09 inventory-balancing step.

    It searches only src < dest, never borrows pre-plan inventory, and accepts a
    transfer only if mean intertemporal Harmony rises. The source good is removed
    from current final availability; the surviving amount is released later.
    """
    F = _array(final_by_year, 2, "final_by_year")
    G = _array(targets, 2, "targets")
    if F.shape != G.shape or np.any(F < -TOL) or np.any(G < -TOL):
        raise ValueError("invalid final/targets")
    if not 0.0 < max_fraction <= 1.0 or not 0.0 <= storage_loss < 1.0:
        raise ValueError("invalid transfer parameters")
    T, N = F.shape
    h0 = np.array([harmony_2020(projection_fulfillment(F[t], G[t])) for t in range(T)])
    mean0 = float(np.mean(h0))
    best: InventoryTransfer | None = None
    for src in range(T-1):
        for dest in range(src+1, T):
            survival = (1.0-storage_loss) ** (dest-src)
            if survival <= 0.0:
                continue
            for i in range(N):
                if F[src, i] <= TOL or G[dest, i] <= TOL:
                    continue
                amount = max_fraction * min(F[src, i], G[dest, i])
                if amount <= TOL:
                    continue
                candidate = F.copy()
                candidate[src, i] -= amount
                candidate[dest, i] += amount * survival
                if candidate[src, i] < -TOL:
                    continue
                hs = np.array([harmony_2020(projection_fulfillment(candidate[t], G[t])) for t in range(T)])
                mean1 = float(np.mean(hs))
                if mean1 > mean0 + min_gain and (best is None or mean1 > best.mean_harmony_after):
                    best = InventoryTransfer(src, dest, i, amount, amount*survival, mean0, mean1)
    return best
