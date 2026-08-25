# Milestone E corrected - conformity audit

## Scope

The corrected engine transfers the ten `csvplan_corrected` rules to the
time-varying 71-sector empirical model. It preserves annual technology,
depreciation, labour, import, and inventory data. It does not import the
five-sector CSV schema and does not introduce the Julia 70% replacement floor.

## Rule-by-rule mapping

| Rule | Implementation | Acceptance evidence |
|---|---|---|
| Consumption net of investment | `evaluate()` recomputes final output from `(I-A_t)x` and subtracts investment and inventory accumulation, adding releases | flow-balance and nonnegative-consumption reports |
| Harmony on positive targets | `fulfillment` and `harmony_by_product` use `goals > tolerance`; zero targets remain `NaN` | zero-target test and product export |
| Exact stock recurrence | `_stock_path()` applies `S_end=S_start*(1-delta_t)+I_t` | differentiated-rate recurrence test |
| Exact inverse depreciation | `inverse_depreciate_gap()` multiplies annual cell survival factors | forward-arrival test |
| Full admissibility | `YearConstraintReport` audits flows, labour, capital, imports, consumption, and inventory | labour-only, capital-cell, and empirical baseline tests |
| Weakest admissible year | `solve_capital()` checks years in ascending Harmony order and continues past uncorrectable years | mocked uncorrectable-weakest-year test |
| Actual capital gap | `_capital_gap_for_scale()` uses `max(C*x-S,0)` | exercised by all empirical transfers |
| Plan-ray scaling | `evaluate()` derives exact linear bounds for fixed final demand plus scaled social targets | flow/resource audits |
| Terminal equation | `terminal_replacement()` solves `(I-A_T-C*delta_T)x=qg_T` and reports labour/capital/import limits | terminal identity and binding-constraint tests |
| Adaptive step | `solve_capital()` and `balance_inventories()` backtrack, grow/shrink the step, and stop at `minimum_step` | backtracking and objective-monotonicity tests |

## Investment policy retained from Milestone E

For years before the terminal boundary, the initial investment tensor is zero.
An accepted addition must satisfy all constraints and increase
`sum_t annual_harmony[t]`. There is no general maintenance investment and no
70% replacement floor. The 0/10/20/30% replacement experiments remain
explicitly non-policy diagnostics.

The terminal equation is a boundary condition required by the corrected
algorithm. It is not extrapolated backward into a general annual floor.

## Replay separation

`new_harmony_empirical_c.py` and `new_harmony_empirical_d.py` remain unchanged.
`solve_configuration(..., legacy_replay=True)` dispatches to the preserved D/E
solver. Corrected runs use `new_harmony_empirical_e_corrected.py` by default.

## Current empirical acceptance

- Frozen: 86 accepted capital transfers, mean Harmony 0.419634659,
  planner/observed investment 26.877%, terminal constraint imports.
- Historical: 74 accepted transfers, mean Harmony 0.419488052,
  planner/observed investment 27.473%, terminal constraint imports.
- Every accepted objective step is strictly positive.
- Every final annual constraint report is compliant.
- Corrected suite: 18/18 tests.
- Locked Milestone D replay: 25/25 tests.
