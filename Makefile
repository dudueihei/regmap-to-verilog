#=============================================================================
# ADA300 SNPU - RTL Simulation Makefile
#=============================================================================
# Tools: Verilator (simulation), GTKWave/Surfer (waveform viewing)
#=============================================================================

# Directories
RTL_DIR   := rtl
TB_DIR    := tb
SIM_DIR   := sim
WAVE_DIR  := waves
SPEC_DIR  := specs
TOOL_DIR  := tools

# Verilator settings
VERILATOR := verilator
VFLAGS    := --cc --exe --build --trace \
             -Wall \
             -Wno-UNUSEDSIGNAL \
             -Wno-UNUSEDPARAM \
             -I$(RTL_DIR) \
             -Mdir $(SIM_DIR)/obj \
             --top-module snpu_mac_unit

# Source files
RTL_SRCS  := $(RTL_DIR)/snpu_pkg.sv \
             $(RTL_DIR)/snpu_mac_unit.sv

TB_SRC    := $(TB_DIR)/tb_mac_unit.cpp

# Output
EXEC      := $(SIM_DIR)/Vsnpu_mac_unit
WAVE      := $(WAVE_DIR)/wave_mac_unit.vcd
REGMAP_SPEC := $(SPEC_DIR)/se_top_regmap_compact.csv
REGMAP_TOOL := $(TOOL_DIR)/regmap_codegen.py

#=============================================================================
# Targets
#=============================================================================

.PHONY: all sim wave lint regmap clean help

all: sim

# Build and run simulation
sim: $(EXEC)
	@mkdir -p $(WAVE_DIR)
	cd $(SIM_DIR) && ./obj/Vsnpu_mac_unit
	@echo ""
	@echo "Simulation complete. Waveform: $(WAVE)"

# Compile Verilator model
$(EXEC): $(RTL_SRCS) $(TB_SRC)
	@mkdir -p $(SIM_DIR)/obj
	$(VERILATOR) $(VFLAGS) $(RTL_SRCS) $(TB_SRC) -o Vsnpu_mac_unit

# View waveform with GTKWave
wave:
	@if [ -f $(WAVE) ]; then \
		gtkwave $(WAVE) & \
	else \
		echo "No waveform found. Run 'make sim' first."; \
	fi

# View waveform with Surfer (if installed)
surfer:
	@if [ -f $(WAVE) ]; then \
		surfer $(WAVE) & \
	else \
		echo "No waveform found. Run 'make sim' first."; \
	fi

# Lint only (fast check)
lint:
	$(VERILATOR) --lint-only -Wall -I$(RTL_DIR) $(RTL_SRCS)

# Generate register artifacts from spreadsheet-style spec
regmap: $(REGMAP_SPEC) $(REGMAP_TOOL)
	python3 $(REGMAP_TOOL) $(REGMAP_SPEC)

# Format RTL with verible (if installed)
fmt:
	@which verible-verilog-format >/dev/null 2>&1 || \
		(echo "verible-verilog-format not found. Install: brew install verible" && exit 1)
	verible-verilog-format --inplace \
		--indentation_spaces=4 \
		--column_limit=100 \
		$(RTL_SRCS)

# Clean build artifacts
clean:
	rm -rf $(SIM_DIR)/obj
	rm -f $(WAVE_DIR)/*.vcd
	rm -f waveform.vcd

# Help
help:
	@echo "ADA300 SNPU RTL Build System"
	@echo ""
	@echo "Targets:"
	@echo "  make sim     - Build and run MAC unit simulation"
	@echo "  make wave    - Open waveform with GTKWave"
	@echo "  make surfer  - Open waveform with Surfer"
	@echo "  make lint    - Run Verilator lint check only"
	@echo "  make regmap  - Regenerate SE register .vh/.v from $(REGMAP_SPEC)"
	@echo "  make fmt     - Format RTL with Verible"
	@echo "  make clean   - Remove build artifacts"
	@echo "  make help    - Show this help"
