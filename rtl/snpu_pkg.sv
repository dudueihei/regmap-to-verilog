//=============================================================================
// ADA300 SNPU - Common Package
//=============================================================================
`timescale 1ns / 1ps

`ifndef SNPU_PKG_SV
`define SNPU_PKG_SV

package snpu_pkg;

    // Data width definitions
    localparam int DATA_WIDTH     = 8;    // INT8 activation/weight
    localparam int ACC_WIDTH      = 32;   // INT32 accumulator
    localparam int MAC_ARRAY_DIM  = 4;    // 4x4 MAC array

    // Activation function types
    typedef enum logic [2:0] {
        ACT_NONE   = 3'b000,
        ACT_RELU   = 3'b001,
        ACT_SILU   = 3'b010,
        ACT_SIGMOID= 3'b011,
        ACT_TANH   = 3'b100
    } act_e;

    // Operation modes
    typedef enum logic [1:0] {
        MODE_IDLE    = 2'b00,
       _MODE_MAC     = 2'b01,
        MODE_ACT     = 2'b10,
        MODE_REDUCE  = 2'b11
    } mode_e;

endpackage
`endif
