from __future__ import annotations

import copy
import csv
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import zipfile

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
import new_harmony_empirical_c as c
import new_harmony_empirical_d as d
import new_harmony_empirical_e_corrected as ec


DATA = ROOT / "data"
RESULTS = ROOT / "results"
REF = ROOT / "reference"
EXPECTED_D_SHA = "ad8487f4e37b3d2cc1a89e4bd692f5424a19d4c586fea5345a4b78d1f29a9732"
EXPECTED_FIXED_ASSET_SHA = "09e71560dd27ac6aa9ea9d06b539ae2b1cadab45509e55b23d7171d0131df519"
CORRECTED_LOCKS = {
    "frozen": {
        "transfers": 86,
        "mean": 0.4196346594277191,
        "cv": 0.0848061798974074,
        "investment_ratio": 0.2687727901475962,
        "stock_ratio": 0.7873808877672887,
    },
    "historical": {
        "transfers": 74,
        "mean": 0.4194880521717638,
        "cv": 0.08643638209600185,
        "investment_ratio": 0.2747260691466431,
        "stock_ratio": 0.7885975383254547,
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def toy_problem(*, capital: float = 50.0, labour: float = 100.0) -> tuple[c.ModelData, d.TradeInventoryData]:
    years = [1, 2, 3]
    sectors = ["A", "B"]
    A = np.repeat(np.array([[[0.10, 0.02], [0.03, 0.10]]]), 3, axis=0)
    L = np.array([np.linalg.inv(np.eye(2) - A[t]) for t in range(3)])
    C = np.array([[1.0, 0.15], [0.10, 1.0]])
    dep = np.array(
        [
            [[0.10, 0.20], [0.15, 0.05]],
            [[0.08, 0.18], [0.12, 0.04]],
            [[0.06, 0.16], [0.10, 0.03]],
        ]
    )
    stock = capital * np.ones((2, 2))
    goals = np.array([[10.0, 0.0], [8.0, 6.0], [9.0, 7.0]])
    labour_coeff = np.repeat(np.array([[0.20, 0.25]]), 3, axis=0)
    observed = {year: np.ones(2) for year in years}
    data = c.ModelData(
        years,
        sectors,
        {"A": "A", "B": "B"},
        A,
        L,
        C,
        dep,
        stock,
        goals,
        labour_coeff,
        np.full(3, labour),
        observed.copy(),
        {**observed, 0: np.ones(2)},
        observed.copy(),
        "toy",
    )
    import_A = np.zeros((3, 2, 2))
    import_cap = np.full((3, 2), 1.0e9)
    zero = np.zeros((3, 2))
    return data, d.TradeInventoryData(import_A, import_cap, zero.copy(), zero.copy())


class MilestoneECorrectedAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = {}
        cls.trade = {}
        cls.corrected = {}
        for mode in ("frozen", "historical"):
            model = c.load_model_data(DATA, mode)
            trade = d.load_trade_inventory(model, DATA)
            cls.data[mode] = model
            cls.trade[mode] = trade
            cls.corrected[mode] = ec.solve_configuration(
                model, trade, imports_enabled=True, inventories_enabled=False
            )

    def test_01_locked_predecessor_and_source_archives_are_preserved(self):
        self.assertEqual(sha256(REF / "NewHarmony_Milestone_D.zip"), EXPECTED_D_SHA)
        self.assertEqual(sha256(ROOT / "sources" / "BEA_FixedAssets_Milestone_B.zip"), EXPECTED_FIXED_ASSET_SHA)

    def test_02_exact_predecessor_archive_still_replays(self):
        with tempfile.TemporaryDirectory() as directory:
            with zipfile.ZipFile(REF / "NewHarmony_Milestone_D.zip") as archive:
                archive.extractall(directory)
            package = Path(directory) / "NewHarmony_Milestone_D"
            process = subprocess.run(
                [sys.executable, "-B", "-m", "unittest", "-q", "tests.test_milestone_d"],
                cwd=package,
                text=True,
                capture_output=True,
                timeout=90,
            )
            output = process.stdout + process.stderr
            self.assertEqual(process.returncode, 0, output)
            self.assertIn("Ran 25 tests", output)
            self.assertIn("OK", output)

    def test_03_empirical_contract_remains_five_years_by_71_sectors(self):
        for model in self.data.values():
            self.assertEqual(model.years, [2019, 2020, 2021, 2022, 2023])
            self.assertEqual(model.goals.shape, (5, 71))
            self.assertEqual(model.C.shape, (71, 71))

    def test_04_no_seventy_percent_replacement_floor_is_introduced(self):
        for result in self.corrected.values():
            self.assertTrue(np.allclose(result.initial.investments[:-1], 0.0))
            self.assertGreater(result.initial.investments[-1].sum(), 0.0)
            self.assertTrue(result.final.terminal_status.enabled)

    def test_05_corrected_baselines_are_reproducible(self):
        for mode, result in self.corrected.items():
            expected = CORRECTED_LOCKS[mode]
            observed = sum(self.data[mode].observed_investment[y].sum() for y in self.data[mode].years)
            self.assertEqual(len(result.capital_transfers), expected["transfers"])
            self.assertAlmostEqual(result.final.mean_harmony, expected["mean"], places=11)
            self.assertAlmostEqual(result.final.cv_harmony, expected["cv"], places=11)
            self.assertAlmostEqual(result.final.investments.sum() / observed, expected["investment_ratio"], places=11)
            self.assertAlmostEqual(
                result.final.stock_end[-1].sum() / self.data[mode].observed_stock[2023].sum(),
                expected["stock_ratio"],
                places=11,
            )

    def test_06_all_corrected_baseline_constraints_are_explicit_and_compliant(self):
        for result in self.corrected.values():
            self.assertEqual(len(result.final.constraint_report), 5)
            self.assertTrue(all(report.compliant for report in result.final.constraint_report))
            self.assertTrue(all(report.flow_balance_ok for report in result.final.constraint_report))
            self.assertTrue(all(report.labour_ok for report in result.final.constraint_report))
            self.assertTrue(all(report.capital_ok for report in result.final.constraint_report))
            self.assertTrue(all(report.imports_ok for report in result.final.constraint_report))
            self.assertTrue(all(report.consumption_ok for report in result.final.constraint_report))

    def test_07_objective_is_strictly_monotone_across_accepted_iterations(self):
        for result in self.corrected.values():
            self.assertTrue(all(b > a for a, b in zip(result.objective_history, result.objective_history[1:])))
            self.assertEqual(len(result.objective_history), len(result.capital_transfers) + 1)

    def test_08_zero_targets_are_excluded_from_product_harmony(self):
        data, trade = toy_problem()
        scenario = ec.evaluate(
            data,
            trade,
            np.zeros((3, 2, 2)),
            imports_enabled=False,
            config=ec.SolverConfig(terminal_replacement=False),
        )
        self.assertTrue(np.isnan(scenario.fulfillment[0, 1]))
        self.assertTrue(np.isnan(scenario.harmony_by_product[0, 1]))
        self.assertTrue(np.isfinite(scenario.annual_harmony).all())

    def test_09_stock_recurrence_and_inverse_depreciation_are_cell_specific(self):
        data, _ = toy_problem()
        investments = np.zeros((3, 2, 2))
        investments[0] = np.array([[3.0, 4.0], [5.0, 6.0]])
        start, end = ec._stock_path(data, investments)
        np.testing.assert_allclose(end[0], data.initial_stock * (1.0 - data.dep_by_year[0]) + investments[0])
        np.testing.assert_allclose(start[1], end[0])
        desired = np.array([[5.0, 4.0], [3.0, 2.0]])
        source = ec.inverse_depreciate_gap(desired, data, 0, 2)
        np.testing.assert_allclose(source * (1.0 - data.dep_by_year[1]), desired)

    def test_10_labour_only_violation_is_detected(self):
        data, trade = toy_problem(capital=1.0e7, labour=1.0)
        investments = np.zeros((3, 2, 2))
        investments[0, 0, 0] = 100.0
        scenario = ec.evaluate(
            data,
            trade,
            investments,
            imports_enabled=False,
            config=ec.SolverConfig(terminal_replacement=False),
        )
        self.assertFalse(scenario.constraint_report[0].labour_ok)
        self.assertTrue(scenario.constraint_report[0].capital_ok)

    def test_11_single_cell_capital_violation_is_detected(self):
        data, trade = toy_problem(capital=20.0, labour=1.0e9)
        investments = np.zeros((3, 2, 2))
        investments[0, 0, 0] = 100.0
        scenario = ec.evaluate(
            data,
            trade,
            investments,
            imports_enabled=False,
            config=ec.SolverConfig(terminal_replacement=False),
        )
        self.assertFalse(scenario.constraint_report[0].capital_ok)
        self.assertTrue(scenario.constraint_report[0].labour_ok)

    def test_12_weakest_uncorrectable_year_does_not_stop_the_search(self):
        data, trade = toy_problem()
        initial = ec.evaluate(
            data,
            trade,
            np.zeros((3, 2, 2)),
            imports_enabled=False,
            config=ec.SolverConfig(terminal_replacement=False),
        )
        initial.annual_harmony[:] = [0.01, 0.10, 0.20]
        initial.mean_harmony = float(initial.annual_harmony.mean())
        initial.std_harmony = float(initial.annual_harmony.std(ddof=1))
        initial.cv_harmony = 1.0
        initial.objective = float(initial.annual_harmony.sum())
        accepted = copy.deepcopy(initial)
        accepted.annual_harmony[2] += 0.01
        accepted.objective += 0.01
        accepted.mean_harmony = accepted.objective / 3.0
        accepted.cv_harmony = 1.0

        def candidate(_data, _trade, _scenario, destination, step, **kwargs):
            if destination == 1:
                return None, None, None, 0.0, 0.0
            return accepted, 1, np.ones((2, 2)), 0.2, 0.21

        with patch.object(ec, "evaluate", return_value=initial), patch.object(
            ec, "_candidate_for_destination", side_effect=candidate
        ):
            result = ec.solve_capital(
                data,
                trade,
                imports_enabled=False,
                config=ec.SolverConfig(max_iterations=1, terminal_replacement=False),
            )
        self.assertEqual(result[2][0]["destination_year"], 3)

    def test_13_adaptive_step_backtracks_until_a_candidate_is_admissible(self):
        data, trade = toy_problem()
        initial = ec.evaluate(
            data,
            trade,
            np.zeros((3, 2, 2)),
            imports_enabled=False,
            config=ec.SolverConfig(terminal_replacement=False),
        )
        initial.cv_harmony = 1.0
        accepted = copy.deepcopy(initial)
        accepted.objective += 0.01
        accepted.mean_harmony += 0.01 / 3.0
        accepted.cv_harmony = 1.0

        def candidate(_data, _trade, _scenario, destination, step, **kwargs):
            if step > 0.125 or destination == 1:
                return None, None, None, 0.0, 0.0
            return accepted, 1, np.ones((2, 2)), 0.2, 0.21

        with patch.object(ec, "evaluate", return_value=initial), patch.object(
            ec, "_candidate_for_destination", side_effect=candidate
        ):
            result = ec.solve_capital(
                data,
                trade,
                imports_enabled=False,
                config=ec.SolverConfig(max_iterations=1, initial_step=0.5, terminal_replacement=False),
            )
        self.assertLessEqual(result[6][0], 0.125)

    def test_14_terminal_equation_and_replacement_accounting_hold(self):
        data, trade = toy_problem(capital=1.0e6, labour=20.0)
        replacement, status = ec.terminal_replacement(
            data,
            trade,
            data.initial_stock,
            imports_enabled=False,
            config=ec.SolverConfig(),
        )
        t = 2
        D_t = data.C * data.dep_by_year[t]
        gross = np.linalg.solve(np.eye(2) - data.A_by_year[t] - D_t, status.q * data.goals[t])
        np.testing.assert_allclose((np.eye(2) - data.A_by_year[t] - D_t) @ gross, status.q * data.goals[t])
        np.testing.assert_allclose(replacement, D_t * gross[None, :])

    def test_15_terminal_reports_labour_capital_and_import_bindings(self):
        cases = []

        data, trade = toy_problem(capital=1.0e6, labour=1.0)
        cases.append(("labour", data, trade, False))

        data, trade = toy_problem(capital=1.0, labour=1.0e9)
        cases.append(("capital", data, trade, False))

        data, trade = toy_problem(capital=1.0e6, labour=1.0e9)
        trade.import_A_by_year[-1] = np.eye(2)
        trade.import_cap_by_year[-1] = np.array([0.01, 0.01])
        cases.append(("imports", data, trade, True))

        for expected, data, trade, imports_enabled in cases:
            _, status = ec.terminal_replacement(
                data,
                trade,
                data.initial_stock,
                imports_enabled=imports_enabled,
                config=ec.SolverConfig(),
            )
            self.assertEqual(status.binding_constraint, expected)
            self.assertAlmostEqual(
                status.q,
                {"labour": status.q_labour, "capital": status.q_capital, "imports": status.q_imports}[expected],
            )

        # The empirical baselines are import-limited, and the condition is
        # explicitly surfaced instead of being silently reported as labour-limited.
        for result in self.corrected.values():
            status = result.final.terminal_status
            self.assertTrue(status.enabled)
            self.assertTrue(status.nonlabour_limited)
            self.assertEqual(status.binding_constraint, "imports")
            self.assertLess(status.q, status.q_labour)

    def test_16_legacy_replay_remains_available_and_numerically_distinct(self):
        model = self.data["frozen"]
        trade = self.trade["frozen"]
        legacy = ec.solve_configuration(
            model,
            trade,
            imports_enabled=True,
            inventories_enabled=False,
            legacy_replay=True,
        )
        corrected = self.corrected["frozen"]
        self.assertAlmostEqual(legacy.final.mean_harmony, 0.4294140538902204, places=12)
        self.assertNotAlmostEqual(legacy.final.investments.sum(), corrected.final.investments.sum(), places=3)

    def test_17_observed_investment_is_diagnostic_not_a_solver_input(self):
        model = copy.deepcopy(self.data["frozen"])
        trade = self.trade["frozen"]
        baseline = self.corrected["frozen"]
        for year in model.years:
            model.observed_investment[year] *= 100.0
        rerun = ec.solve_configuration(model, trade, imports_enabled=True, inventories_enabled=False)
        np.testing.assert_allclose(rerun.final.investments, baseline.final.investments)
        self.assertAlmostEqual(rerun.final.objective, baseline.final.objective, places=12)

    def test_18_generated_corrected_outputs_include_audits(self):
        for mode in ("frozen", "historical"):
            out = RESULTS / "corrected" / mode
            self.assertTrue((out / "constraint_audit.csv").exists())
            self.assertTrue((out / "harmony_by_product.csv").exists())
            if (out / "constraint_audit.csv").exists():
                with open(out / "constraint_audit.csv", encoding="utf-8") as stream:
                    rows = list(csv.DictReader(stream))
                self.assertTrue(rows)
                self.assertTrue(all(row["compliant"] == "True" for row in rows))


if __name__ == "__main__":
    unittest.main(verbosity=2)
