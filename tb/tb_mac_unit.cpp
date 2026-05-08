//=============================================================================
// ADA300 SNPU - MAC Unit Testbench (Verilator C++)
//=============================================================================
// Build & Run:
//   make sim
//=============================================================================

#include <verilated.h>
#include <verilated_vcd_c.h>
#include <iostream>
#include <cstdint>
#include <cmath>

#include "Vsnpu_mac_unit.h"

#define CLK_PERIOD 10  // 10ns = 100MHz

static vluint64_t main_time = 0;

double sc_time_stamp() {
    return main_time;
}

void tick(Vsnpu_mac_unit* dut, VerilatedVcdC* tfp) {
    dut->clk = 0;
    dut->eval();
    if (tfp) tfp->dump(main_time);
    main_time += CLK_PERIOD / 2;

    dut->clk = 1;
    dut->eval();
    if (tfp) tfp->dump(main_time);
    main_time += CLK_PERIOD / 2;
}

void reset(Vsnpu_mac_unit* dut, VerilatedVcdC* tfp) {
    dut->rst_n = 0;
    dut->en = 0;
    dut->clr_acc = 0;
    dut->act_in = 0;
    dut->wgt_in = 0;
    dut->acc_in = 0;

    for (int i = 0; i < 5; i++) {
        tick(dut, tfp);
    }
    dut->rst_n = 1;
    tick(dut, tfp);
}

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    Verilated::traceEverOn(true);

    Vsnpu_mac_unit* dut = new Vsnpu_mac_unit;
    VerilatedVcdC* tfp = new VerilatedVcdC;

    dut->trace(tfp, 99);
    tfp->open("wave_mac_unit.vcd");

    std::cout << "=============================================" << std::endl;
    std::cout << "ADA300 SNPU - MAC Unit Testbench" << std::endl;
    std::cout << "=============================================" << std::endl;

    reset(dut, tfp);

    // Test 1: Clear-and-multiply (ignore acc_in)
    // clr=1: result = (3 * 5) = 15
    std::cout << "\n[Test 1] Clear + Multiply: (3 * 5) = 15" << std::endl;
    dut->en = 1;
    dut->clr_acc = 1;
    dut->act_in = 3;
    dut->wgt_in = 5;
    dut->acc_in = 10;  // should be ignored due to clr_acc=1
    tick(dut, tfp);  // S0
    tick(dut, tfp);  // S1
    tick(dut, tfp);  // S2 -> result
    tick(dut, tfp);  // capture valid

    if (dut->valid_out && dut->acc_out == 15) {
        std::cout << "  PASS: acc_out = " << (int)dut->acc_out << std::endl;
    } else {
        std::cout << "  FAIL: acc_out = " << (int)dut->acc_out
                  << ", valid = " << dut->valid_out << std::endl;
    }

    // Test 2: Accumulate with external acc_in
    // clr=0: result = (-4 * 7) + 20 = -8
    std::cout << "\n[Test 2] Accumulate: (-4 * 7) + 20 = -8" << std::endl;
    dut->clr_acc = 0;
    dut->act_in = -4;
    dut->wgt_in = 7;
    dut->acc_in = 20;
    tick(dut, tfp);
    tick(dut, tfp);
    tick(dut, tfp);
    tick(dut, tfp);

    if (dut->valid_out && dut->acc_out == -8) {
        std::cout << "  PASS: acc_out = " << (int)dut->acc_out << std::endl;
    } else {
        std::cout << "  FAIL: acc_out = " << (int)dut->acc_out
                  << ", valid = " << dut->valid_out << std::endl;
    }

    // Test 3: Accumulation mode (no clear)
    // First: (2 * 3) = 6
    // Second: (4 * 5) + 6 = 26
    std::cout << "\n[Test 3] Accumulation mode" << std::endl;
    dut->clr_acc = 1;
    dut->act_in = 2;
    dut->wgt_in = 3;
    dut->acc_in = 0;
    tick(dut, tfp);
    tick(dut, tfp);
    tick(dut, tfp);
    tick(dut, tfp);

    int first_result = dut->acc_out;
    std::cout << "  First: (2 * 3) = " << first_result << std::endl;

    dut->clr_acc = 0;  // Accumulate!
    dut->act_in = 4;
    dut->wgt_in = 5;
    dut->acc_in = first_result;
    tick(dut, tfp);
    tick(dut, tfp);
    tick(dut, tfp);
    tick(dut, tfp);

    if (dut->valid_out && dut->acc_out == 26) {
        std::cout << "  PASS: (4 * 5) + " << first_result << " = "
                  << (int)dut->acc_out << std::endl;
    } else {
        std::cout << "  FAIL: acc_out = " << (int)dut->acc_out << std::endl;
    }

    // Test 4: Saturation / large values
    // 127 * 127 = 16129 (fits in 32-bit easily)
    std::cout << "\n[Test 4] Max INT8 values: 127 * 127 = 16129" << std::endl;
    dut->clr_acc = 1;
    dut->act_in = 127;
    dut->wgt_in = 127;
    dut->acc_in = 0;
    tick(dut, tfp);
    tick(dut, tfp);
    tick(dut, tfp);
    tick(dut, tfp);

    if (dut->valid_out && dut->acc_out == 16129) {
        std::cout << "  PASS: acc_out = " << (int)dut->acc_out << std::endl;
    } else {
        std::cout << "  FAIL: acc_out = " << (int)dut->acc_out << std::endl;
    }

    // Finish
    dut->en = 0;
    for (int i = 0; i < 5; i++) tick(dut, tfp);

    std::cout << "\n=============================================" << std::endl;
    std::cout << "Testbench finished. VCD: wave_mac_unit.vcd" << std::endl;
    std::cout << "=============================================" << std::endl;

    tfp->close();
    delete tfp;
    delete dut;

    return 0;
}
