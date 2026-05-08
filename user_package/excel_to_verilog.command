#!/bin/zsh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ "$#" -gt 0 ]; then
  /usr/bin/env python3 "$SCRIPT_DIR/excel_to_verilog.py" "$1"
else
  /usr/bin/env python3 "$SCRIPT_DIR/excel_to_verilog.py"
fi

echo ""
echo "按回车退出..."
read
