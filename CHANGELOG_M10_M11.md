# Changelog — M10/M11

> Historical pre-correction record. Its acceptance counts and numerical results
> are superseded by `CHANGELOG_CORRECTED.md` and `MILESTONE_E_ACCEPTANCE.md`.

## M10
- Added investment-gap accounting by year and 71-sector user-of-capital sector.
- Added observed-depreciation and fixed-asset stock-path diagnostics.
- Added BEA fixed-asset composition diagnostics by private/government ownership and equipment/structures/IPP.
- Added explicit reconciliation of chain-type component volumes to the accepted 71-sector real totals; maximum annual absolute residual is below 0.2%.
- Retained Housing in the 71-sector gap table rather than adding residential Section 5 totals again, avoiding double counting.
- Added a stationary terminal continuation-year experiment.
- Added `solve_with_terminal_continuation()` as the accepted prospective boundary treatment.
- Preserved the historical 2019–2023 D benchmark without forcing observed investment.

## M11
- Added 22 one-at-a-time robustness runs: 11 scenarios × 2 technology modes.
- Added a controlled 0/10/20/30% depreciation-maintenance diagnostic.
- Added final interpretation and locked acceptance tests.
- Replayed the exact Milestone D archive and its 25-test suite.
- Final Milestone E acceptance suite: 24/24 tests.
