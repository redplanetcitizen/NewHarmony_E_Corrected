"""Minimal XLSX reader used only to extract BEA source cells.

It deliberately uses only Python's standard library (zipfile + ElementTree).
It is not a general spreadsheet engine and never rewrites the source workbooks.
"""
from __future__ import annotations
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS_MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
NS_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def _col_index(cell_ref: str) -> int:
    match = re.match(r"([A-Z]+)", cell_ref)
    if not match:
        raise ValueError(f"invalid cell reference: {cell_ref}")
    n = 0
    for ch in match.group(1):
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def load_sheet(path: str | Path, sheet_name: str) -> dict[int, list[object | None]]:
    path = Path(path)
    with zipfile.ZipFile(path) as archive:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall(NS_MAIN + "si"):
                shared.append("".join(node.text or "" for node in item.iter(NS_MAIN + "t")))

        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        relmap = {node.attrib["Id"]: node.attrib["Target"] for node in rels}
        target = None
        sheets = workbook.find(NS_MAIN + "sheets")
        for sheet in ([] if sheets is None else list(sheets)):
            if sheet.attrib.get("name") == sheet_name:
                target = relmap[sheet.attrib[NS_REL + "id"]]
                break
        if target is None:
            raise KeyError(f"sheet not found: {sheet_name}")
        filename = target.lstrip("/") if target.startswith("/") else target
        if not filename.startswith("xl/"):
            filename = "xl/" + filename
        root = ET.fromstring(archive.read(filename))
        sheet_data = root.find(NS_MAIN + "sheetData")
        if sheet_data is None:
            return {}

        result: dict[int, list[object | None]] = {}
        for row in sheet_data:
            values: dict[int, object | None] = {}
            for cell in row.findall(NS_MAIN + "c"):
                idx = _col_index(cell.attrib["r"])
                typ = cell.attrib.get("t")
                v = cell.find(NS_MAIN + "v")
                if typ == "inlineStr":
                    inline = cell.find(NS_MAIN + "is")
                    value = "".join(n.text or "" for n in inline.iter(NS_MAIN + "t")) if inline is not None else ""
                elif v is None:
                    value = None
                else:
                    raw = v.text or ""
                    if typ == "s":
                        value = shared[int(raw)]
                    elif typ == "b":
                        value = bool(int(raw))
                    elif typ == "str":
                        value = raw
                    else:
                        try:
                            f = float(raw)
                            value = int(f) if f.is_integer() else f
                        except ValueError:
                            value = raw
                values[idx] = value
            if values:
                out = [None] * (max(values) + 1)
                for idx, value in values.items():
                    out[idx] = value
                result[int(row.attrib["r"])] = out
        return result
