from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'code'))
import new_harmony_empirical_c as c
import new_harmony_empirical_d as d
import new_harmony_empirical_e as e

DATA = ROOT / 'data'
RESULTS = ROOT / 'results'
REF = ROOT / 'reference'
EXPECTED_D_SHA = 'ad8487f4e37b3d2cc1a89e4bd692f5424a19d4c586fea5345a4b78d1f29a9732'
EXPECTED_FIXED_ASSET_SHA = '09e71560dd27ac6aa9ea9d06b539ae2b1cadab45509e55b23d7171d0131df519'
LOCKED = {
    'frozen': {'transfers': 111, 'mean': 0.4294140538902204, 'cv': 0.0722136544998807,
               'inv_ratio': 0.06552247803626672, 'stock_ratio': 0.727899493143283},
    'historical': {'transfers': 142, 'mean': 0.4178483854400241, 'cv': 0.09199400014123496,
                   'inv_ratio': 0.06311172013540048, 'stock_ratio': 0.7268585434914838},
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


class MilestoneEAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = {}; cls.trade = {}; cls.base = {}
        for mode in ('frozen', 'historical'):
            md = c.load_model_data(DATA, mode)
            tr = d.load_trade_inventory(md, DATA)
            cls.data[mode] = md; cls.trade[mode] = tr
            cls.base[mode] = d.solve_configuration(md, tr, imports_enabled=True, inventories_enabled=False)
        cls.gap = {r['technology_mode']: r for r in csv.DictReader(open(RESULTS/'investment_gap'/'INVESTMENT_GAP_HEADLINE.csv', encoding='utf-8'))}
        cls.sensitivity = list(csv.DictReader(open(RESULTS/'robustness'/'SENSITIVITY_RESULTS.csv', encoding='utf-8')))
        cls.terminal = {r['technology_mode']: r for r in csv.DictReader(open(RESULTS/'robustness'/'TERMINAL_HORIZON_DIAGNOSTIC.csv', encoding='utf-8'))}
        cls.maintenance = list(csv.DictReader(open(RESULTS/'robustness'/'MAINTENANCE_FLOOR_DIAGNOSTIC.csv', encoding='utf-8')))
        cls.asset = list(csv.DictReader(open(RESULTS/'investment_gap'/'ASSET_COMPOSITION_HEADLINE.csv', encoding='utf-8')))
        cls.asset_rec = list(csv.DictReader(open(RESULTS/'investment_gap'/'ASSET_COMPOSITION_RECONCILIATION.csv', encoding='utf-8')))

    def test_01_predecessor_D_sha_is_exact(self):
        self.assertEqual(sha256(REF/'NewHarmony_Milestone_D.zip'), EXPECTED_D_SHA)

    def test_02_exact_predecessor_archive_replays_25_tests(self):
        with tempfile.TemporaryDirectory() as td:
            with zipfile.ZipFile(REF/'NewHarmony_Milestone_D.zip') as z:
                z.extractall(td)
            pkg = Path(td) / 'NewHarmony_Milestone_D'
            proc = subprocess.run([sys.executable, '-m', 'unittest', '-q', 'tests.test_milestone_d'],
                                  cwd=pkg, text=True, capture_output=True, timeout=90)
            text = proc.stdout + proc.stderr
            self.assertEqual(proc.returncode, 0, text)
            self.assertIn('Ran 25 tests', text)
            self.assertIn('OK', text)

    def test_03_five_year_71_sector_contract_remains_frozen(self):
        for md in self.data.values():
            self.assertEqual(md.years, [2019, 2020, 2021, 2022, 2023])
            self.assertEqual(md.goals.shape, (5, 71))
            self.assertEqual(md.C.shape, (71, 71))

    def test_04_E_baseline_is_exact_D_M08_path(self):
        for mode, r in self.base.items():
            lk = LOCKED[mode]
            self.assertEqual(len(r.capital_transfers), lk['transfers'])
            self.assertAlmostEqual(r.final.mean_harmony, lk['mean'], places=12)
            self.assertAlmostEqual(r.final.cv_harmony, lk['cv'], places=12)
            observed = sum(self.data[mode].observed_investment[y].sum() for y in self.data[mode].years)
            self.assertAlmostEqual(r.final.investments.sum()/observed, lk['inv_ratio'], places=12)
            self.assertAlmostEqual(r.final.stock_end[-1].sum()/self.data[mode].observed_stock[2023].sum(), lk['stock_ratio'], places=12)

    def test_05_all_baseline_capital_transfers_are_forward_positive_gain(self):
        for r in self.base.values():
            for row in r.capital_transfers:
                self.assertLess(row['source_year'], row['destination_year'])
                self.assertGreater(row['gain'], 0.0)

    def test_06_observed_fixed_asset_accounting_remains_tight(self):
        audit = json.loads((DATA/'DATA_AUDIT.json').read_text(encoding='utf-8'))
        for row in audit['fixed_asset_accounting']:
            self.assertLess(row['weighted_abs_residual_over_stock'], 0.002)

    def test_07_investment_gap_is_large_and_locked(self):
        for mode, lk in LOCKED.items():
            row = self.gap[mode]
            self.assertAlmostEqual(float(row['planned_over_observed']), lk['inv_ratio'], places=12)
            self.assertGreater(float(row['investment_gap_real_musd']), 22_000_000.0)
            self.assertLess(float(row['planned_over_observed']), 0.07)

    def test_08_depreciation_is_the_dominant_accounting_scale_of_the_gap(self):
        for row in self.gap.values():
            self.assertGreater(float(row['observed_depreciation_over_observed_investment']), 0.78)
            self.assertLess(float(row['observed_depreciation_over_observed_investment']), 0.79)
            self.assertGreater(float(row['observed_depreciation_over_investment_gap']), 0.83)
            self.assertLess(float(row['observed_depreciation_over_investment_gap']), 0.85)

    def test_09_observed_net_accumulation_proxy_exceeds_planned_investment(self):
        for row in self.gap.values():
            self.assertGreater(float(row['observed_investment_minus_depreciation_5y_real_musd']), 5_000_000.0)
            self.assertLess(float(row['planned_over_observed_net_accumulation_proxy']), 0.31)

    def test_10_model_decumulates_capital_while_observed_stock_grows(self):
        for row in self.gap.values():
            self.assertLess(float(row['model_stock_change_2018_2023_real_musd']), -13_000_000.0)
            self.assertGreater(float(row['observed_stock_change_2018_2023_real_musd']), 4_000_000.0)

    def test_11_terminal_shadow_year_restores_positive_2023_investment(self):
        for row in self.terminal.values():
            self.assertGreater(float(row['investment_2023_real_musd']), 100_000.0)
            self.assertEqual(float(row['investment_shadow_2024_real_musd']), 0.0)
            self.assertEqual(row['all_transfer_gains_positive'], 'True')

    def test_12_terminal_horizon_effect_is_secondary_not_gap_closure(self):
        for row in self.terminal.values():
            ratio = float(row['planned_over_observed_2019_2023'])
            self.assertGreater(ratio, 0.07)
            self.assertLess(ratio, 0.08)
            self.assertLess(float(row['stock_2023_over_observed']), 0.74)

    def test_13_sensitivity_grid_has_all_22_one_at_a_time_runs(self):
        self.assertEqual(len(self.sensitivity), 22)
        keys = {(r['technology_mode'], r['scenario']) for r in self.sensitivity}
        self.assertEqual(len(keys), 22)

    def test_14_gap_persists_across_all_sensitivity_runs(self):
        for row in self.sensitivity:
            ratio = float(row['planned_over_observed_investment'])
            self.assertGreater(ratio, 0.05)
            self.assertLess(ratio, 0.09)
            self.assertEqual(row['stop_reason'], 'no_positive_transfer')
            self.assertEqual(row['all_transfer_gains_positive'], 'True')
            self.assertGreaterEqual(float(row['minimum_production_scale']), 0.0)

    def test_15_labour_plus_minus_five_percent_does_not_move_capital_bound_solution(self):
        for mode in ('frozen', 'historical'):
            rows = {r['scenario']: r for r in self.sensitivity if r['technology_mode'] == mode}
            base = float(rows['baseline']['final_mean_harmony'])
            self.assertAlmostEqual(float(rows['labour_-5pct']['final_mean_harmony']), base, places=12)
            self.assertAlmostEqual(float(rows['labour_+5pct']['final_mean_harmony']), base, places=12)

    def test_16_sensitivity_ranges_are_locked_and_narrow(self):
        expected={
            'frozen':(0.05815931846153298,0.07912856106054802),
            'historical':(0.056136007436354884,0.07221280821544926),
        }
        for mode,(lo,hi) in expected.items():
            vals=[float(r['planned_over_observed_investment']) for r in self.sensitivity if r['technology_mode']==mode]
            self.assertAlmostEqual(min(vals),lo,places=12)
            self.assertAlmostEqual(max(vals),hi,places=12)

    def test_17_maintenance_floor_raises_investment_and_stock_but_costs_harmony(self):
        for mode in ('frozen', 'historical'):
            rows = sorted((r for r in self.maintenance if r['technology_mode'] == mode),
                          key=lambda x: float(x['replacement_fraction_of_modeled_depreciation']))
            inv = [float(r['total_investment_over_observed']) for r in rows]
            stock = [float(r['stock_2023_over_observed']) for r in rows]
            h = [float(r['final_mean_harmony_after_targeted_additions']) for r in rows]
            self.assertTrue(all(b > a for a, b in zip(inv, inv[1:])))
            self.assertTrue(all(b > a for a, b in zip(stock, stock[1:])))
            self.assertTrue(all(h[0] > x for x in h[1:]))

    def test_18_E_does_not_force_historical_investment(self):
        # The final baseline is exactly D; observed investment is read only for ex-post comparison.
        for mode in ('frozen', 'historical'):
            r = self.base[mode]
            self.assertLess(r.final.investments.sum(), 0.08 * sum(self.data[mode].observed_investment[y].sum() for y in self.data[mode].years))


    def test_19_fixed_asset_source_archive_is_exact(self):
        self.assertEqual(sha256(ROOT/'sources'/'BEA_FixedAssets_Milestone_B.zip'), EXPECTED_FIXED_ASSET_SHA)

    def test_20_asset_composition_covers_private_government_and_three_asset_classes(self):
        keys={(r['flow'], r['owner'], r['asset_type']) for r in self.asset}
        expected={(flow,owner,asset) for flow in ('investment','depreciation')
                  for owner in ('private','government')
                  for asset in ('equipment','structures','ipp')}
        self.assertEqual(keys, expected)

    def test_21_asset_component_real_totals_reconcile_to_accepted_series(self):
        self.assertEqual(len(self.asset_rec), 10)
        self.assertLess(max(float(r['abs_reconciliation_over_accepted']) for r in self.asset_rec), 0.002)

    def test_22_asset_composition_is_economically_material_not_degenerate(self):
        inv=[r for r in self.asset if r['flow']=='investment']
        shares={(r['owner'],r['asset_type']):float(r['component_share_of_component_total']) for r in inv}
        self.assertGreater(shares[('private','structures')], 0.30)
        self.assertGreater(shares[('private','equipment')], 0.24)
        self.assertGreater(shares[('private','ipp')], 0.25)
        self.assertGreater(sum(v for (o,a),v in shares.items() if o=='government'), 0.16)

    def test_23_required_final_validation_outputs_exist(self):
        required = [
            RESULTS/'FINAL_BASELINE.csv',
            RESULTS/'MILESTONE_E_SUMMARY.json',
            RESULTS/'investment_gap'/'INVESTMENT_GAP_HEADLINE.csv',
            RESULTS/'investment_gap'/'INVESTMENT_GAP_ANNUAL.csv',
            RESULTS/'investment_gap'/'INVESTMENT_GAP_BY_SECTOR.csv',
            RESULTS/'investment_gap'/'CAPITAL_STOCK_PATH.csv',
            RESULTS/'investment_gap'/'ASSET_COMPOSITION_HEADLINE.csv',
            RESULTS/'investment_gap'/'ASSET_COMPOSITION_RECONCILIATION.csv',
            RESULTS/'robustness'/'SENSITIVITY_RESULTS.csv',
            RESULTS/'robustness'/'TERMINAL_HORIZON_DIAGNOSTIC.csv',
            RESULTS/'robustness'/'MAINTENANCE_FLOOR_DIAGNOSTIC.csv',
        ]
        for path in required:
            self.assertTrue(path.exists(), str(path))

    def test_24_final_interpretation_is_consistent_across_modes(self):
        # Both technology modes support the same qualitative finding; no result depends
        # on selecting only the more favorable frozen benchmark.
        f, h = self.gap['frozen'], self.gap['historical']
        self.assertLess(abs(float(f['planned_over_observed']) - float(h['planned_over_observed'])), 0.005)
        self.assertLess(abs(float(f['model_2023_stock_over_observed']) - float(h['model_2023_stock_over_observed'])), 0.005)


if __name__ == '__main__':
    unittest.main(verbosity=2)
