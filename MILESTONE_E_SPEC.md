# Milestone E specification

Milestone E is the final validation and freeze of the 2019–2023 empirical New Harmony engine. It does not introduce a new historical calibration target and it does not force the planner to reproduce observed U.S. gross fixed investment.

## M10 — investment-gap diagnosis and horizon boundary

1. Replay Milestone D exactly.
2. Quantify the difference between planner investment and observed BEA real investment.
3. Compare that gap with observed depreciation and with the observed fixed-asset stock path.
4. Decompose the observed fixed-asset flows by **private/government ownership** and by **equipment, structures, and intellectual-property products (IPP)** using the underlying BEA Fixed Assets tables. The decomposition is diagnostic only; BEA chain-type component volumes are reconciled explicitly to the accepted 71-sector real totals because they are not strictly additive away from the reference year.
5. Preserve the 71-sector gap ranking, including the Housing sector, so the residential contribution remains directly visible without adding Section 5 residential totals a second time.
6. Test whether the last-year zero-investment result is mainly a finite-horizon artifact by appending one stationary shadow continuation year.
7. Adopt the stationary shadow continuation year as the default boundary treatment for future prospective applications. It is a boundary condition, not an observed historical year, and it does not rewrite the accepted 2019–2023 benchmark.

## M11 — robustness and final freeze

Run one-at-a-time perturbations around the accepted D model: initial capital ±10%, depreciation ±10%, FTE availability ±5%, social targets ±5%, and import envelope ±10%, in both Frozen and Historical technology modes. The investment-gap conclusion must survive these perturbations without non-finite solutions or non-positive accepted capital transfers.

A separate maintenance-floor diagnostic forces 0%, 10%, 20%, and 30% of modeled depreciation to be replaced before Harmony-directed additions. This is a sensitivity experiment only; it is not the accepted planner rule.

## M12 — corrected solver integration

1. Preserve `new_harmony_empirical_c.py`, `new_harmony_empirical_d.py`, and the locked Milestone D archive as the legacy replay.
2. Use `new_harmony_empirical_e_corrected.py` as the default Milestone E solver.
3. Start non-terminal investment at zero. Do not introduce the `csvplan.jl` preliminary 70% depreciation-replacement floor.
4. Retain the Milestone E marginal capacity-relief rule: non-terminal capital is added only where an actual cell-level future capacity gap can be relieved with a positive total-Harmony gain.
5. Validate every candidate against flow balance, labour, capital by cell, imports, nonnegative consumption, and inventory feasibility.
6. Search years in ascending Harmony order and select the weakest year for which an admissible correction exists.
7. Replace fixed epsilon with adaptive backtracking, step growth/shrinkage, and an explicit minimum-step stop.
8. Apply the terminal equation `x=(I-A_T-D_T)^-1(qg_T)`, with `D_T=C*delta_T`, and report whether labour, capital, or imports bind.
9. Retain the stationary shadow year and maintenance floors as diagnostics only. The shadow year no longer replaces the terminal equation, and maintenance floors cannot double count terminal replacement.
10. Export product-level Harmony and an annual constraint audit for every corrected run.

## Acceptance interpretation

Milestone E corrected passes if all ten corrected rules are exercised by dedicated tests, the objective is strictly monotone over accepted changes, every accepted final scenario passes the complete constraint audit, and the legacy predecessor remains exactly replayable. Empirical claims must be based on regenerated corrected outputs rather than the previous frozen numerical constants.
