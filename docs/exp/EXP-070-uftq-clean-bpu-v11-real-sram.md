# EXP-070：Unified FTQ-64 + LSU/DTLB 切链 + Clean BPU v11（1RW 真实 TSMC 28nm SRAM）+ 同页双取 + A1/A2/B1 时序收敛

- **日期**：2026-11-27
- **分支**：`trace-model` `exp/uftq-subsys`（`c51f05b`）；`rtl` `rtl/uftq-subsys`（`8030408` → 合并 `5fa54e2` `0dceb0d`）
- **状态**：已合入 `main`（2026-11-27：trace-model `c51f05b`、rtl `0dceb0d`）
- **背景**：EXP-069 完成全核 100% 严格同步 SRAM 化后，子系统级 28nm DC 暴露出三大真实物理瓶颈：① `front_top` 中 `ptab_bypass` 将 BPU S2 预测与预译码校验串联（`1.77 ns`），且原 BPU `u_ftb0`（64×4 FF）占逻辑面积 44.5%、大量浅宽 1R1W 阵列映射真实 TSMC 28nm SRAM 宏后仅 `478 MHz`（`v10.1`）；② `back_top` 存在 EXU/LSU ↔ DTLB 同拍往返链（`1.24 ns / 0.78 GHz`）；③ `SRAM_BLACKBOX` 会掩盖真实 SRAM 宏的 `tCKQ`、setup 与面积开销，此后全面切向 `SYNTH_TSMC28_SRAM` 零黑盒真实 SRAM 综合口径。

## 1. 关键架构与微架构改动

### 1.1 Unified FTQ-64 与删 `ptab_bypass`
- 合并原 `PTAB + FA + FTQ` 为统一 **64 项 Unified FTQ**（`ftq_ibuf` 元数据 `ftq_meta` 严格同步 1R1W SRAM 化并直驱 ICache/FDIP），彻底删除 `ptab_bypass`（解开 `bpu_eval(S2) → predecode_checker` 跨模块组合长链）。
- 同步 `trace-model`（22 模块 / 43 阶段，`comb_graph.py --check` 0 隐患）与 `rtl`（`make cfg` 175 常量 0 差异）。

### 1.2 后端 LSU / DTLB 子系统切链（零周期变化）
- DTLB 回填预计算并存储 `ppn_p1 / ppn_m1`（兼容 Sv39 大页与 bare 模式），消除访存翻译关键路径上的 29-bit 加法器。
- 解耦 `mmu_req_vaddr` 与 `ag_acc/srp_ok`、优化 `sta_info_q` 路径，在不损失任何 IPC 的前提下彻底消除 `back_top` 的 `1.24 ns` EXU/LSU ↔ DTLB 同拍往返链；`tlb_mmu_bb` 维持 `1.89 GHz` 零回退。

### 1.3 Clean BPU v11 + 深宏 1RW SRAM + 同页双取 + A1/A2/B1 切链
- **Clean BPU v11（深宏 1RW SRAM + 零黑盒实宏映射）**：
  - 删除 `bpu_ftb_sc.sv`（StatCorrector）与旧 2-Ahead B 冗余路径，精简为干净的 `uFTB (S0) → FTB1 / TAGE / ITT (S1/S2)` 1RW 8-bank 分体结构（`bpu_sram_1rw_banked.sv`、`bpu_uftb.sv`），预测读与提交训练天然避撞；
  - `ttg_sram_1r1w.sv` / `ttg_sram_1rw.sv` 补齐 `SYNTH_TSMC28_SRAM` 真实 TSMC 28nm HPC+ SRAM 宏（`tem5n28hpcplvta*`）自动拼接映射，彻底摆脱黑盒估算。
- **Same-Page 2-Fetch + `off6==32` `up16`**：在同 4KB 页且单预测流下恢复同拍双块取指与 32B 边界半字上移，挽回精简 2-Ahead 后的前端取指带宽。
- **A1 / A2 / B1 关键路径切链**：
  - 切断 `u_s2_tage → u_atage` 关键路径（A1/A2），将实宏 `bpu` WNS 从 `−0.58 ns`（`813 MHz`）推进至 **`−0.49 ns`（`877 MHz`）**、TNS 降 `−18.8%`、级数由 `58 → 47`；
  - 配合 `front_top` 侧 B1 切链（`front_head_fix` / `front_fetch_buf` / `icache`），将无黑盒实宏 `front_top` WNS 从 `−1.57 ns` 压降至 `−0.87 ns`。

