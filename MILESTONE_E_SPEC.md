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

## M12 — reconciled csvplan core plus Milestone E extensions

The corrected empirical solver is aligned against the adjudicated `csvplan_corrected/reconciled.py` reference. Alignment does **not** mean that every code-only `csvplan.jl` choice is imported, and it does not make Milestone E a five-sector replay. The full rule mapping is recorded in `CSVPLAN_RECONCILED_ALIGNMENT.md`.

### Source-supported core inherited by Milestone E

1. Preserve `new_harmony_empirical_c.py`, `new_harmony_empirical_d.py`, and the locked Milestone D archive as the legacy replay.
2. Use vector final-output accounting: social net output is final output net of the complete investment vector and other productive/stock uses.
3. Compute robust annual Harmony as the minimum across all products with positive targets; zero targets are excluded rather than dropped by positional indexing.
4. Apply the exact stock recurrence `S_end[t] = S_start[t]*(1-d_t) + I[t]` with investment produced in year `t` available at the start of `t+1`.
5. Apply exact cell-specific source-to-destination depreciation for investment shifted from an earlier source year.
6. Re-evaluate every proposed candidate and reject it unless flow balance, labour, capital by cell, imports, nonnegative consumption and inventory feasibility all hold on the candidate state.
7. Give first priority to the lowest-Harmony eligible destination year.
8. Restrict source years to years before the destination and accept only transfers with a strictly positive increase in total Harmony; among admissible earlier sources select the best total-Harmony gain.

### Milestone E-specific choices retained explicitly as extensions

9. Start non-terminal investment at zero. This is a **Milestone E initialization choice**, not a claim that the historical `csvplan.jl` 70% warm start was a theoretically invalid rule. The 70% schedule remains a code-only historical boundary/warm-start device and is not imported into E.
10. Retain the Milestone E marginal capacity-relief update `max(C*x_desired-S,0)`. This is an empirical E extension, not the historical csvplan C26 stock-proportional specialization and not a formula recovered uniquely from Design/Chapter 6.
11. Search destination years in ascending Harmony order. The lowest-Harmony year is always tried first; if it is uncorrectable, E may continue to the next-lowest year. This ranked fallback is a **Milestone E search-completion rule**, not a recovered Cockshott step.
12. Retain adaptive backtracking, step growth/shrinkage and an explicit minimum-step stop. These are Milestone E numerical controls; fixed Julia epsilon and the textual first-suggestion epsilon remain separate historical/textual presets in the csvplan audit.
13. Apply the terminal equation `x=(I-A_T-D_T)^-1(qg_T)`, with `D_T=C*delta_T`, and report whether labour, capital or imports bind. This is a Milestone E boundary extension, not a generic csvplan rule.
14. Retain the stationary shadow year and maintenance floors as diagnostics only. The shadow year no longer replaces the terminal equation, and maintenance floors cannot double count terminal replacement.
15. Retain the empirical import envelope and inventory module as Milestone E extensions. They are not attributed to the five-sector csvplan witness.
16. Export product-level Harmony and an annual constraint audit for every corrected run.
17. Emit or preserve alignment provenance distinguishing the reconciled csvplan core from Milestone E initialization, capital-update, search-completion, step-control, boundary and empirical extensions.

## Acceptance interpretation

Milestone E aligned passes if the source-supported core rules above are exercised by dedicated tests, every Milestone E extension is explicitly provenance-labelled, the objective is strictly monotone over accepted changes, every accepted final scenario passes the complete constraint audit, and the legacy predecessor remains exactly replayable. Empirical claims must be based on regenerated aligned outputs rather than on assumptions that code-only csvplan parameters are theoretical constants.
