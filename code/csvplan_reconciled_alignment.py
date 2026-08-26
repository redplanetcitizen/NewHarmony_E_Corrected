from __future__ import annotations

"""Machine-readable provenance for Milestone E's csvplan reconciliation.

This module does not change the numerical Milestone E solver.  It separates
source-supported rules inherited from the reconciled csvplan reference from
Milestone-E-specific empirical, initialization, search-completion and boundary
choices.
"""

from dataclasses import asdict

import new_harmony_empirical_e_corrected as ec


CSVPLAN_RECONCILED_REPO = "redplanetcitizen/csvplan-corrected"
CSVPLAN_RECONCILED_CHECKPOINT = "ded576c5b8c80d2bbc9fbf3a8a7a391f0a64a433"
MILESTONE_E_PRE_ALIGNMENT = "3faf1657bf0df93906477ed3ba85766406f323ba"


CORE_RULES = {
    "vector_net_output": {
        "status": "source_supported_aligned_core",
        "milestone_e_implementation": "evaluate: produced final output minus full investment vector and inventory accumulation plus releases",
    },
    "robust_harmony": {
        "status": "source_supported_aligned_core",
        "milestone_e_implementation": "minimum Harmony across all products with positive targets",
    },
    "candidate_admissibility": {
        "status": "source_supported_aligned_core",
        "milestone_e_implementation": "post-candidate annual flow/labour/capital/import/consumption/inventory audit",
    },
    "stock_recurrence": {
        "status": "source_supported_aligned_core",
        "milestone_e_implementation": "S_end[t]=S_start[t]*(1-d_t)+I[t]; S_start[t+1]=S_end[t]",
    },
    "source_destination_depreciation": {
        "status": "source_supported_aligned_core",
        "milestone_e_implementation": "cell-specific inverse survival from source to destination",
    },
    "destination_priority": {
        "status": "source_supported_aligned_core",
        "milestone_e_implementation": "lowest annual Harmony is tried first",
    },
    "source_selection": {
        "status": "source_supported_aligned_core",
        "milestone_e_implementation": "earlier source years; retain best admissible positive total-Harmony gain",
    },
    "accepted_gain": {
        "status": "source_supported_aligned_core",
        "milestone_e_implementation": "candidate objective must strictly exceed current total Harmony",
    },
}


MILESTONE_E_EXTENSIONS = {
    "warm_start": {
        "policy": "zero_nonterminal_investment",
        "status": "milestone_e_initialization_choice",
        "historical_csvplan_70_percent_imported": False,
        "interpretation": "zero is an E choice; 70% is a code-only historical csvplan warm start, not a theoretical constant",
    },
    "blocked_destination_completion": {
        "policy": "ranked_fallback_after_uncorrectable_weakest_year",
        "status": "milestone_e_search_extension",
    },
    "capital_update": {
        "policy": "actual_cell_capacity_gap",
        "formula": "max(C*x_desired - S_start, 0)",
        "status": "milestone_e_empirical_extension",
        "note": "not the historical csvplan C26 stock-proportional specialization",
    },
    "step_control": {
        "policy": "adaptive_backtracking_growth_shrink",
        "status": "milestone_e_numerical_extension",
    },
    "terminal_boundary": {
        "policy": "terminal_leontief_replacement_equation",
        "formula": "x=(I-A_T-D_T)^-1(q*g_T)",
        "status": "milestone_e_boundary_extension",
    },
    "shadow_continuation": {
        "policy": "stationary_2024_diagnostic_only",
        "status": "milestone_e_boundary_diagnostic",
    },
    "imports": {
        "policy": "componentwise_empirical_import_envelope",
        "status": "milestone_e_empirical_extension",
    },
    "inventories": {
        "policy": "forward_only_inventory_transfers",
        "status": "milestone_e_empirical_extension",
    },
    "observed_investment": {
        "policy": "ex_post_diagnostic_only",
        "status": "milestone_e_empirical_diagnostic",
    },
}


def provenance(config: ec.SolverConfig | None = None) -> dict:
    """Return the complete alignment contract for one Milestone E run."""
    cfg = config or ec.SolverConfig()
    return {
        "profile": "milestone_e_csvplan_reconciled_alignment",
        "csvplan_reference": {
            "repository": CSVPLAN_RECONCILED_REPO,
            "checkpoint": CSVPLAN_RECONCILED_CHECKPOINT,
        },
        "milestone_e_pre_alignment": MILESTONE_E_PRE_ALIGNMENT,
        "core_rules": CORE_RULES,
        "milestone_e_extensions": MILESTONE_E_EXTENSIONS,
        "numerical_controls": {
            "harmony_cv_threshold": float(cfg.harmony_cv_threshold),
            "max_iterations": int(cfg.max_iterations),
            "initial_step": float(cfg.initial_step),
            "minimum_step": float(cfg.minimum_step),
            "maximum_step": float(cfg.maximum_step),
            "step_growth": float(cfg.step_growth),
            "step_shrink": float(cfg.step_shrink),
            "terminal_replacement": bool(cfg.terminal_replacement),
            "status": "milestone_e_numerical_and_boundary_parameters",
        },
        "solver_config": asdict(cfg),
    }


def validate_contract() -> None:
    """Fail fast if the declared alignment contract becomes internally inconsistent."""
    p = provenance()
    if p["milestone_e_extensions"]["warm_start"]["historical_csvplan_70_percent_imported"]:
        raise AssertionError("Milestone E alignment must not silently import the csvplan 70% warm start")
    expected_core = "source_supported_aligned_core"
    if not all(item["status"] == expected_core for item in p["core_rules"].values()):
        raise AssertionError("all inherited core rules must be explicitly labelled source-supported aligned core")
    if p["milestone_e_extensions"]["capital_update"]["status"] != "milestone_e_empirical_extension":
        raise AssertionError("the E capacity-gap update must remain labelled as an E extension")
    if p["milestone_e_extensions"]["blocked_destination_completion"]["status"] != "milestone_e_search_extension":
        raise AssertionError("ranked fallback must remain labelled as an E completion rule")
