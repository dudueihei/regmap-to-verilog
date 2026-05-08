# 用户使用说明

这个目录是给普通使用者的。

你只需要关心这几个文件：

- Excel 模板：
  [se_top_regmap_compact.xlsx](/Users/mac/work/se_reg/user_package/templates/se_top_regmap_compact.xlsx)
- 命令行一键生成：
  [excel_to_verilog.py](/Users/mac/work/se_reg/user_package/excel_to_verilog.py)
- macOS 双击生成：
  [excel_to_verilog.command](/Users/mac/work/se_reg/user_package/excel_to_verilog.command)
- 网页版启动：
  [start_web.command](/Users/mac/work/se_reg/user_package/start_web.command)

## 最简单的用法

### 方法 1：网页方式

最推荐给非开发同学使用。

1. 双击：
   [start_web.command](/Users/mac/work/se_reg/user_package/start_web.command)
2. 浏览器打开：
   `http://127.0.0.1:8765`
3. 拖入 `.xlsx`
4. 填一个输出目录
5. 点击“生成 Verilog”

生成后会自动输出到你填写的目录下：

```text
输出目录/
├── include/
│   └── xxx_regs.vh
└── rtl/
    └── xxx_regfile.v
```

### 方法 2：命令行方式

如果你已经修改好了 Excel：

```bash
cd user_package
python3 excel_to_verilog.py
```

默认会优先使用：

```text
templates/se_top_regmap_compact.xlsx
```

默认输出到：

```text
output/include/
output/rtl/
```

如果你要手动指定某个 Excel：

```bash
cd user_package
python3 excel_to_verilog.py 你的表格.xlsx
```

## Excel 表头建议

推荐表头：

```text
偏移地址,寄存器名,字段名,位段,属性,复位值,描述
```

位段写法支持：

- `0`
- `7:4`
- `31:0`

属性支持：

- `RW`
- `RO`
- `WO`
- `W1C`
