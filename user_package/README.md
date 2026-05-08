# 用户使用说明

这个工具只保留两种使用方式：

1. 浏览器打开生成
2. 命令行生成

先改这个 Excel 模板：

- [se_top_regmap_compact.xlsx](/Users/mac/work/se_reg/user_package/templates/se_top_regmap_compact.xlsx)

---

## 方式 1：浏览器打开生成

最适合普通使用者。

### 第一步

双击这个文件：

- [start_web.command](/Users/mac/work/se_reg/user_package/start_web.command)

### 第二步

浏览器会自动打开这个页面：

```text
http://127.0.0.1:8765
```

### 第三步

在网页里按顺序做 3 件事：

1. 拖入你的 `.xlsx`
2. 填写输出目录
3. 点击“生成 Verilog”

### 第四步

去你填写的输出目录里拿结果：

```text
输出目录/
├── include/
│   └── xxx_regs.vh
└── rtl/
    └── xxx_regfile.v
```

---

## 方式 2：命令行生成

适合会用终端的人。

### 直接生成默认模板

```bash
cd user_package
python3 excel_to_verilog.py
```

默认输入：

```text
templates/se_top_regmap_compact.xlsx
```

默认输出：

```text
output/include/
output/rtl/
```

### 指定你自己的 Excel

```bash
cd user_package
python3 excel_to_verilog.py 你的表格.xlsx
```

---

## Excel 表头怎么写

推荐表头：

```text
偏移地址,寄存器名,字段名,位段,属性,复位值,描述
```

示例：

```text
偏移地址,寄存器名,字段名,位段,属性,复位值,描述
0x0,SE_CTRL,start,0,WO,,写1启动
,,stop,1,WO,,写1停止
0x4,SE_BOOT_PC,boot_pc,31:0,RW,,启动PC
```

支持的位段写法：

- `0`
- `7:4`
- `31:0`

支持的属性：

- `RW`
- `RO`
- `WO`
- `W1C`

---

## 你真正要看的文件

普通使用者只需要看这 3 个：

- 模板：
  [se_top_regmap_compact.xlsx](/Users/mac/work/se_reg/user_package/templates/se_top_regmap_compact.xlsx)
- 浏览器模式：
  [start_web.command](/Users/mac/work/se_reg/user_package/start_web.command)
- 命令行模式：
  [excel_to_verilog.py](/Users/mac/work/se_reg/user_package/excel_to_verilog.py)
