SPEC ?= examples/se_top_regmap_compact.csv
TOOL := core/regmap_codegen.py
XLSX_SPEC := ../user_package/templates/se_top_regmap_compact.xlsx

.PHONY: regmap xlsx excel web test

regmap:
	python3 $(TOOL) $(SPEC)

xlsx:
	python3 $(TOOL) examples/se_top_regmap_compact.csv --export-xlsx $(XLSX_SPEC)

excel:
	python3 ../user_package/excel_to_verilog.py

web:
	python3 webui/server.py

test: regmap
	mkdir -p build/tb
	verilator --binary --sv --timing \
		--top-module se_top_regfile_tb \
		-Mdir build/tb \
		examples_output/rtl/se_top_regfile.v tests/se_top_regfile_tb.sv
	./build/tb/Vse_top_regfile_tb
