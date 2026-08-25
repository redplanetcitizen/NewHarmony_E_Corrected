# Milestone E corrected acceptance

**Status: ACCEPTED - corrected solver**

## Acceptance gates

- The locked Milestone D archive SHA remains exact.
- The predecessor archive replays 25/25 tests.
- The corrected Milestone E suite passes 18/18 tests.
- The 2019-2023, 71-sector empirical contract is unchanged.
- `new_harmony_empirical_c.py` and `new_harmony_empirical_d.py` remain available as the legacy replay.
- There is no 70% preliminary replacement floor in the corrected path.
- Non-terminal investment starts at zero and remains marginal capacity relief.
- Every accepted transfer strictly increases total Harmony.
- Every accepted final scenario passes flow, labour, cell-capital, import, consumption, and inventory checks.
- Product-level Harmony excludes zero targets without division by zero.
- Stock propagation and inverse depreciation use annual cell-specific rates.
- The weakest uncorrectable year no longer terminates the search when a later admissible year exists.
- Adaptive backtracking terminates explicitly at the minimum step when no further improvement is admissible.
- The last year uses `(I-A_T-D_T)^-1(qg_T)` and reports the binding resource.
- The stationary shadow year and 0/10/20/30% maintenance floors remain diagnostics, not accepted replacement rules.
- Observed investment remains excluded from the solver objective and is used only for ex-post comparison.

## Corrected empirical baseline

| Mode | Mean Harmony | CV | Transfers | Planned investment | Planned / observed | 2023 stock / observed |
|---|---:|---:|---:|---:|---:|---:|
| Frozen | 0.419634659 | 0.084806180 | 86 | 6.349 trillion | 26.877% | 78.738% |
| Historical | 0.419488052 | 0.086436382 | 74 | 6.490 trillion | 27.473% | 78.860% |

The terminal year is import-limited in both baseline modes. Its replacement
investment is approximately 2.488 trillion Frozen and 2.554 trillion
Historical. This is a terminal boundary condition, not a general annual
maintenance floor.

## Robustness

Across the 22 one-at-a-time runs, planned investment remains between 22.06%
and 30.08% of observed investment in Frozen mode and between 23.85% and
29.53% in Historical mode. All accepted transfer gains remain positive.

The 10-30% maintenance-floor diagnostics raise investment and terminal stock
but lower final mean Harmony relative to the zero-floor corrected baseline.
They therefore remain sensitivity experiments.

## Revised interpretation

The corrected engine still does not reproduce observed gross fixed capital
formation: it selects roughly 27% of the observed total. The earlier 6-7%
finding is superseded for corrected runs because it omitted the terminal
replacement equation and used a different search procedure.

The result continues to describe a normative marginal-capacity planner. It
does not justify adding the Julia 70% floor, and it cannot be described as a
historical investment forecast.
