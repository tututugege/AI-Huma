# EXP-072 EXU 无阻塞重构、确定性 DIV/FDIV 占槽与真 5 物理 AGU

- **日期 / 版本 / 状态**：2026-11-28；总仓库 `main`（本行所在提交）、`trace-model` `1d9e004`、`rtl` `2eb7b9c`；**已合入 `main`**
- **开关与默认关闭回归**：无保留探索开关或回退分支（`ready/consume` 协议、`exu_ctrl_ready.sv`、`exu_ctrl_lsu_out.sv`、`exu_fu_sc_ctl.sv` 及逻辑 7 → 物理 5 AGU 映射同步删除）；默认配置即为唯一行为，全量回归零回退。

## 1. 动机与方案

EXP-044 / EXP-TLBPORTS 以来，EXU 与 ISU 之间仍保留着逐功能单元 `exe2iss_fu_ready_mask` / `ready_o` / `consume_i` / `busy_o` 握手，且 AGU 在 `config.h` / `isu` / `exu` / `lsu` 间仍残留“逻辑 7 槽、物理 5 实例”的映射与 `req_occ` 占用信号，带来多余组合控制链、寄存器负载与选口浪费。本次按设计本意彻底重构：

1. **取消 EXU ↔ ISU 逐 FU 握手协议（非阻塞发射）**：
   - `trace-model`（12 文件 `+291/−191`）与 `rtl`（55 文件 `+764/−1,225`）删除 `exe2iss_fu_ready_mask` 线网以及 `exu_ctrl_ready.sv`、`exu_fu_sc_ctl.sv` 和 `alu`/`bru`/`agu`/`sdu`/`mul`/`div`/`fp_*` 上的 `ready_o`/`consume_i`/`busy_o` 端口；
   - `mul_pipe` 与固定延迟浮点流水单元改为发射即预约的确定性无条件推进。
2. **变延迟迭代单元改为 ISU 侧确定性占槽 + 提前 1 拍让路**：
   - `isu.sv` 内增加 `div_busy_q`（port 1，随 `grant_uop[1]` 置位、随 `flush` / `rob_bcast_flush` / `exe2iss_div_wb_next` 清零）与 `fdiv_cnt_q`（`FP_LAST` 口，基于 `fp_latency` 倒计数），在 `iss_cls_free` 中阻塞同口迭代类写回，并在 `exe2iss_div_wb_next` 拉高前 1 拍对 PORT 1 ALU 让路（仅留 `div_wb_next` 一根前向指示线给 `isu`）。
3. **逻辑 7 → 物理 5 AGU 彻底合并为真 5 物理 AGU**：
   - `include/config.h` 与 `ttg_cfg_pkg.sv` 收敛为 `LSU_AGU_COUNT = 5`、`ISSUE_WIDTH = 19`（`LSU_AGU_SHARED = 1`）；
   - `isu_iq_select.sv` 在访存队列选口侧直接复用物理共用口 4（Load 优先于 STA），删除 `exu_ctrl_lsu_out.sv`、`req_occ` 与 `lsu`/`prf` 侧口压缩/借用读口特例，消除共用口碰撞拒绝。

## 2. 功能、门禁与 Linux 对齐验证