### 1.4 Linux 26 窗对齐检出的 4 项真实缺陷修复
在全量 26 窗 `rv64gc`+`Sv39` Linux 逐拍锁步验证中，精确定位并修复 4 项边角对齐缺陷，最终达成 **26/26 100% PASS**：
1. `tlb_mmu_core.sv:83`：`early_pf_drop` 补齐 `&& translate && !early_refill_ok`，避免 Berti 跨页预取页表遍历成功时误清 `pf_page_v_q`（一次性修复 `s10/11/13/14/17/18/19/20` 8 个窗口）；
2. `front_fetch_buf.sv:100-103`：`want_pair` 与 `want_tail` 补齐 `&& !inst_full`，防止 `inst_fifo` 满时多入队；
3. `lp_l1.sv:350`：`pf_p_en` 口冲突检查由 `srp_cons` 改为 `srp_req`（对齐 `LsuPipeTranslate.cpp:230`）；
4. `bpu_ftb_tab.sv:280` + `trace-model` `BpuFtb.h`/`BPU_pipe.h`：将预译码误分支清除（`clr_en`）在 `trace-model` 中由不可实现的 1 拍魔法 RMW 改为与硬件完全一致的 **2 拍 1RW `u_ftb1` clear 状态机**，并在 RTL `clr_wr_fire` 补 `!new_ftb_wr` 防止 `u_wrb` 写口冲突丢失清除（根治 `s15` `bin=1653` 分歧）。

## 2. 性能结果（2 GHz SPEC06 INT 386/386）

同口径 2 GHz / 32 ns / `DDR4_8Gb_x8_3200.ini` 全量 SPEC06 INT 386/386（`res_v11_2f_opt_386`，0 失败，386 点指令数完全一致）：
- **Geomean**：**`13.28 分/GHz`**（相对 EXP-068 `res_2g_merge_v2_386` `14.02 /GHz` 为 **`−5.25%`**；相对 EXP-069 `13.94 /GHz` 为 **`−4.71%`**）。
- **分基准对比（vs EXP-068 `2g_merge_v2_386`）**：

| Benchmark | Points | Base CPI | EXP-070 CPI | IPC Delta |
|---|---:|---:|---:|---:|
| `400.perlbench` | 24 | 0.263 | 0.290 | −9.17% |
| `401.bzip2` | 48 | 0.370 | 0.383 | −3.29% |
| `403.gcc` | 34 | 0.544 | 0.567 | −4.20% |
| `429.mcf` | 45 | 2.489 | 2.514 | −1.01% |
| `445.gobmk` | 29 | 0.358 | 0.417 | −14.22% |
| `456.hmmer` | 23 | 0.149 | 0.154 | −2.72% |
| `458.sjeng` | 27 | 0.317 | 0.365 | −13.11% |
| `462.libquantum` | 36 | 0.549 | 0.557 | −1.45% |
| `464.h264ref` | 35 | 0.208 | 0.218 | −4.52% |
| `471.omnetpp` | 25 | 1.024 | 1.050 | −2.51% |
| `473.astar` | 26 | 0.752 | 0.781 | −3.65% |
| `483.xalancbmk` | 34 | 0.437 | 0.445 | −1.90% |
| **Geomean** | **386** | — | — | **−5.25% (`13.28 /GHz`)** |

- **PMU TMA 归因（12 基准均值，vs `2g_merge_v2_386`）**：
  - `MISP_ALL_MPKI`：`4.60 → 5.11`（`BR 4.48→4.92`、`JALR 0.09→0.14`、`RET 0.03→0.04`）→ `SLOT_FE_RECOV_MISPRED` `7.32% → 8.75%`（+1.43 pp，主要来自删除 `bpu_ftb_sc` StatCorrector 与 1RW 深宏架构取舍，在分支密集的 `gobmk`/`sjeng`/`perlbench` 最显著）；
  - `SLOT_FE_OTHER`：`20.42% → 22.57%`（+2.15 pp）→ `SLOT_FE_EMPTY` `47.20% → 49.22%`（+2.02 pp，来自取消旧 2-Ahead B 后的单块/覆盖气泡，已被同页双取部分挽回）；
  - `SLOT_BE`：`10.35% → 10.23%`（基本持平）；
  - **有效算力权衡**：以 `−4.71%`（vs EXP-069）的每 GHz IPC 代价换取真实 TSMC 28nm SRAM 下 BPU 频率 **+83%（`478 → 877 MHz`）**、BPU 纯逻辑面积 **−59.1%**，整核绝对性能（`分/GHz × Fmax`）大幅净增。
- **固定负载（vs EXP-069）**：`dhrystone` `88,338 → 93,928`（IPC `2.75`，+6.33%）、`coremark` `206,578 → 267,370`（IPC `2.36`，+29.43%）、`memory-stress-small` `312,146 → 310,550`（IPC `3.38`，**−0.51%**）。

