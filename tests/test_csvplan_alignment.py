from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))

import csvplan_reconciled_alignment as alignment
import new_harmony_empirical_e_corrected as ec


class CsvplanReconciledAlignmentTests(unittest.TestCase):
    def test_alignment_contract_is_internally_consistent(self):
        alignment.validate_contract()

    def test_reference_checkpoint_and_pre_alignment_baseline_are_pinned(self):
        self.assertEqual(
            alignment.CSVPLAN_RECONCILED_CHECKPOINT,
            "ded576c5b8c80d2bbc9fbf3a8a7a391f0a64a433",
        )
        self.assertEqual(
            alignment.MILESTONE_E_PRE_ALIGNMENT,
            "3faf1657bf0df93906477ed3ba85766406f323ba",
        )

    def test_all_reconciled_core_rules_are_explicitly_source_supported(self):
        self.assertTrue(alignment.CORE_RULES)
        self.assertTrue(
            all(
                rule["status"] == "source_supported_aligned_core"
                for rule in alignment.CORE_RULES.values()
            )
        )
        for required in (
            "vector_net_output",
            "robust_harmony",
            "candidate_admissibility",
            "stock_recurrence",
            "source_destination_depreciation",
            "destination_priority",
            "source_selection",
            "accepted_gain",
        ):
            self.assertIn(required, alignment.CORE_RULES)

    def test_zero_warm_start_is_labelled_as_milestone_e_choice(self):
        warm = alignment.MILESTONE_E_EXTENSIONS["warm_start"]
        self.assertEqual(warm["policy"], "zero_nonterminal_investment")
        self.assertEqual(warm["status"], "milestone_e_initialization_choice")
        self.assertFalse(warm["historical_csvplan_70_percent_imported"])

    def test_ranked_fallback_is_not_misattributed_to_cockshott(self):
        item = alignment.MILESTONE_E_EXTENSIONS["blocked_destination_completion"]
        self.assertEqual(item["policy"], "ranked_fallback_after_uncorrectable_weakest_year")
        self.assertEqual(item["status"], "milestone_e_search_extension")

    def test_capacity_gap_c26_is_labelled_as_empirical_extension(self):
        item = alignment.MILESTONE_E_EXTENSIONS["capital_update"]
        self.assertEqual(item["policy"], "actual_cell_capacity_gap")
        self.assertEqual(item["status"], "milestone_e_empirical_extension")
        self.assertIn("C*x_desired", item["formula"])

    def test_adaptive_step_and_terminal_equation_are_e_extensions(self):
        step = alignment.MILESTONE_E_EXTENSIONS["step_control"]
        terminal = alignment.MILESTONE_E_EXTENSIONS["terminal_boundary"]
        self.assertEqual(step["status"], "milestone_e_numerical_extension")
        self.assertEqual(terminal["status"], "milestone_e_boundary_extension")

    def test_numerical_controls_are_emitted_from_solver_config(self):
        cfg = ec.SolverConfig(
            harmony_cv_threshold=0.05,
            max_iterations=123,
            initial_step=0.2,
            minimum_step=1e-4,
            maximum_step=0.4,
            step_growth=1.1,
            step_shrink=0.6,
            terminal_replacement=False,
        )
        p = alignment.provenance(cfg)
        controls = p["numerical_controls"]
        self.assertEqual(controls["harmony_cv_threshold"], 0.05)
        self.assertEqual(controls["max_iterations"], 123)
        self.assertEqual(controls["initial_step"], 0.2)
        self.assertFalse(controls["terminal_replacement"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
