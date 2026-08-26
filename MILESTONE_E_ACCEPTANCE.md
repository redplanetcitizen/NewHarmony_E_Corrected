# Milestone E corrected acceptance

**Status: ACCEPTED - corrected empirical solver; provenance alignment in progress on `align-csvplan-reconciled`**

## Acceptance gates

- The locked Milestone D archive SHA remains exact.
- The predecessor archive replays 25/25 tests.
- The corrected Milestone E suite passes 18/18 tests at the pre-alignment numerical baseline.
- The 2019-2023, 71-sector empirical contract is unchanged.
- `new_harmony_empirical_c.py` and `new_harmony_empirical_d.py` remain available as the legacy replay.
- No historical `csvplan.jl` 70% preliminary warm start is imported into the Milestone E default.
- Non-terminal investment starts at zero. This is now explicitly classified as a **Milestone E initialization choice**, not as a source-derived correction of a theoretically invalid 70% rule.
- Every accepted transfer strictly increases total Harmony.
- Every accepted final scenario passes flow, labour, cell-capital, import, consumption, and inventory checks.
- Product-level Harmony excludes zero targets without division by zero.
- Stock propagation and inverse depreciation use annual cell-specific rates and the exact source-to-destination timing.
- The lowest-Harmony eligible destination is tried first.
- If the weakest year is uncorrectable, Milestone E may continue to later years. This is a **Milestone E search-completion extension** rather than a recovered Cockshott rule.
- The actual cell-capacity-gap update is retained as a **Milestone E empirical extension** rather than attributed to the historical csvplan C26 specialization.
- Adaptive backtracking remains an explicit **Milestone E numerical extension**.
- The last year uses `(I-A_T-D_T)^-1(qg_T)` and reports the binding resource. This is a **Milestone E terminal-boundary extension**.
- The stationary shadow year and 0/10/20/30% maintenance floors remain diagnostics, not accepted replacement rules.
- Observed investment remains excluded from the solver objective and is used only for ex-post comparison.
- `CSVPLAN_RECONCILED_ALIGNMENT.md` and `code/csvplan_reconciled_alignment.py` provide the human-readable and machine-readable provenance split.

## Corrected empirical baseline

The following values are the frozen pre-alignment numerical baseline at commit `3faf1657bf0df93906477ed3ba85766406f323ba`. The provenance alignment does not by itself authorize changing these values.

| Mode | Mean Harmony | CV | Transfers | Planned investment | Planned / observed | 2023 stock / observed |
|---|---:|---:|---:|---:|---:|---:|
| Frozen | 0.419634659 | 0.084806180 | 86 | 6.349 trillion | 26.877% | 78.738% |
| Historical | 0.419488052 | 0.086436382 | 74 | 6.490 trillion | 27.473% | 78.860% |

The terminal year is import-limited in both baseline modes. Its replacement investment is approximately 2.488 trillion Frozen and 2.554 trillion Historical. This is a Milestone E terminal boundary condition, not a general annual maintenance floor and not a generic csvplan rule.

## Robustness

Across the 22 one-at-a-time runs in the accepted baseline, planned investment remains between 22.06% and 30.08% of observed investment in Frozen mode and between 23.85% and 29.53% in Historical mode. All accepted transfer gains remain positive.

The 10-30% maintenance-floor diagnostics raise investment and terminal stock but lower final mean Harmony relative to the zero-floor corrected baseline. They remain sensitivity experiments. They do not establish zero initialization as a source-derived theoretical rule.

## Revised interpretation

The empirical engine does not reproduce observed gross fixed capital formation: at the frozen pre-alignment baseline it selects roughly 27% of the observed total. This describes a normative marginal-capacity planner and cannot be interpreted as a historical investment forecast.

The csvplan reconciliation changes the attribution of several implementation choices. The aligned Milestone E should be described as:

`source-supported reconciled csvplan core + explicit Milestone E empirical/numerical/boundary extensions`.

It should not be described as a literal implementation of Cockshott's matrix prototype, and its zero warm start, ranked fallback, capacity-gap update, adaptive step and terminal equation should not be presented as generic Cockshott corrections.