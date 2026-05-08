SPEC ?= specs/se_top_regmap_compact.csv
TOOL := tools/regmap_codegen.py
XLSX_SPEC := specs/se_top_regmap_compact.xlsx

.PHONY: regmap xlsx excel test

regmap:
	python3 $(TOOL) $(SPEC)

xlsx:
	python3 $(TOOL) specs/se_top_regmap_compact.csv --export-xlsx $(XLSX_SPEC)

excel:
	python3 excel_to_verilog.py

test: regmap
	mkdir -p build/tb
	verilator --binary --sv --timing \
		--top-module se_top_regfile_tb \
		-Mdir build/tb \
		rtl/se_top_regfile.v tb/se_top_regfile_tb.sv
	./build/tb/Vse_top_regfile_tb
