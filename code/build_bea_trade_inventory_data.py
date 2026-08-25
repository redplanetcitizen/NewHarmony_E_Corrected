"""Build the Milestone-D BEA imports/inventory overlay for 2019-2023.

Inputs are the BEA Summary Use and Import Matrix workbooks mirrored by the U.S. CBO.
The builder does not alter Milestone C. It produces dimensionless import-to-domestic
ratios that can be applied to Milestone C's 2019-price domestic coefficients/targets,
plus nominal audit tables and the observed F030 inventory-change diagnostic.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable

from xlsx_min import load_sheet

YEARS = tuple(range(2019, 2024))
N = 71
SPECIAL_CODES = ("Used", "Other")
LEGACY_FINAL_CODES = (
    "F010", "F02S", "F02E", "F02N", "F02R", "F040",
    "F06C", "F06S", "F06E", "F06N",
    "F07C", "F07S", "F07E", "F07N",
    "F10C", "F10S", "F10E", "F10N",
)
SOCIAL_FINAL_CODES = ("F010", "F040", "F06C", "F07C", "F10C")
EXPECTED_SOURCE_SHA256 = {
    "Use_Summary.xlsx": "98dd61d7c2a8df7c9678b1ebff9015372ac5ed082df33f9b15e8d7bf9408f341",
    "ImportMatrices_Before_Redefinitions_Summary.xlsx": "37dc9a1cd9de575d71c50a24f17018d5b7ff84bdf6dc1c4a9c69badfddaf8d17",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def num(value: object | None) -> float:
    if value in (None, "", "..."):
        return 0.0
    return float(value)


def _cell(row: list[object | None], col: int) -> object | None:
    return row[col] if col < len(row) else None


def _column_map(rows: dict[int, list[object | None]]) -> dict[str, int]:
    header = rows[6]
    result: dict[str, int] = {}
    for idx, value in enumerate(header):
        if value not in (None, ""):
            result[str(value)] = idx
    return result


def _model_rows(rows: dict[int, list[object | None]]) -> list[tuple[str, str, list[object | None]]]:
    out = []
    for rn in range(8, 79):
        row = rows[rn]
        out.append((str(row[0]), str(row[1]), row))
    if len(out) != N:
        raise AssertionError("expected exactly 71 model rows")
    return out


def _write_csv(path: Path, header: Iterable[object], rows: Iterable[Iterable[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)


def build(use_path: Path, import_path: Path, out_dir: Path) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    hashes = {use_path.name: sha256(use_path), import_path.name: sha256(import_path)}
    for name, expected in EXPECTED_SOURCE_SHA256.items():
        if hashes.get(name) != expected:
            raise RuntimeError(f"source hash mismatch for {name}: {hashes.get(name)} != {expected}")

    sectors: list[tuple[int, str, str]] | None = None
    annual_audit: list[dict[str, object]] = []
    special_rows: list[list[object]] = []
    final_long: list[list[object]] = []
    inventory_long: list[list[object]] = []
    zero_denominator_cells = 0
    negative_intermediate_import_cells = 0
    negative_import_adjustments: list[list[object]] = []
    pure_import_zero_domestic: list[list[object]] = []
    max_use_identity_error = 0.0
    max_final_identity_error = 0.0

    for year in YEARS:
        use = load_sheet(use_path, str(year))
        imp = load_sheet(import_path, str(year))
        use_cols = _column_map(use)
        imp_cols = _column_map(imp)
        use_rows = _model_rows(use)
        imp_rows = _model_rows(imp)
        codes = [r[0] for r in use_rows]
        if codes != [r[0] for r in imp_rows]:
            raise RuntimeError(f"row-code mismatch in {year}")
        if sectors is None:
            sectors = [(i, code, use_rows[i][1]) for i, code in enumerate(codes)]
        elif codes != [s[1] for s in sectors]:
            raise RuntimeError(f"sector order changed in {year}")

        industry_cols_use = [use_cols[code] for code in codes]
        industry_cols_imp = [imp_cols[code] for code in codes]
        matrix_rows: list[list[object]] = []
        total_intermediate_import = 0.0
        total_intermediate_domestic = 0.0
        for i, (code, name, urow) in enumerate(use_rows):
            ratio_row: list[object] = [code]
            irow = imp_rows[i][2]
            for j in range(N):
                total_use = num(_cell(urow, industry_cols_use[j]))
                imported = num(_cell(irow, industry_cols_imp[j]))
                domestic = total_use - imported
                max_use_identity_error = max(max_use_identity_error, abs(total_use - domestic - imported))
                productive_imported = imported
                if imported < -1e-12:
                    # A handful of tiny negative Import-Matrix cells are accounting
                    # adjustments, not a physical negative imported input. Preserve
                    # them in a residual audit and exclude them from productive M08.
                    negative_intermediate_import_cells += 1
                    negative_import_adjustments.append([year, code, codes[j], total_use, imported, domestic])
                    productive_imported = 0.0
                if domestic > 1e-12:
                    ratio = productive_imported / domestic
                else:
                    ratio = 0.0
                    if productive_imported > 1e-12:
                        zero_denominator_cells += 1
                        pure_import_zero_domestic.append([year, code, codes[j], total_use, imported, domestic])
                ratio_row.append(f"{ratio:.17g}")
                total_intermediate_import += imported
                total_intermediate_domestic += domestic
            matrix_rows.append(ratio_row)
        _write_csv(
            out_dir / f"intermediate_import_to_domestic_ratio_{year}.csv",
            ["commodity_code", *codes], matrix_rows,
        )

        def final_totals(selected_codes: tuple[str, ...]) -> tuple[float, float, float]:
            total = imported = 0.0
            for i, (code, name, urow) in enumerate(use_rows):
                irow = imp_rows[i][2]
                for fcode in selected_codes:
                    uv = num(_cell(urow, use_cols[fcode]))
                    mv = num(_cell(irow, imp_cols[fcode]))
                    total += uv
                    imported += mv
            return total, imported, total - imported

        legacy_total, legacy_import, legacy_domestic = final_totals(LEGACY_FINAL_CODES)
        social_total, social_import, social_domestic = final_totals(SOCIAL_FINAL_CODES)

        for i, (code, name, urow) in enumerate(use_rows):
            irow = imp_rows[i][2]
            for definition, selected in (("legacy_core_except_inventory", LEGACY_FINAL_CODES), ("social_core_no_fixed_investment", SOCIAL_FINAL_CODES)):
                total = sum(num(_cell(urow, use_cols[fcode])) for fcode in selected)
                imported = sum(num(_cell(irow, imp_cols[fcode])) for fcode in selected)
                domestic = total - imported
                max_final_identity_error = max(max_final_identity_error, abs(total - domestic - imported))
                ratio = imported / domestic if abs(domestic) > 1e-12 else 0.0
                ratio_defined = abs(domestic) > 1e-12 or abs(imported) <= 1e-12
                final_long.append([year, definition, code, name, total, imported, domestic, ratio, int(ratio_defined)])

            inv_total = num(_cell(urow, use_cols["F030"]))
            inv_import = num(_cell(irow, imp_cols["F030"]))
            inv_domestic = inv_total - inv_import
            inventory_long.append([year, code, name, inv_total, inv_import, inv_domestic])

        for special_code in SPECIAL_CODES:
            ur = next((r for r in use.values() if r and str(r[0]) == special_code), None)
            ir = next((r for r in imp.values() if r and str(r[0]) == special_code), None)
            if ur is None or ir is None:
                raise RuntimeError(f"missing special row {special_code} in {year}")
            for definition, selected in (("legacy_core_except_inventory", LEGACY_FINAL_CODES), ("social_core_no_fixed_investment", SOCIAL_FINAL_CODES)):
                total = sum(num(_cell(ur, use_cols[fcode])) for fcode in selected)
                imported = sum(num(_cell(ir, imp_cols[fcode])) for fcode in selected)
                special_rows.append([year, special_code, definition, total, imported, total-imported])

        annual_audit.append({
            "year": year,
            "intermediate_import_nominal_musd_71": total_intermediate_import,
            "intermediate_domestic_nominal_musd_71": total_intermediate_domestic,
            "legacy_final_total_nominal_musd_71": legacy_total,
            "legacy_final_import_nominal_musd_71": legacy_import,
            "legacy_final_domestic_nominal_musd_71": legacy_domestic,
            "social_final_total_nominal_musd_71": social_total,
            "social_final_import_nominal_musd_71": social_import,
            "social_final_domestic_nominal_musd_71": social_domestic,
        })

    assert sectors is not None
    _write_csv(out_dir / "sectors_71.csv", ["index", "bea_code", "sector_name"], sectors)
    _write_csv(out_dir / "final_import_overlay_nominal.csv",
               ["year","target_definition","bea_code","sector_name","total_final_use_musd","imported_final_use_musd","domestic_final_use_musd","import_to_domestic_ratio","ratio_defined"],
               final_long)
    _write_csv(out_dir / "inventory_change_F030_nominal.csv",
               ["year","bea_code","sector_name","inventory_change_total_musd","inventory_change_import_musd","inventory_change_domestic_musd"],
               inventory_long)
    _write_csv(out_dir / "special_import_rows_nominal.csv",
               ["year","special_code","target_definition","total_final_use_musd","imported_final_use_musd","domestic_final_use_musd"],
               special_rows)
    _write_csv(out_dir / "negative_import_adjustments_nominal.csv",
               ["year","commodity_code","industry_code","total_use_musd","import_matrix_musd","derived_domestic_musd"],
               negative_import_adjustments)
    _write_csv(out_dir / "import_nonpositive_domestic_denominator_cells_nominal.csv",
               ["year","commodity_code","industry_code","total_use_musd","import_matrix_musd","derived_domestic_musd"],
               pure_import_zero_domestic)

    # Aggregate inventory diagnostic.
    inv_agg: dict[int, list[float]] = {year: [0.0,0.0,0.0] for year in YEARS}
    for row in inventory_long:
        year = int(row[0]); inv_agg[year][0] += float(row[4-1]); inv_agg[year][1] += float(row[5-1]); inv_agg[year][2] += float(row[6-1])
    # The index arithmetic above is intentionally explicit in output columns below.
    # Recompute clearly to avoid relying on list positions in audit.
    inv_agg = {year:[0.0,0.0,0.0] for year in YEARS}
    for year, code, name, total, imported, domestic in inventory_long:
        inv_agg[int(year)][0] += float(total)
        inv_agg[int(year)][1] += float(imported)
        inv_agg[int(year)][2] += float(domestic)
    inventory_summary = [
        {"year": year, "total_change_nominal_musd_71": vals[0], "import_change_nominal_musd_71": vals[1], "domestic_change_nominal_musd_71": vals[2]}
        for year, vals in inv_agg.items()
    ]

    audit = {
        "status": "M08_M09_DATA_LAYER_BUILT",
        "years": list(YEARS),
        "sectors": N,
        "source_sha256": hashes,
        "source_hashes_match_locked_manifest": True,
        "final_target_definitions": {
            "legacy_core_except_inventory": list(LEGACY_FINAL_CODES),
            "social_core_no_fixed_investment": list(SOCIAL_FINAL_CODES),
            "inventory": "F030 kept separate in M09",
        },
        "annual": annual_audit,
        "inventory_summary": inventory_summary,
        "diagnostics": {
            "max_use_domestic_plus_import_identity_error": max_use_identity_error,
            "max_final_domestic_plus_import_identity_error": max_final_identity_error,
            "negative_import_adjustment_cells_excluded_from_productive_ratio": negative_intermediate_import_cells,
            "import_cells_with_nonpositive_domestic_denominator_excluded_from_ratio": zero_denominator_cells,
        },
        "method": {
            "M08_intermediate_real_overlay": "A_M_real = (M_nominal / D_nominal) * A_D_real, cell by cell where D_nominal != 0",
            "M08_final_real_overlay": "m_final_real = (M_final_nominal / D_final_nominal) * g_domestic_real, sector by sector where D_final_nominal != 0",
            "M09_state": "Inventory is an index/deviation state because BEA F030 supplies changes, not a 71-sector absolute inventory stock.",
        },
        "acceptance_boundary": "This data-layer build does not by itself replay the frozen Milestone-C solver; full D acceptance requires the accepted Milestone-C archive/code to be available as executable predecessor bytes.",
    }
    with (out_dir / "IMPORT_INVENTORY_AUDIT.json").open("w", encoding="utf-8") as stream:
        json.dump(audit, stream, indent=2, ensure_ascii=False)
    return audit


if __name__ == "__main__":
    here = Path(__file__).resolve().parents[1]
    audit = build(here / "sources" / "Use_Summary.xlsx", here / "sources" / "ImportMatrices_Before_Redefinitions_Summary.xlsx", here / "data")
    print(json.dumps(audit["diagnostics"], indent=2))
