`timescale 1ns / 1ps

module se_top_regfile_tb;

    localparam int ADDR_WIDTH = 32;
    localparam int DATA_WIDTH = 32;

    localparam logic [ADDR_WIDTH-1:0] SE_CTRL_ADDR            = 32'h0000_0000;
    localparam logic [ADDR_WIDTH-1:0] SE_BOOT_PC_ADDR         = 32'h0000_0004;
    localparam logic [ADDR_WIDTH-1:0] SE_FETCH_CFG_ADDR       = 32'h0000_0008;
    localparam logic [ADDR_WIDTH-1:0] SE_ERR_STATUS_ADDR      = 32'h0000_0020;
    localparam logic [ADDR_WIDTH-1:0] SE_STATUS_ADDR          = 32'h0000_0010;

    logic clk = 1'b0;
    logic rst_n = 1'b0;
    logic wr_en;
    logic [ADDR_WIDTH-1:0] wr_addr;
    logic [DATA_WIDTH-1:0] wr_data;
    logic rd_en;
    logic [ADDR_WIDTH-1:0] rd_addr;
    logic [DATA_WIDTH-1:0] rd_data;

    logic se_ctrl_start_we_o;
    logic se_ctrl_start_wdata_o;
    logic se_ctrl_stop_we_o;
    logic se_ctrl_stop_wdata_o;
    logic se_ctrl_soft_reset_we_o;
    logic se_ctrl_soft_reset_wdata_o;
    logic se_ctrl_irq_en_o;
    logic [31:0] se_boot_pc_o;
    logic se_fetch_cfg_fetch_enable_o;
    logic [3:0] se_fetch_cfg_burst_beats_o;
    logic [7:0] se_fetch_cfg_fifo_waterline_o;
    logic se_mode_single_step_o;
    logic se_mode_trace_en_o;
    logic se_mode_halt_on_illegal_o;
    logic se_mode_halt_on_unsupported_o;
    logic se_status_running_i;
    logic se_status_idle_i;
    logic se_status_fetch_busy_i;
    logic se_status_decode_hold_i;
    logic se_status_lsu_pending_i;
    logic se_status_error_i;
    logic [31:0] se_pc_cur_i;
    logic [31:0] se_pc_last_commit_i;
    logic se_hold_reason_scalar_raw_i;
    logic se_hold_reason_scalar_waw_i;
    logic se_hold_reason_desc_raw_i;
    logic se_hold_reason_desc_waw_i;
    logic se_hold_reason_lsu_busy_i;
    logic se_hold_reason_ts_not_ready_i;
    logic se_hold_reason_fifo_empty_i;
    logic se_hold_reason_fifo_full_i;
    logic se_err_status_illegal_instr_set_i;
    logic se_err_status_illegal_instr_o;
    logic se_err_status_unsupported_instr_set_i;
    logic se_err_status_unsupported_instr_o;
    logic se_err_status_mif_error_set_i;
    logic se_err_status_mif_error_o;
    logic se_err_status_pc_unaligned_set_i;
    logic se_err_status_pc_unaligned_o;
    logic se_err_status_fifo_overflow_set_i;
    logic se_err_status_fifo_overflow_o;
    logic se_err_status_fifo_underflow_set_i;
    logic se_err_status_fifo_underflow_o;
    logic se_err_status_lsu_error_set_i;
    logic se_err_status_lsu_error_o;
    logic [31:0] se_err_pc_i;
    logic [31:0] se_err_inst_i;
    logic [2:0] se_err_info_engine_i;
    logic [5:0] se_err_info_desc_idx_i;
    logic [4:0] se_err_info_rd_i;
    logic [4:0] se_err_info_rs1_i;
    logic [4:0] se_err_info_rs2_i;
    logic se_err_clear_clear_mask_we_o;
    logic [31:0] se_err_clear_clear_mask_wdata_o;
    logic [31:0] se_cycle_cnt_l_i;
    logic [31:0] se_cycle_cnt_h_i;
    logic [31:0] se_inst_cnt_l_i;
    logic [31:0] se_inst_cnt_h_i;
    logic [31:0] se_fetch_req_cnt_i;
    logic [31:0] se_fetch_stall_cnt_i;
    logic [31:0] se_decode_hold_cnt_i;
    logic [31:0] se_issue_cnt_vec_i;
    logic [31:0] se_issue_cnt_tensor_i;
    logic [31:0] se_issue_cnt_tma_i;
    logic [31:0] se_issue_cnt_cv_i;
    logic [31:0] se_lsu_req_cnt_i;
    logic [31:0] se_last_inst_i;
    logic [5:0] se_last_desc_idx_i;
    logic [2:0] se_last_issue_info_engine_i;
    logic se_last_issue_info_issue_valid_i;
    logic se_last_issue_info_issue_ready_i;
    logic [7:0] se_fifo_level_i;
    logic [5:0] se_desc_dbg_addr_desc_dbg_idx_o;
    logic [31:0] se_desc_dbg_data0_desc_dbg_data_31_0_i;
    logic [31:0] se_desc_dbg_data1_desc_dbg_data_63_32_i;
    logic [31:0] se_desc_dbg_data2_desc_dbg_data_95_64_i;
    logic [31:0] se_desc_dbg_data3_desc_dbg_data_127_96_i;
    logic [31:0] se_desc_dbg_data4_desc_dbg_data_159_128_i;
    logic [31:0] se_desc_dbg_data5_desc_dbg_data_191_160_i;
    logic [31:0] se_desc_dbg_data6_desc_dbg_data_223_192_i;
    logic [31:0] se_desc_dbg_data7_desc_dbg_data_255_224_i;

    se_top_regfile dut (
        .clk(clk),
        .rst_n(rst_n),
        .wr_en(wr_en),
        .wr_addr(wr_addr),
        .wr_data(wr_data),
        .rd_en(rd_en),
        .rd_addr(rd_addr),
        .rd_data(rd_data),
        .se_ctrl_start_we_o(se_ctrl_start_we_o),
        .se_ctrl_start_wdata_o(se_ctrl_start_wdata_o),
        .se_ctrl_stop_we_o(se_ctrl_stop_we_o),
        .se_ctrl_stop_wdata_o(se_ctrl_stop_wdata_o),
        .se_ctrl_soft_reset_we_o(se_ctrl_soft_reset_we_o),
        .se_ctrl_soft_reset_wdata_o(se_ctrl_soft_reset_wdata_o),
        .se_ctrl_irq_en_o(se_ctrl_irq_en_o),
        .se_boot_pc_o(se_boot_pc_o),
        .se_fetch_cfg_fetch_enable_o(se_fetch_cfg_fetch_enable_o),
        .se_fetch_cfg_burst_beats_o(se_fetch_cfg_burst_beats_o),
        .se_fetch_cfg_fifo_waterline_o(se_fetch_cfg_fifo_waterline_o),
        .se_mode_single_step_o(se_mode_single_step_o),
        .se_mode_trace_en_o(se_mode_trace_en_o),
        .se_mode_halt_on_illegal_o(se_mode_halt_on_illegal_o),
        .se_mode_halt_on_unsupported_o(se_mode_halt_on_unsupported_o),
        .se_status_running_i(se_status_running_i),
        .se_status_idle_i(se_status_idle_i),
        .se_status_fetch_busy_i(se_status_fetch_busy_i),
        .se_status_decode_hold_i(se_status_decode_hold_i),
        .se_status_lsu_pending_i(se_status_lsu_pending_i),
        .se_status_error_i(se_status_error_i),
        .se_pc_cur_i(se_pc_cur_i),
        .se_pc_last_commit_i(se_pc_last_commit_i),
        .se_hold_reason_scalar_raw_i(se_hold_reason_scalar_raw_i),
        .se_hold_reason_scalar_waw_i(se_hold_reason_scalar_waw_i),
        .se_hold_reason_desc_raw_i(se_hold_reason_desc_raw_i),
        .se_hold_reason_desc_waw_i(se_hold_reason_desc_waw_i),
        .se_hold_reason_lsu_busy_i(se_hold_reason_lsu_busy_i),
        .se_hold_reason_ts_not_ready_i(se_hold_reason_ts_not_ready_i),
        .se_hold_reason_fifo_empty_i(se_hold_reason_fifo_empty_i),
        .se_hold_reason_fifo_full_i(se_hold_reason_fifo_full_i),
        .se_err_status_illegal_instr_set_i(se_err_status_illegal_instr_set_i),
        .se_err_status_illegal_instr_o(se_err_status_illegal_instr_o),
        .se_err_status_unsupported_instr_set_i(se_err_status_unsupported_instr_set_i),
        .se_err_status_unsupported_instr_o(se_err_status_unsupported_instr_o),
        .se_err_status_mif_error_set_i(se_err_status_mif_error_set_i),
        .se_err_status_mif_error_o(se_err_status_mif_error_o),
        .se_err_status_pc_unaligned_set_i(se_err_status_pc_unaligned_set_i),
        .se_err_status_pc_unaligned_o(se_err_status_pc_unaligned_o),
        .se_err_status_fifo_overflow_set_i(se_err_status_fifo_overflow_set_i),
        .se_err_status_fifo_overflow_o(se_err_status_fifo_overflow_o),
        .se_err_status_fifo_underflow_set_i(se_err_status_fifo_underflow_set_i),
        .se_err_status_fifo_underflow_o(se_err_status_fifo_underflow_o),
        .se_err_status_lsu_error_set_i(se_err_status_lsu_error_set_i),
        .se_err_status_lsu_error_o(se_err_status_lsu_error_o),
        .se_err_pc_i(se_err_pc_i),
        .se_err_inst_i(se_err_inst_i),
        .se_err_info_engine_i(se_err_info_engine_i),
        .se_err_info_desc_idx_i(se_err_info_desc_idx_i),
        .se_err_info_rd_i(se_err_info_rd_i),
        .se_err_info_rs1_i(se_err_info_rs1_i),
        .se_err_info_rs2_i(se_err_info_rs2_i),
        .se_err_clear_clear_mask_we_o(se_err_clear_clear_mask_we_o),
        .se_err_clear_clear_mask_wdata_o(se_err_clear_clear_mask_wdata_o),
        .se_cycle_cnt_l_i(se_cycle_cnt_l_i),
        .se_cycle_cnt_h_i(se_cycle_cnt_h_i),
        .se_inst_cnt_l_i(se_inst_cnt_l_i),
        .se_inst_cnt_h_i(se_inst_cnt_h_i),
        .se_fetch_req_cnt_i(se_fetch_req_cnt_i),
        .se_fetch_stall_cnt_i(se_fetch_stall_cnt_i),
        .se_decode_hold_cnt_i(se_decode_hold_cnt_i),
        .se_issue_cnt_vec_i(se_issue_cnt_vec_i),
        .se_issue_cnt_tensor_i(se_issue_cnt_tensor_i),
        .se_issue_cnt_tma_i(se_issue_cnt_tma_i),
        .se_issue_cnt_cv_i(se_issue_cnt_cv_i),
        .se_lsu_req_cnt_i(se_lsu_req_cnt_i),
        .se_last_inst_i(se_last_inst_i),
        .se_last_desc_idx_i(se_last_desc_idx_i),
        .se_last_issue_info_engine_i(se_last_issue_info_engine_i),
        .se_last_issue_info_issue_valid_i(se_last_issue_info_issue_valid_i),
        .se_last_issue_info_issue_ready_i(se_last_issue_info_issue_ready_i),
        .se_fifo_level_i(se_fifo_level_i),
        .se_desc_dbg_addr_desc_dbg_idx_o(se_desc_dbg_addr_desc_dbg_idx_o),
        .se_desc_dbg_data0_desc_dbg_data_31_0_i(se_desc_dbg_data0_desc_dbg_data_31_0_i),
        .se_desc_dbg_data1_desc_dbg_data_63_32_i(se_desc_dbg_data1_desc_dbg_data_63_32_i),
        .se_desc_dbg_data2_desc_dbg_data_95_64_i(se_desc_dbg_data2_desc_dbg_data_95_64_i),
        .se_desc_dbg_data3_desc_dbg_data_127_96_i(se_desc_dbg_data3_desc_dbg_data_127_96_i),
        .se_desc_dbg_data4_desc_dbg_data_159_128_i(se_desc_dbg_data4_desc_dbg_data_159_128_i),
        .se_desc_dbg_data5_desc_dbg_data_191_160_i(se_desc_dbg_data5_desc_dbg_data_191_160_i),
        .se_desc_dbg_data6_desc_dbg_data_223_192_i(se_desc_dbg_data6_desc_dbg_data_223_192_i),
        .se_desc_dbg_data7_desc_dbg_data_255_224_i(se_desc_dbg_data7_desc_dbg_data_255_224_i)
    );

    always #5 clk = ~clk;

    task automatic clear_bus();
        begin
            wr_en   = 1'b0;
            wr_addr = '0;
            wr_data = '0;
            rd_en   = 1'b0;
            rd_addr = '0;
        end
    endtask

    task automatic write_reg(
        input logic [ADDR_WIDTH-1:0] addr,
        input logic [DATA_WIDTH-1:0] data
    );
        begin
            @(negedge clk);
            wr_en   = 1'b1;
            wr_addr = addr;
            wr_data = data;
            @(posedge clk);
            #1;
            @(negedge clk);
            wr_en   = 1'b0;
            wr_addr = '0;
            wr_data = '0;
        end
    endtask

    task automatic expect_read(
        input logic [ADDR_WIDTH-1:0] addr,
        input logic [DATA_WIDTH-1:0] expected,
        input string label
    );
        begin
            rd_en   = 1'b1;
            rd_addr = addr;
            #1;
            if (rd_data !== expected) begin
                $display("[FAIL] %s expected=0x%08x got=0x%08x", label, expected, rd_data);
                $fatal(1);
            end
            rd_en   = 1'b0;
            rd_addr = '0;
        end
    endtask

    initial begin
        clear_bus();

        {
            se_status_running_i,
            se_status_idle_i,
            se_status_fetch_busy_i,
            se_status_decode_hold_i,
            se_status_lsu_pending_i,
            se_status_error_i,
            se_hold_reason_scalar_raw_i,
            se_hold_reason_scalar_waw_i,
            se_hold_reason_desc_raw_i,
            se_hold_reason_desc_waw_i,
            se_hold_reason_lsu_busy_i,
            se_hold_reason_ts_not_ready_i,
            se_hold_reason_fifo_empty_i,
            se_hold_reason_fifo_full_i,
            se_err_status_illegal_instr_set_i,
            se_err_status_unsupported_instr_set_i,
            se_err_status_mif_error_set_i,
            se_err_status_pc_unaligned_set_i,
            se_err_status_fifo_overflow_set_i,
            se_err_status_fifo_underflow_set_i,
            se_err_status_lsu_error_set_i,
            se_last_issue_info_issue_valid_i,
            se_last_issue_info_issue_ready_i
        } = '0;

        se_pc_cur_i = '0;
        se_pc_last_commit_i = '0;
        se_err_pc_i = '0;
        se_err_inst_i = '0;
        se_err_info_engine_i = '0;
        se_err_info_desc_idx_i = '0;
        se_err_info_rd_i = '0;
        se_err_info_rs1_i = '0;
        se_err_info_rs2_i = '0;
        se_cycle_cnt_l_i = '0;
        se_cycle_cnt_h_i = '0;
        se_inst_cnt_l_i = '0;
        se_inst_cnt_h_i = '0;
        se_fetch_req_cnt_i = '0;
        se_fetch_stall_cnt_i = '0;
        se_decode_hold_cnt_i = '0;
        se_issue_cnt_vec_i = '0;
        se_issue_cnt_tensor_i = '0;
        se_issue_cnt_tma_i = '0;
        se_issue_cnt_cv_i = '0;
        se_lsu_req_cnt_i = '0;
        se_last_inst_i = '0;
        se_last_desc_idx_i = '0;
        se_last_issue_info_engine_i = '0;
        se_fifo_level_i = '0;
        se_desc_dbg_data0_desc_dbg_data_31_0_i = '0;
        se_desc_dbg_data1_desc_dbg_data_63_32_i = '0;
        se_desc_dbg_data2_desc_dbg_data_95_64_i = '0;
        se_desc_dbg_data3_desc_dbg_data_127_96_i = '0;
        se_desc_dbg_data4_desc_dbg_data_159_128_i = '0;
        se_desc_dbg_data5_desc_dbg_data_191_160_i = '0;
        se_desc_dbg_data6_desc_dbg_data_223_192_i = '0;
        se_desc_dbg_data7_desc_dbg_data_255_224_i = '0;

        repeat (3) @(posedge clk);
        rst_n = 1'b1;
        #1;

        expect_read(SE_BOOT_PC_ADDR, 32'h0000_0000, "boot_pc reset");
        expect_read(SE_FETCH_CFG_ADDR, 32'h0000_0000, "fetch_cfg reset");

        write_reg(SE_BOOT_PC_ADDR, 32'h1234_5678);
        expect_read(SE_BOOT_PC_ADDR, 32'h1234_5678, "boot_pc rw");

        write_reg(SE_FETCH_CFG_ADDR, 32'h0000_AB51);
        if (se_fetch_cfg_fetch_enable_o !== 1'b1 ||
            se_fetch_cfg_burst_beats_o !== 4'h5 ||
            se_fetch_cfg_fifo_waterline_o !== 8'hAB) begin
            $display("[FAIL] fetch_cfg outputs mismatch");
            $fatal(1);
        end
        expect_read(SE_FETCH_CFG_ADDR, 32'h0000_AB51, "fetch_cfg rw");

        @(negedge clk);
        wr_en   = 1'b1;
        wr_addr = SE_CTRL_ADDR;
        wr_data = 32'h0000_000D;
        #1;
        if (se_ctrl_start_we_o !== 1'b1 || se_ctrl_start_wdata_o !== 1'b1 ||
            se_ctrl_stop_we_o !== 1'b1 || se_ctrl_stop_wdata_o !== 1'b0 ||
            se_ctrl_soft_reset_we_o !== 1'b1 || se_ctrl_soft_reset_wdata_o !== 1'b1) begin
            $display("[FAIL] wo control outputs mismatch");
            $fatal(1);
        end
        @(posedge clk);
        #1;
        if (se_ctrl_irq_en_o !== 1'b1) begin
            $display("[FAIL] irq_en rw bit mismatch");
            $fatal(1);
        end
        @(negedge clk);
        clear_bus();
        expect_read(SE_CTRL_ADDR, 32'h0000_0008, "ctrl readback");

        se_status_running_i     = 1'b1;
        se_status_fetch_busy_i  = 1'b1;
        se_status_error_i       = 1'b1;
        expect_read(SE_STATUS_ADDR, 32'h0000_0025, "status ro");

        se_err_status_illegal_instr_set_i = 1'b1;
        se_err_status_fifo_overflow_set_i = 1'b1;
        @(posedge clk);
        #1;
        se_err_status_illegal_instr_set_i = 1'b0;
        se_err_status_fifo_overflow_set_i = 1'b0;
        expect_read(SE_ERR_STATUS_ADDR, 32'h0000_0011, "err_status set");

        write_reg(SE_ERR_STATUS_ADDR, 32'h0000_0001);
        expect_read(SE_ERR_STATUS_ADDR, 32'h0000_0010, "err_status clear one bit");

        $display("[PASS] se_top_regfile_tb");
        $finish;
    end

endmodule
