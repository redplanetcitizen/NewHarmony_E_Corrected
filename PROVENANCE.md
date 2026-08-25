# Provenance

Milestone E inherits the empirical model, transformed 71-sector data, and trade/inventory sources from accepted Milestone D. The locked predecessor is `reference/NewHarmony_Milestone_D.zip`, SHA-256 `ad8487f4e37b3d2cc1a89e4bd692f5424a19d4c586fea5345a4b78d1f29a9732`.

Inherited primary sources include:
- BEA Summary Use tables, locked source workbook in `sources/Use_Summary.xlsx`.
- BEA Summary Import Matrices, locked source workbook in `sources/ImportMatrices_Before_Redefinitions_Summary.xlsx`.
- BEA real gross-output, fixed-asset, depreciation, investment, FTE and annual requirements data already transformed and audited in Milestones C/D.

For the final investment-gap diagnosis, Milestone E also exposes the exact BEA Fixed Assets source archive already present in the C/D lineage as `sources/BEA_FixedAssets_Milestone_B.zip`, SHA-256 `09e71560dd27ac6aa9ea9d06b539ae2b1cadab45509e55b23d7171d0131df519`. The diagnostic extracts:
- BEA Section 3 private fixed-asset investment/depreciation and quantity indexes for equipment, structures and intellectual-property products;
- BEA Section 7 government fixed-asset investment/depreciation and quantity indexes for the same three asset classes.

Each component volume is expressed on a 2019-price reference as `current_cost_2019 × quantity_index_t / quantity_index_2019`. BEA chain-type component indexes are not strictly additive away from the reference year, so `ASSET_COMPOSITION_RECONCILIATION.csv` reports the residual against the accepted 71-sector real totals. The maximum annual absolute residual is about 0.176%.

Section 5 residential totals are **not** added to Section 3 private totals: doing so would double count residential private fixed assets already present in the accepted aggregate. The residential contribution remains visible in the accepted 71-sector `Housing` sector diagnostics.

Milestone E uses observed investment and depreciation strictly for ex-post accounting comparison. They do not enter the Harmony objective and are not used to scale or fit planner investment.

The stationary 2024 shadow year is explicitly synthetic: it repeats 2023 target, technology, labour availability and import envelope only to test and correct the terminal boundary in prospective use. It is not represented as observed 2024 data.

## Corrected-solver lineage

The corrected package was derived from the accepted Milestone E without changing any BEA source, transformed empirical input, sector mapping, or locked predecessor archive. The historical modules `new_harmony_empirical_c.py` and `new_harmony_empirical_d.py` are retained for replay. New corrected behavior is isolated in `new_harmony_empirical_e_corrected.py` and selected by default through `new_harmony_empirical_e.py`.

The corrected solver does not use observed investment to determine the plan and does not import the 70% preliminary depreciation-replacement floor from `csvplan.jl`. The only mandatory replacement calculation is the explicit terminal boundary equation; all 0/10/20/30% maintenance floors remain diagnostics.
