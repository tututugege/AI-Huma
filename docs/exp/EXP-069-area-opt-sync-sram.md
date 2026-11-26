# EXP-069：5 项代码/结构清理 + 全核 100% 严格同步 1R1W/1RW SRAM 化（`SRAM_BLACKBOX`）

- **日期**：2026-11-26
- **分支**：`trace-model` `exp/area-opt`；`rtl` `rtl/area-opt`
- **状态**：已合入 `main`（2026-11-26）
- **背景**：在全核 23 模块 TSMC 28nm DC 时序突破 1.12 GHz 并完成 386 点 RTL SPEC06 全量对齐后，集中解决两类物理实现债务：① 后端与总线代码中的固化开关、死线、冗余字段与超长顶层胶水；② 全核存储阵列（L1I / L1D / L2 STLB / 4 MiB LLC / ROB 指令字 / ~590 KiB BPU）彻底告别组合读 RAM（删除 `ttg_sram_rf.sv` 与 `bpu_mem.sv`），统一接入严格 1 拍同步读 `ttg_sram_1r1w` / `ttg_sram_1rw`，支持 `-DSRAM_BLACKBOX` 实现全核大型存储子系统 28nm DC 签核。

## 1. 关键改动

### 1.1 5 项代码、命名与结构体精简
1. 删除全核 113 处固化开关与死分支；
2. 清理 LSU 5 根历史死线；
3. 统一前端/后端队列命名（`front2ftq_*`、`ftq2front_*`、`ibuf2idu_*`）与 `IQ_*` 枚举；
4. 删除 `bpu_pkg.sv` 中 22 个 pre-FTB 死符号；
5. 将 `back_top.sv` 内部 9 组宽总线打包为 `packed struct`（`back_top.sv` 由 1,650 行压缩至 563 行）。

### 1.2 全核 100% 严格同步 1R1W/1RW SRAM 化
- **公共原语（`rtl/common/sram/`）**：统一 `ttg_sram_1r1w.sv`（支持 `WRITE_FIRST`、`INIT_VAL`、`parameter [255:0] TAG`、DC Presto 零报错 `SRAM_BLACKBOX` 单字输出寄存 stub）与 `ttg_sram_1rw.sv`；彻底删除组合读 `ttg_sram_rf.sv` 与 `bpu_mem.sv`（全仓 0 残留）。
- **L1I Cache（32 KiB，0 周期变化）**：`icache_arr.sv` 4×8 组 `16×512b` 数据体改为 `ttg_sram_1r1w`（`ICACHE_DATA`, `WRITE_FIRST=1`），经 `front_fifo.next_rdata → fetch_addr_fifo.next_rd_* → front_fetch_buf.ic_next_{fa,b}_idx` 与 `icache_ctl.arr_next_*` 提前 1 拍预发射读址，附 SVA 断言验证 100% 命中。
- **BPU（~590 KiB，同步 `trace-model`）**：新增 `bpu_sram_sync.sv`（支持按读口配置 `WF_MASK`），将 `u_ftb1`/`u_aftb`/`u_aftb2`/`u_atage`/`u_atage2`/`u_s2_tage`/`u_s2_sc`/`u_s2_itt`/`u_aitt`/`u_aitt2` 及 `u_rec`（512 项偶/奇双 bank）、`u_rf_rec`（256 项偶/奇双 bank，经 `core_front.out_rf_blk` 预发射读址）全部转为严格同步 `ttg_sram_1r1w`；仅保留 S0 小表 `u_ftb0`（64×4 FF）。预测通路 0 周期变化并消除 `ah_pipe_q[0].raw`/`ah2_pipe_q[0]`/`r1_raw_q`/`r1_raw_b_q` 巨型 FF 阵；提交训练改为严格 2 拍同步 RMW（`T0 → T1`，`u_s2_sc` 补 `T1→T0` LHT 前递、`u_ftb1` 1 项 `clr_pend_q` 仲裁、`u_uhi` 1/2048 复位优先），同步 `trace-model/front-end/BPU/{BPU_pipe,BpuFtb,BpuSc}.h`。
- **ROB / 缓存 / TLB**：
  - `rob_core_cpt.sv` 增 8×`32×32b`（1 KiB）严格同步 `ttg_sram_1r1w`（`ROB_INST_WORD`）修复 Fuzzer 检出的执行期 FP 非法指令 `mtval=0` 缺陷，并将 29 级串行 `oldest_trap` 改为 3 级并行锦标赛树将 WNS 由 `−0.95 ns` 拉回 `−0.15 ns`；
  - `dcache_bank.sv`（64 KiB Tag+Data）、`ptw_walk_l2tlb.sv`（1024 项 L2 STLB）、`axi_llc_tables.sv` + `axi_llc_bingo_pht.sv`（4 MiB LLC + Bingo PHT）全部显式接入 `ttg_sram_1r1w` / `ttg_sram_1rw`；
  - 同步在 `trace-model/back-end/Rob.cpp` 与 `rtl` `core_top` 门控 `!rob_bcast_interrupt` 防未执行中断头指令污染 BPU 训练。

## 2. 性能结果（2 GHz SPEC06 INT 386/386）