| 仓库 / 项 | 命令 / 条件 | 结果 |
|---|---|---|
| `trace-model` `main` | `python3 scripts/comb/comb_graph.py --check` | `22 modules, 43 phases`, **0 contract mismatches / 0 hazards** |
| `trace-model` `main` | `run_gate.sh` 默认 / `PF_ENABLE=0` / `run_gate_c.sh` | **`62/62` + `62/62` + `68/68` PASS**（重生成 3 份基线 0 条 `NA`） |
| `trace-model` `exp/exu-clean` | `linux_check.sh`（200M cap） | `rc=3 login=1 oops/panic=0`，到达 `rv64 login:` |
| `rtl` `main` Lint | `lint_chip.sh` / `lint_soc.sh`（Verilator 5.052） | **`0 warnings/errors`** |
| `rtl` `main` Strict+SVA | `SOC_FM=1 SOC_SVA=1 SOC_ASSERT=1 SOC_TB_FM_STRICT=1 fm_gate.sh` | **`PASS 77 FAIL 0 SKIP 0`**，`0` cycle diff vs `ref_cycles.txt` |
| `rtl/exu-clean` 官方 ISA | `SOC_TB_FM_STRICT=1 riscv_tests_gate.sh` | **`PASS 152 FAIL 0 SKIP 1`**（`SKIP rv64ui-ma_data`） |
| `rtl/exu-clean` 全片 SoC | `scripts/soc_gate.sh --linux` | **`PASS 12 FAIL 0`**（AXI4/UART/PLIC/boot/64b+128b+OpenSBI→Linux） |
| 集群 Linux 26 窗对齐 | 8 线程静态 `core_tb` (`SOC_FM=1 SOC_ASSERT=1`) | **`26/26 PASS`**（每窗 5.1M insts，PT/UP 指纹 100% 全等） |
| 固定大程序（2 GHz `trace-model`） | `dhrystone` / `coremark` / `memory-stress-small` | `93,749` (`2.756`) / `267,717` (`2.360`) / `310,480` (`3.378`) |

## 3. SPEC06 INT 全量 386 点性能评估（2 GHz `PMU=1`，vs `res_v11_2f_opt_386` EXP-070）

386/386 点全部通过，**`0` 失败**，12 项基准几何平均 **geomean `+0.144%`**（总分 **`13.2991 /GHz` ≈ `13.30 分/GHz`**，vs EXP-070 `13.28 分/GHz`）；单点区间 `−4.4%` ~ `+3.5%`。

| 基准 (点数) | CPI（旧 → 新） | IPC（旧 → 新） | 变化 | 最差 / 最佳单点 |
|---|---:|---:|---:|---:|
| `400.perlbench` (24) | `0.290 → 0.290` | `3.4477 → 3.4467` | `−0.03%` | `sp6 −3.3% / sp36 +1.1%` |
| `401.bzip2` (48) | `0.383 → 0.382` | `2.6109 → 2.6146` | `+0.14%` | `sp26 −3.1% / sp30 +3.5%` |
| `403.gcc` (34) | `0.567 → 0.567` | `1.7623 → 1.7649` | `+0.14%` | `sp15 −1.3% / sp4 +2.2%` |
| `429.mcf` (45) | `2.514 → 2.513` | `0.3978 → 0.3979` | `+0.04%` | `sp47 −2.4% / sp26 +1.7%` |
| `445.gobmk` (29) | `0.417 → 0.417` | `2.3974 → 2.3996` | `+0.09%` | `sp14 −1.0% / sp32 +1.7%` |
| `456.hmmer` (23) | `0.154 → 0.153` | `6.5139 → 6.5262` | `+0.19%` | `sp22 −0.2% / sp28 +0.5%` |
| `458.sjeng` (27) | `0.365 → 0.364` | `2.7412 → 2.7436` | `+0.09%` | `sp16 −0.6% / sp23 +0.6%` |
| `462.libquantum` (36) | `0.557 → 0.557` | `1.7948 → 1.7965` | `+0.10%` | `sp38 −1.2% / sp6 +3.4%` |
| `464.h264ref` (35) | `0.218 → 0.218` | `4.5870 → 4.5910` | `+0.09%` | `sp13 −0.5% / sp32 +0.8%` |
| `471.omnetpp` (25) | `1.050 → 1.041` | `0.9524 → 0.9609` | **`+0.89%`** | `sp30 −0.9% / sp10 +2.9%` |
| `473.astar` (26) | `0.781 → 0.780` | `1.2805 → 1.2816` | `+0.09%` | `sp25 −0.5% / sp11 +0.8%` |
| `483.xalancbmk` (34) | `0.445 → 0.446` | `2.2453 → 2.2432` | `−0.09%` | `sp25 −4.4% / sp16 +2.5%` |
| **Geomean (12)** | — | — | **`+0.144%`** | **`13.30 /GHz` (`13.2991`)** |

