#!/usr/bin/env python3
"""
Generate Verilog register artifacts from a spreadsheet-friendly register table.

Supported input format:
1. UTF-8/UTF-8-BOM TSV or CSV exported from Excel/WPS/Numbers
2. `.xlsx` workbook edited directly in Excel/WPS/Numbers
3. Markdown-style pipe table copied from docs/wiki
4. Optional metadata comment lines at the top of text files:
   # module = se_top
   # base_addr = 0x0000
   # addr_width = 32
   # data_width = 32
   # addr_stride = 0x4

Supported table styles:
1. Verbose style:
   Offset Address, Register Name, Field Name,
   End Bit, Begin Bit, Width, Attribute, Description
2. Compact style:
   Offset, Register, Field, Bits, Access, Reset, Description
3. Chinese compact style:
   偏移地址, 寄存器名, 字段名, 位段, 属性, 复位值, 描述

Optional columns:
    Bits
    End Bit
    Begin Bit
    Width
    Description
    Reset Value

Blank-cell behavior is intentionally tolerant so future table edits are easy:
1. Blank "Register Name" inherits the previous register.
2. Blank "Offset Address" on a new register auto-increments by addr_stride.
3. Blank "Offset Address" on a continued field row keeps the current register offset.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import re
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from xml.etree import ElementTree as ET


BASE_REQUIRED_COLUMNS = {
    "offset_address",
    "register_name",
    "field_name",
    "attribute",
}

OPTIONAL_COLUMNS = {
    "bits",
    "end_bit",
    "begin_bit",
    "width",
    "description",
    "reset_value",
}

RAW_HEADER_ALIASES = {
    "偏移地址": "offset_address",
    "寄存器名": "register_name",
    "寄存器": "register_name",
    "字段名": "field_name",
    "字段": "field_name",
    "位段": "bits",
    "属性": "attribute",
    "访问属性": "attribute",
    "复位值": "reset_value",
    "默认值": "reset_value",
    "描述": "description",
    "说明": "description",
    "高位": "end_bit",
    "低位": "begin_bit",
    "位宽": "width",
}

HEADER_ALIASES = {
    "offset": "offset_address",
    "offset_address": "offset_address",
    "address_offset": "offset_address",
    "addr": "offset_address",
    "register": "register_name",
    "register_name": "register_name",
    "reg_name": "register_name",
    "registername": "register_name",
    "field": "field_name",
    "field_name": "field_name",
    "fieldname": "field_name",
    "bits": "bits",
    "bit": "bits",
    "bit_range": "bits",
    "bitrange": "bits",
    "range": "bits",
    "end_bit": "end_bit",
    "msb": "end_bit",
    "begin_bit": "begin_bit",
    "lsb": "begin_bit",
    "width": "width",
    "attribute": "attribute",
    "attr": "attribute",
    "access": "attribute",
    "property": "attribute",
    "description": "description",
    "desc": "description",
    "comment": "description",
    "reset": "reset_value",
    "reset_value": "reset_value",
    "default": "reset_value",
    "default_value": "reset_value",
}

SUPPORTED_ATTRS = {"RW", "RO", "WO", "W1C"}
MARKDOWN_SEPARATOR_RE = re.compile(r"^:?-{3,}:?$")
XML_NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
WORKSHEET_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>
{sheet_rows}
  </sheetData>
</worksheet>
"""
WORKBOOK_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="{sheet_name}" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>
"""
WORKBOOK_RELS_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>
"""
ROOT_RELS_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
"""
CONTENT_TYPES_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>
"""
STYLES_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>
  <fills count="2">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
  </fills>
  <borders count="1"><border/></borders>
  <cellStyleXfs count="1"><xf/></cellStyleXfs>
  <cellXfs count="1"><xf xfId="0"/></cellXfs>
  <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>
"""
APP_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
 xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>regmap_codegen.py</Application>
</Properties>
"""
CORE_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:dcmitype="http://purl.org/dc/dcmitype/"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:creator>regmap_codegen.py</dc:creator>
  <cp:lastModifiedBy>regmap_codegen.py</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{timestamp}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{timestamp}</dcterms:modified>
