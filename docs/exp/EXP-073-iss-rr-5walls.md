# EXP-073 后端五墙合一时序切分（ISS→RR + L1 推测唤醒 + WBP v2 + FMA 4 拍 + Dispatch/IQ/LSU 切链）

- **日期 / 版本 / 状态**：2026-11-28；总仓库 `main`（本行所在提交）、`trace-model` `c988e43`、`rtl` `b753928`（`function-model` 未动 `c2dce72`）；**已合入 `main`**
- **开关与默认关闭回归**：无保留探索开关或 `-D` 宏分支（`iss_rr_split`、`lsu_wake_mode`、`lsu_l1_filter`、`lsu_l2_fallback`、`lsu_wbp_v2`、`lsu_srp_reg` 及 `SRAM_BLACKBOX` 已全部固化/清除）；`trace-model` 默认配置与 `rtl/common/ttg_cfg_pkg.sv`（180 常量，相对 `EXP-072` 仅 `FP_FMA_LAT = 4`）严格同步，本地三仓门禁零环境变量全通。

## 1. 动机与方案

在 `EXP-070` 消除 DTLB/LSU `1.24 ns` 往返链、`EXP-072` 完成非阻塞 EXU 与真 5 物理 AGU 重构后，`back_top` 剩余瓶颈集中在五条长组合环/链路（“五墙”）：

1. **Wall #1（`exp/wbp-v2` 解耦 WBP 写回/唤醒 + 最低优先级预寄存 SC）**：
   - `lp_wb.sv` 将 SC 请求预寄存 1 拍（`sc_req_v_q` / `sc_req_idx_q`，由 `alive_w`/`flush`/`mispred` 门控并置于写回口最低优先级），WBP 用 `lp_pickn(64→2)` + `popcount(~wbd_v)` 并行选取最多 `NWBP = 2` 路并以 direct one-hot OR 生成 `wb_go`（消除 `64→idx→译码` 与 SC/WBP 串行链）；`lp_wake.sv` 用每项预门控 `ent_pack` + `ttg_onehot_mux` 直驱 WBP 唤醒通道。
2. **Wall #2（`ISS → RR → EX/LSU` 两拍切分 + L1 推测唤醒 `lf=7`）**：
   - 在 `u_isu` 与 `u_prf` 之间插入 `iss_rr_reg`（`u_iss_rr`），斩断 `u_lsu/u_wake → u_isu → u_prf(27R) → u_exu` 跨模块长路径；
   - `lp_wake` 维护 256×2-bit PC 命中预测器（复位值 `2'd2`）与 `no_l1_spec`，在 L1 发 4 路推测唤醒并合并 L3 直发（4 路）、L2b STLF/L2a fallback（4 路）及 WBP（2 路）为 **14 路** `lsu2iss_wake`；未直接完成则在下一拍经 `lsu2iss_cancel` 撤销；
   - `isu` / `isu_iq_store` / `IssueQueue.h` 增加 1 拍 `spec_t1`/`spec_rr` 停泊与恢复、`fast_spec_q`/`fast_cancel_raw` ALU 孙代 1 周期取消、`isu_wake_mul`/`isu_wake_iter`/`isu_wb_gate`/`isu_fp_gate` 及 `div_spec_mask`/`fdiv_spec_mask` 推测预留回滚；
   - `exu_iter_ctl` 输出提前 2 拍 `wb_in2 = (accept && (lat_m1 == 1)) || (live && (cnt_q == 2))`（兼容 `L=2` early-out DIV），并在 `Exu` / `isu` 适配 **ISS → RR → EX** 旁路与写回冲突屏蔽（同步将 `BpuFtb.h` 合并到主线对齐状态）。
3. **Wall #3（`fp_fma_core` S1a/S1b 拆拍）**：
   - 将 `fp_fma_core` Stage 1 拆分为 S1a（53×53 乘 + C 对齐）与 S1b（加减 + 符号 + `exact_zero`），`FP_FMA_LAT` 从 3 拍增至 **4 拍**（`trace-model/include/config.h` `CFG_FP_FMA_LAT = 5` 同步至 `ttg_cfg_pkg.sv`）。
