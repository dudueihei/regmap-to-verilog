#!/usr/bin/env python3
"""
One-shot Excel-to-Verilog wrapper.

Usage:
1. Put an .xlsx file into templates/ or pass a file path explicitly
2. Run:
   python3 excel_to_verilog.py

Or explicitly:
   python3 excel_to_verilog.py your_regmap.xlsx
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


USER_ROOT = Path(__file__).resolve().parent
REPO_ROOT = USER_ROOT.parent
TEMPLATE_DIR = USER_ROOT / "templates"
GENERATOR = REPO_ROOT / "internal_package" / "core" / "regmap_codegen.py"
OUTPUT_ROOT = USER_ROOT / "output"
RTL_DIR = OUTPUT_ROOT / "rtl"
INCLUDE_DIR = OUTPUT_ROOT / "include"


def pick_default_xlsx() -> Path:
    preferred = TEMPLATE_DIR / "se_top_regmap_compact.xlsx"
    if preferred.exists():
        return preferred

    candidates = sorted(TEMPLATE_DIR.glob("*.xlsx"))
    if not candidates:
        raise FileNotFoundError(
            f"templates/ 下没有找到 .xlsx 文件，请先放入 Excel 表。\n"
            f"例如：{preferred}"
        )
    if len(candidates) == 1:
        return candidates[0]

    latest = max(candidates, key=lambda path: path.stat().st_mtime)
    print(f"[INFO] 检测到多个 xlsx，默认使用最新文件：{latest}")
    return latest


def output_paths(spec: Path) -> tuple[Path, Path]:
    module_name = spec.stem.lower()
    if module_name.endswith("_regmap_compact"):
        module_name = module_name[: -len("_regmap_compact")]
    elif module_name.endswith("_regmap"):
        module_name = module_name[: -len("_regmap")]

    return (
        INCLUDE_DIR / f"{module_name}_regs.vh",
        RTL_DIR / f"{module_name}_regfile.v",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="直接从 Excel 规格表生成 Verilog")
    parser.add_argument("xlsx", nargs="?", type=Path, help="Excel 规格表路径（.xlsx）")
    args = parser.parse_args()

    spec = args.xlsx if args.xlsx is not None else pick_default_xlsx()
    if not spec.exists():
        raise FileNotFoundError(f"找不到文件：{spec}")
    if spec.suffix.lower() != ".xlsx":
        raise ValueError(f"只接受 .xlsx 文件，当前输入为：{spec}")

    out_vh, out_v = output_paths(spec)
    cmd = [
        sys.executable,
        str(GENERATOR),
        str(spec),
        "--out-vh",
        str(out_vh),
        "--out-v",
        str(out_v),
    ]
    subprocess.run(cmd, check=True, cwd=REPO_ROOT)

    print("")
    print("[DONE] Excel -> Verilog 完成")
    print(f"[DONE] 输入表: {spec}")
    print(f"[DONE] 头文件: {out_vh}")
    print(f"[DONE] RTL   : {out_v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