</cp:coreProperties>
"""


@dataclass
class FieldDef:
    reg_name: str
    name: str
    msb: int
    lsb: int
    width: int
    attr: str
    description: str
    reset_value: int = 0

    @property
    def is_reserved(self) -> bool:
        return normalize_symbol(self.name) == "reserved"

    @property
    def range_str(self) -> str:
        if self.msb == self.lsb:
            return f"[{self.lsb}]"
        return f"[{self.msb}:{self.lsb}]"


@dataclass
class RegisterDef:
    name: str
    offset: int
    fields: List[FieldDef] = field(default_factory=list)


@dataclass
class RegModel:
    module_name: str
    addr_width: int
    data_width: int
    base_addr: int
    addr_stride: int
    registers: List[RegisterDef]
    source_path: Path


def normalize_header(value: str) -> str:
    raw = value.strip().strip("\ufeff")
    if raw in RAW_HEADER_ALIASES:
        return RAW_HEADER_ALIASES[raw]
    key = re.sub(r"[^a-z0-9]+", "_", raw.lower()).strip("_")
    return HEADER_ALIASES.get(key, key)


def normalize_symbol(value: str) -> str:
    key = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    return re.sub(r"_+", "_", key)


def to_upper_ident(value: str) -> str:
    ident = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip()).strip("_")
    ident = re.sub(r"_+", "_", ident).upper()
    if not ident:
        ident = "UNNAMED"
    if ident[0].isdigit():
        ident = f"N_{ident}"
    return ident


def to_lower_ident(value: str) -> str:
    ident = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip()).strip("_")
    ident = re.sub(r"_+", "_", ident).lower()
    if not ident:
        ident = "unnamed"
    if ident[0].isdigit():
        ident = f"n_{ident}"
    return ident


def parse_int(text: str, allow_blank: bool = False) -> Optional[int]:
    value = text.strip()
    if not value:
        if allow_blank:
            return None
        raise ValueError("empty numeric field")

    value = value.replace("_", "")
    if value.lower().startswith("0x"):
        return int(value, 16)
    return int(value, 10)


def detect_delimiter(lines: Sequence[str], source: Path) -> str:
    sample = "\n".join(lines[:10])
    if "\t" in sample:
        return "\t"
    if "," in sample:
        return ","
    if "|" in sample:
        return "|"
    raise ValueError(f"Unable to detect delimiter for {source}")


def excel_col_to_name(col_idx: int) -> str:
    result = []
    idx = col_idx
    while idx > 0:
        idx, rem = divmod(idx - 1, 26)
        result.append(chr(ord("A") + rem))
    return "".join(reversed(result))


def escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def trim_pipe_row(row: Sequence[str]) -> List[str]:
    cells = [cell.strip() for cell in row]
    if cells and cells[0] == "":
        cells = cells[1:]
    if cells and cells[-1] == "":
        cells = cells[:-1]
    return cells


def is_markdown_separator_row(row: Sequence[str]) -> bool:
    cells = [cell.strip() for cell in row if cell.strip()]
    if not cells:
        return False
    return all(MARKDOWN_SEPARATOR_RE.fullmatch(cell) for cell in cells)


def validate_header(header: Sequence[str], source: Path) -> None:
    header_set = set(header)
    missing = sorted(BASE_REQUIRED_COLUMNS - header_set)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    has_bits = "bits" in header_set
    has_msb_lsb = {"end_bit", "begin_bit"} <= header_set
    if not has_bits and not has_msb_lsb:
        raise ValueError(
            f"{source}: table must provide either 'Bits' or both 'End Bit'/'Begin Bit' columns"
        )


def cell_text_from_xlsx(cell: ET.Element, shared_strings: Sequence[str]) -> str:
    cell_type = cell.get("t")
    if cell_type == "inlineStr":
        text_nodes = cell.findall(".//main:t", XML_NS)
        return "".join(node.text or "" for node in text_nodes)
    value_node = cell.find("main:v", XML_NS)
    if value_node is None or value_node.text is None:
        return ""
    value = value_node.text
    if cell_type == "s":
        return shared_strings[int(value)]
    return value


def parse_xlsx_shared_strings(archive: zipfile.ZipFile) -> List[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    values: List[str] = []
    for item in root.findall("main:si", XML_NS):
        text_nodes = item.findall(".//main:t", XML_NS)
        values.append("".join(node.text or "" for node in text_nodes))
    return values


def load_rows_from_xlsx(source: Path) -> Tuple[Dict[str, str], List[Dict[str, str]]]:
    with zipfile.ZipFile(source) as archive:
        shared_strings = parse_xlsx_shared_strings(archive)
        sheet_xml = archive.read("xl/worksheets/sheet1.xml")

    root = ET.fromstring(sheet_xml)
    rows_raw: List[List[str]] = []
    for row in root.findall(".//main:sheetData/main:row", XML_NS):
        cells: Dict[int, str] = {}
        max_col = 0
        for cell in row.findall("main:c", XML_NS):
            ref = cell.get("r", "")
            col_letters = "".join(ch for ch in ref if ch.isalpha())
            col_idx = 0
            for ch in col_letters:
                col_idx = col_idx * 26 + (ord(ch.upper()) - ord("A") + 1)
            if col_idx == 0:
                continue
            cells[col_idx] = cell_text_from_xlsx(cell, shared_strings).strip()
            max_col = max(max_col, col_idx)
        if max_col == 0:
            rows_raw.append([])
            continue
        rows_raw.append([cells.get(idx, "").strip() for idx in range(1, max_col + 1)])

    while rows_raw and (not rows_raw[0] or not any(cell for cell in rows_raw[0])):
        rows_raw.pop(0)
    if not rows_raw:
        raise ValueError(f"No rows parsed from {source}")

    metadata: Dict[str, str] = {}
    header_row_idx: Optional[int] = None
    for idx, row in enumerate(rows_raw):
        normalized = [normalize_header(cell) for cell in row]
        header_set = set(normalized)
        has_required = BASE_REQUIRED_COLUMNS <= header_set
        has_layout = "bits" in header_set or {"end_bit", "begin_bit"} <= header_set
        if has_required and has_layout:
            header_row_idx = idx
            break
        if len(row) >= 2 and row[0].strip():
            key = normalize_symbol(row[0])
            if key in {"module", "base_addr", "addr_width", "data_width", "addr_stride"}:
                metadata[key] = row[1].strip()

    if header_row_idx is None:
        raise ValueError(
            f"{source}: unable to find header row in xlsx sheet1; "
            "expected columns like 偏移地址/寄存器名/字段名/位段/属性"
        )

    header = [normalize_header(cell) for cell in rows_raw[header_row_idx]]
    validate_header(header, source)
    normalized_rows: List[Dict[str, str]] = []
    for row in rows_raw[header_row_idx + 1:]:
        if not any(cell.strip() for cell in row):
            continue
        padded = list(row) + [""] * (len(header) - len(row))
        entry = {header[idx]: padded[idx].strip() for idx in range(len(header))}
        if not any(value.strip() for value in entry.values()):
            continue
        normalized_rows.append(entry)
    return metadata, normalized_rows


def parse_metadata(lines: Sequence[str]) -> Dict[str, str]:
    metadata: Dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue
        body = stripped[1:].strip()
        if "=" not in body:
            continue
        key, value = body.split("=", 1)
        metadata[normalize_symbol(key)] = value.strip()
    return metadata


def load_rows(source: Path) -> Tuple[Dict[str, str], List[Dict[str, str]]]:
    if source.suffix.lower() == ".xlsx":
        return load_rows_from_xlsx(source)

    raw_lines = source.read_text(encoding="utf-8-sig").splitlines()
    metadata = parse_metadata(raw_lines)
    data_lines = [line for line in raw_lines if line.strip() and not line.strip().startswith("#")]
    if not data_lines:
        raise ValueError(f"No tabular content found in {source}")

    delimiter = detect_delimiter(data_lines, source)
    reader = csv.reader(data_lines, delimiter=delimiter)
    rows = [trim_pipe_row(row) if delimiter == "|" else list(row) for row in reader]
    if not rows:
        raise ValueError(f"No rows parsed from {source}")

    while rows and (not rows[0] or not any(cell.strip() for cell in rows[0])):
        rows.pop(0)
    if not rows:
        raise ValueError(f"No rows parsed from {source}")

    header = [normalize_header(cell) for cell in rows[0]]
    validate_header(header, source)

    normalized_rows: List[Dict[str, str]] = []
    for row in rows[1:]:
        if delimiter == "|" and (not row or is_markdown_separator_row(row)):
            continue
        if delimiter == "|" and row and not "".join(row).strip():
            continue
        padded = list(row) + [""] * (len(header) - len(row))
        entry = {header[idx]: padded[idx].strip() for idx in range(len(header))}
        if not any(value.strip() for value in entry.values()):
            continue
        normalized_rows.append(entry)

    return metadata, normalized_rows


def parse_bit_range(text: str, source: Path, row_num: int, field_name: str) -> Tuple[int, int]:
    value = text.strip()
    if not value:
        raise ValueError(f"{source}:{row_num}: empty Bits for field {field_name}")
    value = value.strip("[]")
    range_match = re.fullmatch(r"(\d+)\s*:\s*(\d+)", value)
    if range_match:
        msb = int(range_match.group(1))
        lsb = int(range_match.group(2))
        return msb, lsb
    bit_match = re.fullmatch(r"(\d+)", value)
    if bit_match:
        bit = int(bit_match.group(1))
        return bit, bit
    raise ValueError(
        f"{source}:{row_num}: invalid Bits '{text}' for field {field_name}, "
        f"expected forms like '7:4' or '0'"
    )


def parse_field_layout(
    row: Dict[str, str],
    source: Path,
    row_num: int,
    field_name: str,
) -> Tuple[int, int, int]:
    bits_text = row.get("bits", "").strip()
    if bits_text:
        msb, lsb = parse_bit_range(bits_text, source, row_num, field_name)
    else:
        msb = parse_int(row["end_bit"])
        lsb = parse_int(row["begin_bit"])

    width_cell = row.get("width", "").strip()
    width = parse_int(width_cell) if width_cell else (msb - lsb + 1)
    return msb, lsb, width


def parse_model(source: Path, module_override: Optional[str] = None) -> RegModel:
    metadata, rows = load_rows(source)

    module_name = module_override or metadata.get("module") or source.stem
    addr_width = int(metadata.get("addr_width", "32"))
    data_width = int(metadata.get("data_width", "32"))
    base_addr = parse_int(metadata.get("base_addr", "0x0"))
    addr_stride = parse_int(metadata.get("addr_stride", "0x4"))

    registers: List[RegisterDef] = []
    reg_index: Dict[str, RegisterDef] = {}
    current_register: Optional[RegisterDef] = None
    current_offset: Optional[int] = None

    for row_num, row in enumerate(rows, start=2):
        reg_name_cell = row.get("register_name", "").strip()
        field_name_cell = row.get("field_name", "").strip()
        offset_cell = row.get("offset_address", "").strip()

        if reg_name_cell:
            reg_name = to_upper_ident(reg_name_cell)
            is_new_register = current_register is None or current_register.name != reg_name
            if is_new_register:
                if reg_name in reg_index:
                    raise ValueError(
                        f"{source}:{row_num}: duplicate register name '{reg_name_cell}'"
                    )
                if offset_cell:
                    current_offset = parse_int(offset_cell)
                elif current_offset is None:
                    current_offset = 0
                else:
                    current_offset += addr_stride

                current_register = RegisterDef(name=reg_name, offset=current_offset)
                registers.append(current_register)
                reg_index[reg_name] = current_register
            elif offset_cell:
                current_register.offset = parse_int(offset_cell)
                current_offset = current_register.offset
        else:
            if current_register is None:
                raise ValueError(
                    f"{source}:{row_num}: register name is blank before any register is defined"
                )
            if offset_cell:
                current_register.offset = parse_int(offset_cell)
                current_offset = current_register.offset

        if current_register is None:
            raise AssertionError("current_register should not be None here")
        if not field_name_cell:
            raise ValueError(f"{source}:{row_num}: field name is blank")

        msb, lsb, width = parse_field_layout(row, source, row_num, field_name_cell)
        expected_width = msb - lsb + 1
        if width != expected_width:
            raise ValueError(
                f"{source}:{row_num}: width mismatch for {current_register.name}.{field_name_cell} "
                f"(table={width}, bits={expected_width})"
            )

        attr = row["attribute"].strip().upper().replace("/", "")
        if attr not in SUPPORTED_ATTRS:
            raise ValueError(
                f"{source}:{row_num}: unsupported attribute '{row['attribute']}', "
                f"supported={sorted(SUPPORTED_ATTRS)}"
            )

        reset_text = row.get("reset_value", "").strip()
        reset_value = parse_int(reset_text, allow_blank=True) if reset_text else 0
        if reset_value >= (1 << width):
            raise ValueError(
                f"{source}:{row_num}: reset value 0x{reset_value:X} exceeds field width {width}"
            )

        field_def = FieldDef(
            reg_name=current_register.name,
            name=field_name_cell,
            msb=msb,
            lsb=lsb,
            width=width,
            attr=attr,
            description=row.get("description", "").strip(),
            reset_value=reset_value,
        )
        current_register.fields.append(field_def)

    validate_model(registers, source, data_width)

    return RegModel(
        module_name=to_lower_ident(module_name),
        addr_width=addr_width,
        data_width=data_width,
        base_addr=base_addr,
        addr_stride=addr_stride,
        registers=registers,
        source_path=source,
    )


def validate_model(registers: Iterable[RegisterDef], source: Path, data_width: int) -> None:
    used_offsets: Dict[int, str] = {}
    for reg in registers:
        if reg.offset in used_offsets:
            raise ValueError(
                f"{source}: duplicate offset 0x{reg.offset:X} used by "
                f"{used_offsets[reg.offset]} and {reg.name}"
            )
        used_offsets[reg.offset] = reg.name

        used_bits: Dict[int, str] = {}
        for field_def in reg.fields:
            if field_def.msb >= data_width or field_def.lsb < 0:
                raise ValueError(
                    f"{source}: {reg.name}.{field_def.name} bit range {field_def.range_str} "
                    f"exceeds data width {data_width}"
                )
            if field_def.msb < field_def.lsb:
                raise ValueError(
                    f"{source}: {reg.name}.{field_def.name} has msb < lsb ({field_def.range_str})"
                )
            for bit in range(field_def.lsb, field_def.msb + 1):
                if bit in used_bits:
                    raise ValueError(
                        f"{source}: overlapping bits in {reg.name}: "
                        f"{field_def.name} overlaps with {used_bits[bit]} at bit {bit}"
                    )
                used_bits[bit] = field_def.name


def mask_value(msb: int, lsb: int) -> int:
    width = msb - lsb + 1
    return ((1 << width) - 1) << lsb


def hex_literal(value: int, width: int) -> str:
    digits = max(1, (width + 3) // 4)
    return f"{width}'h{value:0{digits}X}"


def vector_decl(width: int) -> str:
    if width == 1:
        return ""
    return f"[{width - 1}:0] "


def slice_expr(msb: int, lsb: int) -> str:
    if msb == lsb:
        return f"[{lsb}]"
    return f"[{msb}:{lsb}]"


def signal_base(reg: RegisterDef, field_def: FieldDef) -> str:
    reg_ident = to_lower_ident(reg.name)
    field_ident = to_lower_ident(field_def.name)
    if reg_ident.endswith(field_ident):
        return reg_ident
    return f"{reg_ident}_{field_ident}"


def reg_addr_ident(reg: RegisterDef) -> str:
    reg_ident = to_upper_ident(reg.name)
    if reg_ident.endswith("_ADDR"):
        return f"{reg_ident}_OFFSET"
    return f"{reg_ident}_ADDR"


def format_bit_range(msb: int, lsb: int) -> str:
    if msb == lsb:
        return str(lsb)
    return f"{msb}:{lsb}"


def emit_vh(model: RegModel) -> str:
    guard = f"{to_upper_ident(model.module_name)}_REGS_VH"
    prefix = to_upper_ident(model.module_name)
    lines: List[str] = []

    lines.append("// -----------------------------------------------------------------------------")
    lines.append("// Auto-generated by regmap_codegen.py")
    lines.append(f"// Source : {model.source_path.name}")
    lines.append(f"// Module : {model.module_name}")
    lines.append("// -----------------------------------------------------------------------------")
    lines.append(f"`ifndef {guard}")
    lines.append(f"`define {guard}")
    lines.append("")

    for reg in model.registers:
        lines.append(f"// {reg.name} @ 0x{reg.offset:08X}")
        lines.append(
            f"`define {prefix}_{reg_addr_ident(reg)} "
            f"{hex_literal(model.base_addr + reg.offset, model.addr_width)}"
        )
        for field_def in reg.fields:
            field_tag = f"{prefix}_{to_upper_ident(reg.name)}_{to_upper_ident(field_def.name)}"
            lines.append(f"`define {field_tag}_MSB   {field_def.msb}")
            lines.append(f"`define {field_tag}_LSB   {field_def.lsb}")
            lines.append(f"`define {field_tag}_WIDTH {field_def.width}")
            lines.append(
                f"`define {field_tag}_MASK  "
                f"{hex_literal(mask_value(field_def.msb, field_def.lsb), model.data_width)}"
            )
        lines.append("")

    lines.append(f"`endif  // {guard}")
    lines.append("")
    return "\n".join(lines)


def emit_module(model: RegModel) -> str:
    module_name = f"{model.module_name}_regfile"
    banner_time = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    stored_fields = [
        (reg, field_def)
        for reg in model.registers
        for field_def in reg.fields
        if not field_def.is_reserved and field_def.attr in {"RW", "W1C"}
    ]

    ports: List[str] = [
        "input  wire                     clk",
        "input  wire                     rst_n",
        "input  wire                     wr_en",
        "input  wire [ADDR_WIDTH-1:0]    wr_addr",
        "input  wire [DATA_WIDTH-1:0]    wr_data",
        "input  wire                     rd_en",
        "input  wire [ADDR_WIDTH-1:0]    rd_addr",
        "output reg  [DATA_WIDTH-1:0]    rd_data",
    ]

    for reg in model.registers:
        for field_def in reg.fields:
            if field_def.is_reserved:
                continue
            base = signal_base(reg, field_def)
            width_decl = vector_decl(field_def.width)
            if field_def.attr == "RO":
                ports.append(
                    f"input  wire {width_decl:<20}{base}_i"
                )
            elif field_def.attr == "RW":
                ports.append(
                    f"output reg  {width_decl:<20}{base}_o"
                )
            elif field_def.attr == "WO":
                ports.append(
                    f"output wire                     {base}_we_o"
                )
                ports.append(
                    f"output wire {width_decl:<20}{base}_wdata_o"
                )
            elif field_def.attr == "W1C":
                ports.append(
                    f"input  wire {width_decl:<20}{base}_set_i"
                )
                ports.append(
                    f"output reg  {width_decl:<20}{base}_o"
                )

    lines: List[str] = []
    lines.append("// -----------------------------------------------------------------------------")
    lines.append(f"// Auto-generated by regmap_codegen.py on {banner_time}")
    lines.append(f"// Source : {model.source_path.name}")
    lines.append("// Notes  :")
    lines.append("//   1. RW fields are stored inside this regfile.")
    lines.append("//   2. RO fields are driven by external *_i inputs.")
    lines.append("//   3. WO fields expose *_we_o + *_wdata_o outputs.")
    lines.append("//   4. W1C fields are stored internally and OR-ed with *_set_i,")
    lines.append("//      then cleared when software writes 1 to the corresponding bits.")
    lines.append("// -----------------------------------------------------------------------------")
    lines.append("`timescale 1ns / 1ps")
    lines.append("")
    lines.append(f"module {module_name} #(")
    lines.append(f"    parameter ADDR_WIDTH = {model.addr_width},")
    lines.append(f"    parameter DATA_WIDTH = {model.data_width},")
    lines.append(
        f"    parameter [ADDR_WIDTH-1:0] BASE_ADDR = {hex_literal(model.base_addr, model.addr_width)}"
    )
    lines.append(") (")
    lines.append("    " + ",\n    ".join(ports))
    lines.append(");")
    lines.append("")

    for reg in model.registers:
        lines.append(
            f"localparam [ADDR_WIDTH-1:0] {reg_addr_ident(reg)} = "
            f"BASE_ADDR + {hex_literal(reg.offset, model.addr_width)};"
        )
    lines.append("")

    writable_regs = [
        reg for reg in model.registers if any(
            (not field_def.is_reserved) and field_def.attr in {"RW", "WO", "W1C"}
            for field_def in reg.fields
        )
    ]
    for reg in writable_regs:
        lines.append(
            f"wire {to_lower_ident(reg.name)}_wr_hit = wr_en && (wr_addr == {reg_addr_ident(reg)});"
        )
    lines.append("")

    for reg in model.registers:
        for field_def in reg.fields:
            if field_def.is_reserved or field_def.attr != "WO":
                continue
            base = signal_base(reg, field_def)
            lines.append(
                f"assign {base}_we_o = {to_lower_ident(reg.name)}_wr_hit;"
            )
            lines.append(
                f"assign {base}_wdata_o = wr_data{slice_expr(field_def.msb, field_def.lsb)};"
            )
    if any((not field_def.is_reserved) and field_def.attr == "WO"
           for reg in model.registers for field_def in reg.fields):
        lines.append("")

    if stored_fields:
        lines.append("always @(posedge clk or negedge rst_n) begin")
        lines.append("    if (!rst_n) begin")
        for reg, field_def in stored_fields:
            base = signal_base(reg, field_def)
            reset_lit = hex_literal(field_def.reset_value, field_def.width)
            lines.append(f"        {base}_o <= {reset_lit};")
        lines.append("    end else begin")

        for reg, field_def in stored_fields:
            if field_def.attr == "W1C":
                base = signal_base(reg, field_def)
                lines.append(f"        {base}_o <= {base}_o | {base}_set_i;")

        for reg in model.registers:
            stored_in_reg = [
                field_def for field_def in reg.fields
                if (not field_def.is_reserved) and field_def.attr in {"RW", "W1C"}
            ]
            if not stored_in_reg:
                continue
            lines.append(f"        if ({to_lower_ident(reg.name)}_wr_hit) begin")
            for field_def in stored_in_reg:
                base = signal_base(reg, field_def)
                wr_slice = f"wr_data{slice_expr(field_def.msb, field_def.lsb)}"
                if field_def.attr == "RW":
                    lines.append(f"            {base}_o <= {wr_slice};")
                elif field_def.attr == "W1C":
                    lines.append(
                        f"            {base}_o <= ({base}_o | {base}_set_i) & ~{wr_slice};"
                    )
            lines.append("        end")
        lines.append("    end")
        lines.append("end")
        lines.append("")

    lines.append("always @* begin")
    lines.append("    rd_data = {DATA_WIDTH{1'b0}};")
    lines.append("    if (rd_en) begin")
    lines.append("        case (rd_addr)")
    for reg in model.registers:
        lines.append(f"            {reg_addr_ident(reg)}: begin")
        for field_def in reg.fields:
            if field_def.is_reserved or field_def.attr == "WO":
                continue
            base = signal_base(reg, field_def)
            expr = f"{base}_i" if field_def.attr == "RO" else f"{base}_o"
            lines.append(
                f"                rd_data{slice_expr(field_def.msb, field_def.lsb)} = {expr};"
            )
        lines.append("            end")
    lines.append("            default: begin")
    lines.append("                rd_data = {DATA_WIDTH{1'b0}};")
    lines.append("            end")
    lines.append("        endcase")
    lines.append("    end")
    lines.append("end")
    lines.append("")
    lines.append("endmodule")
    lines.append("")
    return "\n".join(lines)


def emit_compact_table(model: RegModel, lang: str = "zh") -> str:
    if lang == "zh":
        header = ["偏移地址", "寄存器名", "字段名", "位段", "属性", "复位值", "描述"]
    else:
        header = ["Offset", "Register", "Field", "Bits", "Access", "Reset", "Description"]

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([f"# module = {model.module_name}"])
    writer.writerow([f"# base_addr = 0x{model.base_addr:X}"])
    writer.writerow([f"# addr_width = {model.addr_width}"])
    writer.writerow([f"# data_width = {model.data_width}"])
    writer.writerow([f"# addr_stride = 0x{model.addr_stride:X}"])
    writer.writerow(header)

    for reg in model.registers:
        first_field = True
        for field_def in reg.fields:
            offset = f"0x{reg.offset:X}" if first_field else ""
            reg_name = reg.name if first_field else ""
            reset = "" if field_def.reset_value == 0 else f"0x{field_def.reset_value:X}"
            writer.writerow(
                [
                    offset,
                    reg_name,
                    field_def.name,
                    format_bit_range(field_def.msb, field_def.lsb),
                    field_def.attr,
                    reset,
                    field_def.description,
                ]
            )
            first_field = False

    return buf.getvalue()


def emit_compact_rows(model: RegModel, lang: str = "zh") -> List[List[str]]:
    if lang == "zh":
        header = ["偏移地址", "寄存器名", "字段名", "位段", "属性", "复位值", "描述"]
    else:
        header = ["Offset", "Register", "Field", "Bits", "Access", "Reset", "Description"]

    rows: List[List[str]] = [
        ["module", model.module_name],
        ["base_addr", f"0x{model.base_addr:X}"],
        ["addr_width", str(model.addr_width)],
        ["data_width", str(model.data_width)],
        ["addr_stride", f"0x{model.addr_stride:X}"],
        [],
        header,
    ]

    for reg in model.registers:
        first_field = True
        for field_def in reg.fields:
            offset = f"0x{reg.offset:X}" if first_field else ""
            reg_name = reg.name if first_field else ""
            reset = "" if field_def.reset_value == 0 else f"0x{field_def.reset_value:X}"
            rows.append(
                [
                    offset,
                    reg_name,
                    field_def.name,
                    format_bit_range(field_def.msb, field_def.lsb),
                    field_def.attr,
                    reset,
                    field_def.description,
                ]
            )
            first_field = False
    return rows


def emit_compact_xlsx(model: RegModel, lang: str = "zh", sheet_name: str = "regmap") -> bytes:
    rows = emit_compact_rows(model, lang=lang)
    sheet_rows: List[str] = []
    for row_idx, row in enumerate(rows, start=1):
        if not row:
            sheet_rows.append(f'    <row r="{row_idx}"/>')
            continue
        cell_xml: List[str] = []
        for col_idx, value in enumerate(row, start=1):
            if value == "":
                continue
            cell_ref = f"{excel_col_to_name(col_idx)}{row_idx}"
            if re.fullmatch(r"-?\d+(\.\d+)?", value):
                cell_xml.append(f'      <c r="{cell_ref}"><v>{value}</v></c>')
            else:
                escaped = escape_xml(value)
                cell_xml.append(
                    f'      <c r="{cell_ref}" t="inlineStr"><is><t>{escaped}</t></is></c>'
                )
        sheet_rows.append(f'    <row r="{row_idx}">\n' + "\n".join(cell_xml) + "\n    </row>")

    timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    workbook_xml = WORKBOOK_XML.format(sheet_name=escape_xml(sheet_name))
    worksheet_xml = WORKSHEET_XML.format(sheet_rows="\n".join(sheet_rows))
    core_xml = CORE_XML.format(timestamp=timestamp)

    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", CONTENT_TYPES_XML)
        archive.writestr("_rels/.rels", ROOT_RELS_XML)
        archive.writestr("docProps/app.xml", APP_XML)
        archive.writestr("docProps/core.xml", core_xml)
        archive.writestr("xl/workbook.xml", workbook_xml)
        archive.writestr("xl/_rels/workbook.xml.rels", WORKBOOK_RELS_XML)
        archive.writestr("xl/styles.xml", STYLES_XML)
        archive.writestr("xl/worksheets/sheet1.xml", worksheet_xml)
    return output.getvalue()


def default_outputs(spec_path: Path, module_name: str) -> Tuple[Path, Path]:
    project_root = spec_path.parent.parent
    out_vh = project_root / "include" / f"{module_name}_regs.vh"
    out_v = project_root / "rtl" / f"{module_name}_regfile.v"
    return out_vh, out_v


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate Verilog register artifacts from a TSV/CSV register map."
    )
    parser.add_argument("spec", type=Path, help="Input TSV/CSV spec path")
    parser.add_argument(
        "--module",
        help="Override module name from spec metadata",
    )
    parser.add_argument(
        "--out-v",
        type=Path,
        help="Output Verilog module path (.v). Default: rtl/<module>_regfile.v",
    )
    parser.add_argument(
        "--out-vh",
        type=Path,
        help="Output Verilog header path (.vh). Default: include/<module>_regs.vh",
    )
    parser.add_argument(
        "--export-compact",
        type=Path,
        help="Optional compact CSV export path for spreadsheet editing",
    )
    parser.add_argument(
        "--export-xlsx",
        type=Path,
        help="Optional compact XLSX export path for direct Excel editing",
    )
    parser.add_argument(
        "--compact-lang",
        choices=("zh", "en"),
        default="zh",
        help="Header language for compact CSV/XLSX export (default: zh)",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_argparser().parse_args(argv)
    model = parse_model(args.spec, module_override=args.module)
    out_vh, out_v = default_outputs(args.spec, model.module_name)
    if args.out_vh is not None:
        out_vh = args.out_vh
    if args.out_v is not None:
        out_v = args.out_v

    write_text(out_vh, emit_vh(model))
    write_text(out_v, emit_module(model))
    if args.export_compact is not None:
        write_text(args.export_compact, emit_compact_table(model, lang=args.compact_lang))
    if args.export_xlsx is not None:
        write_bytes(args.export_xlsx, emit_compact_xlsx(model, lang=args.compact_lang))

    print(f"[OK] Spec     : {args.spec}")
    print(f"[OK] Header   : {out_vh}")
    print(f"[OK] Verilog  : {out_v}")
    if args.export_compact is not None:
        print(f"[OK] Compact  : {args.export_compact}")
    if args.export_xlsx is not None:
        print(f"[OK] XLSX     : {args.export_xlsx}")
    print(f"[OK] Registers: {len(model.registers)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - CLI error path
        print(f"[ERROR] {exc}", file=sys.stderr)
        raise SystemExit(1)
