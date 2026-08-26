# Milestone E corrected - conformity audit

## Scope

The original corrected Milestone E described ten rules as if they were transferred uniformly from `csvplan_corrected`. The completed source/code audit now requires a sharper split.

Milestone E contains a **reconciled csvplan core** plus **Milestone E-specific extensions**. The former is source-supported by the New Harmony text/code reconciliation. The latter may remain valid empirical or numerical design choices, but they must not be represented as recovered Cockshott rules.

The full dependency matrix is `CSVPLAN_RECONCILED_ALIGNMENT.md`.

## Source-supported reconciled core

| Rule | Milestone E implementation | Status |
|---|---|---|
| Consumption net of investment | `evaluate()` recomputes final output from `(I-A_t)x` and subtracts the full investment vector and inventory accumulation, adding releases | **ALIGNED CORE** |
| Harmony on all positive targets | `fulfillment` and `harmony_by_product` use `goals > tolerance`; robust annual Harmony is their minimum | **ALIGNED CORE** |
| Exact stock recurrence | `_stock_path()` applies `S_end=S_start*(1-delta_t)+I_t` and carries end stock into next-year start stock | **ALIGNED CORE** |
| Exact source-to-destination depreciation | `inverse_depreciate_gap()` uses annual cell survival factors between source and destination | **ALIGNED CORE** |
| Candidate-state admissibility | Every proposed transfer is re-evaluated; flow, labour, capital, imports, consumption and inventory must all pass on the candidate | **ALIGNED CORE** |
| Lowest-Harmony first priority | `solve_capital()` orders eligible years by annual Harmony, so the weakest eligible year is tried first | **ALIGNED CORE FOR FIRST CHOICE** |
| Earlier source and positive overall gain | Earlier source years are searched and the best candidate must strictly raise total Harmony | **ALIGNED CORE** |

## Milestone E extensions retained

| Rule | Milestone E implementation | Provenance status |
|---|---|---|
| Zero non-terminal initialization | Initial investment tensor starts at zero before the terminal boundary calculation | **MILESTONE E INITIALIZATION CHOICE** |
| Ranked fallback | If the weakest year is uncorrectable, later years may still be tried in ascending Harmony order | **MILESTONE E SEARCH EXTENSION** |
| Actual capital gap | `_capital_gap_for_scale()` uses `max(C*x-S,0)` | **MILESTONE E EMPIRICAL EXTENSION** |
| Adaptive step | Backtracking plus growth/shrinkage and a minimum-step stop | **MILESTONE E NUMERICAL EXTENSION** |
| Terminal equation | `(I-A_T-C*delta_T)^-1(qg_T)` with explicit labour/capital/import binding report | **MILESTONE E BOUNDARY EXTENSION** |
| Import envelope | Empirical componentwise cap | **MILESTONE E EMPIRICAL EXTENSION** |
| Inventory transfers | Forward-only inventory module | **MILESTONE E EMPIRICAL EXTENSION** |

## Status of the historical 70% schedule

Milestone E continues to use zero non-terminal initialization. No 70% schedule is introduced.

The interpretation changes. The 70% rule in `csvplan.jl` is a code-only historical warm start/boundary condition on which the matrix prototype is materially path-dependent. The value 0.70 is not a theoretical constant. Conversely, zero initialization is not source-derived either; it is a Milestone E modeling choice.

Therefore the correct provenance is:

- `csvplan.jl`: historical 70% matrix warm start;
- reconciled csvplan reference: 70% retained only as a labelled historical demonstration preset, not as theory;
- Milestone E: zero non-terminal initialization, explicitly labelled as an E extension.

## C26 distinction

The reconciled csvplan audit retains the historical stock-proportional C26 rule as a matrix-prototype specialization because no unique multi-good update formula is printed in the available text and tested alternatives do not strictly dominate it on all agreed Harmony metrics.

Milestone E does **not** use that formula. It computes a future physical cell-capacity gap from the empirical `C` matrix and the desired gross-output level. That is retained because it is a deliberate Milestone E empirical construction. It is not called a generic csvplan correction.

## Search-completion distinction

The text-supported first destination is the lowest-Harmony eligible year. Milestone E satisfies that priority. Its further behavior, continuing to the next-lowest year after a failed candidate, is a completion rule specific to E. The csvplan audit showed that such a full-pass completion can find additional improving moves, but it remains our choice rather than a recovered Cockshott step.

## Numerical controls

The CV threshold, maximum iterations and step-control parameters are numerical controls. Their numerical values are not treated as theoretical economic constants. Milestone E keeps its adaptive backtracking because this is part of the empirical solver design, not because it is source-superior to the historical fixed epsilon.

## Replay separation

`new_harmony_empirical_c.py` and `new_harmony_empirical_d.py` remain unchanged. `solve_configuration(..., legacy_replay=True)` continues to dispatch to the preserved predecessor solver. The alignment work does not alter the locked Milestone D archive.

## Baseline status

At the pre-alignment baseline commit `3faf1657bf0df93906477ed3ba85766406f323ba`:

- Frozen: 86 accepted capital transfers, mean Harmony 0.419634659, planner/observed investment 26.877%, terminal constraint imports.
- Historical: 74 accepted transfers, mean Harmony 0.419488052, planner/observed investment 27.473%, terminal constraint imports.
- Every accepted objective step is strictly positive.
- Every final annual constraint report is compliant.
- Corrected suite: 18/18 tests.
- Locked Milestone D replay: 25/25 tests.

The alignment changes the provenance and specification first. Any future numerical change must be introduced as a separately tested E revision and compared against this frozen baseline.