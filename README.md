# regmap-to-verilog

一个把寄存器表自动生成 Verilog 文件的小工具。

适合把 Excel / WPS / Markdown 里维护的寄存器定义表，转换成：

- Verilog 宏定义头文件：`include/<module>_regs.vh`
- Verilog 寄存器文件骨架：`rtl/<module>_regfile.v`

## 当前仓库包含什么

这个仓库只保留和“寄存器表生成 Verilog”直接相关的内容：

- 生成脚本：[tools/regmap_codegen.py](/Users/mac/work/ada300_snpu_rtl/tools/regmap_codegen.py)
- 示例规格表：
  - [specs/se_top_regmap.tsv](/Users/mac/work/ada300_snpu_rtl/specs/se_top_regmap.tsv)
  - [specs/se_top_regmap_compact.csv](/Users/mac/work/ada300_snpu_rtl/specs/se_top_regmap_compact.csv)
- 生成结果：
  - [include/se_top_regs.vh](/Users/mac/work/ada300_snpu_rtl/include/se_top_regs.vh)
  - [rtl/se_top_regfile.v](/Users/mac/work/ada300_snpu_rtl/rtl/se_top_regfile.v)
- 辅助文件：
  - [.gitignore](/Users/mac/work/ada300_snpu_rtl/.gitignore)
  - [Makefile](/Users/mac/work/ada300_snpu_rtl/Makefile)

## 支持的输入格式

支持：

- UTF-8 / UTF-8-BOM 的 `CSV`
- `TSV`
- `.xlsx`
- Markdown pipe table
- 英文表头
- 中文表头

推荐优先使用紧凑格式：

```csv
偏移地址,寄存器名,字段名,位段,属性,复位值,描述
0x0,SE_CTRL,start,0,WO,,写1启动
,,stop,1,WO,,写1停止
,,irq_en,3,RW,,中断使能
0x4,SE_BOOT_PC,boot_pc,31:0,RW,,启动PC
```

也支持传统详细格式：

- `End Bit / Begin Bit / Width`
- 或单列 `Bits`

## 支持的属性

当前生成器支持：

- `RW`
- `RO`
- `WO`
- `W1C`

生成语义如下：

- `RW`：内部寄存
- `RO`：外部 `*_i` 输入
- `WO`：生成 `*_we_o` 和 `*_wdata_o`
- `W1C`：内部寄存，外部 `*_set_i` 置位，软件写 1 清零

## 快速开始

最简方式：

1. 把 Excel 文件放到 `specs/`
2. 执行：

```bash
python3 excel_to_verilog.py
```

或者：

```bash
make excel
```

如果你在 macOS 上，也可以直接双击：

```text
excel_to_verilog.command
```

默认会优先使用：

```text
specs/se_top_regmap_compact.xlsx
```

生成结果：

```text
include/se_top_regs.vh
rtl/se_top_regfile.v
```

如果你想手动指定某个 Excel：

```bash
python3 excel_to_verilog.py specs/你的表格.xlsx
```

底层命令仍然可用：

```bash
python3 tools/regmap_codegen.py specs/se_top_regmap_compact.xlsx
```

## 使用 Makefile

也可以直接执行：

```bash
make regmap
```

## 直接导出 Excel 模板

如果你想让表格直接在 Excel 里维护，可以执行：

```bash
make xlsx
```

会生成：

```text
specs/se_top_regmap_compact.xlsx
```

之后可以直接在 Excel / WPS 里修改这个 `.xlsx`，再重新生成：

```bash
python3 tools/regmap_codegen.py specs/se_top_regmap_compact.xlsx
```

## 从详细表导出紧凑表

如果你已经有详细 TSV，可以导出更适合表格维护的紧凑 CSV：

```bash
python3 tools/regmap_codegen.py \
  specs/se_top_regmap.tsv \
  --export-compact specs/se_top_regmap_compact.csv \
  --compact-lang zh
```

## 表格维护规则

为了方便改表，脚本支持下面这些规则：

- 同一寄存器的后续字段行，`寄存器名` 可以留空
- 新寄存器如果 `偏移地址` 留空，会按 `addr_stride` 自动递增
- 同一寄存器的续行如果 `偏移地址` 留空，则沿用当前寄存器地址
- `位段` 支持写成 `31:0`、`7:4`、`0`

## 仓库结构

```text
.
├── tools/
│   └── regmap_codegen.py
├── specs/
│   ├── se_top_regmap.tsv
│   └── se_top_regmap_compact.csv
├── tb/
│   └── se_top_regfile_tb.sv
├── include/
│   └── se_top_regs.vh
├── rtl/
│   └── se_top_regfile.v
├── Makefile
├── README.md
└── .gitignore
```

## Testbench

仓库内带了一个针对示例输出 `se_top_regfile.v` 的自检 testbench：

```bash
make test
```

这个 testbench 会检查：

- `RW` 字段写入与读回
- `WO` 写使能和写数据
- `W1C` 置位与写 1 清零
- 部分 `RO` 字段读回路径