相对 2 GHz 基线（`res_2g_merge_v2_386`，`14.02 分/GHz`）：
- **Geomean IPC：`−0.57%`**（386/386 全通 0 失败，所有点指令数完全一致，换取全核 ~590 KiB BPU + 全缓存严格同步 SRAM 化，真实 2 GHz 约 **`13.94 分/GHz`**）。
- 分程序对比：`483.xalancbmk +0.39%`、`462.libquantum +0.15%`、`471.omnetpp +0.13%`、`429.mcf +0.02%`、`456.hmmer +0.00%`、`473.astar −0.01%`、`401.bzip2 −0.07%`、`403.gcc −0.14%`、`464.h264ref −0.64%`、`445.gobmk −1.18%`、`400.perlbench −1.22%`、`458.sjeng −4.21%`。
- 固定负载：`dhrystone` `86,839 → 88,338` (+1.73%, IPC `2.92`)、`coremark` `208,597 → 206,578` (**−0.97%**, IPC `3.06`)、`memory-stress-small` `312,143 → 312,146` (+0.00%, IPC `3.36`)。

## 3. 验证结果

- **`trace-model`**：`comb_graph.py --check` 0 隐患（25 模块 48 阶段）；`run_gate.sh`（默认 / `PF_ENABLE=0`）均 **62/62 PASS**；`rv64gc` Linux 5.15.170 启动到 `rv64 login:`（0 oops/panic）。
- **`rtl`**：
  - `make cfg` 178 常量（新增 `PC_ALU_NUM=2`）**0 差异**；`lint_chip.sh`（常规与 `-DSRAM_BLACKBOX`）均 **0 警告 / 0 错误**；
  - `fm_gate.sh`（`SOC_FM=1 SOC_SVA=1 SOC_TB_FM_STRICT=1`）：**77/77 PASS、0 FAIL、0 SKIP、0 FM 差、0 周期差**（已将 8 个定向程序并入默认 77 项门禁）；
  - `riscv_tests_gate.sh`（`STRICT=1`）：**152/152 PASS**（1 SKIP `rv64ui-ma_data`）；
  - **`eda` 8 线程静态 `soc_tb` `rv64gc`+`Sv39` Linux 26 窗（`s01..s26`，~1.326 亿指令）**：**26/26 PASS、0 FAIL、0 FM 差、全 bin PT/UP 指纹 100% 逐拍全等**；
  - **严格模式 RV64GC Fuzzer 长跑（`--strict`）**：**55,000 / 55,000 PASS（0 FAIL / 0 ERR）**，累计 **54,956,916 提交指令 / 416,457,603 周期**。

## 4. TSMC 28nm HPC+ DC 综合结果（`ssg0p81v125c`, `0.50 ns / 2.0 GHz`, `SRAM_BLACKBOX`）

| 模块 | WNS / Fmax | 级数 / reg2reg | Area µm²（改前 → 改后） |
|---|---|---|---:|
| **`rob_bb`** | `−0.15 ns (1.54 GHz)` | `42 lvl / −0.15` | `521,086 →` **`121,413` (−76.7%)** |
| **`ftq_ibuf_bb`** | `−0.13 ns (1.59G / reg2reg 1.72G)` | `24 lvl / −0.08` | `1,684,992 →` **`243,191` (−85.6%)** |
| **`isu`** | `−0.23 ns (1.37 GHz 持平)` | `41→28 lvl / −0.23` | `598,408 →` **`467,899` (−21.8%)** |
| **`lsu`** | `−0.39 ns (1.12 GHz 持平)` | `44 lvl / −0.39` | `758,236 → 767,221` |
| **`tlb_mmu_bb`** | `−0.03 ns (1.89 GHz 持平)` | `25 lvl / −0.03` | `57,685 → 57,685 (0.0%)` |
| **`ptw_walk_l2tlb_bb`** | **`0.00 ns (MET ≥2.00G / 2.70G)`** | `19 lvl / 0.00` | **`23,485`**（1024 项 STLB 首次签核） |
| **`icache_bb_v2`** | `−0.95 ns`（`u_fdip` 顶路径） | `86 lvl / −0.94` | **`248,709`**（32 KiB 黑盒化） |
| **`dcache_bb`** | `−0.56 ns`（`u_pf/u_tab`） | `62 lvl / −0.55` | **`866,611`**（64 KiB 黑盒化） |
| **`axi_llc_bb`** | `−0.84 ns`（`victim→bingo`） | `82 lvl / −0.84` | **`644,526`**（4 MiB 黑盒化） |
| **`bpu_spec`** | `−0.34 ns`（reg2reg `1.20 GHz`） | `52→48 lvl / −0.33` | `142,200 → 191,790` |
| **`bpu_bb_p`** | `−1.40 ns`（S2 TAGE→`u_spec`） | `119 lvl / −1.40` | **`941,477`**（`u_ftb0` FF 占 `418.5k` / 44.5%） |

可比三后端核心模块（`rob + ftq_ibuf + isu`）合计净省 **`1.97 mm²`**，详见 [09-synthesis-report.md](../../rtl/docs/09-synthesis-report.md) §20。
