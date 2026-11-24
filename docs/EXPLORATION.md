# AI-Huma 架构探索记录

每次架构/性能探索写一节，最新的在最上面，不论是否合入、结论正负。规则见 [WORKFLOW.md](WORKFLOW.md) 第 5.1 节。

> **已过时说明（2026-11-12）**：下面是按时间追加的历史记录，各节里的开关、环境变量、分支和工作区名按当时的状态写，不再改写。已经不存在的有：EXP-028 清理删掉的 `BPA_TAGW/CNTW/UW/WEAK/UALT/ALLOC/URST`、`BPA_SC*`、`BPA_NOTC`、`BPA_CMTSYNC/NOCMTSYNC` 和 `SIM_UNCACHE_*`；2026-11-12 清理删掉的 `CONFIG_DIFFTEST` / `PERF_COUNTER` / `BPU` / `TLB_MMU` / `ORACLE_STEADY_FETCH_WIDTH` 宏、DDR 延迟推算链（`CONFIG_DDR_CORE_FREQ_MHZ`、`CL` 等，`CONFIG_SIM_DDR_LATENCY` 固定 60）和 6 个调试环境变量（`CKPT_TRACE_PC`、`TB_DEBUG_DDR/FLUSH/PATCH`、`LSU_PIPE_RPREG`、`FE_IPF_MAX`，后者改为常量）。**当前有哪些环境变量、默认值是什么，以 [trace-model/docs/ENV_VARS.md](../trace-model/docs/ENV_VARS.md) 为准**；rtl `rob_pkg` 的 `XLEN` 已改名 `ROB_XLEN`；多数 `exp/*` 分支已合入 main，是否还存在以各仓库 `git branch` 为准。复现旧实验时，用该实验合入前的提交。

| 编号 | 日期 | 题目 | 分支 | 状态 | 一句话结论 |
|---|---|---|---|---|---|
| [EXP-064](#exp-064-第三轮-tsmc-28nm-dc-时序优化dcache_pf--dcache_mshr--lsu-wave-12--ren-2-stage) | 2026-11-24 | 第三轮 TSMC 28nm HPC+ DC 时序优化（`dcache_pf` / `dcache_mshr` / `lsu` Wave 1+2 零周期变化优化 + `ren` 2-stage 流水化）及 `Fu.h` `div_radix16_latency` `msd::taint` 修复 | trace-model `exp/timing-opt3`；rtl `rtl/timing-opt3` | **已合入 `main`（2026-11-24：trace-model `be7699a`、rtl `7d84c7d`）** | 全核 22/23 模块 ≥1.20 GHz（20/23 ≥1.28 GHz，14/23 ≥1.54 GHz）：`dcache_pf` **1.18→1.35 GHz (+14.4%)**（纯组合 1.43，0 周期变化）、`dcache_mshr` **1.15→1.28 GHz (+11.3%)**（纯组合 1.54，面积 **−13.9%**，0 周期变化）、`lsu` Wave 1+2 **0.88→0.97 GHz (+10.2%)**（TNS −32.6%，面积 −4.9%，0 周期变化）、`ren` 2-stage **1.16→1.22 GHz (+5.2%)**（46→40 级，SPEC06 INT 386/386 **`−1.07%`**）；`fm_gate` **69/69 PASS（0 周期差）**，**rv64gc Linux 26 窗（`s01..s26`，~1.326 亿指令）26/26 PASS、0 FM 差、100% PT/UP 全等**；顺带修复 `Fu.h` `div_radix16_latency` 未读 `msd::live()` 导致投机旧值 `divu` 差 1 拍的遗留 bug；同时实测确认 `ren_elim_sel` 33×33 `spec_ref_cnt` 预计算因高扇出回归（−0.36→−0.42 ns）并已回退 |
| [EXP-063](#exp-063-第二轮-tsmc-28nm-dc-时序优化bpu_eval--bpu_spec--lsu--exu_ctrl) | 2026-11-24 | 第二轮 TSMC 28nm HPC+ DC 时序优化（`bpu_eval` 真并行 2-Ahead B / `bpu_spec` 寄存 `M_ARCH` / `lsu` 无移位 CAM + 并行 `lp_wk` / `exu_ctrl` 修 DC `(VER-37)`）及 `ren` 两级流水 DSE | trace-model `exp/timing-opt2`；rtl `rtl/timing-opt2` | **已合入 `main`（2026-11-24：trace-model `4626924`、rtl `aa7888b`）** | 全核 23/23 模块补齐 28nm DC 真实签核数据（22/23 模块 ≥1.15 GHz，14/23 ≥1.54 GHz，仅剩 `lsu` <1.0 GHz）：`exu_ctrl` **MET ≥2.00 GHz**（WNS `0.00 ns` / 13 lvl / 31.8k um²）、`bpu_eval` **0.84→1.28 GHz (+52.4%)**（纯组合 `0.68 ns / 1.47 GHz`、面积 −6.8%）、`bpu_spec` **0.86→1.20 GHz (+39.5%)**（纯组合 `0.70 ns / 1.43 GHz`、面积 −8.9%）、`lsu` **0.83→0.88 GHz**（0 周期变化，暴露第三轮流水切分目标）；**全量 SPEC06 INT 386/386 仅 `−1.20%`**（vs EXP-062，以 1.2% IPC 换 BPU 频率 +40%~+52%）；`fm_gate` **69/69（0 周期差）**，**rv64gc Linux 26 窗（`s01..s26` + `s00`，~1.377 亿指令）26/26 PASS、0 FM 差、100% PT/UP 全等** |
| [EXP-062](#exp-062-tsmc-28nm-dc-时序基线与第一轮-5-模块时序优化) | 2026-11-24 | 建立 TSMC 28nm HPC+ Synopsys DC 真实工艺库时序基线（22 模块）+ 第一轮 5 模块时序优化（`dcache_pf` 4 级流水 / `axi_llc_bop` / `bpu_spec` / `ren` / `dcache_mshr`） | trace-model `exp/timing-opt1`；rtl `rtl/timing-opt1` | **已合入 `main`（2026-11-24：trace-model `d872061`、rtl `7f31634`）** | 首次建立 TSMC 28nm HPC+（`ssg0p81v125c`, 12T SVT+LVT, `0.50ns / 2.0GHz`, `compile_ultra`）22 模块真实时序基线并确立“DC 28nm 权威签核 + Yosys 快速代理”流程；第一轮攻克 5 大瓶颈：`dcache_pf` **0.37→1.18 GHz (+3.19×)** / 面积 −19.8% / Yosys 384→75、`axi_llc_bop` **1.05→1.47 GHz** / Yosys 291→75、`bpu_spec` **0.73→0.86 GHz**（69→41 lvl）、`ren` **1.05→1.16 GHz**、`dcache_mshr` Yosys **123→99 层 (<100)**；**全量 SPEC06 INT 386/386 反涨 `+0.51%`**（vs EXP-060），**rv64gc Linux 26 窗（`s01..s26` + `s00`，~1.377 亿指令）26/26 PASS、0 FM 差、100% PT/UP 逐拍全等** |
| [EXP-061](#exp-061-乘法器-radix-4-booth--1-radix-16-early-out-变延迟除法--全套自研可综合-rv64fd-fpu) | 2026-11-23 | 乘除法优化（Radix-4 Booth 乘法 + 1× Radix-16 双 Radix-4 Early-out 变延迟除法 + EXU 完成前 1 拍动态唤醒）与全套自研可综合 RV64FD FPU（FMISC / I2F / FCVT / 3 拍流水 FMA / 迭代 FDIV-FSQRT，双路径设计） | trace-model `exp/div16`；rtl `rtl/fpu-synth` | **已合入 `main`（2026-11-23：trace-model `ac0a4bc`、rtl `1df38b0`）** | 4 组 386 点 DSE 确认 1× Radix-16 Early-out 为最佳帕累托点（1×32 拍 `−0.42%`、1×R4+EO `+0.37%`、1×R16+EO `+0.52%`、2×4 拍上限 `+0.58%`）；落地硬件忠实版 EXU 动态唤醒（删 `div_wake_slots` 与 Port 1 `isu_wb_gate` 移位寄存器）后，**全量 SPEC06 INT 386/386（0 失败，vs EXP-060 `15.25 /GHz`）Geomean `+0.53%` → `15.33 分/GHz`**（`hmmer +2.65%`、`sjeng +1.12%`、`gobmk +1.05%`、`h264ref +0.85%`、`gcc +0.68%`），`dhrystone −3.72%`、`prime −55.8%`、`wanshu −56.1%`；Yosys：`mul_unit` `40,041→27,473`（−31.4%）/30 层、`div_unit` `12,340`/50 层、`isu` `−8,412`/60 层、自研 RV64FD FPU 5 核心全部 `<100` 层（`fp_fma_core` 33.8k/98 层、`fp_div_core` 10.9k/73 层）、整块 `exu` `304,977`/98 层；`-DFPU_REAL` 整核 `fm_gate` **69/69（0 周期差）**，3 项专项对拍合计 645 万次 0 不一致，Linux 26 窗 1.326 亿指令 0 FM 不一致（25/26 PT/UP 全等，仅 `s19` 1 处错路微差） |
| [EXP-060](#exp-060-load-l2-推测唤醒-stlf-l2-唤醒--wbp-同拍唤醒与-mdp-store-sets-对比) | 2026-11-23 | Load 唤醒优化（L2 推测唤醒 `4→3` 拍 + STLF `data_v` L2 唤醒 + WBP 同拍唤醒 `5→4` 拍 + `isu` 4 路直接比较 cancel + `prf` 整数 `lsu_byp`），并附 MDP Store Sets / Wait Table / Oracle 48 点对比评估 | trace-model `exp/ld-wake`（MDP：`exp/mdp-eval`）；rtl `rtl/ld-wake` | **已合入 `main`（2026-11-23：trace-model `0e609d7`、rtl `99830ea`）** | 先评估 MDP（48 点）：现有 64-entry/2000-cycle Wait Table 已吃掉访存推测空间 88%，Oracle 上限仅 `+1.60%`，经典 Store Sets（SSIT 1024 + LFST 64）因 PC 级假依赖实测反而 **`−1.33% ~ −3.60%`**，决定不采用。转向 Load 唤醒优化：48 点三项逐级叠加（`wbp +0.37%`、`l2 +2.41%`、`l2+stlf +2.51%`、`all +2.84%`），**全量 SPEC06 INT 386/386（0 失败，vs EXP-059 `14.86 /GHz`）Geomean `+2.64%` → `15.25 分/GHz`（首次突破 15 分，12/12 全正零回退）**；Yosys `lsu` 101 / `dispatch` 57 / `prf` 25（均 0 增长）、`isu` 60 层（4 路直接比较 cancel）；`fm_gate` **69/69（0 周期差）**，Linux 26 窗 `1.326 亿` 指令 0 FM 差且 **26/26 PT/UP 100% 逐拍全等** |
| [EXP-059](#exp-059-ren-稀疏-k4-单写口检查点--本地-25625b-ren_log-前向-walk--8-bank-freelist--窄位宽-rat) | 2026-11-23 | `ren` 稀疏 K=4 单写口检查点 + ROB 字段抽离本地 256×25b `ren_log`（1R1W 8 宽前向 Walk）+ 8-bank `free_list` + 删 8×`snapshot` 窄位宽 `ren_rat` | trace-model `exp/ren-ckpt-walk`；rtl `rtl/ren-ckpt-walk` | **已合入 `main`（2026-11-23：trace-model `f4f2122`、rtl `9a52584`）** | `REN_CKPT_NUM=4 / REN_CKPT_INTERVAL=32`（分支触发，1R1W Walk 暂停提交）在全量 SPEC06 INT 386/386 点（0 失败）相对 EXP-058 `main` 仅 **`−0.18%`** Geomean IPC；RTL 叠加 8-bank 1R1W INT/FP `free_list`、删除 `ren_rat` 8 份全量 `snapshot` 与域内窄位宽（INT 8b / FP 7b）后，Yosys `ren` **586,315 → 156,986 cells（−73.22%）/ 91 层（深度持平）**，`rob` **897,972 → 881,101 cells（−1.88%）/ 65 层**，两模块合计 **−446,200 单元**；`fm_gate` **69/69（0 周期差）**，8 线程 `soc_tb` Linux 26 窗（`s01..s26`）`1.36 亿` 指令 0 FM 差且 **26/26 PT/UP 100% 逐拍全等** |
| [EXP-058](#exp-058-硬件忠实版-llc-bingo-4kb-空间预取器) | 2026-11-23 | 硬件忠实版 LLC Bingo 4KB 空间预取器（FT 32 / AGT 32 / 1RW SRAM `PHT_L 256×4` + `PHT_S 128×4` + 12b `pc_hash` 真实边带 + 无乘法器节流器 + 与 BOP 双优先级协同） | trace-model `exp/bingo`；rtl `rtl/bingo` | **已合入 `main`（2026-11-23：trace-model `aa345c9`、rtl `2fbf053`）** | 在 `axi_llc` 落地硬件忠实版 Bingo 4KB（总存储 `~26.75 KiB`，仅占 4 MiB LLC `0.65%`），与既有 BOP 双优先级协同（`bop_q > bingo_q`，`BOP_INF: 4→8`）；**全量 SPEC06 INT 386/386（0 失败，vs EXP-056 `14.69 /GHz`）Geomean `+1.26%` → `14.88 分/GHz`（11 正 1 平 0 回归：`omnetpp +7.01%`、`mcf +2.59%`、`xalancbmk +1.37%`、`gcc +1.11%`、`sjeng +0.99%`、`astar +0.97%`）**；Yosys `axi_llc_bingo` 经桶形移位优化后为 `41,232` cells / **48 层**；`fm_gate` **69/69（0 周期差）**、Linux 27 窗 `1.377 亿` 指令 0 FM 差且 **27/27 PT/UP 100% 逐拍全等** |
| [EXP-057](#exp-057-cache-层级探索64kb-l1i-与-1mb-l2--16mb-l3-简化模型评估) | 2026-11-22 | Cache 层级探索（基于 EXP-056 `L2TLB+PWC`）：① 64KB L1I (`128×8`) + 64KB L1D (`256×4`)；② 1MB 16-way 私有 L2 + 16MB 16-way Non-inclusive SRRIP L3 (`L3_LAT=20` cyc) 简化模型 | trace-model `exp/l2l3`（worktree `trace-model-l2l3`） | **探索完成（未合入）** | **64KB L1I** 全量 SPEC06 INT 386/386 仅 **`+0.36%`**（`perlbench +2.44%`、`xalancbmk +1.28%`、`omnetpp +0.61%`），性价比有限；**1MB L2 + 16MB L3** 相对 4MB L2 达 **`+4.11%`**（`mcf +37.73%`、`omnetpp +14.53%`、`xalancbmk +7.28%`、`libquantum +3.50%`、`astar +2.24%`；L2 缩容回退 `gcc −4.66%`、`bzip2 −3.45%`），相对 EXP-055 `main` 累计 **`+7.42%`（`~15.30 分/GHz`）** |
| [EXP-056](#exp-056-统一-l2-tlb10244-1rw-sram--8-项大页-cam--16-项-sv39-pwc) | 2026-11-22 | 统一 L2 TLB（1024 项 4 路 1RW SRAM，3-bit tree-PLRU）+ 8 项大页 CAM + 16 项 Sv39 PWC 落地 `ptw_walk`，及 `TraceBridge` 已提交页表读修复 | trace-model `exp/l2tlb`；rtl `rtl/l2tlb` | **已合入 `main`（2026-11-22：trace-model `c174d8d`、rtl `c630c5d`）** | 零 L1 关键路径改动，仅在 `ptw_walk` 增加 4 独立 1D 256×76b 1RW SRAM bank + 8 项 RR 大页 CAM + 16 项 RR Sv39 PWC（20-bit root 匹配）；**全量 SPEC06 INT 386/386（0 失败）vs EXP-055 `main` 12/12 全正、Geomean `+3.17%`（`14.24 → 14.69 分/GHz`）**（`mcf +14.61%`、`xalancbmk +9.74%`、`omnetpp +4.38%`、`astar +3.34%`、`perlbench +2.22%`、`bzip2 +2.21%`）；Yosys `ptw_walk` 仅 `5,446` cells（21 `$mem_v2`）/ **44 层**（较改前 47 层反降 3 层）；`fm_gate` **69/69（0 周期差）**、Linux 27 窗 0 FM 差且 27/27 UP / 26/27 PT 全等 |
| [EXP-055](#exp-055-后端指令窗口扩展-prf256--rob256-与-ren-公共原语降深度) | 2026-11-22 | 后端窗口 DSE（PRF/ROB/MAX_BR/IQ/STQ/MSHR）落地 `PRF=256 / ROB=256`（`MAX_BR=32`）+ `ren` 公共原语降深度（`100→91` 层） | trace-model `exp/win256`；rtl `rtl/win256` | **已合入 `main`（2026-11-22：trace-model `16548ba`、rtl `f1fed8a`）** | 基于 386 点 TMA（`NOPREG 14.9%`、`ROB_FULL 11.6%`）做两轮 48 点 DSE：确认现有 IQ/LDQ/STQ/MSHR/`MAX_BR=32` 均已超配，仅改 `PRF=256 / ROB=256`（天然 2 次幂零回绕逻辑）即可吃掉 `256/256/64` 99%+ 收益；**全量 SPEC06 INT 386/386（0 失败）vs EXP-053 `main` `+5.64%`（`13.48 → 14.24 分/GHz`）**，`BE 33.8% → 26.5%`、`MLP 3.54 → 4.63`；RTL `ren` 经 `ren_dep_check` 两级旁路 + `ren_elim_sel` 3 级指针跳跃 + `ren_rat` 去 `fire` 压至 **91 层**（低于原 128/128 的 97 层），`prf` 25 层、`rob` 64 层、`isu` 50 层；`fm_gate` 68/68（0 周期差）、Linux 27 窗 1.377 亿指令 0 FM 差且 27/27 PT/UP 全等 |
| [EXP-054](#exp-054-l1-解耦-breadcrumbs-与-berti-融合及-llc-sms-空间预取体系评估) | 2026-11-22 | L1 解耦 Breadcrumbs（移植自 `gem5x86/gem5rv` 简化版 + 自适应 distance）与硬件 Berti 融合、以及 LLC SMS（trigger-only + 12b PC hash + 密集流过滤 + 准确率节流器）与 BOP 协同评估 | trace-model `exp/pf-bc-sms`（worktree `trace-model-pf-bc-sms`，基于 `1939bd1`，未提交） | **探索完成（待决策，未合入）** | **LLC BOP + trigger-only 稀疏过滤/节流 SMS 为绝对帕累托冠军**：零改动前端/重命名/L1D，仅在 LLC 增加硬件 SMS（FT 32 / AGT 32 / PHT 1024 / 2KB region）与 L1D→LLC 12-bit PC hash 透传，全量 SPEC06 INT **386/386 点（0 失败）Geomean `+1.03% ~ +1.04%`**（`SMS_T1_THR`：**`omnetpp +5.88%`、`mcf +2.10%`、`xalancbmk +1.49%`、`gcc +1.20%`、`perlbench +0.87%`、`astar +0.47%`、`libquantum −0.01%`**，全量 386 点最差点仅 **−2.7%**；无节流版 `mcf` 达 **`+3.85%`**）。L1 解耦 BC 叠加 Berti 全量 386 点仅 **`+0.09%`**（与 SMS 叠加 `COMBO +1.07%`，仅多 +0.03 pp），在已有强硬件 Berti + LLC SMS 之上性价比偏低；`rv64gc` Linux 在 `COMBO` 全开下成功启动到 `rv64 login:`（0 oops/panic）；默认关 `run_gate_c.sh` 68/68 逐拍一致 |
| [EXP-053](#exp-053-前端结构清理与去补丁重构--复用-ttg_pick_k-与双路径加速) | 2026-11-22 | 前端两阶段清理重构（Phase 1：真 4-Bank `icache_arr` / 并行 BPU & `front_head_fix` / 删死 `tage_idx/tag`；Phase 2：删 `fdip_snoop` 改 1 拍探针 / AXI `CLEAR_ON_POP` 消回波 / 显式 1b `pf_inst_hi`）+ 复用 `ttg_pick_k` 与 `` `ifdef SYNTHESIS `` 双路径 + 修复既有 `LSU_MS_DATA` STLF `cam_ok` | trace-model `exp/fe-cleanup`；rtl `rtl/fe-cleanup` | **已合入 `main`（2026-11-22：trace-model `4d4534f`、rtl `28840c8`）** | 零新功能膨胀、彻底清除跨子系统 `fdip_snoop` / `resp_popped_q` / `inst->diag_val[1]` 三处补丁与死线；Yosys 同口径 `front_top` **1,582,763/356 → 1,159,189 (−26.8%) / 216 层 (−39.3%)**、`bpu` **504k/272 → 410k (−18.6%) / 197 层 (−27.6%)**、`icache` **917k/106 → 389k (−57.5%) / 114 层**、`pre_idu_queue` **138k → 131k (−4.5%) / 38 层**；合并后最新 `main`（`4d4534f`+`28840c8`）全量 SPEC06 INT 386/386 **`13.48 分/GHz`**（vs EXP-052 `−0.05%`、vs EXP-051 `+0.50%`）、`lint_chip` 0、`fe_clean_eq_tb` 双路径（仿真 3.6× 提速）0 错、`fm_gate` **68/68 0 周期偏差**、rv64gc Linux 27 窗 **137,700,065 指令 0 FM 差异且 27/27 PT/UP 150,175 bins 全等** |
| [EXP-052](#exp-052-rv64gc-cmv-规范化与组内-1-hop-关键链移动消除--ren-降深度) | 2026-11-21 | RV64GC `c.mv`（`add rd, x0, rs2`）规范化 + 组内 1-hop 关键链移动消除（`ren_elim_sel` 并行根分解 + `head_after`/`head_next` 移出握手关键路径） | trace-model `exp/move-elim-eval`；rtl `rtl/move-elim-1hop` | **已合入 `main`（2026-11-22：trace-model `1939bd1`、rtl `9798eb7`）** | 修复此前 `is_move_shape` 漏掉全部 16-bit `c.mv`（`MOVE_ELIMINATED = 0%`）的缺陷，并增加组内 1-hop 生产链消除；全量 SPEC06 INT **386/386 点（0 失败）Geomean `+0.55%`**（12 程序全正零回退：`xalancbmk +1.62%`、`omnetpp +1.22%`、`sjeng +0.79%`、`h264ref +0.74%`、`gobmk +0.68%`、`mcf +0.43%`、`bzip2 +0.39%`、`astar +0.31%`、`gcc +0.30%`），`coremark +0.99%`；RTL `ren` 深度不升反降 **99 → 97 层**（`475,533` cells，+0.18%）、`idu` 66 层；`tests/ren_elim_sel/run.sh` 100k 随机 0 不一致、`lint_chip` 0、`fm_gate` **68/68（0 周期偏差）**、Linux 27 窗 1.377 亿指令 0 FM 不一致（26/27 PT/UP 全等） |
| [EXP-051](#exp-051-前端-2-fetch--2-taken--真-axi-fdip里程碑-b-模型探索) | 2026-11-21 | 前端 `2-fetch` / `2-taken`（零 S0 串行 SRAM 的 2-Ahead B + 无截断 `NT=1` + 4-Bank 1R1W ICache + 2 读口 ITLB）+ 真 AXI/LLC/DRAM S2 确认 2-slot FDIP + `HistRing 1024b` + 内部 `rec_q[256]` + `BRQ_W=1` | trace-model `exp/fe-2fetch-2taken` → `merge/fe-2fetch-2taken`；rtl `rtl/fe-2fetch-2taken` | **已合入 `main`（2026-11-21：trace-model `5b67500`、rtl `3fa98cd`）** | 全量 SPEC06 INT **386/386 点（0 失败）**：探索版帕累托冠军 `fe2f_b4_it2_ah1k` 达 **+2.30%（`13.44 分/GHz`）**，合入 RTL 对齐版（1-pop/cycle FDIP + `BRQ_W=1` + L1D/WB 脏行嗅探）达 **+2.18%（`13.42 分/GHz`，较 EXP-050 前累计 +10.76%）**，`FE.bw 22.77% → 18.60%`、`coremark −15.77%`；RTL `fm_gate` **68/68 0 周期偏差**，rv64gc Linux **26/26 段（1.326 亿指令）+ `s00` 0 FM/PT/UP 差异**，顺手修复跨 4KB 页 RVC 32 位指令第二半字取指缺页 `stval = pc + 2` 缺陷 |
| [EXP-050](#exp-050-块级-ftb--1-ahead2-ahead-bpu里程碑-a-模型探索) | 2026-11-21 | 块级 FTB（S0 uFTB + S1/S2 Block-FTB/Block-TAGE/单块 Block-ITT）+ 硬件忠实 1-ahead / 2-ahead 流水（`ah1_4k_a2k1k` + `FTB_BRQ=2`，零 `of2` 组合环） | trace-model `exp/ftb-bpu`（归档 `375b080`）→ `merge/ftb-bpu`；rtl `rtl/ftb-bpu` | **已合入 main（2026-11-21：trace-model `ef61350`、rtl `a4dcfb9`）** | 全量 SPEC06 INT（386 点，12 程序全正零回退）：1-ahead（`ah1_4k_a2k1k`，零组合环）达 **+8.48%（`12.11 → 13.14 分/GHz`）**、`FE.bw 31.23% → 22.85%`；RTL 删 22 个旧 16-bank 文件零外部端口改动，Yosys `bpu` **549,458 → 274,811 单元（−50.0%）**、深度 134→131 层；`fm_gate` **67/67 0 周期偏差**，rv64gc Linux **26/26 段（1.325 亿指令）0 FM 不一致、PT/UP 指纹 0 差异** |
| [EXP-048](#exp-048-l1-硬件-berti--llc-bop--mshr-1616-预取体系与-rtl-全程对齐) | 2026-11-20 | L1 硬件 Berti（`PF_KIND=4` + DTLB 跨页翻译）+ LLC Best-Offset（`LLC_BOP=1`）+ L1D/LLC MSHR 16/16，三阶段（M1/M2/M3）写入 RTL 并完成全量 rv64gc Linux 对齐 | trace-model `exp/dse-fork`、rtl `exp/pf-berti-bop` | **已合入 main（2026-11-20：trace-model `6df4312`、rtl `6e2d188`）** | 全量 SPEC06 INT 386 点几何平均 **+6.58%**（libquantum +37.14%、mcf +28.14%、gcc +7.90%、astar +3.35%，零回退）；trace-model 单次从 0 启动 Linux 到 `rv64 login:` PASS；27 窗（0→130M）RTL 对齐修掉 3 类根因（`VQD=32`、非法 `OP-32` 译码、跨 dword 非对齐 load 污点） |
| [EXP-045](#exp-045-cache-替换策略llc-与-l1i-改为-srrip) | 2026-11-19 | cache 替换策略：LLC（rr / PLRU / LRU / SRRIP / BRRIP / DRRIP）、L1I（rr / PLRU / SRRIP）、TLB（rr / NRU / PLRU）在周期模型里实现并比较；LLC 和 L1I 的 SRRIP 写进 RTL | trace-model `exp/llc-plru`（`429172d`，工作区 `trace-model-llcplru`）、rtl `exp/llc-plru`（`aac554a`） | **已合入 main（2026-11-19，与 EXP-046 一起：trace-model `8fd0ae3`、rtl `b9fd0df`，未推送）** | 29 个 SPEC06 rv64gc 高权重点：LLC SRRIP +1.23%（omnetpp +9.0%）、再加 L1I SRRIP 合计 **+1.63%**；TLB ≤ +0.12%、不采用；RTL fm_gate 67/67、周期与模型逐个相等；深度 axi_llc 238 不变、icache 69 → 70 |
| [EXP-046](#exp-046-写口发射时调度选择前查完成周期浮点写通道压缩) | 2026-11-19 | 写口：完成周期的检查移到选择之前（`CFG_WB_PRESEL`），完成周期忙表改成移位寄存器，浮点寄存器堆写通道按发射时的写口预约压缩 | trace-model `exp/wb-port`（`ff96476`、`60aa7e8`），rtl `exp/wb-presel`（`d093291`、`7957ec9`、`f2674cf`） | **已合入 main（2026-11-19，集成分支 trace-model `exp/wb-llc` `8fd0ae3`、rtl `exp/wb-llc-rtl` `b9fd0df`，未推送）** | 模型：67 个 RVC 程序周期 −0.49%，SPEC06 386 点 IPC +0.01%；RTL：isu 单元 −0.9%、深度 88→89，prf 单元 −37%、深度 36→27（单模块口径），整数写口 21→13、浮点 21→6；门禁 67/67、周期与模型相等 |
| [EXP-044](#exp-044-rtl-降深度那一轮和-linux-窗口对齐) | 2026-11-19 | RTL 降深度那一轮：两个 INT 队列、合并访存队列、FLUSH_REG、前端 / BPU / LSU 的低深度改写，模型默认值 = RTL 配置，Linux 12 个窗口对齐 | rtl `exp/agu-share`、trace-model `exp/tlb-ports` | 已合入 main | 67 个程序周期 +1.92%、SPEC06 386 点 IPC −2.15%（hmmer −8.6%），12 个 Linux 窗口全部 PASS；整机深度没有最新数 |
| [EXP-043](#exp-043-l1-berti--store-预取l2-streambreadcrumbs-l1-部分) | 2026-11-17 | 预取组合：L1 Berti、STA 时的 store 预取、LLC 里的 stream、Breadcrumbs（EXP-022 最终设计）的 L1 部分，rv64gc SPEC06 访存组 59 点 | trace-model `exp/pf-l1l2`（`9275c6c`、`215e466`、`39dfc71`，工作区 `trace-model-pfl1l2`） | 未合入 | 第一阶段（1 GHz）：h1 + Berti 最好（+1.9%）；store 预取 ≈ 0；BC L1 + h1 +0.9%。**第二阶段（2026-11-18，3 GHz、MSHR 16、LLC PLRU，只开 L1、相对不预取）：BC_UNIFY（标签步长 + 采样步长按 PC 协同，共用及时距离）+ 按行封顶 + 有用性反馈 +33.1%**，h1 +18.9%，Berti（64 路）+22.5%，原版 Berti +6.3%（`023668e`）。**第三阶段：只留核心规则的 BC_CORE（有用性置信度 + 前沿 + MSHR 反压）+29.8%**（`fc05c5d`），差距在 mcf；探索暂停 |
| [EXP-042](#exp-042-rtl-时序tlb-口并行化first_set-对数深度) | 2026-11-17 | RTL 时序：DTLB/ITLB 的 8 口串行链改为并行，`ttg_first_set` 改为对数深度 | rtl `exp/tlb-par`（`1d8688e`、`261bd67`，基于 main `8abb7ab`） | **已合入 main（2026-11-17，rtl `261bd67`，未推送）** | `tlb_mmu` 深度代理 163 → 67（rv64），行为逐拍不变；fm_gate 67/67、Linux 窗口 3/3 与 main 逐字节相同 |
| [EXP-040](#exp-040-rv64gc-linux-的-rtl-与-trace-model-逐周期对齐) | 2026-11-15 | rv64gc Linux：RTL 与 trace-model 逐周期对齐（旧值路径扩到 rv64、32→64 位错误、页错误 load 的写回、窗口并行检查） | trace-model `exp/rvc-carry`、rtl `exp/rvc-rtl`、function-model `exp/fm-forced-pf` | **待合入**（完整 Linux gate 结果待补） | 18 个 Linux 检查点窗口 PT / UP 指纹全部相同；唯一的 RTL 行为改动是页错误 load 不写 rd |
| [EXP-038](#exp-038-c-扩展trace-model-前端按半字取指) | 2026-11-13 | C 扩展：trace-model（前端半字取指、BPU / FTQ 半字位置、按指令的取指缓冲），参考香山和 BOOM | trace-model `exp/rvc`（工作区 `trace-model-rvc`） | **进行中**：S0–S2 和变慢程序的修复已合入 trace-model `main`（`74e6827`，2026-11-13，已推送）；S3–S5 未做 | S0–S2 完成，`RVC=0` 周期不变；`RVC=1` 的前端能运行带 C 和不带 C 的程序，与 function-model 逐条对拍 0 不一致；S3–S5 未开始 |
| [EXP-037](#exp-037-c-扩展压缩指令function-model-第一步) | 2026-11-13 | C 扩展（压缩指令）：function-model 第一步，之后 trace-model（前端按半字）、RTL | function-model `exp/rvc`、`exp/rvc-fast` | **function-model 完成（含快速路径），已合入 main（2026-11-13，已推送）**；trace-model / RTL 未开始 | `RVC=1` 开关（rv32 / rv64，默认关）；16 位编码逐个与 Spike 一致，带 C 的 Linux（内核 + OpenSBI）从复位到 `rv64 login:` 前 2.5 亿条指令与 Spike 逐条一致 |
| [EXP-036](#exp-036-trace-model-仿真速度去掉每周期的状态拷贝) | 2026-11-13 | trace-model 仿真速度：去掉每周期的状态拷贝（BPU、LSU、Bridge、IQ） | trace-model `exp/fcsr`（`067f02e`…`195dad4`） | **已合入 main（2026-11-13，已推送）** | 周期逐个不变（gate 64/64），耗时累计下降约 24%（各步提交里的计时） |
| [EXP-035](#exp-035-写回口按完成周期在发射时预约) | 2026-11-12 | 每个写回口每周期只能完成一条：发射时按完成周期预约，撞车的留在 IQ | trace-model `exp/fcsr`（`4a1d9df`）、rtl `exp/fd-rtl`（`f61e821`、`b976975`） | **已合入 main（2026-11-13，已推送）** | 撞车从 coremark 12247 次降到 0；coremark −0.80%、dhrystone −0.32% 周期；RTL 与模型逐周期相同 |
| [EXP-034](#exp-034-exu-改成按单元的状态去掉-execution-driven-遗留结构) | 2026-11-12 | Exu 改成按单元的状态（去掉 Fu 对象和输入输出拷贝） | trace-model `exp/fcsr`（`a50b64b`） | **已合入 main（2026-11-13，已推送）** | 与冻结的旧 Exu 逐周期同步比较 0 不同（gate 64/64、fp_check 32/64 为基线内），约快 6% |
| [EXP-033](#exp-032--exp-033-fp-写口与-fcsr-串行化) | 2026-11-12 | fflags/frm/fcsr 是真正的串行 CSR 指令；ROB 从写回取 illegal_inst；I2F 优先于 ALU | trace-model `exp/fcsr`、rtl `exp/fd-rtl` | **已合入 main（2026-11-13，已推送）** | rv32-fp-trap 87154 → 95438 周期；RTL 与模型一致 |
| [EXP-032](#exp-032--exp-033-fp-写口与-fcsr-串行化) | 2026-11-12 | FP 寄存器堆写口限制（`FP_WB_PORTS`，默认 2） | trace-model `exp/fcsr`（`c72e9ec`、`59e197c`） | **已合入 main（2026-11-13，已推送）** | fp_check 24/24，微基准延迟不变 |
| [EXP-031](#exp-031-删除-zfinx全面改用标准-fd含-rv32) | 2026-11-12 | 删除 Zfinx，rv32 也改用标准 F/D（三个仓库） | function-model `exp/fd-all`、trace-model `exp/fd-all`、rtl `exp/no-zfinx` | **已合入 main（2026-11-13，已推送）**，实际合入的是随后的链 `exp/fd-all`→`exp/fp-wb`→`exp/fcsr`（trace-model）和 `exp/fd-rtl`（rtl，含标准 F/D 的 RTL） | F/D 成为默认配置（`FP=1`，rv32 和 rv64），Zfinx 全部删除；rv32 gate 周期不变（64/64，基线只换了 Zfinx 测试），RTL 删掉 Zfinx 的 FPU 后 soc_smoke 56/56 |
| [EXP-030](#exp-030-rv64-的-fd-浮点扩展) | 2026-11-12 | rv64 的 F/D 浮点扩展（function-model 第一步，之后 trace-model、RTL） | function-model `exp/fd` | **function-model（`cdcb74d`）和 trace-model（`2c1d166`）已合入各自的 `main`（2026-11-12，未推送）**；RTL 未开始 | `FP=1` 编译开关；directed 测试 + 编译器生成的浮点代码与 Spike 逐条一致；检查点版本 5；`FP=0` 的构建不变 |
| [EXP-029](#exp-029-从-rv32imab-迁移到-rv64imab) | 2026-11-11 | 从 rv32imab 迁移到 rv64imab（function-model → trace-model → RTL，Linux 启动到登录） | function-model `exp/rv64`、trace-model `exp/rv64-on-main`、rtl `exp/rv64` | **已合入 main（2026-11-12，已推送）**：function-model `b388f39`、trace-model `ccc2d0c`、rtl `8dbb7cd` | rv64 在三个层次都跑通：53 个 cpu-tests、Sv39 测试、Linux 从复位到 `rv64 login:`（RTL 约 1.05 亿周期，逐条对比 0 个不一致）；XLEN=32 完全不变 |
| [EXP-028](#exp-028-rob-压缩加大-rob--prf重命名整组等待) | 2026-11-11 | ROB 压缩 / 加大 ROB、PRF / 重命名整组等待（`REN_AON`），删窗口后在当前 main 上重测（接手 2026-11-10 的未完成实验） | trace-model `merge/rob-compact`（`35b3af4`、`a11b1ca`）、rtl `exp/rob-compact`（`4e954d7`、`a905acd`）；统计 / `REN_AON` 留在 trace-model `exp/rob-compress` | 已合入 main（2026-11-11，默认开） | 30 点（按权重选）：整组等待 +0.59%（hmmer +7.5%），ROB192 不改重命名 −0.29%（hmmer −20.9%），ROB192 + 整组等待 +2.27%，ROB192 + PRF192 +3.06%，PRF160 +0.93%；ROB 行平均填 5.58/8，简单指令压缩比约 1.0–1.5；简单指令压缩不做；**紧凑 ROB（按序分配、前缀提交）+ BPU 训练额度 +2.89%（寄存器版本）**（ROB 仍 128 项，好于 ROB192 + 整组等待）；RTL 已做（fm_gate 69/69 周期与模型逐个相等，Linux 从复位连续启动到登录 0 不一致），`rob` 面积 +11.4%、深度 46 → 53；**SPEC 全量 580 点 +2.74%，分数 11.23 → 11.53 分/GHz**，12 个程序全部提升；已知回退：分支密集的短循环被 BPU 更新带宽卡住（gcc 4 个点 −37%、dhrystone +1.8% 周期） |
| [EXP-027](#exp-027-最新-tma-分析与-0x87f00000-非缓存窗口删除) | 2026-11-11 | 最新 TMA 分析（12 程序最高权重点，main 配置）；查出 0x87f00000 非缓存窗口让 SPEC 普通数据走 MMIO；删除该窗口；PMU 缺失标记 64 位 bug | trace-model `exp/no-uncwin`（`62e4a8b`、`07d567c`）、rtl `exp/no-uncwin`（`1205bff`、`de8d0aa`） | 已合入 main（2026-11-11）；RTL Linux 13 段 13/13 | 删窗口后 SPEC 全量 580 点 12 程序几何平均 IPC **+10.75%**，直接换算分数 10.06 → 11.14 分/GHz（当前 main 10.13，删窗口后估 11.22；以前连乘的 10.53 偏高）（h264ref +137%、hmmer +35%、perlbench +6.3%，其余 ±0.3%）；0 个点变慢；不是微结构收益，是测量假象被去掉 |
| [EXP-026](#exp-026-sdipbreadcrumbs-数据流预取器挂在重命名阶段) | 2026-11-10 | sdip（Breadcrumbs）预取器：重命名阶段寄存器标签给 load 步长/类别，64 项 PC 步长表，填回触发的间接预取；对 h1 的替换与叠加 | trace-model `exp/sdip`（`ffdae56`、`e81aef2`，工作区 `trace-model-sdip`），未合入 | 模型完成；SPEC 全量 580 点（快速预热，服务器）`PF_SDIP=2`（sdip 在前、h1 在后）12 程序几何平均 IPC **+1.74%**（点几何平均 +2.41%），`PF_SDIP=1`（sdip 替换 h1）+0.10%（libquantum −11.9%）；RTL 未做 |
| [EXP-025](#exp-025-前端带宽拆分icache-容量与替换间接跳转预测多表-itt) | 2026-11-10 | 前端 PMU 拆分（取指组形状 vs 空拍）、I$ 容量/替换/victim/预取、perlbench 假退化、多表 ITT | trace-model `exp/itt-multi`（`5d8cf66`）、rtl `exp/itt-multi`（`efaa350`）；PMU/I$ 诊断在 `trace-model-fepmu`（`exp/fe-pmu`，未提交） | ITT 部分已合入 main（2026-11-10，MAIN_RECORDS 同日行；`BPO_LOOP`、I$ 部分未合入） | 多表 ITT（3 张 × 64 项，存储比原来少）SPEC 全量 580 点 12 程序几何平均 IPC **+0.67%**（sjeng +3.8%、perlbench +3.2%、h264ref +0.5%）；RTL fm_gate 69/69、周期与模型逐个相等 |
| [EXP-024](#exp-024-已提交-store-的-write-bufferstq-内分组) | 2026-11-09 | 已提交 store 的 write buffer：4 个条目、每条目最多 2 个同 line 的 store，STQ 内分组；香山 SBuffer 和 BOOM 的对照 | trace-model/rtl `exp/store-wb`（`55c9f64` / `ef6da65`） | 已合入 main（2026-11-09，已推送） | SPEC 全量 580 点 12 个程序几何平均 IPC +0.68%（gcc +4.8%、hmmer +1.5%、gobmk +1.1%，其余基本不变）；`fm_gate` 68/68、周期与模型逐个相等、Linux 13/13；`lsu` 深度 125（main 130），`lp_drain` 模块级 +17% |
| EXP-023 | 2026-11-09 | 前端快速通路：`FE_RFAST`（重定向路径）、`FE_BFAST`（覆盖后同拍发射）、`FE_PAIR`（一拍两块）、`FE_IPF`（I$ 预取）；提交说明里写作 EXP-019 / "fe:" | trace-model `exp/frontend`→`exp/combo`→`exp/fe-refs`（`b02eaf6`）、rtl `exp/fe-rtl`（`71468eb`）；工作区 `trace-model-fe`、`trace-model-ferefs`、`rtl-fe` | `FE_RFAST=15`（RTL 固定）、`FE_BFAST`（默认关）随 `exp/integ` 已合入 main；`FE_PAIR`/`FE_IPF` 只在模型里（默认关） | 25 点精确预热：RFAST=15 +2.61%（`bpu` 深度 151 → 141、面积 +19%）；BFAST +34% 深度换 +1.2~1.8%，所以关；FE_PAIR +2.9%、FE_IPF +1.75%（模型，IPF 不经过真实 LLC/AXI） |
| EXP-020 | 2026-11-08 | 访存推测的值路径 `LSU_MS_DATA`：旧值、污染传播、RTL 独有的预测错误 | trace-model `exp/ms-data`（`97cca34`，工作区 `trace-model-msdata`） | 已合入 main（2026-11-09，随 `exp/integ`，默认开） | dhrystone 115,896、vm_pagefault_test 19,271 = RTL；68/68 程序模型 = RTL；30 点收益 +5.30% → +5.21% |
| EXP-019 | 2026-11-09 | LSU 访存相关推测：load 越过地址未知的更老 store，等待表预测，违例重做；模型探索 + RTL 实现；最早的提交说明写作 EXP-018 | trace-model `exp/mem-spec`→`exp/memspec-refs`（`ef02c4c`）、rtl `exp/memspec-rtl`（`598f4f9`）；工作区 `trace-model-msrefs3`、`rtl-memspec` | 已合入 main（2026-11-09，随 `exp/integ`，`LSU_MEMSPEC` 默认开） | 30 点精确预热 +5.35%；等待表优于 store set 和置信计数器；违例代价 28–52 周期；`lsu` 单元 −7.7%、深度 131 → 128 |
| [EXP-017](#exp-017-issue-queue-入队宽度限制) | 2026-11-08 | 每个 IQ 的入队（dispatch 写口）宽度从 8 限到发射口数附近，省写口 | trace-model `exp/iq-enq`（`cefaee4`）、rtl `exp/iq-enq`（`121324c`，工作区 `trace-model-iqenq`、`rtl-iqenq`） | 已合入 main | INT7/LD6/STA4/STD4/BR5（写口 40→26）：全量 580 点快速预热几何平均 IPC −0.05%；先试的 6/4/3/3/3 为 −1.12%（mcf −3.2%、omnetpp −4.3%） |
| [EXP-016](#exp-016后端资源-dse-prf--rob--ldq--stq--在飞分支--iq--mshr结合-pmu) | 2026-11-08 | 后端资源 DSE（PRF / ROB / LDQ / STQ / 在飞分支 / IQ / MSHR），结合 PMU | trace-model `exp/backend-dse`（`1e43fdf`、`7f8456e`）、rtl `edf9d3b` | 只合入支持代码（`CFG_LDQ_SIZE`、两个 PMU 事件），默认配置没变 | 36 点扫描各资源的收益，结论见本节 |
| EXP-015 | 2026-11-08 | 分级 LSU（含 IPC 修复）+ 流水化 S+R BPU 合并 | trace-model/rtl `lsu-bpu`（旧版 `lsu-bpu-v1`） | 已合入 main | 30 点精确预热 IPC +2.87%；全量 580 点快速预热 −1.20%（bzip2 −10.2%），已知回退，见 MAIN_RECORDS |
| [EXP-014](#exp-014-cache-替换策略与组织形式离线回放--周期模型标定) | 2026-11-07 | cache 替换策略与组织形式的收益空间：用功能模型（FastWarm）录 L1I/L1D/LLC/TLB 访问序列，离线回放各种策略与容量/路数，再用周期模型标定 IPC | trace-model `exp/repl-oracle`（工作区 `trace-model-repl`） | 未提交、不合入（只测空间，没有实现策略） | 替换策略的空间很小：LLC DRRIP 缺失 −3.9%、L1D 现策略已接近最优、L1I SRRIP 缺失 −17% 但标定后全集只有 +0.3% IPC；容量翻倍（L1D 128KB / L1I 64KB / LLC 8MB）各约 +1.1~1.3%（单点、噪声 ±3%）；TLB 离线缺失 −73% 但周期模型只 +2.2% |
| [EXP-013](#exp-013-pmu硬件计数器--trace-model-分析层) | 2026-11-07 | PMU：硬件计数器块（事件总线 + HPM CSR）与 trace-model 分析层（TMA、逐 PC 堵塞画像、直方图、相位）共用一张事件表 | trace-model `exp/pmu`（工作区 `trace-model-pmu`）、rtl `exp/pmu`（工作区 `rtl-pmu`） | 已合入 main（2026-11-07） | trace-model 完整；RTL 只做简单的一档（提交流、重定向、TMA 一级的槽事件）+ 计数器块（未接 CSR） | 52 个事件、槽位恒等式逐拍成立；开关与否周期不变（dhrystone、coremark、mcf 检查点）；mcf 点 Backend Bound 81%（L1D 缺失 53%），两条 load 占堵塞的 61% |
| [EXP-012](#exp-012-mov-消除move-elimination) | 2026-11-06 | `addi rd, rs, 0` 在重命名时共用源物理寄存器（mov 消除），架构引用计数，3 位计数器 + 引用上限 | trace-model `exp/move-elim-v2`、rtl `exp/move-elim` | 已合入 main（默认开启） | quick SPEC 几何平均 IPC 1.550 → 1.551（+0.06%），coremark −1.15% 周期；`ren` +21.5k 单元（+10%）；收益在噪声量级 |
| [EXP-009](#exp-009-l1d-数据预取器与指令侧预取) | 2026-11-06 | 电路风格的 L1D 数据预取器（步长 + LLC 次级 next-line + 准确度限流）；指令侧 next-line / FDIP | trace-model `exp/prefetch-h1`、rtl `exp/l1d-prefetch` | 已合入 main（2026-11-07） | 20 个访存瓶颈点（14 训练 + 6 留出）几何平均 IPC：训练 +37.9%、留出 +30.4%；计算密集守卫集 +0.5%；指令侧最多 +0.4%，不采用 |
| [EXP-010](#exp-010-bpu-预测延迟现有模型每个-taken-分支-0-气泡换成真实延迟后-ipc-掉多少) | 2026-11-06 | BPU 预测延迟：现有模型每个 taken 分支 0 气泡，换成真实延迟后 IPC 掉多少 | trace-model `exp/realistic-timing`（工作区 `trace-model-timing`，未提交） | 未合入（只测空间） | 2 周期预测器约 −7%，3 周期约 −13%；64 项 1 周期 uBTB 拿回约三分之二 |
| [EXP-008](#exp-008-decode-宽度-8-降到-6) | 2026-11-05 | decode/rename 宽度 8→6（含 commit 宽度拆分）；前端取指仍为 8 | trace-model `exp/decode6` | 未提交、不合入；保持 8 | quick SPEC 几何平均 IPC −3.1%（hmmer −12%，其余 5 个 −1.1%）；损失来自 hmmer 的高 IPC 阶段，commit 宽度不是原因 |
| [EXP-007](#exp-007-tage-备选提供者计数器更新) | 2026-11-05 | TAGE 训练时也更新备选提供者的计数器（`altpcpn` 的用途） | trace-model `exp/tage-alt`（工作区 `trace-model-tage`） | 未提交、不合入 | 6 个分支难预测的 SPEC 上 MPKI 变化 ±0.6%、IPC 不变；`altpcpn` 可以删除 |
| [EXP-005](#exp-005-opt1-的-spec-对比与不改结构的参数同步到-rtl) | 2026-11-05 | opt1 的 quick SPEC 对比；不改结构的参数（第 1–3 批）同步到 RTL | trace-model `exp/batch3`、rtl `exp/batch3` | **已合入 main**（2026-11-05） | quick SPEC 6 个程序 opt1、第 3 批都慢 0.5%（gcc 1.3%）；第 1–3 批（不改结构的部分）RTL 门禁均 66/66、周期与 trace-model 一致，约省 161 万门、5 万触发器 |
| [EXP-006](#exp-006-用-dramsim3-替换固定延迟的-simddr去掉-axi-子系统分频) | 2026-11-05 | 用 DRAMsim3 替换固定延迟的 SimDDR，去掉 AXI 子系统 16 倍分频 | trace-model `exp/dram-sim`（`88e5254`）、rtl（`b19a181`） | 已合入 main（2026-11-06），周期基线重做 | 访存密集程序掉得最多（mcf −64%、gcc −36%），计算密集的少（hmmer −6%）；旧数字偏乐观 |
| [EXP-004](#exp-004-组合优化配置-opt1) | 2026-11-04 | 组合优化配置 opt1（MAX_BR 32、INT IQ 64 + 前面所有优化） | trace-model `exp/area-explore` | 未提交、未合入；SPEC 见 EXP-005 | 小程序几何平均持平，coremark 慢 1.8–2.7% |
| [EXP-003](#exp-003-rob-与-prf-扩大到-256) | 2026-11-04 | ROB/PRF 扩大到 192、256 | trace-model `exp/area-explore` | 未提交、未合入 | 都翻倍到 256 只快约 0.8%（coremark 3%），ROB 128 合理 |
| [EXP-002](#exp-002-全核面积浪费排查) | 2026-11-04 | 全核面积浪费排查：各 IQ、ibuf、front2back、分支资源、ALU/BRU 端口 | trace-model `exp/area-explore` | 未提交、未合入 | IQ 总项数 384→192、BRU 4→2 等组合后无性能损失；BPU 存储需大负载评估（“ROB 是瓶颈”的说法已被 EXP-003 否定） |
| [EXP-001](#exp-001-面积优化三个方向) | 2026-11-04 | 面积优化：FTQ 合并、LSU 端口、LD/STA IQ 合并 | trace-model `exp/area-explore` | 未提交、未合入 | 三个方向都能省面积，性能代价 0–1% |

---

## EXP-064 第三轮 TSMC 28nm DC 时序优化（`dcache_pf` / `dcache_mshr` / `lsu` Wave 1+2 / `ren` 2-stage）

- **状态**：**已合入 `main`（2026-11-24：trace-model `be7699a`、rtl `7d84c7d`）**。
- **动机与方法**：
  1. **`dcache_pf`（0 周期变化）**：`dcache_pf_berti_gen.sv` 在 16→1 锦标赛树 `gen_cand_t` 内随路携带 `d` (7b) 与 `st` (2b)，与锦标赛树并行预计算 `gen_vline_q[31:6] ± 1` 及 `xq_va_q` 27b 页标签比较，以 7b 有符号加法 + 6b 去重比较替代 32b 加法器。
  2. **`dcache_mshr`（0 周期变化）**：`dcache_mshr.sv` 与 `dcache_mshr_alloc` 并行一次性预展开 3 路 store 512b 行数据与 64b 字节选通（替代 16× `line_merge_n`）；将 `ax_req_*` 选择拆分为并行 demand/all `ttg_first_set` + `ttg_onehot_mux`。
  3. **`lsu` Wave 1 + Wave 2（0 周期变化）**：
     - Wave 1：`lp_pickn` 全切 `ttg_pick_k`；`lp_cam` 改未旋转 `hi/lo` 拆分消 2× `rotr64` 与 `+ head`；`lp_rp`/`lp_pkg`/`lp_l1`/`lp_l1b`/`lp_ms`/`lp_core` 为 4 个重放槽预寄存不可变载荷 `rp_f_q[0..3]`，消除 L1/CAM 前 64:1 LDQ mux 并切断 `lp_cam → epoch_nx → dcl_req_id`（Wave 1 实测 `0.88 → 0.97 GHz`，`lp_cam` 与 `dcl_req_id` 全部退出 Top 10）。
     - Wave 2：`lp_pkg` `rel12/rel32` 改 8B 块拆分 + 3 路并行高位相等比较（零 32b 进位链）；`lp_rp` 用 `ttg_onehot_mux` 并行选通 `rp_oh_unrot[j]`；`lp_wb` + `lp_core` 用 `alive_unrot(count_q) & rotr64(st_vec, head_q)` + `ttg_onehot_mux` 消除 `count_q → sta_*` 瓶颈。
  4. **`ren` 2-stage 流水化（`IDU → S1 → S2 → DISPATCH`）与负面探索记录**：
     - 负面探索：曾尝试在 `ren_elim_sel.sv` 预计算 33×33 `spec_ref_cnt`，因 `spec_q` 高扇出导致 DC 回归（`−0.36 → −0.42 ns`），立即放弃并回退。
     - 采纳方案：`ren_ckpt_ctl` 静态槽位预计算 `slot_age/slot_ptr/slot_eq_br` + `ren_log` 8:1 旋转后移至 `bank_rd_q` 之后（彻底清掉原 Path #2 `ckpt_head_q → u_log/rd_slot_q`）+ `ren_alloc_sel` 直接前缀 `ttg_popcount(0..7)`；`ren_inst_pipe` 拆分 S1 预译码级（预译码 RAT `rd_oh_q/wr_oh_q`、`move_shape_q`、`is_branch_q`、`raw_hit_*_q`），`ren_rat #(.PRE_OH(1))` 与 `ren_dep_check` 直用预译码结果，同步 `trace-model/back-end/Ren.{h,cpp}`。
  5. **顺带修复 `trace-model` 遗留缺陷**：`memspec_data` 在 2-stage `ren` 节奏下暴露 `back-end/Exu/include/Fu.h` `div_radix16_latency()` 直接读取 oracle `f->rs1_value/rs2_value` 而未查 `msd::live()`，修复后 69/69 全部 0 周期差。
- **实测结果**：
  - **TSMC 28nm HPC+ DC 签核（`ssg0p81v125c`, `0.50 ns`, `compile_ultra`）**：
    - `dcache_pf`：**`1.18 → 1.35 GHz` (+14.4%)**（WNS `−0.35 → −0.24 ns`，纯组合 `0.70 ns / 1.43 GHz`，53→43 级，`151,660 um²`）；
    - `dcache_mshr`：**`1.15 → 1.28 GHz` (+11.3%)**（WNS `−0.37 → −0.28 ns`，reg2reg `−0.27 ns / 1.30 GHz`，纯组合 `0.65 ns / 1.54 GHz`，54→41 级，`99,463 → 85,657 um²` **−13.9%**）；
    - `ren` (`ren_2s`)：**`1.16 → 1.22 GHz` (+5.2%)**（WNS `−0.36 → −0.32 ns`，46→40 级，TNS `−5,375`，`157,570 um²`；S1 过轻仅 ~0.15 ns、S2 仍 0.79 ns，第四轮重平衡 S1/S2 切点冲 ≥1.4 GHz）；
    - `lsu` (Wave 1+2)：**`0.88 → 0.97 GHz` (+10.2%)**（WNS `−0.64 → −0.53 ns`，纯组合 `0.98 ns / 1.02 GHz`，TNS `−15,695 → −10,579` **−32.6%**，`918.6k → 873.6k um²` **−4.9%**；新顶路径 `ldq/st_q → lp_l1 → lp_cam → ldq/f_q[spec]` 0.98 ns，第四轮以 `L0/L1` 流水拆拍攻克）。
  - **全量 SPEC06 INT 386/386 点（`sim64_r3` vs `sim64_r2`，0 失败）**：**Geomean `−1.07%`**（`462.libquantum +0.10%`、`403.gcc −0.25%`、`456.hmmer −0.34%`、`429.mcf −0.37%`、`464.h264ref −0.52%`、`471.omnetpp −0.74%`、`483.xalancbmk −1.15%`、`400.perlbench −1.56%`、`401.bzip2 −1.60%`、`458.sjeng −2.07%`、`445.gobmk −2.09%`、`473.astar −2.17%`）。
  - **验证与对齐**：`comb_graph.py --check` 0 隐患；`trace-model` `linux_check.sh` 启动到 `rv64 login:`（0 oops/panic）；RTL `lint_chip.sh` 0 警告；**`fm_gate.sh` + `tm_cycles.sh` 69/69 PASS、0 FAIL、0 SKIP、0 FM 不一致、69/69 周期 0 差异**；**`eda-05` 8 线程静态 `soc_tb` `rv64gc`+`Sv39` Linux 26 窗（`s01..s26`，每窗 510 万指令，最长达 1,415 万周期/窗，合计 ~1.326 亿指令）：26/26 PASS、0 FAIL、0 FM 不一致、26/26 PT/UP 指纹 100% 逐拍全等**。

---

## EXP-063 第二轮 TSMC 28nm DC 时序优化（`bpu_eval` / `bpu_spec` / `lsu` / `exu_ctrl`）

- **状态**：**已合入 `main`（2026-11-24：trace-model `4626924`、rtl `aa7888b`）**。
- **动机与方法**：
  1. **补齐 `exu_ctrl` DC 28nm 数据**：修复 `exu_ctrl_pkg.sv:205` `xc_is_fp_kind` 返回 `bit` 在 `localparam` 循环内触发 DC Presto `(VER-37)` 断言，改为返回 `int`（`1 : 0`）并同步 3 处调用。
  2. **`bpu_eval` 真并行 2-Ahead B（打破 Block A → Block B 串行天花板）**：纯组合优化仅将 `bpu_eval` 从 `-0.69 ns` 推至 `-0.67 ns`；48 点 SPEC06 DSE 对比 `AH2_PAR=1`（保留 `u0_b` 回退，`+0.10%` 但 DC 仍停在 `~-0.60 ns`）与 `AH2_PAR=2`（2-Ahead B 改为 `(key_base, s0_base)` 索引、`bpu_ftb_tab` 增 `STORE_B_BASE=1` 存 `b_base`、`ah2_eval` 使用 `ah2_b_base + block_bnd(ah2_b_base)` 与 Block A 完全并行评估、删除串行 `u0_b` 回退、末尾校验 `ah2_b_base == s0_b_base` 与 `b_truncated`），采纳 `AH2_PAR=2` 为唯一默认并删实验开关。
  3. **`bpu_spec` 寄存态 `M_ARCH` 恢复**：第一轮优化后残余瓶颈为 `commit br_type[0..7] → aras_d → s_d1 → spec_a_ras_top`（`-0.66 ns`）；改为 `M_ARCH` 直接从寄存态 `arch_sr_q / arch_fh_q / aras_q` 恢复（同步 `BPU_pipe.h`），彻底切断 commit→spec 组合环，IPC 影响 `~0.00%`。
  4. **`lsu` 纯结构优化（0 周期变化）**：`lp_cam.sv` 利用代数恒等式 `rotr64(rotl64(mask_unrot, head) & raw, head) == mask_unrot & rotr64(raw, head)` 与 6-bit 常量比较消除 2×64b 桶形移位器；`lp_wk.sv` 将 3 路 `stlf_confirm` 与 `off_a` 移至与 `sta_info[k].stq == blk` 并行预计算。
  5. **`ren` 两级流水 DSE（暂缓至第三轮）**：在 `trace-model` 48 点探索 2 级 `ren`（有效 47 点均值约 `~−1.0%`），鉴于当前整核唯一 `<1.0 GHz` 瓶颈为 `lsu` (0.88 GHz)，留待第三轮与 `lsu` 流水切分一并落地。
- **实测结果**：
  - **TSMC 28nm HPC+ DC 签核（`ssg0p81v125c`, `0.50 ns`, `compile_ultra`）**：
    - `exu_ctrl`：**WNS `0.00 ns`（MET ≥2.00 GHz）**、13 级、`31,761 um²`；
    - `bpu_eval`：**`0.84 → 1.28 GHz` (+52.4%)**（WNS `−0.69 → −0.28 ns`，纯组合 `0.68 ns / 1.47 GHz`，69→49 级，`25,652 → 23,911 um²` −6.8%）；
    - `bpu_spec`：**`0.86 → 1.20 GHz` (+39.5%)**（WNS `−0.66 → −0.33 ns`，纯组合 `0.70 ns / 1.43 GHz`，`reg2reg −0.32 ns / 1.22 GHz`，`156,084 → 142,200 um²` −8.9%）；
    - `lsu`：**`0.83 → 0.88 GHz` (+6.0%)**（WNS `−0.71 → −0.64 ns`，56 级，`927k → 919k um²`），清晰暴露第三轮流水切分目标（`rp_ldq_q → lp_cam → req_id` 1.06 ns 与 `lp_ldq_ent` P1..P14 状态链 1.10 ns）。
  - **全量 SPEC06 INT 386/386（`res_r2_386` vs EXP-062 `res_pf4_386`，0 失败，全点指令数一致）**：Geomean **`−1.20%`**（`sjeng −3.83%`、`gcc −3.67%`、`perlbench −2.63%`、`gobmk −1.08%`、`bzip2 −0.96%`、`astar −0.79%`、`omnetpp −0.38%`、`xalancbmk −0.31%`、`h264ref −0.28%`、`libquantum −0.12%`、`mcf −0.11%`、`hmmer −0.08%`）。
  - **正确性与对齐**：`comb_graph` 0 隐患、`linux_check.sh` PASS、`lint_chip.sh` 0 警告/0 错误、**`fm_gate.sh` + `tm_cycles.sh` 69/69 PASS（0 FM 差、0 周期差）**、**`eda-04/05/07` 8 线程静态 `soc_tb` rv64gc Linux 26 窗（`s01..s26` + `s00`，~1.377 亿指令，最长达 1,328.5 万周期/窗）26/26 PASS、0 FM 差、100% PT/UP 逐拍全等**。

## EXP-062 TSMC 28nm DC 时序基线与第一轮 5 模块时序优化

- **状态**：**已合入 `main`（2026-11-24：trace-model `d872061`、rtl `7f31634`）**。
- **方法**：
  1. **建立 Synopsys DC 28nm 权威签核体系**：在 `eda` 集群基于 `DC W-2024.09-SP2` + TSMC 28nm HPC+（`tcbn28hpcplusbwp12t40p140{,lvt}ssg0p81v125c.db`，`CLK=0.50ns`，`uncertainty=0.03ns`，`in/out_delay=0.05ns`，`compile_ultra`）完成 22 个核心模块摸底（脚本存档 `/nfs_global/S/houruyao/dc28_check/{run_dc.sh, list_files.py}`，含包拓扑排序与 `div_core`/`bpu_spec` DC Presto 语法修复）。确认核心瓶颈集中于 `dcache_pf` (0.37 GHz)、`bpu_spec` (0.73 GHz)、`lsu` (0.83 GHz)、`bpu_eval` (0.84 GHz)、`ren` / `axi_llc_bop` (1.05 GHz)、`dcache_mshr` (1.15 GHz)；其余 `isu` (1.37) / `rob` (1.64) / `div_unit` (1.67) / `mul_unit` (1.85) / `dispatch` & `tlb_mmu` (1.89) / `dcache_s1/s2` & `icache_ctl/itlb` (≥2.0 GHz) 均健康。
  2. **第一轮 5 模块优化**：
     - **`dcache_pf`**（唯一含流水切分，同步 `trace-model` `DataPrefetcher.h`）：切为 4 级流水（`hist → srch_r_q → tab_s1 → t1_q → tab_s2 → gen`，`srch_stall = srch_r_v_q` 零冒险转发），4 级并行 Top-2 锦标赛树 + `ttg_pick_k(16,2)` 替代两级串行 `pick_slot`，去掉同拍 `srch→trig` 与 `pfi_en→fill→pf_hit` 三级 CAM 旁路。
     - **`axi_llc_bop`**（0 周期变化）：5 级二进制最大分数树 + 3 路候选地址与去重检查同 `rr_tag_q` (256:1 mux) 并行预计算。
     - **`bpu_spec`**（0 周期变化）：3 级 Kogge-Stone 钳位前缀并行 RAS + 128-bit 线性移位寄存器 `arch_sr_q` 替代 1024b 环形 `arch_q` 消除 `M_ARCH` 桶形移位器（并在 `arch_to_hist` 按 `extra_bits` `0/3/6` 对齐 `M_ARCH` 同拍 A/B 推入的 `head`，保持 `HR_BITS=1024`）。
     - **`ren`**（0 周期变化）：`ren_ckpt_ctl` 导出 `rd_base_next`，`ren_log` 在 `T-1` 拍预寄存 8 项读窗 `rd_slot_q[0..7]`，将 32:1+8:1 mux 移出提交→空闲表关键路径。
     - **`dcache_mshr_alloc`**（0 周期变化）：8 级串行 `ttg_first_set` 改 `ttg_pick_k(16,8)` + 并行 `ttg_popcount`。
- **实测结果**：
  - **TSMC 28nm DC 签核（`ssg0p81v125c`, `0.50 ns`）**：`dcache_pf` **0.37→1.18 GHz**（`−2.23→−0.35 ns` / `172→53 lvl` / `184k→148k um²`；Yosys `384→75`）、`axi_llc_bop` **1.05→1.47 GHz**（`−0.45→−0.18 ns` / `51→42 lvl`；Yosys `291→75`）、`bpu_spec` **0.73→0.86 GHz**（`−0.87→−0.66 ns` / `69→41 lvl`）、`ren` **1.05→1.16 GHz**（`−0.45→−0.36 ns`）、`dcache_mshr` **1.15 GHz**（reg2reg `1.18 GHz`；Yosys `123→99` 跌破 100 层）。
  - **SPEC06 INT 386/386（`res_pf4_386` vs EXP-060 `res_dse_ldw_exp060`，0 失败）**：Geomean **`+0.51%`**（`hmmer +2.66%`、`sjeng +1.11%`、`gobmk +1.01%`、`h264ref +0.87%`、`gcc +0.56%`，最差 `−0.09%`，全点指令数一致）。
  - **对齐与正确性**：`comb_graph` 0 隐患、`linux_check.sh` PASS、`lint_chip.sh` 0 警告/0 错误、8 项大程序/定向程序周期全等（`memspec_pf` `3000→3005`）、**rv64gc Linux 26 窗（`s01..s26` + `s00`，~1.377 亿指令）26/26 PASS、0 FM 不一致、100% PT/UP 逐拍全等**。

## EXP-061 乘法器 Radix-4 Booth + 1× Radix-16 Early-out 变延迟除法 + 全套自研可综合 RV64FD FPU

- **状态**：**已合入 `main`（2026-11-23：trace-model `ac0a4bc`、rtl `1df38b0`）**。
- **方法**：
  1. **乘法器（零周期变化）**：`mul_core.sv` 综合路径升级为 Modified Radix-4 Booth 编码（部分积 68→34 行、Wallace 压缩 10→8 级）+ 128 位 Kogge-Stone，仿真保留 `a * b` 快速路径。
  2. **除法器 DSE 与硬件忠实落地**：先在 `trace-model` 用 4 组全量 SPEC06 INT 386 点对比（vs EXP-060 `15.25 /GHz`）：1× 固定 32/16 拍 `−0.42%`、1× Radix-4 + Early-out `+0.37%`、1× Radix-16 (双 Radix-4) + Early-out `+0.52%`、2× 固定 4 拍理论上限 `+0.58%`。采纳帕累托最优的 **1× Radix-16 (双 Radix-4) + CLZ Early-out（2..17 拍）**：Port 3 去掉 `OP_MASK_DIV`（`DIV_NUM=1`、`TOTAL_FU_COUNT=30`、`MAX_WAKEUP_PORTS=21`），`dispatch` 将 `UOP_DIV` 固定路由至 `IQ_INT`，删去 `isu` 的 `div_wake_slots` 与 Port 1 `isu_wb_gate` 移位寄存器，改为由 `exu_iter_ctl.wb_next` 在完成前 1 拍动态广播唤醒消费者并阻塞 Port 1 单周期 ALU 发射。
  3. **全套自研可综合 RV64FD FPU**：在 `rtl/backend/exu_fu/` 新增 `fp_arith_pkg`、`fp_misc_core`、`fp_i2f_core`、`fp_fcvt_core`、3 拍全流水 `fp_fma_core` 与迭代 3b/拍 `fp_div_core`（精确对齐 11/13/19/23 拍），默认仿真保持快速 DPI 路径、`SYNTHESIS` 或 `-DFPU_REAL` 切换为真可综合 RTL。
- **实测结果**：
  - **SPEC06 INT 386/386（硬件忠实版 `div16_hw`，0 失败，vs EXP-060 `15.25 /GHz`）**：Geomean **`+0.53%` → `15.33 分/GHz`**（`hmmer +2.65%`、`sjeng +1.12%`、`gobmk +1.05%`、`h264ref +0.85%`、`gcc +0.68%`、`xalancbmk +0.13%`、单点最高 `+16.7%`）；`dhrystone 88,702 → 85,401 (−3.72%)`、`coremark 207,177 → 206,921 (−0.12%)`、`prime −55.8%`、`wanshu −56.1%`。
  - **Yosys 综合（`eda-10`，`strash;balance;map`）**：`mul_unit` `40,041→27,473`（−31.4%）/30 层、`div_unit` `12,340`/50 层、`isu` `1,079,759→1,071,347`（−8,412）/60 层；自研 FPU 5 核心全部 `<100` 层（`fp_misc_core` 1,874/39 层、`fp_i2f_core` 1,790/73 层、`fp_fcvt_core` 4,646/83 层、`fp_fma_core` 33,776/98 层、`fp_div_core` 10,885/73 层）；整块 `exu` `304,977` cells / **98 层**。
  - **正确性验证**：`comb_graph` 0 隐患、`run_gate` 62/62、`run_gate_c` 68/68、`linux_check` PASS；RTL `lint_chip` 0、`mul_check` 400 万/`div_check` 10.3 万/`fp_synth_check` 235 万全 0 不一致；`-DFPU_REAL` 整核 `fm_gate` **69/69 PASS（0 周期差）**；`eda` 26 窗 Linux（~1.326 亿指令）0 FM 不一致（25/26 PT/UP 全等，仅 `s19` `cyc=2372697` 1 处错路微差）。

## EXP-058 硬件忠实版 LLC Bingo 4KB 空间预取器

- **日期 / 分支**：2026-11-22–23；`trace-model` `exp/bingo`（`aa345c9`）、`rtl` `rtl/bingo`（`2fbf053`），**已合入 `main`**。
- **动机**：在 EXP-054 验证 LLC 空间预取（SMS）零回归有效且 EXP-056 补齐 L2 TLB 后，前端与地址翻译瓶颈进一步缓解，LLC 空间预取对不规则访存（`omnetpp`/`mcf`/`xalancbmk`）收益突出；相比单表 SMS，Bingo 双表（`PHT_L` 长事件 `PC+Offset` + `PHT_S` 短事件 `PC` 兜底）能在不改前端/L1D 关键路径的前提下进一步抬升覆盖率。
- **硬件结构（总存储 `~26.75 KiB`，占 4 MiB LLC `0.65%`）**：
  - **真实 12-bit `pc_hash` 边带**：L1D MSHR 分配时记录 `(pc>>1)^(pc>>13)^(pc>>21)` 低 12 位，经 `dcache_mshr → mem_axi → axi_interconnect → axi_llc_lookup` 透传至 LLC。
  - **FT + AGT + 提交队列（`axi_llc_bingo_agt.sv`）**：32 项 FIFO 过滤表 FT、32 项 31-bit tree-PLRU 全相联累积表 AGT、4 项提交队列 `cmt_q`、1 项待查表锁存 `pred_pend`。
  - **1RW SRAM 双 PHT（`axi_llc_bingo_pht.sv`）**：3 状态 FSM（`ST_IDLE`/`ST_PRED`/`ST_CMT`）驱动 4× 1D `256×138b` `PHT_L`（`17.25 KiB`）+ 4× 1D `128×133b` `PHT_S`（`8.31 KiB`，相对偏移经单行桶形移位还原），均为 3-bit tree-PLRU；配合 `ttg_popcount` 密集流过滤（`>= 48` 跳过）。
  - **节流与发射（`axi_llc_bingo.sv`）**：无乘法器周期准确率节流器（窗口 `256`、阈值 `26` 即 `10.16%`，低于阈值降为 1/8 试探 `deg=2`）、1 候选/拍发射器 + 16 项去重队列 `bingo_q`；与既有 BOP 双优先级协同（`bop_q > bingo_q`，`BOP_INF: 4 → 8`）。
- **SPEC06 INT 386/386 实测（`eda`，`res_bingo_hw_386` vs EXP-056 `res_l2tlb_rtl` `14.69 /GHz`，0 失败）**：
  - **Geomean `+1.26%` → `14.88 分/GHz`**（11 正 1 平 **0 回归**）：
    `471.omnetpp +7.01%`、`429.mcf +2.59%`、`483.xalancbmk +1.37%`、`403.gcc +1.11%`、`458.sjeng +0.99%`、`473.astar +0.97%`、`400.perlbench +0.78%`、`401.bzip2 +0.23%`、`464.h264ref +0.12%`、`462.libquantum +0.09%`、`445.gobmk +0.08%`、`456.hmmer −0.02%`。
- **验证与综合**：
  - `trace-model`：`comb_graph.py --check` 0 隐患；`run_gate.sh` 62/62（默认 / `PF_ENABLE=0` / `LLC_BINGO=0`）；`linux_check.sh` 到 `rv64 login:`（0 oops/panic）。
  - `rtl`：`lint_chip.sh` 0 警告；`fm_gate.sh` **69/69 PASS（0 FM 差、0 周期差）**；`eda-05` Yosys 综合 `axi_llc_bingo` 经桶形移位优化由 163 层降至 **`41,232` cells / 48 层**；`eda-05..09` 27 窗 `rv64gc` Linux 全部跑完（`137,700,059` 指令 0 FM 差、**27/27 PT/UP 指纹 100% 逐拍全等**）。

---

## EXP-057 Cache 层级探索（64KB L1I 与 1MB L2 + 16MB L3 简化模型评估）

- **日期 / 分支**：2026-11-22；基于 EXP-056（`L2TLB+PWC`）评估，分支 `trace-model` `exp/l2l3`（worktree `trace-model-l2l3`，未合入）。
- **实验 1：64KB L1I (`128×8`) + 64KB L1D (`256×4`)**（当前主线 L1D 已是 64KB PIPT，L1I 为 32KB PIPT）：
  - 全量 SPEC06 INT **386/386 点（0 失败，vs EXP-056 `res_l2tlb_rtl` `14.69 /GHz`）**，结果目录 `res_l2tlb_64ki`：
  - **Geomean `+0.36%`**（`perlbench +2.44%`、`xalancbmk +1.28%`、`omnetpp +0.61%`、`h264ref −0.21%`、`gcc −0.19%`，其余基本持平），相对 EXP-055 `main` 累计 `+3.55%`（`~14.75 /GHz`）。收益偏小，暂不采纳。
- **实验 2：1MB 16-way 私有 L2 + 16MB 16-way Non-inclusive SRRIP L3 (`L3_LAT=20` cyc)**（替换当前 4MB 共享 L2/LLC）：
  - 在 `exp/l2l3` 中于 `AXI_LLC` 之后增加简化版 16MB 16-way Non-inclusive SRRIP L3 模型（命中固定 20 周期延迟，未命中走 DRAMsim3）。
  - 全量 SPEC06 INT **386/386 点（0 失败，vs EXP-056 4MB L2 `res_l2tlb_rtl` `14.69 /GHz`）**，结果目录 `res_l2_1m_l3_16m`：
  - **Geomean `+4.11%`**（相对 EXP-055 `main` 累计 **`+7.42%` → `~15.30 分/GHz`**）：
    - 大幅收益项：`429.mcf +37.73%`、`471.omnetpp +14.53%`、`483.xalancbmk +7.28%`、`462.libquantum +3.50%`、`473.astar +2.24%`；
    - L2 缩容（4MB → 1MB）回退项：`403.gcc −4.66%`、`401.bzip2 −3.45%`。
  - **结论**：大工作集访存程序（`mcf`/`omnetpp`/`xalancbmk`）受 16MB L3 收益极大；若后续真正落地三级缓存，建议考虑 `2MB L2 + 16MB L3` 以兼顾 `gcc`/`bzip2` 工作集。当前保留 `exp/l2l3` 分支，暂不合入 `main`。

## EXP-056 统一 L2 TLB（1024×4 1RW SRAM + 8 项大页 CAM）+ 16 项 Sv39 PWC

- **日期 / 分支**：2026-11-22；`trace-model` `exp/l2tlb`（`c174d8d`）、`rtl` `rtl/l2tlb`（`c630c5d`），已快进合入 `main`。
- **问题与设计**：EXP-055 扩窗至 `PRF=256 / ROB=256` 后，`mcf`/`xalancbmk`/`omnetpp`/`astar` 的 L1 DTLB/ITLB miss 直接触发 3 级 Sv39 页表遍历，延迟高且挤占 DCache 读口。本轮在 `ptw_walk`（`MemPtwBlock`）内实现硬件可综合的统一 L2 TLB + PWC，零 L1 关键路径改动：
  - **1024 项 4 路组相联 4KB STLB**：4 个独立 1D `256×76b` 1RW SRAM bank（RTL 中置入 `genvar w` 且无复位，Yosys 综合为干净 `$mem_v2`），XOR 组索引 `vpn[7:0] ^ vpn[16:9]`、3-bit tree-PLRU、1 拍 `STLB_LK` 查表；
  - **8 项 RR 大页 CAM**（2MB/1GB megapage/gigapage）+ **16 项 RR Sv39 PWC**（缓存 L2/L1 非叶 PTE，20-bit `root` 匹配）；
  - **`sfence.vma` 刷新**：`TlbMmu` / `rob_bcast_fence` 透传 `sfence_flush` 至 `ptw_walk` 同拍清空全部有效位。
- **全量 SPEC06 INT 386/386 点验证（`res_l2tlb_rtl` vs EXP-055 `res_dse_win256_main` `14.24 /GHz`，0 失败）**：
  - **12/12 全正、Geomean `+3.17%` → `14.69 SPECint2006 / GHz`**：
    - `429.mcf +14.61%`、`483.xalancbmk +9.74%`、`471.omnetpp +4.38%`、`473.astar +3.34%`、`400.perlbench +2.22%`、`401.bzip2 +2.21%`、`403.gcc +0.62%`、`464.h264ref +0.60%`、`458.sjeng +0.49%`、`445.gobmk +0.48%`、`456.hmmer +0.36%`、`462.libquantum +0.06%`。
- **关键问题修复与 RTL 综合优化**：
  1. **`TraceBridge` PTW 读未提交 PTE 导致 Linux 早期 oops**：`MemRouteBlock::comb_response()` 原调用 `tbhook::mem_read()` 读出 ROB 内未提交 store 的投机值（`setup_vm_final` 中较新 `clear_fixmap` 清零 `0x803e6ff0` 影响 80 条前老 load 的页表遍历），新增 `Bridge::read_committed_word()` / `tbhook::mem_read_committed()` 回溯 `chain_` undo log 读已提交内存，根治 oops 且与 RTL DCache 逐拍一致。
  2. **Yosys 面积与深度优化**：将二维数组 `stlb_mem_q[4][256]` 拆为 `genvar w` 内 4 个独立 1D `mem_q[256]`（`ptw_walk` 单元从 `84,338` 骤降至 **`5,446` cells / 21 `$mem_v2`**）；将 `PW_L1_REQ`/`PW_L2_REQ` 授权与 PTE 分类从 `select_any → state_b` 解耦至 `state_q`，深度从 `50` 降至 **`44` 层**（低于改前 `47` 层）。
- **验证**：
  - `trace-model`：`comb_graph.py --check` 0 隐患、`run_gate.sh` 62/62、`PF_ENABLE=0` 62/62、`run_gate_c.sh` 68/68（`rvc-sv39.bin` `3270→3268`）、`linux_check.sh` `rv64 login:`（0 oops/panic）；
  - `rtl`：`make cfg`（175 常量）、`lint.sh` & `lint_chip.sh` 0 警告/0 错误、新增 `directed/l2tlb_pwc.bin`（`9041 == 9041` 周期，14,243 指令 0 FM 差）、`fm_gate.sh` **69/69 PASS（0 FM 差、0 周期差）**、`eda-05..10` 27 窗 `rv64gc` Linux（27/27 DONE、约 1.377 亿指令 0 FM 差、27/27 UP 全等、26/27 PT 全等，`s02` 1 处错路投机差 3 拍重收敛至末尾全等）。

## EXP-055 后端指令窗口扩展（`PRF=256 / ROB=256`）与 `ren` 公共原语降深度

- **日期 / 分支**：2026-11-22；`trace-model` `exp/win256`（`16548ba`）、`rtl` `rtl/win256`（`f1fed8a`），已快进合入 `main`。
- **问题与动机**：对 EXP-051 全量 386 点（`res_fe2f_final_386`）做 SimPoint 加权 L1+L2 TMA 拆分发现，`Backend Bound = 33.8%` 为头号瓶颈，其中 `SLOT_REN_NOPREG = 14.9%`（`PRF=128` 仅 96 个可用物理寄存器，严重小于 `ROB=128`）、`SLOT_BE_ROB_FULL = 11.6%`、`SLOT_IDU_NOBRTAG = 3.4%`，而执行口与队列（`IQ_FULL = 0.88%`、`LDQ_FULL = 0.0%`、`BE.core = 2.9%`）几乎无瓶颈。
- **两轮 48 点快评 DSE（`me_jobs48.txt`，vs `res_me2_386` 同 48 点，全程 `PMU=1`）**：
  - **第一轮（窗口三参数扫描）**：`160/128/32` **`+0.85%`**、`192/128/32` **`+0.87%`**（单扩 PRF 精确饱和在 160）；`192/192/32` **`+3.89%`**、`192/192/48` **`+3.88%`**、`224/192/64` **`+3.94%`**；`256/256/64` **`+5.53%`**。
  - **第二轮（`ROB=192` 配套队列与 `256/256/32` 验证）**：在 `192/192/32`（`+3.89%`）上叠加 `IQ_STD=32`（`+3.75%`）、`BR=48+IQ_BR=48`（`+3.78%`）、`PRF=224+BR=48`（`+3.86%`）、`STQ=96`（`+3.90%`）、`MSHR=32`（`+3.82%`）均无显著净增益；而 **`256/256/32`**（47/48）即达 **`~+5.48%`**（吃掉 `256/256/64` 99%+ 收益），且 `256` 是 2 的幂（RTL `ren_free_list` 原生 8-bit 环回，且与 `192` 同为 9-bit tag / 8-bit ROB idx），成为最优工程甜点。
- **全量 SPEC06 INT 386/386 点验证（`res_dse_win256_main` vs `res_exp053_main_386` `13.48 /GHz`，0 失败）**：
  - **Geomean `+5.64%` → `14.24 SPECint2006 / GHz`**（`464.h264ref +13.07%`、`471.omnetpp +12.67%`、`483.xalancbmk +8.40%`、`456.hmmer +6.95%`、`458.sjeng +6.56%`、`400.perlbench +5.77%`、`403.gcc +5.45%`、`473.astar +5.00%`、`401.bzip2 +2.18%`、`445.gobmk +1.80%`、`429.mcf +1.06%`、`462.libquantum −0.27%`）。
  - TMA 变化（vs `res_fe2f_final_386`）：`Retiring 31.58% → 33.70%`（+2.12 pp）、`Backend Bound 33.81% → 26.45%`（−7.36 pp）、`MLP 3.54 → 4.63`（+30.8%）。
  - 副产品发现：`462.libquantum` 停滞根因为 16 项 L1D MSHR 100% 饱和（`MLP = 15.07/16`）叠加 L1D Berti 预取 64% 晚发（`PF_LATE 18.4/28.7`）与单通道 DDR4 排队延迟（`MissLat 71.9 cyc`），需后续通过私有 L2 / 更深 LLC 预取 / MSHR 扩容解锁。
- **RTL 落地、Yosys 综合（`eda-08`，`strash;balance;map`）与门禁**：
  - 仅参数化 8 个 wrapper 写死的 `rob_idx` / `rob2dis_free` 位宽，并针对 `ren`（原 100 层）做三处零周期公共原语降深度重构（`ren_dep_check` 两级旁路、`ren_elim_sel` 3 级 Kogge-Stone 指针跳跃、`ren_rat` `snapshot` 去 `fire`）：`ren` **100 → 91 层**（`586,315` cells，低于原 128/128 的 97 层）、`prf` **25 层**（`614,529`）、`rob` **64 层**（`897,972`）、`isu` **50 层**（`1,018,639`）。
  - 验证：`lint_chip` 0、`tests/ren_elim_sel` 100k 0 不一致、`fm_gate` **68/68（0 FM 差、0 周期差）**、`trace-model` `comb_graph` 0 / 62+68 门禁 / Linux 启动、`eda-05..10` 27 窗 `rv64gc` Linux **137,700,051 指令 0 FM 差且 27/27 PT/UP 100% 全等**。

## EXP-054 L1 解耦 Breadcrumbs 与 Berti 融合及 LLC SMS 空间预取体系评估

- **日期 / 分支**：2026-11-22；`trace-model` `exp/pf-bc-sms`（独立 worktree `trace-model-pf-bc-sms`，基于 `main` `1939bd1`，未提交、暂未做 RTL）。**状态**：**探索完成（待决策，未合入）**。
- **问题**：在 EXP-048（L1 硬件 Berti + LLC BOP + 16/16 MSHR）与 EXP-050~052（前端提速）之后，SPEC06 INT 剩余访存瓶颈高度集中在 `429.mcf`、`471.omnetpp`、`473.astar`、`403.gcc`、`483.xalancbmk` 五个程序（空间簇局部性 + 指针追逐/间接数组）。本轮在 `trace-model` 上系统评估：① 移植 `gem5x86`/`gem5rv`（`exp022e` `761b4c8300`）最新解耦简化版 Breadcrumbs（含自适应 timely distance）并与现有硬件 `BertiHw` 融合；② 在 `AXI_LLC` 中引入硬件 SMS（Spatial Memory Streaming）并与现有 BOP 协同。
- **实现与开关（全部默认关闭，零环境变量时 `comb_graph.py --check` 0 隐患、`run_gate_c.sh` 68/68 与 `main` 逐拍相等）**：
  - **L1 解耦 Breadcrumbs（`MemSubSystem/include/Breadcrumbs.h`）**：
    - 解耦 Rename 标签引擎：`BC_LOGTAG=6` 32 项架构寄存器标签表（无 squash 检查点）+ 非阻塞旁路标签队列（只让有传播规则的 `LOAD`/`ADD` 入队，满则丢弃并插 resync marker，零 `ren` 反压）。
    - 训练：16 项 `Value Table`（load 写回锁存，不读 PRF）+ 32 项 `Relation Table`（提交时训练，支持双链 `BC_CHAIN_DUAL`、算术/逻辑右移 `rs`、256-bit `recentMiss` 过滤、可选 `PF_BC_STORE_IND=1` scatter store 消费端）。
    - 与 `BertiHw` 融合：`BertiHw` 保留 6-bit 字节偏移 `boff` 并在发预取时向 BC 登记 producer 行元数据（防结构体读错字段）；所有 BC 虚拟目标加 Sv39 canonical VA 过滤并复用 EXP-048 现成空闲 DTLB 端口翻译队列 `g_pf_xq`（RAM 边界过滤防 MMIO 死锁）。
    - 模式：`PF_BC=0`（关）、`1`（纯间接 + Berti 协同）、`2`（+ 自适应 timely distance 步长，`PF_BC_SMODE=0` 互补 Berti / `1` 并行 / `2` 替换 Berti）、`3`（+ LLC 远端窗口与 LLC fill 提前展开）；支持 `PF_BC_RES`、`PF_BC_IND_LLC`、`PF_BC_TQ_W`、`PF_BC_CONF`、`PF_BC_MAXHOP`。
  - **LLC 硬件 SMS（`MemSubSystem/include/Sms.h` + `AXI_LLC.cpp`）**：
    - 硬件表结构：FT（32 项 FIFO）+ AGT（32 项 LRU，AGT 换出或 LLC 换出时提交至 PHT）+ PHT（1024 项 LRU，2-bit 饱和置信度）。
    - 关键工程设计：① **12-bit PC hash 透传**（`g_llc_pc_sideband` 模拟 L1D MSHR + AXI `ARUSER`，无 PC 对照 `LLC_SMS_PC=0`）；② **标准 trigger-only 预测**（`LLC_SMS_TRIGONLY=1`，仅区域首访预测一次，消除单 region 重复预测风暴）；③ **双优先级队列**（`bop_q_` 高优 + `sms_q_` 低优，不互相挤队）；④ **密集连续流过滤**（`LLC_SMS_MAXDENSE=28`，跳过 2KB 区域内 ≥28/32 块全满的纯顺序流，彻底保护 `libquantum`）；⑤ **10-bit 周期准确率节流器**（`LLC_SMS_THROTTLE=1`，每 256 次发送若 useful < `LLC_SMS_TMIN`%，降为 1/8 试探，彻底消除低准确率随机点回退）。
    - 开关：`LLC_PF_KIND=0`（仅 BOP，默认）/ `1`（仅 SMS）/ `2`（BOP+SMS），配合 `LLC_SMS_REGION`（2048/4096）、`LLC_SMS_THR`（1/2）、`LLC_SMS_DEG`、`LLC_SMS_STORE`、`LLC_BOP_INF`、`LLC_PF_Q`。
- **模型近似与硬件估算**：
  - LLC SMS（2KB region, FT 32, AGT 32, PHT 1024 × 32×2b ≈ 8 KB + tag ≈ **~10 KB**）+ 12-bit PC hash 经 L1D MSHR/AXI `ARUSER` 透传（不进 DDR），逻辑简单且完全不在核内关键路径。
  - L1 BC（32 项 tag + 16 项 TQ + 16 项 LDT + 16 项 Value + 32 项 Relation ≈ **~3 KB**），`trace-model` 里 fill 展开读功能内存 `tbhook::mem_read` 近似 fill buffer 数据，写回值取自 `tb::Fact::rd_value`。
- **阶段 1：访存 6 程序 59 点消融摘要（`memgrp_jobs.txt`，53 交集点 vs `res_me2_386` EXP-052 基线，0 失败）**：
  - **关键发现 1（PC hash 必不可少）**：无 PC 版 `sms_nopc` 为 **−3.11%**（`omnetpp −5.18%`、`xalancbmk −7.46%`），带 12-bit PC hash 立刻翻正。
  - **关键发现 2（纯 SMS 不能替换 BOP，双优先级 + trigger-only + 密集流过滤缺一不可）**：纯 SMS `sms_only_trig` 为 **−1.33%**（`libquantum −4.47%`）；R1 混合版 `bop_sms` 虽把 `omnetpp` 拉到 `+4.67%`，但把 `libquantum` 拖垮 `−7.30%`；改用 **双优先级队列 + trigger-only + `MAXDENSE=24~28` + `INF=8`** 后，`libquantum` 回到 `+0.05%~+0.12%`，6 程序 Geomean 升至 **`+1.39% ~ +1.45%`**（`omnetpp +5.25%`、`mcf +1.66%~+1.91%`、`xalancbmk +1.15%~+1.55%`）。
  - **关键发现 3（Store 辅助训练与 BOP 负偏移）**：`LLC_SMS_STORE=1` 与关闭结果完全一致（+1.23% vs +1.23%），64 STQ + Write Buffer 下无额外收益；`LLC_BOP_NEG=1` 在 53 点上为 −0.07%（无净收益）。
  - **关键发现 4（BC 融合）**：纯 BC 替换 Berti（`PF_BC=2 PF_BC_SMODE=2`）掉 **−10.50%**（`mcf −33.4%`、`libquantum −13.8%`），不可替换 Berti；修复 `boff` 字节偏移 + `conf=3` + canonical VA 过滤后，`PF_BC=2 PF_BC_SMODE=0`（互补 Berti）在 53 点上达 **`+0.38% ~ +0.40%`**（`mcf +1.70%~+1.85%`），与 LLC SMS 叠加达 **`+1.44%`**（`mcf +2.73%`、`omnetpp +3.78%`、`xalancbmk +1.73%`）。
- **阶段 2：全量 SPEC06 INT 386/386 点验证（`jobs95.txt`，SimPoint 加权 IPC，vs EXP-052 `res_me2_386` `13.49 分/GHz`，0 失败）**：

| Benchmark | Pts | EXP-052 Base IPC | `LLC_SMS`（无节流） | `L1_BC2`（纯 L1 BC） | `COMBO`（BC2+SMS） | **`SMS_T1_THR`（推荐冠军）** | `SMS_T2_THR`（保守） | `SMS_T1_THR` 最差 / 最优点 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `400.perlbench` | 24 | 3.5536 | +0.82% | −0.03% | +0.91% | **+0.87%** | +0.89% | sp1 −0.6% / sp39 +3.4% |
| `401.bzip2` | 48 | 2.5643 | +0.16% | +0.78% | +1.03% | **+0.22%** | +0.07% | sp34 −0.6% / sp14 +1.8% |
| `403.gcc` | 34 | 1.8648 | +1.39% | +0.44% | +1.80% | **+1.20%** | +0.70% | sp28 −0.6% / sp9 +9.4% |
| `429.mcf` | 45 | 0.4004 | **+3.85%** | −0.29% | +2.82% | **+2.10%** | +1.23% | sp21 −0.3% / sp43 +7.1% |
| `445.gobmk` | 29 | 2.6172 | +0.06% | +0.03% | +0.06% | **+0.07%** | +0.06% | sp29 −0.5% / sp16 +0.8% |
| `456.hmmer` | 23 | 6.0436 | +0.02% | +0.02% | +0.04% | **+0.01%** | −0.02% | sp2 −0.1% / sp24 +0.3% |
| `458.sjeng` | 27 | 3.0238 | +0.26% | +0.01% | +0.19% | **+0.10%** | +0.06% | sp11 −0.4% / sp28 +0.7% |
| `462.libquantum` | 36 | 2.1645 | −0.01% | −0.02% | +0.18% | **−0.01%** | +0.06% | sp8 −1.3% / sp23 +1.0% |
| `464.h264ref` | 35 | 4.2253 | +0.12% | +0.48% | +0.61% | **+0.11%** | +0.10% | sp33 −0.4% / sp31 +0.6% |
| `471.omnetpp` | 25 | 0.9673 | +5.33% | +0.46% | +5.64% | **+5.88%** | +4.26% | sp30 −0.1% / sp0 +8.1% |
| `473.astar` | 26 | 1.2528 | +0.50% | −0.98% | −0.52% | **+0.47%** | +0.38% | sp10 −0.4% / sp13 +1.4% |
| `483.xalancbmk` | 34 | 2.0299 | +0.07% | +0.20% | +0.21% | **+1.49%** | +1.21% | sp20 −2.7% / sp35 +9.8% |
| **GEOMEAN (12)** | **386** | **13.49 /GHz** | **+1.04%** | **+0.09%** | **+1.07%** | **+1.03% (13.63 /GHz)** | **+0.74%** | **全量最差仅 −2.7%** |

  - 注：`SMS_T2_THR` 截表时完成 385/386（其余 4 组均 386/386 完成）。
- **验证**：
  - `comb_graph.py --check`：0 隐患（25 模块 48 阶段）；
  - 默认关 `run_gate_c.sh`：**68/68 PASS**（与 `main` 逐拍相等）；
  - `rv64gc` Linux 启动（`scripts/linux_check.sh`，`COMBO` 全开）：`rc=3 login=1 oops/panic=0`，成功到 `rv64 login:`。
- **结论与后续建议**：
  1. **强烈推荐优先落地 `LLC BOP + 节流版 SMS`（`SMS_T1_THR`）**：零后端/L1D 改动，在 12 个程序上 11 正 1 平（`omnetpp +5.88%`、`mcf +2.10%`、`xalancbmk +1.49%`、`gcc +1.20%`、`perlbench +0.87%`、`astar +0.47%`），全量 386 点最差单点仅 −2.7%。后续若将节流阈值 `LLC_SMS_TMIN` 从 `15%` 微调至 `8%~10%`，有望在保住 `omnetpp`/`xalancbmk` 零坏点的同时拿回 `mcf` 另一半增益（从 `+2.10%` 回到 `+3.5%+`，Geomean 冲至 `+1.15%~+1.20%`）。
  2. **不建议在当前阶段为 SPEC06 INT 强行做 L1 Breadcrumbs RTL**：在已有强硬件 Berti（含跨页 DTLB 翻译）+ LLC SMS 的体系下，L1 BC 在全量 386 点上净增益仅 `+0.09%`（与 SMS 叠加仅多 `+0.03 pp`），主要因 `mcf` 全量 45 点中部分随机树/高 MSHR 压力点（如 `sp44 −5.8%`）及 `astar`（`−0.98%`）被低命中率间接候选抵消；若未来扩展至图计算（GAP）/ 稀疏科学计算负载，再单独评估带独立 MSHR 预留与准确率反馈的 BC/DMP。
- **复现**：NFS 目录 `/nfs_global/S/houruyao/spec06_rv64gc/tm/`，二进制 `bin/sim64_bcsms_v4` / `bin/sim64_bcsms_v5`，结果目录 `res_bcsms_full_{llc_sms,l1_bc2,combo}`、`res_bcsms_v5_llc_sms_{thr,t2}`。
- **补充探索（2026-11-22 晚些时候）：Fill-side DMP 与 LLC Bingo（长短双事件回退）**：
  - **Fill-side DMP（`MemSubSystem/include/Dmp.h`，`sim64_dmp_bingo_v1`）**：在 L1D fill 时直接扫描 64B 行内 8 个 64-bit 字，用 16 项活跃数据段 VA 前缀过滤 + 128 项 `(PC, 8B-slot)` 置信度表 + 每 PC 准确率节流，复用 `g_pf_xq` 空闲 DTLB 端口翻译。59 点访存消融（53 交集点）：`gcc` 稳定受益 **`+0.82% ~ +0.95%`**（准确率 37.1%），但 `omnetpp`（准确率 16.7%，`−1.10% ~ −1.77%`）与 `xalancbmk`（准确率 10.7%，`−0.81% ~ −1.80%`）在 64 KB L1D / 16 MSHR 约束下净负，6 访存程序 Geomean **`−0.40% ~ −0.70%`**，与 Bingo 叠加反而拖低（`+1.16%` vs 纯 Bingo `+1.86%`），**不采用**。
  - **LLC Bingo（`MemSubSystem/include/Sms.h` `LLC_SMS_BINGO=1`，长事件 `(PC, offset)` + 短事件 `(PC, relative offset)` 双级回退 PHT）**：59 点访存消融中 `short_hit` 让 `astar`/`gcc`/`xalancbmk`/`omnetpp` 覆盖率大幅暴涨（`bingo_4k` 6 访存程序 Geomean **`+2.06%`**、`omnetpp +8.94%`；`bingo_t8` **`+1.95%`**）。**全量 SPEC06 INT 386 点（0 失败，vs EXP-052 `13.49 /GHz`）**：
    - **`BINGO_4K`**（4KB 整页 + `MAXDENSE=48` + `TMIN=10%`，385/386）：**12/12 全正、GEOMEAN `+1.34%`（`13.67 /GHz`）**——`omnetpp +8.81%`、`mcf +2.44%`、`perlbench +1.07%`、`astar +0.98%`、`xalancbmk +0.98%`、`gcc +0.95%`、`sjeng +0.57%`、`bzip2 +0.26%`、`h264ref +0.21%`、`gobmk +0.10%`、`libquantum +0.03%`、`hmmer +0.02%`。
    - **`BINGO_2K_T8`**（2KB 区域 + `MAXDENSE=28` + `TMIN=8%`，384/386）：**12/12 全正、GEOMEAN `+1.28%`（`13.66 /GHz`）**——`omnetpp +7.48%`、`mcf +2.79%`、`perlbench +1.19%`、`xalancbmk +1.11%`、`gcc +0.88%`、`sjeng +0.70%`、`astar +0.70%`、`bzip2 +0.28%`、`h264ref +0.28%`、`gobmk +0.17%`、`libquantum +0.04%`、`hmmer +0.01%`（仅 `gcc sp13 −25.9%` 为短事件回退唯一异常点，可对短事件单独提高置信门槛消除）。
    - 结果目录：`res_db_full_bingo_4k`、`res_db_full_bingo_2k_t8`、`res_db_*`。**最终推荐方案升级为 `LLC BOP + Bingo`（2KB/4KB 任选其一，零核内改动）**。
  - **最新 `main`（EXP-055 `16548ba`，`PRF=256 / ROB=256`，`14.24 /GHz`）上收口验证（分支 `exp/llc-bingo`，worktree `trace-model-llc-bingo`）**：剔除全部 BC/DMP/D5 代码，仅保留 `Berti + LLC BOP + Bingo 4KB`，并将 PHT 改为 RTL 友好的 **4 路组相联 SRAM**（长表 `256×4=1024`、短表 `128×4=512`、`FT=32`、`AGT=32`、`BOP_INF=8`、`Q=24`、`MAXDENSE=48`、`TMIN=10%`）。验证：`comb_graph.py --check` 0 隐患；`LLC_BINGO=1` 下 `rv64gc` Linux 启动 PASS（`rc=3 login=1 oops/panic=0`）；**全量 SPEC06 INT 386/386 点（0 失败，vs `main165_base_386` `14.24 /GHz`）**：加权 CPI **`+1.07%`（`14.39 /GHz`）**、加权 Geomean **`+0.96%`**（10 正 2 平 0 回退：`omnetpp +6.40%`、`mcf +2.28%`、`perlbench +0.96%`、`xalancbmk +0.91%`、`astar +0.71%`、`gcc +0.69%`、`sjeng +0.52%`、`bzip2 +0.22%`、`h264ref +0.16%`、`gobmk +0.13%`、`hmmer -0.00%`、`libquantum -0.01%`）。结果目录：`res_main165_{base,bingo4w}_386`。
  - **补充：`libquantum` 专项（LLC Streamer / BOP 跨页 / DTLB 下一页）**：85 点消融中 `DTLB_NP=1` 在 `libquantum` 持平（`-0.01%`，因 `BertiHw` 的 `g_pf_xq` 已触发真实 PTW）、`LLC Streamer`（同页 `-3.81%`，跨页 `dist=64` `+0.98%` 但压低 `omnetpp` `-2.1%`）；`LLC_BOP_XPAGE=1 + INF=12` 将 `libquantum` 提至 **`+1.42%`**（`sp43 +10.9%`）且 `omnetpp` 升至 **`+7.45%`**，但在全量 386 点上因跨非连续物理页拖累 `bzip2`（`+0.22% → -0.66%`，`sp23 -20.6%`）与 `gcc`（`+0.69% → -0.75%`），总分反略降至 `+1.02%`（`res_main165_bopxp_bingo_386`）。**结论：保持同页 `BOP + 4-way Bingo 4KB`（`+1.07%`，0 回退）作为 RTL 落地规格。**
  - **重大突破：统一 L2 TLB（1024 项 4 路 SRAM，2 拍）+ 16 项 Sv39 PWC（[L2Tlb.h](trace-model-llc-bingo/MemSubSystem/include/L2Tlb.h)，挂在 `MemPtwBlock` 中间，零 L1 关键路径改动）**：
    - 验证：`comb_graph.py --check` 0 隐患；`L2TLB_ENTRIES=1024 L2TLB_PWC=16 LLC_BINGO=1` 下 `rv64gc` Linux 启动 PASS（`rc=3 login=1 oops/panic=0`）；
    - **全量 SPEC06 INT 386/386 点（0 失败，vs 最新 `main` `16548ba` `14.24 /GHz`）**：
      - **单开 `L2TLB(1024×4) + PWC(16)`**：**12/12 全正、GEOMEAN `+3.46%`（`14.73 /GHz`）**——`mcf +15.85%`、`xalancbmk +10.17%`、`omnetpp +5.36%`、`astar +3.83%`、`bzip2 +2.24%`、`perlbench +2.20%`、`h264ref +0.72%`、`gcc +0.63%`、`sjeng +0.61%`、`gobmk +0.51%`、`hmmer +0.36%`、`libquantum +0.17%`。
      - **叠加 `LLC Bingo 4KB`（`main165_l2tlb1k_pwc_bingo_386`）**：**超线性叠加、12/12 全正、GEOMEAN `+4.64%`（`14.90 /GHz`，加权 GM `+4.22%`）**——`mcf +18.85%`（45/45 全正，单点最高 `+53.7%`）、`omnetpp +12.55%`（25/25 全正）、`xalancbmk +11.25%`（最高 `+35.9%`）、`astar +4.72%`（26/26 全正）、`perlbench +2.99%`、`bzip2 +2.48%`、`gcc +1.43%`、`sjeng +1.13%`、`h264ref +0.89%`、`gobmk +0.69%`、`hmmer +0.34%`、`libquantum +0.25%`。结果目录：`res_main165_l2tlb1k_pwc{,_bingo}_386`。
- **补充探索（2026-11-22）：补全机制版 Breadcrumbs（UFB + 扩容 + 冗余触发 + L1D Hit 观测，`sim64_bcfull_v1/v2`）**：
  - **补全内容（`MemSubSystem/include/Breadcrumbs.h` + `MemSubSystem/RealDcache.cpp`）**：① 每 relation 有用性反馈（`PF_BC_UFB=1`，128 项 track 环、16 样本窗口、低于 `PF_BC_UFB_MIN%` 自动静音且 `is_producer()` 屏蔽已静音项）；② 扩容表项（`PF_BC_NV=64` Value Table、`PF_BC_NREL=64` Relation Table、弱项优先替换防 `conf=3` 抖动、`PF_BC_TQ_W=6 PF_BC_TQ_N=32` 令 TQ drop 归零）；③ 完整冗余触发（`PF_BC_RES=2`：L1D 命中驻留行带 `expd_` 去重 + in-MSHR 命中保留 `line_meta_` 待 fill 展开）；④ 可选 `PF_BC_HITS=1`（L1D 普通命中也送 BC）与 `PF_BC_SMODE=3`（仅对活跃 producer 运行 BC 自适应步长，绝不替 Berti 给非 producer 发步长）。默认关 `comb_graph.py --check` 0 隐患、`run_gate_c.sh` 68/68 PASS。
  - **94 点定向消融（`bcfull_jobs.txt` = 全量 `429.mcf` 45 点 + `memgrp` 59 点，0 失败）**：
    - `PF_BC_HITS=1` 全线变差（普通 L1D 命中淹没步长/触发路径，`omnetpp +0.39% → +0.02%`、`mcf -0.41% → -0.62%`）；
    - `NV=64 / NREL=64 / TQ=6x32 + RES=2` 显著提升真指针追逐负载（`xalancbmk` 59 点从 `+0.56% → +1.00%`，`mcf sp4` 达 `+12.82%`），但只要 `smode=0` 仍允许 BC 给非 producer 发步长，`mcf sp44/10/54` 仍暴跌 `-6.07% / -3.92% / -3.86%`（根因：`stride_cand` 达 1.6M）；
    - 切至 **`bc2_pure_ind`（`PF_BC=1` 纯间接 + Berti 步长）** 或 **`bc2_prod_s3`（`PF_BC=2 PF_BC_SMODE=3` 仅 producer 步长）** + `UFB=20% + RES=2 + NV64/NREL64` 后，`mcf` 坏点全部翻正（`sp44 -6.07% → +0.22%`、`sp10 -3.92% → +0.46%`、`sp54 -3.86% → +0.12%`），全量 45 点 `mcf` 加权 CPI 从 **`-0.41%` 翻正至 `+0.36%`**（34/3 正负，最差点仅 `-0.34%`）；但同时证实原 `sp4 +12.8%` 中约 90% 来自 BC 激进步长而非间接预取本身（纯间接在 `sp4` 准确率 87% 下仅 `+1.17%`）。
  - **全量 SPEC06 INT 386/386 点验证（0 失败，vs EXP-052 `res_me2_386`）**：
    - `bcfull_s3_386`（单开补全版 BC）：`483.xalancbmk` 提升至 **`+0.98%`**（加权 CPI；最优单点 `+5.17%`）、`429.mcf +0.34%`、`473.astar +0.03%`（彻底消除简化版 `-1.38%` 回退），12 程序总分近持平（`gcc sp43/13` 个别短点时序抖动）。
    - **`bcfull_s3_bingo_386`（补全版 BC + `BINGO_4K`）**：**386/386 叠加 `BINGO_4K` 额外净增 `+0.17% ~ +0.23%`**（加权 CPI GM **`+1.67%` vs `BINGO_4K +1.44%`**，预估 **`13.72 /GHz`**；加权 Geomean **`+1.38%` vs `+1.21%`**），几乎全部来自 **`483.xalancbmk`（`+0.85% → +2.54%`，净增 `+1.68%`；加权 Geomean `+0.63% → +1.61%`）** 以及 `omnetpp`（`+8.62% → +8.99%`）、`gcc`（`+1.91% → +2.22%`）、`bzip2`（`+0.15% → +0.42%`）、`mcf` **43/0 零负点**。
    - **结论**：补全冗余触发 + UFB + 大表 + producer-only 步长确实让 BC 变得干净且能正向叠加在 `BINGO_4K` 上（尤其 `xalancbmk` 受益显著），但在 SPEC06 INT 全量上增量仅 `+0.17% ~ +0.23%`，ROI 仍远不如单做 `LLC BOP + Bingo`（`+1.34%`，零核内改动）。结果目录：`res_bcfull_*`、`res_bc2_*`。
- **补充探索（2026-11-22）：移植 `gem5gs` `D5` 统一预取器并移除 `BertiHw`（`MemSubSystem/include/BreadcrumbsD5.h`，`sim64_d5_v1..v4`）**：
  - **实现**：按 `D5` 规格完整移植解耦 Rename Tag 引擎（单链 `chainIdx=1`、每 100k 周期清零）+ LDT 循环边界（拦截 RV64 `BR` 比较寄存器 `rs1/rs2`、`bound_index` + `contig` 连续性豁免）+ `uni[32]` 无偏 per-PC/per-Relation MSHR 延迟与 Tag-Seeded 重入 + 融合 Timely Local-Delta（`BC_LD=1`，`MSHR < 70%` 限流）+ 步长网格展开 + 冗余触发 `RES=2` + `l2_far` 经 `g_llc_inject_q` 直注 `AXI_LLC` 与 `l2_fill_trigger=2`，**默认关闭 `BertiHw`**（`PF_BC_D5=1`，默认关 `gate_c` 68/68 PASS）。
  - **4 轮迭代定位的 5 个关键 RV64 / AI-Huma 架构适配点**：
    1. RV64 无 x86 访存寻址融合，`has_rule` 指令密度达 x86 的 2×–2.5×，8 宽核上 `NTQ=8, 3/cyc` 丢弃率高达 55%（`libquantum drop=5.07M`），扩至 `TQ_W=8, TQ_N=32` 后 `drop` 归零、`mcf sp56` 从 `-59.6%` 飙回 `-5.97%`；
    2. `l2_far` 必须经 `g_llc_inject_q` 直注 `AXI_LLC`（不能走 L1D 探针口/MSHR，否则把 `mcf sp4` 从 `+22.9%` 打成 `-3.5%`）；
    3. `handle_aff_access` 不能在 `!newline` 时丢弃 `pf_hit`（乱序先命中行内非 0 偏移），`ld_update` 遇自身 `h.va_line == vline` 须 `continue` 而非 `break`；
    4. AI-Huma 无私有 L2，`BC_LD` 恢复 `rpl == 2`（35%–65% 置信度）直注 `AXI_LLC` 后，`gcc sp47` 从 `-19.5%` 追至 `-3.6%`、`omnetpp` 飙升至 `+8.33%`；
    5. `pop_phys_cand` 在 `mshr_occ >= 15` 时反压保序（消除 `no-mshr = 29k` 破坏 `NOOVL` 导致的 `libquantum` 16 行周期性冷 miss），`libquantum` 从 `-14%` 追至 `-1.85%`。
  - **全量 SPEC06 INT 386/386 点验证（0 失败，vs EXP-052 `BertiHw + BOP` `13.49 /GHz`）**：
    - **`d5v4_386`（纯 `D5` 替换 `BertiHw`，`LDHW=32, LDTAB=32, FAR=2, L2FT=2, MAXLA=24`，无 Bingo）**：**全量 386 点反超 `BertiHw + BOP`**——加权 CPI **`+0.16%`（`13.51 /GHz`）**、加权 Geomean **`+0.39%`（`13.54 /GHz`）**；大胜项：`471.omnetpp +6.44%`、`464.h264ref +1.19%`、`401.bzip2 +0.56%`（`mcf sp4 +28.5%`）；小负项：`libquantum -1.85%`、`astar -1.55%`、`xalancbmk -1.54%`、`gcc -1.05%`（加权 GM `+0.11%`）。
    - **`d5v4_bingo_386`（`D5` 替换 `BertiHw` + `BINGO_4K`）**：加权 CPI **`+1.16%`（`13.65 /GHz`）**、加权 Geomean **`+1.18%`**；其中 **`471.omnetpp` 创纪录达 `+11.97%`**、`464.h264ref +1.27%`、`401.bzip2 +0.75%`，但因 `libquantum -2.11%` / `astar -1.33%` 略低于 `BertiHw + BINGO_4K`（`+1.34%` / `13.67 /GHz`）与 `BertiHw + Full BC(s3) + BINGO_4K`（`+1.56%` / `13.70 /GHz`）。
    - **结论**：`D5` 证明了**无需独立 `BertiHw`** 即可在全量 SPEC06 INT 上超越原 `BertiHw + BOP`（尤其在 `omnetpp`/`h264ref`/`bzip2` 极强）；若追求 SPEC06 INT 最高性价比与零核内 RTL 改动，首选仍为 **`BertiHw + LLC BOP + Bingo 4KB`（`+1.34%`, 12/12 全正）**；若后续兼顾图计算（GAP）/ 稀疏科学计算并希望精简 L1D 预取器为单一统一架构，则 `D5` 极具价值。结果目录：`res_d5_*`、`res_d5v2_*`、`res_d5v3_*`、`res_d5v4_*`。

---

## EXP-053 前端结构清理与去补丁重构 + 复用 `ttg_pick_k` 与双路径加速

- **日期 / 分支**：2026-11-22；`trace-model` `exp/fe-cleanup`（合入 `4d4534f`）、`rtl` `rtl/fe-cleanup`（合入 `28840c8`）。**状态**：**已合入 `main` 并推送**。
- **背景**：EXP-051 合入 `2-taken + 2-Ahead B + 4-Bank ICache + FDIP` 后，`front_top` 面积达 1.58M / 356 层、`bpu` 504k / 272 层、`icache` 917k / 106 层，且留有三处临时补丁（跨子系统 `fdip_snoop` 旁路、`resp_popped_q` AXI 回波挡板、`inst -> diag_val[1]` 搭便车传跨页 RVC 缺页偏移）与全链路死线 `tage_idx/tage_tag`。
- **方案（两阶段清理 + 复用 `main` 公共原语）**：
  1. **Phase 1（零周期结构重构）**：`icache_arr.sv` 显式拆为真 4-Bank 1R1W + 并行 SRRIP；`bpu_types_pkg.sv`/`bpu_eval.sv` 并行 `ftb_eval_ent`（加固奇地址向上取整与 64 位回绕）；`bpu_hist_vec.sv` 零取模并行移位；`bpu_spec.sv` 切断 `r1_q → ovr_a → spec_a → g0_b` 假路径；`inst_fifo` 改为紧凑原始半字、单份展开预译码与 4 轮 Kogge-Stone 起点扫描统一落在 `front_head_fix.sv`；全链路删除死线 `tage_idx`/`tage_tag`。
  2. **复用 `rtl/common` 公共原语与双路径**：`front_pd_info.sv` 用 `ttg_pick_k #(.N(FETCH_WIDTH), .K(2))` 替代两级 `ttg_first_set` + 前缀或；`front_head_fix.sv` 与 `bpu_hist_vec.sv` 按 `rtl/common/ttg_*.sv` 统一风格补齐 `` `ifdef SYNTHESIS ``（综合走并行树/桶形移位，仿真走快速行为路径，`fe_clean_eq_tb` 仿真提速 **3.6×**）。
  3. **Phase 2（微架构去补丁）**：P2-1 删除 `dcache`/`wb`/`mem_top` 上跨子系统 `fdip_snoop_dirty`/`fdip_snoop_line`，改为 `icache_fdip` 发射前经既有 `dc_req`/`dc_resp` 做 1 拍 DCache/WB/MSHR/fill 探针；在 `axi_cpu_port_chan` 通道 0 增加 `CLEAR_ON_POP=1`（对应 `SimCpu.cpp`）根治 AXI 响应回波并删除 `resp_popped_q`；`icache_top.cpp` 补齐 32 KiB L1I 数据阵与 `Blocked::StaleIcache`。P2-2 用显式 1-bit `pf_inst_hi` 贯通前端到 `rob_trap_ctrl` 替代 `inst->diag_val[1]` 搭便车。
  4. **顺带修复既有模型缺陷**：`LsuPipeTranslate.cpp` 命中 STLF 候选（`c.v == true`）时不写 `cam_ok`，消除 `RC_DATA` 等待 SDU 期间错误缓存 oracle `m.rs2` 导致的 Linux `s01`/`s09` 分叉。
- **综合对比（`eda-04..06`，`SYNTH_LIGHT=1 SYNTH_MEM=1 SYNTH_LTP=1 SYNTH_NO_MEMPRIO=1 strash;balance;map`）**：
  - `front_top`：`1,582,763 / 356` → **`1,159,189 (−26.8%) / 216 层 (−39.3%)`**
  - `bpu`：`504,078 / 272` → **`410,093 (−18.6%) / 197 层 (−27.6%)`**
  - `icache`：`916,659 / 106` → **`389,270 (−57.5%) / 114 层`**
  - `pre_idu_queue`：`137,578 / 38` → **`131,433 (−4.5%) / 38 层`**
  - `axi_cpu_port_adapter` `222→227 / 9`、`rob` `466,029→466,653 / 64`、`dcache_bank` `142,429 / 12`、`dcache_s2_ld` `5,097 / 37`、`dcache_wb` `23,334 / 49`。
- **验证**：
  - 性能（全量 SPEC06 INT 386/386 点，0 失败）：合并前 vs EXP-051 为 **+0.020%**；合并后最新 `main`（`4d4534f`，`res_exp053_main_386`）实测 **`13.48 分/GHz`**（vs EXP-052 `13.49 /GHz` **`−0.05%`**、vs EXP-051 `13.42 /GHz` **`+0.50%`**；`gobmk +0.28%`、`sjeng +0.14%`，仅双稳态点 `403.gcc sp13 −25.8%` 拖累 `gcc −0.45%`，其余 384/386 点全在 ±2% 内）；
  - 变基至最新 `main`（`4d4534f` + `28840c8`，含 EXP-052 + `de5fdb9`）后全套复验：`comb_graph.py --check` 0 违例、`run_gate` 62/62 + `PF_ENABLE=0` 62/62 + `run_gate_c` 68/68、`linux_check.sh` 到 `rv64 login:`（0 oops/panic）；RTL `gen_cfg.sh` 171 常量 0 差异、`lint_chip` 0、`common_prims` 100k PASS、`ren_elim_sel` 100k PASS、`fe_clean_eq_tb` 双路径（`SIM` 0.038s / `SYNTHESIS` 0.138s）0 错、`fm_gate.sh` **68/68 PASS 0 周期偏差**；Linux 27 窗（`eda-05..10` `out_exp053_main`，合计 **137,700,065 条指令**）**0 FM 不一致、`s01..s26` 26/26 PASS、27/27 段 `150,175` PT / `150,175` UP bins 100% 全等**（原 EXP-052 `s17` 4 拍差异同步归零）。

## EXP-052 RV64GC `c.mv` 规范化与组内 1-hop 关键链移动消除 + `ren` 降深度

- **日期 / 分支**：2026-11-21；`trace-model` `exp/move-elim-eval`、`rtl` `rtl/move-elim-1hop`
- **背景与根因**：分析 `ren` 99 层逻辑深度时发现 `ren_elim_sel` 占 ~43 层，但现 `main` 在 SPEC06（rv64gc）上 `MOVE_ELIMINATED = 0.00%`。根因：RV64GC 编译器把寄存器拷贝编为 16-bit `c.mv rd, rs2`，前端 `rvc_expand` 按规范展开为 `add rd, x0, rs2`，而 `is_move_shape()` 只匹配 `addi rd, rs1, 0`，导致整个 `MOVE_ELIM` 在 RV64GC 上几乎是死代码。
- **方案**：
  1. **IDU `c.mv` 规范化**（`Idu.cpp` / `idu_decoder.sv`）：将 `add rd, x0, rs2`（含全部展开后的 `c.mv`）规范化为语义等价的 `addi rd, rs2, 0`（`src1_areg = rs2, src2_en = 0, src2_is_imm = 1, imm = 0`），不改 `function-model`；同时在 `MsData.h` 污点求值器中同步该规范化（否则未被消除且带投机污点的 `c.mv` 会误用原始指令字算 `stale_rs2 + true_rs2`）。
  2. **组内 1-hop 关键链消除**（`Ren.cpp` / `ren_elim_sel.sv` / `ren_dep_check.sv`）：当 `src1_areg` 被同组更老的有效整数指令 `j` 写时，若最近老写者 `j` 未被消除（分配全新物理寄存器，RAT 原引用数为 0）且 `(i - j) < MOVE_ELIM_MAX_REFS`（8 宽下仅拦截 `j=0, i=7`，保证 3-bit `arch_cnt` 永不溢出），则允许消除，目的寄存器取旁路后的 `src1_preg`。
  3. **RTL 深度优化**：`ren_elim_sel` 将 1-hop 旁路链拆成仅依赖 `areg` 比较的并行根分解（`is_const / const_val / inv / root_oh`），与 33 路 `spec_rat` `ttg_popcount` 并行；`ren_core` / `ren_fp` 的分支 `head_after` 改用 `alloc_req` 前缀，并由 `ren_free_list` / `ren_fp_free_list` 按 `fire` 末位直接选通 `head_next`（移除握手后的 `popcount + 加法`）。
- **四档消融（48 个 SPEC06 高权重点，修完 `c.mv` 后）**：
  - `m0`（关）→ `m1`（仅 `spec_rat`）：Geomean **+0.18%**（消除率 4%~11%）
  - `m2`（+ 组内 1-hop）：Geomean **+0.51%**（吃掉理想无限制上限 `m3` `+0.60%` 的 ~85%）
- **全量 SPEC06 INT（386/386 点，0 失败，对比 `main` 基线 `res_fe2f_final_386`）**：
  - 12 程序全部正收益、零回退，**Geomean +0.55%**：`400.perlbench +0.01%`、`401.bzip2 +0.39%`、`403.gcc +0.30%`、`429.mcf +0.43%`、`445.gobmk +0.68%`、`456.hmmer +0.14%`、`458.sjeng +0.79%`、`462.libquantum +0.04%`、`464.h264ref +0.74%`、`471.omnetpp +1.22%`、`473.astar +0.31%`、`483.xalancbmk +1.62%`。`coremark +0.99%`（`233,223 → 230,923`）。
- **RTL 综合与验证**：
  - Yosys（`eda-08`，`SYNTH_ABC="strash;balance;map"`）：`ren` **99 → 97 层**（`474,699 → 475,533` cells，+0.18%），`idu` 66 层（`31,607` cells）；
  - `tests/ren_elim_sel/run.sh`：100,000 组随机输入 0 不一致；
  - `lint_chip.sh`：0 警告；`fm_gate.sh`：**68/68 PASS，0 FM 不一致，0 周期偏差**；
  - rv64gc Linux 27 窗回归（`eda-06`~`eda-09`，`out_me2_t4`）：**27/27 全部跑完，共核对 `137,700,067` 条指令，0 FM 不一致**；**26/27 窗口 PT/UP 指纹 100% 相等**。唯一差异 `s17` 已定位清楚：前 `3,639,100` 拍（479.7 万指令）`SLOT_FIRE` / `INSTRET` / `PT` / `UP` 逐拍 100% 相等（且改写 `head_after`/`head_next` 前后的 RTL 表现完全一致，排除了 RTL 改动 bug）；第 `3,639,115` 拍存在一条错误路径 load（`pc=80007d62`，第 `3,639,122` 拍被误预测冲刷），trace 模型与 RTL 在错误路径访存地址上的固有模型差异使随后第 `3,639,125` 拍的 ICache miss 在 LLC/AXI 竞争中早返回 4 拍（`3,639,154` vs `3,639,158`），与本次微架构改动正确性无关。

## EXP-051 前端 2-fetch / 2-taken + 真 AXI FDIP（里程碑 B 模型探索）

- **日期**：2026-11-21。**分支**：trace-model `exp/fe-2fetch-2taken`（DSE 工作区 `trace-model-fe2f`）→ `merge/fe-2fetch-2taken`（`5b67500`）；rtl `rtl/fe-2fetch-2taken`（`3fa98cd`）。**状态**：**已合入 `main`（2026-11-21：trace-model `5b67500`、rtl `3fa98cd`，均已推送 `origin/main`）**。
- **问题**：EXP-050（里程碑 A，1-Ahead 块级 FTB）将 `FE.bw` 从 `31.23%` 降至 `22.77%`（`12.11 → 13.14 分/GHz`）后，剩余 `22.77%` 前端带宽损失中约一半来自 **taken 分支截断取指组**（`FEO_LOSS_TAKEN = 5.95` 槽/拍），另一部分来自 **64B cache line 跨行截断**与 **I-Cache 缺失**（`ICACHE_MISS = 2.16M`）。本轮在严格硬件可实现（无双口 ICache SRAM、零 S0 串行 SRAM、真 AXI/LLC/DRAM 竞争）约束下，系统探索里程碑 B 的帕累托最优解。
- **方案与实验开关（全部默认 `0`，零环境变量下与 `main ef61350` 逐拍一致）**：
  - `FE_2TAKEN`（`0`=关；`1`=1-Ahead A + uFTB B，零新增 2-Ahead SRAM；`2`=1-Ahead A + **2-Ahead B**，提前 1 拍用同一 `(key_base, key_fh)` 并行读 `aftb2/atage2/aitt2`，**S0 零串行 SRAM**；`3`=1-Ahead(pcA) B；`4`=Oracle B 上界）；
  - `FE_2TAKEN_NT`（`0`=截断 B；`1`=**严格不截断**：仅当 `gB.taken || full_bnd_b <= max_b_end` 时配对，杜绝非规范块起点污染 FTB/TAGE；`2/3/4`=32B/16B/64B 对齐截断）；`FE_2TAKEN_FT`（`0`=仅 taken A 配对；`1/2`=短 fall-through A 与次行融合）；`FE_2TAKEN_AHSZ`（2-Ahead B 容量：`0`=`2K/1K`，`1`=**半容量 `1K/512`**，`2`=`4K/2K`，`3`=`512/256`）；
  - `FE_XLINE`（`0`=关；`1`=Even/Odd 跨 64B 行取指；`2`=+miss 自动预取；`3`=仅 `off>=48` 规范跨行）；
  - `FE_FDIP`（真 AXI/LLC/DRAM 预取，复用 `MASTER_ICACHE` txid `8..11` 与需求取指严格仲裁：`1`=S0 入队；`2`=+next-line；`3`=**S2 确认 2 槽干净 FDIP** + `refetch||ovr` 清队列 + `pair_ic_fail` 自动预取；`4`=仅跨行/配对 miss 触发）；
  - `FE_IC_BANKS`（`0`=双口对照；`2`=2-Bank Even/Odd；`4`=**4-Bank 1R1W** 按 64B cache line 低 2 位分体）、`FE_IC_ITLB2`（`0`=单口 ITLB 同 4KB 页；`1`=**2 读口 ITLB** 32 项 FA CAM + 单 PTW walker）、`FE_BRQ_W`（`1`/`2` 分支/拍提交训练队列出队）、`FE_HR1K`（`HistRing` 256b → **1024b**，2-taken 开启时自动启用）。
- **关键微架构根因与发现（4 项必须保留至 RTL）**：
  1. **S2 确认后再做 A/B 通道复选（`alt_a` 机制）**：若在 `InstPort::comb_write` 阶段就用 B 覆写 A 的尾槽，一旦 S2 将 A 从 taken 覆写为 not-taken，A 被提前截断会诱发级联 `predecode_flush`，导致 `ovrA` 暴涨 8×、`FEO_LOSS_REFETCH` 暴涨 6×。保留完整 A 数据至 S2 确认（`is_pair`）后选通，彻底消除额外冲刷。
  2. **`HistRing` 256 位环回覆盖修复（256b → 1024b，单点 +22% 反转）**：`2-taken` 下单拍可推 4 位 GHR，~90 个在飞块累计 ~360 位 + `K.ghr[3]=128` 位 = 488 位 > 256 位，错误路径写入绕环覆盖已提交历史位，致使 `458.sjeng` 恢复失配 `mm0=15.89%`、`mm_any=64.77%`、`IPC −16.0%`。扩宽至 1024 位（RTL 512 位即数学充足，1024 位留 2× 裕量）后 `mm0 → 0.00%`、`mm_any → 0.01%`，`458.sjeng` 由 `−16.0%` 翻转为 **`+5.43%`**。
  3. **不截断（`NT=1`）严格支配截断 / `FE_XLINE` / `FT=1`**：任何截断或 `FE_XLINE`/`FT=1` 都会引入非规范块起点造成 FTB/TAGE/1-Ahead 相位分裂；在 `fe24` 消融集上，纯 `2T2 + NT1 + FDIP=3`（**+3.44%**）直接达到 Oracle B 上界（**+3.50%**）的 **98.3%**，高于叠加 `XL3`（+3.10%）或 `FT1`（+2.74%）。
  4. **RVC `carried` 块 `nb_base` 修复（挽回 `456.hmmer` +16%）**：`front_top.cpp` 上报虚假分支清除基址时若取 `fifo_head.pc[0]`，在 RVC 跨块 `carried` 块上该值被 `rvc_head_fix` 改写为 `base - 2`（如 `0x18e1e` 而非 `0x18e20`），导致 `clear_false_branch` 永远清不掉真实块内的虚假分支并反复触发 4 万+ 次 `predecode_flush`（`456.hmmer` 跌 −14%）。改用 `grp_ptab.predict_base_pc`（单块模式 `nb_base=0` 直接用 `pd_rec.base`）后彻底消除，`456.hmmer` 回升 +16%、全量最差点由 `−16.2%` 收敛至 **`−2.6%`**。
  5. **放弃方案**：`FTQ32`（`PTAB_SIZE=32`）在重 FDIP 下出现 4–6/24 `ROB deadlock` 且 16 项已达 Oracle 上界 98.3%，不采用；`FDIP=1/2`（S0 激进预取 + next-line）拥塞 AXI/LLC 导致负收益（`−0.04%` / `−0.45%`），被 S2 确认 2 槽 `FDIP=3` 严格取代。

- **阶段 1：`fe24` 前端敏感 24 点消融与硬件帕累托扫描（24/24 完成，0 失败，相对 EXP-050 `main` `ah1_4k_a2k1k`）**：

| 轮次 / 配置名 | 关键配置 | `fe24` 几何平均 IPC | 最差点 / 最优点 | 关键结论 |
|---|---|---:|---:|---|
| R3 `r3_hr1k` | 仅 `HR1K + BRQ2` | −0.10% | −0.7% / +0.2% | 单独无额外收益，作为 2-taken 基础设施 |
| R3 `r3_fd3` | 仅 `FDIP=3`（S2 确认 2 槽真 AXI） | +0.11% | −0.5% / +1.0% | 修复 `FDIP=1/2`（−0.04%/−0.45%）拥塞回退 |
| R3 `r3_xl3` / `xl1` | 仅跨行取指 `XL3` / `XL1` | +1.02% / +1.12% | −0.4% / +5.1% | 单独有效，但与 `2-taken` 叠加反而低于纯 `NT=1` |
| R3 `r3_2t1_nt1` | `uFTB B`（零 2-Ah SRAM）+ `NT1 + BRQ2` | +2.99% | −0.6% / +43.9% | `ovrB` 高（4410k），但已拿回大部分增益 |
| R3 `r3_2t2_nt0` / `nt2` | `2-Ah B` + 截断 / 32B 对齐 | +2.77% / +3.07% | −1.2% / +44.0% | 均弱于 `NT1`（非规范起点相位分裂） |
| R3 `r3_2t2_nt1` | `2-Ah B (2K/1K) + NT1 + BRQ2` | **+3.28%** | −0.7% / +44.1% | `ovrB` 较 `uFTB B` 暴降 5×（4410k→870k） |
| R3 `r3_2t4_nt1` | `Oracle B + NT1`（理论天花板） | +3.64% | −0.6% / +44.6% | 2-Ah B 无 FDIP 时已达上界 90% |
| R3 `r3_2t2_xl3_fd3` | `2-Ah B + XL3 + FD3` | +3.10% | −0.4% / +43.7% | `XL3` 改变 `block_bnd(pcB)` 降低 `NT1` 配对率 |
| R4 `r4_2t2_ft1_fd3` / `ft2` | `2-Ah B + FT1/FT2 + FD3` | +2.74% / +2.53% | −1.8% / +41.2% | fall-through 融合反而增加相位碎片 |
| R4 `r4_2t2_nt1_fd3` | **`2-Ah 2K/1K + NT1 + FD3`（双口, ITLB2）** | **+3.44%** | −1.3% / +43.5% | **达 Oracle+FD3 上界（+3.50%）的 98.3%**；`perlbench +9.81%` |
| R5 `r5_2t4_nt1_fd3` | `Oracle B + NT1 + FD3`（双口, ITLB2） | +3.50% | −1.1% / +43.9% | 里程碑 B 2-taken 理论天花板 |
| R5 `r5_nt1_fd3_dp_it1` | `2-Ah 2K/1K`（双口, **1 口 ITLB**） | +3.20% | −0.9% / +43.5% | 2 读口 ITLB 单独贡献 **+0.24%** |
| R5 `r5_nt1_fd3_b2_it1` | `2-Ah 2K/1K`（**2-Bank**, 1 口 ITLB） | +2.75% | −0.9% / +35.8% | 2-Bank 冲突损失 −0.45%，偏大 |
| R5 `r5_nt1_fd3_b4_it1` | `2-Ah 2K/1K`（**4-Bank 1R1W**, 1 口 ITLB） | +3.10% | −0.8% / +43.5% | **4-Bank 相对双口仅损 0.10%** |
| R5 `r5_nt1_fd3_b4_it1_ah1k` | **`2-Ah 1K/512`（4-Bank 1R1W, 1 口 ITLB）** | **+3.05%** | **−0.5%** / +43.5% | **2-Ahead SRAM 减半仅损 0.05%**（`512/256` 掉到 +2.88%） |
| R5 `r5_2t1_nt1_fd3_it1` | `uFTB B`（零 2-Ah SRAM, 双口, 1 口 ITLB） | +2.75% | −0.7% / +43.3% | 零新增 BPU SRAM 基线 |

- **阶段 2：全量 SPEC06 INT 386 点验证（`sim64_fe2f_v4`，386/386 完成、0 失败，SimPoint 加权 CPI，对照 EXP-050 `main` `ah1_4k_a2k1k` `13.14 分/GHz`）**：

| Benchmark | Pts | EXP-050 `main` CPI | 轻量档 `2t1_b4_it2`（零 2-Ah SRAM） | **帕累托冠军 `b4_it2_ah1k`**（4-Bank + ITLB2 + `1K/512`） | 天花板对照 `2t2_dp_it2`（双口 + `2K/1K`） |
|---|---:|---:|---:|---:|---:|
| `400.perlbench` | 24 | 0.299 | +6.47% | **+6.53%** | +6.71% |
| `401.bzip2` | 48 | 0.398 | +1.68% | **+1.57%** | +1.60% |
| `403.gcc` | 34 | 0.570 | +6.02% | **+6.20%** | +6.48% |
| `429.mcf` | 45 | 2.513 | +0.23% | **+0.22%** | +0.27% |
| `445.gobmk` | 29 | 0.403 | +4.08% | **+4.96%** | +5.31% |
| `456.hmmer` | 23 | 0.163 | −1.44% | **−1.41%** | −1.36% |
| `458.sjeng` | 27 | 0.351 | +4.09% | **+5.43%** | +5.63% |
| `462.libquantum` | 36 | 0.466 | +0.80% | **+0.77%** | +0.80% |
| `464.h264ref` | 35 | 0.243 | +1.37% | **+1.91%** | +1.86% |
| `471.omnetpp` | 25 | 1.046 | −0.25% | **−0.20%** | +0.01% |
| `473.astar` | 26 | 0.812 | +1.21% | **+1.45%** | +1.54% |
| `483.xalancbmk` | 34 | 0.501 | +0.29% | **+0.54%** | +0.87% |
| **12 程序几何平均（vs EXP-050 `main`）** | **386** | **13.14 /GHz** | **+2.02% (13.41 /GHz)** | **+2.30% (13.44 /GHz)** | **+2.44% (13.46 /GHz)** |
| **相对 EXP-050 前 `main`（`12.11 /GHz`）** | **386** | +8.40% | +10.59% | **+10.90%** | +11.05% |
| 最差点 / 最优点（vs EXP-050） | 386 | — | −2.6% / +76.7% | **−2.6% / +76.5%** | −2.0% / +76.6% |

- **全量 386 点 TMA 与微架构统计变化（`b4_it2_ah1k` vs EXP-050 `main`）**：
  - `Retiring`：**`30.92% → 31.62% (+0.70 pp)`**；`Frontend Bound`：**`24.57% → 20.27% (−4.30 pp)`**；`FE.bw`：**`22.77% → 18.63% (−4.15 pp)`**（`perlbench −9.22 pp`、`sjeng −7.19 pp`、`gcc −6.13 pp`、`gobmk −5.70 pp`、`astar −5.31 pp`）；`FE.lat`：**`1.79% → 1.64% (−0.15 pp)`**（`perlbench −0.98 pp`、`gobmk −0.58 pp`）；
  - `ICACHE_MISS`：**`2.16M → 1.45M (−32.9%)`**（真 AXI `FDIP=3` 显著消减指令缺失）；`FEO_LOSS_TAKEN`：**`5.95 → 4.08` 槽/拍（−31.4%）**；
  - `paired = 26.63%`，4-Bank 冲突拒配仅 `10.83%`，半容量 `1K/512` 2-Ahead B 命中率 **`78.73%`**，将 `ovrB` 相对 `uFTB B` 压低 **7.1×**（`82.18M → 11.65M`）；
  - 唯一小幅负向程序 `456.hmmer`（`−1.41%`，`IPC 6.02 → 5.94`）原因是 8 宽后端已接近饱和（`Retiring 74.3%`），双块取指在错路径推入更多推测指令引发 `memspec_vio` 与重命名 `NOPREG` 略增（`BadSp +1.01 pp`），属于典型高 IPC 后端饱和效应，所有 23 点最差仅 `−2.6%`。
- **小负载标杆（`rtl/programs/big/`）**：
  - `coremark.bin`：`275,332 (2.295)` → `233,078`（`2t1_b4_it2`, −15.35%）/ **`229,707 (2.751)`（`b4_it2_ah1k`, −16.57% 周期 / +19.86% IPC）** / `229,589`（`2t2_dp_it2`, −16.61%）；
  - `dhrystone.bin`：`102,229 (2.527)` → `95,445`（`2t1_b4_it2`, −6.64%）/ **`95,328 (2.710)`（`b4_it2_ah1k`, −6.75% 周期 / +7.24% IPC）** / `97,232`（`2t2_dp_it2`, −4.89%）。
- **验证**：
  - `comb_graph.py --check`：**0 read-before-later-write hazards**；
  - 零环境变量 `run_gate_c.sh`：**68/68 PASS（0 失败，与 `main ef61350` 逐拍相等）**；
  - `b4_it2_ah1k` 配置 `run_gate_c.sh`：**68/68 PASS（0 失败，全量 difftest 通过）**；
  - `rv64gc` Linux 5.15.170（`~/rv64spec/linux_j.bin`）：`b4_it2_ah1k` 与 `2t2_dp_it1` 均在 ~80M 周期顺利到达 `rv64 login:`，0 oops/panic。
- **结论与 RTL 落地摘要（2026-11-21 合入 `main`）**：
  - 采纳帕累托冠军 **`fe2f_b4_it2_ah1k`**，并在 RTL 落地时完成硬件化收敛：FDIP VA 队列改为 `1-pop/cycle` 无组合环硬件出队、加入 `issued` 响应门控与 `resp_popped_q` 防重复弹栈、加入周期初 L1D/WB 脏行嗅探避免 FDIP 缓存未刷回的旧代码行、BPU 采用 `BRQ_W=1` 与内部 `rec_q[256]` 消除 168 位 `bpu_ck` 跨 FTQ/PTAB 透传、`pre_idu_ftq_bpu` 贯通 4 位 `ftq_offset` 直接索引（删除 16×64 位 PC 扫描）、顺手修复 RVC 跨 4KB 页 32 位指令第二半字取指缺页 `stval = pc + 2` 架构缺陷（`front_head_fix` + `rob_trap_ctrl` / `front_top.cpp` + `Rob.cpp`），并删去旧 `FE_PAIR` / `FE_IPF` / `FE_IPF_LAT` 实验开关。
  - **最终合入版全量 SPEC06 INT 386/386 点**（`sim64_fe2f_final`，`/nfs_global/S/houruyao/spec06_rv64gc/tm/res_fe2f_final_386`）：相对 EXP-050 `main`（`13.14 分/GHz`）几何平均 **+2.18%（`13.42 分/GHz`）**，相对 EXP-048 累计 **+10.76%**（12/12 全正）；`perlbench +6.08%`、`gcc +6.06%`、`sjeng +5.17%`、`gobmk +4.68%`、`h264ref +1.85%`、`bzip2 +1.57%`、`astar +1.44%`、`libquantum +0.77%`、`mcf +0.18%`、`xalancbmk +0.11%`、`omnetpp −0.00%`、`hmmer −1.42%`；TMA `Retiring 30.92% → 31.58% (+0.66 pp)`、`FE 24.57% → 20.31% (−4.26 pp)`、`FE.bw 22.77% → 18.60% (−4.18 pp)`、`FE.lat 1.79% → 1.71% (−0.08 pp)`；固定大程序 `dhrystone 96,351 (2.68, −5.75%)`、`coremark 231,913 (2.72, −15.77%)`、`memory-stress-small 326,797 (3.21, −4.89%)`。
  - **RTL 验证与 Yosys 综合**：`make cfg` 同步（171 常量）、`lint_chip.sh` 0 警告/0 错误、`fm_gate.sh` **68/68 PASS（含新增 `directed/fe_2taken_fdip.bin`，0 FM 不一致，0 周期偏差）**；`eda` rv64gc Linux 27 段检查点（`s01..s26` **26/26 PASS** 合计 ~1.326 亿指令、`s00_inst0` 510 万指令 0 FM 不一致且 1637/1637 PT/UP bins 全等）；Yosys 通用门（`SYNTH_LIGHT=1 SYNTH_MEM=1 SYNTH_LTP=1 SYNTH_NO_MEMPRIO=1 strash;balance;map`）：`predecode` 10,144/27、`pre_idu_queue` 137,578/38、`tlb_mmu` 46,624/61、`icache` 916,659/106、`bpu` 504,078/272、`front_top` 1,582,763/356（见 `rtl/docs/09-synthesis-report.md` 第 13 节，超 100 层路径已登记至 `docs/TODO.md` 后续拆拍）。

---

## EXP-050 块级 FTB + 1-ahead/2-ahead BPU（里程碑 A 模型探索）

- **日期**：2026-11-20 ~ 2026-11-21。**分支**：trace-model `exp/ftb-bpu`（DSE 归档 `375b080`）→ `merge/ftb-bpu`（`ef61350`）；rtl `rtl/ftb-bpu`（`a4dcfb9`）。**状态**：**已合入 `main`（2026-11-21：trace-model `ef61350`、rtl `a4dcfb9`，均已推送 `origin/main`）**。
- **问题**：`main` 现行 BPU 为 16-bank 逐指令槽架构（Type 30 KB + BTB 155 KB + TAGE 110 KB + ITT 29 KB ≈ **325 KB**，RTL `bpu` 高达 549,458 单元 / 134 层），每拍空转 >85% 读口，且 S1 无分支历史导致海量 2 拍 S2 覆写气泡，前端带宽损失（`FE.bw`）高达 `31.2%`。
- **方案（分两阶段在 `BpuFtb.h` / `BPU_pipe.h` 实现，全部由 `BPU_FTB=1` 默认关开关控制）**：
  - **Phase 1（块级 FTB + S1 主力预测 / S2 兜底）**：
    - 以取指块起点 `base_pc` 索引，单 bank 取代 16-bank Type + BTB + TAGE + ITT：
      - **S0（0 气泡）**：uFTB（256 × 4 路，20b 压缩目标，`BR_RET` 走 RAS 不受目标宽度限制）；
      - **S1**：Main FTB（2K/4K × 4 路，每项 **4 槽 `FTB_SLOTS=4`、禁止槽交换**以保持 TAGE 槽归属稳定，含 1b `carried` 标记正确处理 RVC 跨块 4B `CALL` 返回地址 `base+2` 与 `hist_sym(base-2, tgt)`）+ 可选 S1 mini-TAGE（256 × 4 表）；
      - **S2（兜底）**：4-slot Block-TAGE（2K/4K × 4 表，10-bit tag）+ 单块 3 表 Block-ITT（256 项共享）+ RAS；
      - **精确块训练**：通过 FTQ 透传 `blk_id` 与 `ftq_is_last` 到提交侧，经 `ftb_rec_[2048]` 恢复预测时刻的精确 `(base, fh)`，将 `tag_mismatch` 降为 **0**、`train_drops = 0`。
    - 迭代中定位并修复了 4 个关键根因：① 提交侧猜测块起点漂移（`tag_mm` 6.2% → 0）；② 2-slot FTB 在非截断 32B RVC 块中发生 3 分支颠簸（`FTB_SLOTS=2→4`，`evict3` 250k → ~1.7k）；③ `upsert_branch` 槽位交换打乱 TAGE 归属；④ RVC 跨块 4B `CALL` 在槽 0 压栈地址偏 2 字节导致 `COMMIT_MISPRED_RET` 暴增（加 `carried` 位后 `xalancbmk sp5` `RET_MP 38,425 → 9`）。
  - **Phase 2（硬件忠实 1-ahead / 2-ahead，零组合旁路 `FTB_OVR_FAST=0`）**：
    - `FTB_AHEAD=1`（1 拍纯 SRAM 流水）与 `FTB_AHEAD=2`（2 拍纯 SRAM 流水）：提前 1/2 拍用已寄存的 `(pc_{t-k}, H_{t-k})` 读 Ahead FTB（`aftb_`，22b 组合 tag 区分多后继）+ Ahead Block-TAGE（`atage_`，复用 `aftb_` 槽计数器作基表，无基表混叠）+ Ahead Block-ITT，到 S0 时仅做寄存器输出 tag 比较与选路，**完全消除同拍组合环（无需 `of2`）**；
    - 配合 `FTB_AH_ONLY=1` 删掉 `S1 mini-TAGE`（仅在重定向后 2% 冷启动拍退回 uFTB/Main FTB），S2 保留精确 PC/精确历史 Block-TAGE + Block-ITT 兜底（零精度回退）；Ahead 训练同样经 `ftb_rec_` 透传预测时刻 `(ah_key_base, ah_key_fh)`，保证零历史错位。
- **性能结果（全量 SPEC06 INT 12 程序 SimPoint 加权，vs `main` `6df4312`；376/386 点已收齐、0 失败，Phase 1 四组为完整 386/386）**：

| Benchmark | `main` 基线 IPC | P1 `2K_noof` (133 KB) | P1 `4K_noof` (250 KB) | P1 `4K_of2*` (250 KB) | **P2 `ah1_2k_a1k5`** (**174 KB**, `of2=0`) | **P2 `ah1_4k_a2k1k`** (**333 KB**, `of2=0`) | **P2 `ah2_4k_a2k1k`** (**333 KB**, `of2=0`) |
|---|---:|---:|---:|---:|---:|---:|---:|
| `400.perlbench` | 2.908 | +11.23% | +12.77% | +14.10% | +13.31% | **+15.18%** | +14.82% |
| `401.bzip2` | 2.374 | +5.45% | +5.58% | +5.85% | +5.67% | **+5.93%** | +5.73% |
| `403.gcc` | 1.546 | +10.03% | +11.41% | +13.33% | +11.69% | **+13.37%** | +13.17% |
| `429.mcf` | 0.410 | +0.52% | +0.61% | +0.69% | +0.66% | **+0.77%** | +0.78% |
| `445.gobmk` | 2.195 | +0.81% | +7.78% | +11.91% | +4.42% | **+13.11%** | +12.34% |
| `456.hmmer` | 5.278 | +10.24% | +9.91% | +10.08% | +15.90% | **+16.00%** | +15.97% |
| `458.sjeng` | 2.307 | +13.75% | +15.63% | +22.49% | +20.08% | **+23.65%** | +22.56% |
| `462.libquantum` | 2.117 | +1.14% | +1.18% | +1.26% | +1.40% | **+1.39%** | +1.44% |
| `464.h264ref` | 3.983 | +2.41% | +2.62% | +3.34% | +3.15% | **+3.40%** | +3.30% |
| `471.omnetpp` | 0.940 | +1.60% | +1.70% | +1.70% | +1.30% | **+1.64%** | +1.71% |
| `473.astar` | 1.383 | +0.97% | +2.74% | +4.25% | +2.33% | **+4.66%** | +3.91% |
| `483.xalancbmk` | 1.895 | +3.45% | +3.93% | +5.33% | +4.36% | **+5.32%** | +4.80% |
| **12 程序几何平均** | **12.11 /GHz** | **+5.02% (12.72)** | **+6.17% (12.86)** | **+7.61% (13.03)** | **+6.85% (12.94)** | **+8.48% (13.14)** | **+8.17% (13.10)** |

- **TMA 变化（`ah1_4k_a2k1k` vs `main`）**：`Retiring 28.39% → 31.28% (+2.89 pp)`，`Frontend Bound 32.91% → 24.64% (−8.26 pp)`，`FE.bw 31.23% → 22.85% (−8.38 pp)`；`456.hmmer` 达到 `6.03 IPC`（`Retiring 75.36%`）。剩余 `22.85%` 的 `FE.bw` 留待里程碑 B（`2-fetch` + `2-taken`）消化。
- **小负载标杆（`rtl/programs/big/`）**：`dhrystone.bin` `109,797 → 102,249`（`ah1`, +7.38%）/`102,033`（`ah2`, +7.61%）；`coremark.bin` `290,676 → 275,757`（`ah1`, +5.41%）/`276,560`（`ah2`, +5.11%）。
- **验证**：131/131 本地门禁（rv64 + RVC，`FTB_AHEAD=0/1/2` 全部 PASS）；`rv64gc` Linux 5.15.170（`FTB_AHEAD=0/1/2` 均顺利到达 `rv64 login:`，0 Oops/panic，`tag_mm=0`、`drop=0`）；`BPU_FTB=0` 与 `sim64_base`（`main 6df4312`）逐拍相等；`comb_graph.py --check` 0 新增 hazard。
- **里程碑 A RTL 落地与验证（`rtl/ftb-bpu`，`ah1_4k_a2k1k` + `FTB_BRQ=2`）**：
  - 零外部端口改动：通过既有 `out_tage_idxs[*][0]`（10 位）透传 `blk_id`，删 22 个旧 16-bank 文件，新增 `bpu_types_pkg.sv`、`bpu_ftb_tab.sv`、`bpu_ftb_tage.sv`、`bpu_ftb_itt.sv`、`bpu_ftb_brq.sv`、`bpu_ftb_arrays.sv` 并重写 `bpu.sv`（更新 `bpu_stage_pkg.sv`、`bpu_ctl.sv`、`bpu_pdq.sv` 与 `docs/modules/bpu.md`）；
  - **Lint**：`scripts/lint.sh rtl/frontend/bpu` 与 `scripts/lint_chip.sh` 均 **0 warnings / 0 errors**；
  - **裸机等价（`fm_gate.sh`）**：**67/67 PASS，0 FAIL，0 SKIP，0 FM 不一致，0 周期偏差**（`coremark` `275,332 == 275,332`，较 `main` −5.28%；`dhrystone` `102,229 == 102,229`，−6.13%；`itt-dispatch` `208,168 == 208,168`，−3.36%；`coremark` `PT`/`UP` 指纹 276/276 bins 全等）；
  - **`rv64gc` + `Sv39` Linux 26 段检查点对齐（`eda-08`/`eda-09`，`s01..s26`，每段 400 万周期，合计 1.04 亿周期）**：累计验证 **132,473,668 条真实指令**，**26/26 段全部 PASS、0 FM 不一致、全程 `PT`（103,974/103,974 bins）与 `UP`（103,144/103,144 bins）指纹 0 差异**（一并补齐 `LsuPipeInternal.h::ms_load_value` 对 `m.atnt=1` 污染地址 store 的旧物理地址 STLF 前递，一次性消除原 `s10`/`s15` 两处分叉）；
  - **Yosys 综合（`eda-06`，`SYNTH_ABC="strash;balance;map" SYNTH_NO_MEMPRIO=1`）**：`bpu` **`549,458 → 274,811 cells`（−50.0%）**，深度 **`134 → 131` 层**（最长路径仍在原有 `u_spec.aras_q → spec_d`，新块级逻辑未引入新关键路径）；`front_top` **`898,333 cells` / `153` 层**。
- **结论**：里程碑 A 采用 **块级 FTB + 1-Ahead + S2 兜底（`ah1_4k_a2k1k` + `FTB_BRQ=2`，无 `of2` 组合环、无 `S1 mini-TAGE`）**，全量 SPEC06 INT **+8.48%（`13.14 分/GHz`）** 且 RTL `bpu` 单元数直接减半（**−50.0%**）。数据在 NFS `/nfs_global/S/houruyao/spec06_rv64gc/tm/res_ftb*` 与 `/nfs_global/S/houruyao/rtl_ftb/`。

---

## EXP-048 L1 硬件 Berti + LLC BOP + MSHR 16/16 预取体系与 RTL 全程对齐

- **日期**：2026-11-20。**分支**：trace-model `exp/dse-fork`（基于 `main` `8fd0ae3`）；rtl `exp/pf-berti-bop`（基于 `main` `b9fd0df`）。**状态**：**已合入 `main`**（2026-11-20：trace-model `6df4312`、rtl `6e2d188`）。
- **问题**：`main` 基线使用 8/8 MSHR（L1D 8、LLC 8）与 L1 `h1` 预取、无 LLC 预取。全量 SPEC06 INT 访存密集程序（mcf、libquantum、gcc、astar、omnetpp）存在大量 L1D/LLC miss 与 MLP 受限，需要一套面积可控、严格单拍/硬件可实现（1-op/cycle）的 L1+LLC 预取组合并完整写入 RTL。
- **方案（三阶段落地）**：
  - **M1（MSHR 16/16 + `VQD=32`）**：L1D MSHR `8 → 16`、LLC MSHR `8 → 16`（及 AXI 互连读槽 `16`），LLC 受害行写回队列 `VQD = 8 → 32`（`NVL = 51`，与模型 `AXI_LLC.h` 深度一致，避免 16 MSHR + BOP 并发换出满队列）。
  - **M2（LLC Best-Offset 预取，`LLC_BOP=1`）**：在 `axi_llc` 中实现硬件 BOP（Recent-Request 表 + 26 偏移轮询评分 + 候选 FIFO，受 MSHR 保留槽与在飞上限反压）。
  - **M3（L1 硬件 Berti，`PF_KIND=4` + DTLB 跨页翻译）**：在 `dcache` 中实现 1-op/cycle 硬件忠实版 Berti（`dcache_pf_berti_*.sv`，16 路历史表 + 按 PC 步长置信度表 + 候选队列 + `dcache_s1` 隐藏重试保留 `rty_pc_q`/`rty_va_q`），跨页虚拟地址候选通过真实 DTLB 空闲端口翻译（零额外 TLB 端口）。
- **开关与默认值**：实验期通过 `PF_KIND=4`、`LLC_BOP=1` 及 `CFG_DCACHE_MSHR=16` / `CONFIG_AXI_LLC_MSHR_NUM=16u` 控制；合入 `main` 前对齐为默认配置（不依赖环境变量与 `-D`）。
- **性能结果（全量 SPEC06 INT，12 程序 386 个 SimPoint 检查点，386/386 完成，0 失败）**：

| Benchmark | Pts | `main` h1(8/8) | sw b16(16/16) | vs h1 | RTL BertiHw(8/16) | vs h1 | **RTL BertiHw(16/16)** | **vs h1** | hw/b16 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 400.perlbench | 24 | 2.876 | 2.906 | +1.04% | 2.909 | +1.16% | **2.916** | **+1.38%** | +0.34% |
| 401.bzip2 | 48 | 2.325 | 2.373 | +2.09% | 2.370 | +1.97% | **2.374** | **+2.13%** | +0.05% |
| 403.gcc | 34 | 1.431 | 1.544 | +7.93% | 1.529 | +6.84% | **1.544** | **+7.90%** | −0.03% |
| 429.mcf | 45 | 0.309 | 0.389 | +26.02% | 0.389 | +26.24% | **0.395** | **+28.14%** | +1.68% |
| 445.gobmk | 29 | 2.193 | 2.195 | +0.09% | 2.195 | +0.09% | **2.194** | **+0.04%** | −0.05% |
| 456.hmmer | 23 | 5.256 | 5.272 | +0.31% | 5.276 | +0.39% | **5.277** | **+0.40%** | +0.09% |
| 458.sjeng | 27 | 2.285 | 2.306 | +0.95% | 2.307 | +0.99% | **2.307** | **+0.99%** | +0.04% |
| 462.libquantum | 36 | 1.543 | 2.131 | +38.10% | 1.723 | +11.64% | **2.116** | **+37.14%** | −0.70% |
| 464.h264ref | 35 | 3.975 | 3.982 | +0.17% | 3.981 | +0.16% | **3.982** | **+0.18%** | +0.01% |
| 471.omnetpp | 25 | 0.919 | 0.938 | +2.08% | 0.940 | +2.27% | **0.940** | **+2.33%** | +0.24% |
| 473.astar | 26 | 1.148 | 1.184 | +3.16% | 1.176 | +2.50% | **1.186** | **+3.35%** | +0.18% |
| 483.xalancbmk | 34 | 1.863 | 1.882 | +1.07% | 1.887 | +1.30% | **1.897** | **+1.84%** | +0.76% |
| **GEOMEAN** | **386** | **11.37 /GHz** | — | — | — | **+4.40%** | **12.11 /GHz** | **+6.58%** | **+0.22%** |

- **Linux 验证与逐周期对齐**：
  - `trace-model`（`sim64_bop14`，`PF_KIND=4 LLC_BOP=1`）单次从复位启动 rv64gc Linux 5.15.170 直达 `rv64 login:`（1.35 亿条指令，IPC `0.8594`，L1 Berti 准确率 `29.6%`、DTLB 跨页命中率 `98.8%`、LLC BOP 准确率 `73.1%`，0 报错）。
  - 27 个 5M 步长 rv64gc Linux 检查点窗口（`s00..s26`，每窗 `SOC_TB_MAX_INSTS=5100000`，无缝覆盖 `0 → 135.1M` 共 1.377 亿条指令）全量 RTL vs `trace-model` **27/27 PT/UP 逐周期相等、0 FM 不一致**，修掉 3 类根因（详见 `trace-model/docs/LINUX_ALIGN.md`）：① `axi_llc_pkg.sv` `VQD = 8 → 32`；② 双边 `OP-32` 非法指令译码（`idu_ctrl_decode.sv` + `InstDecode.cpp`）；③ 模型 `ms_load_value` 跨 dword 非对齐 load 对齐 RTL `extract_data`（`LsuPipeInternal.h`）。
- **综合**：本轮暂不做综合（后续统一切换 DC 综合）。

---

## EXP-045 cache 替换策略：LLC 与 L1I 改为 SRRIP

- **日期**：2026-11-19。**分支**：trace-model `exp/llc-plru`（工作区 `trace-model-llcplru`，基于 main `c795844`；`69661b9` LLC rr/plru/lru，`edf26f4` srrip/brrip/drrip、`LLC_PF_LOW`、`ICACHE_REPL`、`TLB_REPL`，`429172d` 默认改为 SRRIP + 写口冲突时丢弃分配更新）；rtl `exp/llc-plru`（`aac554a`，工作区 `rtl-llcplru`，基于 main `a26a102`）。**未合入**。
- **问题**：EXP-014 的离线回放说替换策略的空间小（LLC DRRIP 缺失 −3.9%，L1I SRRIP −17%），当时只测空间、没有实现。这次把策略做进周期模型（与 RTL 结构一致：每组的替换状态和行表一起在查表解析时读改写），在真实时序下比较，采用的写进 RTL。负责人 2026-11-17 选过 PLRU 作为标准，本轮按实测改为 SRRIP。
- **做法（模型）**：
  - LLC（4 MiB 16 路）：替换行 8 字节，开关 `LLC_REPL=rr|plru|lru|srrip|brrip|drrip`（`rr` = 旧 main 的"最近被碰的路的下一个"指针）。命中在查表完成时更新该路；分配缺失在分配时更新受害路；重填和写提交不再写替换行。RTL 每拍只有一个行表写口，写提交（stage 2）占口时查表的写被挤掉，模型用 `lookup_tbl_busy_` 同样丢弃这次分配的替换更新。SRRIP：2 位 RRPV，命中置 0，受害路取 RRPV 最大的最低路，分配时整组变老到最大值 3 再把新行置 2；BRRIP 新行置 3（每 32 次有 1 次置 2）；DRRIP 用 set dueling（`set%32==0` SRRIP 领头组、`==1` BRRIP 领头组，10 位 PSEL）。LRU 存"年龄 XOR 路号"，复位全零也是合法状态。
  - L1I（32 KiB 8 路）：`ICACHE_REPL=rr|plru|srrip`，每组 16 位状态在 `ICacheTop` 里，命中在 IDLE 查找后更新，回填在 `finish_refill` 更新，受害路在 `latch_mem_refill` 选。
  - TLB（ITLB/DTLB 各 64 项全相联）：`TLB_REPL=rr|nru|plru`，先选无效项。
  - `LLC_PF_LOW`（预取填充以低优先级插入）没有作用：默认配置没有 LLC 预取器。
- **SPEC 测量**：29 个 rv64gc SPEC06 点（12 个程序各取权重最高的若干点，`pts_names.txt`），stub 检查点、10M 详细预热 + 10M 测量、`PF_ENABLE=1 PMU=1`、`RVC=1`，eda-06/08。按程序加权 CPI 求加速，再取 12 个程序的几何平均（`cmp2.py`）。

| 配置（相对 rr） | 几何平均 | 主要变化 |
|---|---|---|
| LLC PLRU | +0.87% | |
| LLC LRU | +0.99% | |
| **LLC SRRIP** | **+1.23%** | omnetpp +9.0%、xalancbmk +3.75%、mcf +1.76%、perlbench +0.67% |
| LLC DRRIP | +1.17% | 比 SRRIP 多 set dueling，收益不更高 |
| LLC BRRIP | +0.78% | |
| LLC SRRIP + L1I SRRIP（新默认） | **+1.63%** | gobmk +2.9%、perlbench +1.3%、gcc +0.6% |
| 新默认 + TLB NRU | +1.65% | TLB 只多 +0.02% |

  在 LLC PLRU 之上叠加：L1I SRRIP +0.42%（gobmk +3.2%）、L1I PLRU +0.19%、TLB NRU +0.12%、TLB PLRU +0.05%。L1D 本来就是 PLRU，EXP-014 显示没有空间，不动。2 个 rr 对照点在新旧二进制上周期逐个相同。

- **结论**：LLC 和 L1I 改为 SRRIP（模型默认、RTL 实现）；TLB 收益在噪声量级（+0.02%~+0.12%），不值得在 TLB 里加替换状态和选择逻辑，不采用；DRRIP 不值得多出的 PSEL 和领头组逻辑。
- **RTL**（文档先行：`docs/modules/axi_llc.md`、`docs/modules/icache.md`）：
  - LLC：`axi_llc_pkg` 替换行宽 `RB = 2*WAYS`、函数 `rrip_hit` / `rrip_alloc`，删掉 `next_way`；`axi_llc_waypick` 改为"第一个无效的未占用路，否则 RRPV 最高级的第一个未占用路"（每级一个 `ttg_first_set`）；`axi_llc_resolve` 在命中 / 分配时写替换行（写提交占口时丢弃）；写提交和重填不再写替换行。
  - L1I：`icache_arr` 加 `repl_q`（每组 16 位）、选路（每级一个 `ttg_first_set`）和命中 / 回填更新；`icache_swap` 在有效读时用 `repl_way`，否则仍用原轮转指针（非缓存访问不变）。
  - `scripts/ref_cycles.txt` 3 个程序变化（dcache-conflict-writeback 6030 → 6018、memory-stress-small 343672 → 343459、pf-stress 618141 → 580756），旧表存为 `ref_cycles_repl_rr.txt`。
- **验证**：
  - trace-model：C gate 67/68（`fdoff` 没有基线项，原有）；`LLC_REPL=rr ICACHE_REPL=rr` 下 67 个 RTL 门禁程序周期与 main 的 `ref_cycles.txt` 逐个相同。
  - RTL：`lint_chip.sh` 0 警告；`fm_gate.sh` **67/67**，周期与模型（新默认）逐个相等；Linux 检查点窗口 s00–s12（各 400 万周期）**13/13 PASS**，逐条检查 0 不一致，PT / UP 指纹与模型相同。没跑：RTL 从复位的完整 Linux、SPEC 全量。
  - 综合（`synth_depth.sh`，`SYNTH_ABC="strash;balance;map"`，对 main `a26a102`）：axi_llc 深度 238 → 238、单元 470,031 → 470,717（+0.15%）；icache 深度 69 → 70，单元去掉反相器后 304,114 → 305,070（+0.3%；main 的网表多出 26 万个反相器，是 ABC 的映射差异）。替换状态是存储器，不在单元数里：LLC 每组 4 位指针 → 32 位（4096 组共 128 Kbit），L1I 每组 16 位（64 组共 1 Kbit）。
  - **注意**：`scripts/env.sh` 默认的 `TTG_PROGS`（`trace-model/build`）里是旧的 rv32 程序，用它生成参考周期会对不上；本轮用 `TTG_PROGS=trace-model-simplify/build`（rv64，不带 C）。
- **数据**：`~/personal/AI-Huma-data/llc_repl`（`all_res2.txt` 所有配置的逐点结果、`cmp2.py`、权重 `w.txt`、点表、eda 运行脚本、参考周期）。eda 上原始结果在 `/nfs_global/S/houruyao/spec06_rv64gc/tm/res_llc{1,2,3}`。

## EXP-046 写口：发射时调度（选择前查完成周期、浮点写通道压缩）

**问题**：用户问能不能在发射时就把写口调度好。main 其实已经在发射时按完成周期预约每个口的写回（EXP-035，`WbBusy`，冲突为 0），浮点寄存器堆也有发射时的写口限制（EXP-032，`FP_WB_PORTS = 2`）。剩下的三个问题：(1) 预约检查在选择之后，被拒的口这拍空着；(2) 忙表是 21 × 64 位的环；(3) 浮点寄存器堆仍然为每个口留一条写通道，没有利用"每拍最多 2 个浮点单元写回"这个保证。

**分支**：trace-model `exp/wb-port`（工作区 `trace-model-wbport`，`ff96476` 计数器 + `CFG_WB_PRESEL`，`60aa7e8` 只查完成周期）（这两个提交的说明里写的是 EXP-045，与 cache 替换策略撞号，之后改为 EXP-046）；rtl `exp/wb-presel`（工作区 `rtl-wbp`，`d093291` isu、`7957ec9` prf 浮点写通道、`f2674cf` 写回总线按通道；trace-model `98e9d3a` 写回总线按通道）。都从各自 main 拉出，没有合入、没有推送。function-model 用 main（`55affa0`）的私有构建（`fm-wbport-rvc1`，RVC=1）。

**开关**：模型 `CFG_WB_PRESEL`（`include/config.h`，默认 0 = main 行为，周期与基线逐个相同：67 个 RVC 程序 gate 全过）；1 = 选择时跳过完成周期已被占的 uop；2 = 再跳过执行单元不收的 uop（与 1 在 67 个程序上周期完全相同，不采用）。RTL `isu_pkg::WB_PRESEL`（分支上为 1）。

**冲突统计**（模型新 PMU 事件 `ISS_REF_*` / `ISS_LOST_*`，只在模型里；62 个 RVC 程序共 156 万周期）：选中后因完成周期被占而被拒 55,643 次，其中 31,162 次当拍还有别的就绪 uop 能用这个口；因执行单元忙被拒 31,515 次但只有 21 次有替代；FP 写口拒 919 次、共享 AGU 拒 121 次。集中在 pf-stress、shuixianhua、fd-matmul、matrix-mul（乘法和浮点多的程序）。

**性能**：

| 负载 | `CFG_WB_PRESEL=1` 相对 0 |
|---|---|
| 67 个 RVC 程序（`run_gate_c.sh`） | 几何平均 −0.49% 周期（shuixianhua −25.8%、leap-year −1.7%、fd-matmul −0.7%、pf-stress +0.1%，其余不变） |
| RTL 门禁的 67 个 rv64 程序 | coremark −1.4%、dhrystone +0.2%，14 个程序变化 |
| SPEC06 rv64gc 386 点（eda，10M 预热 + 10M，PMU 开） | SimPoint 加权 IPC +0.01%，12 个程序都在 ±0.1% 内（=2 的版本同样 +0.01%） |

**RTL 改动**（`rtl-wbp`，文档 `docs/modules/isu.md`、`prf.md` 已同步）：
1. `isu_wb_gate`：忙表从 21 × 64 位环 + 拍号改成每口一个"距今几拍"的移位寄存器，长度 = 该口最长完成偏移 − 1（共 95 位）。一个口按拍发射，完成周期只会被更早发射、偏移更长的 uop 占，所以每口偏移最长的类、单类口的所有类编译期恒空（`cls_blockable`）。这一步单独看周期与 main 完全相同。
2. 选择前查完成周期：每个槽入队时寄存会被占的完成类位（`slot_cls_q`），选择候选再与上 `~(类位 & ~cls_free)`；`wb_ok` 闸恒 1。
3. `prf`：浮点写通道 21 → 6（4 条 load + 浮点单元 / I2F 的写回按口序取前 `FP_WB_PORTS` 个压成 2 条），浮点结果只为能写浮点寄存器的 9 个口暂存。前提"写回级每拍最多 2 个浮点单元写浮点寄存器"用仿真检查 `[FPWB]` 验证，67 个程序 0 次。
4. **写回总线按通道编号**（用户指出"21 个写口"迷惑）：原来模型和 RTL 的写回数组按发射口编号（21 条），STA / STD / BR 口占着永远不写寄存器的位置，这是照搬模型结构的遗留，没有好处。现在模型 `config.h` 定义 `WB_LANES = 13`（ALU 6 + load 4 + 浮点口 3，`WB_ALU_BASE / WB_LD_BASE / WB_FP_BASE`），模型 `exe2prf.entry`、RTL `exu_ctrl_wb_prf` → `prf` 的写回级、写口、写回旁路、load 唤醒都按通道；STA 的完成只进 ROB。整数寄存器堆写口 21 → 13，浮点 6。周期不变（模型两个程序集、RTL 门禁）。`ttg_cfg_pkg.sv` 手工加了这 4 个常量：现在提交的包本来就和生成器输出不一致（重新生成会丢掉 `XLEN_BITS`、`IQ_MEM_SIZE` 等，isu.md 第 9 节已记为待办）。
5. `tests/wb_gate`：main 上已经编译不过（驱动已删的 `off` 输入），改成按完成类驱动并检查每口每类的 `cls_free`，随机 3 万拍 0 不一致，植入错误后 24,140 拍不一致。

**综合**（单模块，`synth_depth.sh`，`SYNTH_ABC="strash;balance;map"`，yosys 通用门，相对数）：

| 模块 / 版本 | 单元 | 深度 |
|---|---|---|
| isu main | 957,032 | 88 |
| isu 只改忙表 | 945,443（−1.2%） | 88 |
| isu 选择前查（第一版，每槽解码类） | 1,015,056（+6.1%） | 100 |
| isu 选择前查（最终，入队时寄存类位） | 948,874（−0.9%） | 89 |
| prf main | 1,077,848 | 36 |
| prf 浮点写通道压缩 | 867,357（−19.5%） | 36 |
| prf 再加写回总线按通道（整数写口 21 → 13） | 679,466（−37%） | 27 |

prf 的单元数含单模块的边界效应：只暂存 9 个口的那部分（触发器 3570 → 2546）在整芯片展平时本来会被常量传播去掉；实打实的节省是浮点单元的 5 条写通道压成 2 条（96 个浮点寄存器的写口比较和 12 个浮点读口的写回级旁路）。没有做整芯片综合。

**验证**：RTL `fm_gate` 67/67 逐条对函数模型无不一致，周期对模型（同一批 rv64ima 程序，`build_tests.sh` 构建，`LSU_PIPE_NOWD=1`）67/67 相等。（早先记录"crc32 RTL 2196 / 模型 2199，main 原有差异"是错的：生成参考周期时没有关模型的 LDQ / STQ 看门狗，RTL 没有这个看门狗；`rtl/scripts/tm_cycles.sh` 现在默认 `LSU_PIPE_NOWD=1`。）`lint_chip` 0 告警。模型 `CFG_WB_PRESEL=0` 时 RVC gate 67/67 周期不变。

**模型近似**：模型没有数据通路，浮点写通道压缩只在 RTL 里，靠 RTL 仿真检查确认前提；PMU 的"本可替代"计数是上界（替代者可能被后面的口拿走）。

**复现**：模型 `scripts/wb_build.sh <dir> "-DCFG_WB_PRESEL=1"`、`scripts/run_gate_c.sh`、`scripts/wb_refuse_stats.sh`、`scripts/wb_cmp.py`；SPEC 用 eda NFS `tm/wbp_one.sh`（cfg 0 / 1 / w）+ `cmp_ev5.py`，结果 `tm/res_wbp0`、`res_wbp1`、`res_wbpw`（第 2 份任务因启动命令卡住被重复启动过一次，4 个点跑了两次，每个点都有完整结果）。RTL：`tb/soc/build.sh`（`SOC_FM=1`）+ `scripts/fm_gate.sh`（`REF_CYCLES` = 模型 `tm_cycles.sh` 生成的表），`tests/wb_gate/run.sh`，`scripts/synth_depth.sh`。

**合入 main（2026-11-19）**：与 EXP-045（LLC / L1I SRRIP）一起，经集成分支 trace-model `exp/wb-llc`、rtl `exp/wb-llc-rtl`。合入时：删掉探索开关 `CFG_WB_PRESEL` / `WB_PRESEL`（选择前查完成周期是唯一行为，与带开关的版本周期逐个相同）；删掉模型里 RTL 没有的 LDQ / STQ 看门狗和 `LSU_PIPE_NOWD`（默认运行 = 以前 `LSU_PIPE_NOWD=1` 的运行，三套程序逐个相同）；trace-model Makefile 和 rtl `scripts/fm_lib.sh` 从固定版本 `FM_REV` 自动构建 function-model；rtl 脚本默认值改对（`build/progs`、`regen_refs.sh`，见 WORKFLOW 3.3）；合入 `exp/fdoff`（测试处理程序的 rv64 修复）。验证：模型门禁 62/62、62/62（关预取）、C 68/68；RTL `fm_gate` 67/67、周期与 `ref_cycles.txt` 全部相同（不设任何环境变量的默认流程）；Linux 子窗口 s00–s12 共 13 个全部 PASS（约 6400 万条指令逐条检查，PT / UP 指纹与模型相同）。全量 SPEC06（386 点）：合并版（SRRIP + 本实验）相对旧 main IPC +1.66%，LRU 版 +1.39%（libquantum sp44 在 SRRIP 下 −21.6%，原因是 DRAM 读排队，待查）。

**结论**：发射时调度写口本身在 SPEC 上几乎不带来性能（+0.01%），乘法 / 浮点密集的小程序有收益；它的价值在硬件：忙表改写和浮点写通道压缩都是周期不变的面积节省，选择前查的代价是 isu 深度 +1 层。**未覆盖**：整芯片综合、Linux 窗口、SPEC FP（检查点只有整数程序）。

## EXP-044 RTL 降深度那一轮和 Linux 窗口对齐

**目的**：整芯片综合深度（yosys 通用门的深度代理）压到 100 层以下，同时 RTL 周期与 trace-model 逐个相同。负责方法：在深度最长的路径上找结构，能并行的并行，能少一级的少一级，改了必须保持周期不变，或者模型同步改并重新对齐。

**分支**：rtl `exp/agu-share`（比 main 多 47 个提交），trace-model `exp/tlb-ports`（比 main 多 48 个提交），均已快进合入 main。function-model 未动（`55affa0`）。

**配置变化（模型 `include/config.h` 默认值 = RTL 配置，之前要 13 个 `-D`）**：

| 参数 | 旧默认值 | 新默认值 |
|---|---|---|
| `CFG_INT_CLUSTERS` / `CFG_INT_IQ_SIZE` / `CFG_INT_IQ_ENQ_WIDTH` | 1 / 64 / 7 | 2 / 32 / 4（两个 INT 发射队列，端口 0,1,4 / 2,3,5） |
| `CFG_MEM_IQ_ENQ_WIDTH` | 8 | 6（访存队列只有一个，load + STA 合并，去掉了 STA 空队列和 `CFG_MEM_MERGE`，共 6 个队列） |
| `CFG_AGU_SHARED` | 0 | 2（5 个 AGU：2 个 load 专用、2 个 load / STA 共用且 load 优先、1 个 STA 专用） |
| `CFG_ISSUE_OLDEST_FIRST` / `CFG_ISSUE_OLDEST_QUEUES` | 0 / 0xff | 2 / 2（只有访存队列、每种能力的第一个口选最老的） |
| `CFG_IQ_SAME_CYCLE_REUSE` | 1 | 0 |
| `CFG_FLUSH_REG` | 0 | 1（全局 flush 晚一拍到达各模块，`docs/FLUSH_REG.md`） |
| `CFG_LSU_STAEV_REG` / `CFG_LSU_SLOT_FIXED` / `CFG_LSU_WBMERGE_REG` | 0 / 0 / 0 | 1 / 1 / 1（STA / STD 事件先寄存再唤醒停车的 load；L1 的槽 k 就是 AGU 口 k；写缓冲插入只合并到本拍刚开始的项） |
| `CFG_FE_OVR_REG` | 0 | 1（取指地址 FIFO 的一项在写入后一拍才读，不依赖同拍 BPU 最后一级的覆盖） |

**RTL 的结构改写（都有 old-vs-new 随机对拍或整核周期不变的验证）**：`lp_ptr` / `lp_rp`（提交接受从第一个命中 `commit_ptr` 的 store 起算、STA 重放选择不转请求向量）、`lp_wbstep`（写缓冲只合并到本拍刚开始的项）、`lp_ovl`（load 与 store 的邻居比较）、`bpu_ub_track_ser`（提交块跟踪器，余量用独热存：528 → 97 层）、`bpu_updq`（更新队列前缀计数压缩）、`bpu_ub_look`（uBTB 查表 75 → 29 层）、`front_fetch_buf`（指令起点的前缀扫描）、`fetch_addr_fifo`（`head_fresh`）、`mul_core`（乘法铺在 3 拍上，`mul_unit` 209 → 90 层）、dispatch / isu 队列清理。删掉的死代码：旧 LSU 和 `LSU_PIPE`、行式 ROB 和 `ROB_COMPACT`、`csr_fu`、各种只剩一个值的开关（`INT_CLUSTERS`、`MEM_AGE`、`IQ_SAME_CYCLE_REUSE`、`LP_STAEV_REG`、`LSU_WAIT_MSHR_FILL`）。每个原子模块一份设计文档（`rtl/docs/modules/`，34 份，模板 `TEMPLATE.md`，索引 `docs/05-module-tracker.md`），开发流程见 `WORKFLOW.md` 第 7 节（文档先行、提交前核对）。

**Linux 窗口对齐中修掉的问题**（trace-model `docs/LINUX_ALIGN.md` 有过程）：
- RTL `lp_ldq`：DCache 响应选择把 epoch 放进匹配（过期响应盖住有效响应，load 停在 DCW）；
- RTL `bpu_ub_look`：uBTB 目标按完整宽度读（原来取低 32 位，内核地址预测错）；
- RTL `back_top_glue`：flush 决定那一拍不再用重定向地址覆盖提交槽的 `diag_val`（同拍提交的调用用 mtvec 训练了 BTB）；
- 模型：`MsData` 对违例 load 第二次写回的同拍可见性（`MsLdq::early_clean`）、桥接层对 `mstatus.FS = Off` 的 FP store 不先读旧值、flush 型提交指令的 FS-dirty 保留、uBTB 目标全宽；
- 指纹口径：`dir=0` 的训练事件不计目标。

**负载和结果**：
- 67 个程序（`scripts/fm_gate.sh`）：RTL 周期 = 模型周期，逐条提交对 function-model 0 不一致；相对上一版 main 的参考表几何平均 **+1.92%** 周期（变慢）：dhrystone 100,722 → 108,732（+7.95%）、coremark 286,265 → 294,895（+3.0%）、memory-stress-small 343,381 → 343,672（+0.08%）；最差的是 `timer-mmio`（+19.8%）、`goldbach`（+12.3%）、`mersenne`（+8.6%）。
- SPEC06 rv64gc，386 个点（`final95`，约 95% 权重，10M 指令、10M 详细预热，`PF_ENABLE=1`，eda 集群，同一份代码两个配置各跑一遍）：新配置对旧默认值（同一份代码）12 个程序 IPC 几何平均 **−2.15%**（hmmer −8.6%、bzip2 −3.5%、sjeng −3.5%、astar −2.6%、gobmk −2.4%、perlbench −2.0%、gcc −1.4%、omnetpp −1.4%、libquantum −0.7%、mcf −0.4%、h264ref −0.4%、xalancbmk +1.6%）；旧默认值对 11 月 15 日的 `res_final` 基线 +0.04%（说明这期间的代码变化对 SPEC 几乎没有影响）；新配置对 `res_final` −2.11%。结果和对比脚本：`AI-Huma-data/spec06_rv64gc/ev5_run/`（`cmp_ev5.py`）。
- Linux：检查点窗口 s00–s11 共 12 个（各 400 万周期）trace-model 对 RTL 的 PT / UP 指纹全程相等、逐条检查 0 不一致；模型 Linux 从复位启动到 `rv64 login:`，无 oops / panic。
- 综合：这一轮的每个改写在单模块上有深度数字（见各模块文档的 `depth:` 和第 6 节）；**整机深度没有最新数**（`back_top` 135、`front_top` 132 都是后来又改了好几处之前的数；`ren` 110、`axi_llc` 238 超过 100）。

**结论**：深度目标的主要改写已经做完，代价是 SPEC 约 −2.1%、67 个程序 +1.9%，主要来自两个 INT 队列（32 项、4 条入队，hmmer 这种 INT 密集的受影响最大）和 FLUSH_REG；每一项的单独代价没有逐项量化（只做过取指地址 FIFO 晚一拍读：16 个点 IPC −0.82%）。

**后续**（TODO.md）：整机综合和剩余超 100 层的模块；模型里 13 个旧配置宏的旧路径要删；`diag_val` 字段拆分；访存违例改成从 load 本身冲刷（第二次写回不再写寄存器）；新旧并排的等价测试台进 `rtl/tb/`；RTL 从复位的 Linux 全程指纹对比。

## EXP-043 L1 Berti / store 预取、L2 stream、Breadcrumbs L1 部分

**目的**：在 h1（EXP-009：全局单项步长 + 只进 LLC 的 next-line）之外，试 L1 用 Berti 和 store 预取、L2（LLC）放 stream；再把 EXP-022 x86 的最终设计（Breadcrumbs，trace-model-rdf `docs/experiments/exp022_x86_design.md`，gem5 `afba9f8`）的 **L1 部分**移植到 RISC-V。

**实现**（trace-model `exp/pf-l1l2`，全部默认关、关时与 main 周期一致：RVC=1 gate 67/67）：
- 接口：`LoadReq` 带 load 的 PC（以及模型侧的 uid / 虚地址）；LSU 把翻译好的 store 地址送到 L1D（`DCacheReqPorts.sta_pf`）；L1D 把每次填充告诉预取器。
- `PF_STRIDE=0` / `PF_LLC=<n>`：关 h1 的步长 / 设只进 LLC 的 next-line 行数（0 = 关）。
- `PF_BERTI=1`：Berti（历史表 8×16、16 PC × 16 delta，按实测缺失延迟找及时的 delta，覆盖 ≥65 % 进 L1、≥35 % 只进 LLC，页内）。模型级结构。
- `PF_STPF=1`：STA 翻译出地址时预取该行进 L1（8 项最近行过滤）。
- `PF_L2S=1`：`AXI_LLC` 里 16 条流（每条一个 4 KiB 页），用 LLC 收到的 L1D 读训练，确认方向后前取 16 行、每次入队 4 行；最多 4 个预取 MSHR，留 2 个给需求。
- `PF_BC=1`：Breadcrumbs 的 L1 部分。解耦标签引擎（8 项队列、每拍 `BC_TQ_W`=2 条，只有走标签规则的整数写指令进队，其余整数写指令的清除位随下一条入队指令走，分支 / FP load / store 在重命名时直接读标签）；按归纳寄存器的循环表（周期、从分支学边界）；数据流步长实例（距离 = 缺失延迟 ÷ 周期，4 行，流终点截断）；值表 16 + 关系表 32（提交时训练，双链、算术右移）；L1 侧的间接触发（自己取进来的生产者行填充、冗余探测、需求缺失、下一跳）。没做远端窗口和 L2 填充触发。模型简化：元素值读功能内存，预取地址用 1024 项的 VA→PA 页映射翻译（查不到丢弃）。定向测试 `tests/extra/bc-indirect.c`。

**方法**：rv64gc SPEC06 检查点（eda 集群，stub 模式，10M 详细预热 + 10M 测量），访存组 = res_final 里 DRAM 读 / 千指令 > 6 的 6 个程序（gcc、mcf、libquantum、omnetpp、astar、xalancbmk），每个程序权重最高的点到 60 % 或 10 个，共 59 点。基线直接用 `spec06_rv64gc/tm/res_final`（2026-11-15 的二进制，PF 开），没有用当前 main 重跑。程序内按权重加 CPI，程序间几何平均。结果 `/nfs_global/S/houruyao/spec06_rv64gc/tm/res_pf43/<配置>/`，脚本 `tm/pf43_one.sh`。

**结果**（周期加速，相对 res_final）：

| 配置 | gcc | mcf | libq | omnetpp | astar | xalanc | 几何平均 |
|---|---|---|---|---|---|---|---|
| h1 + Berti | +1.3 | +7.6 | +1.2 | 0.0 | +1.4 | 0.0 | **+1.88** |
| h1 + L2 stream（保留 LLC 引擎） | +1.9 | +8.0 | +0.2 | −0.6 | +1.3 | +0.3 | +1.81 |
| h1 步长 + Berti + store + L2 stream（关 LLC 引擎） | +1.9 | +9.2 | +1.6 | −1.7 | +1.0 | −2.1 | +1.57 |
| h1 + Breadcrumbs L1，标签引擎 3 宽 | +0.4 | +5.2 | −1.3 | +0.2 | +0.7 | +1.0 | +1.01 |
| h1 + Breadcrumbs L1（2 宽） | +0.3 | +3.1 | +0.2 | +0.2 | +0.6 | +0.7 | +0.84 |
| L2 stream 替换 LLC 引擎 | +0.6 | +3.8 | +0.3 | −2.2 | +0.6 | −1.7 | +0.21 |
| h1 + store 预取 | +0.1 | 0.0 | 0.0 | +0.3 | 0.0 | 0.0 | +0.06 |
| Breadcrumbs L1，关 LLC 引擎 | −1.6 | +5.4 | +0.3 | −3.5 | +0.2 | −7.0 | −1.09 |
| 只关 h1 步长（Berti + store + L2 stream） | +1.9 | +6.9 | −24.0 | −1.7 | +0.9 | −5.1 | −4.05 |
| 只用 Berti（关 h1） | +0.8 | +4.5 | −30.0 | −3.6 | +0.5 | −9.2 | −6.96 |

**结论**：
1. Berti 只能叠加在 h1 上，替换不了 h1 的步长（libquantum 全部点 −20～−40 %，与 EXP-026 sdip 替换 h1 的现象相同）。
2. h1 的只进 LLC 引擎对 omnetpp / xalancbmk 很重要：L2 stream 或 Breadcrumbs 替换它都会掉；两者并存才有收益。
3. store 预取在访存组上无收益（写缓冲已经吸收 store 缺失）。
4. Breadcrumbs L1 收益不到 Berti 的一半。原因：2 宽标签引擎丢 19～35 % 的标签指令（3 宽仍丢 10～16 %，只多 +0.2）；关系表 32 项在 mcf / xalancbmk 上反复换出（置信转变 13～18 万次）；用于及时距离的缺失延迟 EWMA 只有 19～90 拍（被 LLC 命中拉低），提前量偏小。也没有 L2 部分（gem5 上 GAP 收益的主要来源）。
5. mcf sp21：当前代码重跑基线 35,395,818 周期，与 res_final（35,356,425）差 0.1 %，不是漂移；这个点对预取非常敏感（h1 + Berti 20.5M，h1 + BC 33.4M）。

**Breadcrumbs 移植的修正（2026-11-17 晚，提交 `42edde1`…`249dc82`）**：上面 BC 的数字有移植错误，逐点诊断（`[BC-DIAG]` / `[BC-PC]`）后改正：
- 步长 ≥ 64 B 按迭代取（`va + (D+k)·S`），距离至少 4 个步长（gem5 `min_distance`）；之前一律按行取连续 4 行。
- 寄存器步长归纳 `r = r + rX`：按 gem5 `BC_RSTEP` 在提交时从相邻结果学步长，置信后才给仿射标签；之前沿用了 r 的旧步长（mcf 上 BC stride 填进 L1 的 341 万行只有 2076 行被用到，−17 %）。只有 r 的上一个写者是这条指令或另一条自增 add 时才算（libquantum 的 `ld a5; add a5,a5,a3` 是"新读的基址 + 仿射偏移"，不是归纳）。
- 标签队列 3 宽 16 项（2 宽 8 项在突发时丢 19～35 %）；`BC_TQ_REUSE=1`（本拍出队的空位当拍可写）让 8 深 8 宽不丢、8 深 3 宽丢 2.6 %。
- `BC_NOOVL=1`（gem5 的近端不重叠）、`PF_PCS=1`（gem5 StridePrefetcher 形式的 PC stride，gem5 最终设计近端配的就是它）。
- 错误路径（`BC_WPFLUSH=1` 清队列 / `=2` 再用撤销日志恢复标签）：mcf 上处理的标签写约三分之二来自错误路径，但三种做法周期差 < 0.3 %，不是问题。
- 3 个诊断点上只比 L1 stride：BC stride 实例 + PC stride 对不预取 libquantum +20 %、xalancbmk +49 %，Berti +19 % / +37 %，h1 +34 % / +52 %。xalancbmk 的收益几乎全来自 PC stride（没有数据流步长），libquantum 上 h1 的全局步长（每次缺失连发 8 行）最强。

**修正后的访存组 59 点**（相对 res_final）：

| 配置 | gcc | mcf | libq | omnetpp | astar | xalanc | 几何平均 |
|---|---|---|---|---|---|---|---|
| h1 + Berti | +1.3 | +7.6 | +1.2 | 0.0 | +1.4 | 0.0 | **+1.88** |
| h1 + BC（3 宽 16 项，NOOVL） | +0.3 | +4.9 | −1.8 | +0.1 | +1.3 | +1.0 | +0.92 |
| BC + PC stride + h1 的 LLC 引擎（关 h1 步长） | +0.4 | +10.7 | −8.5 | +0.7 | +1.5 | −1.1 | +0.46 |

结论：修正后 BC 只用 PC stride 作近端时 +0.46 %（修正前 −2.38 %），加在 h1 上 +0.92 %，仍不到 Berti 的一半；差距主要是 libquantum 这类单一大流（h1 / Berti 覆盖得更远）。BC 的间接部分在 mcf 上有效（单点 +2 %）。L2 部分（远端窗口、L2 填充触发）没有移植，是 gem5 上 GAP 收益的主要来源。

### 第二阶段（2026-11-18）：3 GHz、MSHR 16、LLC tree PLRU；BC 的提前量和 BC_UNIFY

**平台改动**（构建参数，模型代码在 `exp/pf-l1l2`）：`CPU_FREQ_MHZ=3000`（CPI 约为 1 GHz 的 1.51 倍）；L1D 和 LLC 的 MSHR 都是 16（`-DCFG_DCACHE_MSHR=16 -DCONFIG_AXI_LLC_MSHR_NUM=16`）；LLC 替换 `LLC_REPL` 默认改成 tree PLRU（`lru` = 时间戳 LRU，`rr` = 原来的"命中路 +1"轮换，即 main）。RTL 的 PLRU、MSHR 16 已记在 [TODO.md](TODO.md)。在这个平台上（相对 3 GHz、MSHR 8、轮换的 h1）：MSHR 16 +7.4 %，再加 PLRU 共 +10.8 %；LLC 用 LRU 在旧平台上 +3.48 %（omnetpp +14 %）；关 h1 的 LLC next-line 引擎 −5 %（但 mcf sp21 上它有害：35.4M → 23.2M 周期）。

**方法**：下面所有数字是新平台、只开 L1 预取（`PF_LLC=0`）、**相对不开预取**（`q_none`），59 点，程序内按权重加 CPI、程序间几何平均。eda 集群，结果 `/nfs_global/S/houruyao/spec06_rv64gc/tm/res_pf43/<配置>/`，脚本 `tm/pf43_one_v20.sh` … `v29.sh`（每次新版本，不覆盖在跑的脚本），比较脚本是会话里的 `cmp43.py`（按权重 CPI）。

**1. 提前量（BC stride 对 h1 / Berti）**：h1 步长 +18.91 %、Berti +6.25 %；BC 逐步改进（30 点 mcf / libq / xalanc）：
- `BC_LATSRC=1`：距离用这条流自己预取请求的实测延迟（发出 → 填充，EWMA），不用全局缺失延迟（被 LLC 命中拉低）。libq 到 +120 %。
- `BC_RAMP=1`（gem5）：流开始 / 跳转时把当前访问到窗口之间的行也发出去（每个新页开头）。
- `BC_PERSRC=1`：周期用这个 PC 在 L1D 的实际访问节奏。
- `BC_NOCUT=1`：不按循环边界截断（边界学错时提前停发；xalancbmk 12.9 → 15.3 %）。`BC_BOUND_BACK`（只从向后分支学边界）、`BC_CONTIG` 被它取代。
- 调 `BC_LATSCALE` / `BC_MAXLA` 基本无效。
- **`PF_RETRY=1` 是 libquantum 的关键**：按页位置统计（`BC_PGH=1`）热点流的每个新行，19 % 是 BC 根本没发出去的缺失，分布在整页，数量与 `probe_mshr_full`（21.6 万）一致——MSHR 全满（预留 0）时探测被丢掉且不重发（NOOVL 的近端指针已经越过）。重发后 libquantum sp25 CPI 0.784 → 0.648（加 PC stride 是 0.745）。h1 用不上 retry（它的突发只在 2 个步长之后，很少碰到 MSHR 满）。

**2. Berti 为什么差**：原版历史表 8 组 × 16 路回溯不到一个延迟（3 GHz 下 320～430 拍），libquantum 90 % 的查找找不到及时的 delta；delta 表只有 16 项，冷 PC 把热点 PC 换出。`PF_BERTI_ALLOC=1`（只有找到及时 delta 的 PC 才分配表项）+ `PF_BERTI_HW=64`（每组 64 路）：libq +2.6 → +122.5 %，59 点 +22.48 %；代价是历史表 128 → 512 项，总存储约 2.5 KB → 4.7 KB（论文的 2.55 KB 是按记忆，未核对原文）。

**3. 统计对比**（`PF_STATS=1`：`[PF-OUT]` 每个来源的去向，`[BERTI-HIST]` / `[BERTI-TAB]` 结构，`[BERTI-WARM]` / `[BC-WARM]` 学习时间；覆盖 = 本来会缺失的行里被预取到的，含 late；按程序权重平均，包含 10M 预热）：

| 预取器 | 覆盖 gcc / mcf / libq / omnetpp / astar / xalanc | 准确率（同序） | 第一次预取前的访问次数 |
|---|---|---|---|
| Berti（16 路） | 2 / 11 / 0.6 / 0 / 7 / 20 % | 55 / 40 / 87 / 57 / 86 / 92 % | 412 ～ 138393 |
| Berti（ALLOC + 64 路） | 4 / 12 / 79 / 0.4 / 8 / 22 % | 48 / 39 / 100 / 61 / 83 / 85 % | 55 ～ 4651 |
| h1 | 1 / 0 / 96 / 0.4 / 1 / 32 % | 40 / 33 / 100 / 21 / 60 / 69 % | — |
| BC + PC stride（下面第 4 项） | 13 / 29 / 96 / 1.2 / 13 / 42 % | BC 18 / 75 / 100 / 7.5 / 33 / 65 % | 2.2 ～ 729 |

Berti 的结构问题：140～860 个 PC 抢 16 个 delta 表项，平均只有 0～4 个 PC 有可用的 delta，256 个 delta 槽最多 8 % 有状态；libquantum 89 % 的查找因为历史窗口短于延迟而落空。BC 覆盖最多、学得最快，但 gcc / omnetpp / astar 上准确率低。

**4. 和 PC stride 的分工、gcc 的指针链**：
- `PF_PCS_UNTAG=1`：PC stride 只训练 BC 没有 stride 标签的 PC（`9bc35dd`）。BC + retry + PCS_UNTAG：+24.25 %（libq +175.7，但 gcc +1.3、Berti +8.9）。
- gcc 的差距全在一个点（sp47，权重 3.2 %，Berti +132 %、BC +4.9 %）：热点 load 在 `fixup_var_refs_insns` / `_insn` / `_1`，沿 obstack 顺序分配的 RTL 链表走——地址来自指针（BC 标签 0 % 仿射、~100 % 链），整体单调向前、步长不定，PC stride 学不到固定步长，Berti 学到 +2/+4/+6/+8 行。
- `PF_PCS_DIR=1`（`3a7e0c7`）：没有固定步长但行号一直同向的 PC，往前发 1～4 行。BC + retry + PCS_UNTAG + PCS_DIR：**+27.46 %**（gcc +7.6、xalanc +20.6）。

**5. BC_UNIFY：标签和采样按 PC 协同**（`c81fb10`、`023668e`）：每个 load PC 一项，两种步长来源共用 BC 的及时距离（延迟 ÷ 周期）：
- **标签步长**：数据流标签给的仿射步长，一开始就可信（置信 2/3）；**按流判断**（PC 第一次访问、或地址跳出一页 / 与标签方向相反算新流）是否变了：相同 +1，不同 −1，到 0 换成新步长、置信 1。
- **采样步长**：同一条流内相邻两次访问的地址差，4 个带计数的步长 + 一个滑动平均和方向置信（针对 gcc 那种同向但步长不定）。
- **使用**：标签可信且本次标签一致 → 标签步长（原 BC 路径）；否则占优的采样步长（计数 ≥ 4 且占一半以上），再否则平均步长（方向置信 ≥ 3）。
- **周期**：链式 load 继承生产者 load 的循环行（`Chain.row`）；`p = load(p + off)`（rd == rs1）的指针递推单独建一行；都没有时用这个 PC 自己的访问间隔。
- `BC_LINECAP=1`：距离只按行封顶（`BC_MAXLA`），不再限 64 次迭代（gem5 的上限，|S| = 1～8 B 时只有 1～8 行；在 mcf / libq / xalanc 上 `BC_MAXIT=1024` 无变化，|S| < 16 的热点 PC 约 10 %）。
- `BC_UFB=1/2`：按 PC 的有用性反馈（采样路径 / 两条路径都管）：每 16 次发出，用上 < 25 % 置信 −1、≥ 50 % +1（0..3，初值 2），到 0 停发，被拦 256 次后以置信 1 重新试探。
- 没有反馈时 omnetpp −20 %（采样路径在 `0x5a1f4` / `0x5a202` 等 PC 上发 190 万次、准确率 3 %，几乎每次访问都是"新流"，每次都 ramp）。

| 配置（相对不开预取） | gcc | mcf | libq | omnetpp | astar | xalanc | 几何平均 |
|---|---|---|---|---|---|---|---|
| h1 步长 | +0.99 | −0.00 | +139.15 | +0.03 | +0.66 | +16.23 | +18.91 |
| Berti（16 路） | +8.90 | +5.94 | +2.57 | −0.10 | +4.87 | +16.04 | +6.25 |
| Berti（ALLOC + 64 路） | +10.28 | +6.17 | +122.52 | +1.69 | +6.04 | +20.18 | +22.48 |
| BC + retry + PCS_UNTAG + PCS_DIR | +7.63 | +10.52 | +176.04 | +1.60 | +6.60 | +20.60 | +27.46 |
| BC_UNIFY（无反馈） | +8.61 | +24.52 | +174.62 | −20.17 | +1.95 | +18.89 | +23.76 |
| BC_UNIFY + LINECAP + UFB=1 | +13.16 | +21.94 | +175.03 | +0.65 | +12.62 | +28.88 | +33.04 |
| **BC_UNIFY + LINECAP + UFB=2** | +12.98 | +21.94 | +175.43 | +0.51 | +12.66 | +29.27 | **+33.08** |

当前最优（不需要单独的 PC stride，也不需要 h1）：`PF_STRIDE=0 PF_LLC=0 PF_BC=1 BC_NOIND=1 BC_TQ_W=3 BC_TQ_N=16 BC_NOOVL=1 BC_RAMP=1 BC_LATSRC=1 BC_PERSRC=1 BC_NOCUT=1 PF_RETRY=1 BC_UNIFY=1 BC_LINECAP=1 BC_UFB=2`。gcc sp47 CPI 1.745 → 0.502（Berti 0.751）。最差点 xalancbmk sp41 −3.5 %（UFB=1 为 −7.7 %）。

### 第三阶段（2026-11-18～19）：BC_CORE，删掉补丁只留核心

**起因**：第二阶段的最优配置叠了十几个开关（LATSRC、RAMP、PERSRC、NOCUT、RETRY、PCS 系列、UNIFY、LINECAP、UFB……），多数是遇到问题时加的新机制，而不是改出问题的那条规则（例如有用性反馈其实是在掩盖采样步长的置信度从不下降、每条流开头无确认就 ramp）。按"每件事一条规则"重写成 `BC_CORE=1`（`fc05c5d`）：
- **标签**：每个架构寄存器只存 {仿射, 步长}；`addi rd==rs1`（同一条指令）是归纳，`addi / slli / add / shNadd / add.uw / sub` 传递或缩放唯一的仿射操作数，其余写清标签。`r = r + rX` 不打标签，交给采样步长。
- **流**：每个 load PC 一项：上次 VA 和时间、周期 = 访问间隔 EWMA、采样步长 = 地址差 EWMA；有标签步长用标签，否则用采样。
- **距离**：D = ⌈延迟 ÷ 周期⌉；|S| < 64 B 按行、否则按步长，上限 `BC_MAXLA`=16；延迟 = 全局 DRAM 缺失延迟（≥ `BC_CORE_LATMIN`=120 拍、不含合并进在途行的缺失）。
- **前沿**：一条规则代替 RAMP + NOOVL：每次触发发出 max(前沿, 当前) 之后到 当前 + D + W − 1 的单元，流开头自然从当前位置铺满，稳态每次一个。窗口宽度 W = clamp(2 × 步距离散度 EWMA, `BC_DEG`=4, 16)，跳出窗口（两侧）就从当前访问重启前沿。
- **置信度 = 有用性**（0..3）：预取行第一次被需求用到 +1，未用就被 L1D 换出 −1（L1D 换出钩子）；≥ 2 发整个窗口，1 每次一个单元，0 每 `BC_CORE_PROBE` 次触发试探一个单元。窗口命中置信度试过（两侧命中、按离散度定宽、向后中性）分不开 gcc 有用的不规则前进和 omnetpp 的随机 PC，换成有用性后 gcc sp47 CPI 1.09 → 0.571。
- **`PF_HOLD=1`**：所有 MSHR 都占满时预取队头在 FIFO 里等（反压），代替丢弃 + `PF_RETRY`；第 2 级抢不到最后一个 MSHR 的探测重新入队。

| 配置（相对不开预取） | gcc | mcf | libq | omnetpp | astar | xalanc | 几何平均 |
|---|---|---|---|---|---|---|---|
| UNIFY + LINECAP + UFB=2（第二阶段最优） | +12.98 | +21.94 | +175.43 | +0.51 | +12.66 | +29.27 | +33.08 |
| **BC_CORE，试探 1/16** | +11.53 | +12.88 | +183.81 | −0.99 | +10.61 | +22.41 | **+29.83** |
| BC_CORE，试探 1/64 | +10.73 | +10.11 | +184.04 | −0.10 | +9.48 | +18.72 | +28.47 |

配置：`PF_STRIDE=0 PF_LLC=0 PF_BC=1 BC_CORE=1 BC_TQ_W=3 BC_TQ_N=16 PF_HOLD=1 BC_CORE_PROBE=16`（脚本 `tm/pf43_one_v36.sh`，二进制 `tm/bin/sim64_pf43z16`）。libquantum 比复杂版好（HOLD + 全局 DRAM 延迟），gcc 基本追平且超过 Berti；差距在 mcf（12.9 对 21.9）、xalancbmk、astar。没验证的嫌疑：mcf 的 `r = r + rX` 交给采样路径后接不住；周期只用 PC 访问间隔（复杂版来自循环行 / PERSRC）；有用性置信度起步慢。试探 1/64 让 omnetpp 回到 0 附近，但其他程序有用 PC 重学变慢。

**硬件评估**：难点有三：翻译（模型用 1024 项 VA→PA 页映射，仍有 4～64 % 的候选翻译失败）；按 PC 的表无上限（每点 600～4000 个 PC）；有用性要每行元数据（约 7 位 × 1024 行）。其余（标签、前沿、距离计算）规模不大。

**还没做 / 待查**（2026-11-19 探索暂停）：BC_CORE 在 mcf / xalancbmk / astar 上的差距（先按 gcc 的方法找出错的规则，再原地改）；omnetpp 约 −1 %；BC_CORE 采纳后删掉旧开关（UNIFY、UFB、LINECAP、PCS 系列、RAMP、RETRY 等）；xalancbmk sp41 的损失原因；BC 的间接部分和 L2 部分在新平台上没有重新评估；表的规模和面积（按 PC 的统一表、采样步长、行号继承）没有按硬件定；RTL 未做。

## EXP-042 RTL 时序：TLB 口并行化、first_set 对数深度

**起因**：综合报告（`rtl/docs/09-synthesis-report.md` 第 10 节）里 `tlb_mmu` 深度代理 159/163 级，用户指出 TLB 没有并行。最长路径：lane 0 查表 → 64 位 `ttg_first_set`（`req & -req` 进位链）→ 8 个口的 `chain` 依次串过去。

**做法**（rtl `exp/tlb-par`，只改 RTL 结构，不改周期）：
- `tlb_mmu_core` / `tlb_mmu_lane`：参考模型 `top_comb` 是口 0→7 依次调用 `core_comb`，但一拍里能改共享状态（walk、回填、PTW 请求/响应）的口最多两个——A（第一个在当前 walk 页上缺失的口：发请求或消费响应/退休 walk）和 B（walk 空闲或被 A 退休后第一个缺失的口：启动新 walk）。各口并行算好自己的缺失/同页/权限和两种回填视图下的结果，A、B 各用一个 8 位 first_set 选出（B 对三种情况预选），选择信号只控制末级二选一。
- `ttg_first_set`（公共原语）：`req & -req` 改为 Kogge-Stone 前缀或，函数相同，37 个模块受益。
- 设计说明：`rtl/docs/modules/tlb_mmu.md` 第 2 节、第 3 节第 6 条。

**验证**：
- `rtl/tests/tlb_par/run.sh`：旧串行核心（原样保留为 `tlb_mmu_core_ref`）与新核心并排，随机输入逐拍比较全部输出（DTLB 8 口 + ITLB 1 口，`ENTRIES=8`），rv64 300 万拍、rv32 配置 500 万拍 0 不一致；覆盖计数：同拍退休 + 新 walk 约 1.7 万次、A 之后的口用 A 的回填约 3 千次、退休出错约 2 万次、多口同页约 7.5 万次；3 个人为变异都被抓到。`ttg_first_set` 在 N=1/3/7/8/13/64 上与 `req & -req` 比较 0 不一致，`make prims` PASS。
- `lint.sh` 输出与 main 相同，`lint_chip.sh` 0 警告。
- 整芯片 fm_gate（rv64，67 个程序）：67/67 逐条对 function-model 一致，周期与 `scripts/ref_cycles.txt` 0 处不同。
- Linux 窗口（`scripts/linux_segments_cmp.sh`，s03/s07/s11，各 400 万周期，RTL 对 trace-model main `5b95b35`，function-model main `55affa0`（`RVC=1`））：**3/3 PASS**，逐条对 function-model 0 不一致（585.7 万 / 536.2 万 / 272.8 万条提交），PT/UP 指纹与 trace-model 相同；同一环境下 rtl main（`8abb7ab`）也 3/3 PASS，且两者的 rtl.out / rtl.err **逐字节相同**。
  （先前用 `drop32/function-model`（`d12be0c`）构建的测试平台，三个窗口都在第 94949 周期报不一致，rtl main 也一样；换成 function-model main 后消失，是检查器版本问题，与 RTL 无关。）

**综合（深度代理，rv64）**：`tlb_mmu` 163 → 67、单元 84,088 → 80,255；`tlb_mmu_lookup` 61 → 33；`icache_itlb` 68 → 49；first_set 的其他用户 `lsu_stlf_match` 139 → 97、`isu_iq_select` 69 → 46、`isu_alloc_chain` 72 → 55（面积 +1.5k）、`bpu_main_sel` 121 → 113。完整表见 `rtl/docs/09-synthesis-report.md` 第 11 节。

**合入**：rtl main 快进到 `261bd67`（另含测试平台自带 `fpr.h` 和构建提速），说明见 [RTL_TLB_PAR.md](RTL_TLB_PAR.md)。

**剩下的**：TLB 最长路径现在是查表（约 33 级）→ A → B → `walk_q`，A→B 是语义依赖；再降要改周期（查表打一拍等），未做。

## EXP-040 rv64gc Linux 的 RTL 与 trace-model 逐周期对齐

- **状态：2026-11-16 已合入本地 main（带已知误差）**（trace-model `exp/rvc-carry`、rtl `exp/rvc-rtl`、function-model `exp/fm-forced-pf`）。**已知误差：从复位的 Linux 在约 3000–3050 万周期起 PMU 区间与 RTL 不同（提交指令数 +0.29%），没有查原因。**
- **问题**：rv64gc（`RVC=1`、`FP=1`）的 Linux 在 RTL 上能启动、逐条对比 0 不一致，但与 trace-model 的周期不同；要合入 main 必须逐周期相等（[WORKFLOW.md](WORKFLOW.md) 第 1 节）。
- **方法**：不比周期总数，比「事件在哪个周期发生」。`FPR=<bin>`：PTAB 写入流（PT）和预测器更新流（UP）每 bin 的个数加可交换哈希，trace-model 与 RTL 测试平台用同一份 `fpr.h`；第一个不同的 bin 用 `FPR_DUMP=<起>:<止>` 展开原始事件，再用 `SOC_TB_VCD` 抓 RTL 那几十个周期的波形、`vcd_query.py` 按层次名查信号，模型一侧在对应函数里加临时打印；定位后删掉打印。长程序先用 `scripts/linux_segments_cmp.sh`（每 1000 万条指令一个检查点，RTL 与模型从同一个检查点冷启动，各跑同样的周期数，约 15 分钟出 18 个窗口），从复位的 140M 周期 gate 留作最后确认。
- **查出并修掉的问题**（按发现的先后）：
  1. 测试平台 `EVAL` 顺序：先读 `env_rd_en` 后稳定 `env_modeled`，Linux 偶尔卡死。
  2. MDP 等待表索引写死按 4 字节（`pc[2+B-1:2]`），`RVC=1` 是 2 字节对齐（`SLOT_SHIFT`），真实的 load 时序差 3 周期。
  3. 三个 32 → 64 位的错误，只在符号扩展的物理地址（`0xffffffff80…`）上暴露：历史哈希符号、uBTB 目标展开（高位应取块基址）、预译码目标类型。这三处之后 UP 流在 150 万周期内逐位相同。
  4. 旧值路径（EXP-020）只对 rv32：`MsData.h` 的 ALU / 乘除 / load 扩展、STQ 的 `m_*` 字段、旧数据转发都改成 XLEN 位。
  5. **页错误的 load 把出错地址写进 rd（RTL）**：体系结构上 rd 不变；错误路径上依赖它的 load 会用这个地址访存，模型取功能模型的值不会，页表遍历和缓存内容分叉（第 4,012,380 周期）。RTL 改成不写、不唤醒（照 store-conditional 页错误的写法），模型同步。
  6. **store 的基址寄存器来自读到旧值的 load 时，数据写到旧地址**，之后在真地址上读到旧内存；模型的 `LSU_MS_DATA` 第 2 位（污染地址）原来默认关，默认改成 7。
  7. **FS=Off 时的错误路径 FP 访存**：trace bridge 对访存指令先查对齐，不对齐就标 `blocked`（不执行），绕过了 FM 的非法指令 trap；RTL 在 `FS=Off` 时把它标成需要冲刷的条目，ROB 通知发射级停住，两边的发射停顿不同（第 4,175,850 周期）。FP 访存在 `FS=Off` 时不再走 `blocked`，交给 FM trap。Linux 的惰性浮点（进程没用过浮点时 `FS=Off`）下，预测错误的路径会走进浮点上下文保存代码。
  8. **旧值污染表泄漏**：污染表只在 ROB 冲刷时整体清空，分支误预测冲掉的错误路径生产者留下的污染会泄漏给寄存器的下一个持有者（检查点 `s45` 第 1,972,774 周期，`p108`）。物理寄存器新分配时清污染；MMIO / LR-SC / 页错误 load 的写回也清；旧值地址对 FP 访存补上立即数（`0x07` / `0x27`）。
- **结果（合入时）**：从复位的 Linux 到约 3000 万周期逐区间相同（400 万、417.6 万周期附近的 167,047 个 25 周期区间全相同），**3000–3050 万周期起有误差（见上）**；rv64gc Linux **18 个检查点窗口 18/18**（用最终修复之前的模型跑的，最终版本没有整批重跑）（每窗 200 万周期，PT / UP 指纹 1998 个 bin 全部相同，逐条检查 0 不一致）；从复位对齐到 450 万周期；rv32 `RVC=0` 的 `fm_gate.sh` 64/64、周期与新模型和 `ref_cycles.txt` 逐个相同，新旧模型 64 个程序周期逐个相同；rv64 directed 3/3。
- **走过的弯路（避免重复）**：
  - 把模型的 stderr 通过管道再接 `grep` 会**丢行**，表现成「模型每次结果不同」；写到文件就逐字节确定。比对指纹一律先写文件。
  - 检查点模式下 trace-model 的 `-c` 是**指令数**不是周期数：高 IPC 的窗口模型提前停，指纹只比了前几百个 bin。要用 `SIM_MAX_CYCLES` 限周期。
  - 检查点恢复程序放在非 RAM 的启动窗口（0x0），RTL 取指很慢（约 100 周期一条，恢复约 26k 周期），模型约 18k 周期；PMU 区间按绝对周期切所以错位，窗口检查只比 PT / UP（它们从恢复结束后开始数周期）。
  - 一度怀疑「模型不会算旧值」：其实 EXP-020 早就有，只是只对 rv32 打开；扩到 rv64 之后大部分差异直接消失。
- **未覆盖的风险**：窗口是冷启动，不能替代从复位的完整 gate；rv32 `RVC=1`、rv64 `RVC=0` 没有整表；SPEC 没跑；PMU 区间（绝对周期）在检查点窗口里没比。
- **复现**：`TM_DIR=<trace-model> FMLIB=<rv64 gc 的 librefcpu.a> bash scripts/build_soc64_linux.sh <目录>` 构建 RTL；`bash scripts/linux_segments_cmp.sh <soc_tb> <trace-model 的 simulator> <检查点目录> <输出目录> 2000000`；从复位：`bash scripts/linux_gate.sh <soc_tb> <simulator> <linux64gc.bin> 140000000 <输出目录>`。rv64 directed：`REF_CYCLES=scripts/ref_cycles_rv64.txt bash scripts/fm_gate.sh <soc_tb> <输出目录>`。

## EXP-038 C 扩展：trace-model 前端按半字取指

- **状态：2026-11-13 进行中；S0–S2 和变慢程序的修复已快进合入 trace-model `main`（`74e6827`）并推送；工作区 `trace-model-rvc`（分支 `exp/rvc`）。** function-model 侧见 EXP-037（已合入 main）。
- **设计依据**（读了香山 [IFU](https://docs.xiangshan.cc/projects/design/en/latest/frontend/IFU/) / [PreDecoder](https://docs.xiangshan.cc/projects/design/en/latest/frontend/IFU/PreDecoder/) / [FTQ](https://docs.xiangshan.cc/projects/design/en/latest/frontend/FTQ/) 文档和 `PreDecode.scala`、`IBuffer.scala`，以及 BOOM 的取指和分支预测文档）：
  - 预测位置：2 字节一个（香山 32B 块 16 个位置；BOOM 按 `fetchWidth*16` 位的取指包）。我们把 slot 宽度参数化：`RVC=1` 时 slot 是 2 字节、每块 16 个位置，`RVC=0` 仍是 4 字节 8 个位置。
  - 跨界的 32 位指令：采用香山的约定，归起始所在的块；取 34B（17 个半字），后半条同拍可见，下一块用 `lastHalf{valid, middlePC}` 作废自己的第 0 个位置，不多一次取指；BOOM 是归含高 16 位的包、F3 带状态多拍拼接，不选。
  - 块起点在 64B 行的后半时 I$ 取两行拼接（BOOM 不支持跨行）。
  - 取指缓冲按指令存：最多 16 条进、`PopCount` 压缩、每拍最多 DecodeWidth 条出、空时旁路、剩余空间容不下一整块就不接收。
  - 预测校验两级：F3 级对 jal / jalr / ret 截断范围；写回级查「预测 taken 的位置不是指令起点」「非跳转被预测 taken」「目标不符」。顺序目标 `pc + (isRVC ? 2 : 4)`。
  - 没查到的：香山 FTB 的分支槽数和偏移编码、跨行气泡周期数、RAS 返回地址规则、译码宽度、BOOM 的 FTQ 字段。
- **步骤**：S0 后端和 bridge 的长度通路（周期不变）；S1 slot 宽度参数化、16 个半字位置（BPU 数组、FTQ 偏移宽度、PTAB）；S2 I$ 取 17 个半字、两行拼接、预译码边界链和 `isRVC`、`lastHalf`；S3 按指令的环形取指缓冲；S4 预测校验两级和 RAS 带长度；S5 PMU 和带 C / 不带 C 的对比。`FE_PAIR` 先与 RVC 互斥。
- **S0 做了什么**：`RVC` 编译开关（默认 0，需要 `RVC` 一致的 `librefcpu`）；每条指令 1 位 `is_rvc`，从前端输出经 FTQ 的 slot、uop、ROB 广播一路带到后端；后端所有 `pc+4`（分支解析的预测目标和 `diag_val`、JAL / JALR 的链接值、flush 后重取地址、MsData、FTQ 的配对判断、提交时训练的目标）改成 `pc + ilen`；`Bridge::dispatch` 带长度，`Fact.len`，不执行或 trap 撤销时的 `pc+4` 改 `pc+len`；`FastWarm` 用单步的 `inst_len`。前端各 lane 的 `is_rvc` 仍恒为 0（S2 才产生）。
- **验证**：`RVC=0` gate 64/64 周期与基线逐个相同；`RVC=1`（function-model 也带 C）能编译，非 C 的测试 61/64 与基线相同，3 个不同是 C 的语义（`jalr` 只清第 0 位、`medeleg[0]`）：`itt-dispatch`、`load-store-aligned`、`supervisor-illegal-delegation`。
- **S1 做了什么**（2026-11-13）：`config.h` 里 `FETCH_BYTES`（32）、`SLOT_SHIFT`、`SLOT_BYTES`、`FETCH_WIDTH = FETCH_BYTES / SLOT_BYTES`（`RVC=0`：8 个 4 字节 slot；`RVC=1`：16 个 2 字节 slot），`BPU_BANK_NUM = FETCH_WIDTH`；BPU（`BPU.h`、`BPU_pipe.h`）里所有 slot 与 pc 的换算、预测表 / BTB / uBTB / TAGE 的索引移位、块边界、`FE_PAIR` 的位置计算都改用 `SLOT_SHIFT` / `SLOT_BYTES`；前端各 slot 的 pc；I$ 每行的 slot 数和按半字对齐的取指窗口 `tbhook::fetch_window_at`。`RVC=0` gate 64/64 周期不变；`RVC=1` 能编译（`FETCH_WIDTH = 16`）。
- **S1 的范围调整**：原计划 S1 里让 `RVC=1` 先跑不带 C 的程序，实际上做不到：前端有多处假定有效 slot 是连续前缀（`sequential_next_pc`、预译码检查器的分段、`multi` 判断、FE_PAIR 的顺序检查），半字 slot 下奇数位置是空的，必须和 S2 的预译码边界逻辑一起改。所以「`RVC=1` 能运行」移到 S2。
- **S2 做了什么**（2026-11-13，`5bd7a75`）：
  - 预译码：对每个 slot 的 32 位窗口判断是否 16 位（低 2 位不是 11）并展开（`function-model/include/rvc.h`，非法编码变成 0）；展开后的字当作该 slot 的指令字做类型和目标预译码。
  - 指令起点：写入指令 FIFO 时算两条链，`start_a`（slot 0 是一条指令的起点）和 `start_b`（slot 0 是上一组最后一条指令的后半，从 slot 1 起），每个 slot 另存 `is_rvc`；读到队首时按 `lastHalf` 状态选链。
  - `lastHalf`（香山的做法）：一条 4 字节指令起始于本组最后一个 slot，则它属于本组，下一组（起点等于本组的块尾、顺序取指、没有 taken 分支、没有预译码 flush）的 slot 0 作废；状态在 flush / refetch 时清除。
  - 有效 slot 允许有空洞：非起点的 slot 变成 `NON_BRANCH`，BPU 在非起点位置预测 taken 会被预译码检查器当成需要 flush 的错误；`is_rvc` 经 front2back FIFO 到后端；I$ 每行 slot 数、单字取指（MMIO）当作两个 slot；uBTB 的 slot / 目标字段宽度随 slot 宽度。
  - 诊断开关（只打印，不影响周期）：`RVC_DBG`（预译码 flush 的原因）、`BPU_OVR_DBG`（S0 与主预测目标不同的情形）。
- **S2 验证**：`RVC=0` gate 64/64 周期不变；`RVC=1`：64 个不带 C 的程序都跑完，0 个 TB_CHECK 不一致，周期与 `RVC=0` 相差约 ±5%（最大 +9.7%：`trap-precise-store`，来自 C 的语义）；cpu-tests 带 C 编译（`rv32imac`）62 个里 58 个通过，不通过的 4 个是测试源码假定 4 字节指令（`interrupt-vectored`、`software-interrupt-vectored`、`supervisor-external-interrupt-vectored`、`trap-precise-store`）；function-model 的 `gen_rvc.py` 生成的测试（`rvc-alu` 589,886 条、`rvc-mem`、`fd-rvc-mem` 各约 300 万条、`rvc-flow`、`rvc-straddle` 跨行跨页）全部通过、0 不一致。过程中查出两个遗漏并修了：I$ 每行 slot 数还按 4 字节算、uBTB 的目标字段只有 30 位（目标取到 31 位后高位丢失，造成 S0 与主预测目标不同的大量 override）。
- **变慢的程序**（52 个同源程序，C 编译 + `RVC=1` 对 不带 C + `RVC=0`，周期比）：第一版几何平均 0.975，个别明显变慢：`itt-dispatch` 1.72、`pascal` 1.62、`recursion` 1.38。查到的原因（`exp/rvc` 的后续提交）：
  - BPU 的训练和 RAS 路径还在用 `pc+4`：uBTB 的块跟踪器用 `pc+4` 当下一条指令的地址，压缩指令一出现跟踪器每条都重置，S0（uBTB）一次都没命中（`s0_hit=0`），每个 taken 分支都要等主预测器 override；架构 RAS 和推测 RAS 压栈、分支误预测后的修复也用 `pc+4`，压缩的 call 的返回地址错，`recursion` 变慢。
  - 修法：训练输入带每条提交指令的长度（`update_is_rvc`、`rf_is_rvc`），跟踪器、RAS、修复都按长度；类型预测器和 uBTB 项记住 call 是不是 16 位指令（预测时 RAS 压栈 `pc+2`）；预热回放也传长度。
  - 还有一处：一条 4 字节指令跨块尾时，跟踪器把下一块的起点记成指令末尾（`nxt`），而取指侧下一块从块尾开始（`lastHalf` 把块头半个字作废），uBTB 的项按错误的块起点存，`memory-stress-small` 里一个内层循环的 S0 一直不命中（override 2 万次，+8.6%）；改成跟踪器的块起点取块尾、期望的下一条指令地址仍是 `nxt`。
  - 结果：几何平均 0.975 → 0.920（C 编译 + `RVC=1` 比不带 C + `RVC=0` 少 8% 周期）；最慢的是 `pascal` 1.16（3141 条指令、2134 周期，冷启动占大头：同一个循环从 `0x5e` 和 `0x60` 两个块起点进入，各自单独学习）、`memory-stress-small` 1.03。`RVC=0` gate 64/64 不变；5 个定向压力测试仍 0 不一致。
- **Linux 与回归**（2026-11-13，已合入 trace-model `main` `538a0b1`）：
  - **EXP-036 的回归**：trace-model 跑 rv32 Linux 时内核在 `kdevtmpfs` 里 NULL 解引用（预 C 的 `195dad4` 也一样）。二分到 `067f02e`（拷贝优化）：`Bridge::find` 的二分查找假定链按 uid 有序，重做 / 重放之后并不总是有序，丢了事实；`BRIDGE_FIND_CHECK` 报 “线性找到、二分没找到”。修法：二分没找到时用线性扫描确认。教训：EXP-034…036 合入时只跑了 gate 和大程序，没有跑 trace-model 的 Linux（`WORKFLOW.md` 要求合入前必跑）。
  - **`lastHalf` 的一个遗漏**：C 内核在 `pc=c00044b4`（`auipc` 的中间）报非法指令。原因：一个预译码 flush 的修正目标正好是本组的块尾（顺序继续）时，我把 `lastHalf` 清掉了，重取的组就从跨界指令的后半条开始解码。修法：顺序继续的预译码 flush 保留 `lastHalf`，flush 之后的重取周期不清。
  - **结果**：rv32 Linux 从复位到 `rv32 login:`（2 亿周期上限内）：不带 C 的镜像在 `RVC=0` 和 `RVC=1` 上、内核和 OpenSBI 带 C 的镜像在 `RVC=1` 上，都 0 个 oops；`RVC=0` gate 64/64、C gate 62/62 不变。`misa.C` 在 trace-model 的 CSR 文件里也补上了。
  - **rv64**：`RVC=1` 的 rv64 构建，rv64 的 C 和不带 C 的 cpu-tests、`gen_rvc.py` 的 rv64 压力测试（含 Sv39 第二半字缺页 `rvc-sv39`）0 不一致。rv64 Linux 在 trace-model 上原来起不来，现在 rv64g（不带 C）和 rv64gc（内核和 OpenSBI 带 C）都到了 `rv64 login:`，`fptest: PASS`，0 个 oops（`cb66f96`）。查到并修掉的 32 位残留：
    1. BPU 的块边界用 32 位算、uBTB 的目标只存低 32 位（内核虚拟地址高于 2^32，块 bank 端口检查报错退出）；
    2. 分级 LSU 的 LDQ / STQ 里 `vaddr` 是 32 位：内核访问高地址时地址被截断，一个 store 页错误反复触发（约 83 万次）；MMIO 读结果 `result` 也改成 `XLEN` 宽；
    3. `LSU_MS_DATA` 的旧值模型整个按 32 位值计算，对 rv64 不成立：rv64 上关掉（rv32 不变）——这是 OpenSBI 之后内核几乎不运行、`rdtime` 模拟占 99% 时间的原因；
    4. `ftq_slot_pc` 返回 `uint32_t`（BPU 误预测修复的块内位置比较对高地址永远不成立）、预译码检查器里 `PdInfo` 的 `pc` 是 `uint32_t`（RAS 压栈值和历史符号被截断）。
    复查后还剩的 32 位字段：LSU 里按字（32 位）做的 store-to-load 转发（`LSU_MS_DATA`，rv64 已关）、DCache 写数据 `wdata`（物理侧字宽接口，rv64 的 `sd` 拆成两个字）、预测器索引用的 `st_pc` / `ldq_pc`（只影响哈希）、`FastWarm` 的 Sv32 页表遍历（只在快速预热模式用，rv64 不支持）；这些目前不影响功能，没有改。
  - **跨缓存行 / 跨页取指（2026-11-13）**：
    - 现状核对：I$ 响应的一组在行尾截断（`base_idx + i >= 行字数` 的 slot 无效），只有行内最后一个半字起头的 32 位指令，其高半字在下一行；这条指令随本组送出，高半字用 `fetch_window_at` 从功能内存直接读。时序上相当于香山「一次读两行、两行同拍可见」，命中时没有额外周期（与设计依据一致）；下一行缺失时，缺失延迟由下一组承担，这条指令只是早到，不改变后面指令的等待，所以没有加第二行的缺失模型（I$ 模块是单行状态机，改成双行请求风险大、预计对 IPC 没有可测影响；这是估计，没有测）。
    - 查出并修掉的真问题：高半字按「物理相邻」读，**跨 4 KiB 页时下一虚拟页的物理页不是相邻的**，前端取到的字和 function-model 执行的字不同（实测：Sv32 下 `addi a0,a0,1` 的高半字读成 `ffff`，译码成了另一条指令）。差异原来没有任何检查能发现（bridge 只用 function-model 的事实）。修法：`ICacheTop` 里组到达页尾时，用 ITLB 只读查询、不命中则用软件页表遍历（`soft_walk_fetch`，Sv32 / Sv39，检查 V/R/W/X/U/A）取下一页的物理地址，高半字从那里读；不可映射时高半字读 0（function-model 会报取指缺页）；`FE_PAIR` 第二块的窗口越过页尾时不供给。**时序上仍是乐观的**：下一页的 ITLB 缺失 / 页表遍历不占周期（跨页的straddler 只占行尾指令的约 1/1000 以下，没有量化）。
    - 新检查：bridge 在每条指令提交时比较前端取到的字和 function-model 执行的字（`[TB_CHECK] bridge inst_mismatch=`，非零时打印前 8 条）；wrong-path 上数据被当成指令取的差异不计（在派发时比较会误报，改到提交时比较）。
    - 新测试 `rvc-sv32`（`gen_rvc.py` 的 `gen_sv()` 把 sv39 版推广到 rv32，并在两页之间放一页 `ffff` 诱饵页，物理上不相邻）：修前 `inst_mismatch=2`，修后 0；加进 `run_gate_c.sh` 和 `baseline_c.csv`（2516 周期）。`RVC=0` gate 64/64、C gate 63/63（`rvc-sv32` 加入后）、rv32c Linux 到登录 0 mismatch。
  - **RVC 边界测试（2026-11-13）**：
    - `tests/rvc/rvc-fencei`：代码按半字逐个偏移（跨 64 B 行边界）改写成 32 位 / 16 位 / 32 位 jalr 三种形式，每次改写后 `fence.i`，各执行一次；`tests/rvc/rvc-irq`：软件中断（程序写 `mip.MSIP`）在一串全部落在 2 mod 4 的 32 位指令流的 16 个不同位置被取，handler 清中断后 `mret`，要求计数 16、累加和精确（不丢不重）。rv32 和 rv64（`build64c`）都通过，`inst_mismatch=0`，0 TB_CHECK 不一致。
    - 发现 simulator 不看 `main` 的返回值，`check()` 失败也打印 `Success!!!!`（负对照：返回 1、或把期望和改错，仍然 `Success`）。这两个测试自己在 UART 上打 `RVC_TEST_PASS` / `RVC_TEST_FAIL`，`run_gate_c.sh` 检查；`rvc-irq` 的负对照（期望和改成 761）正确报 FAIL。
    - 限制：I$ 模型不存数据（取指字从功能内存读），所以去掉 `fence.i` 的负对照 `rvc-fencei` 仍然通过：它检查的是改写后的压缩代码在前端 / bridge / function-model 之间的一致性，不检查 I$ 失效本身；`fence.i` 的时序影响不在测试范围。
    - 没做：MMIO 单字取指（I$ 里 `paddr < 0x40000000` 走单字路径，但平台上该区间没有可执行内存，测试程序和 Linux 都在 `0x80000000` 以上，不可达）；Sv32 第二半字缺页已由 `rvc-sv32` 覆盖（V、非 X、无效、U、A=0 等变体）。C gate 现在 65/65。
  - **FE_PAIR 与 RVC（2026-11-13，已完成，默认仍关）**：原来 `RVC=1` 开 FE_PAIR 直接报错退出。改动（`front_top.cpp`、`predecode_checker.*`；BPU 和 FTQ 原来就是按槽位参数化、带每槽 pc，不用改）：
    - 指令起点链按块分段：每个块的第一个槽是起点；一个块最后的 32 位指令（窗口已完整）不会连进下一个块的第一个槽。
    - 多块预测校验改成按显式块边界（`grp_seg_first`）和指令长度（`is_rvc`）分段；非起点槽（32 位指令的高半字）算组内但不是指令；一个块的顺序续接是它最后一条指令之后。顺序下一 pc 都用「最后一个槽之后的位置」。
    - **查出的 bug**：lastHalf（组尾 32 位指令的高半字留给下一组）原来在「组里有任何预测 taken」时作废，pair 组里第一个块以 taken 分支结尾是正常的，只有最后一个块的 taken 才说明取指不再顺序继续。症状：带 C 的 Linux（`FE_PAIR=1`）下一组的第 0 个槽被当成指令起点译成垃圾，函数模型跟着执行到 `_start_hang` 的 `wfi` 里空转，TB_CHECK 全是 0 不一致。
    - **为什么原来的检查没发现**：function-model 是被前端驱动的，不是独立的答案；cpu-tests 的 `check()` 失败也不会让 simulator 报错；所以 0 不一致不能证明前端走对了路。新检查：`TB_PCTRACE=<file>` 记录提交的指令流，`scripts/stream_cmp.sh` 对两种配置比较（架构上的指令流不应该依赖前端时序），`scripts/run_pair_c.sh` 对所有 C 程序比较 `FE_PAIR=0` 和 `1`：60 个程序流完全一致；`interrupt-vectored` 等依赖中断时机的除外（流本来就会不同）；rvc-alu 49 万、pf-stress 87 万条提交一致。Linux 的流在约 1000 万条提交之后因为定时器中断位置不同而分叉，是预期的，所以 Linux 只看启动结果。
    - 结果：默认（`FE_PAIR=0`）周期不变，gate 64/64、C gate 65/65；`FE_PAIR=1`：rv32c Linux 在约 9000 万周期到登录（不开 pair 约 1 亿）、rv64gc 到登录（1.4 亿，不开 1.3 亿，计数粒度 1000 万），0 oops、0 不一致，`inst_mismatch=0`；19 个周期超过 3000 的 C 程序几何平均周期 −1.1%（itt-dispatch −18.6%，goldbach +7%，prime +5%）。
    - 局限：RVC 没有 SPEC 检查点，所以没有 EXP-023 那样的 SPEC 收益数字；Linux 启动的 IPC 受空转循环影响大，不能当性能数字。
  - **I$ 第二行（2026-11-14，为 RTL 做的，已合入 main）**：原来行尾最后一个半字起头的 32 位指令，其高半字在下一行，模型直接读功能内存、不要时序，真实 I$ 做不到，RTL 也没法与模型逐周期相等。改成香山式、按需：请求的组到达所在行的最后一个半字、且该半字低两位是 11（可能是 32 位指令的开头）时，需要下一行的第一个半字。
    - 下一行（同页）已在 I$ 里：照常应答（第二个 tag 读口命中）。不在，或在下一页：不应答，已登记的请求变成两阶段请求——先把「下一行」当作一次普通请求（同页：直接填它，走原来的缺失通道；跨页：先翻译下一页，再按普通请求查它的第一行），不回应；下一行到位（命中、填完或页缺页）后用保存的原 pc（`xl_pc_r`）重放原请求一次（`xl_done_r` 跳过检查）。刚填完的行如果还需要它的第二行，也不直接应答，而是重放。
    - 下一页的翻译结果（`xl_ppn_r` / `xl_fault_r`）给取指窗口的高半字用；原来用的软件页表遍历删掉了。
    - 周期变化：带 C 的小程序多几个到几十个周期（冷启动时行尾指令要等下一行，如 `add` 1223 → 1270、`quick-sort` 3590 → 3636），新基线 `baseline_c.csv`；`RVC=0` 不受影响（gate 64/64）。`[ICACHE_XL]` 统计（rv64gc Linux 启动 1.7 亿周期）：候选请求 399,629 次，其中转换成两阶段请求 375,027 次（下一行缺失 218,878、下一页 156,149）。跨页的转换占比高（约 40%）：内核代码里行尾 / 页尾的 32 位指令不少，每次都多一次下一页的翻译加重放，这是这个设计的主要时序代价，还没量化它对 IPC 的影响。
    - 验证：C gate 65/65（新基线），55 个 C 程序的提交指令流与改前一致，所有 C 程序 `inst_mismatch=0`，rv32c / rv64gc Linux 到登录。
    - RTL：`rtl-rvc` 分支 `exp/rvc-rtl`（R2a，`RVC=0` 的 lint 0、gate 64/64 周期相等）：I$ 加第二个 tag / 半字读口、两阶段请求寄存器、重放、半字窗口；见 `rtl-rvc/docs/RVC_RTL.md`。
  - **两级预测校验（2026-11-13，结论：不做，加了统计）**：
    - 现状：trace-model 只有一级校验，在指令 FIFO 队头和 PTAB 队头一起读出时做（方向、JAL / 直接分支目标、顺序目标；JALR 目标不可知，留给后端）。香山分 F3（类型、JAL / JALR / ret 截断）和写回（起点、目标）两级，区别只在于一级校验不被后面的缓冲满压住。
    - 新统计 `[PD_CHK]`（`front_top.cpp`，不改周期，gate 64/64、C gate 65/65 不变）：4 个 SPEC 点（本地 `spec-rv32imab` 检查点、`FASTWARM=1000000 MEAS=3000000 PF_ENABLE=1`、rv32 `FP=0` 构建；数据 `AI-Huma-data/pdchk`）：校验触发的 flush 占组数 0.08%（gcc）/ 0.84%（perlbench）/ 1.16%（sjeng）/ 2.34%（gobmk）；flush 的那一组在队头被「front2back FIFO 满」压住的占 flush 的 0%（gcc）/ 0.1%（perlbench、sjeng）/ 7.0%（gobmk，每次 1 周期）；flush 时队列里排在后面的组数平均 ≤ 0.07。
    - 上界：把校验提前到不受后端压住，最多省 gobmk 1863 周期 / 1.34M = 0.14%、sjeng 约 0.015%、perlbench 约 0.006%、gcc 0；所以不实现两级（模型里就是香山 F3 级的行为）。flush 种类：gobmk 的 flush 93% 是「预测 taken 但本组没有 taken 的分支」（BTB / uBTB 别名，大代码），不是方向或目标错，所以也不是校验结构能改善的。
    - 局限：4 个点，每点 3M 条指令，不是全量。RTL 如果要拆成两级是面积 / 时序的取舍，周期模型里没有可量化的收益。
  - **工作负载（带 C 对不带 C）**：同源 dhrystone（64 次）、coremark（2 次迭代），代码大小 −20% 到 −27%，指令数相同，周期：coremark 282,616 → 272,509（−3.6%）、dhrystone `-O0` 116,401 → 113,719（−2.3%）、`-O2` 35,869 → 34,387（−4.1%）；不带 C 的程序在 `RVC=1` 前端上与 `RVC=0` 相差 ±0.5%。
  - **前端统计**（`[RVC_FE]`）：coremark 带 C 时 43.5% 的指令是 16 位、每组 8.2 条指令；`lastHalf` 被用到的组约占 14%（24005 / 169948）。`FE_IPF`、`FE_BFAST` / `FE_RFAST` 与 `RVC=1` 一起跑 C 编译的 cpu-tests：60 个程序 0 个不一致。
- **没做的**：S4 的两级预测校验（与 C 无关，是更一般的前端改动，没做）、RTL；S3 复核结论：`PreIduQueue` 已经是按指令的环形缓冲（64 项，每拍进最多 16 条、出 8 条），不用改；跨 cache line 的 32 位指令取指没有额外延迟（后半条按功能读取，乐观）；预译码检查器的两级、RAS 返回地址按长度（`pc+4` 仍在 BPU 的 RAS 压栈和 BTB 未命中目标里）；`FE_PAIR` 在 `RVC=1` 下没测；`RVC=1` 的 rv64 构建和 rv64gc Linux 没在 trace-model 上跑。
- **（S1 遗留）`pc+4` 在前端的残留**（RAS 压栈 `pc+4`、预译码检查器的 `+4`、`seq_next_pc` 的 `+4`、BTB 未命中目标 `pc+4`）等 S2 / S4 带上每个 slot 的长度后再改。

- **2026-11-15 更新（RTL）**：RTL 侧 R0–R4 在 rtl `exp/rvc-rtl` 完成：`RVC=1` 非 C 程序 64/64 周期与模型相等，C 程序 59/60（`rvc-fencei` 差 7 周期，自修改代码），RAS 改成追加队列后 trace-model 与 RTL 同步（trace-model `73aea0d`、rtl `2ec1d5f`）；rv64gc（`RVC=1`、`FP=1`）的 Linux 对齐见 EXP-040。**未解决**：rv32 `RVC=1`（`FP=0`）整核测试平台起不来（67 个程序在第一条提交 `pc rtl=4 fm=0`），在没有改动的 HEAD 上同样如此，原因没查，登记在 `rtl/docs/RVC_RTL.md`。

## EXP-037 C 扩展（压缩指令）：function-model 第一步

- **状态：2026-11-13 function-model 完成（`exp/rvc`、`exp/rvc-fast`），已快进合入 `main`（`6bf6c59`）并推送；trace-model 和 RTL 还没开始。**
- **为什么做**：RV64GC 是发行版、标准工具链和主流 Linux 核的基本配置；C 改变「每条指令 4 字节、PC 4 字节对齐」这条全核约定，前端（取指、预译码、BPU、I$、ITT）受影响最大，后端只需要每条指令多带一位长度。先做 function-model（Spike 可以逐条对拍），再 trace-model，最后 RTL，和 F/D 同样的顺序。
- **做法**（编译开关 `RVC=1`，`XLEN=32/64`，默认 0，`RVC=0` 行为不变）：
  - 取指单位是半字，一条 32 位指令可以从任意半字开始；第二个半字在下一页时单独翻译，缺页的 `mtval` 是 `pc+2`。
  - 16 位指令在取指时展开成 32 位（`include/rvc.h`，纯函数），执行部分不变；`ilen` 用于 `pc+ilen`、链接值（`jal`/`jalr`/`c.jal`）、`ebreak`/`ecall` 之后；非法或保留编码的 `mtval` 是 16 位原编码。
  - `misa.C`；`jalr` 只清第 0 位；`mepc`/`sepc` 只清第 0 位；`medeleg[0]` 只读 0；`RefCpuStepInfo.inst_len` 给上层。
  - 快速路径（基本块缓存）也支持压缩指令（分支 `exp/rvc-fast`，在 `exp/rvc` 之上）：每条指令记字节偏移和长度；带 C 的 Linux 15 亿条指令 30 s → 4.6 s；与单步路径的状态摘要（含 CSR）在 Linux 前 1 亿条指令和 58 个测试程序上逐块一致。
- **验证**（每条指令与 Spike 比较）：
  - 定向测试（`tests/rv64/gen_rvc.py`，`tests/rv64/rvc.sh`）：全部 16 位编码里非访存非跳转的 18368 个（rv32：16320）在随机寄存器值上执行，非法 / 保留 / HINT 都包括；全部 24576 个访存编码（带读回整块缓冲区的校验和，FS 开 / 关的浮点各一份）；`c.j`/`c.jal`/`c.beqz`/`c.bnez` 前后向多种偏移（taken / not taken，2 字节和 4 字节对齐），`c.jr`/`c.jalr` 每个寄存器（含目标第 0 位为 1）；32 位指令跨 cache line、跨页；Sv39 下第二个半字的页无效 / 不可执行 / 用户页 / A=0 的缺页（`mtval = pc+2`）。rv32 和 rv64 都通过。
  - 注入 3 个展开错误（`c.addi16sp` 立即数位、`c.beqz` 偏移位、`c.fsdsp` 偏移）：第 3 个最初没被发现（测试没有读回 store 写入的数据），补上校验和后 3 个都被抓到。
  - 官方 `riscv-tests` `rv32uc`/`rv64uc`（含跨页取 4 字节指令）通过；trace-model 的 cpu-tests 带 C 编译：rv64 47/52、rv32 46/51，不通过的 5 个都是测试源码假定 4 字节指令（`interrupt-vectored`、`supervisor-external-interrupt-vectored` 的向量表 4 字节槽位，`trap-precise-store` 用 `+8` 跳过 `ecall; sw`）或不带 C 时就有的平台差异（`software-interrupt-vectored`、`timer-interrupt-mask`）。
  - Linux：内核和 OpenSBI 带 C（`CONFIG_RISCV_ISA_C=y`、`PLATFORM_RISCV_ISA=rv64imafdc_zicsr_zifencei`），用户态仍是 rv64g；`ttg64gc.dts`；到 `rv64 login:` 且 `fptest: PASS`，Spike 逐条对拍前 2.5 亿条指令 0 不一致（过程中发现并修了 `medeleg[0]`）。
  - `RVC=0` 回归：`tests/rv32/run.sh`、`tests/rv64/run.sh` 与改动前一致（rv32 53/56、rv64 52/54，不通过的是已知平台差异；F/D 和官方 rv32uf/ud 全过）。
- **没做的**：48 位以上指令；`misa.C` 可写；Zc*；用户态也带 C 的 Linux（需要重编 Buildroot 工具链）；trace-model 前端按半字取指、BPU / FTQ 半字粒度、RTL 预译码和边界。

## EXP-036 trace-model 仿真速度：去掉每周期的状态拷贝

- **状态：2026-11-13 已合入 trace-model `main`（`195dad4`，已推送）。** 日期 2026-11-12/13。**目标**：trace-model 每周期要把整个流水线状态拷一份（cur → nxt），先量了耗时占比（function model 只占一小部分），再按 `sample`（macOS）和临时 `cntvct` 计时器找拷贝热点，逐个去掉。**每一步周期都和之前逐个相同**（gate 64/64、`fp_check`、大程序）。
- **改动**：
  - `BpuPipe`：流水线寄存器双缓冲加指针交换（提交时不再拷 14 KB），下一拍状态不拷 `R`，S0 块原地构建，`Txn` 不带状态（省 16 KB 清零），`Decision` 只在块离开时清；只拷活的检查点，`Decision.blk` 用指针（约 −14%，累计 −18%）。
  - 分级 LSU：`cur`/`nxt` 里只保留两个共用的旧单元；`pcur = pnxt` 只拷活的 LDQ / STQ 表项（空 LDQ 项只留 epoch，窗口外的 STQ 项跳过）；`LSU_SEQ_POISON` 构建把跳过的表项填垃圾仍然逐个一致，用来证明没有漏拷（累计约 −20%）。
  - `LSU_PIPE_DUMP` 只读一次环境变量（每周期 `getenv` 约占 4.5%）。
  - `TraceBridge::find` 改二分查找（`BRIDGE_FIND_CHECK` 构建会和线性查找对照）。
  - 发射队列：空位 / 分支扫描用有效位掩码，`clear_br` 只标记变化的项，唤醒以紧凑列表送到各队列，grant gate 只在初始化时设置（不再每周期给 `std::function` 赋值），每个队列只访问自己的端口范围（约 −4.5%）。
- **结果**：相对 EXP-035 的二进制累计耗时下降约 24%（各步提交里记的是 −14%、累计 −18%、累计 −20%、再 −4.5%；memory-stress-small 一次计时 18.0 s → 12.9 s）。
- **验证**：每步 gate 64/64、`fp_check`、大程序；LSU 稀疏拷贝用毒化构建验证。
- **没做的**：`BpuPipe` 的 `R[0]=Blk{}` 和移位（每次约 2.6 KB）、function model 每次派发的 `get_state`（约 2.5%）；多线程加速没做。

## EXP-035 写回口按完成周期在发射时预约

- **状态：2026-11-12 已合入 trace-model `main`（`4a1d9df`）和 rtl `main`（`f61e821`、`b976975`），2026-11-13 已推送。**
- **问题**：一个写回口每周期只能完成一条 uop，旧模型里撞车的那条先在执行单元里等，而它的消费者已经被唤醒了（带值的核里会读到旧值）。coremark 里撞车 12247 次，fp-kernels 124 次。
- **做法**：发射时按「完成周期 = 发射 + 延迟（DIV / FDIV 再 +1）」查每个端口的占用环（`WbBusy`，64 项），与 FP 写口的 gate 合并；撞车的 uop 留在 IQ 里下一拍重试，所以撞车数是 0（`WB_RESERVE`，默认开）。
- **RTL**：`isu_wb_gate`（每端口一个占用位环，偏移用 `isu_pkg::wb_offset()`），接到 `isu.sv` 的候选有效信号上；单元测试 `tests/wb_gate`（随机序列与参考实现的 `WbBusy` 对照，0 不一致）。
- **周期**：coremark 284,902 → 282,616（−0.80%），dhrystone 116,774 → 116,401（−0.32%），memory-stress-small 325,458 不变；gate 64 个程序里 11 个变化，几何平均约 0，基线已重生成。RTL 与模型逐周期相同（smoke、dhrystone、coremark、pf-stress、fd-*、FP 内核、rv64）。

## EXP-034 Exu 改成按单元的状态，去掉 execution-driven 遗留结构

- **状态：2026-11-13 已合入 trace-model `main`（`a50b64b`，已推送）。**
- **问题**：Exu 还是最早 execution-driven 时期的结构：每个功能单元是一个 `Fu` 对象，每周期输入输出整体拷贝。
- **做法**：每个单元一个 `FuUnit`（`SINGLE`/`PIPE`/`ITER` 三种模式，完成周期环形缓冲，赢家用位掩码），各阶段每周期只跑一遍，所以一份状态数组就够；`Fu.h` 只留 `FuKind`/`FuMode` 和 `fu::compute`、`fu::iter_latency`；只访问有 uop 在里面的单元。旧 Exu 冻结成 `tests/exu_ref`，`EXU_SHADOW` 构建里新旧并行、每周期比较输出。
- **验证**：gate 64/64、`fp_check` 32/64 与基线相同，同步比较 0 不同；约快 6%。过程中修了一处：收集阶段对死 uop 和 LSU 写回要用 `rob_bcast.flush`，不是 `flush_any`。`fd-matmul` 的基线是 EXP-033 的 I2F 优先级变化的陈旧基线，已更新。

## EXP-032 / EXP-033 FP 写口与 fcsr 串行化

- **状态：2026-11-13 已合入 trace-model / rtl `main`，已推送。**
- **EXP-032**：FP 寄存器堆写口数 `FP_WB_PORTS`（默认 2），发射时预约；统计各口使用；FP 内核和扫描脚本；`fp_check` 24/24、微基准延迟不变。
- **EXP-033**：`fflags` / `frm` / `fcsr` 是真正的 CSR 指令（串行，`FS=Off` 时非法，`CSR_NUM` 22）；时序模型的 CSR 值不再回补 function model；ROB 从写回取 `illegal_inst`（以前 FP uop 在执行时发现非法不会产生异常）；整数端口的写回优先级里 I2F 在 ALU 之前（I2F 被饿死时消费者读到旧值，带值的核里会错）。`rv32-fp-trap` 87154 → 95438 周期。
- **RTL 标准 F/D（`exp/fd-rtl`，计划见 `rtl/docs/10-fd-rtl-plan.md`）**：S1 译码和 FP 重命名域、S2 FP 发射队列 / 发射口 / I2F / 第三源唤醒 / FP 写口 gate、S3 FP 寄存器堆和 FP 单元（DPI softfloat）、S4a `flw/fsw`、S5 `fflags/frm/fcsr` / `mstatus.FS/SD` / `misa` / FS=Off 异常、S6 每条提交逐位比较 FP 寄存器（含 NaN-boxing）、rv64 的字 load 宽度位；`exu_ctrl` 的 CSR FU 旁路带 CSR 读数据（以前消费者与 CSR 同拍执行时读到 0，rv32uf-fcmp/fdiv 多 1 周期）。**FP 单元是 DPI softfloat，不可综合**（S7 没做）。
- **rv64g Linux**（function-model `exp/fd-all`）：Buildroot 2024.02.9、`lp64d`、`riscv,isa = "rv64imafd"`（`linux/ttg64g.dts`）、rootfs 里带 `fptest`；function model 上到登录且 `fptest: PASS`。
- **RTL 上 rv64g Linux 从复位启动**（2026-11-13）：RTL（rv64、`FP=1`）每条提交与 function model 逐条对比（`SOC_TB_FM=1`），**到 `rv64 login:`，`fptest: PASS`，171,931,468 条指令、6282 个设备/计数器值、816 次中断，0 不一致**；2.2 亿周期上限、约 2 小时 41 分（约 2.3 万周期/秒）。从复位需要 `-DTTG_EBREAK_TRAP` 构建加 `SOC_TB_SEMIHOST=1`（OpenSBI 探测半主机用 ebreak；没有它在 9.7 万周期处停住）。日志和镜像：`AI-Huma-data/linux_rv64g/`。之前还验证过 4 个 Linux 中段检查点各 3M 周期 0 不一致（检查点文件在会话临时目录，已丢，可用 `function-model --mode special-ckpt` 重生成）。

## EXP-031 删除 Zfinx，全面改用标准 F/D（含 rv32）

- **状态：2026-11-12 三个分支完成，未合入、未推送**：function-model `exp/fd-all`（`eca7c83`）、trace-model `exp/fd-all`（`8017ffb`）、rtl `exp/no-zfinx`（`3ff0253`）。
- **目标**：rv32 原来的浮点是 Zfinx（浮点放在整数寄存器里，只有单精度），rv64 有 EXP-030 的标准 F/D。统一成一套：F/D 是默认配置（`FP=1`），Zfinx 删掉；`FP=0` 是没有任何浮点的核。
- **function-model**：rv32 F/D（FLEN 仍是 64）：`fld/fsd` 是 8 字节访问（两个字），rv32 没有 `fmv.x.d/fmv.d.x` 和 `fcvt.l/lu`（当作非法指令）；`mstatus.SD` 是第 31 位且只读；`misa` 带 F/D；检查点版本 6；`FP` 默认 1；删除 `RV32Zfinx`。前门恢复在 rv32 上只能还原 NaN-boxed 的单精度浮点寄存器。
- **trace-model**：删除 `UOP_FP`、Zfinx 的 `FuKind::FPU`、`OP_MASK_FP`、Zfinx 译码和唤醒；rv32 的 LSU 宽度辅助函数对 `fld/fsd` 返回 8 字节；`FP` 默认 1；rv32 的 `mstatus.SD`/`misa`；检查点版本 6；5 个 Zfinx 测试（`zfinx*`、`matmul_fpu`）换成 F/D 版本 `tests/extra/fd-*`（同样的运算，操作数仍是 `uint32_t` 位型，经浮点寄存器运算），`build_tests.sh` 对 `fd-*` 用 `imafd` + 双精度 ABI；`results/baseline/*.csv` 去掉 Zfinx 行、加入 `fd-*` 行。
- **RTL**：删除 `rtl/backend/fpu`、`tests/fpu`、`spec/fpu.io`、`tools/fp`；译码去掉 OP-FP（`CLS_FP*`，立即数选择从 7 位改 6 位）、派发去掉 `INST_FP`/`UOP_FP`、ISU 去掉 FP 的延迟唤醒源和 FP 发射能力、exu_ctrl 的 FU 编号 5 之后整体前移一位（mc 序 `{MUL(0), DIV(3), MUL(5), DIV(7)}`）、`exu.sv`/`gen_backtop.py` 去掉 `u_fpu`；`ttg_cfg_pkg.sv` 用 `-DFP=0` 重新生成（RTL 目前没有浮点，和模型的 `FP=0` 一致）；`scripts/` 里的程序列表去掉 Zfinx 程序。
- **验证**：
  - function-model：rv32 的 21 个官方 `rv32uf/ud`、`rv32-fp`（约 16 万行汇编）、`rv32-fp-trap`、`fp-kernels` 与 Spike 逐条一致；rv32 整数程序 50/53（3 个是改动前就有的差异）；rv64 整套 52/54（2 个已知平台差异）加 F/D 3/3。
  - trace-model：rv32 gate 64/64（所有原有程序周期与基线逐个相同，只有 Zfinx 行换成 `fd-*` 行）；55 个 rv64 整数程序周期与改动前逐个相同；`scripts/fp_check.sh`（`XLEN=32` 24/24，`XLEN=64` 26/26，微基准延迟不变）。
  - RTL：`lint.sh` 0 警告、`lint_chip.sh` 0、`soc_smoke.sh` 56/56、dhrystone 116,774 和 coremark 284,902 与模型逐周期相同。
- **没做的**：RTL 的标准 F/D（见 [EXP-030-trace-model-plan.md](EXP-030-trace-model-plan.md) 之后的 RTL 讨论）；rv32 F/D 的 SPEC / Linux 用户态验证；半精度；rv32 前门恢复的双精度寄存器。

## EXP-030 rv64 的 F/D 浮点扩展

- **状态：function-model（`cdcb74d`）和 trace-model（`2c1d166`）第一版已合入各自的 `main`（2026-11-12，未推送）；RTL 还没开始。**
- **日期**：2026-11-12。**目标**：补标准 F/D（rv64），这样 SPECfp 和标准工具链的 `lp64d` ABI 才能跑；顺序是 function-model（Spike 对拍）→ trace-model（周期模型）→ RTL。F/D 先于 C，原因：F/D 是加法（新寄存器堆和浮点单元，整数路径不动），C 改的是前端（PC 2 字节对齐、取指跨行、预译码、BPU/I$/ITT），会让所有前端基线失效，要作为单独的实验。
- **做法**：编译开关 `FP=1`（只能和 `XLEN=64` 一起用，默认 0，`FP=0` 的 rv32 / rv64 构建行为不变）；rv32 仍是 Zfinx。
  - 状态：`CPU_state.fpr[32]`（64 位，单精度做 NaN-boxing，没有 box 好的读成规范 NaN `0x7fc00000`）、`fcsr`（`fflags`/`frm`）、`mstatus.FS`（Off 时所有浮点指令和 `fflags/frm/fcsr` 访问都是非法指令）和 `SD`（FS=Dirty 时置位，读 `mstatus/sstatus` 可见）；任何浮点寄存器写入或 `fflags` 变化把 FS 置 Dirty；`misa` 多了 F、D。
  - 指令：`RVFD()` 处理 OP-FP（`fadd/fsub/fmul/fdiv/fsqrt`、`fsgnj*`、`fmin/fmax`、`fcvt.s.d/d.s`、`feq/flt/fle`、`fcvt.w/wu/l/lu` 两个方向、`fmv.x.w/d`、`fmv.w/d.x`、`fclass`）和四个融合乘加；`flw/fld/fsw/fsd` 并进 `RV32IM()` 的 load/store 代码（同一套地址翻译、缺页、MMIO、store 路径，只换寄存器堆）；运算都用仓库里的 softfloat，舍入模式、保留编码、`fcvt` 的 rm 检查、NaN 处理按 Spike 的行为。
  - 检查点：格式版本 5（`CPU_state` 带 `fpr`，其后一个 `fcsr`）；`tools/ckpt2stub.py` 能读，前门恢复程序用 `fmv.d.x` / `csrw fcsr` 还原浮点状态，状态摘要里加入了浮点寄存器。
  - Spike 对拍：ISA 串 `rv64imafdb_zbc_zbkb_zbkx`，逐条比较增加 f 寄存器；`scripts/build_spike.sh` 认 `FP=1`。
- **验证**（全部是 Spike 逐条比对 x/f 寄存器和 CSR）：
  - `tests/rv64/gen_fp.py`：约 13 万行汇编、35 万条指令，F/D 每条指令 × 5 种舍入模式 × 27 个特殊操作数（±0、1、次正规数、最大有限数、∞、qNaN/sNaN、整数转换的边界），含 NaN-boxing 违规、动态舍入、`fcsr` 访问和 `flw/fld/fsw/fsd`。
  - `tests/rv64/gen_fp_trap.py`：FS 取 Off / Initial / Clean / Dirty 时每类指令和 CSR 的行为、`mstatus/sstatus` 的 FS/SD、近 900 个保留编码（保留舍入模式、半精度/四精度格式、未用 funct7、保留的 load/store 宽度）、动态 rm 取保留值。
  - `tests/rv64/fp-kernels.c`：编译器（clang，`-march=rv64imafd -mabi=lp64d`）生成的矩阵乘、Horner、牛顿迭代、整数 ↔ 浮点转换、fma、比较。
  - 官方 riscv-tests `rv64uf`（11 个）+ `rv64ud`（12 个）：自检通过且与 Spike 逐条一致，23/23（`tests/rv64/riscv-tests-fp.sh`；用例来自 `~/personal/simulator/baremetal/riscv-tests`，该检出的 `riscv_test.h` 是适配过的，用 `ebreak` 报告结果，脚本另加了一个头文件打开 FS）。
  - 前门 / 后门恢复：两个在 `fp-kernels` 中段（浮点寄存器非平凡）生成的检查点，各 3000 条指令、30 个状态摘要（含 32 个浮点寄存器）完全相同。
  - 回归：rv64 的 54 个整数程序仍是 52 个一致（2 个已知平台差异）；rv32 的对拍结果和改动前一致（`load-store`、`software-interrupt-vectored`、`timer-interrupt-mask` 三个在改动前就不一致）。
- **顺带修的老 bug**：`csrrwi csr, 0`（`csrwi` 立即数为 0）原来不写 CSR（`we = funct3 == 1 || rs1 != 0` 漏了 `funct3 == 5`），Spike 会写；现在 `csrrw/csrrwi` 总是写。影响：rv32 / rv64 默认构建里 `csrwi x, 0` 的行为变对了，周期模型和 RTL 不受影响（它们不执行这条路径的差别）。
- **trace-model（2026-11-12，已合入 main：trace-model `2c1d166`，function-model `cdcb74d`）**：方案见 [EXP-030-trace-model-plan.md](EXP-030-trace-model-plan.md)，实现见 trace-model `docs/PROJECT.md` 的 F/D 一节。
  - 做了：`FP=1`（rv64）下的 FP 重命名（RAT / 空闲表 / 分支检查点）、FP 发射队列（32 项，三源唤醒矩阵）、三个 FP 发射口（两个 FMA 流水 + 一个 fdiv/fsqrt，都带 MISC）、`I2F` 走整数口、`flw/fld/fsw/fsd` 走现有 LSU、译码、按事实产生非法指令异常、`mstatus.FS/SD` 与 `misa` 的 F/D 在 CSR 模型里、bridge 的 FP 事实/撤销/检查点版本 5；统一的标签编号（模型）对分开的寄存器堆（RTL）。
  - 验证：`FP=0` 的 rv32 gate 62/62 周期与基线逐个相同；rv64 的 55 个整数程序 `FP=0` 与 `FP=1` 周期逐个相同；function-model 的三个 FP 测试和官方 `rv64uf/ud` 共 26 个程序跑到结束（difftest Success、指令数等于 function-model 的）；微基准显示配置的延迟（4 个相关 `fadd.d` 16 周期、8 个独立 `fadd.d` 4 周期即两条 FMA 流水满载、相关 `fdiv.d` 20 周期）；小 FPRF（36）、小 FP 队列（8）、长 FMA 延迟下无死锁，FP 空闲表不变量每周期断言；CSR 读补丁次数 0。脚本 `scripts/fp_check.sh`。
  - 和方案不同的地方：FP store 的数据源先让**所有** STD 口都能收（方案是只让 0 号口收，留给 RTL 决定）；`fflags/frm/fcsr` 的读写仍是 NOP、没有串行化（模型不算值，动态舍入没有时序效果）；`CFG_FP_*_LAT` 写成"相关指令的发射间隔"（延迟唤醒比单元延迟多一拍，和 MUL/DIV 一致）。
  - 起始参数（FP 物理寄存器 96、FP 队列 32、FMA 4 / MISC 3 / I2F 3、fdiv 12/20、fsqrt 14/24）都是经验值，没有 FP 负载标定。
- **没做的**：半精度 Zfh；RTL 的浮点单元；PolyBench / SPECfp 负载上的标定；`mstatus` 写掩码里 WPRI 位 0、4 和 XS 与 Spike 不同（只有写全 1 才看得见）；F/D 的 SPEC 和 Linux 用户态验证。

## EXP-029 从 rv32imab 迁移到 rv64imab

- **状态：2026-11-12 已合入三个仓库的 `main` 并推送，合并后重验见 MAIN_RECORDS 2026-11-12 行。**
- **日期**：2026-11-11 至 2026-11-12。**分支**（合入前；没有推送）：function-model `exp/rv64`（7 个提交，基于 `d40c588` 之后的 main）；trace-model **`exp/rv64-on-main`**（11 个提交，基于 `07d567c`，即 RTL 标定所用的模型；旧的 `exp/rv64` 建在更老的 main 上，rv32 `add` 给 1415 周期而参考表是 1276，不要用）；rtl `exp/rv64`（7 个提交，基于 `de8d0aa`，早于 EXP-028 合入的 `a905acd`）。
- **目标和范围**：先做 rv64imab（Zfinx 去掉，F/D 以后按标准浮点单独加），再 C，最后 G；SPEC 重新生成不在这一轮。顺序：function-model → Spike 对拍 → rv64 Linux 镜像 → 检查点 / BBV → trace-model → RTL。`XLEN` 是编译期参数（`-DXLEN=64`，默认 32），XLEN=32 的行为和周期要保持逐位不变。
- **function-model**：RV64IM + Zba / Zbb / Zbs，A 扩展带 `.d`，Sv39 页表遍历，`ld` / `sd` / `lwu`、`*W` 指令，`misa` / `mstatus` 的 UXL / SXL（只读），rv64 启动 ROM，基本块快速通路按 XLEN 泛化，检查点格式 v4（`ckpt2stub.py` 的 rv64 版本，前门恢复与后门恢复一致），BBV 只数 U 模式指令。对拍：Spike 52 / 54 通过，另外两个（software-interrupt-vectored、timer-interrupt-mask）是平台差异（中断来自平台，Spike 没有该来源）。Sv39 变异测试 9 / 9 被抓到。rv64 Linux 镜像（Buildroot，主机名 rv64）在函数模型上启动到登录，与 Spike 无不一致。
- **trace-model**：接口层（facts / 状态 / 检查点）、译码（OP-IMM-32 / OP-32，`is_word`）、MMU Sv39（3 级、8 字节 PTE、保留位与超级页对齐检查、16 位 ASID、规范地址检查，非翻译的 >32 位地址映射到 `0x7fffffff`）、CSR 64 位、前后端 PC 全部加宽（`pc_t` / `fetch_addr_t` / `target_addr_t`，BPU 的哈希取字地址的低 32 位 `pc[33:2]`）、外设模型 8 字节访问（`sd` = 两次字写，`ld` = 两次字读）。乘除延迟：乘 3 周期（32 位保持 2）、除法每周期 2 步所以 64 位 32 周期、`*W` 除法 16 周期（32 位保持 16）。`addiw rd, rs, 0` 不再当 move 消除（它是符号扩展）。
- **RTL（本次的主要工作）**：
  - `XLEN_BITS` 进配置包（`ttg_cfg_pkg.sv`；`DST_STRB_W`、`DST_L2_W` 也在生成器里）。后端：PRF / ALU（6 位移位量，`addw` … `rorw`、`add.uw`、`shNadd.uw`、`slli.uw`、`clzw` / `ctzw` / `cpopw`、`packw`，64 位 clmul）/ BRU / AGU / SDU / 乘（2×XLEN 乘积 + `mulw`）/ 除（`divw` 系列半数迭代）/ CSR（掩码、`misa`、`mstatus` 复位 UXL = SXL = 2、`satp` 只接受 Bare 和 Sv39）；新的 uop 位 `is_word` 从译码一路到执行单元；AMO `.w` 的 min / max 只比较低字。
  - LSU（分级）和 dcache：数据字 XLEN 位，行和 AXI 侧仍是 32 位字；`extract_data` / `store_strb` / `align_store_data` / `mem_width` / `check_addr` 按 XLEN；store 字节掩码 XLEN/8 + 1 位；写缓冲第二个 store 字；转发、SC 返回值。旧的非分级 LSU（`LSU_PIPE=0`）没有扩宽，在 XLEN=64 下不可用。
  - Sv39 TLB 和页表遍历器：叶子级别 0..2，标签带三级 VPN，PTE 事件 64 位，物理地址仍 32 位（只用 `ppn[19:0]`）。
  - 前端：取指 / 重取指地址、FTQ、ptab、FIFO、predecode（立即数符号扩展）、BPU（BTB 目标、RAS、uBTB 目标扩到 XLEN，哈希取低 32 位）、ICache / ITLB（虚拟标签 XLEN−12 位）、核心层接线。
  - 外设：请求 / 响应 / 环境接口数据 XLEN 位（`lw` 符号扩展，`lwu` 零扩展），`ld` / `sd` 仍是一次事务，和模型时序一致。
  - 测试平台：rv64 启动桩（与函数模型的启动 ROM 同样的字）、64 位的逐条对比器、`SOC_XLEN=64` / `FMLIB`、`SOC_TB_LOG=<n>`（周期 / 提交 / 最近 PC / 速度 / 预计剩余时间）、`SOC_TB_STLOG`（按地址记录提交的 store，调试用）。
- **用 rv64 程序跑出来的 RTL / 模型 bug**（lint 和 XLEN=32 回归都发现不了，只有真正跑 rv64 才暴露）：
  1. dcache 的"未命中后同拍把填充行转发给 load / 合并 store"路径用 32 位字下标去取 XLEN 数据字。
  2. **dcache 写回缓冲合并 store 字节时写死 `b < 4`、`<< 5`**：store 落在正在写回的脏行上时，rv64 的高半个字被丢掉。只有大数组造成大量脏行写回的程序才暴露（`memory-stress` 在第 72 万条指令；rv32 同一个程序不出问题）。
  3. 发射队列给 `divw` / `remw` 的唤醒倒计时用了 64 位除法的 32 周期，而除法器 16 周期就完成，唤醒槽不够，触发 `isu_alloc_chain` 断言。
  4. load / store 重叠判断（`lp_ovl`）把 8 字节的宽度编码成 3 位而截成 0。
  5. 测试平台按位置读 STQ 条目：重排结构体字段会让中断类测试死循环（XLEN=32 回归才发现）。
  6. trace-model：`csrw sstatus` 之后 `sstatus` 的读视图丢了 UXL（视图掩码用了写掩码），`csr-alias-boundary` 在模型上多执行 2 条指令。
- **验证**：
  - lint：整颗芯片 333 个文件，XLEN=32、XLEN=64 都 0 警告。
  - XLEN=32 不变：`fm_gate` 周期 ≤ 15 万的 64 个程序全部通过，周期与参考表逐个相同；rv32 `memory-stress`（745 万条指令）逐条对比 0 个不一致。**注意**：这 64 个程序的子集不含脏行写回压力大的程序，上面第 2 个 bug 就是因此没有在 rv32 回归里暴露；以后回归要把 rv32 `memory-stress` 放进去。
  - rv64：53 个 cpu-tests（去掉浮点、`load-store`、`bitmanip-boundary`、`rv64-sv39`）在 RTL 上全部通过逐条对比；**周期与 trace-model（`exp/rv64-on-main`）逐个比较：52 个完全相同**，`memory-stress` 差 24 周期（230 万周期，0.001%；rv32 的同一程序也差 63 周期，是原来就有的微小偏差，和 rv64 无关）。早先看到的 −16% 到 +37% 是用错了模型（`exp/rv64` 在更老的 main 上）。`rv64-sv39` 在 RTL 上 3.6 万条指令通过；新写的 `tests/rv64/mmio64.c`（`sd` / `ld` / `lw` / `lwu` 访问定时器和 `mtimecmp`）通过。
  - **rv64 Linux 在 RTL 上从复位启动到 `rv64 login:`**：约 1.05 亿周期（与 trace-model 一致），仿真速度约 3.5 万周期 / 秒（约 50 分钟），逐条对比开着 0 个不一致，Verilator 断言 0 个。构建和运行：`SOC_XLEN=64 SOC_FM=1 FMLIB=<XLEN=64 的 librefcpu.a> SOC_VOPT="--threads 4 -DTTG_EBREAK_TRAP" tb/soc/build.sh`；`SOC_TB_LOG=2000000 SOC_TB_SEMIHOST=1 SOC_TB_FM=1 soc_tb AI-Huma-data/linux_rv64/linux.bin 400000000`。
- **结论**：rv64imab 在函数模型、周期模型、RTL 三个层次都跑通，且 XLEN=32 的行为和周期完全不变；RTL 的周期与模型一致（52 / 53 个程序逐周期相同）。
- **没做 / 已知问题**：
  - 浮点（F / D，rv64 下 Zfinx 被关掉，FPU 只接低字；`OP-FP` 按非法指令）、C 扩展、`bitmanip-boundary` 的 rv64 版本、SPEC 的 rv64 流程、FastWarm 的 Sv39 TLB 预热（现在还是 Sv32）。
  - function-model 的 rv64 MMIO `sd` / `ld`：只按 4 字节读写设备寄存器，`mmio64` 的读回检查在模型上失败（RTL 正确）；Linux 只写 `mtimecmp` 不读回，所以没有影响。
  - 登录之后的交互（需要给 UART 喂输入）没有验证。
  - 外设的 AXI 一路（地址不属于本地模型或未缓存内存）仍是一次 32 位字。
  - **生成文件的债务**：`back_top.sv`、`exu.sv`、`soc_top.sv` 由 `tools/gen_backtop.py`、`gen_soc_top.py` 和 `spec/*.io` 生成，这几步都是手改的位宽，重新生成会改回去；`ttg_cfg_pkg.sv` 里的 `XLEN_BITS` 是手写，合入前要由生成器（用 trace-model 的 `config.h -DXLEN`）输出。
- **合入 `main` 的注意事项**：三个仓库都要 rebase 到现在的 main：RTL 的基线早于 EXP-028（紧凑 ROB，`rob_core_cpt.sv` 等），要在紧凑 ROB 上再核一遍；trace-model 以 `exp/rv64-on-main` 为基础重放到 `a11b1ca`（EXP-028 之后）；合入前要重跑 XLEN=32 的 fm_gate、rv32 `memory-stress` 和 rv32 Linux，以及 rv64 的 53 个程序和 Linux。

## EXP-028 ROB 压缩、加大 ROB / PRF、重命名整组等待

- **日期**：2026-11-11（接手 2026-11-10 会话"Trace model 未合并分支"里没做完的部分）。**分支**：trace-model `exp/rob-compress`（工作区 `trace-model-robc`，5 个提交变基到 main `07d567c`：`a80e221`/`1d97a7e` `ROB_COMP_STATS`、`fac878e` `REN_STATS`、`0406a5c` `REN_AON`、`bb89d17` `ROB_FILL_STATS`；统计都是只计数、默认关，`REN_AON` 是运行时开关，默认关时 coremark 283,240 与 main 相同；这些实验提交留在该分支，不进 main）。**2026-11-11 合入 main**：紧凑 ROB + 寄存器额度和同批清理放在 trace-model `merge/rob-compact`（`35b3af4` 开关默认关、`a11b1ca` 默认开 + 基线）、rtl `exp/rob-compact`（`4e954d7`、`a905acd`）；实验用的 `ROB_CPT_CREDIT` / `ROB_CPT_K` 等运行时开关合入时删掉，只留编译期 `CFG_ROB_COMPACT`（现默认 1）。
- **问题**：要不要做 ROB 压缩（连续简单指令共用一项）或紧凑 ROB（不按行），还是直接加大 ROB / PRF。前一天的结论（30 点：整组等待 +0.5%、ROB192 + 整组等待 +2.2%、ROB192 + PRF192 +3.2%，不建议做压缩）有三个问题：① 在删除 0x87f00000 非缓存窗口（EXP-027）之前测的，结论主要靠 hmmer、h264ref，而这两个程序正好受窗口影响；② 30 个点按 `points_full.txt` 第 4 列选，那是旧 IPC 不是权重，选出来的是高 IPC 点；③ 原始数据在服务器（关机）。所以在当前 main 上本机重测。
- **背景机制**（前一天已查明）：ROB 按行组织，8 个 bank × 16 行 = 128，一个分发组占一整行（槽 i 进 bank i），整行提交；重命名在组中间没有空闲物理寄存器时只放行前面几条（"半组"），留下的半满行浪费 ROB；ROB 越大、PRF 越紧，半满行越多，hmmer 因此在只加 ROB 时变慢。`REN_AON=1`：组里任何一条拿不到寄存器就整组不放行。
- **方法**：30 个点按 SimPoint 权重选（gcc、perlbench、h264ref、xalancbmk、gobmk、sjeng 各 3 个，其余 6 个程序各 2 个，`AI-Huma-data/robc/points_w30.txt`），快速预热 100 万条、预取开、`PMU=1`；程序 IPC = 1/Σ(w·CPI)，变化相对 ROB128 / PRF128；构建 `CFG_ROB_NUM`、`CFG_PRF_NUM`；本机 13 并行，210 次全部完成。
- **结果**（IPC 变化）：

| 程序 | 整组等待 | ROB192 | ROB192 + 整组等待 | ROB192 + PRF192 | ROB192 + PRF192 + 整组等待 | PRF160 |
|---|---|---|---|---|---|---|
| perlbench | +0.02% | +1.07% | +1.06% | +1.25% | +1.19% | +0.09% |
| bzip2 | 0.00% | +1.06% | +0.85% | +1.51% | +1.44% | −0.02% |
| gcc | 0.00% | +0.10% | +0.09% | +0.10% | +0.10% | −0.01% |
| mcf | +0.03% | +2.37% | +2.43% | +2.43% | +2.43% | −0.06% |
| gobmk | +0.25% | +0.46% | +0.59% | +0.66% | +0.66% | +0.27% |
| hmmer | **+7.49%** | **−20.88%** | +7.60% | **+13.22%** | +13.22% | **+11.00%** |
| sjeng | +0.14% | +2.24% | +2.31% | +2.62% | +2.67% | +0.16% |
| libquantum | +0.12% | +0.90% | +0.70% | −0.48% | −0.55% | −0.50% |
| h264ref | −0.06% | +3.99% | +4.02% | **+6.53%** | +6.49% | +0.59% |
| omnetpp | −0.07% | +4.34% | +4.22% | +4.77% | +4.77% | −0.13% |
| astar | +0.09% | +2.01% | +2.17% | +3.50% | +3.71% | +0.42% |
| xalancbmk | −0.64% | +1.60% | +1.38% | +1.28% | +1.28% | −0.09% |
| **几何平均** | **+0.59%** | **−0.29%** | **+2.27%** | **+3.06%** | **+3.06%** | **+0.93%** |
| 最差点 | −1.36% | −20.91% | −0.17% | −1.61% | −1.82% | −0.92% |

- **统计**（对照配置，每程序各点平均）：ROB 行平均填充 5.58/8（70%；gcc 4.09 最低，libquantum 6.72 最高）；重命名"半组"周期占比 hmmer 19.0%、h264ref 10.8%、astar 7.1%、libquantum 5.9%、bzip2 2.0%，其余 <0.6%；简单指令（ALU/MUL/DIV/NOP）比例 25–55%，按提交顺序理想合并、K=4 的有效容量比 gcc 1.01、bzip2 1.07、mcf 1.09、xalancbmk 1.11、perlbench 1.15、h264ref 1.15、astar 1.23、sjeng 1.25、libquantum 1.25、gobmk 1.28、omnetpp 1.37、hmmer 1.53（每程序第一个点）。
- **结论**：
  1. 删窗口、换选点后，前一天的结论基本不变（+0.59 / +2.27 / +3.06% 对 +0.5 / +2.2 / +3.2%）；hmmer 的问题是真的重命名行为，不是窗口假象。
  2. **整组等待是加大窗口的前提**：不改重命名就加 ROB，hmmer −21%；加了整组等待后最差点 −0.17%。单独开只有 hmmer 受益（+7.5%），平均 +0.59%。**RTL 的 `ren_handshake.sv` 也是半组放行**（第一个拿不到寄存器的槽之前都放行），改成"有任何一个失败就整组不放行"逻辑更简单（去掉 `ttg_first_set`），代价很小。
  3. **ROB 压缩不值得做**：有效容量比大多 1.0–1.3，最需要窗口的 gcc、xalancbmk、bzip2 最低；收益上限不到 ROB192 的 +2.3%。紧凑 ROB（不按行）的上限：128 项按 70% 填充约等于 183 条，接近 ROB192 + 整组等待的 +2.3%，但要加写入旋转、读出旋转和前缀提交，不如直接加行。
  4. **加大窗口**：ROB192 + 整组等待 +2.27%（ROB +50% 项）；ROB192 + PRF192 +3.06%（再加 PRF，主要给 hmmer、h264ref、astar）；只加 PRF160 +0.93%（几乎全是 hmmer）。是否值得要看面积和时序，**没综合**。
- **紧凑 ROB（同日续做，`ROB_COMPACT=1`，运行时开关，默认关）**：
  - **实现**（`Rob.cpp`、`Rob.h`、`Dispatch.cpp`、`IO.h`，约 200 行）：存储布局不变（项 n 在 bank n%8、行 n/8），`rob_idx` = 环形位置，其他模块不改；分发按组内有效槽的顺序编号、按空闲项数放行；提交取队头起最长的已完成前缀（最多 8 条，冲刷类 / fence / WFI / 中断仍在队头单独提交）；分支误预测时尾指针退到分支后一条；单条提交的副作用抽成 `single_actions()`，两种模式共用。默认模式 gate 64/64 与基线逐个相同；紧凑模式 gate 64/64 全部 difftest Success，Linux（加整组等待）从复位到 `rv32 login:`，0 不一致。dhrystone 114,685 → 111,231（−3.0%），coremark 283,240 → 282,591。
  - **BPU 训练带宽**：只开紧凑时 gcc 两个点各慢约 2%，原因是 BPU 的更新队列（8 项；表是单口，预测读优先）和 uBTB 训练队列（4 项，每拍消化 1 个事件）**满了就丢**，不回压提交。单拍分支数不是问题（紧凑模式下一拍 5 条分支的周期约 3%），问题是突发：gcc sp10 上"连续 2–4 拍每拍提交 ≥2 个取指块"的段从约 4.5 千段增到约 15 万段。30 点合计 uBTB 训练丢弃 88 万 → 290 万，控制流更新丢弃 162 万 → 401 万（按行提交本来也丢约 2.6%）。加 `ROB_CPT_CREDIT=2`：BPU 每拍送出两个队列的空位数，提交前缀里的分支数不超过更新队列空位、取指块结束数不超过训练队列空位（队头那条总能走），丢弃降为 0 和 96 万。剩下的条件分支误预测增多（gcc sp10 4,049 → 6,929；ROB192 上也有 5,445）是窗口变深后预测器按提交训练的滞后，不是紧凑本身。RAS 从提交状态恢复（`BPA_REPAIR=3`）在深窗口下 ret 误预测变多（770 → 2,020），`BPA_REPAIR=1` 可压回 254，但周期只少 0.4%。
  - **30 点结果**（相对 ROB128 / PRF128）：只开紧凑 +2.78%（最差 −2.24%）；**紧凑 + 额度 +2.92%（最差 −1.24%）**：hmmer +9.3%、omnetpp +5.7%、h264ref +4.1%、astar +3.7%、sjeng +2.8%、mcf +2.5%、libquantum +2.5%、perlbench +1.5%、bzip2 +1.4%、xalancbmk +1.2%、gobmk +1.1%、gcc −0.3%；再限制提交最多跨 4 个取指块 +2.88%；紧凑 + 整组等待 +2.55%（紧凑下不需要整组等待）；紧凑 + 整组等待 + PRF160 +2.92%。对照：ROB192 + 整组等待 +2.27%，ROB192 + PRF192 +3.06%。
  - **寄存器版本的额度（`ROB_CPT_CREDIT=3`）**：上面 `=2` 用的是 BPU 当拍算出的队列占用，RTL 里是一条前端到后端的组合路径。`=3` 只用寄存器：额度 = 队列容量 − 本拍开始时的占用 − ROB 上一拍提交的分支数（训练队列用取指块结束数），本拍和下一拍的消化不算回来，偏保守。30 点 **+2.89%（最差 −0.86%）**，与 `=2` 的 +2.92% 基本相同；uBTB 训练丢弃 0，控制流更新丢弃 89 万（`=2` 为 96 万，按行提交 162 万）。gate 两种模式 64/64。各程序：perlbench +2.27%、bzip2 +1.19%、gcc −0.30%、mcf +2.43%、gobmk +0.79%、hmmer +9.29%、sjeng +2.61%、libquantum +2.35%、h264ref +4.35%、omnetpp +5.41%、astar +2.98%、xalancbmk +1.66%。RTL 按这个版本做：BPU 送出两个占用寄存器（4 位、3 位），ROB 记上一拍提交的两个计数，提交选择里各加一组 8 槽前缀计数和比较。
  - **RTL（2026-11-11，rtl `exp/rob-compact`，工作区 `rtl-robc`，`4e954d7`、`a905acd`）**：配置包常量 `ROB_COMPACT`（模型 `CFG_ROB_COMPACT`，默认 0；为 1 时模型默认用寄存器额度），`rob.sv` 按它在原行式 `rob_core` 与新 `rob_core_cpt` 之间二选一。
    - `rob_core_cpt.sv`（新，约 330 行）：存储复用 `rob_entry`（按 `rob_idx` 写，bank 取分发槽里落在该 bank 的那条）；提交窗口 = 每 bank 读队头行或下一行（寄存器保存的队头行独热码、"读下一行"8 位、队头 bank 独热码，不每拍解码指针），再按 bank 独热码旋转到槽顺序；前缀提交（每槽并行算更老的分支数 / 块结束数，与额度比较，前缀"与"并行）；新队头 / 项数按提交条数从预先算好的"加 j / 减 j"里选；分支恢复按项清除比分支更年轻的项；异常、冲刷复用 `rob_trap_ctrl`。
    - 分发（`dispatch_core`、`dispatch_fire_ctl`）：编号 = 尾 + 组内有效槽序号（翻转位跨环），放行检查空闲项数。BPU：`bpu_updq` / `bpu_ub_tq` 输出占用寄存器，经 `bpu_ubtb`、`bpu`、`front_pred_path`、`front_top`、`core_front`、`core_top`、`back_top` 接到 ROB（`commit_upd_free` = 8 − 占用，`commit_tq_free` = 4 − 占用）。共 15 个文件改动加 1 个新文件。
    - 验证：`lint.sh` 通过；`lint_chip.sh` 默认配置、紧凑配置都 0 警告。**紧凑配置 fm_gate 69/69、0 个函数模型不一致、69 个周期与紧凑模型（`build_cpt`，`LSU_PIPE_NOWD=1`）逐个相等**；默认配置 fm_gate 69/69、与原 `ref_cycles.txt` 0 处不同。紧凑配置 RTL Linux 13 段 13/13（每段检查 700 万到 2,450 万条指令，0 不一致；深度优化前、后各跑一遍，结果相同）；模型 `build_cpt` Linux 从复位到 `rv32 login:`，0 不一致。gate 程序周期几何平均与行式 ROB 相比 +0.06%（小程序用不满窗口）。
    - **面积 / 深度**（yosys 通用门代理，`synth_depth.sh`，单元数 / 最长路径级数，相对数字）：

| 配置 | `rob` 单元 | `rob` 深度 | `dispatch` 单元 | `dispatch` 深度 |
|---|---|---|---|---|
| 行式 ROB128（现状） | 316,758 | 46 | 78,558 | 46 |
| 紧凑 ROB128（第一版） | 355,644 | **97** | 81,650 | 47 |
| **紧凑 ROB128（深度优化后）** | **352,903（+11.4%）** | **53（+15%）** | 81,650（+3.9%） | 47 |
| 行式 ROB192 | 342,475（+8.1%） | 49 | 78,553 | 46 |

    - 第一版深度 97：队头指针每拍现解码读哪一行、额度累计计数串行、提交条数先加总再做指针加法，三段串成一条链。改成寄存器保存读选择、并行计数、按条数选择候选指针后为 53；剩下的最长路径是 读出 → 旋转 → 指令分类与额度比较 → 前缀 → 新队头选择。再要降可以把"完成 / 冲刷类 / 分支 / 块结束"这几位在项里算好存下（省掉分类的几级）。
    - 面积：紧凑 ROB128 比行式 ROB192 还多约 1 万单元（写入时每 bank 从 8 个分发槽选一条、读出旋转都是整项宽度的 8 选 1，按项比较的分支清除）。但 ROB192 的代理只统计了 `rob` 模块，没算 ROB 编号加 1 位在发射队列、LSQ、分支标签等处的代价，也没算它要配的整组等待；两者的面积差不大，性能紧凑 +2.89% 对 ROB192 + 整组等待 +2.27%。
- **合入批次**（同一次跑完、一起合入；其余几项都是不改周期的清理或很小的修正）：
  1. 紧凑 ROB + 寄存器额度，`CFG_ROB_COMPACT` 默认 1；
  2. 删掉剩下的非缓存 RAM 窗口和它的访问通路（EXP-027 只删了 0x87f00000；模型 `PeripheralAxi` 的非缓存读、RTL `peripheral_axi` 的 `env_region` 写通路、tb 的辅助函数）：可缓存 = 0x40000000–0x4fffffff、0x80000000–0xffffffff，其余全是 MMIO；`software-interrupt-vectored` 2,254 → 2,356（有一条 load 原来落在窗口里）；
  3. 前端 PMU 事件 `FEO_*`（17 个，来自 `exp/fe-pmu`）和 `scripts/pmu/fe_summary.py`；
  4. 删掉 FTQ / BPU 元数据里存着的 `altpcpn`、`sc_used`（模型、RTL 都删，TAGE 内部仍算 alt）；
  5. 删掉 rtl 分支 `exp/lsu-stwin`（已被 main 覆盖）；
  6. 删掉不再需要的开关（A 组）：TAGE 参数扫描（`BPA_TAGW/CNTW/UW/WEAK/UALT/ALLOC/URST`，固定为 RTL 的值）、统计校正器 `BPA_SC*`、目标缓存 `BPA_NOTC`（连同 BHT、mode 表）、`BPA_CMTSYNC/NOCMTSYNC`、一次性调试打印（`FE_DIAG`、`FE_PCDBG*`、`FE_PAIR_DBG`、`BPU_PIPE_DBG`、`BPA_REPAIR_DBG`、`FE_FUSE_DIAG`）。旧设计回归串里的 `BPA_NOTC=0` 因此不能再还原旧基线（`PROJECT.md` 已注明）。
- **SPEC 全量**（580 点，快速预热 100 万条，预取开，`PMU=1`，本机 8 并行，两种配置都 580/580；`AI-Huma-data/robc/full`，`score2.py` 出分）：

| 程序 | 删窗口后（EXP-027 全量） | 本批，行式 ROB | 本批，紧凑 ROB | 紧凑 vs 行式 |
|---|---|---|---|---|
| perlbench | 10.27 | 10.59 | 10.76 | +1.55% |
| bzip2 | 9.13 | 9.14 | 9.26 | +1.33% |
| gcc | 11.05 | 11.14 | 11.28 | +1.32% |
| mcf | 15.01 | 15.01 | 15.45 | +2.91% |
| gobmk | 10.03 | 10.03 | 10.10 | +0.77% |
| hmmer | 12.81 | 12.82 | 13.40 | +4.55% |
| sjeng | 9.77 | 10.16 | 10.46 | +2.89% |
| libquantum | 14.76 | 14.76 | 15.00 | +1.64% |
| h264ref | 14.35 | 14.49 | 14.99 | +3.50% |
| omnetpp | 7.46 | 7.46 | 7.83 | +5.00% |
| astar | 8.59 | 8.60 | 9.04 | +5.07% |
| xalancbmk | 13.84 | 13.83 | 14.18 | +2.51% |
| **几何平均（分/GHz）** | **11.14** | **11.23** | **11.53** | **+2.74%** |

  - 行式 ROB 这一列就是合入前的 main（含 ITT）实测：11.23，与之前估的 11.22 一致；比删窗口那次全量 +0.74%，来自 ITT（perlbench、sjeng、gcc、h264ref）。
  - 紧凑 ROB 全量 +2.74%，与 30 点的 +2.89% 一致。最好点 astar sp19 +16.4%、gobmk sp39 +16.3%。
  - **已知回退**：gcc 4 个短点慢约 37%（sp48、sp21、sp12、sp2，另 sp5 −26%，权重合计约 0.03，gcc 整体仍 +1.32%）；xalancbmk sp12 −9.5%、perlbench sp38 −8.6%。以 sp48 为例：分支占 36% 的密循环；行式 ROB 时更新队列一直满，396 万次控制流更新丢了 351 万（89%），预测照样好，IPC 4.65；紧凑 ROB 的额度不让提交冲爆队列，305 万次都写进去，但队列每拍只能写回不到 1 条（2 个写口，常被预测读挡住），提交被卡在约每拍 1 个分支，IPC 2.98，ROB 长期近满（平均 119 / 128），前端跟着堵（`s0_stall_ptab` 24 万 → 142 万），误预测反而 4.9 千 → 9.3 千。PMU 把这段记成 `SLOT_BE_SERIAL`，实际是分发被 ROB 空闲项数挡住（归因不准，待修）。大程序同理：dhrystone 114,685 → 116,774（+1.8%）、coremark 283,240 → 284,902（+0.6%），其余 6 个快 1.2–2.1%。
  - 可试的修法（未做）：额度不够时不挡提交，只丢预测正确、计数器已饱和的分支的更新，误预测和要分配新表项的更新照样占额度。
- **合入时的验证**（提交后的代码）：trace-model 默认关时 gate 64/64 与旧基线逐个相同、8 个大程序与标准周期相同；默认开时 gate 64/64 + load-store 全部 difftest Success、0 个 TB_CHECK 不一致，`baseline.csv` 32 个程序变化（−5.2% … +6.0%）；trace-model Linux 从复位到 `rv32 login:`（见 MAIN_RECORDS）。RTL：`lint.sh` / `lint_chip.sh` 两种配置 0 警告；`gen_cfg.sh` 不带 `-D` 生成的包与实验的紧凑包逐字节相同；`fm_gate` 69/69、周期与 `ref_cycles.txt`（37 个程序变化）0 处不同、0 个函数模型不一致；默认关时 fm_gate 69/69 与模型逐个相等；Linux 从复位**一次连续跑到 `rv32 login:`**（不分段，4 线程 tb，逐提交与函数模型对比，约 2 小时 19 分钟），0 不一致。
- **复现**：`~/personal/AI-Huma-data/robc/run.sh <jobs> <cfg>...`（cfg：ctl aon r192 r192aon r192p192 r192p192aon p160），`summary.py` 出表；构建 `gmake LDFLAGS="-lz" DS3_DIR=../trace-model/third_party/DRAMsim3 BUILD_DIR=build_<n> EXTRA_CXXFLAGS="-DCFG_ROB_NUM=192 -DCFG_PRF_NUM=192"`。

---

## EXP-027 最新 TMA 分析与 0x87f00000 非缓存窗口删除

- **日期**：2026-11-11。**分支**：trace-model `exp/no-uncwin`（工作区 `trace-model-uncwin`，基于 main `e84e53a`）、rtl `exp/no-uncwin`（工作区 `rtl-uncwin`，基于 main `1c0d110`）；**2026-11-11 已合入 main**（trace-model `62e4a8b` 删窗口、`07d567c` PMU 缺失标记；rtl `1205bff` 删窗口、`de8d0aa` `tm_cycles.sh`）。诊断用的 `ICM_DIAG` 等仍在 `trace-model-fepmu`（`exp/fe-pmu`，未提交）。
- **问题**：用最新 PMU/TMA 数据决定下一步优化方向。服务器（47.117.141.194）关机，EXP-025/026 全量的逐点 TMA 拿不到，改为本机跑 12 个程序各自权重最高的 SimPoint（快速预热 100 万条、预取开、`PMU=1`，配置 = main：write buffer + 3×64 多表 ITT，`BPA_ITTH=1,2,3 BPA_ITTN=64`）。
- **PMU bug**：默认的流水线 LSU 在 `RealLsuPipe.cpp` `comb_lsu2rob_p` 里用 `uint64_t m |= 1ULL << rob_idx` 做 TMA 缺失标记，ROB 有 128 项，`rob_idx` ≥ 64 的缺失标记丢失（EXP-013 在旧 LSU 里修过同一个 bug）。改为 `std::bitset<ROB_NUM>` 后 12 个点周期逐个相同，但"ROB 头是访存且 L1D 缺失 / 未缺失"的划分大变：libquantum 22.9/22.3 → 43.6/1.7、omnetpp 21.1/26.7 → 41.8/6.1、mcf 20.4/45.9 → 39.2/27.1、bzip2 12.3/21.9 → 24.0/10.2。**此前所有 SPEC TMA 里 "Mem 未缺失" 都偏高**。已随本次合入 main（trace-model `07d567c`）。
- **TMA 一级（修正后，槽位 %，12 点平均）**：Retiring 32.5、BadSpec 6.5、Frontend 26.0、Backend 35.0。要点：
  - 前端：取指组遇到 taken 分支截断是最普遍的损失（占 FEO 槽：libquantum 37%、perlbench 32%、xalancbmk 31%、gcc 28%、astar 23%、mcf 22%、omnetpp 21%）；gcc 另有 27% 是行尾截断；每组平均 3.4–6 条（满宽 8）、每拍约 1 组。gobmk I$ 缺失 23%，sjeng/astar/omnetpp ififo 空 17–26%。
  - 后端：L1D 缺失在 ROB 头占 mcf 39%、libquantum 44%、omnetpp 42%、bzip2 24%；gcc STQ 满 32.6%、ROB 头是 store 14%（0x2df39c 起 6 条连续 store）；DCache bank 冲突重放很多（libquantum 3.3M 个 load 里 1.2M、mcf 1.9M、h264ref 0.66M）。
  - h264ref 34% 槽是"ROB 头是 load 但没缺失"，`LSU_PIPE_STATS` 显示 `mmio_ld=305,749`（其他 11 个点 ≤7K）。
- **根因**：h264ref 的用户数据物理页在 0x87f3a000–0x87f4e000，落在 `SIM_UNCACHE_DDR_RESERVED`（0x87f00000–0x87ffffff，`SD_DMA_POOL`）里，被 `simulator_is_mmio_addr` 当成 MMIO：每个 load 等到 ROB 头、经非缓存单元访存。Linux 设备树 `memory@80000000` 是完整 256 MB，没有 reserved-memory，所以内核把这段当普通内存分给用户。用户确认这段窗口是早先为 SoC 上 DMA 与 CPU cache 一致性问题留下的，后来按 MMIO 访问，可以删除。`LSU_PIPE.md` 第 12 节之前"SPEC 检查点 MMIO load 太多"的疑问即此；那次的"MMIO 豁免"（h264ref −4.9%）优化的是这个假象。
- **改动**：
  - trace-model：`config.h` 删 `SIM_UNCACHE_DDR_RESERVED_*`、`SD_DMA_POOL_*`，可缓存窗口合为 0x40000000–0x4fefffff 与 0x80000000–0xffefffff（删 `SIM_CACHE_ADDR_3_*`）；`mmio_address_map.h` 两处同步；`PeripheralAxi.cpp` 注释。
  - rtl：`ttg_cfg_pkg.sv` 重新生成；`lsu_pkg::is_mmio_addr` 改两段；`tb/soc/platform/include/{config.h,mmio_address_map.h}` 同步；`scripts/ref_cycles.txt` 3 个程序；`scripts/tm_cycles.sh` 修原有 bug（没有导出 `ROOT`，`directed/*` 程序路径为空、挂住）。
- **验证**：
  - trace-model gate 64/64 全部 difftest Success；3 个程序周期变化：fence-i-self-modify 1405 → 1407、recursion 2876 → 2878、vm_pagefault_test 19060 → 19212（栈/页表在 0x88000000 以下），`baseline.csv` 待更新。大程序 8 个与 PROJECT.md 标准周期逐个相同（dhrystone 114,685、coremark 283,240、memory-stress 2,358,268、smc-div 10,875、smc-addi 10,315、memory-stress-small 329,424、pf-stress 630,916、itt-dispatch 222,445）。Linux 从复位到 `rv32 login:`，0 不一致（网络 FAIL 与旧版相同）。
  - rtl：`lint.sh`、`lint_chip.sh` 0 警告；`fm_gate` 69/69，0 个函数模型不一致，周期与新的 `ref_cycles.txt`（`LSU_PIPE_NOWD=1`）**0 处不同**。合入后补跑 RTL Linux 13 段（s01–s13，本机 13 个并行，每段 1600 万周期，逐提交与函数模型对比）13/13 通过，每段检查 692 万到 2424 万条指令，0 不一致。
- **SPEC 全量 580 点**（快速预热、预取开、`PMU=1`、本机 12 并行；构建 = `exp/fe-pmu` + 窗口改为可缓存，不设 ITT 环境变量即 main + write buffer；基线 `AI-Huma-data/stwb/full/new` 同口径，抽查 gcc sp0、h264ref sp17 两点用不改窗口的同一构建周期逐个相同）：580/580 完成，0 不一致；**12 程序几何平均 IPC +10.75%**；78 个点变化 > 1%，**全部变快**。
  - h264ref 1.465 → 3.480（**+137.5%**，35/37 点 > 1%，单点最高 +270%）；hmmer 3.629 → 4.889（**+34.7%**，26/34，最高 +158%）；perlbench 2.501 → 2.658（**+6.3%**，12/44）；xalancbmk +0.25%；gcc +0.04%；omnetpp −0.16%；其余 6 个 ±0.02% 以内。
  - hmmer、perlbench 权重最高的点没踩到这段地址，所以单点分析看不出；之前所有 SPEC 基线里这三个程序的数字都被压低。
- **分数重新核对（直接换算，不再连乘）**：参考时间与 spec.org 官方结果 `cpu2006-20060513-00042.txt` 逐个核对，12 个都与以前用的相同（perlbench 9770、bzip2 9650、gcc 8050、mcf 9120、gobmk 10490、hmmer 9330、sjeng 12100、libquantum 20720、h264ref 22130、omnetpp 6250、astar 7020、xalancbmk 6900）；分数 = 参考时间 × IPC × 1 GHz / 总指令数，总指令数 = BBV 区间数 × 1000 万（`spec-rv32imab/status/<bench>.txt`），用旧表反推的指令数与它相差 ≤0.1%，说明以前的换算方法本身是对的。程序 IPC = 1/Σ(w·CPI)（SimPoint 权重）。脚本 `~/personal/AI-Huma-data/mmio/score.py`。结果（分/GHz，12 个比值的几何平均）：main + write buffer（EXP-024）**10.06**；当前 main（+ 多表 ITT，`AI-Huma-data/itt/res_new_lines.txt`）**10.13**；main + write buffer 删窗口 **11.14**；当前 main 删窗口（按程序把删窗口的 IPC 比值乘到 ITT 结果上，估算）**约 11.22**。**此前文档里连乘得到的 10.46 / 10.53 偏高约 4.7%**：起点 9.42 是近似值，中间还换过基线，以后都用 `score.py` 直接算。
- **下一步优化的排序（基于修正后的 TMA）**：① 合入删窗口 + PMU 修正，重建 SPEC 基线；② 前端取指带宽（`FE_PAIR` 一拍两块，EXP-023 25 点 +2.88%，加 `FE_IPF` +5.22%，RTL 代价大；或先做一拍跨行取指解决 gcc 行尾截断）；③ L1D 缺失（sdip `PF_SDIP=2`，EXP-026 +1.74%，RTL 未做）；④ gcc 连续 store 的写回带宽；⑤ DCache bank 冲突重放；⑥ BadSpec（gobmk、mcf、sjeng、astar）与 gobmk I$ 容量。
- **复现**：TMA 数据 `~/personal/AI-Huma-data/fepmu/tma_fix`（`run.sh <out> <jobs> 1 <bench>...`，`BPA_ITTH=1,2,3 BPA_ITTN=64`），`scripts/pmu/spec_summary.py`、`fe_summary.py`；`LSU_PIPE_STATS=1` 数据 `fepmu/lsustat`；全量 `~/personal/AI-Huma-data/mmio/full.sh <cfg> <simulator> <jobs>`、对比 `mmio/cmp.py <base> <new>`（权重取自 `spec-rv32imab/sp/<bench>.weights`；`points_full.txt` 第 4 列是旧 IPC 不是权重），结果 `mmio/cmp_result.txt`；Linux `~/personal/AI-Huma-data/linux/uncwin`；RTL `~/personal/AI-Huma-data/uncwin_rtl`。trace-model macOS 构建：`gmake LDFLAGS="-lz" DS3_DIR=../trace-model/third_party/DRAMsim3`。

---

## EXP-026 sdip（Breadcrumbs）数据流预取器，挂在重命名阶段

- **日期**：2026-11-10。**分支**：trace-model `exp/sdip`（`ffdae56` 模型、`e81aef2` 只预取 DDR 地址；工作区 `trace-model-sdip`，基于 main `e84e53a`），**未合入、未推送**；RTL 没有做。设计与 ChampSim/gem5 上的实验记录在 trace-model `exp/regdataflow`（`docs/experiments/exp022_regdataflow.md` §27、§31、§32、§38）。
- **非 SPEC 负载的流程**（EXP-022 的 GAP / PolyBench / Ligra / Olden 数据）：镜像、BBV、SimPoint、检查点见 `function-model/scripts/wl/README.md`（只支持 rv32imab，数据目录 `~/personal/AI-Huma-data/wl-rv32imab`）；trace-model 的 `scripts/pf/run_point.sh` 设 `SPEC=$WLDATA` 即可回放。
- **问题**：EXP-022 里的 sdip（约 2 KB 状态）在 ChampSim 上对 SPEC 与 Berti 持平、对 GAP/PolyBench 间接访问很强；用户提出它的硬件开销很小、主要补间接访存。它在我们的周期模型里相对默认的 h1（EXP-009）有多少收益，能不能替换 h1。
- **实现**（`MemSubSystem/include/Sdip.h` 一个头文件，开关 `PF_SDIP=0|1|2`，默认 0：模型逐周期等同 main，gate 63/63；`1` = sdip 替换 h1，`2` = sdip 候选先发、h1 在后）：
  - **重命名阶段**（`Ren::comb_fire`）：每个物理寄存器一个标签（仿射步长 / 新指针 / 写者 PC / 来自某条 32 位 load 的链及左移量），由指令编码和源寄存器标签算出；16 项栈槽保存/恢复标签；load 带着 dsig（步长或类别）和链信息走到 L1D（LSU 把 PC、VA、dsig 作为旁带传给 L1D 第 2 级）。
  - **提交阶段**（`BackTop` 在 `on_commit` 之前读 fact）：提交的 32 位 load 记录值（32 项，按实例号），提交的消费者训练关系（生产者 PC → 消费者 PC、移位、c = 地址 − (值 << 移位)，64 项）。
  - **L1D 第 2 级**：每条 demand load 进入引擎（命中、缺失、预取行第一次使用），按"进入新行才发"（64 项按 PC 的上一行表，`PF_SDIP_LASTLINE=1`）发 stride 预取（距离 `max(4, ⌈8 行/|S|⌉)` 步，步长 ≥ 一行取 16 步）；没有数据流步长的 load 用 64 项 PC 步长表（只由缺失和预取行首次使用训练）；兜底：缺失时预取下一行、新指针缺失时预取后 8 行，受全局准确率门控（每 1024 个一轮，有用比例 < 1/16 就关，保留 1/16 抽样）。
  - **间接**：只由 L1D 填回触发——生产者 demand 填回、带元素标记的间接预取填回（串多级）、生产者自己的 stride 预取填回（读该行里步长碰到的所有元素）；元素值取自填回行（模型里读功能内存）；目标 `(值 << 移位) + c`，经只读 DTLB 探测翻译，查不到就丢。`PF_SDIP_RES=1`（默认，同 `sdip.h` 的 `res`）：生产者下一行已在 L1D 时直接读它的元素（**需要 L1D 数据阵列读口**）；`PF_SDIP_RES=0`：间接预取只由填回触发，不读 L1D 数据阵列。
  - 候选进 32 项 FIFO（每周期一个探测口，去重），其余沿用 h1 的 L1D 探测、MSHR 与填回通路；`PF_SDIP_NOIND=1` 去掉间接部分，`PF_SDIP_NOSTRIDE=1` 去掉 stride/兜底，`PF_SDIP_LA`、`PF_SDIP_FBTHR`、`PF_SDIP_FRESH` 等为参数；`[SDIP-STATS]` 在 stderr 里给出各来源计数。
- **状态（硬件估算，bit）**：重命名标签 128 × 22 = 2,816；栈槽表 16 × 55 = 880；提交值表 32 × 40 = 1,280；关系表 64 × 59 = 3,776；PC 步长表 64 × 64 = 4,096；上一行表 64 × 58 = 3,712；缺失过滤器 256；每个 L1D 行 2 位元数据 2,048；候选 FIFO 32 × 60 = 1,920；合计约 20.8 Kb（≈ 2.6 KB），h1 是 418 bit。
- **模型里的近似（硬件做不到或需要额外代价）**：① 元素值从功能内存读（硬件是填回数据）；② 标签里的 PC、实例号是全宽（硬件要哈希）；③ 候选翻译用无副作用的 DTLB 探测（硬件：每个候选一次额外 DTLB 查找，查不到丢弃；`xl_fail` 在 mcf 点上占候选的约 25%）；④ 填回触发、FIFO 入队没有速率限制（`peak_push` 每周期最多 8~30 个候选）；⑤ 每周期最多处理 4 个访问事件（= load 口数），上一行表要 4 个读口；⑥ PC 步长表只由缺失和预取行首次使用训练（原版由所有访问训练）；⑦ 没有自适应距离（`PF_SDIP_ADAPT`，EXP-022 §38 中也只是 libquantum 受益）；⑧ 预取只发往 DDR 地址（`pa >= 0x80000000`）。
- **一个 bug**：第一版没有地址范围过滤，gobmk 两个点（sp10 的 `PF_SDIP=2`、sp46 的 `PF_SDIP=1`）出现 ROB 死锁（预取发往非 RAM 物理地址，MSHR 永远等不到响应）。加过滤后（`e81aef2`）重跑这两个点；其余结果用的是过滤前的二进制（17 点用修复后的二进制重跑，几何平均 +5.31% → +5.35%，没有实质变化）。
- **结果 1：SPEC 全量 580 点（快速预热、`PMU=1`、服务器，对 main 的 h1，基线是同一台服务器上的 main 全量结果，17 点上逐点验证过 PF_SDIP 关闭时周期逐个相同）**

| 程序 | 点数 | `PF_SDIP=1`（替换 h1） | `PF_SDIP=2`（sdip + h1） |
|---|---|---|---|
| mcf | 79 | +8.63% | **+9.38%** |
| gcc | 55 | +3.97% | **+5.79%** |
| bzip2 | 76 | +2.51% | **+3.11%** |
| astar | 35 | +0.87% | +1.32% |
| xalancbmk | 51 | +0.94% | +0.82% |
| hmmer | 34 | +0.63% | +0.66% |
| perlbench | 44 | +0.12% | +0.38% |
| libquantum | 51 | **−11.85%** | +0.33% |
| gobmk | 50 | +0.17% | +0.29% |
| h264ref | 37 | −0.37% | +0.02% |
| sjeng | 28 | −0.15% | −0.17% |
| omnetpp | 40 | −2.97% | −0.57% |
| **12 程序几何平均** | 580 | **+0.10%** | **+1.74%** |
| 580 点几何平均 | | +0.67% | **+2.41%** |

  `PF_SDIP=2`：118 个点 > +2%，50 个点 < −2%，5 个点 < −5%（xalancbmk sp34 −15.5%：兜底预取 24 万次只有 9% 有用，h1 的 `probe_mshr_full` 11 万；omnetpp sp22 −9.1%、mcf sp20 −6.1%、gcc sp36 −5.9%、astar sp27 −5.2%）；mcf 的最大点 +74%（sp72）。`PF_SDIP=1`：108 个点 > +2%，132 个点 < −2%，43 个点 < −5%（libquantum 的所有点 −19% ~ −25%）。
- **结果 2：30 点（精确预热，8 个程序：perlbench 2、gcc 3、mcf 8、gobmk 4、hmmer 4、sjeng 4、h264ref 2、astar 3；对 h1）**

| 程序 | `PF_SDIP=1` | `1`, `RES=0` | `PF_SDIP=2` | `2`, `RES=0` |
|---|---|---|---|---|
| perlbench | −0.77% | −0.73% | −0.57% | −0.95% |
| gcc | −0.20% | −0.18% | −0.09% | +0.07% |
| mcf | +9.16% | +7.55% | +10.44% | +8.67% |
| gobmk | −0.07% | +0.03% | +0.23% | +0.21% |
| hmmer | +2.76% | +2.65% | +2.82% | +2.84% |
| sjeng | −0.24% | −0.11% | −0.20% | −0.10% |
| h264ref | 0.00% | +0.02% | −0.03% | +0.04% |
| astar | −0.08% | −0.21% | −0.09% | −0.21% |
| **几何平均** | **+2.61%** | +2.22% | **+3.01%** | +2.56% |

- **结果 3：17 个点（12 个程序的最高权重点加 mcf sp29/sp51/sp60、omnetpp sp36、xalancbmk sp21/sp46、gcc sp16；快速预热）及消融**

| 点 | `1` | `2` | `1`, `RES=0` | `1`, 无间接 | `2`, 无间接 |
|---|---|---|---|---|---|
| mcf sp29 | +50.95% | +50.97% | +42.10% | +29.63% | +28.94% |
| mcf sp51 | +36.62% | +37.56% | +29.99% | +17.94% | +19.70% |
| mcf sp60 | −4.95% | −4.66% | −4.93% | −4.91% | −4.54% |
| bzip2 sp74 | +6.57% | +9.37% | +6.59% | +6.59% | +9.41% |
| hmmer sp26 | +3.31% | +3.32% | +3.34% | +3.30% | +3.38% |
| xalancbmk sp21 | +0.49% | +1.40% | **−5.48%** | +0.55% | +1.80% |
| xalancbmk sp46 | +2.93% | +7.41% | +2.16% | +1.24% | +7.26% |
| libquantum sp15 | **−20.33%** | −0.11% | −20.40% | −20.43% | −0.05% |
| omnetpp sp12 / sp36 | −3.32% / −4.59% | −0.16% / −0.65% | −3.12% / −4.78% | −3.49% / −4.98% | −0.77% / −1.09% |
| 其余 6 个点 | 各 ±0.8% 以内 | 各 ±0.6% 以内 | 同左 | 同左 | 同左 |
| **17 点几何平均** | +2.90% | **+5.31%** | +1.81% | +0.99% | +3.44% |

  - **mcf 的收益来源**：去掉间接部分（stride + PC 步长表 + 兜底）仍有 sp29 +29.6%、sp51 +17.9%，间接部分再加 +21 个、+19 个百分点（sp29 +51%、sp51 +37%）。bzip2、hmmer、gobmk 的收益全部来自 stride/PC 表（去掉间接不变）；xalancbmk sp46 mode 1 间接 +1.7 个百分点，mode 2 下 stride 已占大头（+7.26% 无间接、+7.41% 有间接）。
  - **间接部分需要读 L1D 数据阵列吗**：`PF_SDIP=1` 的间接预取里，mcf sp29 有 233K 个（60%）来自"生产者下一行已在 L1D"的读，157K 个来自填回；sp51 16K 对 10K；xalancbmk sp21 8K 对 14K、sp46 6K 对 20K。关掉读（`RES=0`）后：mcf sp29 +51% → +42%、sp51 +37% → +30%（保留约 80%）、xalancbmk sp21 +0.5% → −5.5%、sp46 +2.9% → +2.2%；17 点几何平均 +2.90% → +1.81%（只留 63%），30 点 +2.61% → +2.22%（85%）、`PF_SDIP=2` +3.01% → +2.56%（85%）。**结论：不读 L1D 数据阵列（只由填回触发）能保留 mcf 收益的 80% 左右、30 点收益的 85%，但 xalancbmk 会变负，所以"不需要额外读口"在 SPEC 子集上不是无损的。**
  - **能不能替换 h1**：不能。`PF_SDIP=1` 在 libquantum 上所有点 −19% ~ −25%（`PF_SDIP_LA=16/32` 变得更差，−28.7% / −31.3%，所以不是前瞻距离不够；原因没有进一步查，疑似 h1 的 LLC-only 下一行引擎和"每次 8 步突发"对 libquantum 这种高带宽流有关），omnetpp −3% ~ −5%，而 `PF_SDIP=2` 保住了这些程序。所以只有"sdip 在前、h1 在后"（`PF_SDIP=2`）成立；`PF_SDIP=1` 的 12 程序几何平均只有 +0.10%。
- **回退点**：`PF_SDIP=2` 下 xalancbmk sp34（−15.5%）、omnetpp sp22（−9.1%）的兜底预取（下一行、新指针后 8 行）准确率很低（9%、<1%），门控门槛 1/16 太松；没有扫门槛和 8 行的参数，没有进一步查 mcf sp20/sp60、gcc sp36、astar sp27。
- **RTL 代价估计（没有做）**：① 重命名阶段：每个物理寄存器 22 位标签（128 × 22 位）加一个规则网络（加/移位/shNadd/自增/栈槽，同组内要旁路），每个重命名槽读两个标签、写一个，8 槽/拍；比 `ren` 现有关键路径的深度不详，需要综合；② load 要把 dsig（32 位）和链信息（PC、实例号、移位）带到提交（ROB/LDQ 每项约 +70 位），L1D 第 2 级要多收 PC 和 VA 旁带；③ 提交阶段：32 项值表、64 项关系表训练，按提交宽度（8）的 load 数处理；④ 每个候选一次额外 DTLB 探测（每周期最多 4~8 个，模型未限速）；⑤ `RES=1` 需要 L1D 数据阵列读口（间接部分）；填回触发需要按"填回行的元素"读数据（可从填回缓冲区读，不用阵列口）；⑥ 上一行表每周期 4 读 4 写。状态合计约 2.6 KB，对比 h1 的 418 bit。重命名阶段的标签网络和 DTLB 探测口是主要的实现风险。
- **可复现**：`PF_SDIP=2 PF_ENABLE=1 FASTWARM=1000000 PMU=1`（运行时环境变量）；服务器 `/root/sdip/res/{full_sd1,full_sd2,ctl,sd1,sd2,sd1r0,sd1_noind,sd2_noind,p30_*}`、`/root/sdip2/res/{sd1,sd2,sd1_la16,sd1_la32}`；构建与批跑见 docs/SERVER.md。`full_sd1r0`（`PF_SDIP=1 PF_SDIP_RES=0` 全量）按用户要求停掉，没有跑完。
- **没有做**：RTL；全量上的 `RES=0`；自适应距离；兜底门控与 8 行参数的扫描；ROB 死锁之外的失败点分析；对 EXP-014 的缓存替换和 EXP-018 SMS 的对比；GAP/PolyBench 点（我们的标准分数是 SPEC INT）。

## EXP-025 前端带宽拆分、I$ 容量与替换、间接跳转预测（多表 ITT）

- **日期**：2026-11-10。**分支**：trace-model `exp/itt-multi`（`5d8cf66`，工作区 `trace-model-itt`）、rtl `exp/itt-multi`（`efaa350`，工作区 `rtl-itt`）；PMU 前端拆分、`ICM_DIAG`、`ICACHE_REPL`、`CFG_ICACHE_WAY_NUM` 在 trace-model `exp/fe-pmu`（工作区 `trace-model-fepmu`，基于 main `55c9f64`，**未提交**）。
- **问题**：TMA 里前端空槽最大（`fBW` 占 FE 的 90% 以上），不知道是"每拍只取一个块"还是延迟。
- **PMU 前端拆分**（`FEO_*`，model-only，不进 RTL 总线，开关 PMU 周期不变）：在前端到后端的接口按取指组计槽（每拍 8 槽，只算后端能读的拍），短组按结尾原因分（以 taken 分支结尾 / 到 64B 行尾 / 其他），空拍按原因分（重定向重填、I$ 缺失、预译码冲刷、BPU 覆盖气泡、PTAB 停顿、指令 FIFO 空等）。`scripts/pmu/fe_summary.py`。9 个前端受限程序各取最高权重点：
  - **形状限制**（gcc、xalancbmk、perlbench、libquantum、h264ref）：每拍 0.85~0.99 个组、每组 3.4~5.6 条，丢槽主要是以 taken 结尾（15~37%）和到行尾（gcc 27%、xalancbmk 13%、perlbench/h264ref 10%）；BPU 覆盖气泡、PTAB 停顿、I$ 未就绪几乎为 0。
  - **空拍多**（gobmk、sjeng、astar、omnetpp）：每拍 0.5~0.7 个组；gobmk I$ 缺失 22.5%，sjeng/astar 指令 FIFO 空 22~25%，重填 3~11%。
  - `FE_PAIR` 是"2-taken"（一拍跨一个 taken 分支取两块），不是 2-ahead；"到行尾"的丢槽用越过行边界取指就能拿，比 2-taken 便宜（没做）。
- **I$ 容量与替换（单点，gobmk sp24 为主）**：热代码约 95 KB（1,483 条不同的行），32 KB I$ 反复颠簸：115,320 次缺失中 98.7% 是重复缺失，回填平均 10.4 拍（LLC 命中）。EXP-014 已有同样的容量结论（L1I 64KB +1.3%、gobmk +15%）。
  | 改动 | gobmk IPC | 缺失 |
  |---|---|---|
  | 12 路（48 KB） | +12.0% | 30,508 |
  | 16 路（64 KB） | +15.25% | 10,753 |
  | `FE_IPF` 预取 | +7.75% | — |
  | BIP（真 LRU，1/32 插 MRU） | +5.23% | 74,365 |
  | BRRIP | +5.46% | — |
  | SRRIP / 树形 PLRU+BIP | +3.96% / +3.93% | — |
  | LRU / 随机 | +1.56% / +0.06% | 101,827 / 115,430 |
  | victim buffer（影子统计，全相联 LRU） | 16 项接住 5.9%、32 项 11.6%、128 项 35.7% | — |
  - 9 个点几何平均：16 路 +1.93%（几乎全是 gobmk，其余 8 个约 +0.4%）、PLRU+BIP +0.21%、SRRIP +0.25%、`FE_IPF` +0.75%。只为 gobmk 加容量不划算；替换策略几乎不花硬件但全集收益很小（EXP-014 估 SRRIP 全集 +0.30%）。**未做 RTL**。
- **perlbench 的 ±2% 假退化**：perlbench 在加大 I$（−1.95%）、预取（−2.09%）、PLRU/SRRIP/BRRIP/LRU（−1.45%~−2.16%）下都变差，随机替换却 +1.68%。7 种策略的周期完全跟着已提交 JALR 误预测次数走（7,440~13,550，每次约 17 拍），I$ 缺失只有 600~700 次、条件分支误预测不变；三个不同策略停在完全相同的 13,550。原因：BTB/ITT 的间接目标靠提交时更新队列训练，对取指节奏敏感。**含义：评估前端改动时 perlbench 的单点数不可信，要看 JALR 误预测是否相同。**
- **多表 ITT**：模型里原来就是 ITTAGE 风格（复用 TAGE 某张表的索引和标签，每 bank 一张 256 项、历史 13 位，RTL 与之对齐）。只有这一张短历史表时 sjeng 20,051、perlbench 9,896、h264ref 4,974 次 JALR 误预测（约占周期 7.1%、6.0%、1.9%）。BPA_ITTH/BPA_ITTN 扫描（3 个 JALR 重的点，相对 1 张 13 位 256 项）：
  | 配置（每 bank 总项数） | sjeng | perlbench | h264ref | 几何平均 |
  |---|---|---|---|---|
  | 关 ITT | −9.6% | −5.6% | −0.1% | −5.2% |
  | 1 张 32 位 / 119 位 | +3.35% / −1.29% | −2.27% / +0.60% | +1.24% / +1.63% | +0.75% / +0.31% |
  | 2 张 13+119，每表 256（512） | +5.05% | +11.02% | +1.70% | +5.85% |
  | 2 张，每表 128（256，存储同现状） | +3.92% | +10.98% | +2.07% | +5.59% |
  | 3 张 13+32+119，每表 256（768） | +7.20% | +11.02% | +1.69% | +6.57% |
  | **3 张，每表 64（192）** | +5.67% | +11.02% | +1.70% | +6.06% |
  - 更早的 `BPU_ACC.md` 4.1 节结论是"一张表就够，两张只多 +0.13pp"：那次是零气泡 BPU、方向历史、有 TC 回落、14 点，与现在的流水化 BPU + taken 路径历史（13 位只覆盖约 4 个 taken 分支）不同，不能沿用。
  - **选定**：3 张表 × 64 项，TAGE 历史表 1/2/3（13/32/119 位），预测取最长历史的命中，更新沿用单表规则（提供者命中同目标则计数加、不同则减/置换；提供者不对或没命中时向更长的表分配，经过的更长项 useful 清零）。每项 42 位，8 bank 共 64.5 Kb，比原来的 86 Kb 少 21.5 Kb。模型默认 `CFG_ITT_H="1,2,3"`、`CFG_ITT_SIZE=64`（环境变量 `BPA_ITTH`/`BPA_ITTN` 仍可覆盖）。
- **新增测试** `itt-dispatch`（tests/extra、rtl `programs/directed`）：周期 64 的字节码分派，jalr 调用加 computed goto，模型周期 222,445（3 张表）/ 345,573（原 1 张 256 项）/ 570,723（关），gate 因此是 64 个程序。原来的 63 个程序周期**没有任何变化**（它们覆盖不到多表）。
- **验证结果**：
  - trace-model gate 64/64；服务器构建与本机周期一致（旧配置 xalancbmk 点 2,867,154）。
  - **SPEC 全量 580 点**（快速预热、PF 开、PMU 开，服务器 47.117.141.194，相对 main + write buffer 的全量结果）：12 个程序几何平均 IPC **+0.67%**。sjeng +3.77%、perlbench +3.16%、h264ref +0.53%、gcc +0.38%，其余（bzip2、mcf、gobmk、hmmer、libquantum、omnetpp、astar、xalancbmk）−0.02%~+0.08%。58 个点变化超过 2%，其中 <−2% 的 3 个（perlbench sp13 −4.5%、gcc sp29 −3.8%、xalancbmk sp31 −3.3%）没有查，perlbench 的单点结果见上面的假退化。
  - **RTL**（`bpu_stage_pkg` 的 `NITT=3`、`ITT_IDX_W=6`、`ITT_TBL='{1,2,3}`；`bpu_btb_bank/upd/sel`、`bpu_main_lane/sel`、`bpu_banks`、`bpu` 共 8 个文件）：`bpu` 目录 lint 0 警告；`fm_gate` 69/69（68 + `itt-dispatch`）、0 个 `[FM]` 不一致、**与模型周期逐个相等（0 个不同）**；`itt-dispatch` RTL 222,445 = 模型；`ref_cycles.txt` 只改了 coremark 283270→283240、dhrystone 114418→114685 并加了 `itt-dispatch`。综合（通用门级数，单元数/深度，对 main 同条件）：`bpu` 237,174→242,631（+2.3%）、141→141；`front_pred_path` 243,614→250,251（+2.7%）、142→144（+1.4%）；`bpu_main_sel` 20,004→23,904、70→69；`bpu_btb_sel` 829→1,128、34→33。深度都在 5% 判据内。**Linux**：13 段（s01–s13 接力，服务器，每提交逐条对比）13/13 通过，每段检查 690 万到 2420 万条指令，0 个 `[FM]` 不一致。**从复位连续启动（服务器单进程，4 线程，逐提交对比）一直走到 `rv32 login:`，0 个 `[FM]` 不一致**（2026-11-10，约 2.5 小时）。
- **后续量的两个便宜项（2026-11-10，9 个最高权重点，快速预热，对本次 ITT 默认）**：
  - **RAS 修复档（`BPA_REPAIR`，默认 3 = 历史从检查点还原、RAS 取已提交状态；1 = RAS 用压缩检查点；2 = 整份 RAS 拷贝，理想上界）**：模式 2 几何平均周期约 −0.2%（gobmk −0.87%、omnetpp −0.84%、sjeng −0.32%，其余基本不变），模式 1 约持平（xalancbmk +0.36% 变慢）；dhrystone 上 ret 误预测 800 → 290/230、周期 −0.9%/−0.4%。结论：能做到的压缩检查点没有收益，**不做**。TODO 里"dhrystone 两条 `ret` 约 100% 误预测"已过时（现在约 1%）。h264ref 的 6,400 次 ret 误预测对修复不敏感，原因未查（疑 RAS 深度）。
  - **TAGE 参数与循环预测器扫描（IPC 相对默认，9 点几何平均）**：`BPA_HLEN=4,9,20,60` −0.67%、`4,9,20,40` −1.42%、`8,13,32,60` −0.42%（astar −4%~−7%，且连带改了 ITT 用的历史长度），每表 512 项 −0.51%（gobmk −1.9%、sjeng −1.2%），每表 2048 项 +0.35%（gobmk +1.8%、sjeng +0.9%），**`BPO_LOOP=1`（S0 单块循环退出预测，默认关）+0.60%，几乎全来自 xalancbmk +4.79%**（gobmk +0.61%，其余 ±0.1%）。更短的历史在新的 taken 路径历史下不再有收益（旧的零气泡 BPU 上曾 +0.5~0.7%）；加表容量收益小；循环预测器值得单独看（xalancbmk 点单点，需要更多点和 RTL 代价评估，`BPU_pipe.h` 里已有模型）。
- **没有做**：RTL 上的 SPEC；I$ 替换策略和容量的 RTL（BIP/SRRIP 只在 gobmk 等点上有收益，全集预计零点几个百分点）；越过行边界取指和 `FE_PAIR` 的 RTL；上面三个 −3%~−5% 的退步点；ITT 表的目标压缩。
- **复现**：`~/personal/AI-Huma-data/fepmu`（`run.sh` 取每个程序最高权重点，快速预热）、`~/personal/AI-Huma-data/itt`（全量脚本 `full.sh`、`res_new_lines.txt`）、`~/personal/AI-Huma-data/itt_rtl`（周期对照表、`gate_itt`、综合日志）。

## EXP-024 已提交 store 的 write buffer（STQ 内分组）

- **日期**：2026-11-09。**分支**：trace-model `exp/store-wb`（`55c9f64`，工作区 `trace-model-stwb`）、rtl `exp/store-wb`（`ef6da65`，工作区 `rtl-stwb`）；已合入 main（2026-11-09），已推送。
- **问题**：最新 TMA 里 gcc 的 STQ 满占 45% 的槽。瓶颈是 STQ 容量，还是已提交 store 写 L1D 的带宽。
- **方法和结论的演变**：
  1. **容量上限实验**（`CFG_STQ_UNC`，已删除）：gcc sp42 上 STQ 64 → 128 项、已提交 store 不占 dispatch 容量，周期 +0.04%（7,216,215 → 7,218,766）；STQ 在 94% 的时间 ≥120/128 仍然是满的：**瓶颈是排空带宽，不是容量**。base 的 3 个排空口全程饱和（排空请求 21.4M 次 ≈ 3 口 × 7.2M 周期），这个点 10M 条指令里有 7.66M 个 store，每个 store 平均发送约 2.8 次（重放 6.1M 次），原来没有任何合并（`merge_pair` 恒为 0）。
  2. **同 line 合并的上限模型**（`LSU_PIPE_MERGE`，默认关）：同一周期内同 line 的 store 共用一个排空口。gcc sp42 周期 −22.8%（7,216,215 → 5,567,370），但 gcc 的另外 6 个高权重点平均只有 +0.24%，sp42 是个别极端点（store 占 77%）；12 个程序各取权重最高的点没有回退。L1D 的 bank 按 set 号交错（`bank = set_idx & 15`），同一条 line 在同一个 bank，合并的 store 只占一个 bank。
  3. **in-drain 配对的 RTL（cD：16B 粒度、每口 2 个、6 个候选、2 口，模型 +7.22%）**：RTL 周期与模型逐个相等，但 `lp_drain` 深度 110（main 83），`lsu` 169（main 130）：配对要等冲突 CAM 的结果，排在关键路径最后；并行化配对反而 154；限制配对范围（`MADJ`）和"先配对后用 CAM 屏蔽"（`MSPEC`）的收益损失太大（+5.4~6.8%、hmmer 变负）。**放弃**。
  4. **write buffer（本次合入）**：合并发生在 store 进入缓冲区时，不在排空的关键路径上。
- **最终设计**（开关 `CFG_LSU_PIPE_WBUF=4` 默认开，`WBMAX=2`、`WBINS=4`、`WBSCAN=4`、`DRAIN=2`，运行时 `LSU_PIPE_WBUF` 等；`WBUF=0` 加 `DRAIN=3` 回到合入前的行为）：
  - 4 个条目，每个条目最多 2 个同一 cache line（`LSU_PIPE_MGRAN=64`）的已提交 store，条目里存两个 STQ 序号和地址、数据副本；**store 仍留在 STQ 里，响应回来才退休**（所以 load 的转发和冲突检查不变，STQ 容量没有释放）。
  - 排空决策只读寄存器里的缓冲区：条目在等待、其中所有 store 就绪、没有被更老的条目挡住（字节重叠，只在条目之间比），就按年龄顺序占用空闲口（2 个）；一个条目是一个 DCache 请求，第二个 store 走 DCache 的第二字通路，响应由领头 store 的响应带给跟随者。
  - 插入在决策之后：每周期最多 4 个已提交 store（MMIO 和被取消的只占一个插入名额），合并进最年轻且还在等待、本周期没有被发出的条目，否则新开条目；满了就停；新条目下一个周期才能发；LR/SC 不合并。
  - 响应：领头 store 命中就释放条目，否则条目回到等待（可以继续合并）；看门狗清掉 `iss` 时条目也回到等待。
- **负载和结果**（trace-model，精确预热，10M 预热 + 10M 测量，本机）：
  - 参数扫描用 gcc sp42、h264ref、hmmer、perlbench、gobmk 各 1 个点（对不合并，几何平均 IPC）：4 / 8 / 16 项 +7.35% / +7.34% / +7.34%；2 项 +6.03%；每周期只插入 1 个 −2.50%、2 个 +6.58%、4 个 +7.35%；单口 +7.07%；粒度 32B +7.28%、16B +6.01%；每条目最多 2/3/4 个 +7.26% / +6.47% / +7.39%；每周期看 2 个条目 +6.07%。perlbench 对时序很敏感（+0.2% 到 −4% 随机波动，条目数、口数的小变化都会让它跳）。
  - 硬件友好的时序（决策只读寄存器、先决策后插入、新条目下一周期才可发、合并只进未发出的最年轻条目）比无时序约束版本低 0.3pt：4 项、每条目 2 个、2 口为 **+6.95%**（cD 的 in-drain 配对是 +7.22%）。
  - **12 个程序各取权重最高的点，合入前 main 配置 → 新默认值（IPC）**：perlbench +0.22%、bzip2 −0.08%、gcc +29.59%、mcf +0.13%、gobmk +0.65%、hmmer +3.80%、sjeng 0.00%、libquantum +0.11%、h264ref +3.11%、omnetpp −0.13%、astar +0.06%、xalancbmk 0.00%，**几何平均 +2.85%**（最差 −0.13%）。数据 `~/personal/AI-Huma-data/stwb/sw1..sw4`。
  - **SPEC 全量 580 点（快速预热 100 万条指令，预取开，本机并行 8，580/580 成功，无失败点）对合入前 main（`integ`，同样口径，逐点周期与本机 main 配置复现 58/58 相同）：12 个程序几何平均 IPC +0.68%**（按 SimPoint 权重加权同为 +0.68%）：gcc +4.80%（加权 +4.37%）、hmmer +1.45%、gobmk +1.07%、h264ref +0.30%、libquantum +0.19%、perlbench +0.12%、astar +0.12%、mcf +0.05%、bzip2 +0.02%、omnetpp +0.03%、sjeng +0.03%、xalancbmk +0.03%；最好点 gcc +47.92%，最差点 h264ref −6.25%、bzip2 −5.88%、perlbench −4.61%，低于 −2% 的点 6 个、低于 −5% 的点 2 个（这些点对时序敏感，个别点有几个百分点的随机波动，没有逐个分析）；估算分数 10.46 → 约 10.53 分/GHz（参考时间没有核对官方表，起点沿用上一行的近似值）。原始数据 `~/personal/AI-Huma-data/stwb/full/new/`，基线 `~/personal/AI-Huma-data/integ/integ/res`。**之前 12 个点的 +2.85% 偏高**：每个程序只取一个点，gcc 的 sp42 是个别极端点（store 占 77%），全量按所有点平均后收益主要来自 gcc。
- **RTL**：`lp_wbuf`（决策、请求、响应、插入）、`lp_wbstep`（插入的一步，4 级串联）、`lp_stq` 每项加"已处理"标记、`lp_drain` 只剩 MMIO 路径加缓冲区；DCache 的双字通路（`dcache_s1/arr/bank/mshr/wb/resp`，每个 store 口一个 `st2_t` 第二字）沿用，合并写成每字节一次并行选择（`line_merge_n`），不再是串联的 512 位合并。详见 `rtl/RTL_WBUF_NOTES.md`。
- **验证**：trace-model gate 63/63（基线重生成，17 个程序周期小幅变化）；RTL `lint.sh`、`lint_chip.sh` 0 警告；`fm_gate.sh` 68/68，周期与 trace-model（`LSU_PIPE_NOWD=1`）逐个相等（0 个不同）；Linux 13 段 13/13，每段检查 690 万到 2420 万条指令，0 不一致。
- **综合**（yosys 通用门，面积 / 深度，main → 本次）：`lsu` 1,276,574 / 130 → 1,279,658 / **125**；`lp_stq` 158,221 / 72 → 161,937 / 74；`lp_drain` 86,260 / 83 → 68,767 / 97（**模块级深度 +17%，超过 5% 判据**，但包含它的 `lsu` 整体比 main 浅，说明不在 `lsu` 的关键路径上）；`lp_wbuf` 59,014 / 89；DCache：`dcache_s1` 12,970 / 45 → 16,101 / 28，`dcache_mshr` 110,574 / 114 → 83,386 / 101，`dcache_resp` 14,188 / 34 → 17,418 / 22，`dcache_wb` 20,563 / 69 → 26,673 / 57。`dcache_arr` 两边都综合失败，没有数据。
- **别人怎么做**（查阅，未读到源码）：香山（昆明湖）有独立的 SBuffer：64B 整行条目加字节掩码，StoreQueue 每周期最多送 2 个，按占用阈值排空，load 同时查 StoreQueue、SBuffer、DCache（优先级 StoreQueue > SBuffer > DCache），StoreQueue 项在 store 进入 SBuffer 后释放。BOOM 没有 write buffer：提交后的 store 留在 STQ 里按序发给存储系统，文档没有写合并。本次合入的是"STQ 内分组"，介于两者之间；香山式独立缓冲区记在 TODO。
- **模型近似和未覆盖**：缓冲区条目是对 STQ 项的分组，没有字节掩码数据，load 的转发仍查 STQ；参数扫描只在 5 个点上做，对单点有 ±1~4% 的波动；SPEC 30 点精确预热没有跑（全量 580 点快速预热已在本机跑完，见上）；RTL 上没有跑 SPEC；PMU 的 RTL 事件没有对新缓冲区加事件。第一版 in-drain 配对 RTL 在 Linux `s04` 有 1 处 `sc.w` 判失败（SC 的成功在自己的写回拍按预约状态判定，时序变化可能暴露原有竞争），本版 13/13 通过，**原因没有定位**（TODO）。
- **复现**：`LSU_PIPE_WBUF=0 LSU_PIPE_DRAIN=3` 是合入前的配置；`scripts/pf/run_point.sh`（gcc sp42 需要 `tm/pf_stubs` 里的 stub，`pmu_spec` 里的 stub 起点不同、结果有差异）。

---

## EXP-023 前端快速通路：FE_RFAST / FE_BFAST / FE_PAIR / FE_IPF

- **日期**：2026-11-08 至 2026-11-09。**分支**：trace-model `exp/frontend`（`c8b92cf`，工作区 `trace-model-fe`，笔记 `FRONTEND_NOTES.md`，**未合入 main**）→ `exp/combo`（`2e1a27c`）→ `exp/fe-refs`（`b02eaf6`，工作区 `trace-model-ferefs`，基于 main `7f8456e` + `CFG_FE_*` 宏）；rtl `exp/fe-rtl`（`71468eb`，工作区 `rtl-fe`，笔记 `RTL_FE_NOTES.md`）。**`FE_RFAST` + `FE_BFAST` 的模型与 RTL 以及 `FE_PAIR`/`FE_IPF` 的模型代码随 `exp/integ` 合入 main（2026-11-09，见 MAIN_RECORDS）；RTL 只有 `FE_RFAST=15`（固定）和 `FE_BFAST`（默认关）。**
- **编号说明**：这些分支的提交说明里写的是"EXP-019"（`FE_RFAST`、`FE_BFAST`、`FE_PAIR`、`FE_DIAG`）或 "fe:"，与访存推测（EXP-019）撞号；EXP-021（LLC 预取模式 bandit）、EXP-022（ChampSim 预取器选择）已被别的分支占用，所以文档里前端记为 EXP-023。
- **问题**：重定向（分支预测错误）后第一条指令到达 dispatch 要 8 个周期；每周期最多取一个基本块。哪些拍可以省，RTL 能不能做到。
- **测量（模型，`FE_DIAG`/`FE_TRACE`）**：重定向到 dispatch 第一条有效指令 8 拍（全部是预测错误，无 I$ miss）：back2front 寄存器 1、BPU 重取指周期不发射 S0 1、S0 → 取指地址 FIFO → I$ 1（I$ 重取指后还会拉低 ready 一拍）、PTAB 在 S_D 写入下一拍才可读 1、pre-IDU 缓冲 1、重命名寄存器 1、dispatch 寄存器 1。取指极限研究（提交流、完美预测、无气泡，`FE_FUSE_DIAG`）：每个取指周期的指令数，一块一拍 4.7–5.0；越过目标在同一 64 B 行内的 taken 分支（占 taken 的 17–26%）5.0–5.4（+6%）；一拍两个基本块 6.5–6.8（+35%）。
- **开关**：`FE_RFAST`（4 位）：bit0 S0 在重取指周期发射；bit1 PTAB 写到读旁路；bit2 重定向后 I$ 立即 ready（单独无效，需要 bit0）；bit3 pre-IDU 缓冲旁路。`FE_BFAST`（2 位）：S1(L1) / S_D 覆盖后，修正的块在同一周期发射。`FE_PAIR`：跨 taken 分支同周期取两个块（同 4 KiB 页、第二块来自已驻留的行）；`FE_IPF`：BPU 驱动的 I$ 预取。默认全关时周期不变（gate 63/63）。
- **模型结果（25 点，精确预热，`PF_ENABLE=1 PMU=1`，几何平均 IPC，对 main `cefaee4`；`exp/frontend` 构建）**：

| 开关 | 几何平均 | 说明 |
|---|---|---|
| `FE_RFAST=15` | +2.3% | perlbench +3.1、gobmk +3.2、sjeng +5.4、astar +5.2，h264ref/hmmer/bzip2 约 +0.3~0.5 |
| `FE_BFAST=3` | +2.1% | gcc +4.9、gobmk +4.2、sjeng +4.5、xalancbmk +3.6 |
| 两者 | +4.3% | sjeng +10.1、astar +7.1、gobmk +6.3 |
| 在两者之上 `FE_IPF=1` | +1.75% | gobmk +8.3、xalancbmk +3.9 |
| 在两者之上 `FE_PAIR=1` | +2.88% | sjeng +12.4、xalancbmk +9.5，perlbench −1.0 |
| 在两者之上 `FE_PAIR=1 FE_IPF=1` | +5.22%（对 main +9.75%） | |

  - `FE_RFAST=15 FE_BFAST=0` 在 `exp/fe-refs`（基于 main `7f8456e`）上重测为 **+2.61%**（与上表 +2.3% 是不同的构建和基线，两个数字都留着）：perlbench +3.1、bzip2 +0.5、gcc +0.6、gobmk +3.2、hmmer +0.5、sjeng +5.4、h264ref +0.3、astar +5.2、xalancbmk +1.7。
  - `FE_PAIR` 一开始有个 bug：一拍两个块使 256 位历史环溢出，长历史 TAGE 索引被修复操作破坏（sjeng 的已提交条件分支预测错误 ×2.5），改成 512 位环。第一块以条件分支结尾时预测错误会增加，其他类型中性。
- **RTL 实现与逐位测量**（`FE_RFAST`/`FE_BFAST` 每一位都有 RTL；`lint.sh`/`lint_chip.sh` 全部设置 0 警告；67 个程序周期与同设置的模型逐个相等；深度用 `synth_depth.sh`，通用门级数，噪声约 ±10%）：

| RFAST | BFAST | `bpu` 深度 | `front_pred_path` 深度 | `bpu` 单元 | 模型 IPC（25 点） |
|---|---|---|---|---|---|
| 0 | 0 | 151 | 138 | 199,240 | 0 |
| 1 | 0 | 141 | 142 | 237,174（+19%） | +1.15% |
| 2 | 0 | 151 | 137 | 199,240 | +0.86% |
| 4 | 0 | 151 | 138 | 199,240 | 0.00%（需要 bit0） |
| 8 | 0 | 151 | 138 | 199,240 | +0.99% |
| 14 | 0 | 151 | 137 | 199,240 | +2.02% |
| **15** | 0 | 141 | 142（+3%） | 237,174（+19%） | **+2.61%** |
| 0 | 1 | 202（+34%） | 195（+41%） | 217,154 | +1.17% |
| 0 | 2 | 202 | 195 | 217,177 | +1.76% |
| 15 | 3 | 199（+32%） | 202（+46%） | 218,713 | +5.03% |

  - 第一版（`bpu` 从 `pc1`/`spec1_*` 取 S0 状态）的 RFAST bit0 深度 186（+26%），被 S2 选择 → 覆盖 → 修正 pc → uBTB 读与比较 → 历史推入的链撑起；改成 S0 用重取指专用的恢复命令副本（`spec_r1`/`sras_r1`，选择用 `refetch`）、历史一步线性多位推入后，`RFAST=15` 的 `bpu` 深度 141（比关闭的 151 还浅）。
  - 综合单元数也有一个没有对上的地方：这张表里 off 是 199,240，较早的一次测量是 222,883，合并后的综合表里 main 是 223,476；不同脚本和树，见 MAIN_RECORDS 的"文档之间互相矛盾"一条。
  - RTL 发现并修复的问题（RFAST bit2）：RTL 的 I$ AXI 接收脉冲比模型早一拍；bit2 在 kill 周期就给 ready，所以 kill 落在脉冲周期时仍要算"接收未完成"（`accepted_now`）。不修时 6/67 个程序差 1–4 周期（coremark −4、memory-stress-small +116、pf-stress +201，`DS3=0`）。用定延迟内存在两边都构建来定位；DRAMsim3 相位差是误导。
- **为什么 `FE_BFAST` 关**：+34% 深度换 +1.2%（bit0）/ +1.8%（bit1）/ 在 `RFAST=15` 之上约 +2.4%（两位）。链 S1/S2 比较 → 修正 pc → uBTB 组读 + 标签比较 → 历史推入无法在不改变事件时序的前提下缩短（uBTB 索引是迟到的比较结果）；没有频率目标，建议保持关；只有时钟周期被更深的路径（约 200 级以上）决定时才考虑只开 bit1。
- **`FE_PAIR` 的 RTL 代价（没做）**：不是开关而是改写 BPU 前端：S0 要第二次 uBTB 读（组索引是第一块猜测的目标，一拍里串联 uBTB → 目标 → uBTB）、第二套历史/RAS 步进和 TAGE 索引；256 位历史环变 512 位、12 个折叠历史每拍两次推入；主阵列每个 bank 需要第二读口或更多 bank；`bpu_main_sel` 与覆盖比较复制；PTAB 项约 +50%、每个 slot 带显式 pc；I$ 在同一拍功能性读第二块；预译码检查器按段处理；后端 FTQ 项两个段。估计 3–4 周含验证，前端面积（不含 I$ 阵列）+30% 以上，且 S0 双查在当前深度下放不进一个周期；现实的变体是第二块放到 S1 用寄存的首块猜测查，稳态每拍两块、重定向后一个气泡，会损失模型 +2.9% 的一部分。
- **`FE_IPF` 的模型局限**：预取不经过真实的 LLC/AXI/DRAM 路径：只对此前被需求 miss 填过的行预取（"行在 LLC 里"的替代），延迟固定 `FE_IPF_LAT=12`，最多 4 个在飞，不建模 LLC 和总线带宽，安装 = 在轮转牺牲路里写 tag+valid（污染有建模）。所以 +1.75% 是上界，RTL 的值要重新量。
- **验证**：见 RTL 笔记。模型 gate（开关关）63/63；`FE_RFAST=15 FE_BFAST=3` 下 63 个程序 difftest Success。RTL 最终配置（`RFAST=15 BFAST=0`）：本机测试平台 fm_gate 67/67、周期与模型相等；Linux 从复位启动到 `rv32 login:`（本机，逐条对比 0 个 `[FM]` 不一致）和 13 段检查点接力 13/13、0 不一致（服务器）。服务器上的 per-setting 扫描有 3 个 zfinx 程序因服务器旧 `librefcpu.a` 对函数模型检查失败（所有设置，含全关），是环境问题。
- **未覆盖 / 后续**：`FE_PAIR` 的 RTL 和 `FE_IPF` 走真实内存通路；`bpu` 的 +19% 面积（可以用 `spec_r1` 推导 `spec_r2` 换深度）；BFAST 深度；`pre_idu_queue` 的 bypass 真实路径跨模块，没有量；没有时钟频率目标。
- **复现**：模型 `FE_RFAST=15 FE_BFAST=3 LSU_PIPE_NOWD=1 bash scripts/tm_cycles.sh <simulator> out.txt`；RTL 在 `exp/fe-rtl` 上 `SOC_FM=1 tb/soc/build.sh`，`REF_CYCLES=out.txt scripts/fm_gate.sh`；SPEC 点 `scripts/pf/points_fe.lst`，比较脚本 `~/personal/AI-Huma-data/frontend/cmp.py`。

---

## EXP-020 访存推测的值路径（`LSU_MS_DATA`）

- **日期**：2026-11-08。**分支**：trace-model `exp/ms-data`（`97cca34`，从 `exp/memspec-refs` `40ed5bc` 分出，工作区 `trace-model-msdata`，笔记 `MS_DATA_NOTES.md`）。**随 `exp/integ` 合入 main（2026-11-09），默认开（`CFG_LSU_MS_DATA=1`，只在 `LSU_MEMSPEC=1` 时有效）。**
- **问题**：开 `LSU_MEMSPEC` 后 RTL 与模型在两个程序上周期不同（dhrystone 115,896 vs 115,830，vm_pagefault_test 19,271 vs 19,270）。模型按轨迹事实执行，没有数据值；RTL 执行真实数据：越过地址未知 store 的 load 读到旧值，消费者用旧值算，依赖它的分支可能解析错，产生 RTL 独有的预测错误。
- **诊断**：dhrystone 的差异全部来自同一条静态分支（pc `0x800003f8` 的 `bne a0,x0`，在读旧字节的 `lbu a0,55(sp)` 之后），模型里共 27 次翻转，平均每次 2.4 周期（累计 +66，翻转 1–2 周期损失在违例 load，另有 BPU/取指状态扰动）；把它们当作 RTL 独有的预测错误重定向后，逐提交周期序列整个运行（291,710 条提交）与 RTL 完全一致（之前 2,894 个差异事件）。vm_pagefault_test 一次翻转（pc `0x800003f4`）= +1。SPD/release/违例/二次写回事件原本就逐个相等，没有别的差异类别。
- **模型做了什么**：旧值 = 最老的未排空 STQ store 之前的字（缓存内容）或核心 RAM，再叠加该 load 最后一次 L1 CAM 时可见的更老 STQ store（按年龄，最年轻的赢，含字节通道和部分重叠）；污染表（物理寄存器 → 值、链深度）在第一次写回置位、第二次写回和每次 ROB 冲刷清除；消费者用 `MsData.h` 的 RV32IMAB 求值器按真实语义计算，结果恰好等于真值就解除污染；污染的分支重新算方向/目标，翻转与预测不一致时发出重定向；污染的 store 数据进 STQ；模式位 2 允许旧地址。模式位：1 分支 + store 数据、2 旧地址、4 旧 store 数据、8 自检（调试）。
- **验证**：默认（`LSU_MS_DATA=0`）对 `ref_cycles_memspec.txt` 68/68 逐个相同；`LSU_MS_DATA=1`/`7` 下 66 个不变，dhrystone 115,896、vm_pagefault_test 19,271 = RTL，`vm_asid_test` 41,097 = RTL。自检（每个非推测 load 和二次写回的值都应等于事实）在 perlbench sp3 的 340 万个 load 上 0 个不一致；RV32IMAB 求值器在 dhrystone 的 9.5 万条 ALU/分支 uop 上 0 个错误；每个旧值 load 的二次写回都带 `vio`（`stale_without_vio=0`）。第一版用 `src2_is_imm` 判断分支的第二个源，漏掉了 `beq`，被 `vm_asid_test`（41,096）抓出。
- **30 点（`PF_ENABLE=1 PMU=1 FASTWARM=1000000 LSU_MEMSPEC=1 LSU_MS_DATA=1`）**：对预言机 `MEMSPEC=1` 几何平均 −0.085%；对 `MEMSPEC=0` 的加速从 +5.30% 变成 +5.21%（预言机模型高估 0.09 个百分点）。每点 −0.93%（gobmk sp23）到 +0.35%（mcf sp16）；14/30 个点在 ±0.05% 以内。1,333 万次推测第一次写回里 12,234 次是旧值（0.09%），其余相等；消费者 35,397；污染的分支 6,807 个，1,190 个翻转（1,175 个增加预测错误，15 个去掉真预测错误）+ 42 个 jalr 目标翻转。
- **没建模 / 没验证**：旧地址的 load/store（实现了、没有程序能验证，模式 7 没在 30 点上跑）；CSR/FP/AMO 消费者（计为 `unmodelled`，没出现）；错误路径 load 的旧值用错误路径的功能模型状态算；源操作数读时机比寄存器读晚一级的细微差异（68 个程序里没出现）。
- **复现**：`LSU_MEMSPEC=1 LSU_MS_DATA=1`；`LSU_MS_DTRACE=1` 打印每次旧值/翻转，`LSU_PIPE_STATS=1` 打印 `[MS_DATA]` 统计。

---

## EXP-019 LSU 访存相关推测（模型探索 + RTL 实现）

- **日期**：2026-11-07 至 2026-11-09。**分支**：trace-model `exp/mem-spec`（`2196889`，最早版本，提交说明里写的是"EXP-018"）→ `exp/memspec-refs`（`ef02c4c`，工作区 `trace-model-msrefs3`）；rtl `exp/memspec-rtl`（`598f4f9`，`exp/memspec-rtl-on` `37182cd`，工作区 `rtl-memspec`，笔记 `RTL_MEMSPEC_NOTES.md`）。**随 `exp/integ` 合入 main（2026-11-09，默认开，见 MAIN_RECORDS）。**
- **编号说明**：模型分支最早的提交写"EXP-018"，该编号被 SMS 预取器占用（`exp/sms`），所以改为 EXP-019；值路径是 EXP-020；EXP-021、EXP-022 被别的分支占用，前端为 EXP-023。
- **问题**：load 必须等所有更老 store 的地址才能执行吗？让 load 越过地址未知的更老 store（推测），违例时重执行并冲刷，收益多大，硬件代价多大。
- **机制**（`LSU_MEMSPEC`）：地址未知的更老 store 被 CAM 跳过时，load 标记为推测（`spec`）；第一次写回延迟（`rob_defer`，ROB 不完成），load 进入 SPD 状态，等所有更老 store 的地址都已知才 release 并做第二次写回；STA 到达时 CAM 检查所有 LDQ 项，重叠的推测 load 置 `vio`，重做并在提交时冲刷（`flush_pipe`，pc+4 重取）。预测器：load 等待表（PC 哈希索引、1 位、每 2000 周期清零），违例的 load 训练；表里置位的 load 不推测。
- **预测器比较**（30 点 `points_p30_local.txt`，对 `MEMSPEC=0`，几何平均 IPC，预言机模型、没有值路径；由 `~/personal/AI-Huma-data/memspec` 的结果文件重新计算）：

| 变体 | 几何平均 | 备注 |
|---|---|---|
| 等待表 12 位、清零 2000（`final`，最终机制） | **+5.30%** | 没有推测限制 |
| 等待表 12 位、清零 5000 / 14 位、清零 1000 | +5.17% / +5.29% | 表大小几乎不影响 |
| 置信计数器（阈值/衰减/清零周期）2/0/20000、2/1/2000、2/1/5000、2/1/20000、3/1/20000、3/1/100000 | +4.86 / +5.13 / +5.08 / +4.76 / +5.19 / +4.80% | 没有一个超过粘滞 1 位 |
| store set（PC 对共用 set id；位数/清零）10/100000、12/不清零、12/20000、12/100000、12/1000000 | +3.90 / +2.80 / +4.65 / +3.87 / +3.37% | 都低于等待表 |
| 唤醒放在 release（`wrel`，笔记里没有这个变体的文字说明，按目录名理解） | **+1.30%** | 拒绝：+5.30% → +1.30% |
| `spec1`、`mdp10`（目录，笔记里没写配置） | +4.60% / +3.68% | 只记结果 |

  清零周期扫描（等待表 12 位，只有 8 个点，不能和上面直接比）：清零 1000/2000/5000/10000 周期为 +12.5 / +12.5 / +11.8 / +10.6%；不清零最差（14 位 +2.4%）；2000 周期附近平坦。**结论：粘滞 1 位等待表 + 2000 周期清零就够**，store set 和置信计数器都没有带来收益，所以只实现了等待表（`LSU_MDP_MODE=1` store set 与 `THR/DEC` 置信计数器留在模型里，默认关，RTL 没有）。
- **RTL 可实现性修改（模型）**：等待表训练按"所有违例的 load 标记，每拍最多训练两个最低 LDQ 索引，在时钟沿写入"建模（`LSU_MDP_HW=1`，67 个程序周期与理想训练一致）；`HW=2`：违例标志存寄存器，每拍训练一个标志项，表在违例后两拍写入（没有 STA 到达 → 表写入的组合路径，写口 2 → 1）；`LSU_MS_SLOTS=N` 限制同时推测的 load 数（16 个：+4.95%，8 个：+3.76%，太少）。`HW=2` 表大小 6 位（64 × 1）：30 点 +5.35%（12 位 +5.27%、8 位 +5.30%；表大小无所谓，清零周期决定一切）。
- **违例代价**（`[MS_PENALTY]`，`LSU_PIPE_STATS=1`）：走到冲刷提交的违例，检测 → 冲刷提交 17–41 周期，冲刷提交 → 下一次提交（重取指气泡）11–12 周期，合计 **28–52 周期**（之前估计的 20–30 偏低），其中真正没有提交的周期 **13–32**，被冲刷的更年轻指令约 82–98 条；只有约 55% 的违例走到冲刷提交（其余死在错误路径）。astar 8,194 次违例/4,439 次冲刷提交，perlbench 5,205/3,140，bzip2 6,560/3,292。dhrystone 27 / 11.6（笔记里只给了这两个数，含义同前两列）。bzip2 三个点 IPC 对 `MEMSPEC=0` 为 +126% / +99% / +0.3%。
- **RTL 实现**（对应表：`stq_cam(spec_ok)` → `lp_cam`（`spec_ok` 输入、`unk` 输出，按优先级前缀 OR）；LDQ 项新状态 `LS_SPD` 和标志 `spec vio second wait_b`（`lp_ent_ms`）；`lp_wb` 的 `wb_defer`/`wb_flushp` → ROB `rob_wb_t.defer/flush_pipe`；`lp_ms`（SPD release 扫描：从头第一个地址未知的 store，旋转 + find-first）；`lp_mdp`（等待表，惰性清零在清零到期后的第一个 load dispatch）；`dis2lsu.ldq_pc` 是 PC **哈希**不是 PC：FTQ 读基址加偏移（见下）→ 哈希进 `dis_inst_t` → LDQ 项）。第二次写回不再唤醒（RTL 的 PRF 侧唤醒幂等）。
- **面积与深度**（yosys 通用门，`synth_cfg.sh` 数单元，`synth_depth.sh` 数深度；main `edf9d3b` → 合并后；相对数字）：

| 模块 | main 单元 | 合并后 | 深度 main → 合并后 |
|---|---|---|---|
| `lsu`（`lp_core`） | 969,441 | 894,874（−7.7%，触发器 +779） | 131 → 128 |
| `lp_ldq`（64 项） | 330,074 | 386,345 | 78 → 78 |
| `lp_cam`（4 口） | 69,666 | 31,279 | 81 → 82 |
| `lp_l1b` | 248,896 | 110,854 | 82 → 83 |
| `lp_wb` | 124,377 | 126,730 | 63 → 57 |
| `lp_ms`（含等待表 2.7k）+ `lp_mdp` + `lp_ent_ms` × 64 | — | 4.3k + 44.6k | 45 / 43 / 34 |
| `rob` | 201,672 | 206,695（+128 触发器） | 47 → 46 |
| `dispatch` | 91,937 | 92,518（+48 触发器） | 46 → 45 |

  - 第一版（12 位表、2 个写口、`lp_cam` 用加法器）：`lsu` +158.9k（+16.4%），`lp_mdp` 69.5k 单元 / 4,096 触发器，`lp_ent_ms` 每项 1,183 单元；然后做了面积/深度削减（模型先做、RTL 跟着，每一步 68 个程序周期保持相等）：重叠判断 `lp_ovl` 一个对数深度比较器（对 6M 随机 + 边界向量验证等价），`lp_cam` 73.7k → 31.3k、`lp_ent_ms` 1,183 → 697 单元，**对关闭推测的设计也有利**；训练从标志寄存器、一个写口；表 64 × 1（69.5k → 2.7k 单元，4,096 → 64 触发器）；FTQ 给 dispatch 读 PC 用 64 选 1 块基 PC + 4 × 偏移代替 8 个 512 选 1 读口（+16.9k，估计的按用到位数算原做法约 100k）；`lp_cam` 的 `unk` 复用 find-first 前缀（96 → 82 级）。
  - 笔记没有把"推测本身的代价"和"重写 `lp_ovl` 的收益"拆开，不能把 `lsu` −7.7% 说成推测免费。
  - 最长链 STA 到达 → 违例检查 → 训练 → 表写入原先估计约 90 级，改成标志寄存器后该链在寄存器处断开。
- **验证**：见 MAIN_RECORDS 2026-11-09。过程中的检查：关推测的树 67/67 周期等于 `ref_cycles.txt`；开推测的树 fm_gate 68/68；Linux 13 段第一次 7 通过 6 失败（同一指令模式：用户态 `lbu` 返回旧字节），根因是违例检查漏了停在 `L_RPW` 的 load，局部 62k 周期复现（s06），修复后 13/13；定向测试 `directed/memspec_vio`（违例、部分/字节重叠、迟到的 store 地址，没有依赖 load 值的分支，否则 RTL 3914 vs 模型 3579）。
- **未覆盖 / 后续**：store set 与置信计数器的 RTL；`LSU_MS_SLOTS`（5.06% vs 5.35%，省约 3% 的 LSU 单元，拒绝）；LD/STA IQ 合并（`exp/ldsta-merge`）与本机制的交互；`spec/*.io` 没更新；FTQ 读口面积没有计入综合表；RTL 上的 SPEC；把哈希沿 ibuf/idu/ren 带下来（64 × 6 + 3 × 8 × 6 触发器加写口，比 +16.9k 还贵，不做）。
- **复现**：模型 `LSU_MEMSPEC=1`（默认）、`LSU_MS_TRACE=1`（与 RTL 调试打印同拍号），30 点集 `scripts/pf/points_p30_local.txt`，`PF_ENABLE=1 PMU=1 FASTWARM=1000000`；RTL `bash scripts/gen_cfg.sh -DCFG_LSU_MEMSPEC=0` 切回 kill switch，`scripts/linux_segments.sh <tb> <ckpt dir> <out>`。

---

## EXP-017 issue queue 入队宽度限制

- **日期**：2026-11-08。**分支**：trace-model `exp/iq-enq`（基于 main `1d08b15`，提交 `5851e1d`、`9da2f6e`、`e0d7375`、`cefaee4`）、rtl `exp/iq-enq`（基于 `cc90cc2`，`66f7096`、`121324c`）。**已合入 main（2026-11-08，快进）。** 提交说明里写的是"EXP-014"，是编号撞车写错了，正确编号是 EXP-017（EXP-016 被后端 DSE 占用）。
- **问题**：五个 IQ 的入队宽度都等于 DECODE_WIDTH=8，每个 IQ 8 个写口，不现实。
- **开关**：`CFG_{INT,LD,STA,STD,BR}_IQ_ENQ_WIDTH`（编译期，`config.h`），导出为 `IQ_*_ENQ_WIDTH` 给 RTL 配置包；原设计 = 全 8，周期不变。RTL：`isu.sv` 每个 IQ 只实例化这么多入队通道，`iss2dis_ready_num = min(空位, 通道数)`（模型也是两个条件都查）。
- **PMU 补充**（trace-model 专用，事件表末尾追加，id 不变）：`SLOT_BE_IQ_SPACE_*`（该 IQ 没空位）、`SLOT_BE_IQ_WIDTH_*`（有空位但本拍入队宽度用完）、`OCC_IQ_*`；十个停顿事件之和恒等于 `SLOT_BE_IQ_FULL`（每拍检查）。**LD 被 LD IQ 入队宽度挡住原来记成 `LDQ_FULL`，现在记在 IQ 里**（宽度 8 时不会发生，旧数字不变）。
- **结果**（周期；快速预热，预取开，对比 main `1d08b15` 的 `/root/lsubpu/res/full_new`；dhrystone / coremark）：

| INT/LD/STA/STD/BR | dhrystone | coremark | 全量 580 点几何平均 IPC |
|---|---|---|---|
| 8/8/8/8/8（main） | 123,684 | 295,351 | — |
| 6/4/3/3/3 | 123,608 | 295,601 | **−1.12%**（563 点；30 点精确预热 −1.55%；mcf −3.15%、omnetpp −4.30%） |
| **7/6/4/4/5** | 123,519 | 293,286 | **−0.05%**（580 点；30 点精确预热 −0.48%；mcf −0.33%、omnetpp −0.94%、hmmer +0.92%、sjeng +0.82%） |

  - 小程序看不出差别（6/4/3/3/3 在 dhrystone/coremark 上 ±0.1%），SPEC 的 mcf/omnetpp 才暴露。
  - 定位方法：用新计数器看 mcf/omnetpp 的 28 个点（mcf 每 5 取 1、omnetpp 每 3 取 1）。6/4/3/3/3 下的宽度停顿占槽位：omnetpp BR 1.54%、INT 0.50%、STA 0.42%、LD 0.20%；mcf LD 0.58%、BR 0.43%、STA 0.25%；IQ 本身基本没满，STD 队列（16 项）有一点。放宽后（同 28 点，对比 main）：6/4/3/3/3 mcf −2.66%/omnetpp −4.03%；6/5/4/3/4 −0.76%/−1.90%；7/6/4/3/5 −0.41%/−1.06%（剩下的是 STD 宽度 3）；**7/6/4/4/5 −0.28%/−0.85%**；6/5/4/4/4 −0.54%/−1.68%。
- **面积依据**：入队写口数 8×5=40 → 7+6+4+4+5=26（−35%）；RTL 只是少实例化通道，没做综合，**没有量面积**。
- **验证**：trace-model gate 63/63（基线按新默认重生成，20 个程序周期变化，全部 difftest 通过）；RTL `lint.sh`、`lint_chip.sh` 0 警告；fm_gate 67/67，周期与 trace-model（`LSU_PIPE_NOWD=1`）0 处不同。trace-model Linux 到 `rv32 login:`，mismatch 0RTL Linux（`SOC_FM=1 SOC_TB_FM=1`，逐条对比函数模型）也到 `rv32 login:`，不一致 0（登录后手动停止仿真，约 3.7 h 墙钟）。综合（`synth_cfg.sh`，Yosys 单元数代理）：`isu` 全 8 入队 1,039,339 → 7/6/4/4/5 入队 843,910，**−18.8%（−195k 单元）**。**没跑**：小 LLC 检查、顶层时序/WNS。
- **未覆盖**：全量只比了 7/6/4/4/5 的快速预热；omnetpp 仍 −0.94%，接近判据；INT 7、LD 6 比发射口数（INT 6 口、LD 4 口）还宽，是否还能降没有试；未测时序（写口少应有利）。
- **复现**：`CFG_*_IQ_ENQ_WIDTH` 用 `-D`（`EXTRA_CXXFLAGS`）；SPEC 用 `scripts/pf/run_eval.sh`，`PF_ENABLE=1 PMU=1 FASTWARM=1000000`，点列表 `points_full.txt`；服务器用法见 [SERVER.md](SERVER.md)。

---

## EXP-014 cache 替换策略与组织形式：离线回放 + 周期模型标定

- **日期**：2026-11-07。**分支**：trace-model `exp/repl-oracle`（工作区 `trace-model-repl`，基于 main `a7960e4`，**未提交**）。
- **问题**：L1D（64KB 4 路 tree-PLRU）、L1I（32KB 8 路，全局轮转指针，命中不更新）、LLC（4MB 16 路，"最近被碰的路的下一个"指针）、ITLB/DTLB（各 64 项全相联 FIFO）的替换策略和容量还有多少空间。
- **走过的弯路（没有用）**：先把 Belady 直接做进周期模型的 LLC（第一遍录序列、第二遍按序列选 victim），mcf sp0 上 oracle 那遍 44.3M 周期，基线 27.76M，慢 60%，且改成按组位置比较后周期逐位不变；原因是闭环下两遍运行的访问顺序会分叉（oracle 一改时序，LSU 就报 `REQ-GEN-MISMATCH`），我没有查到更细的根因，放弃。结论：**Belady 只能开环测**。
- **做法**（开环）：
  - 在 FastWarm（`diff/FastWarm.cpp`，EXP-011 的功能预热，按程序序、只有已提交路径、无预取、无错误路径）的 `LlcModel::access`、`dcache_warm_access`、`L1iModel::access`、`TlbModel::translate` 入口录访问序列（`include/LlcOracle.h`，环境变量 `LLC_ORACLE/L1D_ORACLE/L1I_ORACLE/ITLB_ORACLE/DTLB_ORACLE=rec:<文件>`，默认关、对周期零影响）。每点功能重放 1000 万条指令约 5 秒（`--fast-warmup -w 100000 -c 100000`），580 点 8 并行 3~6 分钟。
  - 离线回放程序 `scripts/repl/llc_replay.cpp`：指针（现 LLC）、tree-PLRU（现 L1D）、全局轮转（现 L1I）、FIFO（现 TLB）、LRU、SRRIP、BRRIP、DRRIP（set dueling）、Belady、Belady+旁路；任意容量/路数。构造序列验证（17 行循环 16 路：LRU/SRRIP 全缺失，BRRIP 12%，Belady 6.5%）。统计窗口取序列后半（前半预热），按 SimPoint 权重汇总，12 个程序取几何平均。
  - 周期模型标定：`scripts/pf/run_point.sh` 跑 `-c 10000000`（前门恢复、精确预热），变体用 `-DCFG_ICACHE_WAYS/CFG_DCACHE_SETS/CFG_DTLB_ENTRIES/CONFIG_AXI_LLC_SIZE_BYTES`。
- **更正：不存在"LLC 每个请求被查两次"。** 早先在周期模型里录到的 LLC 序列有 50% 是紧邻重复，我一度当成性能问题，**查清后是测量伪影**：`AXI_Interconnect` 每个周期调用两次 `llc.comb()`（`AXI_Interconnect.cpp` 1212 行和 1302 行），`llc.seq()` 一次；`accept_new_requests → start_lookup` 只写 `reg_write`（重复求值幂等），实际一次查找、一次响应。我把录制钩子放在组合逻辑里，所以每条被记了两遍（诊断：L1D MSHR 接受 76,382 次、互联捕获 76,382 次、LLC 钩子和"响应入队"计数各 152,764 次，恰为 2 倍；两次"接受"的 `lookup_valid` 都是 0）。含义：① 周期模型序列里 BRRIP 与 SRRIP 逐位相同是因为第二份副本把新行立刻提升；② **本记录里所有结果用的是 FastWarm 的功能序列（单次、不重复），不受影响**；③ 闭环 Belady 的钩子同样被数了两遍，使那次 oracle 结果更不可信（失败的根因仍未查清）；④ 以后在 trace-model 里挂计数/录制钩子要放在 `seq`，不要放在会重复求值的 `comb`。
- **结果 1：替换策略（缺失数相对现策略，580 点、12 程序几何平均）**

| 结构 | 现策略 | LRU | SRRIP | BRRIP | DRRIP | Belady（不可达） |
|---|---|---|---|---|---|---|
| LLC 4MB 16 路 | 指针 | −0.7% | −1.4% | −3.0% | **−3.9%** | −11.9%（8MB 时 −5.3%） |
| L1D 64KB 4 路 | tree-PLRU | −1.1% | −0.3% | +1.4% | −0.0% | −18.6% |
| L1I 32KB 8 路 | 全局轮转 | −3.3% | **−17.4%** | −12.4% | −16.2% | −45.7% |

  - LLC：只有 bzip2（任何近 LRU 策略 −10%）、gcc（只有 BRRIP/DRRIP −23%，抗抖动）、mcf（DRRIP −6.9%，Belady −33%）、astar（Belady −38%、实用策略 ≈0，LRU 反而 +6.7%）有变化，7 个程序 LLC 根本没满或纯流式。
  - L1D：所有实用策略在 ±1.5% 内；DRRIP 与 PLRU 持平。
  - L1I：SRRIP 在各程序上稳定受益（gobmk −37%、sjeng −42%、gcc −23.5%、xalancbmk −22%、omnetpp −26%、perlbench −17%）。LRU 在 xalancbmk、omnetpp 上比轮转还差 13~14%。
- **结果 2：容量/路数（缺失数相对现组织形式，几何平均，策略不变）**
  - L1D（PLRU）：32KB 4 路 +39%；128KB 4 路 −20%；256KB 4 路 −32%；64KB 8 路 −3%；2 路 +19%；直接映射 +100%。
  - L1I（轮转）：16KB +235%（8 路）；64KB 8 路 −79%；64KB 16 路 −81%；32KB 16 路 −25%；4 路 +42%。SRRIP 下 32KB 16 路 −43%。
  - LLC（指针）：2MB +22%；8MB −15%；16MB −20%；路数 8/16/32 差别 <1.5%。
  - DTLB（FIFO）：**LRU 换 FIFO（64 项全相联）−23.6%**；128 项 −39%（LRU −50%）；256 项 −58%；512 项 4 路 −73%；1024 项 −85%。ITLB：128 项 −59%，但绝大多数程序基数很小。
- **结果 3：周期模型标定（单点有 ±3% 噪声，只看量级）**
  - L1I 32KB→64KB（16 路，缺失 −80%），14 个 L1I 压力最大的点：**几何平均 IPC +9.5%**（perlbench +10~16%、xalancbmk +10~25%、gobmk +9~11%）。用这 14 点标定"每减少 1000 个 L1I 缺失涨 0.196% IPC"（R²≈0.62），套到全部 580 点：**SRRIP 全集几何平均 +0.30%**（gobmk +1.8%、xalancbmk +0.6%、perlbench +0.5%、gcc +0.4%），64KB L1I 全集约 +0.95%。
  - DTLB 64→128→512 项，14 个 DTLB 压力最大的点：+0.7% / +2.2%（mcf 离线 DTLB 缺失率 32%，每千条指令约 142 次，IPC 只 +0.1% / +1.4%）；**离线缺失减少不能直接当 IPC**。
  - 统一对照（每个程序最高权重 1 个点，12 点几何平均，相对基线）：L1D 128KB **+1.3%**（mcf +8.9%、bzip2 +6.1%）、L1I 64KB **+1.3%**（gobmk +15%）、LLC 8MB **+1.1%**（omnetpp +13%、mcf +2.8%）、DTLB 512 项 **+0.2%**。有反直觉的负值（perlbench L1I 64KB −3.4%、gcc DTLB 512 −2.8%、libquantum LLC 8MB −2.0%），属于单点噪声（h1 预取与时序交互），不是结论。
- **结论**：
  1. **替换策略的空间很小**：LLC DRRIP 估约 +0.3~0.5%、L1I SRRIP +0.3%、L1D 无；与 EXP-012 mov 消除（+0.06%）同量级。可以做的（成本极低）：L1I SRRIP（1 Kb）、LLC DRRIP（16 KB 状态）、TLB FIFO→PLRU/NRU（几位）。
  2. **容量收益也不大**：各结构翻倍各 +1.1~1.3%（单点估计），面积成本远高于替换策略；L1D 128KB 对 mcf、bzip2 有 +6~9%，L1I 64KB 对 gobmk 有 +15%。
  3. 现有的 EXP-009 预取器已经把最大的内存瓶颈吃掉，剩下的 cache 空间都是小头。
- **局限**：功能序列没有预取（h1 默认开，预取污染/提前量未计入）、没有错误路径；每点只 ~900 万条指令（后半 450 万）；IPC 换算靠 14 点的线性标定；统一对照每程序一个点；TLB 的序列只有虚拟页号，没有区分超级页；没有测 L2（私有二级）、LLC 命中延迟敏感度、预取行低优先级插入。
- **复现**：`scripts/repl/fw_seq.sh`（LLC）、`fw_seq_l1.sh`（L1D/L1I）、`fw_seq_tlb.sh`（TLB）录序列，`llc_agg.py` 汇总策略，`org_sweep.py L1D|L1I|LLC|DTLB|ITLB` 扫组织形式，`l1i_est.py` 标定；序列在 `~/personal/AI-Huma-data/repl_fw`（LLC，1.3GB）、`repl_l1`（L1D/L1I，21GB）、`repl_tlb`，周期模型标定结果在 `repl_cl`。
- **后续**：① L1I SRRIP 在 trace-model 实现，quick SPEC 验证（预期 +0.3%）；② LLC 命中延迟敏感度（`CONFIG_AXI_LLC_LOOKUP_LATENCY`）与私有 L2 的价值；③ 预取行低优先级插入（需要闭环）；④ 若关心 TLB，先量页表遍历代价为何被隐藏。

## EXP-013 PMU：硬件计数器 + trace-model 分析层

- **日期**：2026-11-07。**分支**：trace-model `exp/pmu`（工作区 `trace-model-pmu`，基于 main `ac16e92`，已快进合入：`ee988d0`、`a7960e4`）、rtl `exp/pmu`（工作区 `rtl-pmu`，基于 main `9279125`，已快进合入：`b5a299a`、`5829f07`）。设计和用法见 [PMU.md](PMU.md)。
- **问题**：探索靠队列占用、阻塞原因、TMA，旧的统计套件（2026-11-02 随清理删除）口径松散、不能进 RTL；要一套两边都有的计数器框架，再加只有模型能做的更细分析。
- **做法**：
  - 事件表 `trace-model/include/pmu_events.def`（52 个事件，每个 = 一个信号每拍加几）；trace-model 每拍在 `BackTop::comb()` 末尾填事件向量并累加（`back-end/PmuSample.cpp`），dispatch 的 8 个槽逐槽归桶（`Dispatch::pmu_slots`），恒等式 `slots = FIRE + KILLED + FE_EMPTY + BE_*` 每拍检查。
  - 分析层：逐 PC 堵塞画像（把丢掉的 dispatch 槽记给最老未完成指令）、提交数/ROB/LDQ/STQ/未完成缺失数直方图、`PMU_INTERVAL` 相位曲线；`scripts/pmu/pmu_report.py` 汇总。
  - RTL：`rtl/pmu/pmu.sv`（mcycle、minstret、8 个可编程 HPM、mcountinhibit、mcounteren、user 影子，事件由 `mhpmevent = 事件号+1` 选择）；`pmu_ev_pkg.sv` 由 `scripts/gen_pmu_pkg.py` 从事件表生成。
- **开关**：环境变量 `PMU=1`（默认关）、`PMU_OUT`、`PMU_INTERVAL`、`PMU_PCPROF=0`。
- **验证**：① 周期：dhrystone 161,183、coremark 251,535、mcf 检查点 sp0（10M+10M）27,764,655，`PMU=1` 与 main 的 `build/simulator` 逐个相同；② 槽恒等式违反 0 次（三个负载）；`INSTRET` 等于提交数（检查点模式停在拍中间，最多多计 7 条）；③ **RTL tier 1 逐事件对齐**：`rtl/scripts/pmu_parity.sh`，dhrystone、coremark 各 18 个事件（含 TMA 一级的槽事件）RTL 与 trace-model 总数全部相等（周期 161,183 / 251,535）；④ RTL 计数器块：`tests/pmu/run.sh` 30 万拍随机对 C++ 模型 0 不一致，故意改坏模型能被抓到；lint 干净。
- **结果（样例，只看分析层能给什么）**：
  - mcf sp0：IPC 0.36；Retiring 4.5% / Bad Spec 10.5% / Frontend 3.8% / **Backend 81.2%**；按 ROB 头看 Memory 74.9%（L1D 缺失 53.1%），按资源看 ROB 满 80.6%；L1D load 缺失 162 MPKI（48%），MLP 4.4，83.5% 的周期有缺失在途；**两条 load（0x123ac、0x10938）占全部堵塞槽的 61%**，访存指令占 94%；分支 15.7 MPKI，0x12388 一条分支占误预测 55%。预取 744,735 次、有用 13 次（计数口径见 PMU.md 第 6 节，需要核实）。
  - dhrystone 64 次：Retiring 22.6% / Bad Spec 27.3% / Frontend 32.0% / Backend 18.1%；**两条 `ret`（xputc/打印路径里）预测错误率 99.9%**，占全部误预测的 46%、Bad Spec 的大头——像是 `jalr a1` 这类间接调用没有压 RAS，**没有确认**。
  - coremark：Retiring 26.8% / Bad Spec 20.4% / Frontend 23.5% / Backend 29.3%（ROB 满 29%）。
- **顺带发现（不是本实验引入，未处理）**：
  1. `RealLsu::load_miss_mask` 用 `uint64_t` 与 `1ULL << rob_idx`，ROB 有 128 项：rob_idx ≥ 64 的缺失标记丢失、移位越界；只喂旧 TMA 元数据，不影响周期。本分支已改成 `bitset<ROB_NUM>`。
  2. 前门恢复的 SPEC 点：`cycle_base`（恢复程序用的周期，mcf 点 10,668）在预热结束的 `perf_reset()` 之后没有清零，报告的 `sim-time(cycle)` 比测量窗口实际周期少 `cycle_base`（mcf 点 27,764,655 对 27,775,324，−0.04%）。基线都带同样的偏差所以比值基本不变，但绝对 IPC 偏高；修它会改所有 SPEC 基线周期，需要你定。
- **未覆盖**：RTL 只接了 tier 1（18 个事件，PMU.md 第 4 节），其余事件（二级拆分、前端、访存、占用）只在 trace-model；CSR 软件可见（要改 function-model/OpenSBI 看到的 ISA 约定）没做；计数器块没综合；没有 L2/LLC/DRAM 级事件；没跑 gate（工作区没建测试程序）、没跑 SPEC 全量。
- **合入前复验（在提交后的代码上）**：trace-model gate 63/63（PMU 关、`PMU=1` 各一遍，都与基线逐个相同）；RTL `fm_gate.sh` 67/67、周期与 `ref_cycles.txt` 全部相同（预取开），关预取（`PF_EN=0`）67/67、与 `ref_cycles_nopf.txt` 全部相同，0 个函数模型不一致；`lint.sh`、`lint_chip.sh` 0 警告；Linux 13 段（s01–s13，每段 1600 万周期）逐条对比 13/13 通过、0 不一致，s01–s04 在本机、s05–s13 在服务器（4 线程 Verilator），s05/s08/s13 检查指令数 18,017,937 / 21,387,965 / 6,331,761，与合并预取后的树相同；综合代理（yosys 通用门）`dispatch` 86,637 不变，`pmu_ev_core` 518 单元，`pmu`（8 个 HPM）约 10.2k 单元（计数器存储按 `$mem`，不计触发器）。
- **结论**：已合入。trace-model 侧可以用了（`PMU=1`，默认关）；RTL 带 tier 1 事件总线（永远在，组合逻辑）和还没接 CSR 的计数器块；周期不受影响。后续见 TODO（软件可见、更多事件、综合）。
- **复现**：`gmake LDFLAGS="-lz"`；`PMU=1 PMU_OUT=out/x build/simulator prog.bin`；`python3 scripts/pmu/pmu_report.py out/x`；rtl `bash tests/pmu/run.sh`、`python3 scripts/gen_pmu_pkg.py <pmu_events.def>`。

---

## EXP-012 mov 消除（move elimination）

- **日期**：2026-11-06（最早的探索 2026-11-03：trace-model `exp/move-elim`，3 个提交，未合入；2026-11-06 重放到新 main 并做到 RTL）
- **分支**：trace-model `exp/move-elim-v2`（`767c25f`，基于 main `88e5254`）、rtl `exp/move-elim`（`1e5d656`，基于 main `b19a181`）；已快进合入 main。
- **问题**：`addi rd, rs, 0`（rd、rs 都是真寄存器）占提交指令的 3%（dhrystone 64 次）到 9%（coremark），能否在重命名时去掉，省下一个物理寄存器、一个发射槽和一次写回？
- **做法**：
  - Ren：这类指令不取空闲寄存器，rd 直接指向 rs 的物理寄存器（`dest_preg = src1_preg`）；不产生 uop，ROB 条目在 dispatch 时就完成，Dispatch 不置 busy 位、不参与组内 RAW 判断。
  - 寄存器的释放：**提交时**统计架构 RAT 里有多少项指向它（`arch_cnt`），旧寄存器的计数降到 0 才放回空闲表。重命名端不改计数，所以分支误预测和冲刷**不需要回滚计数**；`free_head_commit` 跳过被消除的 mov，空闲表头指针的检查点仍然有效。
  - 计数器上限：某条 mov 提交后的架构状态等于它重命名后的推测 RAT，所以架构计数不会超过重命名时推测 RAT 中指向该寄存器的项数。规则（`Ren::elim_refs_ok`）：源寄存器直接来自推测 RAT（本组内没有更老的指令写同一个源架构寄存器），且（推测 RAT 中指向它的项数）+（本组更老的有目的寄存器的指令数）+ 1 ≤ `CFG_MOVE_ELIM_REFS`（默认 7）。这样计数器只要 3 位，不用维护第二份推测计数，同组内的 mov 链也没有组合依赖。
  - RTL：新增 `ren_elim_sel`（判定）、`ren_arch_cnt`（计数与释放）、`ren_rank`；`me_elim` 一位从 Ren 经 Dispatch、ROB 回到 Ren；`MOVE_ELIM = 0` 时不生成任何新逻辑。
- **开关**：trace-model `CFG_MOVE_ELIM`（默认 1，原 `ME_ELIM` 环境变量）、`CFG_MOVE_ELIM_REFS`（7）；RTL 参数 `MOVE_ELIM`、`MOVE_ELIM_MAX_REFS` 由 `make cfg` 从 config.h 取。运行时 `ME_CHECK=1` 每周期检查：计数等于架构 RAT 指向该寄存器的项数、无物理寄存器泄漏，并打印最大引用数。
- **关闭开关时**：trace-model gate 62/62 与原基线逐个相同，dhrystone 162,033、coremark 255,335 不变；RTL（`MOVE_ELIM=0`）`fm_gate` 66/66，周期与原 `ref_cycles.txt` 逐个相等。
- **结果**（周期，1 GHz + DRAMsim3 基线）：

| 负载 | 关闭 | 开启 | 变化 | 被消除的 mov |
|---|---|---|---|---|
| dhrystone（64 次） | 162,033 | 162,033 | 0 | 129 |
| coremark（2 次迭代） | 255,335 | 252,400 | −1.15% | 34,737 |
| memory-stress | 2,428,470 | 2,425,220 | −0.13% | |
| gate 62 个程序 | | | 7 个程序周期变化 | |

  quick SPEC（6 个程序、129 个点，`replay.sh quick`，每点 1000 万条指令，无 difftest 不一致）：perlbench 2.100 → 2.090、gcc 1.523 → 1.525、mcf 0.420 → 0.420、hmmer 3.770 → 3.771、sjeng 1.830 → 1.831、h264ref 1.497 → 1.507；**几何平均 1.550 → 1.551（+0.06%）**。引用数最大 4（coremark），上限 7 有余量。
  没有引用上限的第一版（旧基线，2026-11-03）：dhrystone −0.77%、coremark10 −1.15%、quick SPEC +0.46%；加上限后 coremark 少消除约 25% 的 mov（组内旁路的源不再消除），周期反而略好（噪声内）。
- **面积**（yosys 通用门面积代理，`scripts/synth_cfg.sh`，原配置 vs 开启）：`ren` 206,228 → 227,720 单元（+21.5k，+10.4%）；`dispatch` 86,637、`rob` 201,672 不变（`me_elim` 一位的存储没有计入）。上面的数字里 `arch_cnt` 被综合脚本（`SYNTH_MEM=1`）当存储，触发器没有计入；把计数器映射成触发器重跑 `ren`（`memory_map`，同一套 abc 脚本）：**206,228 → 231,029 单元（+24.8k，+12.0%），触发器 10,315 → 10,699（+384）**；整机占比不到 0.5%。
- **关键路径（局部 yosys `ltp`，通用门级数，不是时序）**：`ren` 最长组合路径 **63 → 130 级**。开启后最长路径是 流水寄存器 → `ren_elim_sel`（33 项 RAT 比较求和）→ `ren_alloc_sel`（8 级串行选择）→ 目的寄存器选择 → RAT 快照 → 分支检查点；原来消除判定不在分配之前。重命名级的频率风险是实在的，需要有工艺库的综合确认；缓解办法：先分配后判定（被消除的指令不用寄存器，但分配编号对它们无害，只需把「占用」与「判定」解耦）、或放宽上限判定为流水一级。
- **验证**：trace-model gate 62/62、`ME_CHECK=1` 零断言；RTL 开启时 `fm_gate` 66/66、周期与 trace-model 逐个相等；trace-model 与 RTL（逐条对比）Linux 从复位启动到 `rv32 login:`；lint.sh/lint_chip.sh 0 警告（开、关两种配置）。
- **与开源设计的对比（只查到一部分）**：香山 `Rename.scala` / `BaseFreeList.scala`：被消除的 mov 不分配寄存器（`allocateReq := needIntDest && !isMove`），架构头指针 `archHeadPtr` 同样跳过 mov，空闲表头指针靠快照或从架构头指针回走恢复——与本实现的 `free_head_commit` 思路一致；引用计数本身（计数宽度、上限、推测/架构是否分开）在读到的源码里没有找到（`MEFreeList.scala` 里只有一条提到 refCounter 的过期注释），**没有确认**。文献上"重命名时计数"的做法能精确判断上限，但计数是推测的，冲刷时要回滚（快照或回走 ROB）；本实现只数架构表项，免回滚，代价是上限判断保守、提交端每拍要做 8 个提交槽的计数算术（面积的主要来源）。
- **模型近似/未覆盖**：① 同一拍里提交带目的寄存器的指令与分支误预测同拍，ME 模式下会 `Assert`（原空闲表检查本来就当作不可达；门禁、大程序、Linux、SPEC 均未触发）；② `add rd, rs, x0` 不处理（工具链不生成压缩 `c.mv`）；③ 面积没有计入计数器触发器；④ Linux 启动（RTL，逐条对比）已到 `rv32 login:`，0 不一致，没有总周期数；⑤ 没有做真实时序，只有上面的门级数（`ren` 63 → 130 级）；提交端 8 路计数算术没有单独评估。
- **结论**：功能正确、关闭时零影响，但收益在噪声量级（quick SPEC +0.06%，coremark −1.15% 周期），面积 `ren` +10%。按负责人决定默认开启并合入；如果以后面积成为约束，把 `CFG_MOVE_ELIM` 设为 0 即可去掉。
- **后续**：若要提高收益，可放宽"源来自同组旁路不消除"的限制；3 位计数器的面积收益和 `ren` 的关键路径需要有工艺库的综合才能评估。
- **复现**：trace-model `gmake LDFLAGS="-lz"`（默认开）、`ME_CHECK=1 build/simulator rtl/programs/big/coremark.bin`；关闭 `gmake EXTRA_CXXFLAGS="-DCFG_MOVE_ELIM=0" BUILD_DIR=build_off`；quick SPEC `scripts/spec/replay.sh quick`；RTL `make cfg`（取 trace-model 默认）、`scripts/fm_gate.sh`、`scripts/tm_cycles.sh <simulator>`（重新生成 `ref_cycles.txt`）。

---

## EXP-010 BPU 预测延迟：现有模型每个 taken 分支 0 气泡，换成真实延迟后 IPC 掉多少

- **日期**：2026-11-06
- **分支**：trace-model `exp/realistic-timing`（工作区 `trace-model-timing`，基于 main `88e5254`，改动未提交）。
- **问题**：`BPU::comb` 在一拍里完成 type 表 → 8 bank TAGE → BTB → RAS → next_pc（`rtl/docs/modules/bpu.md` 第 3 节），阵列是异步读的寄存器堆，约 10^6 位，NLP/2-ahead 和 SRAM 延迟模型已作为死代码删除（`16a0774`、`e99145a`）。也就是说模型里每个 taken 分支 0 气泡。1 GHz 下做不到；真实设计是"1 周期小表 + 多周期主预测器 override"。这对 IPC 估计偏乐观多少？
- **开关**（默认 0，关闭时 gate 与基线逐个相同：dhrystone 162,033 周期不变）：
  - `BPU_BUBBLE=B`：预测 taken 的取指组之后，BPU 空转 B 个周期（`bpu_instance.bubble()` 让前端的 `bpu_can_run` 为假）；
  - `BPU_UBTB=N`：N 项直接映射、12 位 tag 的 1 周期目标表（索引取取指组基址）；命中且目标与主预测器一致则免气泡；陈旧命中（主预测器说不跳）也吃气泡并失效。
- **微基准**（`tests/ubench/`，`scripts/ubench.sh`，两个迭代数相减）：L1D 命中 load-to-use **4.0 周期**；store→load 转发链 5.0（转发也是 4 周期）；2 条指令的循环、16 个连续跳转、call/ret 都是 **1 周期/taken 分支**（0 气泡）；同目标 `jr` 3 周期/2 个 taken（间接跳转多 1 气泡，基线就有）；50% 随机分支约 **11.6 周期/次误预测**。所以 load-to-use 和误预测恢复延迟本身是合理的，问题只在预测延迟。
- **负载**：8 个程序（perlbench gcc mcf hmmer sjeng gobmk astar h264ref），SimPoint 覆盖 25% 权重，共 30 个点，每点 1000 万预热 + 1000 万测量；基线为现有 `tm/res_dram60`（同一份代码，周期逐点相同）。`scripts/spec/timing_eval.sh`、`timing_eval_all.sh`，结果在 `tm/tim_{b1,b1u64,b2}`。

| 配置（IPC 相对 0 气泡基线） | 几何平均 | perlbench | gcc | sjeng | gobmk | hmmer | astar | mcf | h264ref |
|---|---|---|---|---|---|---|---|---|---|
| 每个 taken +1 气泡，无 uBTB（2 周期预测器） | **−6.8%** | −19.1% | −21.7% | −8.3% | −4.6% | −5.0% | −2.6% | −1.6% | −0.4% |
| +1 气泡，加 64 项 uBTB | **−2.2%** | −5.2% | −6.7% | −4.2% | −2.9% | −0.1% | −0.9% | −0.5% | 0.0% |
| 每个 taken +2 气泡，无 uBTB（3 周期预测器） | **−13.5%** | −33.1% | −34.5% | −17.6% | −10.7% | −12.4% | −6.8% | −3.2% | −1.9% |

- **结论**：现有所有 IPC 数字相对"可实现的预测器"偏乐观；2 周期预测器约 −7%，3 周期约 −13%，perlbench/gcc（代码足迹大、taken 分支多）最敏感，超过 −19%。一个 64 项的 1 周期 uBTB 能拿回约三分之二（−6.8% → −2.2%），但 perlbench、gcc 仍有 −5%~−7%，说明 uBTB 容量值得单独扫（128/256/512）。预测器需要 uBTB 或同类的快速路径，这是便宜且收益确定的方向。
- **模型近似**：① uBTB 用主预测器的输出训练，真实硬件用解析结果训练，命中率偏乐观；② 主预测器的"B 个气泡"是整体常数，没有区分条件分支/间接/返回，也没有 TAGE 在 override 时与 uBTB 方向不一致的重定向惩罚；③ 间接跳转额外那 1 个气泡没有建模；④ 每个程序只有 2~8 个点（perlbench 只有 2 个，范围 −7.8%~−29%），程序级数字噪声大，几何平均较稳。
- **没做**：uBTB 容量/相联度扫描；NLP/2-ahead；LSU 的同拍组合链（`rtl/docs/modules/lsu.md` 第 1.1 节，是时序问题，不影响模型周期）；TAGE 容量与历史长度（4 个表，历史 {8,13,32,119}）。
- **复现**：`gmake LDFLAGS="-lz" BUILD_DIR=build_base DS3_DIR=… DS3_LIB=…`；`BPU_BUBBLE=1 BPU_UBTB=64 bash scripts/spec/timing_eval.sh <tag> BPU_BUBBLE=1 BPU_UBTB=64`；微基准 `bash scripts/ubench.sh $PWD/build_base/simulator`。

---

## EXP-009 L1D 数据预取器与指令侧预取

- **日期**：2026-11-06
- **分支**：trace-model `exp/prefetch`（研究快照 `27a878f`）→ `exp/prefetch-h1`（冻结版，默认开）；rtl `exp/l1d-prefetch`（RTL 实现，`PF_EN`）。`scripts/pf/` 里有评测脚本、`scripts/pf/cloud/` 里有云上批量运行脚本。
- **问题**：在 DRAMsim3、不分频的新基线上，加一个"能在电路上实现、状态能数清楚"的预取器能带来多少性能？分别放在 L1D 数据侧和 I-cache 侧。次要目标：总结用 agent 迭代做架构探索的经验，以及 trace-model 自身的提速方向。

### 1. 先回答"流量建模够不够真实"（预取实验的前提）
- **已经真实**：DRAMsim3 有 bank/行缓冲/刷新/读写切换，实测 mcf 平均读延迟 113 ns（最大 577 ns）、libquantum 85 ns；L1D 的 tag/PLRU 是真的，所以污染看得出来；预取行挤掉的脏行会走写缓冲变成 DRAM 写；模型跟着错误路径访存，错误路径上的预取也会污染。
- **不够真实**：① 单核带宽用不满（mcf 约 1.5 GB/s、libquantum 约 2 GB/s，DDR4-3200 峰值 25.6 GB/s，`rd_stall` 为 0），无用预取"占带宽"测不出来，只能通过延迟体现（按用户要求不做流量注入器）；② 原来预取和普通读完全同级（L1D MSHR 按下标发、互联对 master 轮转），没有优先级；③ L1D 看不到访存指令的 PC；④ 预取跨页要走 DTLB 和页表遍历，没建模，所以预取限定在 4 KiB 页内；⑤ LLC 自带的预取默认关，只在 LLC 完全空闲时发、同时只允许 1 个在飞；⑥ DRAM 是单通道 8 个 bank、60 ns 附加延迟是常数；⑦ 预热长度由检查点间隔固定为 1000 万条，不能缩短（`--restore-stub` 强制要求）。

### 2. 实现（均为 trace-model 的电路风格，可在 RTL 里对应）
- **预取器框架**（`MemSubSystem/include/Prefetch.h`、`DataPrefetcher.h`）：状态只能由带位宽声明的 `PF_ENTRY` 表项、`pf::Table`、`pf::Fifo` 组成；写入时按声明位宽截断；每个表有固定的读/写/CAM 口数，**一周期内超过就直接中止**（这条规则抓出过两个真实的端口冲突）；状态总量自动统计并受 4 KB 预算约束；comb 只读状态、seq 才更新。
- **L1D 侧接入**（`RealDcache.cpp`、`MSHR.cpp`）：
  - 训练事件在 stage2 产生（load 未命中、首次命中预取行），**先打一拍寄存**再用，预取逻辑不在 L1D 命中判断的关键路径上；
  - 预取请求进独立的 8 项 FIFO；**tag 探测借用空闲的 load 口**，和普通访问一样要抢 bank，优先级最低；
  - 探测命中就丢弃，未命中才占 MSHR；MSHR 向 AXI 发请求时**普通读优先**；普通读撞上在飞的预取项时，该项升级为普通填充；
  - L1D 每行加 1 位"预取未用"标记（首次使用时清零并产生训练事件，被换出时产生"无用预取"事件）；
  - **预取目标可选 L1D 或 LLC-only**：LLC-only 的 MSHR 项响应回来直接释放、不进 L1D，释放时给 LSU 发一个"MSHR 空出"事件。
- **算法**（运行期参数 `PF_*`）：`ALGO=1` next-line；`2` 步长（64 项直接映射表，每项 41 位；按 PC 哈希索引，但见上面的 bug，实测过的版本等价于全局步长，`PF_NOPC=1` 可显式选择）；`3` Best-Offset（256 项 RR 表 + 26 个候选偏移的得分）；`4` 步长 + BO；`7` 仅 LLC next-line 引擎。另有与主算法正交的 **LLC 次级 next-line 引擎**（`PF_NLLC`，每次 L1D load 未命中顺带把后 N 行带进 LLC）、**准确度限流**（统计"首次使用"与"未用被换出"两类事件，每 256 个事件调整度数等级）、预取距离 `PF_DIST`、度数 `PF_DEGREE`、MSHR 保留项 `PF_RESERVE`。
- **LSU→L1D 的 PC 哈希**（10 位）：给 `LoadReq`、LDQ 项、L1D 流水寄存器各加一个字段，仅步长预取器使用。**注意（2026-11-06 发现的 bug）**：LSU 里取 PC 用的是 `inst->pc`，这个字段对 load 没有被填，恒为 0，真正的 PC 在 `inst->dbg.pc`。所以下文所有"IP-stride"结果（标 `cl_*`/`a2`/`f3`/`g*`/`h*` 的配置）**实际是"全局步长检测器"**：64 项表只用了第 0 项，所有 load 的 miss 流混在一起判断步长。修复后（`pc_*` 配置，真实 PC）的结果见第 4 节，**没有更好**。
- **指令侧**（`front-end/icache/include/IPrefetch.h`）：I-cache 数组只存 tag/valid，指令数据来自功能内存，所以预取 = 一次独立 AXI id 的读 + 响应回来写 tag/valid。两种候选：`IMODE=0` 对每次需求 miss 顺带预取后续行；`IMODE=1` FDIP，一周期扫一个取指地址 FIFO 里的未来地址，用从需求翻译里学到的小 µTLB 转成物理地址。最多 4 个预取同时在飞（AXI id 12~15），需求 miss 优先。

**模型近似（要记住）**：① 探测"目标行是否已在 L1D"在模型里读 tag 阵列；硬件上是借用空闲 load 口的那一次 tag 读，已按这个写，不再多出端口；② PC 哈希在模型里直接取自 uop 的 `pc`，硬件上要么在 IQ/LDQ 项里多带 10 位、要么从 FTQ 多读一个口，这部分成本记在第 6 节；③ LLC-only 预取占用 L1D 的 MSHR 项但不占 L1D 行，MSHR 在模型里没有数据缓冲，硬件上每个 MSHR 项要配一个 64 B 填充缓冲，所以"MSHR 数量"的成本被低估了；④ DRAM 附加延迟仍是固定的 60 ns；⑤ 指令侧 FDIP 的 µTLB 只学需求路径的翻译，不能预取没翻译过的页（约 24% 候选因此被跳过）。

### 3. 评测方法
- **选点**：从 `res_dram`（580 个 SimPoint）里，在访存重的程序里取"权重×CPI"最大的点，共 20 个：mcf 5、libquantum 4、astar 3、omnetpp 2、xalancbmk 2、bzip2 2、gcc 2；**14 个训练点 + 6 个留出点**（mcf 2、libquantum 1、astar 1、xalancbmk 1、gcc 1），调参只看训练点，留出点只用来确认。另有**守卫集**（计算密集：hmmer 2、h264ref 2，加 perlbench/gcc/gobmk/sjeng 共 14 个点）验证预取不拖累不需要它的程序，指令侧另用 10 个代码重的点。
- **指标**：每个点 IPC 相对"关闭预取"的比值，取几何平均；每个点 2000 万条指令（1000 万预热 + 1000 万测量）。
- **执行**：本机 8 并行 → 后期放到 3 台阿里云（Xeon 6982P-C，32 vCPU）；云上重编了 softfloat（用 git 历史里的 Linux 版）和模拟器，5 个校验程序的周期与 Mac 逐个相等，**云上与本地的 14 个训练点周期逐点完全相同**。

### 4. 结果

**数据侧演进（训练集 14 点，几何平均加速）**

| 配置 | 加速 | 说明 |
|---|---|---|
| next-line 度数 4 | +20.4% | mcf +10% 但 astar/bzip2 变差 |
| IP-stride | +23.2% | |
| Best-Offset | +25.6% | libquantum 最好，mcf +3.6% |
| BO + 准确度限流 | +26.5% | 消除了 astar/bzip2 的亏损 |
| BO + 限流 + 预取可用全部 MSHR（`RESERVE=0`） | +29.9% | 其他程序没受损 |
| BO + 限流 + LLC next-line（1 行） | +32.9% | mcf 收益来自 LLC |
| 步长 + 限流 + 度数 8 + LLC next-line（2 行） | +35.4% | |
| 加距离 2、LLC 行数改 1（**h1**） | **+37.9%** | 最终配置 |

**最终配置 h1**：`ALGO=2 THROTTLE=1 DEGREE=8 RESERVE=0 NLLC=1 DIST=2`（**全局**步长检测器（PC 哈希恒为 0），训练在 load 未命中和预取行首次使用上，距离 2、度数 8，准确度限流，预取可占满 8 个 MSHR，另有 LLC 次级引擎预取后 1 行）。

| | mcf | libquantum | astar | omnetpp | xalancbmk | bzip2 | gcc | 几何平均 |
|---|---|---|---|---|---|---|---|---|
| h1，20 点（云上，当前代码） | 1.145 | 3.399 | 1.038 | 1.037 | 1.166 | 1.007 | 1.003 | **1.3557** |
| 训练 14 点 | | | | | | | | 1.3786 |
| **留出 6 点（调参时没看过）** | | | | | | | | **1.3036** |

训练集的 +37.9% 带有选优偏差，**对没见过的点的估计是 +30%**。留出集上各配置排序不变：h1 +30.4% > g2 +28.1% > g4 +27.9% > f3 +25.6% > Best-Offset +24.0% > 基础步长 +16.4%。

**守卫集（计算密集，14 点，h1 对关闭预取）**：几何平均 **+0.5%**，最差单点 −0.5%（gobmk）；hmmer +0.1%、h264ref +0.1%~+0.6%、gcc +0.5%~+1.0%、sjeng 0%。预取不拖累计算密集的程序。

**几个有结构意义的对比**
- **预取必须填进 L1D（流式）**：BO 的远处几行改成"只填 LLC"，libquantum 从 ×2.65 降到 ×2.27。
- **LLC 次级 next-line 是 mcf 的关键**：只做"LLC next-line"就让 mcf +16%（L1D 里用不上，它们是被换出后命中 LLC 的）；但 LLC 行数从 1 行加到 2、4 行反而更差（mcf 1.190 → 1.168 → 1.140），跳过紧邻的下一行（`NLLC_DIST=2`）也更差。
- **IP-stride 比 Best-Offset 更好**：同样带 1 行 LLC next-line 时，训练集 +36.3%（步长，g4）对 +32.9%（BO，f2）；留出集上 h1 +30.4% 对不带 LLC 引擎的 BO（e0）+24.0%。步长 + BO 的组合反而不如单独步长（训练集 +33.6% 对 +35.4%，−1.8 个百分点）。
- **准确度限流**对阈值不敏感（放宽到 60/25 完全相同），但有无差别很大（astar −3.7% → +1.5%）。
- **libquantum 卡在"在飞请求数"**：BO 配置下所有变体都是 ×2.646，用 6 个可用 MSHR × 64 B / 113 ns ≈ 3.4 GB/s 恰好等于实测带宽。放开保留项（8 个 MSHR 全可用）→ ×2.95，MSHR 总数加到 16 → ×3.54（h1，相对同样 16 个 MSHR 的基线整体 +37.2%，比 8 个时只多 1.6 个百分点），**说明主要瓶颈是在飞预取数**，但翻倍 MSHR 的面积（每项带 64 B 填充缓冲）对整体收益不划算。
- 预取行低优先级插入（不更新 PLRU）：+0.1%，不采用；度数 4（对 8）使 libquantum 从 3.34 掉到 2.79，度数 8 必要。
- **指令侧**：I-cache 的 miss 惩罚周期占总周期 30%~50%（perlbench、gobmk），每次约 13 周期（LLC 命中）。next-line 预取是**负收益**（度数 1/2/4：−0.75%/−0.89%/−1.23%，因为 miss 多在分支目标和调用处，且部分触发来自错误路径，预取的行挤掉了有用行）；FDIP（4 个在飞，µTLB 16 项）把 I-cache miss 降了 21% 但周期只少约 1%，几何平均 **+0.4%**；叠加在 h1 上整体 **−0.1%**。**结论：指令侧预取暂不采用**，I-cache miss 惩罚大部分被后端的访存等待掩盖。

**修复 PC 之后（真实 PC，8 位步长，不跨页，20 点云上重跑）**：真实 PC 版本**没有更好**，略差：h1 20 点 +35.6%（全局）→ +34.9%（真实 PC）；mcf 不变（×1.145 对 ×1.146）；libquantum ×3.399 → ×3.376；xalancbmk ×1.166 → ×1.098（流被按 PC 拆开后训练更慢、哈希冲突）；bzip2 +1.8%。g4/f3/基础步长同样略差。**所以全局步长既更好又不需要从 LSU 传 PC**，设计更便宜（省掉 LDQ 里 64×10 位和 L1D 流水线里的连线）。

**指令侧上限**（把 I-cache 做到几乎无 miss，128 路，`CFG_ICACHE_WAYS`）：10 个代码重的点几何平均 **×1.053**（perlbench ×1.080、gobmk ×1.126、sjeng ×1.023、gcc ×1.001；单点最高 gobmk sp24 ×1.159、perlbench sp25 ×1.148，perlbench sp25 的 miss 309,840 → 11,824）。这就是**阻塞式 I-cache 全部代价的上限**；FDIP 只拿到 +0.4%。

**其他三个云上批次**：MSHR 16 + 预取保留项 2 对比保留项 0：+0.2%（无意义）；h1 叠加 FDIP 的三种参数（4 个在飞 µTLB 16/64 项、2 个在飞 µTLB 32 项）相对 h1：−0.02% ~ −0.13%，指令侧 FDIP 在数据侧预取之上没有增益。

### 4b. 为什么 mcf 的收益低（2026-11-06 研究）

mcf 的 5 个点 h1 的提升只有 ×1.07~×1.25。研究用了一个仅在 `-DPF_STUDY` 下编译的探针（`PfStudy.h`，按完整 PC 统计 load miss、支持"理想 L1D"和"按 PC 理想"）。

- **上限**：理想 L1D（所有 load 命中）sp60 ×2.49、sp71 ×2.85；DRAM 附加延迟 60 ns → 0（平均读延迟 113 → 52 ns）只有 sp60 ×1.28，说明 mcf 的损失**大半在 L1D→LLC 一段**，不是 DRAM 延迟本身。L1D 未命中约 50%，其中约 82% 命中 LLC。
- **sp60 的 miss 几乎全部来自 `primal_bea_mpp` 一个循环里的 6 条 load**（99.8%）：`a5 += t1`（步长 `nr_group × sizeof(arc)`）后读 `arc->ident`（33%，物理行地址差 **+45,548 行 = 2.9 MB 占 77%**）、`arc->tail/head/cost`（约 22%，同一条 arc 的其他字段）、再读 `tail->potential` 和 `head->potential`（24% 和 21%，**依赖前面读出的指针**，行地址差无规律）。
- **按 PC 的理想上限**（只让指定 PC 的 load 命中）：sp60 完美的 arc 字段预取 **×1.91**，完美的 node 间接预取 ×1.21，两者都完美 **×2.49**（等于整体理想 L1D，说明 sp60 的损失全在这个循环）；sp71 里这个循环只占 ×1.32（arc ×1.22、node ×1.04），其余在 `refresh_potential`/`update_tree`/`primal_iminus`（树遍历，纯指针追逐），整体上限 ×2.85。
- **为什么步长预取抓不到**：① 步长 45,548 行远超我的 8 位步长字段（±127 行）；② 预取候选限定在 4 KiB 页内，2.9 MB 的步长必然跨页，全被丢弃；③ （PC bug，见上）；④ MSHR 饱和（h1 在 mcf 上 `probe_mshr_full` 40 万~150 万次，预取经常因 MSHR 被占满而放弃）。h1 在 mcf 上发的 110 万~200 万次预取几乎全是"LLC 后 1 行"引擎发的，步长预取只填了约 300 行。
- **加宽步长字段到 18 位 + 允许跨页（模型近似：假设相邻迭代的物理距离恒定，sp60 里 77% 成立；硬件上需要 DTLB 翻译或按虚拟地址训练）**：sp60 ×1.243 → **×1.343**、sp38 ×1.250 → ×1.361、sp71 ×1.085 → ×1.106、sp16/sp32 ×1.07/×1.09 → ×1.09/×1.11；预取准确度约 90%（sp60 填 131 万行、118 万次被用到）。所以 arc 扫描确实被抓住了，但离 ×1.91 的上限还差一截（预取距离、MSHR 并行度）。（这一组同时带了 PC 修复和负步长修复，20 点全量的拆分验证见 `gw_*`/`pw_x` 配置，云上进行中。）
- **20 点全量验证（云上，同一份代码，只动步长位宽、是否跨页、PC 与全局）**：

| 配置 | mcf | libquantum | xalancbmk | 20 点 | 留出 6 点 |
|---|---|---|---|---|---|
| h1：全局，8 位步长，页内 | 1.145 | 3.399 | 1.166 | +35.6% | +30.4% |
| 全局，18 位步长，页内（`gw_nx`） | 1.144 | 3.399 | 1.166 | +35.5% | +30.4% |
| 全局，18 位，**跨页**（`gw_x`） | 1.127 | 3.773 | 1.186 | +38.2% | +33.2% |
| 真实 PC，18 位，跨页（`pw_x`） | 1.195 | 3.720 | 1.108 | +39.2% | +33.2% |
| 按 PC 表 + 1 个全局表项（混合），18 位，页内（`hy_nx`） | 1.137 | 3.397 | 1.144 | +35.3% | +29.8% |
| 混合，18 位，跨页（`hy_x`） | 1.184 | 3.750 | 1.156 | +39.7% | +33.0% |
| 混合，跨页，预取距离 4（`hy_x4`） | 1.184 | 3.836 | 1.144 | +40.0% | +33.2% |

  结论：**单独加宽步长没有收益（页内发不出去）；决定性的是跨页**：libquantum 的顺序流跨页后 ×3.40 → ×3.75，mcf 的 arc 扫描只有跨页 + 宽步长才能抓到；**页内版本不论是全局、按 PC 还是混合，都停在 +35% 左右**；跨页后三种设计在留出集上几乎一样（+33%），混合多花的一个表项没有换来收益。全局步长对 xalancbmk 好（多流混在一起反而稳），按 PC 对 mcf 好（多个循环各有各的步长），两者互补，但互补的幅度（约 +0.4 个百分点）不值得多一份表。**跨页是模型近似**（用物理地址上的恒定差；硬件上要给预取目标做 DTLB 翻译，或按虚拟地址训练再翻译），成本和时序要单独评估；它能多给约 3 个百分点（留出集），而且是流式程序（libquantum）和大步长扫描（mcf）才受益。
- **剩下的是指针追逐**：node 间接访问（sp60 里 ×1.21）和 sp71 的树遍历需要"读到预取回来的 arc 行里的 tail/head 指针再去预取 node"这类间接预取，需要数据值和虚拟地址翻译，成本大，没做。

### 5. 过程中发现并修复的问题（预取代码和评测流程）
0. **LSU 传给预取器的 PC 恒为 0**（`inst->pc` 对 load 没有被填，应取 `inst->dbg.pc`），导致"IP-stride"实际是全局步长；是在做 mcf 的 PC 访问模式统计时发现的。同时发现步长生成器的负步长被错误地按无符号 8 位累加（下降的流会跑到 +255 行外），已改为有符号。
1. 预取行"是否预取"标志在最常见的填充分支漏传（脚本替换误伤），导致首次使用事件丢失、第一轮结果作废并重跑。
2. "只填 LLC"的预取项释放 MSHR 时没有给 LSU 发"MSHR 空出"事件，预取占满 MSHR 时普通读无人唤醒，ROB 死锁；同时普通读命中在飞预取项时需要升级为普通填充。两处都已修，涉及 LLC-only 的早期结果已删除重跑。
3. 次级生成器和主生成器同周期写 FIFO 超过 1 个写口，被电路规则检查抓住并修正。
4. 云上：中止的并行传输通过 rsync `--partial` 留下了损坏的检查点（只有 bzip2 sp10 一个点），模拟器在 `gzread` 里死循环；新增 `verify` 子命令校验每个检查点（含"空 gzip 也能通过 `gzip -t`"的情况）。已发布的数字不受影响。
5. 本机多次并行超过用户给定的上限（8），影响了用户使用，之后云上做评测、本机只做开发。

### 6. 面积与时序估计（第一步，粗估）

**状态（h1 配置，位数由模型自动统计）**：步长表 2624 位 + 请求 FIFO 232 + 生成器 39+31 + 限流 22 + 输入寄存器 108 = **3056 位（382 B）**，预算 4 KB 的 9%。预取器之外的成本：L1D 每行 1 位标记 256×4 = 1024 位；LSU→L1D 的 PC 哈希 LDQ 64×10 = 640 位 + 流水寄存器/连线约 120 位（**实测全局步长比真实 PC 更好，这 760 位可以整体省掉**，则合计约 4.1 Kb）；MSHR 每项 2 位 + 填充通路 2 位，约 18 位。**合计约 4.9 Kb（约 0.6 KB）**，大约是 L1D 数据阵列（64 KB）的 1%。Best-Offset 版 3546 位，同量级。

**时序（结构分析，没有综合）**：
- 预取逻辑本身：IP-stride 一次决策是"表读 → 标签比较 → 26 位减法 → 与步长比较 → 置信度更新"，训练事件已先寄存一拍，可拆成两拍；生成器每周期只发 1 个候选，没有宽比较器和宽加法。复杂度低。
- 对已有关键路径的影响集中在三处：① **tag 探测借用空闲 load 口**：需要在 load 口的 tag 读地址上多一级选择（LSU 请求地址 vs 预取地址）和"空闲口"判断，这是 L1D 查找路径，最敏感；缓解办法是 LSU 在上一拍就告知下一拍哪个口空闲；② MSHR 向 AXI 发请求从"取最低下标"变成"先取普通读、再取预取"的两级优先选择，8 项很小；③ MSHR 分配**不需要新增分配口**，预取借用空闲 load 口自己的分配槽。
- 综合没有做；这一节要等时序综合流程（TODO 中已有）才能给出 WNS。

### 7. 结论与建议
- **采用 h1 作为数据侧预取器的候选设计**：对访存瓶颈点留出集 +30%，计算密集程序无副作用，状态 0.4 KB、**不需要从 LSU 传 PC**（全局步长），总成本约 0.5 KB，不新增 tag 端口。
- **可选升级：允许预取跨 4 KiB 页**（需要给预取目标做地址翻译）：留出集再多约 3 个百分点（+30% → +33%），主要来自 libquantum 和 mcf；决定做不做取决于 DTLB 多一个探测口的成本。
- **不采用指令侧预取**（+0.4%，叠加后为负）。
- 如果要继续压榨：在飞预取数是 libquantum 的上限，"为预取单独加一小组 MSHR/流缓冲"比"把所有 MSHR 翻倍"更划算；训练也可以扩到 store 未命中。
- **未做/限制**：只测了 12 个 SPEC 程序里的 8 个，没有 Linux 启动、也没有多核；留出集只有 6 个点；FDIP 的 µTLB 太小、没试过用真实 ITLB 端口；没做指针类（CDP）预取——它需要虚拟地址和 DTLB 翻译，成本大；store 未命中没有参与训练；DRAM 单通道 8 bank、60 ns 常数附加延迟；综合与 RTL 都没做。
- **复现**：`gmake LDFLAGS="-lz" DS3_DIR=<DRAMsim3> DS3_LIB=<lib> BUILD_DIR=build_area/x`；运行期用环境变量选算法，如 `PF_ALGO=2 PF_THROTTLE=1 PF_DEGREE=8 PF_RESERVE=0 PF_NLLC=1 PF_DIST=2 PF_STATS=1`（`PF_STATS=1` 打印状态位数和各类计数）；`scripts/pf/run_eval.sh`（评测点集）、`scripts/pf/table.py`、`scripts/pf/cmp_cloud.py`（汇总比对）、`scripts/pf/cloud/fleet.sh`（云上批量运行）；结果在 `~/personal/AI-Huma-data/spec-rv32imab/tm/pfexp{,_cloud}/`。

### 8. 次要任务一：用 agent 迭代做架构探索，哪些经验有用
- **先固定评测，再让 agent 改设计**：点集、基线、汇总脚本、回归检查都不让设计迭代去动；训练/留出拆分和守卫集从第一天就有，否则"选优偏差"会悄悄进到结论里（这次训练 +37.9%、留出 +30.4%）。
- **把"电路约束"做成运行时的硬检查**，而不是靠 agent 自觉：位宽截断、每周期端口数上限、状态预算三条规则让不合理的设计直接中止，而且确实抓出了真问题。
- **每次改动都要有"关闭时与基线逐周期相同"的回归**，并且**把统计和行为分开验证**：这次最大的两个坑（标志漏传、唤醒事件缺失）都靠"统计量对不上"才发现——`issued` 应当等于 `filled`、有用 + 无用应能解释周期变化。
- **看结构性对比，不只看总分**：最有价值的发现（LLC next-line 才是 mcf 的收益来源、libquantum 卡在在飞请求数、远处行必须填 L1D）都来自"同一个旋钮在不同程序上方向相反"，不是来自最高分。
- **工程化的坑也要进经验**：评测一轮 40~50 分钟是迭代的主要成本，上云把它降到约 20 分钟；一旦并行、传输、校验出错，会悄悄污染结果（本次的损坏检查点、被删的结果文件），所以每个脚本都应该幂等、能校验、不覆盖已有结果。
- **子 agent 适合做边界清楚的只读研究**（如仿真提速调研），不适合直接改共享状态。

### 9. 次要任务二：trace-model 自身的提速方向（2026-11-06，子 agent 调研 + 实测）
报告全文在本会话的 scratchpad（`sim_speedup_report.md`），这里记结论。数字里**只有 PGO 是实测并验证了周期的，其余都是估计**。
- **时间分布**（mcf，占总时间）：`back.comb` 51%、前端 BPU/取指 16%、AXI+LLC+DDR 合计约 23%（其中 DRAMsim3 只有 3.4%~4.4%，批量推进最多省 4%）、各 seq 合计约 10%；`back.comb` 内部也很平。`memmove` 7%（很多次小结构体拷贝，单次只有几百字节）。
- **空转周期很少，整核快进收益有限**：严格"全核状态与上一周期相同"的周期 mcf 只有 1.2%、libquantum 0.25%，原因是 LSU 等 miss 时每 4 周期向 L1D 重放一次（`replay_delay_cycles`），请求编号每次递增。按"每 4 周期重复一次"的判据，可预测重复的周期占 mcf 19%、libquantum 35%；但这些周期仍要花活跃周期 60%~70% 的耗时，所以现实的快进收益只有 mcf ×1.13、libquantum ×1.27，而且要给 LSU/MSHR/L1D/TLB/ICache/BPU 各加"推进 k 周期"的接口，AXI 一侧在等 DRAM 时是在确定性演化而不是空闲，相位对齐很绕，**风险高，不建议先做**。
- **PGO（实测）**：同机并排对跑，mcf 快 10.6%~13%、训练里没有的 astar 快 11%，**周期逐位不变**（3 个小程序、完整长度的 mcf/libquantum 点；云上 gcc 构建同样通过 3 个校验程序）。云上构建用 `scripts/pf/cloud/pgo_build.sh`（`fleet.sh pgo <目录> [标志]`）：instrument 构建 → 4 个点各 500 万周期训练 → 同一目录里用 profile 重编 → 校验周期 → 并排计时；mcf 600 万周期用户时间 52.6 s → 47.0 s。thin LTO 单独约 −5%。
- **多线程**：同周期内前端 → 后端 → L1D/MSHR → AXI 是一条组合依赖链，每个活跃周期只有约 5~10 µs，同步开销占一成以上；最大的 `back.comb` 占 51%，两线程上限不到 ×1.6、现实 ×1.2~1.4；GSIM 论文里单线程 GSIM 对 8 线程 Verilator 仍快 ×1.18，说明细粒度多线程 RTL 仿真回报低。**点与点之间的并行（云上每台 20 个进程）才是高效的多核利用。**
- **写法层面的改动（均未实现）**：`Dispatch::is_preg_woken` 改位图（约 2%）、Exu/Isu 的 `comb_begin` 改脏标记（2~3%）、`TlbMmu` 备忘（2~4%）、BPU 备忘（3~6%）、去掉 `SimCpu::cycle`/`back2front` 里的冗余结构体拷贝（1~2%）、`Bridge::find` 改直接索引（约 1%）、LLC 备忘扩展（1~2%）、DRAMsim3 关 epoch 打印（≤1%）；合计估计 ×1.1~1.15。再往上是模块级"输入没变就不求值"的活动门控（GSIM/ESSENT 思路，估计再 ×1.1~1.25，中风险）。
- **允许误差时的选项**（未测）：用功能模型做预热代替 1000 万条详细预热（约 ×1.8，误差通常 1%~2%）；筛选阶段缩短测量窗口、只跑敏感点；AXI/LLC/DRAM 放另一个线程并加固定一拍延迟（×1.2~1.3，延迟可补偿）；区间/解析模型误差过大不适用。验收线建议：近似版本的"提升比"偏差 <0.5 个百分点且配置排序不变。

迟 `CONFIG_SIM_DDR_LATENCY_CALC` = 86 ns。改成 60 ns 后 dhrystone/coremark 的平均读延迟约 85–87 ns，与 86 ns 吻合（32 ns 时 56–58 ns，memory-stress-small 81 ns → 105 ns）。`DS3_EXTRA_NS` 仍可覆盖。

DDR 配置：DRAMsim3 `DDR4_8Gb_x16_3200`（tCK 0.63 ns，CL/tRCD/tRP 22，1 通道、64 位、2 bank group × 4 bank、BL8、open page、地址映射 `rochrababgco`、rank 级交错刷新），与 `config.h` 里原来的 CL 22 / tRCD 22 / tRP 22 / 1600 MHz 一致。

| 程序 | 32 ns | 60 ns |
|---|---|---|
| dhrystone | 158,756 | 162,033 |
| coremark | 250,658 | 255,335 |
| memory-stress | 2,425,029 | 2,428,470 |
| smc-div | 11,096 | 11,348 |
| smc-addi | 10,966 | 11,218 |
| memory-stress-small | 343,975 | 347,305 |

`baseline.csv` 63 个程序：周期平均 +23%、中位 +28%、最大 +36%；gate 62/62。RTL：`ref_cycles.txt` 重新生成，`fm_gate.sh` 66/66、66 个周期与 trace-model 全部相等；Linux 从复位启动到 `rv32 login:`（`RQD=8`，无断言、无不一致）。trace-model 上 LLC 读响应队列峰值：master 1 排队 3 + 输出寄存器（32 ns 时 4 + 1），`RQD=8` 仍够用，延迟变高反而排队更少。

SPEC 全量回放（580 点，无失败，无 difftest 不一致；`tm/res_dram60`，12 路并行）：

| 程序 | 加权 IPC | 估算分数@1GHz | 32 ns 的 IPC |
|---|---|---|---|
| 400.perlbench | 2.092 | 8.08 | 2.131 |
| 401.bzip2 | 1.600 | 7.13 | 1.645 |
| 403.gcc | 1.474 | 9.32 | 1.590 |
| 429.mcf | 0.405 | 12.62 | 0.463 |
| 445.gobmk | 1.763 | 8.85 | 1.783 |
| 456.hmmer | 3.720 | 9.75 | 3.718 |
| 458.sjeng | 1.834 | 8.44 | 1.858 |
| 462.libquantum | 0.663 | 4.73 | 0.857 |
| 464.h264ref | 1.475 | 6.08 | 1.489 |
| 471.omnetpp | 1.333 | 6.92 | 1.508 |
| 473.astar | 0.928 | 7.00 | 0.975 |
| 483.xalancbmk | 1.873 | 12.04 | 1.959 |
| **几何平均** | **1.396** | **8.12** | 1.487（分数 8.66） |

quick 的 6 个程序（旧基线 `tm/b3` 同一批点）：几何平均 IPC 旧（16 倍分频）2.204 → 32 ns 1.613 → 60 ns 1.550。分数的换算方法和局限见上面"估算分数"一段（参考时间是凭记忆写的，未核对官方表）。

综合前后对比（2026-11-06，Yosys + yosys-slang 的相对面积代理，`scripts/synth_module.sh`，`SYNTH_LIGHT=1 SYNTH_MEM=1`；改动前 = `main`/`exp/batch3` 的 rtl，改动后 = `exp/dram-sim`；**不是工艺库面积、没有时序**）：

| 模块 | 改动前 | 改动后 | 变化 | 原因 |
|---|---|---|---|---|
| `axi_llc_rq`（每个读主设备一份） | 10,439 单元 / 2,584 触发器 | 18,768 / 4,649 | +8,329 / +2,065（+80%） | `RQD` 4 → 8 |
| `axi_llc`（整个 LLC，`NR=4` 个读主设备） | 489,436 / 22,324 | 522,758 / 30,584 | **+33,322 / +8,260（+6.8% / +37%）** | 4 × `axi_llc_rq` 的增量，吻合 |
| `lsu_dc_req_st` | 86,150 / 0 | 62,755 / 0 | **−23,395（−27%）** | store 窗口 20 → 15 |
| `dcache_resp`、`axi_cpu_port_chan` | 14,113 / 38；59 / 24 | 相同 | 0 | 单独综合时 `phase0`、`phase_last` 是悬空输入，看不出常量化的效果 |

净变化约 +9.9k 单元（+33.3k − 23.4k），相对整机推算的约 952 万个门不到 0.2%；触发器 +8,260，相对整机约 18.1 万是 +4.6%，全部来自 `RQD`。`mem_top` 的 `TICKS == 1` 常量化（去掉 16 tick 折叠逻辑）预计是减量，但 `mem_top` 太大，Yosys 超时，没有测到。每增加一项 `RQD`，4 个队列合计约 +8.3k 单元（`RQD=5` 即最小可用值约 +8.3k，`RQD=6` 约 +16.7k，`RQD=8` 为 +33.3k）。

### 10. 冻结版 h1 与 RTL 实现（2026-11-06）
- **冻结版**：trace-model `exp/prefetch-h1`（从研究快照 `exp/prefetch` `27a878f` 切出，`0eb258c`；默认开 `1fe92b5`）。单表项全局步长（8 位有符号步长，2 位置信度，度 8、距离 2，页内）+ 1 行 LLC-only next-line + 8 项请求 FIFO；无 PC、无限流、无 BOP、无 I 侧预取、无研究开关。`PF_ENABLE=0` 关闭。状态约 0.4 KB（FIFO 8×27 位、步长表项、两个生成器、训练输入寄存器）+ L1D 每行 1 位（1,024 位）。
- **与研究版 rv_s2 的差别**：步长 8 位有符号（研究版曾把负步长截成无符号）；因此冻结版的 20 点数字不会与 rv_s2 逐位一致，**云上 20 点复跑尚未做**（服务器已关），引用的 +35.5% / +30.6% 仍是研究版 rv_s2 的数字。
- **关闭时周期不变**：trace-model gate 62/62 与旧基线逐个相同（`results/baseline/baseline_nopf.csv`）；64 KiB LLC 的 5 个测试与 main 相同。
- **开启时**（默认）：gate 62/62 对照新 `baseline.csv`；dhrystone 162,033 → 161,183（−0.5%），coremark 255,335 → 256,573（+0.5%），memory-stress 2,428,470 → 2,383,063（−1.9%），memory-stress-small 347,305 → 334,635（−3.6%；64 KiB LLC 下 971,687 → 632,880）。小程序里 25 个周期有变化。
- **RTL**（rtl `exp/l1d-prefetch`，规格 `rtl/docs/modules/dcache_pf.md`）：新 `dcache_pf`、L1D stage1 探测槽、stage2 事件、MSHR 的 `is_prefetch/no_fill`/提升/两遍 AXI 选择/无填充释放、阵列 pf 位、LSU 到 L1D 的 `replay` 位（训练要排除 LSU 重放；原 RTL 接口里没有）。`PF_EN=1`（默认）：门禁 66/66 逐条对比通过，**66 个程序周期与 trace-model 逐个相等**；`PF_EN=0`：66/66，周期与旧基线相同。面积代理：`dcache_pf` 3,334 单元、422 触发器，阵列 +1,024 触发器，`dcache_mshr` 95,540 → 95,020（噪声内）；工艺库、WNS 未做。
- **RTL 里发现的实现错误**：`always_comb` 多驱动（预取器从不入队）、`no_fill` 标志没有和 `pf` 相与（需求项被误标，dhrystone 差 2 周期）。逐周期定位办法：两边各打印 `take/alloc/relnf` 事件序列后对比。
- **未做**：`axi_llc` 读响应队列 RQD（现 8）在预取下的重测；冻结版 SPEC 20 点复跑；跨页预取（要 DTLB 翻译）；时序。

### 11. 全量 SPEC、坏点原因与控制实验、合入（2026-11-07）

- **全量 SPEC（580 点，fast warmup，对比 2026-11-05 精确 PF 关基线）**：按 SimPoint 权重的 12 个程序几何平均 **+8.3%**（libquantum +96.3%、mcf +10.8%、gcc +9.0%、bzip2 +6.2%、h264ref +2.7%、perlbench +2.7%、astar +2.3%、omnetpp +0.9%、xalancbmk −0.2%、gobmk −0.8%、hmmer −1.6%、sjeng −3.0%）；580 个点不加权的几何平均约 +11.2%。fast warmup 的系统偏差约 −0.5%（绝对 IPC）、对"预取加速比"约 −0.3 个百分点，方案之间的差异同口径可比。`400.perlbench ckpt_sp11_target184332` 曾缺失：服务器上的检查点文件被截断（本地 gz 完好），重传校验后补齐，该点 +12.2%。
- **坏点是真的，不是 fast warmup 的假象**：12 个最差点用精确预热重跑，omnetpp sp22 −40.7%（fast −40.9%）、gcc sp38 −29.9%、xalancbmk sp34 −22.2%；只有 hmmer、sjeng 和 xalancbmk sp30 的约 −5% 是 fast warmup 造成的（精确预热下约 0%）。全量里低于 −10% 的点共 5 个（约 0.9%）。
- **原因**：LLC-only 的 next-line 引擎在这些点上发出几十万个预取、真正被用到的只有几百个（omnetpp sp22：发出 50 万、用到约 500）；关掉该引擎后 12 个点中 10 个回到 0% 附近。omnetpp 的伤害是 MSHR 争抢（`probe_mshr_full` 52 万次），gcc sp38 是 DRAM 带宽或 LLC 污染（MSHR 预留无效）。xalancbmk sp15 例外：关掉引擎反而更差（−11.8% → −21.3%）。但引擎也是 mcf（+10.8%）、gcc、bzip2 收益的主要来源。
- **控制实验（都没有进入源码树，补丁在 trace-model `docs/experiments/exp009_llc_engine_control.patch`，开关 `PF_LLC_THR/PF_LLC_WIN`、`PF_RES_LLC`、`PF_DUEL_SLICE/PF_DUEL_EXPLOIT`）**：
  1. 准确率节流（256 位过滤器记"本该预取的行"，每窗口命中数低于阈值则关）：THR=6、窗口 32 最好，最坏点压到 omnetpp sp22 −1.2%、gcc sp38 −8.1%，但 mcf 只剩 +2.1%（第一版 64 位过滤器假命中约 40%，永远不关，无效）。
  2. LLC 预取探测时预留 MSHR：预留 6 才修好 omnetpp sp22（−4.4%），mcf 同时降到 +0.6%；对 gcc sp38 基本无效。
  3. 时间片对抗（轮流开/关 LLC 引擎，比较 demand 访问数/周期）：片长 131072 周期、生效 8 片，mcf +7.7%，但 gcc sp38 仍 −28%、omnetpp sp22 −14%。
  全量对比（三方案都有结果的 579 个点）：h1 **+8.2%**，THR=6 +7.2%，对抗 +7.7%；低于 −10% 的点 5 / 2 / 4 个，最差点 −40.9% / −23.6% / −28.3%。**结论：平均收益 h1 最高、硬件最简单，保持 h1 原样合入**；mcf 与坏点此消彼长，没有哪个静态阈值或简单反馈能同时保住。xalancbmk sp34（−22%）原因与 LLC 引擎无关，未查。
- **评测基础设施**：稀疏检查点恢复（只恢复非零页，RSS −62% 到 −96%，结果逐字节相同；function-model `exp/sparse-mem`）；fast warmup（EXP-011 的 `--fast-warmup`）并入后单点墙钟约 1.75 倍快；云服务器 32 核/121 GB 全量约 1 小时；并发超过内存（40 以上的 4.7 GB 进程）会 OOM（rc=137）。
- **合入**：2026-11-07 合入 main（已推送）。合并时 main 已有 move elimination（EXP-012），基线用合并后的树重新生成；预取关与 main 基线 62/62 相同。

### 后续

- **已决定（2026-11-05）：不分频 + DRAMsim3 + 默认 1 GHz 作为新基线**（trace-model 侧已完成：`config.h` 默认 `FREQ_DIV=1`、`CPU_FREQ_MHZ=1000`，Makefile 默认 `DS3=1`，`baseline.csv` 已重生成，gate 62/62，大程序标准周期见 trace-model `docs/PROJECT.md`）。新旧基线周期对比：gate 平均 +146%、中位 +135%，dhrystone 150,427 → 158,756，coremark 233,515 → 250,658，memory-stress 1,541,195 → 2,425,029，memory-stress-small 189,128 → 343,975。RTL 侧已同步（见下一节），66 个程序周期与 trace-model 全部相等。
- 开启 difftest 逐条比较重跑 gate；用 Linux 启动片段、SPEC 检查点（不要用 cjpeg/linear_alg/parser/sha）测带宽和 bank 冲突敏感的负载。
- 校准附加延迟，或与 RTL 闭环里的 SimDDR 对齐；试 DRAMsim3 的地址映射和 open/close page。
- RTL 其他 store 队列窗口（`wait_mmu_stq`、`mmu_done_stq`）与 trace-model 的 15 不一致，需给 `ring_apply` 带窗口参数。
- RTL 侧合入 `main` 前还要跑 Linux 启动（`SOC_FM=1 SOC_TB_SEMIHOST=1`，数小时）和综合对比。
- Ramulator 2.0 作为后备，未试。

## EXP-008 decode 宽度 8 降到 6

- **日期**：2026-11-05
- **分支**：trace-model `exp/decode6`（改动未提交，工作区 `trace-model`）
- **问题**：前端一次给 8 条，后端 decode/rename 改成 6 宽（issue 宽度由 FU 个数决定，本实验未动 FU），性能代价多大？
- **方法**：`config.h` 新增 `CFG_DECODE_WIDTH`（默认 8）、`CFG_ROB_BANK_NUM`（ROB 行宽 = commit 宽度，默认等于 decode 宽度，可以更大）；放宽两处断言。**顺带修了 `make_rob_idx`**：原来用 `(line*BANK)|bank`，BANK 不是 2 的幂时索引错、ROB 死锁，改为 `+`（BANK=8 时等价，gate 62/62 不变）。ROB 每行放一个 decode 组，容量按行数算：6 宽时 ROB=126（21 行）；行宽 8 时 ROB=176（22 行），使行数相近。默认配置 gate 62/62；两种 decode=6 配置 62 个小程序 difftest 全过、无死锁。
- **负载**：quick SPEC（6 个程序，129 个点），基线为第 3 批（EXP-005）。

| 程序 | decode 8 | decode 6（commit 6，ROB 126） | 变化 |
|---|---|---|---|
| perlbench | 2.468 | 2.414 | −2.2% |
| gcc | 2.566 | 2.570 | +0.2% |
| mcf | 1.327 | 1.315 | −0.9% |
| hmmer | 4.007 | 3.513 | −12.3% |
| sjeng | 2.027 | 2.008 | −0.9% |
| h264ref | 1.677 | 1.648 | −1.7% |
| 几何平均 | 2.204 | 2.136 | −3.1% |

- **拆分实验**（只跑 hmmer，24 个点）：decode 6、commit 8、ROB 176 → IPC 3.434（−14.3%），没有比 commit 6 更好。commit 宽度不是原因；那 2% 的差别原因未查（推测行宽 8 时每行有空槽）。
- **原因**（埋点 `CFG_DW_HIST`：每拍 decode 取走几条；每拍被计两次，已按 IPC 校准，只看占比）：hmmer 有基线 IPC 5.8–6.4 的点，这些点掉 19–21%；sp5（IPC 6.42→5.07）decode 8 时 77% 的周期取满 8 条，6 宽就是硬上限；sp4（3.52→3.14）呈“取满 8 或取 0”的双峰，后端停顿后 decode 追赶变慢。两个点里队列积压超过 12 条的周期都 >90%，前端不是瓶颈。decode 取 0 条的周期占 20–40%（后端反压），具体哪项资源满了未查。
- **结论**：decode 6 对多数程序约 −1%，对 hmmer 这类高 IPC 程序 −12% 以上，无廉价补救。**不合入，保持 8。** 未做：decode 7；FU 裁剪（瓶颈在 decode，单独裁 FU 只会更差）；其余程序的拆分实验。
- **复现**：`gmake EXTRA_CXXFLAGS="-DCFG_DECODE_WIDTH=6 -DCFG_ROB_NUM=126" BUILD_DIR=build_area/dw6 LDFLAGS="-lz"`；拆分用 `-DCFG_DECODE_WIDTH=6 -DCFG_ROB_BANK_NUM=8 -DCFG_ROB_NUM=176`；回放结果在 `~/personal/AI-Huma-data/spec-rv32imab/tm/{dw6,dw6b8}`。

---

## EXP-007 TAGE 备选提供者计数器更新

- **日期**：2026-11-05
- **分支**：trace-model `exp/tage-alt`（工作区 `trace-model-tage`，从 `exp/batch3` 切出），改动未提交
- **问题**：BPU 预测时算出“备选提供者”的表号 `altpcpn`，一路存进 PTAB、FTQ、更新队列，但训练（`Tage::update`）从不读它。标准 TAGE（Seznec）在提供者的有用位为 0 时也训练备选提供者的计数器——补上这一步，分支预测会不会更准？
- **方法**：开关 `CFG_TAGE_ALT_UPDATE`（默认 0，关闭时 gate 62/62 与基线逐个相同）。打开后，提供者有用位为 0 时，备选提供者表的计数器（没有备选时是基础表）也向实际方向更新一步；备选表号小于提供者，与分配新项的表不重叠。打开时 gate 15 个程序周期变化，全部 difftest Success、无不一致。
- **负载**：第 3 批配置，quick SPEC（覆盖 90% 权重的点）里分支预测差的 6 个程序，共 176 个点；基线 perlbench/gcc/mcf/sjeng 用 EXP-005 的第 3 批结果，gobmk/astar 补跑。

| 程序 | MPKI 基线 | MPKI 加更新 | IPC 基线 | IPC 加更新 |
|---|---|---|---|---|
| perlbench | 8.53 | 8.53 | 2.468 | 2.471 |
| gcc | 9.30 | 9.30 | 2.566 | 2.565 |
| mcf | 16.61 | 16.62 | 1.327 | 1.327 |
| sjeng | 18.73 | 18.69 | 2.027 | 2.029 |
| gobmk | 16.26 | 16.35 | 2.130 | 2.126 |
| astar | 26.90 | 26.95 | 1.253 | 1.252 |
| 几何平均 IPC | | | 1.889 | 1.889 |

（MPKI 按 SimPoint 权重加权，分母含 1000 万条预热。）

- **结论**：没有收益（MPKI ±0.6%，有升有降）。推测原因：备选预测只在“提供者弱 + 有用位低 + `use_alt` 倾向备选”时才被采用，稳态下很少；备选表项多分支共享，额外更新也可能干扰。**不合入**；`altpcpn` 的存储可以删除（统一 FTQ 的 RTL 试做里已删，周期不变）。
- **顺带**：gobmk（16.3）、astar（26.9）的 MPKI 高于 quick 集合里的程序，做分支预测相关实验时应一起测。
- **复现**：`gmake EXTRA_CXXFLAGS="<第 3 批默认> -DCFG_TAGE_ALT_UPDATE=1" BUILD_DIR=build_area/alt`，`replay_one.sh` 回放，结果在 `~/personal/AI-Huma-data/spec-rv32imab/tm/{b3,tagealt}`。

---

## EXP-006 用 DRAMsim3 替换固定延迟的 SimDDR，去掉 AXI 子系统分频

日期 2026-11-05。分支 `trace-model` 的 `exp/dram-sim`（工作目录 `trace-model-dram`，基于 `exp/batch3` 的 `08e9cfe`，未提交、未合入）。

**状态：已合入 `main`（2026-11-06）**：trace-model `88e5254`、rtl `b19a181`，两边都是从 `exp/dram-sim` 快进合入；记录见 [MAIN_RECORDS.md](MAIN_RECORDS.md)。

> **2026-11-06 更新：附加延迟默认值由 32 ns 改为 60 ns，基线已重做**（见下面"基线重做"一节）。本节前面各表（结果 1–4、SPEC、估算分数、`RQD` 测量）都是 32 ns 版本的数字，保留作为历史；当前基线的数字以"基线重做"一节和 trace-model `docs/PROJECT.md` 为准。

### 动机

现有 `SimDDR` 只有固定 60 个 tick 的读延迟（`CONFIG_SIM_DDR_LATENCY`），不看地址：没有 bank/row、刷新、读写争用。后续要去掉"DDR 分频"、外接开源 DRAM 模拟器，先在 trace-model 上验证接入方式和影响。

### 现有的"分频"是什么

`CONFIG_AXI_SUBSYSTEM_FREQ_DIV = 16`（trace-model 与 `rtl/tb/soc/platform` 的 `config.h` 里都有）：AXI 互联、LLC、DDR、MMIO 每个核心周期跑 16 个 tick（`run_extra_axi_subsystem_ticks`，全空闲时提前跳过）。所以基线的"60 周期 DDR 延迟"其实是 60 个子系统 tick = 3.75 个核心周期，远小于真实 DRAM 延迟。这个分频让存储相对核心快 16 倍。

### 方法

- 选 DRAMsim3（umd-memsys，C++，tick 驱动，克隆到 `AI-Huma-data/third_party/DRAMsim3`，编成 `libdramsim3.dylib`；macOS 上 cmake 需加 `-DCMAKE_POLICY_VERSION_MINIMUM=3.5`）。
- 开关：`gmake DS3=1 BUILD_DIR=build_ds3 LDFLAGS="-lz"`（编译宏 `SIM_DDR_DS3`），默认关闭。**DS3 构建同时把 `CONFIG_AXI_SUBSYSTEM_FREQ_DIV` 定为 1（不分频）**，一次 `SimDDR::seq()` 就是一个核心周期。关闭 DS3 时代码与基线完全相同：dhrystone 150,427、coremark 233,515、memory-stress-small 189,128，gate 62/62 通过。
- **核心频率可配置**：编译期 `gmake CPU_FREQ_MHZ=1000`（`CONFIG_CPU_FREQ_MHZ`，默认 500），运行期环境变量 `CPU_FREQ_MHZ=1000` 覆盖。它决定 DRAM 时钟与核心时钟的比例，以及附加延迟（ns）折算成多少个核心周期。
- 实现：`sim_ddr/include/SimDDR_DS3.h`（后端）加 `SimDDR.cpp/.h`、`rv_simu_mmu_v2.cpp` 里 `#ifdef` 的几处改动。AXI 前端（AR/AW 队列、W FIFO、R burst 排放）不变。
  - 读：每个 AR 拆成 64 B 的 DRAM 读，按序送入 DRAMsim3；所有行返回后，再加固定附加延迟才允许吐数据。
  - 写：W FIFO 排空后拆成 64 B 写送入 DRAMsim3；被接收后返回 B（posted 写）。
  - 时钟：按飞秒累计时间，每个 tick 补足所需的 DRAM `ClockTick`（DDR4-3200 的 tCK = 0.63 ns）。保留分频时，被跳过的空闲 tick 也会推进 DRAM 时间。
  - 读写数据相的互斥和 turnaround 在该模式下关闭（总线由 DRAMsim3 负责）。
- 其他环境变量：`DS3_CONFIG`（ini，默认 DDR4_8Gb_x16_3200）、`DS3_EXTRA_NS`（默认 SOC+CDC = 32 ns）、`DS3_OUT`、`DS3_STATS=1`（退出时打印读数、平均/最大读延迟、写数、反压次数）。

### 模型近似（要记住）

- 附加延迟是常数：SoC、CDC 以及 PHY 路径 DRAMsim3 不建模。默认 32 ns 只取 SOC+CDC，CTL 与 PHY 的 28 ns 假定已被 DRAMsim3 自身的控制器延迟和 CL/tRCD 覆盖，没有校准过。
- 读按 AR 顺序整笔发出；SimDDR 前端仍按事务 round-robin 排放数据。
- 数据不存在 DRAMsim3 里，功能内存仍在 trace bridge。

### 勘误

本记录的第一版（同日早些时候）把每个 `seq()` 当成一个完整核心周期，没有计入 16 倍分频，延迟换算偏小，结论"小负载对 DRAM 不敏感、周期变化 ±1%"是错的，已作废。下面的数字是修正后的。另有一次增量编译混用了不同分频的目标文件，已用干净构建重测。

### 结果 1：分频的影响（原 SimDDR，不用 DS3）

| 程序 | 分频 16（基线） | 不分频（`FREQ_DIV=1`） | 变化 |
|---|---|---|---|
| dhrystone | 150,427 | 159,053 | +5.7% |
| coremark | 233,515 | 250,834 | +7.4% |
| memory-stress-small | 189,128 | 342,754 | +81% |
| gate 62 个 | — | 平均 +151%，中位 +146% | 最大 +441% |

不分频后固定 60 周期延迟才是真正的 60 个核心周期（120 ns）。基线的数字是靠分频"偷"来的。

### 结果 2：不分频，DRAMsim3 对比原 SimDDR（CPU 500 MHz，DDR4-3200，附加 32 ns）

| 程序 | 原 SimDDR | DS3 | DS3 平均读延迟 |
|---|---|---|---|
| dhrystone | 159,053 | 155,600 | 62.0 ns |
| coremark | 250,834 | 246,150 | 57.7 ns |
| memory-stress-small | 342,754 | 342,452 | 89.9 ns |
| gate 62 个（对 baseline.csv） | 平均 +151% | 平均 +80%，中位 +78% | — |

DS3 的读延迟 58–90 ns 比固定的 120 ns 低，所以周期更少；memory-stress-small 的差别小，因为它的瓶颈是带宽而不是延迟。

### 结果 3：核心频率（不分频，DS3，DDR4-3200）

| CPU 频率 | dhrystone | coremark | memory-stress-small | memory-stress-small（64 KiB LLC） |
|---|---|---|---|---|
| 500 MHz | 155,600 | 246,150 | 342,452 | 571,850 |
| 1000 MHz | 158,756 | 250,658 | 343,975 | 799,040 |
| 2000 MHz | 164,862 | 260,914 | 366,989 | 1,335,536 |

频率翻倍，DRAM 延迟折合的核心周期数翻倍：dhrystone 每翻倍约 +2–4%，访存密集的 memory-stress-small（64 KiB LLC，约 2.3 万次读、1.1 万次写）约 +40–67%。

### 结果 4：gate 全集（不分频 DS3，500 MHz）

62 个测试里 61 个正常退出；`dcache-conflict-writeback` 超过 gate 的 4 倍基线周期上限（3,616）而被判超时，原 SimDDR 不分频时同样超限。提交指令数 58 个与基线相同，另 4 个不同：3 个是中断类（`interrupt-vectored`、`supervisor-external-interrupt-vectored`、`timer-interrupt-mask`，中断到达点随周期变化，预期）以及上面那个超时的。默认的 `[TB_CHECK]` 没开比较（compared=0），所以正确性只靠提交数一致和正常退出，没有跑 difftest 逐条比较。

### 结论

- 接入可行：AXI 端口不变，只换时序；关闭 DS3 与基线逐周期相同。
- 现有 16 倍分频掩盖了 DRAM 延迟：不分频后原模型就比基线慢 5–80%（gate 平均 +151%）。以后凡是不分频，基线周期数、gate 的 baseline.csv、docs 里的标准周期都要重新生成。
- DRAMsim3 给出 58–90 ns 的平均读延迟，比固定 60 周期（120 ns）更合理，并且随地址和读写争用变化。
- 核心频率会明显改变结果，需要在记录里标明频率；默认 500 MHz。

### RTL 侧同步（2026-11-05，`rtl` 的 `exp/dram-sim`，工作目录 `rtl-dram`，基于 `exp/batch3` 的 `52d2b84`，未提交）

RTL 里的 16 倍分频是 `mem_top` 的 4 位 `phase_q`（每 CPU 周期 16 个快 tick，`phase0` 是 tick 0、`phase_last` 是 tick 15），`axi_cpu_port_adapter`、`dcache_resp`、`mem_axi` 的累积/锁存逻辑都按 `phase0`/`phase_last` 写，所以把它参数化即可，不需要改这些模块：

- `trace-model/include/config.h` 新增 `constexpr int AXI_SUBSYSTEM_FREQ_DIV`，`gen_cfg.sh` 把它带进 `ttg_cfg_pkg.sv`（用 `SIM_SRC=<trace-model-dram 的绝对路径> scripts/gen_cfg.sh` 重新生成；新包只多这一项，并更新了 `CONFIG_CPU_CYCLE_FS` / `CONFIG_SIM_DDR_LATENCY_CALC` 两个随频率变化的派生值）。
- `mem_top.sv`：`phase_q` 在 `TICKS-1` 后回 0，`phase_last = (phase_q == TICKS-1)`；`TICKS = AXI_SUBSYSTEM_FREQ_DIV`，取 16 时与原来逐位相同，取 1 时 `phase0` 和 `phase_last` 恒为 1。
- `tb/soc/soc_tb.cpp`：`kTicks` 取自平台 `config.h`（`CONFIG_AXI_SUBSYSTEM_FREQ_DIV`，现为 1）；空闲 tick 跳过只在 16 tick 时启用；`ddr_idle` 改用 `idle_quiescent()`；复位期间不推进 DDR 模型（否则 DRAMsim3 的时钟比 trace-model 早 3 个周期，所有程序差 1 周期）。
- 平台模型 `tb/soc/platform`：`config.h` 改为不分频、1 GHz；`SimDDR.cpp/.h` 换成 trace-model 的版本加 DRAMsim3 后端，再加编译宏 `SIM_DDR_DATA`（读数据取自、写数据落到 `PhysMemory`，复刻原 `do_memory_read/do_memory_write`；trace-model 构建不开它）。
- `tb/soc/build.sh`：默认带 DRAMsim3（`DS3=0` 退回固定延迟，`DS3_DIR` 指向 DRAMsim3 目录），并一律定义 `SIM_DDR_DATA`。
- `scripts/ref_cycles.txt`：66 项参考周期用新基线的 trace-model 重新生成。

结果（整核测试平台，带功能模型逐条比对）：

| 检查 | 结果 |
|---|---|
| `fm_gate.sh`（66 个程序） | 66/66 通过，没有功能模型不一致 |
| 周期与新 trace-model 逐个相等 | 修复 store 窗口后 66/66 相等（修复前 62/66，见下） |
| 不相等的 4 个 | dcache-conflict-writeback 4,271（tm 4,293）、matmul_fpu 43,242（43,256）、memory-stress-small 343,543（343,975）、pascal 1,785（1,747） |
| `DS3=0`（固定延迟）、同样不分频 | RTL 与 trace-model 在 add、dummy、fib、crc32 上逐个相等；同样那 4 个程序也不相等（pascal 1,823 对 1,748 等），所以差异**与 DRAMsim3 无关**，来自不分频本身 |

RTL 仿真速度（同一台机器、单次运行、未做负载控制）：不分频后 dhrystone 36.0 s → 4.4 s、coremark 50.9 s → 6.9 s，约快 8 倍（周期数不同，折算每秒仿真周期约 4.2 千 → 36 千，也是约 8.6 倍）。原因是每个 CPU 周期只需 1 个 tick，不再是 16 个，也不再需要空闲 tick 跳过。旧数字用 `rtl/build/soc_fm_b3`（16 tick，固定延迟 SimDDR），新数字用 DRAMsim3 版本。

**原因已查清并修复**：RTL 的 LSU 把所有队列扫描窗口都写成 `WIN = LSU_LOAD_WINDOW_WIDTH`（注释写"== `LSU_STORE_WINDOW_WIDTH`"），第 3 批把端口改成 LD 4 / STA 3 之后，load 窗口是 4×5 = 20，store 窗口是 3×5 = 15，两者不再相等；trace-model 的 store 提交窗口 `comb_lsu2dcache_stq` 用 `LSU_STORE_WINDOW_WIDTH`（15），RTL 的 `lsu_dc_req_st` 却看 20 个。链头的 store 因 DCache 重放卡住时，RTL 会提前发出窗口 15 之外的 store（pascal 在 cycle 1031 发出 `0x80000178`，trace-model 到 1038 才发）。16 倍分频时 store 响应在额外 tick 里很快回来，链头不会卡住，所以这个差别一直没有被周期对比抓到。定位办法：逐周期打印 LSU 到 DCache 的 load/store 端口请求与响应、`mshr_fill`，两边第一个不同的输入就是这个 store 请求，再对照 `RealLsu.cpp` 的窗口。

修复：`lsu_pkg.sv` 新增 `STWIN = LSU_STORE_WINDOW_WIDTH`，`lsu_dc_req_st.sv` 的窗口成员改为 `stq_ccount > q && q < STWIN`。修复后固定延迟（`DS3=0`）下 4 个程序全部与 trace-model 相等（pascal 1,748、matmul_fpu 43,272、memory-stress-small 342,754、dcache-conflict-writeback 4,454），DRAMsim3 下 `fm_gate.sh` 66/66 通过，**66 个程序周期与新 trace-model 全部相等**；`lint.sh` 和 `lint_chip.sh` 通过。

仍有隐患：RTL 的其他 store 队列窗口（`wait_mmu_stq`、`mmu_done_stq` 等，经 `lsu_pkg.sv` 里的通用 `ring_apply` 用 `WIN`）同样按 20 处理，trace-model 用 15；这 66 个程序没有触发，修它需要给 ring 操作带上窗口参数，尚未做，已记入风险。（后来在 rtl 分支 `exp/lsu-stwin`（`b94b4f5`）里修了全部 store 侧队列窗口，包含这两个 ring，尚未合入；本分支的 `0fce9a6` 只修了提交窗口，是它的子集。）

RTL 仿真提速试验（同日，dhrystone 158,756 周期，墙钟秒；机器上同时跑着另一个 4 线程的 Linux 启动，数字有噪声，每项重复 2–3 次）：

| 变化 | 墙钟 | 说明 |
|---|---|---|
| 基线（`--threads 4`，`-O2`） | 4.5–4.7 | |
| `mem_top` 在 `TICKS==1` 时把 `phase0`/`phase_last` 做成编译期常量 | 4.4–4.5 | 约 2–3%，周期不变；`fm_gate` 66/66、周期全部相等 |
| 再加 `-O3 -march=native`（`SOC_COPT`） | 4.2–4.3 | 再约 4–5% |
| `--threads 1 / 2 / 4 / 6 / 8` | 10.5 / 6.4 / 4.5 / 5.0 / 7.4 | 4 线程最好，线程更多反而慢（本机 14 核，被另一个进程占去 4 个） |

结论：模型很大，多线程收益显著（1 → 4 线程快 2.3 倍），但 4 线程已是拐点；剩下的收益要靠减少每周期的 `eval()` 次数、DRAMsim3 空闲快进和缩小设计状态，本次未做。`phase0` 常量化已保留在 `mem_top.sv`；`-O3` 未改默认值，用 `SOC_COPT="-O3 -march=native"` 打开。

Linux 启动（RTL，不分频 + DRAMsim3 + 1 GHz，`SOC_TB_FM=1 SOC_TB_SEMIHOST=1`，镜像 `AI-Huma-data/linux/linux.bin`）：

- 第一次在内核初始化末尾被 `axi_llc_rq.sv:95` 的断言（读响应队列满）中止。该队列深度 `RQD=4` 是按 16 tick 下"程序最多 1、随机测试最多 3"定的；不分频后互联每个核心周期只排空一次，Linux 的 DCache 重填并发更高，于是溢出。trace-model 的对应队列是 32 项，且没有溢出断言，所以没有报错；不分频的 trace-model 没有跑过 Linux，实际最大占用未知。
- 先把 `RQD` 改为 32（与 trace-model 一致）后重跑：启动到 `rv32 login:`，日志（`rtl_dram_boot2.log`）没有断言、没有功能模型不一致行；到登录后手动结束进程，因此没有 `[FM] N instructions checked` 汇总行，也没有总周期数。
- 在不分频 trace-model（DRAMsim3、1 GHz）上加临时占用探针跑 Linux 启动到 `rv32 login:`：master 0 排队峰值 1、master 1（DCache MSHR）排队峰值 4，加输出寄存器后的总占用分别为 2 和 5；dhrystone、coremark、memory-stress、memory-stress-small 的队列都没被用到。RTL 的断言是 `总占用 ≤ RQD`，原 `RQD=4` 正好在总占用到 5 时溢出，与实测吻合。**决定 `RQD = 8`**（最小可用 5，留 3 的余量，比 32 省约四分之三的队列存储）。RTL 一侧的同样探针测量被我中途结束，没有出结果。
- 遗留：`RQD=8` 只按 Linux 启动一个大负载定；SPEC 等其他大负载未测。其他按 16 tick 下的小程序测出来的小深度队列可能同样不够，尚未逐个检查。

SPEC CPU2006 整数 checkpoint 回放（trace-model，新基线：不分频、DRAMsim3 DDR4-3200、1 GHz；`scripts/spec/replay.sh full`，12 个程序、580 个 SimPoint、每点预热后测 1000 万条指令，8 路并行，用时约 1 小时 45 分，结果在 `AI-Huma-data/spec-rv32imab/tm/res_dram`）：

| 程序 | 点数 | 加权 IPC |
|---|---|---|
| 400.perlbench | 44 | 2.131 |
| 401.bzip2 | 76 | 1.645 |
| 403.gcc | 55 | 1.590 |
| 429.mcf | 79 | 0.463 |
| 445.gobmk | 50 | 1.783 |
| 456.hmmer | 34 | 3.718 |
| 458.sjeng | 28 | 1.858 |
| 462.libquantum | 51 | 0.857 |
| 464.h264ref | 37 | 1.489 |
| 471.omnetpp | 40 | 1.508 |
| 473.astar | 35 | 0.975 |
| 483.xalancbmk | 51 | 1.959 |
| **几何平均** | 580 | **1.487** |

580 个点全部完成，没有失败，没有 difftest 不一致（mismatch-points 全为 0）。

与旧基线（`tm/b3`，第 3 批配置、16 倍分频、固定 60 tick 延迟；只有 quick 的 6 个程序、覆盖 90% 权重的点，所以用同一批点比较；该目录的配置我没有逐项核对，按目录名和日期判断）：

| 程序 | 旧 IPC | 新 IPC | 变化 |
|---|---|---|---|
| 400.perlbench | 2.468 | 2.135 | −13.5% |
| 403.gcc | 2.566 | 1.631 | −36.4% |
| 429.mcf | 1.327 | 0.480 | −63.8% |
| 456.hmmer | 4.007 | 3.767 | −6.0% |
| 458.sjeng | 2.027 | 1.853 | −8.6% |
| 464.h264ref | 1.677 | 1.511 | −9.9% |
| **几何平均** | 2.204 | 1.613 | **−26.8%** |

结论：去掉 16 倍分频、换成 DRAMsim3 之后，访存密集的程序掉得最多（mcf −64%、gcc −36%），计算密集的掉得少（hmmer −6%），符合"分频让 DRAM 相对核心快了约 13 倍"的判断。旧数字是偏乐观的，新数字才反映 1 GHz 核心配 DDR4 的情况。附加延迟 32 ns 仍未校准，绝对值会随它变。

DRAMsim3 依赖（同日）：改为 trace-model 仓库的固定版本子模块 `third_party/DRAMsim3`（`2981759`）；Makefile 把它的 12 个源文件直接编成 `build_dramsim3/libdramsim3.a`（`gmake dramsim3`，不用 cmake、不用动态库、不设 rpath、不往子模块里写文件），RTL 的 `tb/soc/build.sh` 链接同一个静态库（`TM_DIR` 指定 trace-model 目录）。克隆后要 `git submodule update --init third_party/DRAMsim3`。验证：全新 `BUILD_DIR` 构建后 gate 62/62、dhrystone 158,756、coremark 250,658（与动态库版相同）；`DS3=0` 仍可不带 DRAMsim3 构建；RTL `fm_gate.sh` 66/66、66 个周期与 trace-model 全部相等。

### 基线重做：非核心延迟 60 ns（2026-11-06）

原因：32 ns 只取了 SOC+CDC，理由是控制器和 PHY 已被 DRAMsim3 覆盖；这个假设不成立（DRAMsim3 只建模命令调度和 DRAM 时序，不含控制器流水线和 PHY）。`config.h` 里本来的非核心路径是 SOC 20 + CDC 12 + CTL 15 + PHY 13 = 60 ns，设计读延迟 `CONFIG_SIM_DDR_LATENCY_CALC` = 86 ns。改成 60 ns 后 dhrystone/coremark 的平均读延迟约 85–87 ns，与 86 ns 吻合（32 ns 时 56–58 ns，memory-stress-small 81 ns → 105 ns）。`DS3_EXTRA_NS` 仍可覆盖。

DDR 配置：DRAMsim3 `DDR4_8Gb_x16_3200`（tCK 0.63 ns，CL/tRCD/tRP 22，1 通道、64 位、2 bank group × 4 bank、BL8、open page、地址映射 `rochrababgco`、rank 级交错刷新），与 `config.h` 里原来的 CL 22 / tRCD 22 / tRP 22 / 1600 MHz 一致。

| 程序 | 32 ns | 60 ns |
|---|---|---|
| dhrystone | 158,756 | 162,033 |
| coremark | 250,658 | 255,335 |
| memory-stress | 2,425,029 | 2,428,470 |
| smc-div | 11,096 | 11,348 |
| smc-addi | 10,966 | 11,218 |
| memory-stress-small | 343,975 | 347,305 |

`baseline.csv` 63 个程序：周期平均 +23%、中位 +28%、最大 +36%；gate 62/62。RTL：`ref_cycles.txt` 重新生成，`fm_gate.sh` 66/66、66 个周期与 trace-model 全部相等；Linux 从复位启动到 `rv32 login:`（`RQD=8`，无断言、无不一致）。trace-model 上 LLC 读响应队列峰值：master 1 排队 3 + 输出寄存器（32 ns 时 4 + 1），`RQD=8` 仍够用，延迟变高反而排队更少。

SPEC 全量回放（580 点，无失败，无 difftest 不一致；`tm/res_dram60`，12 路并行）：

| 程序 | 加权 IPC | 估算分数@1GHz | 32 ns 的 IPC |
|---|---|---|---|
| 400.perlbench | 2.092 | 8.08 | 2.131 |
| 401.bzip2 | 1.600 | 7.13 | 1.645 |
| 403.gcc | 1.474 | 9.32 | 1.590 |
| 429.mcf | 0.405 | 12.62 | 0.463 |
| 445.gobmk | 1.763 | 8.85 | 1.783 |
| 456.hmmer | 3.720 | 9.75 | 3.718 |
| 458.sjeng | 1.834 | 8.44 | 1.858 |
| 462.libquantum | 0.663 | 4.73 | 0.857 |
| 464.h264ref | 1.475 | 6.08 | 1.489 |
| 471.omnetpp | 1.333 | 6.92 | 1.508 |
| 473.astar | 0.928 | 7.00 | 0.975 |
| 483.xalancbmk | 1.873 | 12.04 | 1.959 |
| **几何平均** | **1.396** | **8.12** | 1.487（分数 8.66） |

quick 的 6 个程序（旧基线 `tm/b3` 同一批点）：几何平均 IPC 旧（16 倍分频）2.204 → 32 ns 1.613 → 60 ns 1.550。分数的换算方法和局限见上面"估算分数"一段（参考时间是凭记忆写的，未核对官方表）。

综合前后对比（2026-11-06，Yosys + yosys-slang 的相对面积代理，`scripts/synth_module.sh`，`SYNTH_LIGHT=1 SYNTH_MEM=1`；改动前 = `main`/`exp/batch3` 的 rtl，改动后 = `exp/dram-sim`；**不是工艺库面积、没有时序**）：

| 模块 | 改动前 | 改动后 | 变化 | 原因 |
|---|---|---|---|---|
| `axi_llc_rq`（每个读主设备一份） | 10,439 单元 / 2,584 触发器 | 18,768 / 4,649 | +8,329 / +2,065（+80%） | `RQD` 4 → 8 |
| `axi_llc`（整个 LLC，`NR=4` 个读主设备） | 489,436 / 22,324 | 522,758 / 30,584 | **+33,322 / +8,260（+6.8% / +37%）** | 4 × `axi_llc_rq` 的增量，吻合 |
| `lsu_dc_req_st` | 86,150 / 0 | 62,755 / 0 | **−23,395（−27%）** | store 窗口 20 → 15 |
| `dcache_resp`、`axi_cpu_port_chan` | 14,113 / 38；59 / 24 | 相同 | 0 | 单独综合时 `phase0`、`phase_last` 是悬空输入，看不出常量化的效果 |

净变化约 +9.9k 单元（+33.3k − 23.4k），相对整机推算的约 952 万个门不到 0.2%；触发器 +8,260，相对整机约 18.1 万是 +4.6%，全部来自 `RQD`。`mem_top` 的 `TICKS == 1` 常量化（去掉 16 tick 折叠逻辑）预计是减量，但 `mem_top` 太大，Yosys 超时，没有测到。每增加一项 `RQD`，4 个队列合计约 +8.3k 单元（`RQD=5` 即最小可用值约 +8.3k，`RQD=6` 约 +16.7k，`RQD=8` 为 +33.3k）。

### 后续

- **已决定（2026-11-05）：不分频 + DRAMsim3 + 默认 1 GHz 作为新基线**（trace-model 侧已完成：`config.h` 默认 `FREQ_DIV=1`、`CPU_FREQ_MHZ=1000`，Makefile 默认 `DS3=1`，`baseline.csv` 已重生成，gate 62/62，大程序标准周期见 trace-model `docs/PROJECT.md`）。新旧基线周期对比：gate 平均 +146%、中位 +135%，dhrystone 150,427 → 158,756，coremark 233,515 → 250,658，memory-stress 1,541,195 → 2,425,029，memory-stress-small 189,128 → 343,975。RTL 侧已同步（见下一节），66 个程序周期与 trace-model 全部相等。
- 开启 difftest 逐条比较重跑 gate；用 Linux 启动片段、SPEC 检查点（不要用 cjpeg/linear_alg/parser/sha）测带宽和 bank 冲突敏感的负载。
- 校准附加延迟，或与 RTL 闭环里的 SimDDR 对齐；试 DRAMsim3 的地址映射和 open/close page。
- RTL 其他 store 队列窗口（`wait_mmu_stq`、`mmu_done_stq`）与 trace-model 的 15 不一致，需给 `ring_apply` 带窗口参数。
- RTL 侧合入 `main` 前还要跑 Linux 启动（`SOC_FM=1 SOC_TB_SEMIHOST=1`，数小时）和综合对比。
- Ramulator 2.0 作为后备，未试。

## EXP-005 opt1 的 SPEC 对比与不改结构的参数同步到 RTL

- **日期**：2026-11-05
- **分支**：trace-model `exp/area-explore`（未提交）；rtl `exp/batch1-params`（未提交）；function-model `exp/spec-rv32imab`（SPEC 脚本，未提交）
- **问题**：opt1 在 SPEC 上的性能代价多大？其中零风险的参数部分能否直接同步到 RTL，面积省多少？

### SPEC 检查点重建（rv32imab）

- 原检查点放在 `/tmp` 里，重启后丢失（见 EXP-004）。按原流程重建，改为 rv32imab（GCC 13.3，`-march=rv32ima_zicsr_zifencei_zba_zbb_zbs`），数据放在 `~/personal/AI-Huma-data/spec-rv32imab`。流程、参数、耗时见 `function-model/scripts/spec/README.md`。
- 12 个程序的 BBV 全部跑完、输出与 SPEC 参考一致；检查点共约 60 GB。
- 发现并修正 `pipeline.sh` 的误判：模拟器的 BBV 打印会插进 `RUN ... rc=0` 行中间，perlbench 和 sjeng 因此被判为“退出码非零”。现在先删掉这些插入的打印再校验。
- 因为编译选项（加了 B 扩展、换了 GCC）变了，新的 IPC 不能和旧的 rv32ima 数字（quick 几何平均 2.356）直接比。

### quick SPEC：基线 vs opt1（90% 权重的点，前门恢复，测 1000 万条）

| 程序 | 点数 | 基线 IPC | opt1 | 变化 | opt1 + 统一 FTQ 上限 64 | 第 3 批（RTL 配置） |
|---|---|---|---|---|---|---|
| perlbench | 21 | 2.487 | 2.473 | −0.6% | — | 2.468（−0.8%） |
| gcc | 31 | 2.600 | 2.568 | −1.2% | 2.567 | 2.566（−1.3%） |
| mcf | 53 | 1.333 | 1.328 | −0.4% | 1.328 | 1.327（−0.5%） |
| hmmer | 24 | 4.018 | 4.005 | −0.3% | 4.005 | 4.007（−0.3%） |
| sjeng | 21 | 2.038 | 2.022 | −0.8% | — | 2.027（−0.5%） |
| h264ref | 28 | 1.677 | 1.677 | 0.0% | 1.677 | 1.677（0.0%） |
| 几何平均（4 个：gcc mcf hmmer h264ref） | | 2.198 | 2.187 | −0.5% | 2.187 | 2.187（−0.5%） |
| **几何平均（6 个）** | | **2.216** | **2.204** | **−0.5%** | — | **2.204（−0.5%）** |

- 所有点都跑完，无比对不一致。第 3 批（LD/STA IQ 不合并、各 64）与 opt1 几乎相同，说明 opt1 的 SPEC 损失来自第 1–3 批的参数，不来自 LD/STA 合并。统一 FTQ 的上限近似（`UFTQ_CAP=64`）和 opt1 结果相同。
- gcc 损失最大的三个点原因各不同：在飞分支数顶到 32、STD IQ（16 项）满、STA 端口 3 个占满。只在 gcc 上逐项放宽验证：在飞分支回到 64 不起作用（2.568），STD IQ 32 只回到 2.572。差距不大，按用户决定不再追。

### 第 1 批同步到 RTL：BACKEND_FETCH_WIDTH 8、MAX_BR_NUM 32、ibuf 64

只改参数，RTL 结构不动。参数包由 `make cfg` 从 trace-model `config.h` 生成（这次用 `gen_cfg.sh -DCFG_BACKEND_FETCH_WIDTH=8 -DCFG_MAX_BR_NUM=32 -DCFG_IBUF_SIZE=64`），连带 `BR_MASK_WIDTH` 64→32、`BR_TAG_WIDTH` 6→5、`FTQ_OFFSET_WIDTH` 4→3。

要修的地方（都是字段位宽写死成数字）：
- 生成的 `back_top.sv`、`exu.sv` 以及手写的 `dispatch.sv`、`lsu.sv`、`rob.sv` 端口：`tools/dimmap.py` 加了字段位宽规则（`br_mask`/`clear_mask` 64 → `BR_MASK_WIDTH`，`br_id` 6 → `BR_TAG_WIDTH`，`ftq_offset` 4 → `FTQ_OFFSET_WIDTH`），`gen_backtop.py` 生成时用同一规则。改之前确认了重新生成与仓库里的文件完全一致。
- 测试平台 `tb/soc/soc_tb.cpp` 按写死的位偏移从 LSU 的 `st_fld_q` 取 MMIO store 的地址/数据（88/91/155）。br_mask 变窄后字段前移，外设模型收到错字节：串口输出乱码，`supervisor-external-interrupt-vectored` 等不到中断。function-model 逐条对比不比较 store 数据，所以没报错。现在 `gen_soc_probe.py` 从参数包读出位宽，偏移按结构体布局计算。

验证：
- 新旧两套参数下，整芯片 Verilator `-Wall` 0 条警告，`lint.sh` 通过。
- 整核测试平台 + function-model 逐条对比，66 个程序（gate、vm、dhrystone、coremark）两种参数都全部通过，串口输出逐字节一致。
- 周期数：66 个里 3 个变化，与同参数的 trace-model 完全一致。

| 程序 | 基线 | 第 1 批（RTL = trace-model） |
|---|---|---|
| coremark | 226,991 | 232,353（+2.36%，来自在飞分支 32） |
| dhrystone | 150,838 | 150,582 |
| prime | 11,760 | 11,591 |

综合（`synth_module.sh`，`SYNTH_LIGHT=1 SYNTH_MEM=1`，与 `rtl/docs/09-synthesis-report.md` 同流程；基线数字与报告一致）：

| 模块 | 基线单元数 | 第 1 批 | 变化 | 触发器 基线→第 1 批 |
|---|---|---|---|---|
| isu | 2,119,233 | 1,727,421 | −18% | 73,204 → 60,052 |
| ren | 345,198 | 206,193 | −40% | 18,203 → 10,315 |
| pre_idu_queue | 188,943 | 50,225 | −73% | 36 → 33 |
| idu | 97,352 | 30,640 | −69% | 4,213 → 1,108 |
| dispatch | 104,827 | 86,586 | −17% | 1,896 → 1,624 |
| exu_ctrl | 22,016 | 14,129 | −36% | 5,486 → 4,586 |
| prf | 376,833 | 372,609 | −1% | 2,310 → 1,606 |
| rob | 235,182 | 234,791 | 0% | 17,802 → 17,674 |
| 合计 | | | 约 −77 万（整机约 952 万的 8%） | 约 −2.4 万 |

- 单元数不含存储阵列（保留为 `$mem`）。存储按位宽手算：FTQ 每项 1824→912 位，64 项省约 5.8 万位；ibuf 128×44 → 64×43，省约 2.8 千位。
- `lsu_ring`、`lsu_stlf`、`idu_br_cp` 不变。

### 第 2、3 批同步到 RTL：IQ 大小、front2back 深度、端口数

- **第 2 批**（在第 1 批之上）：INT IQ 64、BR IQ 32、STD IQ 16、front2back FIFO 8。LD/STA IQ 仍分开各 64（合并要改结构，不在这一批）。
- **第 3 批**（在第 2 批之上）：端口 LD/STA/STD/BRU 4/3/3/2。`ISSUE_WIDTH` 22→18、FU 总数 28→24、AGU 8→7、DCache miss 数 8→7、store 窗口 20→15 等随之变化。

要改的地方：
- trace-model `config.h` 新增标量 `IQ_INT_SIZE`、`IQ_LD_SIZE` 等（生成器只导出标量常量）；`gen_cfg_pkg.py` 同时读取 `frontend_feature_config.h` 的 FIFO 深度。`isu_pkg::iq_size()`（原来写死 128/64）和 `front_pkg` 的 FIFO 深度改为读参数包。
- `dimmap.py` 新增规则：`ready_num` 8 位 → `IQ_READY_NUM_WIDTH`，`ftq_prf_pc_req/resp` 10 → `FTQ_PRF_PC_PORT_NUM`。
- `lsu.sv`：20 个通道向量宽度、18 个循环上界写死为 4，改为按通道类型用 `LSU_LDU_COUNT`/`LSU_STA_COUNT`/`LSU_SDU_COUNT`/`LSU_LOAD_WB_WIDTH`。
- **潜在 bug**：`lsu_core.sv` 的 store MMU 请求端口（`mmu_st_req_*`）按 load 端口数 `NLD` 声明，应为 `NST`。两者原来都是 4，所以一直没暴露。
- `exu_ctrl_pkg::xc_fu_kind()` 中 LD/STA/STD 的 FU 编号区段写死，改为按端口基址推出；`isu.sv` 的配置自检从“发射宽度必须是 22”改为“ALU 组在端口 0–5”。

验证（三批都做了）：
- 基线、第 1、2、3 批四套参数：整芯片 Verilator `-Wall` 0 警告，`lint.sh` 通过。
- 整核测试平台 + function-model 逐条对比：四套参数各 66/66 通过。改完 RTL 后用基线参数重跑，66 个程序的周期与改前逐个相同，串口输出逐字节一致。
- 各批周期有变化的程序（第 1 批 3 个、第 2 批 9 个、第 3 批 26 个），RTL 与同参数的 trace-model 逐周期一致。`timer-mmio` 打印计时器读数，周期变了读数就变，属于正常差异。

| 5 个小程序（RTL 周期） | 基线 | 第 1 批 | 第 2 批 | 第 3 批 |
|---|---|---|---|---|
| dhrystone | 150,838 | −0.17% | −0.42% | −0.27% |
| coremark | 226,991 | +2.36% | +3.00% | +2.87% |
| memory-stress-small | 189,128 | 0 | 0 | 0 |
| matmul_fpu | 42,253 | 0 | +0.16% | +0.28% |
| prime | 11,760 | −1.44% | −2.64% | −1.89% |
| 几何平均 | | +0.14% | 0.00% | +0.19% |

综合（同一流程，三套参数各综合一遍；`lsu`、`dcache` 等综合不出来的聚合模块没有算，所以是下限）：

| 模块 | 基线 | 第 2 批 | 第 3 批 |
|---|---|---|---|
| isu | 2,119,233 | 1,072,997 | 1,029,239 |
| prf | 376,833 | 372,609 | 282,121 |
| ren | 345,198 | 206,193 | 206,193 |
| rob | 235,182 | 234,791 | 201,297 |
| pre_idu_queue | 188,943 | 50,225 | 49,764 |
| exu（含 exu_ctrl 和各 FU） | 107,137 | 97,364 | 91,509 |
| dispatch | 104,827 | 86,598 | 86,598 |
| idu | 97,352 | 30,640 | 30,640 |
| lsu_dc_req_st | 87,426 | 87,426 | 86,150 |
| tlb_mmu | 60,793 | 60,793 | 53,454 |
| 合计（上述 11 个，含 front2back） | 3,723,024 | 2,299,695 | 2,117,024 |
| 触发器（同上范围） | 123,595 | 74,883 | 73,873 |

- 第 3 批相比基线：约 −161 万门（整机约 952 万的 17%），约 −5 万触发器（整机约 18.1 万的 27%）。isu 减半，来自 IQ 总项数 384→240 和 br_mask 64→32。
- 存储阵列另算：FTQ 约 −5.8 万位，ibuf 约 −2.8 千位，front2back 32→8 项约 −2.3 万位。
- 端口减少还会缩小 DCache 写口、LSU 的 STA 通路，这部分在 `lsu`/`dcache` 聚合模块里，没有数字。

### 后续

- 第 1–3 批要合入 main，需要先把 trace-model 的 `CFG_*` 开关合入并改默认值（RTL 参数包从 main 的 `config.h` 生成），并按规则记录性能和综合结果。
- LD/STA IQ 真合并、PTAB/front2back/FTQ 真统一：在 trace-model 里按真实硬件结构实现，再给 RTL 方案（进行中）。

---

## EXP-004 组合优化配置 opt1

- **日期**：2026-11-04
- **分支**：trace-model `exp/area-explore`，改动**未提交**
- **问题**：在飞分支缩到 32、INT IQ 用 64，再叠加前面所有优化，整体性能怎样？
- **配置 opt1**（构建命令在 `scripts/area/build_variants2.sh` 末尾）：

| 项 | 原设计 | opt1 |
|---|---|---|
| `BACKEND_FETCH_WIDTH` | 16 | 8 |
| MAX_BR_NUM（在飞分支） | 64 | 32 |
| INT IQ | 128 | 64 |
| BR IQ | 64 | 32（在飞分支只有 32 个，BR IQ 再大也用不上） |
| LD / STA IQ | 64 / 64 | 合并为 64 |
| STD IQ | 64 | 16 |
| ibuf | 128 | 64 |
| front2back FIFO | 32 | 8 |
| 端口 LD/STA/STD/BRU | 4/4/4/4 | 4/3/3/2 |
| 统一 FTQ（`UFTQ_CAP`，近似） | — | 分别测了不开和开 64 两种 |

- IQ 总项数 384 → 176（64+64+16+32）；重命名检查点 64 份 → 32 份；br_mask 64 位 → 32 位（IQ、LDQ、STQ 每项都省 32 位）。

### 结果

**正确性**：gate 的 62 个程序全部跑完，逐条提交 difftest 无不一致。周期数和基线不同是预期的，因为配置变了。

| 配置 | dhrystone | coremark | memory-stress-small | matmul_fpu | prime | 几何平均 |
|---|---|---|---|---|---|---|
| lean2（EXP-002，MAX_BR 64、INT 48、BR IQ 64） | −0.23% | −1.16% | 0 | +0.28% | −2.76% | −0.78% |
| opt1 | −0.23% | +2.74% | 0 | +0.28% | −1.89% | +0.17% |
| opt1 + 统一 FTQ 64 | −0.23% | +1.79% | 0 | +0.28% | −1.89% | −0.02% |

- coremark 的损失来自在飞分支 32 和 BR IQ 32，和 EXP-002 的单项结果一致（单项各约 +2.4%）。其余负载不受影响。
- 小程序几何平均基本持平。在飞分支 32 的代价集中在分支密集、长依赖的程序上，需要用 SPEC 确认。

### quick SPEC 没有跑：检查点丢失

- `scripts/spec/replay.sh quick` 需要 `/tmp/specref/ckpt/<bench>/*.gz` 和 `sp/<bench>.weights`，`function-model/mem/*.bin` 的 SPEC 镜像也不在了。
- 原因：机器在 2026-11-04 15:30 重启过，macOS 重启时会清空 `/tmp`。这些检查点是生成的数据，不在任何仓库里。
- `/tmp` 里还留着重启之后生成的东西：Linux 特殊检查点 `/tmp/ckpt`（595 MB）、`/tmp/linux_check.bin`、模块级综合结果 `/tmp/synth_results.txt`。下次重启也会丢，应该挪到持久目录。
- **教训**：生成的检查点、镜像、综合结果不能只放在 `/tmp`，要放到持久目录，并在文档里写明位置和生成命令。

### 后续

- 重新生成 SPEC 检查点后，跑 quick SPEC：基线、opt1、opt1 + 统一 FTQ 64，另加 opt1 配 MAX_BR 64 作对照。

---

## EXP-003 ROB 与 PRF 扩大到 256

- **日期**：2026-11-04
- **分支**：trace-model `exp/area-explore`，改动**未提交**
- **问题**：EXP-002 看到 ROB（128 项 = 16 行×8）经常是满的。扩大 ROB 能换来多少性能？
- **开关**：`CFG_ROB_NUM`（默认 128）、`CFG_PRF_NUM`（默认 128），写在 `include/config.h`；构建命令在 `scripts/area/build_variants2.sh` 末尾。
- **负载和方法**：同 EXP-001。所有变体都开着逐条提交 difftest 跑完，ROB 192（12 行）也能正常运行。

| 配置 | dhrystone | coremark | memory-stress-small | matmul_fpu | prime | 几何平均 |
|---|---|---|---|---|---|---|
| ROB 256、PRF 128 | +0.64% | −1.89% | +0.97% | +0.18% | +0.16% | +0.01% |
| ROB 128、PRF 256 | +0.01% | −0.78% | −0.00% | +1.28% | 0 | +0.10% |
| ROB 192、PRF 192 | −0.01% | −0.44% | −0.00% | −0.04% | −1.49% | −0.40% |
| ROB 256、PRF 256 | −0.73% | −3.07% | −0.00% | +1.11% | −1.36% | −0.82% |
| ROB 256、PRF 256 + lean2（EXP-002） | −1.38% | −1.56% | −0.00% | +1.03% | −3.04% | −1.00% |

### 结论

- 只加 ROB 不加 PRF 没有用：可重命名的寄存器只有 96 个，ROB 填不满。
- ROB 和 PRF 都翻倍，几何平均只快约 0.8%，coremark 快 3%，matmul_fpu 反而慢 1%。ROB 256 时占用 p99 仍是满的（32 行），说明这些程序是依赖链和延迟受限，窗口再大也帮不上多少。
- **ROB 128 是合理的**：EXP-002 里"ROB 经常满"只说明它是后端最先满的结构，不代表扩大它收益很大。
- lean2 加上 ROB/PRF 256，比基线快 1%，但 ROB 和 PRF 都翻倍的面积代价远大于这点收益，不建议。
- 局限：负载很小；大负载（工作集更大、访存延迟更长）下窗口的收益可能更高，需要复核。

---

## EXP-002 全核面积浪费排查

- **日期**：2026-11-04
- **分支**：trace-model `exp/area-explore`，在 EXP-001 的基础上继续，改动**未提交**
- **问题**：除 EXP-001 的三个方向外，设计里还有哪些结构明显过大、存在面积浪费？

### 方法

在 EXP-001 的插桩和开关上新增以下内容，默认值都和原设计一致：

| 开关 / 统计 | 默认 | 作用 |
|---|---|---|
| `CFG_INT_IQ_SIZE` / `CFG_BR_IQ_SIZE` | 128 / 64 | INT、BR 两个 IQ 的容量 |
| `CFG_IBUF_SIZE` | 128 | pre-IDU 指令缓冲（`IDU_INST_BUFFER_SIZE`） |
| `FRONT2BACK_FIFO_SIZE`（已有宏） | 32 | front2back FIFO 深度 |
| `CFG_MAX_BR_NUM` | 64 | 在飞分支数上限，决定重命名检查点份数和 br_mask 位宽 |
| `CFG_PLAIN_ALU_PORTS` | 2 | 只做 ALU 的端口数（前 4 个兼做 MUL/DIV/FP/CSR 的端口不变） |
| `CFG_BR_PORTS` | 4 | 分支执行端口数 |
| `[AS] br_inflt` / `rob_lines` | — | 在飞分支数（`now_br_mask` 置位数）、ROB 占用的行数（每行 8 项，共 16 行） |

- 新增改动：`back-end/Idu.cpp`、`back-end/Rob.cpp`（统计）、`include/config.h`（开关）、`scripts/area/build_variants2.sh`。
- **默认配置验证**：gate 62/62，周期与基线一致。
- **负载、运行上限、复现方式**：同 EXP-001（`run_set.sh`、`summarize.sh`）。
- **位宽来源**：IQ 项按 RTL `isu_pkg.sv` 的 uop 结构手算，约 189b/项；BPU 按 `bpu_pkg.sv`、`bpu_btb_pkg.sv`、`bpu_*bank.sv` 手算。

### 模型近似和局限

- 负载和 EXP-001 一样小。coremark 对时序变化敏感，单项结果有约 ±1% 的噪声（例如 INT IQ 64 比 48 还慢 1.2%）；prime 只有 1.2 万拍，噪声更大。
- 分支预测器容量问题，小程序**完全测不出来**（代码体量太小），这里只做存储量统计，不下性能结论。
- 端口减少带来的频率、布线收益没有建模。

### 基线观察（`ARCH_STATS=1`）

| 结构 | 容量 | dhrystone 占用 p99 | coremark 占用 p99 | 说明 |
|---|---|---|---|---|
| ROB（行） | 16 | 16（p50=15） | 16 | **经常满，是真正的瓶颈** |
| INT IQ | 128 | 27 | 57 | 与 ROB(128) 一样大 |
| LD IQ / STA IQ | 64 / 64 | 12 / 11 | 61 / 17 | 分别受 LDQ、STQ 限制 |
| STD IQ | 64 | 34 | 16 | |
| BR IQ | 64 | 12 | 41 | |
| 在飞分支 | 64 | 13 | 48（最大 51） | |
| ibuf | 128 | 128 | 128 | 反压时被填满 |
| front2back | 32 | 32 | 32 | 反压时被填满 |

- 基线下分派从未因 IQ 满而阻塞。前端 FIFO 和 ibuf 被填满，是 ROB 满之后层层反压的结果，并不是需要这么深。
- 前端到译码之间能缓存约 512 条指令（指令 FIFO 16 组 + front2back 32 组 + ibuf 128 条），是 ROB 容量的 4 倍。
- IQ 总项数 384，是 ROB 的 3 倍。

### 结果：单项扫描（周期变化，相对基线）

| 变体 | dhrystone | coremark | memory-stress-small | matmul_fpu | 几何平均 | 判断 |
|---|---|---|---|---|---|---|
| INT IQ 64 | +0.00% | +1.20% | 0 | 0 | +0.24% | 噪声 |
| INT IQ 48 | +0.00% | −0.20% | 0 | 0 | −0.04% | **可缩** |
| INT IQ 32 | −0.05% | +1.66% | 0 | +0.04% | +0.38% | 边缘 |
| BR IQ 32 | 0 | +2.43% | 0 | 0 | +0.16% | 不缩 |
| BR IQ 16 | 0 | +4.71% | 0 | 0 | +0.82% | 不缩 |
| STD IQ 32 | −0.37% | 0 | 0 | 0 | −0.07% | 可缩 |
| STD IQ 16 | −0.41% | −0.55% | 0 | +0.02% | −0.19% | **可缩** |
| ibuf 64 | −0.17% | −0.21% | 0 | 0 | −0.93% | **可缩** |
| ibuf 32 | +0.13% | +1.65% | 0 | 0 | +0.23% | 边缘 |
| front2back 16 | 0 | 0 | 0 | 0 | −0.46% | 可缩 |
| front2back 8 | 0 | 0 | 0 | 0 | −0.55% | **可缩** |
| MAX_BR_NUM 32 | 0 | +2.36% | 0 | 0 | +0.08% | 不缩 |
| MAX_BR_NUM 16 | 0 | +6.15% | 0 | 0 | +1.24% | 不缩 |
| 纯 ALU 端口 2→1 | +0.06% | +1.11% | +0.59% | +0.01% | +0.09% | 边缘 |
| 纯 ALU 端口 2→0 | −0.06% | −0.46% | +8.04% | −0.12% | +1.67% | 不缩 |
| BRU 4→3 | 0 | +0.28% | 0 | 0 | +0.06% | 可缩 |
| BRU 4→2 | −0.13% | −0.34% | 0 | 0 | −0.48% | **可缩** |
| BRU 4→1 | +1.75% | +8.79% | 0 | −0.08% | +1.58% | 不缩 |

### 结果：组合配置

| 配置 | 内容 | dhrystone | coremark | memory-stress-small | matmul_fpu | 几何平均 |
|---|---|---|---|---|---|---|
| lean | INT48、BR IQ 32、STD32、LD+STA 合并 64、ibuf 64、front2back 16、MAX_BR 32、端口 4/3/3 | −0.29% | +2.12% | 0 | +0.11% | +0.20% |
| **lean2** | INT48、BR IQ 64、STD16、LD+STA 合并 64、ibuf 64、front2back 8、MAX_BR 64、BRU 2、端口 4/3/3 | −0.23% | −1.16% | 0 | +0.28% | −0.78% |
| lean2 + 统一 FTQ 64 | 同上，加 `UFTQ_CAP=64` | −0.23% | −1.16% | 0 | +0.28% | −0.78% |

lean 的 coremark 损失来自 BR IQ 32 和 MAX_BR 32；lean2 保留两者为 64 后，与基线持平。

**lean2 节省（只算存储，手算）**：
- IQ 384→192 项（48+64+16+64；2026-11-05 更正，原写 176 是 opt1 的数）：约 36 Kb；唤醒比较器按 项数×2 源×15 个唤醒口 算，从 11,520 个降到 5,760 个。
- ibuf 64 项：约 2.8 Kb。
- front2back 24 项：约 23 Kb（若同时做 EXP-001 的 FTQ 合并，按 278b/项算约 6.7 Kb）。
- 端口：BRU 2 个，含配套的 FTQ PC 读口和 PRF 读口；STA、STD 各 1 个。
- 再加上 EXP-001 的 FTQ 改造（约 105 Kb）。

### 没有用 trace model 验证、但值得排查的设计问题

1. **每个 IQ 项都存完整 uop（约 189b）**：imm 32b、csr_idx 12b、func7、ftq_idx/offset、ldq_idx 等。STD IQ 实际只需要 src preg、stq_idx、rob_idx 和 br_mask。按 IQ 专门化字段，还能再省不少。
2. **br_mask 64 位**：每个 IQ 项、LDQ/STQ 项都带，约占 IQ 项的三分之一。性能上 MAX_BR 需要保持 64，可以考虑 ROB 区间等其他编码方式。
3. **BPU 存储约 1.1 Mb，比 L1D 数据阵列（64KB = 524 Kb）还大**：
   - TAGE：8 bank ×（1024×2b 基表 + 4×1024×13b）≈ 442 Kb
   - BTB：8×4 路×256×44b ≈ 360 Kb
   - TC：8×2 路×128×46b，加上同样大小的 pre 表 ≈ 188 Kb
   - 类型预测器：2 路×4096×14b ≈ 115 Kb
   - 类型预测器带 **16 个读口、8 个写口**，多端口阵列代价远大于存储本身。预测侧 8 个读口 + 提交侧 8 个读口，可以考虑提交侧改成从 FTQ 带回的信息更新，或只在分支上更新。
   - 容量是否合理需要用 Linux、SPEC 等大负载评估。
4. **ROB 经常满**：它是后端最先满的结构。EXP-003 实测把 ROB 和 PRF 都翻倍到 256 只快约 0.8%，所以 ROB 128 是合理的，不值得把面积挪过去。
5. **BPU 更新队列（`Q_DEPTH=2`，每 bank 一个，约 16×142b ≈ 2.3 Kb）**：它是 BPU 里另一个 FIFO，训练数据来自 FTQ。可以和 FTQ 合并成"提交时直接从 FTQ 读训练信息"，但体量很小，收益有限。

### 后续

- 在大负载上复核 lean2，并评估 BPU 容量（TAGE/BTB 每 bank 项数、类型预测器端口）。
- IQ 项按队列类型专门化字段，用 RTL 估算位宽。
- 实验：lean2 省下的面积挪给 ROB（160/192）。

---

## EXP-001 面积优化三个方向

- **日期**：2026-11-04
- **分支**：trace-model `exp/area-explore`（从 `main` `41a5cdd` 切出；改动**未提交**）
- **问题**：
  1. BPU 侧的预测 FIFO（PTAB）能否与 pre-IDU 的 FTQ 合并？
  2. LSU 端口（4 LD + 4 STA + 4 STD）是否过多？
  3. LD IQ 和 STA IQ（各 64 项）能否合并？

### 方法

插桩和开关，默认全部关闭：

| 开关 | 类型 | 默认 | 作用 |
|---|---|---|---|
| `ARCH_STATS=1` | 环境变量 | 关 | 每拍统计 FIFO/FTQ/IQ 占用、各类端口每拍发射数、分派阻塞原因，结束时打印 `[AS]` 行 |
| `UFTQ_CAP=N` | 环境变量（需 `ARCH_STATS=1`） | 关 | 模拟统一 FTQ：PTAB + front2back + 保持寄存器 + FTQ 总占用 ≥ N−1 时 BPU 停顿 |
| `CFG_LD_PORTS` / `CFG_STA_PORTS` / `CFG_STD_PORTS` | 编译宏 | 4/4/4 | 访存发射端口数（1–4） |
| `CFG_LD_IQ_SIZE` / `CFG_STA_IQ_SIZE` / `CFG_STD_IQ_SIZE` | 编译宏 | 64/64/64 | 各 IQ 容量 |
| `CFG_MERGE_LDSTA` + `CFG_MEM_IQ_SIZE` | 编译宏 | 0 / 64 | LD 和 STA uop 进同一个 IQ，向 LD 端口和 STA 端口发射（端口仍分开） |

- 改动的文件：`include/ArchStats.h`（新）、`include/config.h`、`front-end/front_top.cpp`、`back-end/PreIduQueue.cpp`、`back-end/Isu.cpp`、`back-end/include/IssueQueue.h`、`back-end/Dispatch.cpp`（IQ 合并时的路由 `route_iq`，ROB 完成掩码仍按原 IQ 计算）、`rv_simu_mmu_v2.cpp`、`main.cpp`；脚本 `scripts/area/{build_variants,run_set,summarize}.sh`。
- **默认配置验证**：开关关闭和 `ARCH_STATS=1` 两种情况 gate 都是 62/62，周期与基线完全一致。
- **负载**：dhrystone（150,838 拍）、coremark（226,991）、memory-stress-small（189,128）、matmul_fpu（42,253）、prime（11,760）。大程序（cjpeg、linear_alg、parser、sha、memory-stress、Linux）**没有跑**。
- **复现**：
  ```bash
  cd trace-model
  bash scripts/area/build_variants.sh                    # 各变体编进 build_area/<名字>
  bash scripts/area/run_set.sh build/simulator <out>/base
  bash scripts/area/run_set.sh build/simulator <out>/uftq64 UFTQ_CAP=64
  bash scripts/area/run_set.sh build_area/m64/simulator <out>/m64
  bash scripts/area/summarize.sh <out> uftq64 m64 ...
  ```

### 模型近似（结论的局限）

- `UFTQ_CAP` 不是真正的统一 FTQ：PTAB(16) 和 front2back(32) 的原有容量限制还在，只是在其上加一个总量上限；用上一拍的占用判断，有一拍滞后；取指地址 FIFO 没有并入。
- 端口数只改了发射端口和由它派生的 LSU/DCache/DTLB 端口数，**没有建模**端口减少后可能带来的频率提升或流水线变化。
- 负载都很小：prime 只有 1.2 万拍，±1.5% 以内基本是错误路径造成的噪声；memory-stress-small 是合成测试。
- 面积只按存储位数估算，**没有综合**；端口带来的多端口读写、比较器、选择逻辑只做定性分析。

### 基线观察（`ARCH_STATS=1`）

- 前端各 FIFO 经常打满（dhrystone：PTAB p90=14/16，front2back p90=31/32，FTQ p90=58/64）。原因是后端 ibuf(128) 满了在反压，并不是真需要这么多缓冲。三处加起来的预测信息占用 p99 = 111（上限 112）。
- 访存发射：dhrystone 平均每拍 LD 0.76 条、STA 0.53 条、STD 0.48 条；每拍发 3–4 条 LD 的周期约占 6.5%，3–4 条 STA 约占 8%。
- 基线下**分派从未因 IQ 满而阻塞**；coremark 有 4.5% 的周期因 LDQ 满阻塞。LD IQ 的占用受 LDQ(64) 限制，STA IQ 的占用受 STQ(64) 限制。

### 结果 1：PTAB + front2back + FTQ 合并为统一 FTQ

位宽来自 RTL（`rtl/rtl/frontend/front_pkg.sv`、`rtl/rtl/backend/pre_idu_queue/`），手算，未编译确认：

| 结构 | 现状 | 合并后 |
|---|---|---|
| PTAB | 16 × 704b = 11,264b | 去掉 |
| front2back FIFO | 32 × 976b = 31,232b（预测相关 22,528b） | 32 × 278b = 8,896b（指令 + ftq_idx） |
| FTQ | 64 × 1824b = 116,736b | 64 × 704b = 45,056b |
| 合计 | 159,232b | 53,952b（−66%） |

- **与合并无关、零性能风险的部分**：FTQ 每项按 `BACKEND_FETCH_WIDTH=16` 存 16 个槽，但前端每组最多 8 条（`FETCH_WIDTH=8`），第 8–15 槽永远无效。每个槽又各存一份 PC，其实就是 base+4i。只把 FTQ 改成 8 槽、存 base pc，就从 116,736b 降到 45,056b。PC 数组有 19 个读端口（ALU/BR 10 + ROB 1 + 提交 8），改成只读 32 位 base 后读口也会小很多。
- **已验证**（2026-11-04）：`BACKEND_FETCH_WIDTH=16` 是遗留参数，前端都按 8 来。新增开关 `CFG_BACKEND_FETCH_WIDTH`（默认 16），设成 8 后 gate 62/62，5 个负载的周期全部不变。可以直接把它改成 8（或等于 `FETCH_WIDTH`），FTQ、ibuf 偏移位、前后端接口随之减半。
- 合并后 FTQ 要多一个写端口，供预译码检查器回写纠正后的方向和下一取指地址。

| 统一 FTQ 容量 | dhrystone | coremark | memory-stress-small | matmul_fpu | prime | 几何平均 |
|---|---|---|---|---|---|---|
| 96 | +0.00% | +0.00% | 0 | 0 | +0.00% | +0.00% |
| 80 | +0.00% | +0.00% | 0 | 0 | −0.36% | −0.07% |
| 64 | +0.00% | +0.00% | 0 | 0 | −1.45% | −0.29% |
| 48 | +0.06% | +0.98% | 0 | +0.01% | −0.17% | +0.18% |
| 32 | +1.22% | +1.53% | 0 | +0.11% | −1.51% | +0.26% |

**结论**：统一 FTQ 64 项性能不变，建议做。

### 结果 2：LSU 端口数（LD/STA/STD）

| 端口 | dhrystone | coremark | memory-stress-small | matmul_fpu | 几何平均 |
|---|---|---|---|---|---|
| 4/4/4（基线） | 150,838 | 226,991 | 189,128 | 42,253 | — |
| 4/3/3 | +0.10% | +0.00% | 0 | +0.11% | +0.04% |
| 4/3/2 | +0.16% | +0.77% | 0 | +0.18% | +0.22% |
| 4/2/2 | +1.57% | +0.93% | 0 | +0.28% | +0.56% |
| 3/3/3 | +1.07% | +1.08% | 0 | +0.11% | +0.45% |
| 3/2/2 | +2.56% | +0.55% | 0 | +0.28% | +0.68% |
| 2/2/2 | +7.12% | +1.71% | 0 | +0.28% | +1.79% |
| 4/1/1 | +12.66% | −0.58% | +10.25% | +0.75% | +4.47% |
| 3/1/1 | +13.91% | +0.95% | +10.25% | +0.75% | +5.02% |
| 2/1/1 | +20.42% | +1.29% | +10.25% | +0.75% | +6.26% |

每个端口牵动：LD → AGU、DTLB 查找口（现在共 8 个）、DCache 读口、STQ 转发比较、load 写回和唤醒广播（每个 IQ 项的源操作数都要比较）；STA → AGU、DTLB 查找口、DCache 写口、LDQ 顺序检查比较；STD → PRF 读口、STQ 数据写口。

**结论**：4/3/3 基本免费（省 2 个端口）；4/2/2 代价 0.6–1.6%（省 4 个端口）。LD 不要降到 2，STA/STD 不要降到 1。

### 结果 3：LD IQ 与 STA IQ 合并

| 配置 | 总项数 | dhrystone | coremark | 其余三个 | 几何平均 |
|---|---|---|---|---|---|
| 分开 64+64（基线） | 128 | — | — | — | — |
| 合并 64 | 64 | −0.03% | −0.05% | 0 | −0.02% |
| 合并 48 | 48 | −0.03% | +0.54% | 0 | +0.10% |
| 分开 32+32 | 64 | +0.00% | +3.38% | 0 | +0.67% |
| 合并 32 | 32 | −0.03% | +3.61% | 0 | +0.71% |
| 分开 16+16 | 32 | −0.09% | +5.94% | ≈0 | +1.15% |
| 合并 48 + 端口 3/2/2 | 48 | +2.45% | +2.55% | ≈0 | +1.05% |
| 合并 32 + 端口 3/2/2 | 32 | +2.45% | +2.89% | ≈0 | +1.12% |

**结论**：合并成 64 项，IQ 项数减半，没有性能损失；同样的总容量下合并明显比分开好。入队写端口从 8+8 降到 8。可以在共享存储上保留两个独立选择器（只挑 LD / 只挑 STA），选择复杂度不变。与端口裁剪叠加有交互：合并 48 + 3/2/2 在 coremark 上比单独减端口差 2 个百分点；合并 64 + 减端口的组合还没测。

### 后续

- 在大负载（Linux 启动片段、SPEC 检查点）上复核三组结论。
- 测合并 64 项 IQ + 端口 4/3/3、4/2/2 的组合。
- 真正实现统一 FTQ（去掉 PTAB、front2back 只存指令和 ftq_idx），替代 `UFTQ_CAP` 近似。
- 有综合流程后，用面积数字代替存储位数估算。

## EXP-016：后端资源 DSE（PRF / ROB / LDQ / STQ / 在飞分支 / IQ / MSHR），结合 PMU

**日期**：2026-11-08　**分支**：trace-model `exp/backend-dse`（基于 main `1d08b15`，**已合入 main**：`1e43fdf`、`7f8456e`；rtl `edf9d3b`；只合入支持代码，默认配置没变）　**脚本**：trace-model `scripts/dse/`（`configs.txt`、`dse_run.sh`、`local_run.sh`、`dse_report.py`）；数据 `~/personal/AI-Huma-data/dse/res`

**方法**：每个配置单独编一个二进制（`-DCFG_*`），基线 PRF128 / ROB128 / LDQ64 / STQ64 / MAX_BR 32 / MSHR 8 / IQ 64-64-64-16-32（共 240 项）。12 个 SPEC 程序各取权重最高的 3 个检查点（36 点，只覆盖每个程序 13%–38% 的权重，只反映趋势），精确预热 1000 万 + 测量 1000 万，`PMU=1`。程序内按权重取 CPI，12 个程序取几何平均。第一轮在服务器上跑（42 个配置 × 36 点，32 并发；60 并发超过 32 物理核且内存吃紧，已降），补充一轮在本地跑（4 个配置 × 每程序权重最高 1 点）。本地与服务器基线 sjeng 点周期一致（5,520,430），新增 PMU 事件不改周期。

**模型改动**：`CFG_LDQ_SIZE`（原写死 64；LSU 用 64 位掩码，LDQ/STQ 不能超过 64，所以只扫 ≤64）；两个只在 trace-model 的 PMU 事件 `SLOT_FE_OTHER_NOPREG`（重命名无空闲物理寄存器）、`SLOT_FE_OTHER_NOBRTAG`（IDU 无空闲分支标签），是 `SLOT_FE_OTHER` 的子项，原因取自同一拍的停顿标志（近似），不上 RTL 事件总线。原先这两种停顿都被算进"取指带宽"，PRF 不够会被误读成前端问题。

### 结果（12 个程序几何平均 IPC，相对基线；36 点）

| 参数 | 取值 → 变化 |
|---|---|
| PRF（ROB 128） | 64 −17.9%，80 −8.2%，96 −3.8%，112 −1.3%，**160 +0.18%，192/256 +0.14%（相同，饱和）** |
| ROB（PRF 128） | 64 −7.5%，96 −1.1%，192 −1.6%，256 −3.3%，384 −7.7%（PRF 不够，noPREG 升到 10%–21%） |
| PRF×ROB 同时放大 | 96/96 −3.8%，112/112 −1.0%，160/160 +0.23%，192/192 +0.47%，192/256 −0.15%，256/256 +0.55%，256/384 +0.53% |
| LDQ | 16 −1.2%，32 +0.3%，48 +0.1% |
| STQ | 16 −4.1%，32 −0.8%，48 −0.1% |
| MAX_BR_NUM | 12 −2.0%，16 −0.7%，24 −0.3%，48/64 +0.06%（相同） |
| MSHR | 4 −4.7%（libquantum −33%、mcf −11%），16 +0.8%（libquantum +8%） |
| IQ | 整体 ×0.5 −2.0%（hmmer −14%），×1.5 −0.1%，×2 −0.2%；INT 32 −0.4%，INT 128 0；LD 32 −0.1%；STD 32 0；BR 16 −0.3%，BR 64 与基线相同 |

补充（每程序 1 点，12 点，基线 IPC 1.994，与上面的 36 点表同方向但幅度不同）：`p256r256b64` +0.45%（对照 `prf256_rob256` +0.41%）；`p256r256b64m16` +2.01%（`mshr16` 单独 +1.75%）；`ldq32stq32` −0.65%（`ldq32` +0.32%、`stq32` −1.28%）；`mshr16ldq32` +1.43%（`mshr16` +1.75%，不可叠加，bzip2 −4.3%）。

### PMU 读出的瓶颈

- **基线是平衡的**：Ret 25.1% / BadSp 12.7% / FE 25.9% / BE 36.3%，BE 里几乎全是 ROB 满（33.2%），IQ 满 0.3%、LDQ 满 0、STQ 满 2.5%；noPREG 0.9%、noBRtag 0.4%。平均占用 ROB 67/128、LDQ 11.8/64、STQ 12.9/64。
- **PRF 128 是 ROB 128 的合适配对**：PRF<112 时 noPREG 占 3%–33%，IPC 急降；hmmer 最敏感（PRF 112 −12.5%，96 −31%，64 −63%）。PRF ≥160 后 noPREG 归零，再加无收益。
- **只加大 ROB 没用**：被 PRF 卡住（ROB 384 + PRF 128 时 noPREG 21%）。
- **窗口放大后收益很小，原因不是分支标签**：PRF/ROB 同时放大后 ROB 满从 33% 降到 9%–19%，但 IPC 只 +0.5%，BadSp 从 12.7% 升到 15%（1 点集 8.9% → 11.3%），sjeng/astar/libquantum/h264ref 回退 3%–6%，mcf/omnetpp/xalancbmk 涨 2%–7%。我原先猜是分支标签耗尽（noBRtag 升到 3%–7%），补充实验把在飞分支放大到 64 后 noBRtag 降到 0，IPC 不变（+0.45% vs +0.41%，回退仍在：astar −5.8%、libquantum −4.7%），**所以分支标签不是原因**；回退与 BadSp 上升同步，更可能是更深的窗口带来更多错误路径访存/污染，这一点没有单独验证。
- **LDQ 平均占用 12**，但 16 项时 7.8% 的槽因 LDQ 满停顿；32 即足够。STQ 16 明显不够（STQ 满 7.4%），32 小损，48 基本无损。
- **MAX_BR_NUM** 24 以下开始损失，32 合适。
- **MSHR** 是少数还有收益的参数（MLP 受限的 libquantum 大涨），MSHR 4 非常伤。
- **IQ**：基线 IQ 满只有 0.3%，加大无用；减半在 hmmer 上 −14%；INT IQ 64→32 仅 −0.4%，BR IQ 64 与 32 完全相同，有缩减空间。

### 结论与建议

1. 基线（PRF128/ROB128/MAX_BR32/IQ 240 项）在这组点上接近拐点：PRF/ROB 同时放大到 192/192 只有 +0.5%，256/384 也是 +0.5%，换来的触发器代价不值得。
2. **可缩减（省面积，需综合数字确认）**：LDQ 64→32（+0.3%）、STQ 64→48（−0.1%）、INT IQ 64→32（−0.4%）、BR IQ 32→16（−0.3%）。LDQ32+STQ32 一起是 −0.65%。
3. **可加**：MSHR 8→16（+0.8%，36 点集；1 点集 +1.75%），主要救访存密集程序，与 LDQ 缩减叠加时不可加。
4. PRF 不要低于 128，ROB 与 PRF 必须一起动；ROB 放大的收益被错误路径抵消，需要更好的分支预测才可能兑现。

### 没做 / 局限

- 每程序只有 3 点（补充 1 点），精确预热；没做发射端口数、取指/译码宽度；LDQ/STQ >64 受 LSU 实现限制，没扫。
- 面积代价没综合，只用"项数"定性比较；RTL 无改动；默认配置不变（只增加 `CFG_LDQ_SIZE` 开关和两个 PMU 事件），所以没有合入 main，也不需要 MAIN_RECORDS。
- 窗口放大后回退的原因（错误路径访存污染）没有验证；可以用关闭错误路径访存或统计错误路径 L1D 填充来验证。
- 补跑的服务器第二轮（6 个配置×36 点）因服务器关机作废，用本地 4 个配置×12 点代替。
