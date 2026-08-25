# Changelog - corrected Milestone E

## Solver

- Added `new_harmony_empirical_e_corrected.py` as the default engine.
- Preserved C/D modules and the locked D archive for legacy replay.
- Added product-level Harmony with explicit zero-target handling.
- Added annual flow, labour, cell-capital, import, consumption, and inventory audits.
- Fixed the ineffective infeasibility check caused by testing a production scale after it had been clamped to zero.
- Added weakest-admissible-year selection.
- Added adaptive step backtracking, growth, shrinkage, and minimum-step termination.
- Added the full terminal equation with labour, capital, and import bounds.
- Kept non-terminal investment as marginal capacity relief with no 70% replacement floor.
- Applied the same admissible-year and adaptive-step principles to inventory balancing.

## Outputs

- Added `results/corrected/{mode}/constraint_audit.csv`.
- Added `results/corrected/{mode}/harmony_by_product.csv`.
- Added corrected solver, terminal status, objective history, and step history to run metadata.
- Regenerated baseline, investment-gap, sensitivity, shadow-year, and maintenance-floor outputs.

## Tests

- Replaced the old numerical acceptance suite with 18 corrected tests.
- Archived the previous suite as `tests/legacy_acceptance_snapshot.py`.
- Retained the exact 25-test Milestone D archive replay.

## Empirical revision

- Frozen planned/observed investment: 26.877%.
- Historical planned/observed investment: 27.473%.
- The former 6-7% corrected claim is superseded.
- Terminal replacement is import-limited in both baseline modes.
