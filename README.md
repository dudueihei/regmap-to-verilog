# regmap-to-verilog

A small Python-based register map code generator for turning spreadsheet-friendly register tables into Verilog artifacts.

## What It Generates

Given a register table in `CSV` / `TSV` / Markdown table form, the generator emits:

- Verilog address/field macro header: `include/<module>_regs.vh`
- Verilog register file skeleton: `rtl/<module>_regfile.v`

## Supported Input Styles

The generator accepts:

- UTF-8 or UTF-8-BOM `CSV`
- `TSV`
- Markdown pipe tables
- English or Chinese headers

Recommended compact header style:

```csv
偏移地址,寄存器名,字段名,位段,属性,复位值,描述
0x0,SE_CTRL,start,0,WO,,写1启动
,,stop,1,WO,,写1停止
,,irq_en,3,RW,,中断使能
0x4,SE_BOOT_PC,boot_pc,31:0,RW,,启动PC
```

Also supported:

- verbose `End Bit / Begin Bit / Width`
- compact `Bits`
- optional `Reset Value`

## Repository Layout

```text
.
├── tools/
│   └── regmap_codegen.py
├── specs/
│   ├── se_top_regmap.tsv
│   └── se_top_regmap_compact.csv
├── include/
│   └── se_top_regs.vh
└── rtl/
    └── se_top_regfile.v
```

## Quick Start

Run from the repository root:

```bash
python3 tools/regmap_codegen.py specs/se_top_regmap_compact.csv
```

This generates:

```text
include/se_top_regs.vh
rtl/se_top_regfile.v
```

## Optional Compact Export

If you already have a verbose TSV table, you can export a more spreadsheet-friendly compact CSV:

```bash
python3 tools/regmap_codegen.py \
  specs/se_top_regmap.tsv \
  --export-compact specs/se_top_regmap_compact.csv \
  --compact-lang zh
```

## Generated Verilog Behavior

The generated register file currently supports:

- `RW`: stored internally
- `RO`: driven by external `*_i`
- `WO`: emits `*_we_o` and `*_wdata_o`
- `W1C`: stored internally, set by `*_set_i`, cleared by software write-1

## Example

The sample spec in `specs/se_top_regmap_compact.csv` generates:

- `include/se_top_regs.vh`
- `rtl/se_top_regfile.v`

These files are included in the repository as reference output.

## Notes

- Blank register names inherit the previous register
- Blank offsets on a new register auto-increment by `addr_stride`
- Blank offsets on continued field rows reuse the current register offset

## License

No license file is included yet. Add one before wider public reuse if needed.
