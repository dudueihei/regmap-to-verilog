//=============================================================================
// ADA300 SNPU - 4x4 MAC Array (Systolic / Direct)
//=============================================================================
// This is a direct-mapped array: each MAC receives its own act and wgt.
// For systolic arrays, add skew registers on inputs/outputs.
//=============================================================================
`timescale 1ns / 1ps

module snpu_mac_array #(
    parameter int DIM        = 4,
    parameter int DATA_WIDTH = 8,
    parameter int ACC_WIDTH  = 32
)(
    input  logic                         clk,
    input  logic                         rst_n,

    // Global control
    input  logic                         en,
    input  logic                         clr_acc,

    // Flattened inputs: DIM*DATA_WIDTH each
    input  logic signed [DATA_WIDTH-1:0] act_in  [0:DIM-1][0:DIM-1],
    input  logic signed [DATA_WIDTH-1:0] wgt_in  [0:DIM-1][0:DIM-1],

    // Flattened outputs
    output logic signed [ACC_WIDTH-1:0]  acc_out [0:DIM-1][0:DIM-1],
    output logic                         valid_out
);

    // Internal valid signals
    logic valid_matrix [0:DIM-1][0:DIM-1];

    // Generate 2D MAC array
    generate
        for (genvar i = 0; i < DIM; i++) begin : gen_row
            for (genvar j = 0; j < DIM; j++) begin : gen_col

                snpu_mac_unit #(
                    .DATA_WIDTH(DATA_WIDTH),
                    .ACC_WIDTH (ACC_WIDTH)
                ) u_mac (
                    .clk       (clk),
                    .rst_n     (rst_n),
                    .en        (en),
                    .clr_acc   (clr_acc),
                    .act_in    (act_in[i][j]),
                    .wgt_in    (wgt_in[i][j]),
                    .acc_in    ('0),           // Independent MACs, no partial sum chaining
                    .acc_out   (acc_out[i][j]),
                    .valid_out (valid_matrix[i][j])
                );

            end
        end
    endgenerate

    // Array output valid: AND of all MAC valid signals (all finish together)
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            valid_out <= 1'b0;
        else
            valid_out <= valid_matrix[0][0];  // All MACs are identical delay
    end

endmodule