- **关键 PMU 均值变化（12 基准均值）**：`ISS_REF_AGU` 由 **`130,716.48 → 0.00`**（共用 AGU 碰撞拒绝清零），`OCC_STQ` `89,812,869.6 → 89,608,207.6`（`−204,662.1`），`SLOT_BE` `9,533,935.6 → 9,472,143.2`（`−61,792.5`，主要来自 `SLOT_BE_HEAD_MISS` `6,474,745.3 → 6,435,619.3`、`SLOT_BE_STQ_FULL` `995,956.2 → 980,517.9` 与 `SLOT_BE_FLUSH_WAIT` `128,794.9 → 100,838.0`），`SLOT_FE_OTHER` `13,027,735.3 → 12,987,924.8`。

## 4. 综合结果（TSMC 28nm DC Tier 3 签核 + EXP-071 Tier 1 快速确认路径）

全部报告均通过 `DC_LINK_STATUS=1` / `PT_LINK_STATUS=1`、`0` 错误、`0` 未映射单元（详细分析见 [../rtl/docs/09-synthesis-report.md](../../rtl/docs/09-synthesis-report.md) §23）：

| 模块 / 口径 | 基线 WNS / 级数 / Seq / 面积 (`µm²`) | EXP-072 WNS / 级数 / Seq / 面积 (`µm²`) | 变化 |
|---|---|---|---|
| **`exu_ctrl`** (Tier 3 DC, `none`) | `0.00 ns` / `13 lvl` / — / `31,760.90` | **`0.00 ns` (`CPL 0.37`) / `11 lvl` / `4,765` / `19,432.06`** | 面积 **`−38.8%`** |
| **`exu`** (Tier 3 DC vs 同日 `exu_base`) | `−0.41 ns` / `40 lvl` / `8,704` / `217,730.69` | **`−0.41 ns` / `46 lvl` / `6,755` / `207,202.80`** | TNS **`−18.1%`**, FF **`−22.4%`**, 面积 **`−4.84%`** |
| **`rob_bb`** (Tier 3 DC, `sram_bb`) | `−0.15 ns` / `42 lvl` / — / `121,413.43` | **`−0.16 ns` / `34 lvl` / `13,200` / `123,159.29`** | TNS **`−47.0%`**, 面积 `+1.44%` |
| **`prf`** (Tier 3 DC vs 同日 `prf_base`) | `0.00 ns` (`CPL 0.45`) / `11 lvl` / `24,196` / `580,853.60` | **`0.00 ns` (`CPL 0.45`) / `17 lvl` / `24,196` / `587,386.28`** | WNS 持平达标, 面积 `+1.12%` |
| **`isu`** (Tier 1 `Yosys+PT` vs EXP-071) | `−0.39` (`r2r −0.38`) / `39 lvl` / `29,106` / `526,654.30` | `−0.48` (**`r2r −0.39`**) / `37 lvl` / **`28,331`** / **`512,886.19`** | 面积 **`−2.61%` (`−775 FF`)**, `r2r` TNS `−5,794 → −5,648` |
| **`lsu`** (Tier 1 `Yosys+PT` vs EXP-071) | `−0.87` (`r2r −0.87`) / `33,974` / `1,052,504.38` | `−0.89` (`r2r −0.88`) / `33,974` / **`1,049,909.78`** | 面积 **`−0.25%`**, 时序持平 |

> **集群后台任务备注**：长程 Tier 3 DC28（`isu_new`、`lsu_new`）、Tier 2a（`back_top_bb_t2a_base/new`）与 `eda-10` 140M 周期 Linux 从零启动仍在集群目录 `/nfs_global/S/houruyao/dc28_exu_clean/` 与 `/nfs_global/S/houruyao/linux_ckpt_rv64gc/out_exu_clean_boot/` 异步继续运行。
