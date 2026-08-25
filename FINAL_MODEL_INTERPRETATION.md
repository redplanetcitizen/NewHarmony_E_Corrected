# Final empirical interpretation - Milestone E corrected

The corrected 2019-2023 New Harmony engine remains a normative planner rather
than a predictor of historical gross fixed capital formation. It adds
non-terminal capital only when a cell-level capacity gap can be relieved by an
earlier investment that raises total Harmony. It does not apply the 70%
preliminary depreciation-replacement floor used by `csvplan.jl`.

The corrected terminal equation changes the quantitative result materially.
Observed real investment is 23.623 trillion 2019-price dollars. The corrected
planner selects 6.349 trillion in Frozen mode and 6.490 trillion in Historical
mode, respectively 26.88% and 27.47% of observed investment. The corresponding
gaps are 17.274 and 17.133 trillion.

Observed depreciation over the period is 18.510 trillion. It is slightly larger
than the corrected observed-minus-planned gap. Planned investment also exceeds
the simple observed investment-minus-depreciation proxy. These comparisons do
not turn the solver into a historical calibration: observed investment and
depreciation do not enter its objective or candidate selection.

The planner begins with 64.245 trillion of real fixed assets and ends 2023 with
54.482 trillion Frozen and 54.566 trillion Historical. These totals are 78.74%
and 78.86% of observed 2023 stock. Non-binding capital is still allowed to run
down; the corrected boundary merely prevents the last year from being treated
as if depreciation after production had no planning consequence.

The last-year equation is constrained by the import envelope in both baseline
modes. Terminal replacement is approximately 2.488 trillion Frozen and 2.554
trillion Historical. This investment is calculated from
`(I-A_T-D_T)^-1(qg_T)` and is confined to the terminal boundary. It is not a
70% floor and is not imposed indiscriminately in earlier years.

The stationary 2024 shadow year now has a different interpretation. Because
the corrected terminal equation already operates in the last modeled year,
adding 2024 moves that terminal replacement to the synthetic year and lets
2023 acquire productive value for 2024. First-five-year investment becomes
22.44% of observed investment Frozen and 24.63% Historical. The shadow-year
experiment is therefore an alternative boundary placement, not the sole repair
for terminal liquidation.

The one-at-a-time robustness grid preserves the qualitative conclusion.
Planner investment ranges from 22.06% to 30.08% of observed investment in
Frozen mode and from 23.85% to 29.53% in Historical mode. The solution remains
well below historical GFCF without a general replacement floor.

Maintenance-floor experiments remain informative but non-normative. Forcing
10-30% replacement before targeted additions raises total investment and
terminal stock, while lowering final mean Harmony relative to the corrected
zero-floor baseline. The final year in these experiments is determined by the
terminal equation, so the diagnostic floor cannot double count terminal
replacement.

The fixed-asset composition evidence is unchanged: observed investment is
broadly distributed across equipment, structures, intellectual-property
products, private ownership, and government ownership. The remaining gap
cannot be attributed to the omission of one conventional asset class.

The corrected conclusion is narrower than the previous freeze. New Harmony
continues to select productive sufficiency along the plan ray rather than the
historical capital path, but the former 6-7% investment ratio is not robust to
the corrected terminal accounting and is superseded. The accepted corrected
benchmark is approximately 27%, with complete resource audits and strictly
monotone accepted Harmony gains.