4. **Wall #4（切分 DTLB → STQ → `lp_rp` 尾链）**：
   - `lp_stq_ent` 导出纯寄存态 `trp_v`（不再直连 `trp8`）；`lp_rp` 用预寄存 `trp_ge_q` 替代组合桶形移位。
5. **Wall #5（Dispatch / IQ 容量 & `ttg_popcount` 切链）**：
   - `dispatch_iq_alloc` 直接导出未截断 `used_pos`，`dispatch_iq_req` 剥离 `dis_fire` 数据选通；移除实例化 `dispatch_wake_match`（仅保留未实例化文件），同拍唤醒由 `isu_iq` 入队侧与 `dispatch_busy_table` 叠加；
   - `isu_iq` 用寄存计数器 `used_q`/`ready_num_q` 替代每拍 64-bit `slot_valid` 归约（绕开 `isu_alloc_chain`），`ttg_popcount` 改逐层收窄位宽加法器；
   - `ttg_sram_1rw.sv` / `ttg_sram_1r1w.sv` / `scripts/fast_ppa.sh` / `docs/modules/{common,soc_periph}.md` 同步去除 `SRAM_BLACKBOX` 分支，统一 `SYNTH_TSMC28_SRAM` 与列表路径修复。

## 2. 验证结果（合并后主线复验全通）

| 仓库 / 项 | 命令 / 条件 | 结果 |
|---|---|---|
| `trace-model` 调度检查 | `python3 scripts/comb/comb_graph.py --check` | `22 modules, 43 phases`, **0 contract mismatches / 0 hazards** |
| `trace-model` 构建 | `make -j16` | 成功生成 `build/simulator` |
| `trace-model` 本地门禁 | `run_gate.sh` 默认 / `PF_ENABLE=0` / `run_gate_c.sh` | **`62/62` + `62/62` + `68/68` PASS**（重生成 3 份基线，0 条 `NA`） |
| `trace-model` Linux 启动 | `scripts/linux_check.sh build/simulator ~/rv64spec/linux_j.bin 150000000` | **PASS**（`exit 0`，`login=1`，`<90M` 拍到 `rv64 login:`，`oops/panic=0`，0 mismatch） |
| 固定大程序（2 GHz `trace-model`） | `dhrystone` / `coremark` / `memory-stress-small` | `102,117` (`2.530`) / `280,555` (`2.252`) / `311,806` (`3.363`) |
| `rtl` 配置同步 | `SIM_SRC=trace-model scripts/gen_cfg.sh` | `180` 常量，仅 `FP_FMA_LAT: 3 -> 4` |
| `rtl` Lint | `lint_chip.sh` / `lint_soc.sh` / `lint.sh`（Verilator 5.052） | **`lint_chip` 0 / `lint_soc` 0 / `lint.sh` 0 新增**（仅 6 条 `2eb7b9c` 原有提示） |
| `rtl` 单元等价测试 | `common_prims` / `wb_gate` / `fp_synth_check` / `div_check` | `100,000` PASS / `30,000` 拍 0 不一致 / `2,349,997` 0 不一致 / `103,528` PASS |
| `rtl` 整核 Strict+SVA 门禁 | `SOC_FM=1 SOC_SVA=1 SOC_XINIT_UNIQUE=1 fm_gate.sh` | **`PASS 77 FAIL 0 SKIP 0`**，`0` FM/SVA 错，**`0` cycle diff vs `ref_cycles.txt`** |
| `rtl` 严格随机 Fuzzer | `tools/fuzz/fuzz_run.py --seeds 50 --strict` | **`PASS=50 FAIL=0 ERR=0`**（`27,725` commits / `237,755` cycles） |

## 3. 待后续统一进行的评估

按本轮直接合入并推进前后端统一关键路径重跑的安排，以下集群/全芯片长跑暂未在本次合入前重复执行，将在下一轮统一关键路径扫面时集中完成：
- Synopsys DC / `fast_ppa.sh` Tier 1 后端与全核关键路径综合；
- `eda` 集群 `SPEC06 INT` 全量 386 点（及性能归因 / `iss-rr` + L1 推测唤醒收益评估）；
- `eda` 集群 8 线程静态 `core_tb` Linux 26 窗对比与全片 SoC `scripts/soc_gate.sh --linux`。
