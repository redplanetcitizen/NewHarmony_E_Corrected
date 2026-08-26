# Milestone E alignment with the reconciled csvplan reference

## Scope

This document aligns Milestone E with the source/code adjudication completed in `redplanetcitizen/csvplan-corrected` without converting Milestone E into a five-sector `csvplan` replay.

Reference points:

- Milestone E pre-alignment baseline: `3faf1657bf0df93906477ed3ba85766406f323ba`.
- Historical Cockshott witness: `csvplan.jl`, preserved separately and numerically replayed by `legacy.py` in `csvplan-corrected`.
- Reconciled csvplan implementation checkpoint: `ded576c5b8c80d2bbc9fbf3a8a7a391f0a64a433` in `csvplan-corrected`.

The alignment rule is hierarchical. Source-supported accounting and dynamic identities are inherited. Milestone-E-specific empirical or numerical choices remain permitted, but they must be labelled as Milestone E extensions rather than as recovered Cockshott rules.

## Dependency matrix

| Topic | Reconciled csvplan status | Milestone E implementation | Alignment decision |
|---|---|---|---|
| Net social output | Vector accounting: final output minus investment and productive uses | `evaluate()` computes produced final output and subtracts the full investment vector and inventory accumulation, adding releases | **ALIGNED CORE** |
| Robust annual Harmony | Minimum across all products with positive targets | `evaluate()` excludes zero targets and takes the minimum product Harmony | **ALIGNED CORE** |
| Candidate non-negativity | Check the post-transfer candidate | Every candidate is re-evaluated and rejected unless annual constraint reports are compliant | **ALIGNED CORE** |
| Stock recurrence | Investment produced in year `t` is available at start `t+1`; cell-specific depreciation thereafter | `_stock_path()` uses `S_end[t]=S_start[t]*(1-d_t)+I_t`, `S_start[t+1]=S_end[t]` | **ALIGNED CORE** |
| Source-to-destination depreciation | Mandatory exact survival between source and destination | `inverse_depreciate_gap()` uses cell-specific annual survival factors | **ALIGNED CORE** |
| Destination priority | Lowest-Harmony destination is the source-supported first choice | E orders eligible years by ascending Harmony | **ALIGNED CORE FOR FIRST CHOICE** |
| Blocked lowest-Harmony year | Reconciled reference can preserve historical first-blocked termination; a full ordered pass is a completion rule, not recovered text | E continues to later years if the weakest year has no admissible correction | **MILESTONE E EXTENSION** |
| Source-year selection | Earlier source years; accept only positive overall-Harmony gain and select the best admissible source | E tries all earlier source years and retains the candidate with highest total-Harmony objective | **ALIGNED CORE** |
| C26 additional-capital amount | Historical matrix specialization is `current_stock * scale_increment`; no unique text formula exists | E computes actual future cell-capacity gap `max(C*x-S,0)` | **MILESTONE E EMPIRICAL EXTENSION** |
| Preliminary 70% schedule | Code-only historical warm start/boundary condition; `0.70` is not a theoretical constant | E starts non-terminal investment at zero | **MILESTONE E INITIALIZATION CHOICE**. Zero is not described as a correction of a theoretically wrong 70% rule |
| Step size | Historical fixed epsilon is a code preset; textual epsilon is only a first suggestion | E uses adaptive backtracking with growth/shrinkage and minimum step | **MILESTONE E NUMERICAL EXTENSION** |
| CV threshold | Numerical stopping tolerance, not a theoretical constant | Configurable through `SolverConfig` | **ALIGNED PARAMETER STATUS** |
| Maximum iterations | Computational safeguard | Configurable through `SolverConfig` | **ALIGNED PARAMETER STATUS** |
| Terminal boundary | Reconciled csvplan uses the audited multi-year boundary treatment; no unique terminal equation is recovered from the matrix prototype | E uses `(I-A_T-D_T)^-1(q g_T)` | **MILESTONE E BOUNDARY EXTENSION** |
| Shadow continuation | `repeat_last` is a code-only boundary policy in the matrix prototype | E uses a stationary 2024 continuation only as a diagnostic around the accepted five-year benchmark | **MILESTONE E BOUNDARY DIAGNOSTIC** |
| Imports | Not part of the five-sector csvplan witness | Componentwise empirical import envelope | **MILESTONE E EMPIRICAL EXTENSION** |
| Inventories | Not part of the reconciled csvplan core | Forward-only inventory transfer module | **MILESTONE E EMPIRICAL EXTENSION** |
| Observed BEA investment | Not an optimization target in reconciled csvplan | Ex-post diagnostic only | **MILESTONE E EMPIRICAL DIAGNOSTIC** |

## Consequence for the solver

No 70% preliminary investment schedule is imported into Milestone E. The accepted zero non-terminal initialization is retained, but its provenance changes from an implied correction of `csvplan.jl` to an explicit Milestone E initialization choice.

No numerical change is required for the already aligned core identities listed above. The current E-specific search completion, actual-capacity-gap rule, adaptive step control, terminal equation, imports and inventories remain in place because they are deliberate extensions of the empirical model. They must not be described as direct translations of Design/Chapter 6 or as generic `csvplan` corrections.

## Performance criterion

Harmony remains the objective used by the E search, but alignment decisions are not selected solely by whichever variant yields the highest mean Harmony. Source-supported identities and explicit constraints take precedence. Numerical Harmony comparisons are used only where multiple source-compatible implementation choices remain admissible.

For numerical comparisons the audit continues to record at least:

- mean annual Harmony;
- coefficient of variation of annual Harmony;
- worst annual Harmony;
- total Harmony;
- accepted-transfer count and stop reason;
- full annual constraint compliance.

## Required provenance labels

Every aligned Milestone E run should distinguish at least:

- `csvplan_reconciled_core`: vector accounting, robust all-positive-target Harmony, candidate-state admissibility, exact stock recurrence, exact source-to-destination depreciation, global-lowest-first destination priority, positive overall-Harmony gain;
- `milestone_e_initialization`: zero non-terminal warm start;
- `milestone_e_capital_update`: actual cell-capacity gap;
- `milestone_e_search_completion`: ranked fallback after an uncorrectable weakest year;
- `milestone_e_step_control`: adaptive backtracking;
- `milestone_e_terminal_boundary`: terminal Leontief-plus-replacement equation;
- `milestone_e_empirical_extensions`: imports and inventories.

This provenance split is the alignment target. It preserves the empirical Milestone E architecture without attributing its additional decisions to Cockshott's printed New Harmony algorithm.