# EXP-068：方案 C（9-bit `rob_ptr` 循环年龄冲刷 + `IQ_BR=64`）与硬件忠实版 S2 `ExBlockTage(4096×8)` + `StatCorrector` 全栈落地

- **日期**：2026-11-25
- **分支**：`trace-model` `exp/rob-ptr-bpu`；`rtl` `rtl/rob-ptr-bpu`
- **状态**：已合入 `main`（2026-11-25）
- **背景**：承接 [EXP-067](../archive/EXPLORATION_001_067.md#exp-067-2-ghz-冲-15-分ghz-全栈架构探索2mb-l2--16mb-l3--l3-stream--rob_ptr-冲刷--iq_br64--s2-8-表-tagesc) 探索结论，将其中**高性价比、低改造风险的第一批与第二批**（后端 9-bit `rob_ptr` 冲刷 + `IQ_BR=64`；前端 S2 8 表长历史 Block-TAGE + 硬件忠实版 StatCorrector）一次性在 `trace-model` 与 `rtl` 完成逐拍对齐落地与全量验证。

## 1. 微架构与 RTL 改动

### 第一批：方案 C（9-bit `rob_ptr` 循环年龄冲刷 + `IQ_BR=64`）
- **彻底删除 `br_mask` / `clear_mask` / `br_id`**：不再由 IDU 分配 31 个在飞分支标签，解除 `MAX_BR_NUM=32` 在飞分支上限（消除 `noBRT` 停顿）。
- **9-bit 循环年龄比较**：以 `{rob_flag, rob_idx}` 表示指令 ROB 指针，分支误预测时 EXU 通过 `idu_br_latch` 广播 `{redirect_rob_flag, redirect_rob_idx}`，各后端模块（`dispatch`、`prf`、`isu`、`exu_fu`、`exu_ctrl`、`lsu`）统一以 `rob_younger(a, b) = (a.flag == b.flag) ? (a.idx > b.idx) : (a.idx < b.idx)` 判定并冲刷年轻指令；`lsu_lrsc` 新增 1-bit `reserve_spec` 标记以区分投机/已提交保留位。
- **`idu` 大幅瘦身**：删除 `idu_br_alloc.sv`、`idu_br_group.sv`、`idu_br_state.sv`、`idu_br_cp.sv`、`idu_fire_ctl.sv` 5 个子模块。
- **`IQ_BR_SIZE` 扩容**：由 `32` 扩至 `64`（`trace-model/include/config.h` → `make cfg` 同步生成 `ttg_cfg_pkg.sv`）。

### 第二批：硬件忠实版 S2 `ExBlockTage(4096×8)` + `StatCorrector`
- **S2 `ExBlockTage`（`bpu_ftb_ex_tage.sv`）**：8 张几何历史表（长度 `{5, 11, 22, 44, 89, 178, 356, 712}`），每表 `4096 × 4` 槽、11-bit tag、`.INIT(2'd1)` 基表、16 项 per-PC `use_alt_q`；提交端口导出 `upd_live_pred/prov_hit/prov_cnt/base_cnt` 供 SC 共享单分支端口（`BRQ_W=1`）。
- **S2 `StatCorrector`（`bpu_ftb_sc.sv`）**：`Bias 64×4-way` + 4 张全局 `GEHL 512`（历史 `{4, 10, 20, 40}`）+ `IMLI 256`（8-bit 饱和后向条件循环计数器）+ `Local 256` + `LHT 64×10b` + 16 项动态阈值 `thres_q`（初值 35）。S1 读全部 7 路原始表项寄存至 S2，S2 仅做 4:1 多路选择 + 7 项加法与阈值比较，**对 S0/S1 关键路径零影响**。
- **历史维护（`bpu_spec.sv` / `bpu_stage_pkg.sv`）**：复用 1024-bit `HistRing`，增量维护 `ex_fh[3][8]`、`sc_fh[4]` 与 8-bit `imli`；提交态 `arch_sr_q` 拓宽至 720-bit。

## 2. 性能结果（2 GHz SPEC06 INT 386/386）

相对 2 GHz `main` 基线（`phys_2g_386`，`13.87 分/GHz`，EXP-066）：
- **Geomean IPC：`+1.90%`（`13.87 → 14.13 分/GHz`，386/386 全通 0 失败）**
- 分程序对比：
  - `445.gobmk`: **+5.85%**、`400.perlbench`: **+4.03%**、`483.xalancbmk`: **+3.25%**、`458.sjeng`: **+2.48%**、`401.bzip2`: **+2.30%**、`464.h264ref`: **+1.51%**、`473.astar`: **+1.29%**、`456.hmmer`: **+1.26%**、`403.gcc`: **+1.18%**、`429.mcf`: **+0.25%**、`462.libquantum`: **+0.00%**、`471.omnetpp`: **−0.45%**。
- 固定负载：`dhrystone` `89,802 → 86,839` (**−3.30%**, IPC `2.98`)、`coremark` `217,062 → 208,597` (**−3.90%**, IPC `3.03`)、`memory-stress-small` `311,381 → 312,143` (+0.24%, IPC `3.36`)。

## 3. 验证结果

- **`trace-model`**：`comb_graph.py --check` 0 隐患（25 模块 48 阶段）；`run_gate.sh`（默认 / `PF_ENABLE=0`）均 **62/62 PASS**；`rv64gc` Linux 5.15.170 从复位启动到 `rv64 login:`（0 oops/panic）。
- **`rtl`**：
  - `make cfg` 177 常量 **0 差异**；`lint_chip.sh` **0 警告 / 0 错误**；
  - `fm_gate.sh`（`SOC_FM=1`）：**69/69 PASS、0 FAIL、0 SKIP、0 FM 不一致、0 周期偏差**；
  - **`eda-06/07` 8 线程静态 `soc_tb` `rv64gc` + `Sv39` Linux 26 窗对齐（`s01..s26`，~1.326 亿指令）**：**26/26 PASS、0 FAIL、0 FM 不一致、26/26 全部 PT/UP 指纹 100% 逐拍全等**。

## 4. TSMC 28nm HPC+ DC 综合结果（`ssg0p81v125c`, `0.50 ns / 2.0 GHz`）

| 模块 | 逻辑级数 (`main` → 新) | WNS / Fmax (`main` → 新) | TNS (`main` → 新) | 面积 µm² (`main` → 新) |
|---|---:|---|---:|---:|
| **`idu`** | `35 → 14` (**−60.0%**) | `−0.15 (1.54G) → 0.00 ns (2.70G)` | `→ 0` | `18,196 → 1,994` (**−89.0%**) |
| **`isu`** | `→ 41` | `−0.23 (1.37G) → −0.23 ns (1.37G)` | `−5,096` | `608,221 → 598,408` (**−1.6%**) |
| **`lsu`** | `49 → 43` (**−12.2%**) | `−0.39 (1.12G) → −0.39 ns (1.12G)` | `−8,988 → −7,496` (**−16.6%**) | `840,182 → 758,236` (**−9.8%**) |

三模块合计后端面积净省 **107,960 µm²**，全核短板频率维持 `1.12 GHz` 零回退。
