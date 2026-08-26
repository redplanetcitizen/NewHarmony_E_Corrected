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

## Reconciled csvplan lineage

The source/code audit in `redplanetcitizen/csvplan-corrected` separates three objects that must remain distinct:

1. Cockshott's historical `csvplan.jl` matrix prototype;
2. the exact historical replay `legacy.py`;
3. the source-reconciled reference `reconciled.py`.

Milestone E aligns to the third object only for the source-supported accounting and dynamic core. The reference implementation checkpoint used for this alignment is `ded576c5b8c80d2bbc9fbf3a8a7a391f0a64a433`. The pre-alignment Milestone E baseline is `3faf1657bf0df93906477ed3ba85766406f323ba`.

The inherited reconciled core is:

- vector accounting of final output and investment;
- robust annual Harmony over all positive-target products;
- post-candidate feasibility checks;
- exact stock recurrence;
- exact source-to-destination depreciation;
- lowest-Harmony destination tried first;
- earlier-source search with strictly positive total-Harmony gain.

The historical `csvplan.jl` preliminary 70% replacement schedule is **not** imported. The audit establishes that 70% is a code-only structural warm start/boundary condition, not a theoretical New Harmony constant. Milestone E's zero non-terminal initialization is therefore retained as a **Milestone E initialization choice**, not described as a correction of a theoretically erroneous 70% rule.

## Milestone E extensions beyond the reconciled core

The following behavior belongs to Milestone E and must not be attributed to Cockshott's printed algorithm:

- ranked fallback to a later destination if the current lowest-Harmony year is uncorrectable;
- actual cell-capacity-gap update `max(C*x_desired-S,0)` rather than the historical matrix C26 stock-proportional specialization;
- adaptive step backtracking and growth/shrinkage;
- the terminal equation `(I-A_T-D_T)^-1(qg_T)`;
- componentwise empirical import envelopes;
- forward-only inventory transfers;
- the synthetic 2024 diagnostic continuation.

The detailed rule-by-rule mapping is in `CSVPLAN_RECONCILED_ALIGNMENT.md`. Machine-readable labels are defined in `code/csvplan_reconciled_alignment.py`.

## Replay separation

The historical modules `new_harmony_empirical_c.py` and `new_harmony_empirical_d.py` remain available for replay. New aligned provenance does not rewrite their numerical behavior or the locked Milestone D archive.
