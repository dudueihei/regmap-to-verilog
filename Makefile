SPEC ?= specs/se_top_regmap_compact.csv
TOOL := tools/regmap_codegen.py

.PHONY: regmap

regmap:
	python3 $(TOOL) $(SPEC)
