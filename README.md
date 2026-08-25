# New Harmony - Milestone E Corrected

This package updates the empirical 71-sector U.S. New Harmony engine so that it
incorporates the ten corrections implemented in `csvplan_corrected`, while
preserving Milestones C/D as an exact historical replay.

The accepted investment rule remains **marginal capacity relief**. The solver
starts with zero non-terminal investment and adds capital only where a future
capacity gap can be relieved while increasing total Harmony. It does **not**
apply the 70% preliminary depreciation-replacement floor found in `csvplan.jl`.

## Corrected baseline, 2019-2023

| Mode | Mean Harmony | CV | Capital transfers | Planner / observed investment | 2023 model / observed stock |
|---|---:|---:|---:|---:|---:|
| Frozen | 0.419634659 | 0.084806180 | 86 | 26.877% | 78.738% |
| Historical | 0.419488052 | 0.086436382 | 74 | 27.473% | 78.860% |

The larger investment total relative to the previous Milestone E is caused
primarily by the corrected terminal equation, not by a general replacement
floor. Non-terminal investment remains targeted to demonstrated capital gaps.

All accepted transfers increase the sum of annual Harmonies. Every accepted
scenario passes explicit flow-balance, labour, cell-level capital, import,
nonnegative-consumption, and inventory checks.

## Corrected rules

The new engine provides:

1. explicit separation of consumption and investment;
2. product-level Harmony for positive targets only;
3. exact annual stock recurrence;
4. cell-specific inverse depreciation;
5. complete candidate admissibility reports;
6. selection of the weakest year that has an admissible correction;
7. capital additions computed from actual cell-level capacity gaps;
8. exact plan-ray scaling under capital, labour, and import limits;
9. the terminal equation `x=(I-A-D)^-1(qg)` with the binding constraint reported;
10. adaptive step size with backtracking and a minimum-step stop.

For the empirical baseline, the terminal year is import-limited in both Frozen
and Historical modes. This is reported explicitly in the run metadata.

## Boundary and maintenance diagnostics

The stationary 2024 shadow year remains available as an alternative boundary
diagnostic. In the corrected engine it no longer substitutes for the terminal
equation: the synthetic 2024 year receives its own terminal replacement, while
2023 can receive targeted investment for 2024.

The 0%, 10%, 20%, and 30% maintenance-floor experiments remain diagnostics.
They are not part of the accepted investment rule. The final-year investment in
those experiments is always determined by the terminal equation, preventing
double counting.

## Running the package

From the package root:

```text
python -B code/new_harmony_empirical_e.py
```

To replay the preserved legacy engine instead:

```text
python -B code/new_harmony_empirical_e.py --legacy-replay
```

Run the corrected acceptance suite with:

```text
python -B -m unittest -q tests.test_milestone_e
```

## Main files

- `code/new_harmony_empirical_e_corrected.py` - corrected solver.
- `code/new_harmony_empirical_e.py` - empirical diagnostics and command entry point.
- `code/new_harmony_empirical_c.py` and `code/new_harmony_empirical_d.py` - unchanged replay engines.
- `tests/test_milestone_e.py` - corrected acceptance suite.
- `tests/legacy_acceptance_snapshot.py` - archived previous E acceptance suite.
- `results/corrected/` - annual paths, constraint audits, product Harmonies, and metadata.
- `results/investment_gap/` - corrected investment and stock comparison.
- `results/robustness/` - regenerated sensitivities and boundary diagnostics.
- `CORRECTIONS_AUDIT.md` - mapping of all ten corrections to code and tests.
- `FINAL_MODEL_INTERPRETATION.md` - revised empirical interpretation.

Raw BEA data, the 71-sector mapping, Frozen/Historical technology modes, the
fixed-asset decomposition, and the locked Milestone D archive are unchanged.