## 3. 验证结果

- **`trace-model`**：`comb_graph.py --check` 0 隐患（22 模块 43 阶段）；`run_gate.sh` **62/62 PASS**、`PF_ENABLE=0` **62/62 PASS**、`run_gate_c.sh` **68/68 PASS**（全部 0 周期差）；`linux_check.sh`（`rv64gc` Linux 5.15.170）启动至 `rv64 login:`（`login=1, oops/panic=0`）；SPEC06 INT **386/386 PASS**（0 失败）。
- **`rtl`**：
  - `make cfg` 175 常量 **0 差异**；`lint_chip.sh` & `lint_soc.sh` **0 警告 / 0 错误**；
  - `fm_gate.sh`（`SOC_FM=1 SOC_SVA=1 SOC_ASSERT=1 SOC_TB_FM_STRICT=1`，合并 `5fa54e2` 后复验）：**77/77 PASS、0 FAIL、0 SKIP、0 FM 差、周期与 `ref_cycles.txt` 0 处不同**；
  - `riscv_tests_gate.sh`（`STRICT=1`）：**152/152 PASS**（1 SKIP `rv64ui-ma_data`）；
  - `scripts/soc_gate.sh --linux`（合并 `5fa54e2` 后全片 SoC `DDR_DATA_W=64/128` + `--assert`）：**12/12 PASS、0 FAIL**；
  - **`eda` 8 线程静态 `core_tb` `rv64gc`+`Sv39` Linux 26 窗（`s01..s26`，~1.326 亿指令）**：**26/26 PASS、0 FAIL、0 FM 差、全部 bin PT/UP 指纹 100% 逐拍全等**。

## 4. TSMC 28nm HPC+ DC 综合结果（零黑盒真实 SRAM + 子系统签核）

| 模块 / 口径 | 时钟约束 | WNS / 估算 Fmax | 逻辑级数 / TNS | Area (µm²) / 宏单元 | 关键路径与结论 |
|---|---:|---|---|---:|---|
| **`bpu`（v11 实宏，A1/A2 前）** | `0.65 ns` | `−0.58 ns` / `813 MHz` | `58 lvl` / `−27,002` | `2,076,194`（`386.0k` 逻辑 + `1,690.2k` **156 真宏**） | 顶路径 `u_s2_tage → u_atage`（`1.11 ns`） |
| **`bpu`（v11 + A1/A2 实宏）** | `0.65 ns` | **`−0.49 ns` / `877 MHz`**（**+83%** vs `v10.1` `478 MHz`） | **`47 lvl` / `−21,929` (−18.8%)** | **`2,075,545`**（`385.4k` 逻辑 **−59.1%** vs EXP-069 + `1,690.2k` **156 真宏**，`50,913` FFs） | 顶路径移至 `u_ftb1` 真宏 → `u_spec/st_q`（`arrival 1.09 ns`） |
| **`front_top`（v11 + A1/A2/B1 实宏）** | `0.65 ns` | 收尾中（已压至 **`−0.87 ns`** vs 改前 `−1.57 ns`） | 持续收敛 | `~4,230,674`（含全部真实 BPU + ICache SRAM 宏） | 彻底取消 `SRAM_BLACKBOX`，待 `eda-06` `qor.rpt` 落地后回填终值 |
| **`back_top_bb`（Unified FTQ + DTLB 切链）** | `0.50 ns` | `−0.70 ns` / `833 MHz`（`arrival 1.16 ns`） | `62 lvl` / `−71,543` | `2,572,725`（`159,559` FFs） | 彻底消除 EXU/LSU ↔ DTLB `1.24 ns` 往返链；新顶路径 `u_lsu/u_ldq → u_isu/g_iq[5]`（下轮 `Issue/RegRead` 拆拍目标） |
| **`ftq_ibuf_bb`（Unified FTQ-64）** | `0.50 ns` | `−0.15 ns` / `1.54 GHz`（reg2reg `1.56 GHz`） | `32 lvl` / `−749` | `239,315`（`23,025` FFs） | 统一 64 项 FTQ + 同步 1R1W `ftq_meta`，面积与 EXP-069 持平 |
| **`tlb_mmu_bb`（`ppn_p1/m1`）** | `0.50 ns` | **`−0.03 ns` / `1.89 GHz`（零回退）** | `23 lvl` / `−110` | `94,793`（`7,490` FFs） | 预存 `ppn±1` 零频率损失，换取 `back_top` 彻底解耦 |

详见 [09-synthesis-report.md](../../rtl/docs/09-synthesis-report.md) §21。
