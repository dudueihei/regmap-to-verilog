//=============================================================================
// ADA300 SNPU - Single MAC Unit (INT8 x INT8 -> INT32)
//=============================================================================
// Pipeline stages:
//   S0: Register inputs
//   S1: Signed multiplication
//   S2: Accumulate with previous partial sum
//=============================================================================
`timescale 1ns / 1ps

module snpu_mac_unit #(
    parameter int DATA_WIDTH = 8,
    parameter int ACC_WIDTH  = 32
)(
    input  logic                    clk,
    input  logic                    rst_n,

    // Control
    input  logic                    en,         // enable this MAC
    input  logic                    clr_acc,    // clear accumulator

    // Data interface
    input  logic signed [DATA_WIDTH-1:0] act_in,     // activation (feature)
    input  logic signed [DATA_WIDTH-1:0] wgt_in,     // weight
    input  logic signed [ACC_WIDTH-1:0]  acc_in,     // partial sum from previous MAC

    output logic signed [ACC_WIDTH-1:0]  acc_out,    // accumulated result
    output logic                         valid_out   // output valid
);

    // Pipeline registers
    logic signed [DATA_WIDTH-1:0]  act_s0, wgt_s0;
    logic signed [2*DATA_WIDTH-1:0] mult_s1;
    logic signed [ACC_WIDTH-1:0]   acc_s1;
    logic                           en_s0, en_s1;
    logic                           clr_s0, clr_s1;

    //=========================================================================
    // Stage 0: Input registration
    //=========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            act_s0 <= '0;
            wgt_s0 <= '0;
            acc_s1 <= '0;
            en_s0  <= 1'b0;
            clr_s0 <= 1'b0;
        end else begin
            if (en) begin
                act_s0 <= act_in;
                wgt_s0 <= wgt_in;
            end
            acc_s1 <= acc_in;   // carry partial sum through
            en_s0  <= en;
            clr_s0 <= clr_acc;
        end
    end

    //=========================================================================
    // Stage 1: Multiplication
    //=========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            mult_s1 <= '0;
            en_s1   <= 1'b0;
            clr_s1  <= 1'b0;
        end else begin
            if (en_s0) begin
                mult_s1 <= act_s0 * wgt_s0;
            end
            en_s1  <= en_s0;
            clr_s1 <= clr_s0;
        end
    end

    //=========================================================================
    // Stage 2: Accumulation
    //=========================================================================
    logic signed [ACC_WIDTH-1:0] mult_ext;
    logic signed [ACC_WIDTH-1:0] acc_next;

    assign mult_ext = ACC_WIDTH'(mult_s1);

    always_comb begin
        if (clr_s1)
            acc_next = mult_ext;
        else
            acc_next = acc_s1 + mult_ext;
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            acc_out   <= '0;
            valid_out <= 1'b0;
        end else begin
            if (en_s1) begin
                acc_out <= acc_next;
            end
            valid_out <= en_s1;
        end
    end

endmodule
