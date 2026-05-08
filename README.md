# regmap-to-verilog

一个把寄存器 Excel 表格直接生成 Verilog 文件的小工具。

输入：
- Excel / WPS 表格 `.xlsx`

输出：
- Verilog 宏定义头文件：`include/<module>_regs.vh`
- Verilog 寄存器文件骨架：`rtl/<module>_regfile.v`

---

## 1. 给使用者的最简教程

如果你只是想用它，不想看实现细节，按下面 3 步就够了。

### 第 1 步：准备 Excel 表

直接修改这个模板：

- [se_top_regmap_compact.xlsx](/Users/mac/work/se_reg/specs/se_top_regmap_compact.xlsx)

或者把你自己的 `.xlsx` 文件放到：

- [specs](/Users/mac/work/se_reg/specs)

### 第 2 步：一键生成

进入仓库根目录后，执行下面任意一种方式。

方式 A：终端执行

```bash
cd /Users/mac/work/se_reg
python3 excel_to_verilog.py
```

方式 B：`make`

```bash
cd /Users/mac/work/se_reg
make excel
```

方式 C：macOS 直接双击

- [excel_to_verilog.command](/Users/mac/work/se_reg/excel_to_verilog.command)

### 第 3 步：查看输出文件

生成结果默认在：

- [se_top_regs.vh](/Users/mac/work/se_reg/include/se_top_regs.vh)
- [se_top_regfile.v](/Users/mac/work/se_reg/rtl/se_top_regfile.v)

---

## 2. 常见使用场景

### 场景 1：直接用默认模板

这是最推荐的方式。

1. 改这个文件：
   [se_top_regmap_compact.xlsx](/Users/mac/work/se_reg/specs/se_top_regmap_compact.xlsx)
2. 执行：

```bash
cd /Users/mac/work/se_reg
python3 excel_to_verilog.py
```

### 场景 2：你有自己的 Excel 文件

比如你新建了：

```text
specs/my_regmap.xlsx
```

那就执行：

```bash
cd /Users/mac/work/se_reg
python3 excel_to_verilog.py specs/my_regmap.xlsx
```

生成结果会自动输出到：

```text
include/my_regs.vh
rtl/my_regfile.v
```

---

## 3. Excel 表头怎么写

推荐使用这套中文表头：

```text
偏移地址,寄存器名,字段名,位段,属性,复位值,描述
```

示例：

```text
偏移地址,寄存器名,字段名,位段,属性,复位值,描述
0x0,SE_CTRL,start,0,WO,,写1启动
,,stop,1,WO,,写1停止
,,irq_en,3,RW,,中断使能
0x4,SE_BOOT_PC,boot_pc,31:0,RW,,启动PC
```

支持的属性：

- `RW`
- `RO`
- `WO`
- `W1C`

支持的位段写法：

- `0`
- `7:4`
- `31:0`

---

## 4. 文件怎么放

为了让别人拿到仓库就知道怎么看，这里把文件分成两类。

### 4.1 直接使用的文件

这些是普通使用者最该关注的文件：

- 一键生成入口：
  - [excel_to_verilog.py](/Users/mac/work/se_reg/excel_to_verilog.py)
  - [excel_to_verilog.command](/Users/mac/work/se_reg/excel_to_verilog.command)
- Excel 规格表：
  - [se_top_regmap_compact.xlsx](/Users/mac/work/se_reg/specs/se_top_regmap_compact.xlsx)
- 生成结果：
  - [se_top_regs.vh](/Users/mac/work/se_reg/include/se_top_regs.vh)
  - [se_top_regfile.v](/Users/mac/work/se_reg/rtl/se_top_regfile.v)

如果只是“改表然后出 Verilog”，只看这些文件就够了。

### 4.2 其他配置 / 开发文件

这些文件更偏开发、调试、扩展，不是普通使用者必须看的：

- 真实生成器实现：
  - [regmap_codegen.py](/Users/mac/work/se_reg/tools/regmap_codegen.py)
- 其他规格表示例：
  - [se_top_regmap.tsv](/Users/mac/work/se_reg/specs/se_top_regmap.tsv)
  - [se_top_regmap_compact.csv](/Users/mac/work/se_reg/specs/se_top_regmap_compact.csv)
- 自检 testbench：
  - [se_top_regfile_tb.sv](/Users/mac/work/se_reg/tb/se_top_regfile_tb.sv)
- 辅助命令：
  - [Makefile](/Users/mac/work/se_reg/Makefile)
- 忽略规则：
  - [.gitignore](/Users/mac/work/se_reg/.gitignore)

---

## 5. 仓库结构建议理解

```text
se_reg/
├── excel_to_verilog.py          # 普通用户用这个
├── excel_to_verilog.command     # macOS 双击入口
├── specs/                       # 放 Excel / CSV / TSV 规格表
├── include/                     # 生成的 .vh
├── rtl/                         # 生成的 .v
├── tools/                       # 生成器源码
├── tb/                          # testbench
├── Makefile                     # 辅助命令
└── README.md
```

你可以把它理解成：

- `specs/`：输入
- `include/`、`rtl/`：输出
- `tools/`、`tb/`：开发和验证

---

## 6. 验证生成结果

仓库里带了一个示例 testbench，可以用来验证示例生成结果：

```bash
cd /Users/mac/work/se_reg
make test
```

当前 testbench 会检查：

- `RW` 字段写入与读回
- `WO` 写使能和写数据
- `W1C` 置位与写 1 清零
- 部分 `RO` 字段读回路径

---

## 7. 一句话总结

如果你要教别人怎么用，最短版本就是：

1. 打开 [se_top_regmap_compact.xlsx](/Users/mac/work/se_reg/specs/se_top_regmap_compact.xlsx)
2. 修改寄存器表
3. 运行 `python3 excel_to_verilog.py`
4. 去 `rtl/` 和 `include/` 里拿生成结果
