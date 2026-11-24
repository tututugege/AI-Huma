# AI-Huma 合入 main 记录

每次合入 `main` 追加一行，最新的在最上面。规则见 [WORKFLOW.md](WORKFLOW.md) 第 5.2 节。

- 性能数字来自 trace-model，负载固定：dhrystone（64 次，`rtl/programs/big/dhrystone.bin`）、coremark（2 次迭代，`rtl/programs/big/coremark.bin`）、memory-stress-small（`trace-model/build/tests/memory-stress-small`）。
- 变化百分比相对上一行；正数表示周期变多（变慢）。
- 综合还没做时写"未做"和原因，不留空。

## 记录

| 日期 | 版本（总仓库 / function-model / trace-model / rtl） | 正确性 | dhrystone 周期 (IPC) | coremark 周期 (IPC) | memory-stress-small 周期 (IPC) | RTL 周期 | 综合（工具 / 频率 / 面积 / WNS） | 说明 |
|---|---|---|---|---|---|---|---|---|
| 2026-11-24 | 本行所在提交 / 未动（`55affa0`）/ `be7699a` / `7d84c7d` | **EXP-064（第三轮 TSMC 28nm HPC+ DC 时序优化：`dcache_pf` / `dcache_mshr` / `lsu` Wave 1+2 零周期变化优化 + `ren` 2-stage 流水化 + `Fu.h` `div_radix16_latency` `msd::taint` 修复）**。trace-model：`comb_graph.py --check` 0 隐患（25 模块 48 阶段）；`rv64gc` Linux `linux_check.sh` 启动到 `rv64 login:`（0 oops/panic）。RTL：`lint_chip.sh` 0 警告/0 错误；**`fm_gate.sh` + `tm_cycles.sh` 69/69 PASS、0 FAIL、0 SKIP、0 FM 不一致、周期与 `ref_cycles.txt` 0 处不同**；**`eda-05` 8 线程静态 `soc_tb` `rv64gc`+`Sv39` Linux 26 窗（`s01..s26`，每窗 510 万指令，最长达 1,415 万周期/窗，合计 ~1.326 亿指令）：26/26 PASS、0 FAIL、0 FM 不一致、26/26 PT/UP 指纹 100% 逐拍全等** | 87,468 (2.95)，−0.40% | 211,024 (2.99)，+1.28% | 310,301 (3.39)，−0.17% | RTL = trace-model（`ref_cycles{,_nopf}.txt` 69/69 全部相同） | **Synopsys DC `W-2024.09-SP2` + TSMC 28nm HPC+ (`ssg0p81v125c`, 12T SVT+LVT, `CLK=0.50ns / 2.0GHz`, `compile_ultra`)**：全核 **22/23 模块 ≥1.20 GHz（20/23 ≥1.28 GHz，14/23 ≥1.54 GHz）**：`dcache_pf` **1.18→1.35 GHz (+14.4%)**（WNS `−0.35→−0.24 ns` / 纯组合 `0.70 ns (1.43 GHz)` / 53→43 lvl / `151.7k um²`）、`dcache_mshr` **1.15→1.28 GHz (+11.3%)**（WNS `−0.37→−0.28 ns` / reg2reg `1.30 GHz` / 纯组合 `0.65 ns (1.54 GHz)` / 54→41 lvl / `99.5k→85.7k um²` **−13.9%**）、`ren` (`ren_2s`) **1.16→1.22 GHz (+5.2%)**（WNS `−0.36→−0.32 ns` / 46→40 lvl / TNS `−5,375` / `157.6k um²`）、`lsu` Wave 1+2 **0.88→0.97 GHz (+10.2%)**（WNS `−0.64→−0.53 ns` / 纯组合 `0.98 ns (1.02 GHz)` / TNS `−15.7k→−10.6k` **−32.6%** / `918.6k→873.6k um²` **−4.9%**）。详见 `rtl/docs/09-synthesis-report.md` §17 | `dcache_pf_berti_gen` 锦标赛树随路携 `d/st` + 并行页标签预计算（0 周期变化）；`dcache_mshr` 并行一次性预展开 3 路 store 数据/选通 + demand/all 并行选路（0 周期变化）；`lsu` Wave 1+2（`lp_pickn→ttg_pick_k`、`lp_cam` 未旋转 `hi/lo` 拆分、`lp_rp` 预寄存 `rp_f_q[0..3]`、`lp_pkg` `rel12/32` 8B 拆分、`lp_wb` `alive_unrot(count_q)&rotr64`，0 周期变化）；`ren` 落地 2 级流水（`IDU→S1→S2→DISPATCH`）+ `ren_ckpt_ctl` 静态槽位预计算 + `ren_log` 后置旋转 + `ren_alloc_sel` 直接前缀 `popcount`；顺带修 `Fu.h` `div_radix16_latency` `msd::live()` 遗留 bug。**全量 SPEC06 INT 386/386 点（0 失败，vs EXP-063 `res_r2_386`）：Geomean `−1.07%`**（`~14.99 /GHz`）。第四轮将主攻 `lsu` `L0/L1` 流水拆拍与 `ren` S1/S2 切点重平衡。见 EXPLORATION EXP-064 |
| 2026-11-24 | 本行所在提交 / 未动（`55affa0`）/ `4626924` / `aa7888b` | **EXP-063（第二轮 TSMC 28nm HPC+ DC 时序优化：`bpu_eval` 真并行 2-Ahead B + `bpu_spec` 寄存 `M_ARCH` + `lsu` 无移位 CAM/并行 `lp_wk` + `exu_ctrl` 修 DC `(VER-37)`）**。trace-model（零环境变量，已删实验开关）：`comb_graph.py --check` 0 隐患（25 模块 48 阶段）；`rv64gc` Linux `linux_check.sh` 启动到 `rv64 login:`（0 oops/panic）。RTL：`lint_chip.sh` 0 警告/0 错误；**`fm_gate.sh` + `tm_cycles.sh` 69/69 PASS、0 FAIL、0 SKIP、0 FM 不一致、周期与 `ref_cycles.txt` 0 处不同**；**`eda-04/05/07` 8 线程静态 `soc_tb` `rv64gc`+`Sv39` Linux 26 窗（`s01..s26`，每窗 510 万指令，最长达 1,328.5 万周期/窗）：26/26 PASS、0 FAIL、0 FM 不一致、26/26 PT/UP 指纹 100% 逐拍全等**（含 `s00` 1,497/1,497 桶全等，合计 ~1.377 亿指令） | 87,822 (2.94)，+2.83% | 208,361 (3.03)，+0.70% | 310,817 (3.38)，+0.11% | RTL = trace-model（`ref_cycles{,_nopf}.txt` 69/69 全部相同） | **Synopsys DC `W-2024.09-SP2` + TSMC 28nm HPC+ (`ssg0p81v125c`, 12T SVT+LVT, `CLK=0.50ns / 2.0GHz`, `compile_ultra`)**：全核 23/23 模块数据补齐（仅剩 `lsu` <1.0 GHz，22/23 模块 ≥1.15 GHz，14/23 ≥1.54 GHz）：`exu_ctrl` **MET ≥2.00 GHz**（WNS `0.00 ns` / 13 lvl / `31,761 um²`）、`bpu_eval` **0.84→1.28 GHz (+52.4%)**（WNS `−0.69→−0.28 ns` / 纯组合 `0.68 ns (1.47 GHz)` / 69→49 lvl / `25,652→23,911 um²`）、`bpu_spec` **0.86→1.20 GHz (+39.5%)**（WNS `−0.66→−0.33 ns` / 纯组合 `0.70 ns (1.43 GHz)` / reg2reg `−0.32 ns (1.22 GHz)` / `156k→142k um²`）、`lsu` **0.83→0.88 GHz (+6.0%)**（WNS `−0.71→−0.64 ns` / 56 lvl / `927k→919k um²`）。详见 `rtl/docs/09-synthesis-report.md` §16 | 2-Ahead B 改以 `(key_base, s0_base)` 索引与 Block A 真并行评估（`bpu_ftb_tab` 增 `STORE_B_BASE=1` 存 `b_base`、删除串行 `u0_b` 回退、`bpu_eval` 并行 `ttg_first_set` 与 6-bit 快速 `s0_b_bnd`）；`bpu_spec` `M_ARCH` 改读寄存态 `arch_sr_q/arch_fh_q/aras_q` 彻底切断 `commit → spec_a_ras_top` 关键路径；`lsu`（0 周期变化）在 `lp_cam` 用代数恒等式消除 2×64b 桶形移位器并在 `lp_wk` 并行预计算 3 路 `stlf_confirm`；`exu_ctrl_pkg` 修 `xc_is_fp_kind` 返回 `int` 消除 DC `(VER-37)`。**全量 SPEC06 INT 386/386 点（0 失败，vs EXP-062 `res_pf4_386`）：Geomean `−1.20%`（`~15.15 /GHz`，全点指令数一致）**，以 1.2% IPC 换取 BPU 频率 +40%~+52%。见 EXPLORATION EXP-063 |
| 2026-11-24 | 本行所在提交 / 未动（`55affa0`）/ `d872061` / `7f31634` | **EXP-062（建立 TSMC 28nm HPC+ DC 真实时序基线 + 第一轮 5 模块时序优化）**。trace-model：`comb_graph.py --check` 0 隐患（25 模块 48 阶段）；`rv64gc` Linux `linux_check.sh` 启动到 `rv64 login:`（0 oops/panic）。RTL：`lint_chip.sh` 0 警告/0 错误；8 项大程序与定向测试与 trace-model 逐拍全等（`memspec_pf` `3000→3005`，其余不变）；**`eda-06..10` 8 线程静态 `soc_tb` `rv64gc`+`Sv39` Linux 26 窗（`s01..s26`，每窗 510 万指令，最长达 1286 万周期/窗）：26/26 PASS、0 FAIL、0 FM 不一致、26/26 PT/UP 指纹 100% 逐拍全等**（含 `s00` 1492/1492 桶全等，合计 ~1.377 亿指令） | 85,401 (3.02)，0.00% | 206,921 (3.05)，0.00% | 未重跑（见说明） | RTL = trace-model（`ref_cycles.txt` 同步 `memspec_pf` `3000→3005`） | **首次 Synopsys DC `W-2024.09-SP2` + TSMC 28nm HPC+ (`ssg0p81v125c`, 12T SVT+LVT, `CLK=0.50ns / 2.0GHz`, `compile_ultra`)**：全核 22 模块建基线 + 第一轮 5 模块签核：`dcache_pf` **0.37→1.18 GHz**（WNS `−2.23→−0.35 ns` / 172→53 lvl / 184k→148k um²；Yosys 384→75）、`axi_llc_bop` **1.05→1.47 GHz**（`−0.45→−0.18 ns` / 51→42 lvl / 46k um²；Yosys 291→75）、`bpu_spec` **0.73→0.86 GHz**（`−0.87→−0.66 ns` / 69→41 lvl / 156k um²）、`ren` **1.05→1.16 GHz**（`−0.45→−0.36 ns` / 49→48 lvl / 144k um²）、`dcache_mshr` **1.15 GHz**（reg2reg 1.18 GHz / 99k um²；Yosys **123→99 层 <100**）。详见 `rtl/docs/09-synthesis-report.md` §15 | 建立权威 DC 28nm 时序签核体系（后续以 DC 28nm WNS/Fmax 推送、Yosys 作快速代理）；`dcache_pf` 改 4 级流水（`hist→srch_r_q→tab_s1→t1_q→tab_s2→gen`）+ 4 级 Top-2 锦标赛树 + 去 `srch→trig` 与 `pfi→fill→pf_hit` 同拍旁路并同步 `DataPrefetcher.h`；`axi_llc_bop` 5 级树+3 路并行预计算、`bpu_spec` 3 级 Kogge-Stone RAS + 128b 线性 `arch_sr_q`、`ren` `T-1` 预寄存 `ren_log` 8 项读窗、`dcache_mshr_alloc` `ttg_pick_k(16,8)` 均为 0 周期变化；修 `div_core`/`bpu_spec` DC Presto 语法。**全量 SPEC06 INT 386/386 点（0 失败，vs EXP-060 `15.25 /GHz`）：Geomean `+0.51%`（`~15.33 /GHz`，`hmmer +2.66%`、`sjeng +1.11%`、`gobmk +1.01%`、`h264ref +0.87%`、`gcc +0.56%`，最差 `−0.09%`）**。见 EXPLORATION EXP-062 |
| 2026-11-23 | 本行所在提交 / 未动（`55affa0`）/ `ac0a4bc` / `1df38b0` | **EXP-061（Radix-4 Booth 乘法 + 1× Radix-16 双 Radix-4 Early-out 变延迟除法与 EXU 动态唤醒 + 全套自研可综合 RV64FD FPU）**。trace-model：`comb_graph.py --check` 0 隐患（25 模块 48 阶段）；`run_gate.sh` 62/62、`PF_ENABLE=0` 62/62、`run_gate_c.sh` 68/68（新基线）；`rv64gc` Linux `linux_check.sh` 启动到 `rv64 login:`（0 oops/panic）。RTL：`make cfg` 同步（177 常量：`DIV_MAX_LATENCY=17`、`MAX_WAKEUP_PORTS=21`、`TOTAL_FU_COUNT=30`）；`lint_chip.sh` 0 警告/0 错误；专项逐位对拍：`mul_check` 400 万 PASS、`div_check` 10.3 万 PASS、`fp_synth_check` 235 万（对拍 SoftFloat）PASS；`-DFPU_REAL` 真自研 FPU 整核 `fm_gate.sh` **69/69 PASS、0 FAIL、0 SKIP、0 FM 不一致、周期与 `ref_cycles.txt` 0 处不同**；`eda-05..10` 8 线程静态 `soc_tb` `rv64gc` Linux 26 窗口（`s01..s26`，合计 ~1.326 亿指令）：**26/26 0 FM 不一致**（25/26 PT/UP 全程逐拍全等，仅 `s19` `cyc=2372697` 1 处错路微差） | 85,401 (3.02)，−3.72% | 206,921 (3.05)，−0.12% | 310,468 (3.38)，0.00% | RTL = trace-model（`-DFPU_REAL` `ref_cycles.txt` 69/69 全部相同） | 未做工艺库/WNS；`eda-10` Yosys 通用门（`SYNTH_LIGHT=1 SYNTH_MEM=1 SYNTH_LTP=1 strash;balance;map`）：`mul_unit` **40,041→27,473（−31.4%）/ 30 层**、`div_unit`（1× Radix-16 Early-out）**12,340 / 50 层**、`isu` **1,079,759→1,071,347（−8,412）/ 60 层**；自研 FPU 5 核心：`fp_misc_core` **1,874 / 39 层**、`fp_i2f_core` **1,790 / 73 层**、`fp_fcvt_core` **4,646 / 83 层**、`fp_fma_core` **33,776 / 98 层**、`fp_div_core` **10,885 / 73 层**；整块 `exu`（含真 FPU + 优化乘除法）**304,977 / 98 层** | `mul_core` 改 Radix-4 Booth（部分积 68→34 行）；DIV 缩为 1 个（Port 1）Radix-16（双 Radix-4 串联）+ CLZ Early-out（2..17 拍），由 `exu_iter_ctl.wb_next` 在完成前 1 拍动态广播唤醒并阻塞 Port 1 ALU（删除 `isu` `div_wake_slots` 与 Port 1 `isu_wb_gate`）；全套自研可综合 RV64FD FPU（默认仿真走快速 DPI，`SYNTHESIS` / `-DFPU_REAL` 走真可综合 RTL）。**全量 SPEC06 INT 386/386 点（0 失败，vs EXP-060 `15.25 /GHz`）：Geomean `+0.53%` → `15.33 分/GHz`**（`hmmer +2.65%`、`sjeng +1.12%`、`gobmk +1.05%`、`h264ref +0.85%`、`gcc +0.68%`、`xalancbmk +0.13%`）。见 EXPLORATION EXP-061 |
| 2026-11-23 | 本行所在提交 / 未动（`55affa0`）/ `0e609d7` / `99830ea` | **EXP-060（Load L2 推测唤醒 `load-to-use 4→3` + STLF `data_v` 纳入 L2 唤醒 + WBP 同拍唤醒 `5→4` + `isu` 4 路直接比较 cancel + `prf` 整数 `lsu_byp`）**。trace-model（零环境变量，已删实验开关）：`comb_graph.py --check` 0 隐患（25 模块 48 阶段）；`run_gate.sh` 62/62、`PF_ENABLE=0` 62/62、`run_gate_c.sh` 68/68（新基线）；`rv64gc` Linux `linux_check.sh`（`linux_j.bin`）启动到 `rv64 login:`（0 oops/panic）。RTL：`lint_chip.sh` 0 警告/0 错误；`fm_gate.sh` **69/69 PASS、0 FAIL、0 SKIP、0 FM 不一致、周期与 `ref_cycles.txt` 0 处不同**；**`eda-05..10` 实测 8 线程静态 `soc_tb` `rv64gc` + `Sv39` Linux 26 窗口检查点（`s01..s26`，每窗 510 万指令）：26/26 PASS、0 FAIL、合计 `132,600,045` 条指令 0 FM 不一致、26/26 全部 PT/UP 指纹 100% 逐拍全等** | 88,702 (2.91)，−4.88% | 207,177 (3.05)，−7.71% | 310,468 (3.38)，−0.24% | RTL = trace-model（`ref_cycles.txt` 69/69 全部相同） | 未做工艺库/WNS；`eda-08` Yosys 通用门（`SYNTH_LIGHT=1 SYNTH_MEM=1 SYNTH_LTP=1 SYNTH_NO_MEMPRIO=1 strash;balance;map`）：`lsu` **101 层（0 增长）/ 1,239,556 单元**、`dispatch` **57 层（0 增长）/ 212,064 单元（+5.9%）**、`prf` **25 层（0 增长）/ 639,644 单元（+4.1%）**、`isu` **60 层（50→60 层，仍远低于 `ren` 91 / `lsu` 101）/ 1,079,759 单元（+6.0%）** | 开启 `LP_L2[3]`（`LP_L2=1915`）实现 L2 推测唤醒与下拍取消（L1D Hit 及 `data_v=1 && !suppress` 的 STLF 候选均在 L2 提前 1 拍发唤醒，未直接完成则寄存 `cn_q` 于下拍 select 前撤回，零 replay 惩罚），`lp_wb` 导出 `wp_v/wp_idx` 让 WBP（MSHR Fill/Replay 返回）共享 `wk_valid[NLD+p]` 同拍唤醒；`prf_bypass` 补齐整数 4 路 `HAS_LSU_BYP` 旁路，同步收紧 `MsData.h` `until/pwhen` 至 `sim_time` 匹配旁路可见性；`isu` 删除 256/96-bit cancel 位图解码器改用 4 路 9-bit 直接比较（`match_cancel`）。**全量 SPEC06 INT 386/386 点（0 失败，vs EXP-059 `main` `14.86 /GHz`）：Geomean `+2.64%` → `15.25 分/GHz`（首次突破 15 分，12/12 全正零回退）**（`astar +4.67%`、`bzip2 +4.53%`、`perlbench +4.25%`、`gobmk +4.02%`、`sjeng +3.66%`、`xalancbmk +2.52%`、`hmmer +2.12%`、`h264ref +1.83%`、`omnetpp +1.68%`、`gcc +1.07%`、`mcf +0.87%`、`libquantum +0.61%`）。RTL 未跑 SPEC 与从复位长跑。见 EXPLORATION EXP-060 |
| 2026-11-23 | 本行所在提交 / 未动（`55affa0`）/ `f4f2122` / `9a52584` | **EXP-059（`ren` 稀疏 K=4 单写口检查点 + 本地 256×25b `ren_log` 8 宽前向 Walk + 8-bank 1R1W `free_list` + 删 8×`snapshot` 窄位宽 `ren_rat`）**。trace-model（零环境变量，已删旧 32 分支检查点与 DSE 开关）：`comb_graph.py --check` 0 隐患（25 模块 48 阶段）；`run_gate.sh` 62/62、`PF_ENABLE=0` 62/62、`run_gate_c.sh` 68/68（新基线）；`rv64gc` Linux `linux_check.sh` 启动到 `rv64 login:`（0 oops/panic，`RenLog` 逐条提交断言 0 偏差）。RTL：`make cfg` 同步（177 常量）；`lint_chip.sh` 0 警告/0 错误；`fm_gate.sh` **69/69 PASS、0 FAIL、0 SKIP、0 FM 不一致、周期与 `ref_cycles.txt` 0 处不同**；**`eda-05..10` 实测 8 线程 `soc_tb` `rv64gc` + `Sv39` Linux 26 窗口检查点（`s01..s26`，每窗 400 万周期）：26/26 PASS、0 FAIL、合计 `136,048,377` 条指令 0 FM 不一致、26/26 全部 PT/UP 指纹 100% 逐拍全等** | 93,252 (2.77)，+0.62% | 224,485 (2.81)，+0.03% | 311,226 (3.37)，+0.58% | RTL = trace-model（`ref_cycles.txt` 69/69 全部相同） | 未做工艺库/WNS；`eda-08` Yosys 通用门（`SYNTH_LIGHT=1 SYNTH_MEM=1 SYNTH_LTP=1 SYNTH_NO_MEMPRIO=1 strash;balance;map`）：`ren` **586,315 → 156,986 单元（−429,329，−73.22%）/ 91 层（与基线持平）**、`rob` **897,972 → 881,101 单元（−16,871，−1.88%）/ 65 层**、`dispatch` **200,195 单元 / 57 层**（`ren` + `rob` 合计净减 **−446,200 单元**） | 将 `dest_preg`/`old_dest_preg`/`me_elim` 从 ROB 抽离至 `ren` 本地 256×25b 8-bank 1R1W `ren_log`；`ren_ckpt` 从 32 项×8 写口缩减为 `REN_CKPT_NUM=4` 单写口 FIFO（分支间距 ≥ `REN_CKPT_INTERVAL=32` 分配，误预测命中 0 拍恢复、未命中复用 `ren_rat` 8 宽写口前向 Walk 并经 `ren2rob_walking` 暂停提交）；同步将 INT/FP `free_list` 改为 8-bank 1R1W（8b/7b 域内窄位宽）、删除 `ren_rat` 8 份全量 `snapshot[0..7]` 改双口直算并将 `ckpt_wr_lane_oh` 提前至 `inst_valid`。**全量 SPEC06 INT 386/386 点（0 失败，vs EXP-058 `main`）：Geomean `−0.18%`（`~14.85 分/GHz`）**（`hmmer +0.33%`、`gcc −0.05%`、`libquantum −0.06%`、`mcf −0.09%`、`h264ref −0.11%`、`gobmk −0.16%`、`omnetpp −0.19%`、`astar −0.26%`、`xalancbmk −0.28%`、`perlbench −0.36%`、`sjeng −0.39%`、`bzip2 −0.55%`）。RTL 未跑 SPEC 与从复位 1.4 亿周期长跑。见 EXPLORATION EXP-059 |
| 2026-11-23 | 本行所在提交 / 未动（`55affa0`）/ `aa345c9` / `2fbf053` | **EXP-058（硬件忠实版 LLC Bingo 4KB 空间预取器，与 BOP 双优先级协同）**。trace-model：`comb_graph.py --check` 0 隐患（25 模块 48 阶段）；`run_gate.sh` 62/62（默认 / `PF_ENABLE=0` / `LLC_BINGO=0` 均 62/62）；`rv64gc` Linux `linux_check.sh` 启动到 `rv64 login:`（0 oops/panic）。RTL：`lint_chip.sh` 0 警告/0 错误；`fm_gate.sh` **69/69 PASS、0 FAIL、0 SKIP、0 FM 不一致、周期与 `ref_cycles.txt` 0 处不同**；**`eda-05..09` 实测 `rv64gc` + `Sv39` Linux 27 窗口检查点与从复位验证（27/27 DONE、合计 `137,700,059` 条指令 0 FM 不一致、27/27 全部 PT/UP 指纹 100% 逐拍全等；`s01..s26` 26/26 PASS，`s00` 仅既有 PMU `SLOT_FE_RECOV_FLUSH` 归类口径差异）** | 92,674 (2.79)，0.00% | 224,411 (2.82)，0.00% | 309,431 (3.39)，−0.02% | RTL = trace-model（`ref_cycles.txt` 69/69 全部相同；`l2tlb_pwc` `9041→9028`、`memory-stress-small` `309486→309431`） | 未做工艺库/WNS；`eda-05` Yosys 通用门（`SYNTH_LIGHT=1 SYNTH_MEM=1 SYNTH_LTP=1 SYNTH_NO_MEMPRIO=1 strash;balance;map`）：新增 `axi_llc_bingo` **41,232 单元（25 `$mem_v2`、394 FFs）/ 48 层**（桶形移位优化后由 163 层降至 48 层，远低于 `axi_llc` 整体深度） | 在 `axi_llc` 落地硬件忠实版 LLC Bingo 4KB 空间预取器（总存储约 `26.75 KiB`，其中 `25.56 KiB` 为 1RW SRAM，占 4 MiB LLC `0.65%`）：32 项 FIFO FT + 32 项 31b tree-PLRU AGT + 4 项 `cmt_q` + `PHT_L`（256×4 1RW SRAM，3b tree-PLRU）& `PHT_S`（128×4 1RW SRAM，相对偏移桶形移位）+ 密集流过滤（`popcount >= 48`）+ 无乘法器节流器（256 窗 `<26` 命中降为 1/8 试探 `deg=2`）+ 1 候选/拍发射器 + 16 项 `bingo_q`（优先级低于 `bop_q`，`BOP_INF` `4→8`），打通 `dcache_mshr → axi_interconnect → axi_llc` 12-bit 负载 `pc_hash` 真实边带；**全量 SPEC06 INT 386/386 点（0 失败，vs EXP-056 `main` `14.69 /GHz`）：Geomean `+1.26%` → `14.88 分/GHz`（11 正 1 平 0 回归）**（`omnetpp +7.01%`、`mcf +2.59%`、`xalancbmk +1.37%`、`gcc +1.11%`、`sjeng +0.99%`、`astar +0.97%`、`perlbench +0.78%`、`bzip2 +0.23%`、`h264ref +0.12%`、`libquantum +0.09%`、`gobmk +0.08%`、`hmmer −0.02%`）。RTL 未跑 SPEC。见下文「变化」、EXPLORATION EXP-058 |
| 2026-11-22 | 本行所在提交 / 未动（`55affa0`）/ `c174d8d` / `c630c5d` | **EXP-056（统一 L2 TLB 1024×4 1RW SRAM + 8 项大页 CAM + 16 项 Sv39 PWC，及 `TraceBridge` 已提交页表读修复）**。trace-model：`comb_graph.py --check` 0 隐患（25 模块 48 阶段）；`run_gate.sh` 62/62、`PF_ENABLE=0` 62/62、`run_gate_c.sh` 68/68（`rvc-sv39.bin` `3270→3268`）；`rv64gc` Linux `linux_check.sh` 启动到 `rv64 login:`（0 oops/panic）。RTL：`make cfg` 同步（175 常量）；`lint.sh`（`ptw_walk`/`memcpu_pkg`）与 `lint_chip.sh` 0 警告/0 错误；新增 `directed/l2tlb_pwc.bin`（`9041 == 9041` 周期，14,243 指令 0 FM 不一致）；`fm_gate.sh` **69/69 PASS、0 FAIL、0 SKIP、0 FM 不一致、周期与 `ref_cycles.txt` 0 处不同**；**`eda-05..10` 实测 `rv64gc` + `Sv39` Linux 27 窗口检查点与从复位验证（27/27 DONE、约 1.377 亿指令 0 FM 不一致、27/27 UP 指纹 100% 全等、26/27 PT 指纹 100% 全等；`s02` 1 处错路投机重定向差 3 拍即重收敛至末尾全等）** | 92,674 (2.79)，0.00% | 224,411 (2.82)，0.00% | 309,486 (3.39)，0.00% | RTL = trace-model（`ref_cycles.txt` 69/69 全部相同） | 未做工艺库/WNS；`eda-05` Yosys 通用门（`SYNTH_LIGHT=1 SYNTH_MEM=1 SYNTH_LTP=1 SYNTH_NO_MEMPRIO=1 strash;balance;map`）：`ptw_walk` **5,446 单元（21 `$mem_v2`、206 FFs）/ 44 层**（较改前 47 层反降 3 层） | 在 `ptw_walk` 落地硬件可综合统一 L2 TLB（4 独立 1D 256×76b 1RW SRAM bank、XOR 索引 `vpn[7:0]^vpn[16:9]`、3-bit tree-PLRU）+ 8 项 RR 大页 CAM + 16 项 RR Sv39 PWC（20-bit root 匹配），零 L1 关键路径改动；**全量 SPEC06 INT 386/386 点（0 失败，vs EXP-055 `main` `14.24 /GHz`）：12/12 全正、Geomean `+3.17%` → `14.69 分/GHz`**（`mcf +14.61%`、`xalancbmk +9.74%`、`omnetpp +4.38%`、`astar +3.34%`、`perlbench +2.22%`、`bzip2 +2.21%`、`gcc +0.62%`、`h264ref +0.60%`、`sjeng +0.49%`、`gobmk +0.48%`、`hmmer +0.36%`、`libquantum +0.06%`）。同步修复 `TraceBridge` PTW 读到 ROB 内未提交 store 投机值导致 Linux 早期 oops 的缺陷。RTL 未跑 SPEC。见下文「变化」、EXPLORATION EXP-056 |
| 2026-11-22 | 本行所在提交 / 未动（`55affa0`）/ `16548ba` / `f1fed8a` | **EXP-055（后端指令窗口扩展 `PRF=256 / ROB=256`、`MAX_BR=32` 不变 + `ren` 公共原语降深度 `100→91` 层）**。trace-model：`comb_graph.py --check` 0 隐患（25 模块 48 阶段）；`run_gate.sh` 62/62、`run_gate_c.sh` 68/68（新基线）；`rv64gc` Linux `linux_check.sh` 启动到 `rv64 login:`（0 oops/panic）。RTL：`make cfg` 同步（171 常量）；`lint_chip.sh` 0 警告/0 错误；`tests/ren_elim_sel/run.sh` 100k 随机 0 不一致；`fm_gate.sh` **68/68 PASS、0 FAIL、0 SKIP、0 FM 不一致、周期与 `ref_cycles.txt` 0 处不同**；**`eda-05..10` 实测 `rv64gc` + `Sv39` Linux 27 窗口检查点与从复位验证（`s01..s26` 26/26 PASS + `s00_inst0` PT/UP `0..1513` 全等，合计 `137,700,051` 条指令 0 FM 不一致、27/27 全部 PT/UP 100% 全等）** | 92,674 (2.79)，−3.74% | 224,411 (2.82)，−3.33% | 309,486 (3.39)，−5.37% | RTL = trace-model（`ref_cycles.txt` 68/68 全部相同） | 未做工艺库/WNS；`eda-08` Yosys 通用门（`SYNTH_LIGHT=1 SYNTH_MEM=1 SYNTH_LTP=1 SYNTH_NO_MEMPRIO=1 strash;balance;map`）：`ren` **97 → 100 → 91 层** / 586,315 单元、`prf` **27 → 25 层** / 614,529 单元、`rob` **64 层**（不变）/ 897,972 单元、`isu` **50 层**（不变）/ 1,018,639 单元 | 基于 386 点加权 TMA（原 `128/128` 下 `NOPREG=14.9%`、`ROB_FULL=11.6%`）与两轮 DSE 落地 `PRF=256 / ROB=256`（`MAX_BR=32` 及全部 IQ/LDQ/STQ/MSHR 不变）；**全量 SPEC06 INT 386/386 点（0 失败，vs EXP-053 `main` `13.48 /GHz`）：Geomean `+5.64%` → `14.24 分/GHz`**（`h264ref +13.07%`、`omnetpp +12.67%`、`xalancbmk +8.40%`、`hmmer +6.95%`、`sjeng +6.56%`、`perlbench +5.77%`、`gcc +5.45%`、`astar +5.00%`、`bzip2 +2.18%`、`gobmk +1.80%`、`mcf +1.06%`、`libquantum −0.27%`），`BE` 降至 `26.45%`（−7.36 pp）、`MLP` `3.54 → 4.63`。RTL 侧同步复用 `ttg_first_set`/`ttg_onehot_mux`/`ttg_onehot_to_idx` 压降 `ren` 至 91 层（低于 128/128 基线 6 层）。RTL 未跑 SPEC。见下文「变化」、EXPLORATION EXP-055 |
| 2026-11-22 | 本行所在提交 / 未动（`55affa0`）/ `4d4534f` / `28840c8` | **EXP-053（前端两阶段清理重构 + 复用 `ttg_pick_k` 与 `` `ifdef SYNTHESIS `` 双路径 + `LSU_MS_DATA` STLF `cam_ok` 修复）**。trace-model：`comb_graph.py --check` 0 隐患（25 模块 48 阶段）；`run_gate.sh` 62/62、`PF_ENABLE=0` 62/62、`run_gate_c.sh` 68/68（新基线）；`rv64gc` Linux `linux_check.sh` 启动到 `rv64 login:`（~75M 周期，0 oops/panic）。RTL：`gen_cfg.sh` 171 常量 0 差异；`lint_chip.sh` 0 警告/0 错误；`tests/common_prims` 100k PASS、`tests/ren_elim_sel` 100k PASS、`tb/fe_clean_eq/fe_clean_eq_tb.sv` 双路径（`SIM` 0.038s / `SYNTHESIS` 0.138s）0 错；`fm_gate.sh` **68/68 PASS、0 FAIL、0 SKIP、0 FM 不一致、周期与 `ref_cycles.txt` 0 处不同**；**合并后 `4d4534f`+`28840c8` 在 `eda-05..10` 实测 `rv64gc` + `Sv39` Linux 27 窗口检查点与从复位验证（`s01..s26` 26/26 PASS + `s00` PT/UP `0..1619` 全等，合计 `137,700,065` 条指令 0 FM 不一致，27/27 全部 PT/UP `150,175 / 150,175` bins 100% 全等，含原 EXP-052 `s17` 也归零对齐）** | 96,276 (2.68)，−0.08% | 232,140 (2.72)，+0.53% | 327,038 (3.21)，+0.07% | RTL = trace-model（`ref_cycles.txt` 68/68 全部相同） | 未做工艺库/WNS；`eda-04..06` Yosys 通用门（`SYNTH_LIGHT=1 SYNTH_MEM=1 SYNTH_LTP=1 SYNTH_NO_MEMPRIO=1 strash;balance;map`）：`front_top` **1,582,763/356 → 1,159,189 (−26.8%) / 216 层 (−39.3%)**、`bpu` **504,078/272 → 410,093 (−18.6%) / 197 层 (−27.6%)**、`icache` **916,659/106 → 389,270 (−57.5%) / 114 层**、`pre_idu_queue` **137,578 → 131,433 (−4.5%) / 38 层**、`axi_cpu_port_adapter` 227/9、`dcache_bank` 142,429/12、`dcache_s2_ld` 5,097/37、`dcache_wb` 23,334/49、`rob` 466,653/64 | 彻底清除 EXP-051 遗留三处微架构补丁（跨子系统 `fdip_snoop` 旁路改 1 拍 `dc_req/dc_resp` 探针、`resp_popped_q` 改 AXI 通道 0 `CLEAR_ON_POP=1`、跨页 RVC 缺页 `inst→diag_val[1]` 搭便车改显式 1b `pf_inst_hi`）与全链路死线 `tage_idx/tag`；显式真 4-Bank `icache_arr` 面积砍半；`front_pd_info` 复用公用 `ttg_pick_k`，`front_head_fix`/`bpu_hist_vec` 补齐 `` `ifdef SYNTHESIS `` 仿真快速路径（3.6× 提速）；顺带修复 `LsuPipeTranslate.cpp` STLF `cam_ok` 缺陷。SPEC06 INT 386/386 合并后实测（`res_exp053_main_386`，0 失败）：**`13.48 分/GHz`（vs EXP-052 `13.49 /GHz` −0.05%、vs EXP-051 `13.42 /GHz` +0.50%**；`gobmk +0.28%`、`sjeng +0.14%`，仅 `403.gcc sp13 −25.8%` 拖累 `gcc −0.45%`，其余 384/386 点均在 ±2% 内；合并前 vs EXP-051 为 +0.020%）。RTL 未跑 SPEC；未在合并后重跑 Yosys 综合（仅 `front_pd_info` 换 `ttg_pick_k`）。见下文「变化」、EXPLORATION EXP-053 |
| 2026-11-22 | 本行所在提交 / 未动（`55affa0`）/ `1939bd1` / `9798eb7` | **EXP-052（RV64GC `c.mv` 规范化 + 组内 1-hop 关键链移动消除 + `ren` 降深度 99→97 层）**。trace-model：`comb_graph.py --check` 0 隐患（25 模块 48 阶段）；`run_gate.sh` 62/62、`run_gate_c.sh` 68/68（新基线）；`rv64gc` Linux `linux_check.sh` 启动到 `rv64 login:`（~75M 周期，0 oops/panic）。RTL：`lint_chip.sh` 0 警告/0 错误；`tests/ren_elim_sel/run.sh` 100,000 次随机 0 不一致；`fm_gate.sh` **68/68 PASS、0 FAIL、0 SKIP、0 FM 不一致、周期与 `ref_cycles.txt` 0 处不同**；**`rv64gc` + `Sv39` Linux 27 窗口检查点与从复位验证（合计 137,700,067 条指令 0 FM 不一致，26/27 窗口 PT/UP 0 差异；`s17` 前 3,639,100 拍 100% 相等，第 3,639,154 拍 ICache miss 早返回 4 拍，经确认属 trace-model 错误路径访存模型差、予以接受）** | 96,351 (2.68)，0.00% | 230,923 (2.74)，−0.43% | 326,797 (3.21)，0.00% | RTL = trace-model（`ref_cycles.txt` 68/68 全部相同；`itt-dispatch` −6.1%，`coremark` −0.43%） | 未做工艺库/WNS；`eda-08` Yosys 通用门（`SYNTH_LIGHT=1 SYNTH_MEM=1 SYNTH_LTP=1 SYNTH_NO_MEMPRIO=1 strash;balance;map`）：`ren` **99 → 97 层** / 475,533 单元（+834，+0.18%）、`idu` **66 层** / 31,607 单元 | 修复此前 `is_move_shape` 漏掉全部 RV64GC 16-bit `c.mv`（`MOVE_ELIMINATED=0%`）的缺陷，并新增组内 1-hop 生产链移动消除。**全量 SPEC06 INT 386/386 点（0 失败，vs `res_fe2f_final_386`）：12 程序全正零回退、Geomean `+0.55%`**（`xalancbmk +1.62%`、`omnetpp +1.22%`、`sjeng +0.79%`、`h264ref +0.74%`、`gobmk +0.68%`、`mcf +0.43%`、`bzip2 +0.39%`、`astar +0.31%`、`gcc +0.30%`、`hmmer +0.14%`、`libquantum +0.04%`、`perlbench +0.01%`）。RTL 未跑 SPEC；`ren` 深度不升反降 2 层（销项 TODO 中 `mov` 消除拉长 `ren` 条目）。见下文「变化」、EXPLORATION EXP-052 |
| 2026-11-21 | 本行所在提交 / 未动（`55affa0`）/ 未动（`7e00aae`）/ `de5fdb9` | **RTL 公共原语平衡树与 `isu`（89→50 层）/ `ren`（111→99 层）零周期变化降深度重构**：新增 `ttg_pick_k.sv`（温度计 Kogge-Stone 并行前 K 选口）、`ttg_onehot_mux`/`ttg_popcount` 改堆式平衡树，4 个公共原语均加 `` `ifdef SYNTHESIS `` 仿真快速路径；`isu_alloc_chain`/`isu_wake_compact`/`isu_iq_select`/`ren_alloc_sel` 统一复用 `ttg_pick_k`，同步优化 `isu_iq`/`isu_fp_gate`/`isu_wake_src`/`isu_iq_store` 关键路径。RTL：`lint_chip.sh` 0 警告/0 错误；`tests/common_prims/run.sh` 100,000 次随机双路等价测试 0 差异；`fm_gate.sh` **68/68 PASS、0 FAIL、0 SKIP、0 FM 不一致、周期与 `ref_cycles.txt` 0 处不同**；**`rv64gc` + `Sv39` Linux 27 窗口检查点与从复位验证（`s01..s26` 26/26 PASS + `s00_inst0` 510 万指令，合计 137,700,071 条指令 0 FM 不一致、27/27 全部 PT/UP 指纹 bin 0 差异）** | 96,351 (2.68)，0.00% | 231,913 (2.72)，0.00% | 326,797 (3.21)，0.00% | RTL = trace-model（`ref_cycles.txt` 68/68 全部相同） | 未做工艺库/WNS；`eda-08` Yosys 通用门（`SYNTH_LIGHT=1 SYNTH_MEM=1 SYNTH_LTP=1 SYNTH_NO_MEMPRIO=1 strash;balance;map`）：`isu` **89 → 50 层（−43.8%）** / 931,747 单元、`ren` **111 → 99 层（跌破 100 层红线）** / 474,699 单元、`rob` 64 层 / 466,402、`tlb_mmu` 61 层 / 46,582 | 纯 RTL 结构与公共原语重构（零周期变化）；`isu` 仅剩纯整数单周期选择-唤醒核心环路（50 层），`ren` 从超 100 层清单销项；4 个公共原语仿真快速路径与综合平衡树经 10 万次随机验证逐位等价 |
| 2026-11-21 | 本行所在提交 / 未动（`55affa0`）/ `7e00aae` / `05ec97f`（优化本体 `480a89e`） | **后端执行唤醒与 Bypass 阶段一瘦身（唤醒驱动 6 位二维 EXU Bypass Mask + 按域裁剪 PRF 读口/旁路 + 删除 31 路 `exe2prf_bypass` + 快慢唤醒分离 + 23 级移位寄存器 `isu_fp_gate` + `dispatch` 去重唤醒）及 `trace-model` 清理（删死 `ExePrfIO` + 13 个已采纳 `CFG_*` 旧开关）**。trace-model：`comb_graph.py --check` 0 隐患（25 模块 48 阶段）；`run_gate.sh` 62/62、`run_gate_c.sh` 68/68（零周期变化）；`rv64gc` Linux 从复位启动到 `rv64 login:`（约 80M 周期，0 oops/panic）。RTL：`make cfg` 同步（171 常量）；`lint_chip.sh` 0 警告/0 错误；`fm_gate.sh` **68/68 PASS、0 FAIL、0 SKIP、0 FM 不一致、周期与 `ref_cycles.txt` 0 处不同**；**`rv64gc` + `Sv39` Linux 27 窗口检查点与从复位验证（`s01..s26` 26/26 PASS + `s00_inst0` 510 万指令，合计 137,700,071 条指令 0 FM 不一致、27/27 全部 PT/UP 指纹 bin 0 差异）** | 96,351 (2.68)，0.00% | 231,913 (2.72)，0.00% | 326,797 (3.21)，0.00% | RTL = trace-model（`ref_cycles.txt` 68/68 全部相同） | 未做工艺库/WNS；`eda-06` Yosys 通用门（`SYNTH_LIGHT=1 SYNTH_MEM=1 SYNTH_LTP=1 SYNTH_NO_MEMPRIO=1 strash;balance;map`）：`prf` 679,466 → **395,785 (−41.8%) / 27 层**、`isu` 948,982 → **916,275 (−3.4%) / 89 层**（原 90 层）、`dispatch` 186,536 → **176,071 (−5.6%) / 56 层**、`exu_ctrl` 20,133 → **20,037 (−0.5%) / 17 层**（四模块合计 **−326,949 单元，−17.8%**） | 零周期变化纯结构优化；彻底消除 `prf` EXU 级 378 个 8-bit 比较器与 31 路 `exe2prf_bypass` 广播总线，四模块深度全部持平或下降；同步将 RTL `rob_pkg::EBREAK_TRAP` 设为默认开启。未重跑 SPEC06（周期不变）、未重跑整块 `back_top` 综合。见下文「变化」 |
| 2026-11-21 | 本行所在提交 / 未动（`55affa0`）/ `5b67500` / `3fa98cd` | **EXP-051（前端 `2-taken` + `2-Ahead B` + 4-Bank 1R1W ICache / 2 读口 ITLB + 实 AXI S2 确认 2-slot FDIP，里程碑 B）+ RVC 跨 4KB 页第二半字取指缺页 `stval = pc + 2` 架构缺陷修复**。trace-model（零环境变量，删旧 `FE_PAIR`/`FE_IPF`/`FE_IPF_LAT`）：`comb_graph.py --check` 0 隐患（25 模块 48 阶段）；门禁 62/62、62/62（`PF_ENABLE=0`）、C 68/68（新基线）；`rv64gc` Linux 5.15.170 从复位启动到 `rv64 login:`（默认 `--irq-seed 1` 及 seed 2 / `PF_ENABLE=0`，约 80M 周期，0 oops/panic）。RTL：`make cfg` 同步（171 常量）；`lint_chip.sh` 0 警告/0 错误；`fm_gate.sh` **68/68 PASS（含新增 `directed/fe_2taken_fdip.bin`）、0 FAIL、0 SKIP、0 FM 不一致、周期与 `ref_cycles.txt` 0 处不同**；**`rv64gc` + `Sv39` Linux 27 段检查点窗口（`s01..s26` 26/26 PASS 合计 ~1.326 亿指令、`s00_inst0` 510 万指令 0 FM 不一致且 1637/1637 PT/UP bins 0 差异）** | 96,351 (2.68)，−5.75% | 231,913 (2.72)，−15.77% | 326,797 (3.21)，−4.89% | RTL = trace-model（`ref_cycles.txt` 68/68 全部相同；`fe_2taken_fdip` 3,602、`dhrystone` −5.75%、`coremark` −15.77%、`memory-stress-small` −4.89%） | 未做工艺库/WNS；`eda-04/05` Yosys 通用门（`SYNTH_LIGHT=1 SYNTH_MEM=1 SYNTH_LTP=1 SYNTH_NO_MEMPRIO=1 strash;balance;map`）：`predecode` **10,144 / 27**（−2 层）、`pre_idu_queue` **137,578 / 38**（−1 层）、`tlb_mmu` **46,624 / 61**（不变）、`icache` **916,659 / 106**（原 312k/70）、`bpu` **504,078 / 272**（较旧 16-bank 549k 仍 −8.3%，较 EXP-050 275k/131）、`front_top` **1,582,763 / 356**（超 100 层已登记 TODO） | 全量 SPEC06 INT 386/386 点（`sim64_fe2f_final`，vs EXP-050 `main` `13.14 /GHz`）：**+2.18%（`13.42 分/GHz`）**，相对 EXP-048 累计 **+10.76%**（12/12 全正）；`perlbench +6.08%`、`gcc +6.06%`、`sjeng +5.17%`、`gobmk +4.68%`、`h264ref +1.85%`、`bzip2 +1.57%`、`astar +1.44%`、`libquantum +0.77%`、`mcf +0.18%`、`xalancbmk +0.11%`、`omnetpp −0.00%`、`hmmer −1.42%`；TMA `Retiring 30.92% → 31.58% (+0.66 pp)`、`FE.bw 22.77% → 18.60% (−4.18 pp)`、`FE.lat 1.79% → 1.71%`。RTL 未跑 SPEC，未跑从复位 1.4 亿周期全程指纹对比。见下文「变化」、EXPLORATION EXP-051 |
| 2026-11-21 | 本行所在提交 / 未动（`55affa0`）/ `ef61350` / `a4dcfb9` | **EXP-050（块级 1-Ahead FTB + S2 Block-TAGE/ITT 分支预测器，里程碑 A）+ `LsuPipeInternal.h` 污染 store 旧物理地址 STLF 修复**。trace-model（零环境变量，实验开关已删）：`comb_graph.py --check` 0 隐患；门禁 62/62、62/62（`PF_ENABLE=0`）、C 68/68（新基线，含 `build_tests.sh` 对 Ubuntu clang-18/lld-18 的 `.data/.sdata` 与 `unalign` 修复）；`rv64gc` Linux 5.15.170 从复位启动到 `rv64 login:`（0 oops/panic）。RTL：`lint.sh rtl/frontend/bpu`（15 文件）与 `lint_chip.sh` 均 0 警告/0 错误；`fm_gate.sh` **67/67 PASS、0 FAIL、0 SKIP、0 FM 不一致、周期与 `ref_cycles.txt` 0 处不同**；**`rv64gc` + `Sv39` Linux 26 段检查点窗口（`s01..s26`，每段 400 万周期，合计 1.04 亿周期、132,473,668 条指令）26/26 PASS、0 FM 不一致、PT（103,974 bins）与 UP（103,144 bins）指纹全程 0 差异** | 102,229 (2.53)，−6.13% | 275,332 (2.29)，−5.28% | 343,584 (3.05)，+0.04% | RTL = trace-model（`ref_cycles.txt` 67/67 全部相同；`itt-dispatch` 208,168 −3.36%、`dhrystone` −6.13%、`coremark` −5.28%） | 未做工艺库/WNS；`eda-06` Yosys 通用门（`SYNTH_LIGHT=1 SYNTH_MEM=1 SYNTH_LTP=1 SYNTH_NO_MEMPRIO=1 strash;balance;map`）：`bpu` **549,458 → 274,811 单元（−50.0%）**、深度 **134 → 131 层**（最长路径仍在原有 `u_spec.aras_q → spec_d`）；`front_top` **898,333 单元 / 153 层**（原超 3600s 未出数） | 全量 SPEC06 INT 386 点（SimPoint 加权，vs `main 6df4312`）：**+8.48%（`12.11 → 13.14 分/GHz`）**，12/12 程序全正零回退（sjeng +23.65%、hmmer +16.00%、perlbench +15.18%、gcc +13.37%、gobmk +13.11%）；`FE.bw 31.23% → 22.85% (−8.38 pp)`。删 22 个旧 16-bank BPU SV 文件，零外部端口改动。RTL 未跑 SPEC，未跑从复位 1.4 亿周期全程指纹对比。见下文「变化」、EXPLORATION EXP-050、[BPU_OPT_PLAN.md](BPU_OPT_PLAN.md) |
| 2026-11-19 | 本行所在提交 / 未动（`55affa0`，trace-model 与 rtl 现在都按固定版本 `FM_REV` 自己构建）/ `8fd0ae3` / `b9fd0df` | EXP-045（LLC / L1I SRRIP）+ EXP-046（选择前查完成周期、完成周期忙表移位寄存器、浮点写通道 21→6、写回总线按通道 13 条）+ 默认配置 = RTL（删 LDQ/STQ 看门狗）+ fdoff 修复。trace-model：门禁 62/62、62/62（关预取）、C 68/68（新基线）；删开关 / 删看门狗前后在 C、标准、RTL 三套程序上周期逐个相同。RTL：`lint_chip` 0；`fm_gate.sh` 67/67、周期与 `ref_cycles.txt`（`regen_refs`/`tm_cycles` 生成）0 处不同、0 个函数模型不一致，不设任何环境变量（`fm_lib.sh`、`build/progs`）；`tests/wb_gate` 0 不一致；Linux 子窗口 s00–s12 共 13 个全部 PASS（约 6400 万条指令逐条检查，PT / UP 指纹全程相等） | 108,907 (2.37)，+0.16% | 290,676 (2.17)，−1.43% | 343,459 (3.05)，−0.06% | RTL = trace-model（`ref_cycles.txt` 67 个程序全部相同；67 个程序里 14 个周期变化，coremark −1.43%、shuixianhua −23%） | 未做整芯片综合；单模块 yosys 通用门（`synth_depth.sh`，`strash;balance;map`）：`isu` 957,032 → 948,874 单元、深度 88 → 89；`prf` 1,077,848 → 679,466 单元（单模块口径，含恒 0 通道的边界效应）、深度 36 → 27 | SPEC06 rv64gc 全量 386 点（eda，PMU 开）：IPC 相对旧 main +1.66%（omnetpp +9.9%、xalancbmk +3.4%、mcf +2.9%，libquantum −1.2%）；其中 EXP-046 本身 +0.01%，SRRIP 是主要来源。PMU 的 TMA 分类修正（重命名 / IDU 停顿算 Backend）同批合入。见 EXPLORATION EXP-045 / EXP-046、WORKFLOW 3.3 |
| 2026-11-19 | 本行所在提交 / 未动（`55affa0`）/ `c795844` / `a26a102` | RTL：`lint_chip` 0；`fm_gate.sh` 67/67、周期与 `ref_cycles.txt` 0 处不同、0 个函数模型不一致；Linux 检查点窗口 s00–s11 共 12 个全部 PASS（约 5900 万条指令逐条检查，PT / UP 指纹全程相等）。trace-model：RVC=0 门禁 62/62（新基线）、RVC=1 C 门禁 67/67（新基线）、67 个程序周期 = RTL；Linux 从复位启动到 `rv64 login:`（无 oops / panic）。SPEC06 rv64gc 386 点（eda 集群）新旧两个配置各跑一遍，0 失败 | 108,732 (2.38)，相对上一版 main 的 100,722 +7.95% | 294,895 (2.14)，相对 286,265 +3.0% | 343,672 (3.05)，相对 343,381 +0.08% | RTL = trace-model：dhrystone 108,732、coremark 294,895、memory-stress-small 343,672（`ref_cycles.txt`，67 个程序几何平均 +1.92%） | 未做整芯片综合（整芯片要一次一个、耗时几十分钟到数小时，这一轮只做了单模块；yosys 通用门深度代理，无工艺库 / 无 WNS）：`bpu_ub_track_ser` 528 → 97、`bpu_ub_look` 75 → 29、`mul_unit` 209 → 90；整机 `back_top` 135 / `front_top` 132 是后来又改了几处之前的数，`ren` 110、`axi_llc` 238 仍超过 100 层（见 TODO） | **有意的性能回退**：67 个程序周期 +1.92%，SPEC06 386 点 IPC 几何平均 −2.15%（hmmer −8.6%），换来压低综合深度的结构（两个 INT 队列、合并访存队列、FLUSH_REG 等，[EXPLORATION.md](EXPLORATION.md) EXP-044）。这一行的固定负载用 rv64 的 `big/dhrystone.bin`、`big/coremark.bin`（RTL 门禁里的版本），与前几行 trace-model 列的数字（另一版程序）不可直接比；相对上一版用 RTL 的 `ref_cycles.txt` 比 |
| 2026-11-17 | 本行所在提交 / 未动 / 未动 / `261bd67` | RTL TLB 口并行化 + first_set 对数深度 + 测试平台自带 fpr.h、构建提速（[RTL_TLB_PAR.md](RTL_TLB_PAR.md)）：`tests/tlb_par` 300 万拍新旧 TLB 核心 0 不一致；lint_chip 0；fm_gate 67/67 周期 0 差异；Linux 窗口 s03/s07/s11 3/3 PASS（trace-model `5b95b35`、function-model `55affa0`），与 rtl main 逐字节相同 | 未动（trace-model 未改） | 未动 | 未动 | 不变：dhrystone 100,722、coremark 286,265、memory-stress-small 343,381（与 `ref_cycles.txt` 相同） | yosys 通用门深度代理（无工艺库 / 无 WNS）：`tlb_mmu` 163 → 67、单元 84,088 → 80,255；`lsu_stlf_match` 139 → 97、`isu_iq_select` 69 → 46（rtl `docs/09-synthesis-report.md` 第 11 节） | 只改结构不改周期；rv64 Linux 测试平台构建 111 s → 89 s |
| 2026-11-17 | 本行所在提交 / 未动 / `e971e79` / 未动 | trace-model 模块整理（[TM_MODULE_CLEANUP.md](TM_MODULE_CLEANUP.md)）：RVC=0 门禁 62/62、RVC=1 门禁 67/67 周期与基线逐个相同；FPR、TB / LSU 轨迹、Linux 检查点、FE_PAIR / FE_IPF 相同；Linux 窗口与 RTL 13/13；Linux 2 亿周期输出与合入前逐字节相同 | 1,526,122 (2.98)，不变 | 未测（rv64 coremark 未建） | 327,170 (3.21)，不变 | 门禁程序不变（`ref_cycles*.txt` 不变） | 未做：RTL 未改 | 源码 30070 → 29096 行，周期不变 |
| 2026-11-17 | 本行所在提交 / 未动 / `83af731` / 未动 | trace-model 结构整理和提速（[TM_GLOBAL_SCHED.md](TM_GLOBAL_SCHED.md)）：RVC=0 门禁 62/62、RVC=1 门禁 67/67 周期与基线逐个相同；FPR、TB / LSU 轨迹、Linux 检查点、FE_PAIR / FE_IPF 相同；Linux 窗口与 RTL 13/13（s03 由 LSU_MS_DATA 修复对齐，之前 12/13）；Linux 2 亿周期控制台文本相同 | 1,526,122 (2.98)，不变 | 未测（rv64 coremark 未建） | 327,170 (3.21)，不变 | 门禁程序不变（`ref_cycles*.txt` 不变） | 未做：RTL 未改 | 模拟速度：dhrystone 7.85 s → 6.3 s |
| 2026-11-15 | 本行所在提交 / `6555530` / `fb5096e` / `4a6397f` | **待补：以最终的 Linux gate 结果为准**；已完成：trace-model（`RVC=0` rv32 默认）周期与 RTL 逐个相同，rv32 逐条对比 `fm_gate.sh` **64/64**（67 个程序的表里新增 3 个 directed：`memspec_data` 5598、`memspec_addr` 3086、`memspec_pf` 2700，各自模型周期 = RTL 周期、逐条检查 0 不一致）、与提交的 `ref_cycles.txt` 逐个相同；rv64：directed 3/3 周期相等（`scripts/ref_cycles_rv64.txt`），rv64gc Linux 检查点窗口 **18/18**（`linux_segments_cmp.sh`，每窗 200 万周期，PT / UP 指纹全部相同，逐条检查 0 不一致）；从复位的 Linux（rv64gc，140M 周期的 gate，**最终版本只跑到 3400 万周期就停了**）：**到 3000 万周期为止 PMU 一级事件逐区间完全相同；第 3000–3050 万周期区间开始有误差（提交指令数 模型 684,700 / RTL 686,688，+0.29%），原因未查，这是已知误差**，逐条功能检查到 3400 万周期 0 个不一致 | 116,399（−0.002%） | 282,735（+0.04%） | 325,458（不变） | 与 trace-model 逐个相等（见左） | 未做（只改 RTL 行为和模型，没有新综合）；`lp_wb` / `lp_wake` 各改一行条件 | **RVC=1 / rv64gc 的 RTL 与 trace-model 逐周期对齐（Linux 到约 3000 万周期逐区间相同，之后有已知误差）**：见下面的「变化」。rv32 `RVC=1`（`FP=0`）的整核测试平台起不来，在没有改动的 HEAD 上同样如此（已存在的遗留，已登记，没有修） |
| 2026-11-13 | 本行所在提交 / `c602794` / `74e6827` / 未动 | trace-model：`RVC=0`（默认）gate 64/64 周期与基线逐个相同；`RVC=1`：不带 C 的 64 个程序 0 个 difftest 不一致（周期约 ±5%）；C 编译的 cpu-tests 62/62（`results/baseline/baseline_c.csv`，`scripts/run_gate_c.sh`），function-model 的 `gen_rvc.py` 压力测试（全部 16 位编码、访存、跳转、跨行跨页）0 不一致；C 编译 + `RVC=1` 对 不带 C + `RVC=0` 周期几何平均 0.920（52 个程序）；function-model：`rvc.h` 沿用编译开关 | 116,401（不变） | 282,616（不变） | 325,458（不变） | 未动 | 未做（只改 trace-model） | **EXP-038 S0–S2 合入**：C 扩展在 trace-model 的前端（`RVC=1`，默认关）：slot 宽度参数化（16 个 2 字节 slot）、预译码展开和指令起点链、`lastHalf`、有空洞的有效位、`is_rvc` 到后端、BPU 训练和 RAS 按指令长度。还没做：两级预测校验、跨 cache line 的取指延迟、PMU 和带 C / 不带 C 对比、rv64 的 `RVC=1`、RTL |
| 2026-11-13 | 本行所在提交 / `6bf6c59` / 未动 / 未动 | function-model：`RVC=0`（默认）回归不变：rv32 53/56、rv64 52/54（不通过的是已知平台差异）、F/D 3/3、官方 rv32uf/ud 21/21、快速路径与单步路径状态摘要（含 CSR）在 rv64g Linux 前 1 亿条指令逐块一致；`RVC=1`：定向 RVC 测试（全部 16 位编码、访存、跳转、跨行跨页、Sv39 缺页）rv32 / rv64 与 Spike 逐条一致、官方 rv32uc / rv64uc、cpu-tests 带 C rv64 47/52 rv32 46/51（不通过的是测试源码假定 4 字节指令或已知平台差异）、带 C 的 rv64 Linux（内核 + OpenSBI）到 `rv64 login:` 前 2.5 亿条指令与 Spike 逐条一致、快速路径与单步状态摘要在 Linux 前 1 亿条指令和 58 个程序上一致 | 未动 | 未动 | 未动 | 未动 | 未做（只改 function-model） | **EXP-037：C 扩展（function-model）合入**（`RVC=1`，默认关）：半字取指、16 位展开、跨页第二半字缺页、`misa.C`、`RefCpuStepInfo.inst_len`、快速路径支持压缩指令（带 C 的 Linux 15 亿条指令 30 s → 4.6 s）。trace-model / RTL 的 C 还没做 |
| 2026-11-13 | 本行所在提交 / `0323bd9` / `195dad4` / `15af4b4` | trace-model：rv32 gate 64/64（11 个程序因 EXP-035 周期变化，基线已重生成）、`fp_check` 32/64 与基线相同、`EXU_SHADOW` 与冻结旧 Exu 逐周期 0 不同、`LSU_SEQ_POISON` 构建一致；RTL：与模型逐周期相同（smoke、dhrystone、coremark、pf-stress、fd-*、FP 内核、rv64），`isu_wb_gate` 单元测试 0 不一致；**rv64g Linux 从复位到 `rv64 login:`，`fptest: PASS`，171,931,468 条指令逐条对比 function model 0 不一致（2.2 亿周期，816 次中断）**；function-model：F/D 的 rv32 + rv64 与 Spike 一致，rv64g Linux 到登录 `fptest: PASS` | 116,401（−0.32%） | 282,616（−0.80%） | 325,458（0.00%） | 与模型相同 | 未做（FP 单元是 DPI softfloat，不可综合；FP 寄存器堆和 FP IQ 的面积还没估） | **EXP-031…036 合入（均为快进，已推送）**：删 Zfinx、rv32/rv64 标准 F/D 为默认（`FP=1`）；EXP-032/033 FP 写口与 fcsr 串行化；EXP-034 Exu 按单元重写；EXP-035 写回口发射时预约（trace-model + RTL）；EXP-036 仿真提速约 24%（周期不变）；RTL 标准 F/D（S1–S6）与 rv64g Linux。已知回退：coremark / dhrystone 周期略降是 EXP-035 的建模修正（−0.8% / −0.3%），不是性能优化 |
| 2026-11-12 | 本行所在提交 / `e0078bc`→`cdcb74d` / `4cf9b6b`→`2c1d166` / 未动 | trace-model：`FP=0` rv32 gate 62/62 周期与基线逐个相同（该检出能构建的 62 个，`matmul_soft`/`mersenne`/`string` 构建失败，与改动前一致）；rv64 的 55 个整数程序 `FP=0` 与 `FP=1` 周期逐个相同；`FP=1`：26 个 FP 程序（含官方 rv64uf/ud）跑到结束，`scripts/fp_check.sh` 全过 | 116,774（0.00%） | 284,902（0.00%） | 325,458（0.00%） | 未动 | 未做（只改 function-model 的 API 和 trace-model，RTL 没变） | **EXP-030：rv64 F/D 的 trace-model 第一版合入**（`FP=1` 编译开关，默认关）：FP 重命名、FP 发射队列和三个 FP 发射口、FMA/MISC/FDIV/I2F 单元、FP load/store 走现有 LSU、FS/SD；延迟等参数是未标定的起始值；RTL 浮点未做 |
| 2026-11-12 | 本行所在提交 / `e0078bc` / 未动 / 未动 | function-model：`FP=0` 默认构建不变（rv64 整数程序 52/54 与 Spike 一致，另 2 个是已知平台差异；rv32 对拍结果与改动前相同）；`FP=1`：定向 F/D 测试（35 万条指令）、FS/保留编码测试、编译器生成的浮点代码、官方 riscv-tests rv64uf/ud 23/23 与 Spike 逐条一致 | 未动（周期模型没改） | 未动 | 未动 | 未动 | 未做（只改 function-model，RTL 没变） | **EXP-030：rv64 F/D（function-model）合入**（`FP=1` 编译开关，默认关）；顺带修 `csrrwi csr,0` 不写 CSR；检查点版本 5。trace-model / RTL 的浮点还没做 |
| 2026-11-12 | 本行所在提交 / `b388f39` / `ccc2d0c` / `8dbb7cd` | XLEN=32（默认配置不变）：trace-model 三个大程序周期与上一行逐个相同；RTL `lint.sh`/`lint_chip.sh` XLEN=32 和 64 两种都 0 警告，`fm_gate.sh` 69/69、周期与 `ref_cycles.txt` 0 处不同、0 个函数模型不一致；rv32 `memory-stress` 230.8 万周期、745 万条指令逐条对比 0 不一致；**RTL Linux 从复位到 `rv32 login:`**（2 亿周期上限内，1.6 亿条指令，740 次中断，0 不一致）。rv64（`XLEN_BITS=64` 副本）：53 个 cpu-tests 逐条对比通过，与合并后模型（`LSU_PIPE_NOWD=1`，RTL 标定所用）周期 53/53 相同（先前看到的 `crc32` 2306 vs 2259、`memory-stress` 2,260,146 vs 2,260,326 是模型没加 `LSU_PIPE_NOWD=1`、63 周期看门狗重发 store 造成的，不是 RTL 偏差）；**RTL Linux 从复位到 `rv64 login:`**（1.3 亿周期、1.29 亿条指令，5161 个设备值采纳，474 次中断，0 不一致） | 116,774（0.00%） | 284,902（0.00%） | 325,458（0.00%） | 见 ref_cycles（69 个程序逐个相等） | yosys 通用门代理（rv32 → rv64，24 个受影响模块，`rtl/docs/09-synthesis-report.md` 第 10 节）：18 个互不重叠的模块合计 1610468 → 2111073 单元（+31%），`prf` +82.9%、`bpu` +54.3%、`tlb_mmu` +31.6%、`mul_core` +276%；`icache` / `dcache_wb` / `dcache_resp` 基本不变；加法链深度被通用映射高估；rv64 `dcache_bank` 超内存看门狗未出数；工艺库、WNS：**未做**（XLEN=32 本身的逻辑不变） | **EXP-029：rv64imab 迁移合入**（`XLEN_BITS` 配置包参数，默认 32）；`back_top.sv` / `exu.sv` / `soc_top.sv` 为手改，重新生成会丢位宽（见 TODO） |
| 2026-11-11 | 本行所在提交 / `7b8ee1b` / `a11b1ca` / `a905acd` | trace-model：开关默认关（`35b3af4`）gate 64/64 与旧基线逐个相同（只有 `software-interrupt-vectored` 2,254 → 2,356，来自删掉的非缓存窗口）、8 个大程序与标准周期相同；默认开（`a11b1ca`）gate 64/64 + load-store 全部 difftest Success、0 个 TB_CHECK 不一致，`baseline.csv` 32 个程序变化（−5.2% … +6.0%）；trace-model Linux 从复位到 `rv32 login:`，0 不一致。RTL：`lint.sh`/`lint_chip.sh` 两种配置 0 警告；不带 `-D` 生成的 `ttg_cfg_pkg.sv` 与实验紧凑包逐字节相同；`fm_gate.sh` 69/69，周期与 `ref_cycles.txt`（`LSU_PIPE_NOWD=1`，37 个程序变化）0 处不同，0 个函数模型不一致；`ROB_COMPACT=0` 时 fm_gate 69/69、周期与模型逐个相等；**RTL Linux 从复位一次连续跑到 `rv32 login:`**（不分段，本机 4 线程 tb，逐提交与函数模型对比，约 2 小时 19 分钟），0 不一致 | 116,774（+1.82%） | 284,902（+0.59%） | 325,458（−1.20%） | 见 ref_cycles（69 个程序逐个相等） | yosys 通用门面积代理（`synth_depth.sh`，相对数字，无工艺库、无时序；单元 / 深度，行式 → 紧凑，实验版本上测）：`rob` 316,758 / 46 → 352,903 / **53**（+11.4% / **+15%，超过 5% 深度判据**，作为例外记录，降深度的办法见 TODO）；`dispatch` 78,558 / 46 → 81,650 / 47（+3.9%）；对照行式 ROB192 `rob` 342,475 / 49（+8.1%，未计 ROB 编号加宽的代价）；工艺库、WNS：**未做** | **EXP-028：紧凑 ROB**（按序分配、前缀提交最多 8 条，ROB 仍 128 项）+ 寄存器版 BPU 提交额度，默认开；同批清理：删掉剩下的非缓存 RAM 窗口及其通路、前端 PMU `FEO_*` 事件、删 `altpcpn`/`sc_used` 存储、删 A 组开关（TAGE 参数扫描、SC、`BPA_NOTC` 目标缓存、`CMTSYNC`、调试打印）。**SPEC 全量 580 点（快速预热，`PMU=1`，本机）对本批行式 ROB：12 个程序几何平均 IPC +2.74%，12 个程序全部提升**（astar +5.07%、omnetpp +5.00%、hmmer +4.55%、h264ref +3.50%、mcf +2.91%、sjeng +2.89%、xalancbmk +2.51%、libquantum +1.64%、perlbench +1.55%、bzip2 +1.33%、gcc +1.32%、gobmk +0.77%）；分数 **11.23 → 11.53 分/GHz**（官方参考时间换算；11.23 是合入前 main 的实测，与之前估的 11.22 一致）。**已知回退**：分支密集短循环被 BPU 更新带宽卡住，gcc 4 个短点约 −37%（权重合计约 0.03）、dhrystone 周期 +1.8%、coremark +0.6%（见 TODO）。RTL 没跑 SPEC |
| 2026-11-11 | 本行所在提交 / `7b8ee1b` / `07d567c` / `de8d0aa` | trace-model gate 64/64 全部 difftest Success（3 个程序周期变化，`baseline.csv` 更新：fence-i-self-modify 1405 → 1407、recursion 2876 → 2878、vm_pagefault_test 19060 → 19212）；8 个大程序与标准周期逐个相同；trace-model Linux 从复位到 `rv32 login:`，0 不一致；RTL `lint.sh`/`lint_chip.sh` 0 警告；`fm_gate.sh` 69/69，0 个函数模型不一致，周期与 trace-model（`LSU_PIPE_NOWD=1`）0 处不同；RTL Linux 13 段（s01–s13，本机 13 个并行，每段 1600 万周期，逐提交与函数模型对比）13/13 通过，每段检查 692 万到 2424 万条指令，0 不一致 | 114,685（0.00%） | 283,240（0.00%） | 329,424（0.00%） | 见 ref_cycles（69 个程序逐个相等，3 个程序随模型变化） | 未做：只把 `lsu_pkg::is_mmio_addr` 的可缓存比较从 3 段减为 2 段（少两个 32 位比较器），其余是 tb 和配置包，判断不值得单独综合 | **EXP-027：删除 0x87f00000 非缓存窗口**（SoC DMA/cache 一致性的遗留，Linux 把这段当普通内存分给用户程序，普通 load 走 MMIO）。SPEC 全量 580 点（快速预热，本机，对 main + write buffer）几何平均 IPC **+10.75%**（h264ref +137.5%、hmmer +34.7%、perlbench +6.3%，其余 ±0.3%），0 个点变慢；用官方参考时间直接换算分数 10.06 → 11.14 分/GHz（当前 main 含 ITT 10.13，删窗口后估约 11.22）。另：PMU 的 TMA 缺失标记修成 `bitset<ROB_NUM>`（周期不变） |
| 2026-11-10 | 本行所在提交 / `7b8ee1b` / `e84e53a` / `1c0d110` | trace-model gate 64/64（63 + `itt-dispatch`；原 63 个程序周期无变化）；RTL `bpu` 目录 lint 0 警告；`fm_gate.sh` 69/69（68 + `itt-dispatch`），周期与 trace-model（`LSU_PIPE_NOWD=1`）0 处不同，0 个函数模型不一致；Linux 13 段（s01–s13，服务器 4 线程，每提交逐条对比）13/13，每段检查 690 万到 2420 万条指令，0 不一致；从复位连续启动（服务器单进程，逐提交对比）走到 `rv32 login:`，0 不一致 | 114,685（+0.23%） | 283,240（−0.01%） | 329,424（0.00%） | 见 ref_cycles（69 个程序逐个相等；coremark 283,240、dhrystone 114,685、itt-dispatch 222,445） | yosys 通用门面积代理（相对数字，无工艺库、无时序；单元 / 深度，main → 本次）：`bpu` 237,174 / 141 → 242,631 / 141（+2.3%）；`front_pred_path` 243,614 / 142 → 250,251 / 144（+2.7% / +1.4%）；`bpu_main_sel` 20,004 / 70 → 23,904 / 69；`bpu_btb_sel` 829 / 34 → 1,128 / 33；深度都在 5% 判据内。ITT 存储 86 Kb → 64.5 Kb | **EXP-025：间接跳转目标表 1 张 256 项 → 3 张 × 64 项**（TAGE 历史表 1/2/3，13/32/119 位，取最长历史命中，`CFG_ITT_H` 取 1,2,3、`CFG_ITT_SIZE=64`）。SPEC 全量 580 点（快速预热，服务器，对 main）几何平均 IPC **+0.67%**（sjeng +3.77%、perlbench +3.16%、h264ref +0.53%、gcc +0.38%，其余 8 个程序 −0.02%~+0.08%）；58 个点变化超过 2%，3 个点低于 −2%（perlbench sp13 −4.5%、gcc sp29 −3.8%、xalancbmk sp31 −3.3%，未查）。RTL 没跑 SPEC |
| 2026-11-09 | 本行所在提交 / `7b8ee1b` / `55c9f64` / `ef6da65` | trace-model gate 63/63（基线重生成，17 个程序周期小幅变化，全部 difftest Success）；旧配置回归（`LSU_PIPE_WBUF=0 LSU_PIPE_DRAIN=3`）仍可用；RTL `lint.sh`/`lint_chip.sh` 0 警告；`fm_gate.sh` 68/68（67 + `directed/memspec_vio`），周期与 trace-model（`LSU_PIPE_NOWD=1` 表）0 处不同，0 个函数模型不一致；Linux 13 段（s01–s13 接力，每段 1600 万周期，本机 4 路并行）13/13 通过，每段检查 690 万到 2420 万条指令，0 不一致；`ttg_cfg_pkg.sv` 与模型配置一致 | 114,418（+0.10%） | 283,270（0.00%） | 329,424（+0.19%） | 见 ref_cycles（67 个程序逐个相等） | yosys 通用门面积代理（相对数字，无工艺库、无时序，`SYNTH_LIGHT=1 SYNTH_MEM=1`；面积 / 深度，main → 本次）：`lsu` 1,276,574 / 130 → 1,279,658 / **125**（面积 +0.2%，深度 −4%）；`lp_stq` 158,221 / 72 → 161,937 / 74；`lp_drain` 86,260 / 83 → 68,767 / **97**（**模块级深度 +17%，超过"没有模块比 main 深 5% 以上"的判据**，但包含它的 `lsu` 整体比 main 浅，`lp_drain` 不在 `lsu` 的关键路径上，作为例外记录）；新增 `lp_wbuf` 59,014 / 89；`dcache_s1` 12,970 / 45 → 16,101 / 28，`dcache_mshr` 110,574 / 114 → 83,386 / 101，`dcache_resp` 14,188 / 34 → 17,418 / 22，`dcache_wb` 20,563 / 69 → 26,673 / 57；`dcache_arr` 两边都综合失败，没有数据；新增触发器（按 RTL 声明统计的位数，不是综合结果）：write buffer 4 项 × 174 位 + 年龄矩阵 16 位 = 712，DCache 第二字通路 `slot` / `rty` / `resp` 各 3 口 × 40 位 = 360，STQ 每项"已处理"1 位加跟随者标记 7 位 × 64 = 512，合计约 1,584；工艺库、约束频率、WNS：**未做** | 已提交 store 的 write buffer（EXP-024）：4 个条目、每条目最多 2 个同 cache line 的 store，STQ 内分组（store 仍留在 STQ 里等响应，load 的转发不变）；一个条目是一个 DCache 请求，第二个 store 走第二字通路；排空口 3 → 2；决策只读寄存器，插入在决策之后。**SPEC 全量 580 点（快速预热 100 万条指令，预取开，本机并行 8，580/580 成功，无失败点）对合入前 main（`integ`，同样口径，逐点周期与本机 main 配置复现 58/58 相同）：12 个程序几何平均 IPC +0.68%**（按 SimPoint 权重加权同为 +0.68%）：gcc +4.80%（加权 +4.37%）、hmmer +1.45%、gobmk +1.07%、h264ref +0.30%、libquantum +0.19%、perlbench +0.12%、astar +0.12%、mcf +0.05%、bzip2 +0.02%、omnetpp +0.03%、sjeng +0.03%、xalancbmk +0.03%；最好点 gcc +47.92%，最差点 h264ref −6.25%、bzip2 −5.88%、perlbench −4.61%，低于 −2% 的点 6 个、低于 −5% 的点 2 个（这些点对时序敏感，个别点有几个百分点的随机波动，没有逐个分析）；估算分数 10.46 → 约 10.53 分/GHz（参考时间没有核对官方表，起点沿用上一行的近似值）；**RTL 没有跑 SPEC**，30 点精确预热没有跑；参数扫描只在 5 个点上做。另：12 个程序各取权重最高的点（精确预热）是 +2.85%，偏高，原因是 gcc 的 sp42 是极端点。与 `exp/store-wb` 之前的 in-drain 配对版本（+7.22%，`lp_drain` 深度 110、`lsu` 169）相比，这版收益略低、深度达标。Linux `s04` 在第一版配对 RTL 上有 1 处 `sc.w` 不一致，本版 13/13 通过，原因没有定位（见 TODO） |
| 2026-11-09 | 本行所在提交 / `7b8ee1b` / `31bfb03` / `29e535b` | trace-model gate 64/64（63 + load-store，默认配置，全部 difftest Success、0 个 TB_CHECK 不一致；基线重生成，63 个程序周期变化，最大 −51%）；旧配置回归（`LSU_MEMSPEC=0 FE_RFAST=0`）对 main 基线 63/63 逐个相同，dhrystone 123,519、coremark 293,286 与 main 相同；trace-model Linux 从复位到 `rv32 login:`；RTL `lint.sh`/`lint_chip.sh` 0 警告（默认与 `LSU_MEMSPEC=0` 各一遍）；`fm_gate.sh` 68/68（67 + `directed/memspec_vio`），周期与 trace-model（`LSU_PIPE_NOWD=1`）68/68 逐个相等；kill switch（`LSU_MEMSPEC=0`，`FE_RFAST` 仍为固定值 15）68/68，周期 68/68 相等；Linux 13 段（s01–s13，服务器 4 线程，每提交逐条对比）13/13、0 不一致；SPEC 全量 580/580 成功（快速预热，`PMU=1`，对同一服务器上构建的 main `7f8456e`），12 个程序 SimPoint 加权几何平均 IPC **+11.02%**，最差点 −4.3% | 114,299（−7.46%） | 283,280（−3.41%） | 328,606（−0.98%）；RTL 参考表（`LSU_PIPE_NOWD=1`）里该程序是 328,787 | RTL 与 trace-model（`NOWD=1` 表）逐个相等：dhrystone 114,299、coremark 283,280、memory-stress-small 328,787 | yosys 通用门面积代理（`synth_cfg.sh` 轻量 ABC 数单元，`synth_depth.sh` 平衡 ABC 数深度，相对数字，无工艺库、无时序），main `edf9d3b` → 合并后：`lsu` 969,441 → 894,874（−7.7%，深度 131 → 128）、`bpu` 223,476 → 202,257（深度 149 → 141）、`front_pred_path` 226,649 → 208,401（深度 134 → 142，**+6%，超过 5% 判据**）、`rob` 201,672 → 206,695、`dispatch` 91,937 → 92,518、`pre_idu_queue` 49,795 → 54,186；工艺库、WNS：**未做** | EXP-019/020/023：LSU 访存相关推测（`LSU_MEMSPEC`，默认开，等待表 + 值路径 `LSU_MS_DATA`）+ 前端快速通路（`FE_RFAST=15` 固定、`FE_BFAST` 默认关）；SPEC 估算分数 9.42 → 约 10.46 分/GHz（**参考时间未核对官方表**；9.42 是最后一次记录的分数（EXP-015），EXP-016/017 在其后合入，起点只是近似）；SPEC 只在 trace-model 上跑过，**RTL 没跑 SPEC** |
| 2026-11-08 | 本行所在提交 / `7b8ee1b` / `7f8456e` / `edf9d3b` | trace-model gate 63/63（与基线逐个相同）；7 个大程序（dhrystone、coremark、memory-stress、memory-stress-small、smc-div、smc-addi、pf-stress）周期与 main `cefaee4` 的构建逐个相同；quick SPEC 178 点（`PMU=1`）与 main 构建**逐点周期相同**（总周期 1,842,054,299，0 个 difftest 不一致）；trace-model Linux 到 `rv32 login:`；RTL 生成的 `pmu_ev_pkg.sv`、`ttg_cfg_pkg.sv` 与 main **逐字节相同**；RTL 中间版本（PMU 包 68 个事件）`lint.sh`/`lint_chip.sh` 0 警告、逐条对比 67/67、周期与 `ref_cycles.txt` 0 处不同 | 123,519（0%） | 293,286（0%） | 331,844（0%） | 不变（RTL 逻辑与 PMU 包都没改） | RTL 逻辑没改，**未重做综合**；中间版本把 2 个 model-only 事件放进 RTL 包会使 `pmu` 11,465 → 11,627 个单元（+1.4%，事件选择多路器变宽），因此改为让生成器跳过它们；工艺库、WNS：**未做** | EXP-016：后端资源 DSE（无配置默认值变化）：新增 `CFG_LDQ_SIZE`（默认 64）、PMU 的 model-only 事件 `SLOT_FE_OTHER_NOPREG/NOBRTAG`、`scripts/dse/`；RTL 只改 `gen_pmu_pkg.py`（跳过标 `// model-only` 的事件） |
| 2026-11-08 | 本行所在提交 / `7b8ee1b` / `cefaee4` / `121324c` | trace-model gate 63/63（基线重生成，20 个程序周期变化，全部 difftest 通过）；RTL 逐条对比 67/67，周期与 trace-model（`LSU_PIPE_NOWD=1` 表）0 处不同；`lint.sh`/`lint_chip.sh` 0 警告；`ttg_cfg_pkg.sv` 与模型配置一致；trace-model、RTL Linux 均到 `rv32 login:`，RTL 逐条对比 0 不一致；SPEC 全量 580/580 成功（快速预热）、30 点精确预热 30/30 成功 | 123,519（−0.13%） | 293,286（−0.70%） | 331,844（+0.16%） | 见 ref_cycles | yosys 通用门面积代理（`synth_cfg.sh`，相对数字，无工艺库、无时序）：`isu` 全 8 入队 1,039,339 → 843,910 个单元（−18.8%）；工艺库、WNS：**未做** | EXP-017：每个 IQ 的入队宽度 INT7/LD6/STA4/STD4/BR5（原来全是 8，写口 40→26）；SPEC 全量几何平均 IPC −0.05%、30 点精确预热 −0.48%（mcf −1.26%、perlbench −1.53%） |
| 2026-11-08 | 本行所在提交 / `7b8ee1b` / `1d08b15` / `cc90cc2` | trace-model gate 63/63（预取开、关）；旧设计开关串 63/63 与 `legacy_lsu_baseline*.csv` 逐个相同；`LSU_PIPE_NOWD=1` gate 63/63；小 LLC 5/5；RTL 逐条对比 67/67（预取开、关），周期与 trace-model（NOWD=1 表）0 处不同；`lint.sh`/`lint_chip.sh` 0 警告；`ttg_cfg_pkg.sv` 与模型配置逐字节相同；RTL、模型 Linux 均到 `rv32 login:`，RTL 逐条对比 0 不一致 | 123,684 | 295,351 | 331,311 | 见 ref_cycles | 未测 | |
| 2026-11-07 | 本行所在提交 / `7b8ee1b` / `a7960e4` / `5829f07` | trace-model gate 63/63（PMU 关、`PMU=1` 各一遍，都与基线逐个相同）；RTL 逐条对比 67/67，预取开、关（`PF_EN=0`）周期都与参考逐个相等（0 个不同），0 个函数模型不一致；`lint.sh`、`lint_chip.sh` 0 警告；Linux 13 段（s01–s13 接力，每段 1600 万周期，s01–s04 本机、s05–s13 服务器 4 线程）逐条对比 13/13 通过、0 不一致；PMU 的 RTL 与 trace-model 在 dhrystone、coremark 上 18 个 tier-1 事件总数逐个相等；`tests/pmu/run.sh` 30 万拍随机 0 不一致 | 161,183 (1.811)，0% | 251,535 (2.140)，0% | 334,635 (3.232)，0% | 与 trace-model 相同（67 个程序逐个相等，预取开、关都是） | yosys 通用门面积代理（相对数字，无工艺库、无时序，`SYNTH_LIGHT=1 SYNTH_MEM=1`）：`dispatch` 86,637 → 86,637（不变）；新增 `pmu_ev_core` 518 个单元；`pmu` 计数器块（8 个 HPM）约 10.2k 单元，计数器存储按 `$mem` 未计触发器（估计约 750 个触发器），**计数器块没有接到任何东西，综合器会把它整个删掉**；工艺库、WNS：**未做** | PMU（EXP-013）：trace-model `PMU=1`（默认关）51 个事件、TMA 一二级、逐 PC 堵塞画像、相位；RTL 事件总线 tier 1（18 个事件含 TMA 一级）+ 计数器块（未接 CSR，软件不可见）；周期不变 |
| 2026-11-07 | 本行所在提交 / `7b8ee1b` / `b301161` / `9279125` | trace-model gate 63/63（基线更新，预取开；`PF_ENABLE=0` 对 main 基线 62/62 相同，另加 pf-stress）；RTL 逐条对比 67/67，预取开、关两种配置周期都与 trace-model 逐个相等（0 个不同），0 个函数模型不一致；`lint.sh`、`lint_chip.sh` 0 警告；Linux 分 13 段（检查点 s01–s13 接力，每段 1600 万周期，每段检查 630 万到 2400 万条指令，不是一次连续运行、微架构每段冷启动，周期不比较）在**合并后的树**（预取开 + move elimination，rtl `9279125`）上逐条对比，13/13 通过、0 不一致；SPEC full 580/580 点（fast warmup），无 difftest 不一致 | 161,183 (1.811)，−0.52% | 251,535 (2.140)，−0.34% | 334,635 (3.232)，−3.65% | 与 trace-model 相同（67 个程序逐个相等） | yosys 通用门面积代理（相对数字，无工艺库、无时序；合并后的树，2026-11-07 重测，`SYNTH_LIGHT=1`）：新增 `dcache_pf` 4,172 个单元、422 个触发器；`dcache_mshr`（`SYNTH_LIGHT=1 SYNTH_MEM=1`）main 96,296 → 96,931 个单元（+635，+0.7%）、触发器 748 → 764；L1D 阵列新增 pf 位 256×4 = 1,024 个触发器（未重测）；净增触发器约 1,460；工艺库、约束频率、WNS：**未做** | L1D 数据预取器 h1（EXP-009）：单条全局步长表项、度 8、距离 2、页内、LLC-only next-line 引擎、无 PC、无限流；默认开（`PF_ENABLE` / RTL `PF_EN`）。SPEC full 12 个程序几何平均 +8.3%，估算分数 8.12 → 约 8.80 分/GHz（SimPoint 权重，对精确 PF 关基线，分数 = 旧分数 × 加速比，参考时间未核对官方表；libquantum +96.3%、mcf +10.8%、gcc +9.0%、bzip2 +6.2%，gobmk/hmmer/sjeng −0.8%/−1.6%/−3.0%）；低于 −10% 的 5 个点（omnetpp sp22 −40.7%、sp7 −22.8%，gcc sp38 −29.9%，xalancbmk sp34 −22.2%、sp15 −11.8%）是已知回退，原因是 LLC-only 引擎；节流、MSHR 预留、时间片对抗三个修复中，节流（几何平均 +7.2%）和时间片对抗（+7.7%）在全量上都不如 h1（+8.2%，三方案都有结果的 579 个点同口径），MSHR 预留只在抽样点上测过、也没有同时保住 mcf，按负责人决定保持 h1 合入 |
| 2026-11-06 | 本行所在提交 / `d40c588` / `767c25f` / `1e5d656` | trace-model gate 62/62（基线更新，7 个程序周期变化，全部 difftest Success、`ME_CHECK=1` 0 次断言）；RTL 66 个程序逐条对比 66/66，周期与 trace-model 逐个相等（开、关 `MOVE_ELIM` 两种配置都跑了：关闭时与原 `ref_cycles.txt` 逐个相等）；Linux 从复位启动到 `rv32 login:`：trace-model 与 RTL（`SOC_TB_FM=1`，每条提交逐条对比，0 不一致、无断言；登录后手动结束，没有总周期数和"N 条已检查"汇总）都通过；quick SPEC 129 个点无 difftest 不一致 | 162,033 (1.802)，0 | 252,400 (2.133)，−1.15% | 347,305 (3.114)，0 | 与 trace-model 相同 | yosys 通用门面积代理（相对数字，无工艺库、无时序）：`ren` 206,228 → 227,720 个单元（+21.5k，+10.4%；`arch_cnt` 映射成触发器后 → 231,029，+24.8k，+12.0%，触发器 +384），`dispatch` 86,637、`rob` 201,672 不变；`ren` 最长组合路径 63 → 130 级（通用门级数，不是时序）；工艺库、约束频率、WNS：**未做** | mov 消除（EXP-012），默认开启。quick SPEC 6 个程序几何平均 IPC 1.550 → 1.551（+0.06%）：收益在噪声量级，按负责人决定合入 |
| 2026-11-06 | 本行所在提交 / `d40c588` / `88e5254` / `b19a181` | trace-model gate 62/62（基线更新，63 个程序周期全部变化）；RTL 66 个程序逐条对比 66/66，周期与 trace-model 逐个相等；Linux 从复位启动到 `rv32 login:`：trace-model 与 RTL（每条提交逐条对比，无断言、0 不一致；登录后手动结束，没有总周期数和"N 条已检查"汇总）；SPEC full 580 点无失败、无 difftest 不一致 | 162,033 (1.802)，+7.7% | 255,335 (2.108)，+9.4% | 347,305 (3.114)，+83.6% | 与 trace-model 相同 | yosys 通用门面积代理（相对数字，无工艺库、无时序）：`axi_llc` 489,436 → 522,758 个单元（+33.3k）、触发器 22,324 → 30,584；`lsu_dc_req_st` 86,150 → 62,755（−23.4k）；净约 +9.9k 单元（不到整机的 0.2%）、触发器 +8.3k（约 +4.6%）；`mem_top` 太大综合超时，`TICKS=1` 常量化的效果未测到；工艺库、约束频率、WNS：**未做** | DRAMsim3 DDR（EXP-006）：去掉 16 倍 AXI 子系统分频、核心 1 GHz、DDR4-3200 加 60 ns 非核心延迟，见下文“变化”。SPEC full 几何平均 IPC 1.396、估算 8.12 分/GHz；quick 6 个程序 IPC 2.204 → 1.550（−29.7%）。周期变多是因为旧基线靠分频把 DRAM 做快了约 13 倍 |
| 2026-11-05 | 本行所在提交 / `d40c588` / `08e9cfe` / `52d2b84` | trace-model gate 62/62（基线更新，25 个程序周期变化）；RTL 66 个程序逐条对比 66/66，周期与 trace-model 逐个相等；Linux 从复位启动到 `rv32 login:`：trace-model（约 7–8 千万周期）与 RTL（全程逐条对比，0 不一致，约 3.6 小时）| 150,427 (1.941)，−0.27% | 233,515 (2.305)，+2.87% | 189,128 (5.718)，0 | 与 trace-model 相同 | yosys 通用门面积代理（`rtl/docs/09-synthesis-report.md` 第 9 节）：受影响的 14 个模块 3,723,024 → 2,117,024 个单元（约 −161 万，整机约 17%），触发器 123,595 → 73,873；整机推算未按新配置重做；工艺库、约束频率、WNS：**未做**（没有工艺库和时序流程，见 TODO） | 第 3 批面积配置（EXP-005），见下文“变化”。quick SPEC（6 个程序）IPC 2.216 → 2.204（−0.5%）；coremark 变慢来自在飞分支 32 |
| 2026-11-04 | `6210e46` / `4f99467` / `41a5cdd` / `dc46f6d`（rtl 工作区有未提交修改） | gate 62/62；RTL gate+vm 64 个程序逐条对比一致 | 150,838 (1.935) | 226,991 (2.371) | 189,128 (5.718) | 待补 | **未做**：还没有综合流程（见 README"下一步"第 2 条） | 起始记录（本表从这里开始） |

## 变化

### 2026-11-23 EXP-058 硬件忠实版 LLC Bingo 4KB 空间预取器（`axi_llc_bingo`）

- **配置变化**：`AXI_LLC` 默认开启 `LLC_BINGO=1` 与既有 `LLC_BOP=1` 协同工作，在途预取 MSHR 上限 `BOP_INF` 由 `4` 提至 `8`（`bop_q` 严格优先于 `bingo_q`）；`include/config.h` 无改动。
- **设计改动与 `axi_llc_bingo` 降深度（`163 → 48` 层）**：
  - **12-bit 负载 `pc_hash` 真实边带通路**：由 `RealDcache / MSHR`（`dcache.sv` / `dcache_mshr.sv`）在 L1D miss 分配 MSHR 时捕获 `(pc>>1)^(pc>>13)^(pc>>21)` 低 12 位，经 `mem_axi` → `axi_interconnect` / `axi_ic_stage` 透传至 `axi_llc_lookup` 供 Bingo 训练与预测使用。
  - **硬件忠实 Bingo 4KB（`BingoHw.h` / `axi_llc_bingo.sv` / `axi_llc_bingo_agt.sv` / `axi_llc_bingo_pht.sv`）**：32 项 FIFO 过滤表 FT、32 项 31-bit tree-PLRU 全相联累积表 AGT、4 项提交队列 `cmt_q`、3 状态 1RW SRAM FSM（`ST_IDLE` / `ST_PRED` / `ST_CMT`）驱动 4 路 `PHT_L`（`256×4×138b`，3-bit tree-PLRU）与 `PHT_S`（`128×4×133b`，相对偏移）、`ttg_popcount` 密集流过滤（`>= 48` 跳过）、无乘法器周期准确率节流器（256 发窗口 `< 26` 命中即 `< 10.16%` 降为 1/8 试探 `deg=2`）、1 候选/拍发射器与 16 项去重队列 `bingo_q`。总存储约 `26.75 KiB`（`25.56 KiB` 1RW SRAM + `~1.2 KiB` FF，占 4 MiB LLC `0.65%`）。
  - **桶形移位优化**：将 `PHT_S` 相对偏移掩码还原从 64 步串行循环改为单行桶形移位 `(pred_s_mask << off) | (pred_s_mask >> (64 - off))`，`eda-05` Yosys 综合 `axi_llc_bingo` 由 `52,853` cells / 163 层降至 **`41,232` cells（25 `$mem_v2`、394 FFs）/ 48 层**。
- **验证范围**：`trace-model` `comb_graph` 0 / `run_gate` 62/62（默认 / `PF_ENABLE=0` / `LLC_BINGO=0`）/ `linux_check.sh` `rv64 login:`（0 oops/panic）/ 全量 SPEC06 INT 386/386（`+1.26%` → `14.88 分/GHz`，11 正 1 平 0 回归）；RTL `lint_chip` 0 / `fm_gate.sh` **69/69（0 FM 差、0 周期差）**/ `eda-05` Yosys `axi_llc_bingo`（41,232 cells / 48 层）/ `eda-05..09` 27 窗 `rv64gc` Linux（27/27 DONE、`137,700,059` 指令 0 FM 差、27/27 PT/UP 100% 逐拍全等）。未跑 RTL SPEC 与工艺库时序。

### 2026-11-22 EXP-056 统一 L2 TLB（1024×4 1RW SRAM + 8 项大页 CAM）+ 16 项 Sv39 PWC 与 `TraceBridge` 已提交页表读修复

- **配置变化**：`trace-model/include/config.h` 新增 4 个参数：`L2TLB_ENTRIES = 1024`、`L2TLB_WAYS = 4`、`L2TLB_SP_ENTRIES = 8`、`L2TLB_PWC_ENTRIES = 16`（零新增环境变量）。RTL 经 `make cfg` 自动同步 `ttg_cfg_pkg.sv`（171 → 175 常量）。
- **设计改动与 `ptw_walk` 降深度（`47 → 44` 层）**：
  - **统一 L2 TLB + 大页 CAM + Sv39 PWC**（`MemPtwBlock.h` / `ptw_walk_l2tlb.sv` / `ptw_walk_engine.sv`）：在 PTW 入口增加 1 拍 `STLB_LK` 状态；4KB 项存入 4 个独立 1D `256×76b` 1RW SRAM bank（无复位，Yosys 综合为干净 `$mem_v2`），XOR 索引 `vpn[7:0] ^ vpn[16:9]`、3-bit tree-PLRU 替换；2MB/1GB 大页存入 8 项 RR 全相联 CAM；L2/L1 非叶页表项存入 16 项 RR Sv39 PWC（20-bit `root` 匹配）；`sfence.vma` 从 `TlbMmu`/`rob_bcast_fence` 透传至 `ptw_walk.sfence_flush` 同拍清空有效位。
  - **关键路径解耦（47 → 44 层）**：`ptw_walk_engine.sv` 将 `PW_L1_REQ`/`PW_L2_REQ` 授权与 PTE 分类直接挂在 `state_q` 而非 `select_any → state_b`，`eda-05` Yosys 综合 `ptw_walk` 仅 `5,446` cells（21 `$mem_v2`、206 FFs）/ **44 层**（低于改前 47 层）。
  - **修复 `TraceBridge` PTW 读未提交 PTE 缺陷**：`MemRouteBlock::comb_response()` 原用 `tbhook::mem_read()` 读出 ROB 内未提交 store 的投机值（导致 `rv64gc` Linux `setup_vm_final` 早期 oops），新增 `Bridge::read_committed_word()` / `tbhook::mem_read_committed()` 回溯 `chain_` undo log 读已提交内存，根治 oops 并与 RTL DCache 逐拍对齐。
- **验证范围**：`trace-model` `comb_graph` 0 / `run_gate` 62/62 / `PF_ENABLE=0` 62/62 / `run_gate_c` 68/68（`rvc-sv39.bin` `3270→3268`）/ `linux_check.sh` `rv64 login:`（0 oops/panic）/ 全量 SPEC06 INT 386/386（`+3.17%` → `14.69 分/GHz`，12/12 全正）；RTL `lint` & `lint_chip` 0 / 新增 `directed/l2tlb_pwc.bin`（`9041 == 9041` 周期，14,243 指令 0 FM 差）/ `fm_gate.sh` **69/69（0 FM 差、0 周期差）**/ `eda-05` Yosys `ptw_walk`（5,446 cells / 44 层）/ `eda-05..10` 27 窗 `rv64gc` Linux（27/27 DONE、约 1.377 亿指令 0 FM 差、27/27 UP 全等、26/27 PT 全等，`s02` 1 处错路投机差 3 拍重收敛）。未跑 RTL SPEC 与工艺库时序。

### 2026-11-22 EXP-055 后端指令窗口扩展（`PRF=256 / ROB=256`，`MAX_BR=32`）与 `ren` 公共原语降深度（`100→91` 层）

- **配置变化**：`trace-model/include/config.h` 仅改两项默认值：`CFG_PRF_NUM: 128 → 256`、`CFG_ROB_NUM: 128 → 256`（`PRF_IDX_WIDTH 8→9`、`ROB_IDX_WIDTH 7→8`、`FP_TAG_BASE 128→256`）；`MAX_BR_NUM=32` 与所有 IQ/LDQ/STQ/MSHR 保持不变（DSE 实测在 192/256 窗口下均无净收益）。RTL `make cfg` 自动同步 `ttg_cfg_pkg.sv`（171 常量），零新增环境变量。
- **RTL 改动与 `ren` 降深度（`100 → 91` 层，较 128/128 基线 97 层反降 6 层）**：
  - 参数化 8 个 wrapper 文件里写死的 `[6:0] rob_idx` / `[7:0] rob2dis_free` 为 `[ROB_IDX_WIDTH-1:0]` / `[ROB_IDX_WIDTH:0]`（`rob.sv`、`dispatch.sv`、`lsu.sv`、`lsu_pipe.sv`、`exu.sv`、`back_top.sv`、`core_top.sv`、`soc_top.sv`）。
  - **`ren_dep_check.sv`**：利用 1-hop 消除不变式将 7 级假串行 `dest_preg[0..7]` 拆为两级并行旁路（复用 `ttg_first_set` + `ttg_onehot_mux`）。
  - **`ren_elim_sel.sv`**：将 7 级串行 `parent_state` 改写为 3 级 Kogge-Stone 并行指针跳跃网络（复用 `ttg_first_set` + `ttg_onehot_to_idx` + `ttg_onehot_mux` + `ttg_popcount`）。
  - **`ren_rat.sv` / `ren_core.sv` / `ren_fp.sv`**：将 `fire` 移出 8×33 `snapshot` 矩阵，`spec_d` 通过 `ren_last_write` 按 `fire` 末位选通，把 `ren_handshake` 移出 `ren_ckpt` 关键路径。
  - 修复 `tb/soc/soc_tb.cpp` 写死的 `c.fpreg - 128`（改为动态取整数 `reg_file_q` 大小）与 `tests/ren_elim_sel/tb_ren_elim_sel.cpp` 9-bit `spec_rat` 打包。
- **验证范围**：跑齐 `trace-model` `comb_graph` / 62+68 门禁 / Linux 启动 / 全量 SPEC06 INT 386/386（`+5.64%` → `14.24 分/GHz`）、RTL `lint_chip` 0 / `tests/ren_elim_sel` 100k 0 不一致 / `fm_gate` 68/68（0 周期差）/ `eda-08` Yosys（`ren`/`prf`/`rob`/`isu`）/ `eda-05..10` 27 窗 `rv64gc` Linux（137,700,051 指令 0 FM 差且 27/27 PT/UP 全等）；未跑 RTL SPEC 与工艺库时序。

### 2026-11-22 EXP-053 前端两阶段结构清理与去补丁重构 + 复用 `ttg_pick_k` 与双路径加速

- **配置变化**：无核参数变化（`gen_cfg.sh` 与 `trace-model/include/config.h` 171 常量逐字节一致，零新增环境变量）。
- **设计改动与修 bug**：
  - **Phase 1（零周期结构重构）**：`icache_arr.sv` 显式拆为真 4-Bank 1R1W + 并行 SRRIP（`icache` 单元 **−57.5%**）；`bpu_types_pkg.sv`/`bpu_eval.sv` 并行 `ftb_eval_ent`（加固错路奇地址 `ceil` 与 64 位回绕）、`bpu_hist_vec.sv` 零取模并行移位、`bpu_spec.sv` 切断 `r1_q→ovr_a→spec_a→g0_b` 假路径（`bpu` **−18.6% 单元 / −27.6% 深度**）；`inst_fifo` 改为紧凑原始半字流、单份展开预译码与 4 轮 Kogge-Stone `start_a/b` 扫描集中至 `front_head_fix.sv`（`front_top` **−26.8% 单元 / −39.3% 深度**）；全链路删除死线 `tage_idx/tage_tag`。
  - **复用公用原语与双路径仿真加速**：`front_pd_info.sv` 复用 `rtl/common/ttg_pick_k #(.N(FETCH_WIDTH), .K(2))`；`front_head_fix.sv` 与 `bpu_hist_vec.sv` 按 `rtl/common/ttg_*.sv` 统一风格补齐 `` `ifdef SYNTHESIS `` 快速仿真路径（`fe_clean_eq_tb` 仿真提速 **3.6×**）。
  - **Phase 2（微架构去补丁）**：P2-1 删除 `dcache`/`wb`/`mem_top` 上跨子系统 `fdip_snoop` 旁路，改为 `icache_fdip` 发射前经既有 `dc_req`/`dc_resp` 做 1 拍 DCache/WB/MSHR/fill 探针；`axi_cpu_port_chan` 通道 0 增加 `CLEAR_ON_POP=1`（对应 `SimCpu.cpp`）根治 AXI 响应回波并删除 `resp_popped_q` 补丁；`icache_top.cpp` 补齐 32 KiB L1I 数据阵与 `Blocked::StaleIcache`。P2-2 用显式 1-bit `pf_inst_hi` 替代跨页 RVC 缺页 `inst→diag_val[1]` 搭便车编码。
  - **顺带修 bug**：修复 `trace-model` `LsuPipeTranslate.cpp` 既有 STLF `cam_ok` 缺陷（命中 STLF 候选时不缓存 `cam_val`，消除 `s01`/`s09` 两处 `RC_DATA` 投机污点分叉）。
- **验证范围与已知说明**：合入 EXP-052 + `de5fdb9` 后（`4d4534f` + `28840c8`）已全量实测：`trace-model` `comb_graph` / 192 本地门禁 / Linux `rv64 login:` / **SPEC06 INT 386/386（`res_exp053_main_386`，`13.48 分/GHz`，vs EXP-052 `−0.05%`、vs EXP-051 `+0.50%`）**、RTL `gen_cfg` / `lint_chip` / `common_prims` 100k / `ren_elim_sel` 100k / `fe_clean_eq_tb` 双路径 / `fm_gate` 68/68（0 周期差）以及 **`eda-05..10` 全量 27 窗 `rv64gc`+`Sv39` Linux 检查点（`out_exp053_main`，`s01..s26` 26/26 PASS + `s00` PT/UP `0..1619` 全等，合计 `137,700,065` 指令 0 FM 差、27/27 PT/UP `150,175 / 150,175` bins 全等，原 EXP-052 `s17` 亦归零对齐）**；Yosys 9 模块综合跑于变基前同前端实现。未跑 RTL SPEC 与工艺库时序。

### 2026-11-22 EXP-052 RV64GC `c.mv` 规范化、组内 1-hop 关键链移动消除与 `ren` 降深度（99→97 层）

- **配置变化**：无核参数变化（`MOVE_ELIM = 1`、`MOVE_ELIM_MAX_REFS = 7`、`DECODE_WIDTH = 8` 保持默认不变，零新增环境变量）。
- **设计改动与修 bug**：
  - **修复 RV64GC `c.mv` 漏消除**（`Idu.cpp` / `idu_decoder.sv` / `MsData.h`）：将 `add rd, x0, rs2`（含全部展开后的 16-bit `c.mv`）规范化为 `addi rd, rs2, 0`，消除率在 SPEC06 上从 `0.00%` 恢复至 `4%~13%`；同步修复 `MsData.h` 污点求值器对规范化 `c.mv` 的求值。
  - **组内 1-hop 关键链移动消除**（`Ren.cpp` / `ren_elim_sel.sv` / `ren_dep_check.sv`）：允许同组内最近老整数写者 `j` 未被消除且 `(i - j) < MOVE_ELIM_MAX_REFS` 时消除 move 并共享 `alloc_reg[j]`，3-bit `arch_cnt` 永不溢出。
  - **`ren` 深度压降（99 → 97 层）**：`ren_elim_sel` 采用并行根分解把 1-hop 旁路链移出 33 路 `spec_rat` `ttg_popcount` 关键路径；`ren_core` / `ren_fp` 的分支 `head_after` 改用 `alloc_req` 前缀并由 `ren_free_list` / `ren_fp_free_list` 按 `fire` 末位直接选通 `head_next`。
- **验证范围与已知说明**：已跑全量 SPEC06 INT 386/386（+0.55%，12/12 全正）、`trace-model` `comb_graph` / 62+68 gate / Linux 启动、RTL `lint_chip` / 100k `tests/ren_elim_sel` / `fm_gate` 68/68（0 周期差） / Yosys `ren` & `idu` / Linux 27 窗（1.377 亿指令 0 FM 不一致，26/27 PT/UP 全等；`s17` 在第 3,639,154 拍 ICache miss 早 4 拍属错误路径访存模型差，已接受）；未跑 RTL SPEC 与工艺库时序。

### 2026-11-21 后端执行唤醒与 Bypass 阶段一优化（二维 EXU Bypass Mask + 读口/旁路裁剪 + `isu_fp_gate` 移位寄存器）及 `trace-model` 清理

在**零周期变化**的前提下，完成后端 `prf` / `isu` / `dispatch` / `exu_ctrl` 硬件结构瘦身与 `trace-model` 死代码清理：
- **RTL（`480a89e`）**：
  - **PRF 读口与 Bypass 重构**：整数读口 42→27（`prf_regfile` 平铺 `NRD` 口，裁掉 LD/STA `src2`、共用 STA `src1` 与 FP 口整数读口）；整数 EXU 级旁路改为 ISU 随发射送来的 6 位二维独热 Mask 直驱 `exe2prf_entry[0..5]`（0 个 EXU 级 tag 比较器）；浮点 EXU 级旁路压至单路迭代 FDIV（`exe2prf_entry[WB_FP_BASE+2]`）；彻底删除 31 路 `exe2prf_bypass` 总线（`exu_ctrl_wb_prf`/`exu_ctrl`/`exu`/`prf`/`back_top`）。
  - **ISU 唤醒分离与 `isu_fp_gate` 降深度**：慢速寄存唤醒按域拆分为 `woken_slow_int[128]` / `woken_slow_fp[96]`，6 路单周期 ALU 快速唤醒直连 7-bit CAM；非 FP 队列裁 `wait3`，MEM 队列裁 `wait2`；MUL/DIV 延迟唤醒槽补存 1 位来源口以驱动槽内 6 位 `byp_q`；`isu_fp_gate` 从 64 项环形数组 + `now_q` 改写为 23 级移位寄存器。
  - **Dispatch 唤醒去重**：去掉与 `iss_awake[0..3]` 重复的 4 路 `prf_awake` 比较及 `LP_L2[3]=0` 时的 L2 推测唤醒（34→26 路）。
  - **综合收益**（`eda-06` Yosys `strash;balance;map`）：`prf` **−41.8%**（679,466→395,785 / 27 层）、`isu` **−3.4%**（948,982→916,275 / 90→89 层）、`dispatch` **−5.6%**（186,536→176,071 / 56 层）、`exu_ctrl`（20,133→20,037 / 17 层），四模块合计 **−326,949 单元（−17.8%）**。
- **trace-model（`7e00aae`）**：删除无人读取的 `ExePrfIO`（31 路 `bypass` + 13 路 `entry` + `int_res[6]`），`Exu::Regs::lwake_r` 从 13 缩至 4；按 `WORKFLOW` §7.6 删除 13 个已采纳的 `CFG_*` 历史开关与死分支（含 `RealLsu.h` 每拍空拷的 `agu_q_`/`agu_d_`）。
- **验证范围**：跑了 `comb_graph.py --check`（0 隐患）、trace-model 门禁 62/62 + C 门禁 68/68 + rv64gc Linux 启动至 `rv64 login:`（0 oops/panic）、RTL `make cfg` + `lint_chip.sh`（0 警告）+ `fm_gate.sh` 68/68（0 FM 不一致、0 周期差）、`eda-06` 四模块 Yosys 综合、`eda-06..09` `rv64gc` + `Sv39` Linux 27 窗口检查点与从复位验证（`s01..s26` 26/26 PASS + `s00_inst0` 510 万指令，合计 137,700,071 条指令 0 FM 不一致、27/27 全部 PT/UP 指纹 bin 0 差异）；未跑 SPEC06（零周期变化）、未跑整块 `back_top` 综合。

### 2026-11-21 EXP-051 前端 `2-taken` + `2-Ahead B` + 4-Bank 1R1W ICache / 2 读口 ITLB + 实 AXI FDIP（里程碑 B）与 RVC 跨页取指缺页 `stval` 修复

落地前端里程碑 B 帕累托冠军（`fe2f_b4_it2_ah1k`），在无双口 ICache SRAM、零 S0 串行 SRAM、真 AXI/LLC/DRAM 仲裁约束下将全量 SPEC06 INT 相对 EXP-050 再提升 **+2.18%（`13.14 → 13.42 分/GHz`，相对 EXP-048 累计 +10.76%，12/12 全正）**，`FE.bw` 降至 `18.60%`、`coremark` 周期再降 **−15.77%**，并修复了一处潜伏的 RVC 跨 4KB 页 32 位指令第二半字取指缺页 `stval = pc + 2` 架构缺陷。

**配置与接口变化**

| 项目 | 旧值（EXP-050 里程碑 A） | 新值（EXP-051 里程碑 B，默认即唯一实现） |
|---|---|---|
| BPU 预测与训练 | 单块 1-Ahead A（`2K/1K/256`）+ `HistRing 256b` + `bpu_ck` 168b 经 PTAB/F2B/FTQ 透传 | `2-taken` 双块融合（`NT=1` 不截断，4-bank `ic_pair_ok`）+ `1-Ahead A (2K/1K/256)` + `2-Ahead B (1K/512/256)` + `HistRing 1024b` + 内部 `rec_q[256]`（省去跨管线 `bpu_ck`）+ `BRQ_W=1` |
| ICache / ITLB / FDIP | 单块 ICache + 单读口 ITLB + 模型理想 `FE_IPF`（默认关） | **4-Bank 1R1W ICache**（`icache_arr.sv`）+ **2 读口 peek ITLB**（`tlb_mmu_core.sv` `NPEEK=2`，零新增 PTW walker）+ **S2 确认 2-slot 实 AXI FDIP**（`icache_fdip.sv`，txid `8..9`、8 项 VA 队列 `1-pop/cycle`、`issued` 响应门控、`resp_popped_q` 防重弹、周期初 L1D/WB 脏行嗅探） |
| 前端与 FTQ/后端连线 | 单块 `inst_fifo`/`predecode_checker`；`pre_idu_ftq_bpu` 无 `ftq_offset` | `FetchPair` + `pend_pair_q`；S2 确认 `alt_a` 完整 A 块兜底；双段 `predecode_checker` 与 2-symbol/2-RAS `front_pd_info`；4 位 `ftq_offset` 贯通 `prf → exu_ctrl → idu_br_latch → pre_idu_ftq_bpu` 直接索引 `{blk_id[16], kind[16]}` |
| 实验开关与参考表 | 保留 `FE_PAIR` / `FE_IPF` / `FE_IPF_LAT`；67 个 RTL 参考程序 | 按 WORKFLOW 7.6 彻底删除旧开关与理想预取代码（`ENV_VARS.md` 16→13 个）；新增 `directed/fe_2taken_fdip.{S,bin}`，重生成 `baseline{,_nopf,_c}.csv` 与 `ref_cycles{,_nopf}.txt`（68 程序） |

**设计改动与修掉的问题**
- **RTL（`3fa98cd`）**：新增 `rtl/frontend/bpu/bpu_eval.sv` 与 `rtl/frontend/icache/icache_fdip.sv`（Yosys-Slang 兼容内联队列入队），同步更新前端 BPU/ICache/FIFO/检查器、TLB、DCache/WB 脏行嗅探、`pre_idu_ftq_{pc,bpu}`、`prf`/`exu_ctrl`/`idu`、`rob_trap_ctrl`；`make cfg` 同步 `ttg_cfg_pkg.sv`（171 常量）；全核 RTL 285 文件 / 37,525 行（`05-module-tracker.md`）。
- **trace-model（`5b67500`）**：`BpuFtb.h` / `BPU_pipe.h` / `front_top.cpp` / `icache_top.{h,cpp}` / `MemSubsystem.h` 收敛为唯一默认实现并清理 `comb_graph.py --check` 契约告警；修复 `baremetal/test/cpu-tests/supervisor-external-interrupt-vectored-helper.S` RV64 `sd`/`ld` 现场保存。
- **跨 4KB 页 RVC 指令第二半字取指缺页 `stval` 修复（三仓一致）**：当 32 位指令位于页尾 `0x...ffe` 且次页 `0x...000` 缺页时，`front_head_fix` / `rvc_head_fix` 将 `pc[0]` 拼回 `0x...ffe` 并通过 `inst → diag_val[1]` 携带 `+2` 偏移，`rob_trap_ctrl.sv` / `Rob.cpp` 输出 `trap_val = pc + (diag_val & 2)`，与 RISC-V 规范及 `function-model` 一致，根治 `rv64gc` Linux `Running sysctl:` 在跨页缺页处死循环。

**验证范围**
- **跑了**：`comb_graph.py --check` 0 隐患；trace-model `run_gate.sh` 62/62、`PF_ENABLE=0` 62/62、`run_gate_c.sh` 68/68、`linux_check.sh`（rv64gc Linux 5.15.170 默认 `--irq-seed 1` 及 seed 2 / `PF_ENABLE=0` 均到 `rv64 login:`，0 oops/panic）；RTL `lint_chip.sh` 0 警告/0 错误、`fm_gate.sh` **68/68 PASS、0 FM 不一致、0 周期偏差**；`eda` rv64gc Linux 27 段检查点（`s01..s26` **26/26 PASS** ~1.326 亿指令、`s00_inst0` 510 万指令 0 FM 不一致且 1637/1637 PT/UP bins 0 差异）；`eda-04/05` Yosys 综合 6 模块（`predecode` 10k/27、`pre_idu_queue` 138k/38、`tlb_mmu` 47k/61、`icache` 917k/106、`bpu` 504k/272、`front_top` 1.58M/356）；SPEC06 INT 386/386 点（`+2.18%`，`13.42 /GHz`）。
- **没跑**：RTL SPEC06；RTL 从复位 1.4 亿周期连续 Linux 指纹对比；工艺库时序综合（Synopsys DC / WNS）。

**对应** EXP-051；总仓库本行所在提交 / function-model `55affa0`（未动）/ trace-model `5b67500` / rtl `3fa98cd`。

### 2026-11-21 EXP-050 块级 1-Ahead FTB 分支预测器（里程碑 A）与 LSU_MS_DATA 污染 store 前递修复

将原有 16-bank 逐指令槽 BPU 整体替换为**块级 1-Ahead FTB + S2 Block-TAGE/ITT + 1-branch/cycle 提交训练队列（`ah1_4k_a2k1k` + `FTB_BRQ=2`）**，消除 `of2` 同拍组合环，模型全量 SPEC06 INT 提升 **+8.48%（`12.11 → 13.14 分/GHz`）** 且 RTL `bpu` 单元数直接减半（**−50.0%**），并补齐 `LsuPipeInternal.h` 污染地址 store 前递缺口实现 26 段 rv64gc Linux 检查点 100% 0 差异。

**配置与接口变化**

| 项目 | 旧值（16-bank BPU） | 新值（EXP-050 里程碑 A，默认即唯一实现） |
|---|---|---|
| BPU 预测组织 | 16-bank 逐槽 Type + BTB + TAGE + 3 表 ITT | 块级 S0 uFTB（256×4）+ S1 Main FTB（4K×4，4 槽禁交换，含 1b `carried`）+ 1-Ahead FTB（2K×8）/ Block-TAGE（1K×4 表）/ Block-ITT（256 项）+ S2 兜底 Block-TAGE（4K×4 表）/ Block-ITT（256 项） |
| 外部端口与参数包 | `bpu.sv` 既有端口；`ttg_cfg_pkg.sv` | **零外部端口改动**（10 位 `blk_id` 经既有 `out_tage_idxs[*][0]` 透传）；`include/config.h` 与 `ttg_cfg_pkg.sv` 不变 |
| 实验开关清理 | `exp/ftb-bpu` (`375b080`) 保留 19 个 `BPU_FTB`/`FTB_*` DSE 开关 | 按 WORKFLOW 7.6 全部删除，默认即 RTL 配置（零环境变量）；保留 `DS3_CONFIG` |
| 基线与参考表 | `results/baseline/baseline{,_nopf,_c}.csv`、`ref_cycles{,_nopf}.txt` | 全部用默认零环境变量模型重生成（`baseline` 62、`nopf` 62、`baseline_c` 68、`ref_cycles` 67） |

**设计改动与修掉的问题**
- **RTL（`a4dcfb9`）**：删除 22 个旧 16-bank BPU SV 文件，新增 `bpu_types_pkg.sv`、`bpu_ftb_tab.sv`、`bpu_ftb_tage.sv`、`bpu_ftb_itt.sv`、`bpu_ftb_brq.sv`、`bpu_ftb_arrays.sv` 并重写 `bpu.sv`（更新 `bpu_stage_pkg.sv`、`bpu_ctl.sv`、`bpu_pdq.sv`、`tb/soc/{pmu_public.vlt,soc_tb.cpp}`）；全核 RTL 文件 283 个 / 36,360 行（`05-module-tracker.md`）。
- **trace-model（`ef61350`）**：`BpuFtb.h` / `BPU_pipe.h` 精简为唯一块级 1-Ahead 实现；修复 `back-end/Lsu/LsuPipeInternal.h::ms_load_value` 对 `m.atnt=1`（地址污染）老 store 跳过 STLF 前递的问题——当其旧物理地址 `t.paddr`（`t.pa_v && !t.pf && !t.mmio`）命中年轻 load 时正确前递旧值，一次消除 `s10`/`s15` 两处 Linux 检查点分叉；修复 `scripts/build_tests.sh` 在 Ubuntu `clang-18`/`ld.lld-18` 下 `.data/.sdata` 溢出及 `unalign` 缺少 `-fmax-type-align=1` 的问题。

**验证范围**
- **跑了**：`comb_graph.py --check` 0 隐患；trace-model `run_gate.sh` 62/62、`PF_ENABLE=0` 62/62、`run_gate_c.sh` 68/68、`linux_check.sh`（rv64gc Linux 5.15.170 到 `rv64 login:`，0 oops/panic）；RTL `lint.sh rtl/frontend/bpu` & `lint_chip.sh` 0 警告/0 错误、`fm_gate.sh` **67/67 PASS、0 FM 不一致、0 周期偏差**；`eda-08`/`eda-09` rv64gc Linux 26 段检查点（`s01..s26`，4M 周期/段，132,473,668 条指令）**26/26 PASS、0 FM 不一致、103,974 PT bins / 103,144 UP bins 全程 0 差异**；`eda-06` Yosys 综合 `bpu`（`274,811 cells` / `131` 层，−50.0% 单元）与 `front_top`（`898,333 cells` / `153` 层）；SPEC06 INT 386 点（`+8.48%`，12/12 全正）。
- **没跑**：RTL SPEC06；RTL 从复位 1.4 亿周期连续 Linux 指纹对比；工艺库时序综合（Synopsys DC / WNS）。

**对应** EXP-050；总仓库本行所在提交 / function-model `55affa0`（未动）/ trace-model `ef61350` / rtl `a4dcfb9`。

### 2026-11-19 RTL 降深度那一轮：两个 INT 队列、合并访存队列、FLUSH_REG、低深度改写，模型默认值 = RTL 配置（EXP-044）

这是一次很大的合入（rtl 47 个提交、trace-model 48 个提交）：RTL 为压低综合深度改了发射队列、访存队列、flush、前端 / BPU / LSU 的结构，trace-model 的默认值同步改成 RTL 的配置（之前要带 13 个 `-D`），并用 12 个 Linux 检查点窗口对齐。**有意的性能回退**：67 个程序周期几何平均 +1.92%，SPEC06 386 点 IPC 几何平均 −2.15%。

**配置变化**（trace-model `include/config.h` 的默认值；RTL 一直是这个配置）

| 参数 | 旧值 | 新值 |
|---|---|---|
| `CFG_INT_CLUSTERS` / `CFG_INT_IQ_SIZE` / `CFG_INT_IQ_ENQ_WIDTH` | 1 / 64 / 7 | 2 / 32 / 4（两个 INT 发射队列，端口 0,1,4 / 2,3,5） |
| `CFG_MEM_IQ_ENQ_WIDTH` | 8 | 6（访存队列 load + STA 合并，去掉 STA 空队列和 `CFG_MEM_MERGE`，共 6 个发射队列） |
| `CFG_AGU_SHARED` | 0 | 2（5 个 AGU：2 个 load 专用、2 个 load / STA 共用、1 个 STA 专用） |
| `CFG_ISSUE_OLDEST_FIRST` / `CFG_ISSUE_OLDEST_QUEUES` | 0 / 0xff | 2 / 2 |
| `CFG_IQ_SAME_CYCLE_REUSE` | 1 | 0 |
| `CFG_FLUSH_REG` | 0 | 1（全局 flush 晚一拍到各模块，`rtl/docs/FLUSH_REG.md`） |
| `CFG_LSU_STAEV_REG` / `CFG_LSU_SLOT_FIXED` / `CFG_LSU_WBMERGE_REG` | 0 / 0 / 0 | 1 / 1 / 1 |
| `CFG_FE_OVR_REG` | 0 | 1（取指地址 FIFO 晚一拍读） |
| `scripts/ref_cycles.txt`（rtl）| 上一版 main 的表 | 新配置的表（67 个程序，几何平均 +1.92%） |
| 基线（trace-model `results/baseline/baseline.csv`、`baseline_c.csv`） | 旧配置 | 新配置重新生成（62 / 62（关预取）/ 67 个程序周期都变化，见下） |

**设计改动和修掉的问题**
- **RTL 结构改写**（周期不变或与模型同步）：`lp_ptr` / `lp_rp`、`lp_wbstep`、`lp_ovl`、`bpu_ub_track_ser`（528 → 97 层）、`bpu_updq`、`bpu_ub_look`（75 → 29 层）、`front_fetch_buf` 的起点前缀扫描、`fetch_addr_fifo` 的 `head_fresh`、`mul_core` 铺在 3 拍（`mul_unit` 209 → 90 层）、dispatch / isu 队列清理；删除旧 LSU、`LSU_PIPE`、行式 ROB、`csr_fu` 和只剩一个值的开关。
- **RTL 修掉的 bug**：`lp_ldq` 的 DCache 响应选择不比 epoch（过期响应盖住有效响应，load 停在 DCW）；`bpu_ub_look` uBTB 目标只取低 32 位；`back_top_glue` 在 flush 决定那一拍用重定向地址覆盖提交槽的 `diag_val`（同拍提交的调用用 mtvec 训练了 BTB）。
- **trace-model**：桥接层对 `mstatus.FS = Off` 的 FP store 不先读旧值（Linux 里 `illegal word load`）；flush 型提交指令的 FS-dirty 保留；uBTB 目标全宽；`MsData` 对违例 load 第二次写回的同拍可见性（`MsLdq::early_clean`）；指纹口径：`dir=0` 的训练事件不计目标。
- **文档**：每个原子模块一份设计文档（`rtl/docs/modules/`，34 份）、`WORKFLOW.md` 第 7 节（RTL 开发流程：文档先行、提交前核对）、`LINUX_ALIGN.md`。

**验证范围**
- 跑了：RTL `lint_chip` 0；`fm_gate.sh` 67/67、周期与 `ref_cycles.txt` 0 处不同、0 个函数模型不一致；Linux 检查点窗口 s00–s11 12/12 PASS（约 5900 万条指令逐条检查，PT / UP 指纹全程相等）；trace-model：RVC=0 门禁 62/62、RVC=1 C 门禁（新基线）、67 个程序周期 = RTL、Linux 从复位启动到 `rv64 login:`（无 oops / panic）；SPEC06 rv64gc 386 点（`final95`，eda 集群，0 失败）新旧两个配置各跑一遍。
- **没跑**：RTL 从复位的 Linux 全程（1.4 亿周期）指纹对比；整机综合（`back_top` 135、`front_top` 132 是后来又改了几处之前的数，`ren` 110、`axi_llc` 238 超过 100 层）；SPEC 的两次全量用的是没有 `early_clean` 补丁的模型（影响应远小于 0.1%，没有重跑）。

**已知回退**
- 67 个程序：几何平均 +1.92% 周期（dhrystone +7.95%、coremark +3.0%、memory-stress-small +0.08%；最差 `timer-mmio` +19.8%、`goldbach` +12.3%）。
- SPEC06 386 点：新配置对旧默认值（同一份代码）IPC 几何平均 −2.15%（hmmer −8.6%、bzip2 −3.5%、sjeng −3.5%、astar −2.6%、gobmk −2.4%、perlbench −2.0%，xalancbmk +1.6%）；旧默认值对 11 月 15 日 `res_final` +0.04%。主要来自两个 INT 队列（32 项、4 条入队）和 FLUSH_REG，每一项的单独代价没有量化。

**对应** EXP-044；总仓库本行所在提交 / function-model `55affa0`（未动）/ trace-model `c795844` / rtl `a26a102`。

### 2026-11-15 RVC=1 / rv64gc 的 RTL 与 trace-model 逐周期对齐，含 Linux（EXP-038、EXP-040）

这是一次很大的合入：把 C 扩展（`RVC=1`）从 trace-model 做到 RTL，并把 rv64gc 的 Linux 在 RTL 和 trace-model 上对齐到逐周期。默认配置（rv32、`RVC=0`、`FP` 同原来）的周期不变，下面的新行为都在 `RVC=1` 或 rv64 下才生效。

**配置变化**

| 参数 | 旧值 | 新值 |
|---|---|---|
| `CFG_LSU_MS_DATA`（trace-model `include/config.h`，旧值路径的位掩码） | 1（分支 + store 数据） | 7（再加第 2 位：污染地址）；rv32 默认配置周期逐个不变 |
| 配置包（`ttg_cfg_pkg.sv`） | 提交的是 rv32 `RVC=0`；rv64 要手工 `sed` | 提交的不变；`tb/soc/build.sh` 在 `SOC_XLEN=64` 时从 trace-model 生成 `-DXLEN=64 -DRVC=1 -DFP=1` 的配置包（与 `gen_cfg.sh` 同一个脚本，`SOC_RVC`、`SOC_FP` 可改） |

**设计改动和修掉的问题**（trace-model 与 RTL 的差别，按发现的先后）
- **C 扩展 RTL**（R0–R4，`exp/rvc-rtl`）：配置包导出 `RVC_ENABLE` / `SLOT_*`；后端带每条指令的 `is_rvc`、`pc + 长度`；前端 `rvc_expand`、携带寄存器（C910 式：组末的 32 位指令前半字存起来，下一个顺序组的 slot 0 拼成整条）、BPU 16 槽几何；`RVC=1` 非 C 程序 64/64 周期与模型相等，C 程序 59/60（`rvc-fencei` 差 7 周期，自修改代码）。
- **trace-model**：C910 式携带（取代 I$ 第二行）；删掉不再使用的旧 BPU（`class Bpu`、`BPU_PIPE 0..2` 等）和冻结 RTL 差分测试；冻结只跑过默认值的开关；RAS 改成追加队列 + 指针检查点；FE 三个 RVC=1 / rv64 预测修复（hmmer 上 48.7% 的取指组被预译码冲刷）；STQ store 数据加宽到 XLEN（rv64 的 `sd` 之前丢了高 32 位，OpenSBI 的 mtimecmp 高半字写成 0，定时器一直挂起）；FP load 遇 `mstatus.FS=Off` 现在作为非法指令到达 ROB。
- **对齐工具**：`FPR=<bin>`（PTAB 写入流 PT 和预测器更新流 UP 的逐 bin 计数加可交换哈希，trace-model 与 RTL 测试平台同一份代码，UP 里含 TAGE 的 4×10 位索引、4×8 位标签）、`FPR_DUMP=<起>:<止>` 展开原始事件；PMU 时间序列（`SOC_TB_PMU_IV` / `PMU=1`）；`scripts/align_check.py`、`scripts/linux_gate.sh`（逐条检查 + 每区间 PMU + 到 `login:`）、**`scripts/linux_segments_cmp.sh`（检查点窗口并行，RTL 对 trace-model，约 15 分钟出全部结果）**；`SOC_TB_VCD=<起>:<止>:<文件>` 波形导出 + `scripts/vcd_query.py`（按层次名逐周期查信号，窗口几十周期，文件不大）。
- **rv64 的 32 → 64 位错误**（RTL 里按 32 位处理的地址，Linux 的符号扩展物理地址 `0xffffffff80…` 才暴露）：历史哈希符号 `hsym_of`（先按槽移位再截断）、uBTB 目标展开（高位取块基址而不是补 0）、预译码目标类型、MDP 等待表索引（`SLOT_SHIFT` 而不是写死的 2）。
- **测试平台**：`EVAL()` 在读 `env_rd_en` 之前先稳定 `env_modeled`（旧顺序下 Linux 偶尔卡死）；逐条检查加了 **store 的地址和数据**与 **设备 load** 的检查；RTL 报 page fault 而功能模型不报的合法情形（遍历器在 `sfence.vma` 前读到旧页表项）由 `refcpu_force_next_page_fault`（function-model）强制模型同样 fault。
- **EXP-020 旧值路径扩到 rv64**（`MsData.h`，XLEN 位的 ALU / 乘除 / W 形式 / 带符号扩展的 load，STQ 的 `m_*` 字段 64 位，旧数据转发的 load 也打污染）；**默认打开污染地址**：store 的基址寄存器来自读到旧值的 load 时，数据写到旧地址、之后在真地址上读到旧内存，RTL 如此，模型原来不跟。
- **RTL 行为改动（唯一的 RTL 功能改动）**：页错误的 load 不再把出错地址写进目的寄存器（`lp_wb.sv` 的 `wb_dest` / `wb_dest_en` 照 store-conditional 页错误的写法；`lp_wake.sv` 的 L3 唤醒加 `!pf`）。体系结构上 rd 本来不变；原来写 `rd = 出错地址` 会让错误路径上依赖它的 load 用这个地址去访存，模型（取功能模型的值）不会，两边的页表遍历和缓存内容因此分叉（Linux 第 4,012,380 周期）。模型同步（`RealLsuPipe.cpp`：wb 的 `dest_en` / `dest_preg`、L3 唤醒）。

**验证范围**
- 跑了：rv32 `RVC=0` 的 `fm_gate.sh` 64/64、周期与新模型、与提交的 `ref_cycles.txt` 都逐个相同；旧 rv32 模型（`build32g`）与新模型（默认值 7）在 64 个程序上周期逐个相同；rv32 的 `memspec_vio`、`itt-dispatch`（旧 rv32 模型构建上崩溃过，新构建没有）正常；rv64 directed 3/3；rv64gc Linux **18 个检查点窗口 18/18**（每 1000 万条指令一个，每窗 200 万周期，PT / UP 指纹 1998 个 bin 全部相同，逐条检查全部 0 不一致）；从复位的 Linux 对齐到 450 万周期。
- **从复位的 Linux 长跑（最终版本）**：RTL 用 `rtl-rvc` 自己构建的 rv64gc（4 线程），模型是合入的这一版；PMU 区间 50 万周期。**3000 万周期之前 60 个区间的一级事件全部相同**（包括之前一路追下来的 400 万、417.6 万周期附近，那里 167,047 个 25 周期区间全相同）。**第 60 个区间（3000–3050 万周期）起出现误差**：INSTRET 模型 684,700 / RTL 686,688、COMMIT_LOAD 136,214 / 136,554、COMMIT_STORE 124,138 / 124,546、COMMIT_BRANCH 87,460 / 87,736、BR_MISPRED 3,706 / 3,690、SLOT_FIRE 757,105 / 759,115。之后的区间差异正负不定（较早一版模型的对比里，到 5850 万周期的 117 个区间有 58 个有差异，单区间提交指令数差到 ±2.7 万）。逐条功能检查到 3400 万周期 0 个不一致（更早一版跑到 9800 万周期同样 0 个）。**没有在最终版本上跑到 `login:`**。
- **已知误差（没查原因，不阻塞合入，用户决定先合）**：误差点在 Linux 约第 3000–3050 万周期（约第 4,620 万–4,690 万条提交指令）。已排除：从 4400 万、4600 万条指令的检查点冷启动（`s44`、`s46`，200 万周期）都不复现；4500 万条指令（`s45`）复现过一处不同的分叉，已修（旧值路径的污染表泄漏），修后窗口 PT / UP 与 RTL 逐行一致。这一处需要热状态，只能从复位复现：`bash scripts/drill_pmu.sh <rtl soc_tb> <模型 simulator> <带波形的 soc_tb> <linux64gc.bin> 30500000 <输出目录> 25`（先 25 周期区间找出第一个差异窗口，再抓这个窗口的波形，两次 RTL 运行约 45 分钟）。上一个类似的问题（400 万周期处）最后是模型对错误路径的处理：FP 访存在 `FS=Off` 时模型先按地址挡掉没走非法指令判断、污染表在分支误预测冲刷后泄漏，可作为这一处的线索。
- **最终版本上没有重跑的验证**：18 个检查点窗口（18/18 全过）是用最终修复之前的模型跑的；最终版本只验了 rv64 directed 3/3、s45 窗口、从复位 417.6 万周期以内。最后几处修复是：FP 访存的污染立即数、MMIO / LR-SC load 写回清污染、重命名处清污染、`FS=Off` 时 FP 访存走 FM 的非法指令 trap。
- 没跑：rv32 `RVC=1` 与 rv64 `RVC=0` 的整表；SPEC；综合。
- **rv32 `RVC=1`（`FP=0`）整核测试平台起不来**（67 个程序在第一条提交 `pc rtl=4 fm=0`），在没有任何未提交改动的 HEAD 上同样复现，不是这次引入的，没有查原因，登记在 `rtl/docs/RVC_RTL.md` 的"已知遗留"。

**已知回退**：dhrystone −2 周期、coremark +119 周期（+0.04%），来自 RAS 追加队列；其余默认配置程序周期不变。

**短 gate 测试程序**（新约定，见 [WORKFLOW.md](WORKFLOW.md) 第 3.3 节）：`programs/directed/memspec_data`（旧值路径）、`memspec_addr`（污染地址，默认 `LSU_MS_DATA=1` 的模型周期对不上）、`memspec_pf`（页错误 load 的消费者；rv64 版能区分旧 RTL，周期差 9），rv32 / rv64 同源，周期在 `scripts/ref_cycles.txt`、`scripts/ref_cycles_rv64.txt`。

**对应记录**：[EXPLORATION.md](EXPLORATION.md) EXP-038、EXP-040；[LOG.md](LOG.md) 2026-11-15 各行。

### 2026-11-12 rv64imab 迁移（EXP-029）

- **配置变化**：

| 参数 | 旧值 | 新值 |
|---|---|---|
| 位宽 | 只有 rv32imab | `XLEN` 是构建参数，**默认 32（行为和周期不变）**；RTL `XLEN_BITS`（配置包 `ttg_cfg_pkg.sv`）、模型和 function-model 的 `-DXLEN` 取 64 即 rv64imab + Sv39 |
| 乘除延迟（XLEN=64） | — | `MUL_MAX_LATENCY` 3、`DIV_MAX_LATENCY` 32（XLEN=32 仍是 2 / 16） |
| RTL `rob_pkg` 位宽常量 | `XLEN` | `ROB_XLEN`（与 `-DXLEN` 重名，`DEBUG=1` 的 rv64 测试平台因此编不过；2026-11-12 同日清理） |

- **设计改动**：function-model RV64IMAB、Sv39、Spike 对拍、rv64 Linux 镜像、检查点 v4 / BBV；trace-model 接口层、译码、Sv39 MMU、64 位 CSR、PC 加宽、外设 8 字节；RTL 后端 XLEN 数据通路、LSU / dcache 8 字节数据、Sv39 TLB 与页表遍历、前端 / BPU PC 加宽、测试平台 XLEN 化（`SOC_XLEN`、`FMLIB`、`SOC_TB_LOG`）；跑 rv64 程序发现并修了 4 个 RTL bug（dcache 填充转发 / 写回缓冲写死 4 字节、DIV 唤醒倒计时、`lp_ovl` 宽度）和 1 个模型 bug（`sstatus` 视图丢 UXL）。同日清理：模型删 5 个无引用宏和 DDR 延迟推算链、6 个调试环境变量，其余环境变量写进 [trace-model/docs/ENV_VARS.md](../trace-model/docs/ENV_VARS.md)。
- **验证范围**：见上表最上一行（XLEN=32 全套回归 + rv64 的 53 个 cpu-tests、Linux 到 `rv64 login:`）。没跑：F/D、C、SPEC rv64、rv64 的综合和面积；RTL 的 rv64 配置只作为 `XLEN_BITS=64` 副本验证，`back_top.sv` / `exu.sv` / `soc_top.sv` 的生成器没同步（见 TODO）。
- **已知问题**：对 RTL 比周期必须给模型设 `LSU_PIPE_NOWD=1`（否则 63 周期看门狗让 store 重发，`crc32` 等差几十周期，不是 RTL 偏差）；function-model 的 rv64 MMIO `sd` / `ld` 只按 4 字节读写设备寄存器（Linux 不受影响）。
- **对应记录**：EXPLORATION.md EXP-029；总仓库、function-model `b388f39`、trace-model `ccc2d0c`、rtl `8dbb7cd`；数据 `~/personal/AI-Huma-data/linux_rv64`。

### 2026-11-11 紧凑 ROB + 寄存器 BPU 额度，同批清理（EXP-028）

- **配置变化**：

| 参数 | 旧值 | 新值 |
|---|---|---|
| `CFG_ROB_COMPACT` / RTL `ROB_COMPACT` | 无（行式 ROB：一个分发组占一行，整行提交） | **1**（按序分配、前缀提交；`-DCFG_ROB_COMPACT=0` 回到行式） |
| BPU 提交额度 | 无（BPU 更新队列 8 项、uBTB 训练队列 4 项满了就丢） | 寄存器版：额度 = 本拍开始时空位 − 上一拍提交的分支数 / 取指块结束数；只在紧凑模式下用 |
| 可缓存窗口 | 0x40000000–0x4fefffff、0x80000000–0xffefffff，另有非缓存 RAM 窗口 | 0x40000000–0x4fffffff、0x80000000–0xffffffff，其余全是 MMIO（`SIM_UNCACHE_*`、`simulator_is_uncached_memory_addr` 删掉） |
| `BPA_TAGW/CNTW/UW/WEAK/UALT/ALLOC/URST`、`BPA_SC*`、`BPA_NOTC`、`BPA_CMTSYNC/NOCMTSYNC` | 运行时开关 | 删除（固定为原默认值 / RTL 的值；`BPA_HLEN` 保留） |

- **设计改动**：
  - trace-model `35b3af4`（默认关）：`Rob.cpp`/`Rob.h` 紧凑模式（`comb_commit_compact`、`single_actions` 两种模式共用）、`Dispatch.cpp` 按尾指针编号并按空闲项数放行、BPU 送出 `upd_free`/`tq_free`（寄存器）；`PeripheralAxi.cpp` 非缓存读通路、`config.h`/`mmio_address_map.h` 窗口；`pmu_events.def` 17 个 `FEO_*` 事件、`front_top.cpp` 统计、`scripts/pmu/fe_summary.py`；FTQ 提交信息去掉 `altpcpn`、`sc_used`；TAGE 参数常量化、删 SC、删目标缓存 / BHT / mode 表、删调试打印；`PROJECT.md` 加 `CFG_ROB_COMPACT`。
  - trace-model `a11b1ca`：`CFG_ROB_COMPACT` 默认 1，`baseline.csv`、`PROJECT.md` 大程序标准周期。
  - rtl `4e954d7`（默认关）：新 `rob_core_cpt.sv`（约 330 行），`rob.sv` 按 `ROB_COMPACT` 二选一；`dispatch_core`/`dispatch_fire_ctl` 编号与空闲检查；`bpu_updq`/`bpu_ub_tq` 占用经前端、`core_top`、`back_top` 接到 ROB；`lsu_pkg::is_mmio_addr`、`peripheral_axi(_ctl)`、`mem_top`、`soc_top`（`env_region` → `env_modeled`，删非缓存写）、tb 地址表；`altpcpn` 从 BPU、PTAB、front2back、pre-IDU 队列和核心胶合层删掉；`ref_cycles.txt` 1 个程序。
  - rtl `a905acd`：`ttg_cfg_pkg.sv`（`ROB_COMPACT=1`）、`ref_cycles.txt` 37 个程序。
  - rtl 分支 `exp/lsu-stwin` 删除（内容已被 main 覆盖）。
- **验证范围**：见上表。没跑：RTL 上的 SPEC；时序综合；面积代理是在清理前的紧凑 RTL 上测的（清理不动 `rob`/`dispatch`）。
- **已知回退**：gcc sp48/sp21/sp12/sp2 约 −37%、sp5 −26%、xalancbmk sp12 −9.5%、perlbench sp38 −8.6%；dhrystone +1.8%、coremark +0.6% 周期。原因：额度挡住提交后，BPU 更新队列每拍只写回不到 1 条，分支密集的循环被卡在约每拍 1 个分支（行式 ROB 时这些更新 89% 被丢掉）。PMU 把这段停顿记成 `SLOT_BE_SERIAL`（实际是 ROB 满）。两项都在 TODO。
- **对应记录**：EXPLORATION.md EXP-028；数据 `~/personal/AI-Huma-data/robc`（30 点、`full/` 全量与 `score2.py`、`mm/` 合入验证）、`~/personal/AI-Huma-data/robc_rtl`（`gate_final`、`linux_full`）。

### 2026-11-11 删除 0x87f00000 非缓存窗口 + PMU 缺失标记（EXP-027）

- **配置变化**：

| 参数 | 旧值 | 新值 |
|---|---|---|
| `SIM_UNCACHE_DDR_RESERVED_*`、`SD_DMA_POOL_*` | 0x87f00000，1 MB | 删除 |
| 可缓存窗口（`SIM_CACHE_ADDR_*`） | 0x40000000–0x4fefffff、0x80000000–0x87efffff、0x88000000–0xffefffff | 0x40000000–0x4fefffff、0x80000000–0xffefffff（删 `SIM_CACHE_ADDR_3_*`） |

- **设计改动和修掉的 bug**：
  - trace-model `62e4a8b`：`config.h`、`mmio_address_map.h` 删窗口；`baseline.csv` 3 个程序；`PeripheralAxi.cpp` 注释。
  - trace-model `07d567c`：`RealLsuPipe.cpp` `comb_lsu2rob_p` 的 TMA 缺失标记由 `uint64_t` 改为 `std::bitset<ROB_NUM>`（ROB 后 64 项的 L1D 缺失原被记成"访存未缺失"，只影响 PMU 归因）。
  - rtl `1205bff`：`lsu_pkg::is_mmio_addr` 两段；`ttg_cfg_pkg.sv` 重新生成；`tb/soc/platform/include/{config.h,mmio_address_map.h}` 同步；`ref_cycles.txt` 3 个程序。
  - rtl `de8d0aa`：`scripts/tm_cycles.sh` 导出 `ROOT`（原来 `directed/*` 程序路径为空、挂到 900 秒超时）。
- **验证范围**：跑了 trace-model gate、8 个大程序、trace-model Linux 到 login；RTL lint、`fm_gate` 69/69；SPEC 全量 580 点（构建为 `exp/fe-pmu` + 窗口可缓存，即 main + write buffer、无 ITT；抽查两点不改窗口时与基线周期逐个相同）。合入后补跑了 RTL Linux 13 段（s01–s13，本机 13 个并行，每段 1600 万周期，逐提交与函数模型对比）13/13 通过，每段检查 692 万到 2424 万条指令，0 不一致。**没跑**：RTL 从复位连续启动、带 ITT 的当前 main 删窗口后的 SPEC 全量（分数 11.22 是把删窗口的逐程序 IPC 比值乘到 ITT 全量上估算的，用户认为不必为此重跑）、综合。
- **已知回退**：无；580 个点没有一个变慢。
- **对应记录**：EXPLORATION.md EXP-027；数据 `~/personal/AI-Huma-data/mmio`（`cmp.py`、`score.py`、`cmp_result.txt`）、`~/personal/AI-Huma-data/fepmu/tma_fix`、`~/personal/AI-Huma-data/linux/uncwin`、`~/personal/AI-Huma-data/uncwin_rtl`。

### 2026-11-09 LSU 访存相关推测 + 前端快速通路（EXP-019 / EXP-020 / EXP-023）

- **配置变化**：

| 参数 | 旧值 | 新值 |
|---|---|---|
| `CFG_LSU_MEMSPEC` / RTL `LSU_MEMSPEC` | 0 | **1**（kill switch：模型 `LSU_MEMSPEC=0`，RTL `bash scripts/gen_cfg.sh -DCFG_LSU_MEMSPEC=0`） |
| `CFG_LSU_MS_DATA`（模型值路径，仅 MEMSPEC=1 时有效） | 无 | 1 |
| `CFG_LSU_MDP_BITS`（等待表索引位数，表 64 × 1） | 无（实验阶段 12） | 6，RTL 里是生成器写死的常量 |
| `CFG_LSU_MDP_CLR`（等待表清零周期） | 无 | 2000，RTL 里是写死的常量 |
| `CFG_LSU_MDP_HW`（训练方式） | 无 | 2（违例标志寄存，每拍训练一个标志项，表在违例后两拍写入） |
| `CFG_LSU_MDP_MODE` / `CFG_LSU_MS_SLOTS` | 无 | 0（等待表）/ 0（不限推测 load 数），只在模型里 |
| `CFG_FE_RFAST` / RTL `FE_RFAST`（4 位：S0 在重取指周期发射、PTAB 旁路、重定向后 I$ 立即 ready、pre-IDU 缓冲旁路） | 0 | **15**，RTL 里是写死的常量 |
| `CFG_FE_BFAST` / RTL `FE_BFAST` | 0 | 0（保持关；深度 +34%） |
| `FE_PAIR`（两块并取）、`FE_IPF`（I$ 预取） | 无 | 只在模型里，环境变量、默认 0，**RTL 没有** |

- **开关策略**：导出给 RTL 的开关只有两个：`LSU_MEMSPEC`（默认 1，kill switch）和 `FE_BFAST`（默认 0）。`LSU_MDP_BITS`、`LSU_MDP_CLR`、`FE_RFAST` 是 `harness/tools/gen_cfg_pkg.py` 里 `FIXED` 的常量，不从 `config.h` 导出；其余（`LSU_MDP_HW/MODE/SLOTS`、`LSU_MS_DATA`、`FE_PAIR`、`FE_IPF`）是模型的宏或环境变量，RTL 不读。注意：RTL 的 kill switch 只关 `LSU_MEMSPEC`，`FE_RFAST=15` 关不掉，所以 RTL 无法逐位还原成 main 的设计；模型的旧配置回归（`LSU_MEMSPEC=0 FE_RFAST=0`）只在模型一侧成立。模型要保持 `LSU_MS_DATA=1`：`LSU_MEMSPEC=1` 而 `LSU_MS_DATA=0` 时模型与 RTL 在 dhrystone、vm_pagefault_test 上分别差 66、1 个周期。

- **设计改动**（一句一条）：
  - 访存推测：load 可越过地址未知的更老 store；推测 load 的第一次写回先延迟、ROB 不完成（`rob_defer`），STA 到达时 CAM 检查每个 LDQ 项（`lp_ent_ms`），违例 load 二次写回并在提交时冲刷（`flush_pipe`，pc+4 重取）；用 PC 哈希查等待表（`lp_mdp`，64 × 1 位，每 2000 周期清零），表里置位的 load 不推测。
  - RTL 的 FTQ 给 dispatch 读 PC：64 选 1 的块基 PC 加 4 × 偏移，不用 8 个 512 选 1 读口（+16.9k 单元，**不计入上表的 `pre_idu_queue`**）；6 位 PC 哈希进 `dis_inst_t` 和 LDQ 项。
  - 重叠判断 `lp_ovl`：一个对数深度比较器代替两个加法器和三个比较，`lp_cam` 73.7k → 31.3k 单元（×4 口），关闭推测时也受益；`lp_cam` 的 `unk` 复用 find-first 的前缀。
  - 值路径（EXP-020，模型）：推测 load 读到未被更老 store 覆盖的旧值，消费者按真实 ISA 语义用旧值计算，分支可能因旧值翻转，成为只在 RTL 里出现的预测错误。模型按轨迹里的事实执行、不算数据，RTL 执行真实数据；没有这条路径时两者在 dhrystone（27 次同一条分支的翻转，+66 周期）和 vm_pagefault_test（+1）上周期不同，`LSU_MS_DATA=1` 把这个效果放进模型，所以现在模型周期等于 RTL。
  - 修掉的 bug：违例检查漏掉停在 `L_RPW` 的 load（被更老 store 挡住、被唤醒后直接从该 store 转发，没有第二次 CAM，漏掉它越过的更年轻 store）；是 RTL Linux 逐条对比发现的，模型靠轨迹事实看不到。
  - 前端：`FE_RFAST` 四个位见 EXPLORATION EXP-023；`bpu_spec` 里重取指专用的 S0 状态（`spec_r1`/`sras_r1`），快速配置下历史用一步线性多位推入（`bpu_hist_vec`）；`front_pred_path` 把 `slot_kind` 声明提到使用之前（原文件被 slang 拒绝，`lint.sh` 此前只对它做规范检查）；`icache_kill` 对 RFAST bit2 加 `accepted_now`（RTL 的 I$ AXI 接收脉冲比模型早一拍，不修会在 6/67 个程序上差 1–4 周期）。

- **SPEC 全量（580 点，快速预热 `FASTWARM=1000000`，`PF_ENABLE=1`，`PMU=1`，服务器 106.14.7.26）**：基线 = 同一台服务器上构建的 main `7f8456e`（`/root/integbase/res`），因为已有的全量结果是 EXP-015 的 main（无 PMU）或零散的 EXP-017 局部结果；这个新基线与 EXP-015 全量（`lsubpu/full_new`）的几何平均比为 1.0000（一致性检查）。580/580 成功，无失败。SimPoint 权重 CPI，12 个程序几何平均（`trace-model/scripts/integ/spec_cmp.py`）：

| 程序 | 点数 | IPC main | IPC 合并 | 变化 |
|---|---|---|---|---|
| 429.mcf | 79 | 0.5394 | 0.5523 | +2.40% |
| 403.gcc | 55 | 1.9366 | 2.0591 | +6.33% |
| 462.libquantum | 51 | 2.2475 | 2.4931 | +10.92% |
| 473.astar | 35 | 1.2500 | 1.5314 | +22.51% |
| 445.gobmk | 50 | 1.6986 | 1.9150 | +12.74% |
| 401.bzip2 | 76 | 1.5146 | 2.0895 | +37.95% |
| 458.sjeng | 28 | 1.7251 | 2.0656 | +19.73% |
| 483.xalancbmk | 51 | 2.0868 | 2.1600 | +3.51% |
| 464.h264ref | 37 | 1.5882 | 1.6465 | +3.67% |
| 471.omnetpp | 40 | 1.3886 | 1.4624 | +5.32% |
| 400.perlbench | 44 | 2.1725 | 2.3979 | +10.38% |
| 456.hmmer | 34 | 3.4736 | 3.5441 | +2.03% |
| **几何平均** | 580 | | | **+11.02%** |

  不加权的逐点几何平均 +11.63%，最大 ×2.77，最小 −4.3%（401.bzip2 sp20），没有低于 −5% 的点。估算分数 9.42 × 1.1102 = **约 10.46 分/GHz**：参考时间没有核对官方表；9.42 是最后一次记录的分数（EXP-015 全量），EXP-016/017 在其后合入（EXP-017 −0.05%），所以起点是近似值。
- **收益拆分**（便宜的估计，来自已有的 25/30 点精确预热结果，不可相加）：`FE_RFAST=15` 约 +2.6%（25 点）；访存推测 +5.35%（30 点，`LSU_MS_DATA=1`）；全量合计 +11.0% 大于二者之和，主要来自 bzip2、astar、sjeng，**拆分没有在全量上验证**。早先的模型组合运行（`exp/combo`）报过 +20.16%，**不是 RTL 能得到的数字**：RTL 里没有 `FE_PAIR`、`FE_IPF`，`FE_BFAST` 关闭，RTL 对应的模型数是 +11.02%（+20.16% 的出处笔记本次整理时没有找到，数字照负责人给出的写）。
- **TMA 一级**（12 个程序各取权重最高的点，快速预热，`PMU=1`，12 个平均，槽位 %）：Retiring 41.7 → 43.2，BadSpec 9.3 → 7.3，Frontend 29.7 → 31.5，Backend 19.3 → 18.0。BadSpec 降幅最大：gobmk 23.7 → 18.3、sjeng 21.2 → 15.3、astar 14.7 → 11.7、mcf 18.5 → 15.0；sjeng 的 Backend 20.0 → 11.9。原始数据在服务器 `/root/integ/tma`、`/root/integbase/tma`，本机 `~/personal/AI-Huma-data/integ/`。全量运行里 `PMU=1` 的 `pmu_*.csv` 写在同一个 cwd、被并发的点互相覆盖，所以没有逐点 TMA，TMA 来自单独的最高权重点运行。
- **综合与深度**（见上表，相对数字）：判据是"没有模块比 main 深 5% 以上"，除 `front_pred_path`（134 → 142，+6%）外都满足。`front_pred_path` main 一侧的数字（226,649 单元、深度 134）是在**临时副本**上量的：main 里的文件被 slang 拒绝（`slot_kind` 先使用后声明），合并后的树已改好声明顺序。`bpu` 本身更浅（149 → 141）。`FE_BFAST=3` 在前端笔记里量到 192（+43%），所以 `FE_BFAST` 保持关。`lsu` 总单元 −7.7%：`lp_cam`、`lp_l1b` 变小（重叠判断重写，对关闭推测的设计也有利），`lp_ldq` +56k，新增 `lp_ms` 4.3k；笔记没有把"推测本身的代价"和"重写的收益"拆开，**不能把 −7.7% 当作推测免费**。新增触发器合计约 779（LSU）+ 128（ROB）+ 48（dispatch）。
- **文档之间互相矛盾或没有对上的数字**（不隐藏）：
  1. **BPU 面积**：合并笔记的综合表里 `bpu` 是 223,476（main）→ 202,257（合并后），即 −9.5%；前端笔记按 `FE_RFAST` 逐位量的结果是 off 199,240、`RFAST=15` 237,174（**+19%**，来自重取指专用状态和第二套历史更新网络）。两组数字来自不同的综合脚本（`synth_cfg.sh` 轻量 ABC 与 `synth_depth.sh` 平衡 ABC）和不同的树（前端笔记早先量到的 off 是 222,883，与合并笔记里 main 的 223,476 接近，而与同一笔记后面的 199,240 差 12%）。没有在同一流程里对合并后的树做 `RFAST=0` 与 15 的对比，所以"RFAST 的真实 BPU 面积代价"没有定论；保守起见按 +19% 理解，合并后 `bpu` 总量比 main 低的原因没有查明（综合噪声笔记里写约 ±10%）。
  2. **memory-stress-small 周期**：trace-model 默认 328,606，RTL 参考表（`LSU_PIPE_NOWD=1`）328,787；RTL 没有 LDQ/STQ 看门狗，参考表与默认模型在个别程序上本来就会不同（EXP-015 已记过），这一项没有逐个核对原因。
  3. **程序个数**：模型 gate 64（63 + load-store），RTL 68（67 + `directed/memspec_vio`），不是同一组。
  4. **dhrystone 的中间数字**：只开访存推测（`FE_RFAST=0`）116,217；访存推测笔记里的 115,896 是更早的 `LSU_MDP_HW` 模式；默认配置 114,299。
  5. **服务器 gate**：前端笔记里服务器 64/67，3 个 zfinx 程序在服务器旧的 `librefcpu.a` 上对函数模型检查失败（所有设置、包括全关），环境问题；本机测试平台 67/67，合并后 68/68。
- **模型和 RTL 能相等的前提**：靠 `LSU_MS_DATA` 值路径（上面第三条设计改动）。它覆盖旧值、污染传播和分支翻转；**没有在 RTL 上验证的情况**：旧地址的 load/store（模式位 2，30 点里也没跑）、CSR/FP/AMO 消费者（这批程序里没有出现）。30 点上它使模型收益从 +5.30% 降到 +5.21%（预言机模型高估约 0.09 个百分点）。
- **违例代价**（模型 `[MS_PENALTY]`）：从检测到恢复提交 28–52 个周期，其中真正损失（提交空闲）13–32 个周期；约 55% 的违例会走到冲刷提交（其余死在错误路径上）。
- **已知回退与风险**：
  - 最差点 −4.3%（bzip2 sp20）；TMA 里 BadSpec 降，但 Frontend 占比升（29.7 → 31.5）。
  - `front_pred_path` 深度 +6%（超过 5% 判据）；`FE_RFAST=15` 的 BPU 面积 +19%（见上）；没有时序库，深度只是通用门级数。
  - 违例检查的 `L_RPW` 漏洞只被 RTL Linux 逐条对比抓到，说明 gate 程序和模型覆盖不到这类情况；合并后的树上 Linux 是 13 段检查点接力。
  - FTQ 读口的 +16.9k 单元不在上表里；`spec/*.io` 没更新。
- **没跑**：RTL 上的 SPEC；合并后的 RTL 树上从复位一次连续跑到 `rv32 login:` 的 Linux（只做了 13 段接力，微架构每段冷启动）；小 LLC 检查（模型和 RTL）；有工艺库的综合与时序（WNS）；`FE_PAIR`、`FE_IPF` 的 RTL；FTQ 读口面积计入；`spec/*.io` 更新。服务器上 FE 扫描的 3 个 zfinx 程序在旧 `librefcpu.a` 上失败，是环境问题，不是这次改动。
- **对应记录**：EXPLORATION.md EXP-019、EXP-020、EXP-023；各仓库 commit：trace-model `31bfb03`（`exp/integ`，快进）、rtl `29e535b`（`exp/integ` `bd6ba1d` 快进，再 cherry-pick 前端笔记提交 `71468eb`，只改 `RTL_FE_NOTES.md`）。分支内笔记：trace-model `INTEG_NOTES.md`、`MS_DATA_NOTES.md`（`97cca34`）、`FRONTEND_NOTES.md`（`exp/frontend`，工作区 `trace-model-fe`，未合入 main）；rtl `RTL_INTEG_NOTES.md`、`RTL_MEMSPEC_NOTES.md`、`RTL_FE_NOTES.md`。

### 2026-11-08 后端资源 DSE 的支持代码（EXP-016）

- **内容**：没有改任何默认配置。trace-model：`CFG_LDQ_SIZE`（默认 64，LDQ 大小此前写死）；PMU 新增 `SLOT_FE_OTHER_NOPREG`、`SLOT_FE_OTHER_NOBRTAG`（把取指带宽空槽中"重命名没有空闲物理寄存器"和"IDU 没有空闲分支标签"拆出来），在 `pmu_events.def` 里追加到表尾并标 `// model-only`；`scripts/dse/`（服务器扫描、本机运行、汇总）、`scripts/pf/points_dse*.txt`；`replay.sh` 注释里 quick 的点数改为 178。rtl：`gen_pmu_pkg.py` 跳过标 `// model-only` 的事件，且要求它们在事件表尾部（否则事件 id 会与模型错位）；生成的包不变（66 个事件）。
- **为什么 RTL 要这样**：不跳过时 RTL 包变成 68 个事件，两个事件没有驱动，`pmu` 多 162 个单元（+1.4%）。EXP-017 的 IQ 事件也是 model-only，但已经在 RTL 包里，没有改。
- **验证范围**：见上表。RTL 的 fm_gate、lint 是在中间版本（68 个事件的包）上跑的，最终 RTL 的生成产物与 main 逐字节相同，所以沿用 main 的结果，没有再跑；**RTL Linux 没有重跑**（RTL 与 main 一致）；没做综合。
- **结论**（DSE 本身，见 EXPLORATION.md EXP-016）：基线 PRF128 / ROB128 附近已接近拐点；PRF 不能低于 128；MSHR 8→16 约 +0.8%；LDQ 32、STQ 48、INT IQ 32、BR IQ 16 几乎免费，面积收益还没有综合数字。
- **对应记录**：EXPLORATION.md EXP-016；各仓库 commit：trace-model `7f8456e`、rtl `edf9d3b`。

### 2026-11-08 issue queue 入队宽度（EXP-017）

- **内容**：`CFG_{INT,LD,STA,STD,BR}_IQ_ENQ_WIDTH` 默认 7/6/4/4/5（原来都是 DECODE_WIDTH=8）；`isu` 每个 IQ 只实例化这么多入队通道，`iss2dis.ready_num = min(空位, 通道数)`；PMU 新增 `SLOT_BE_IQ_{SPACE,WIDTH}_*`、`OCC_IQ_*`（trace-model 专用）。
- **SPEC**：全量 580 点（快速预热）几何平均 IPC 比 main −0.05%；30 点精确预热 −0.48%（mcf −1.26%、perlbench −1.53%、h264ref −0.40%）。先试的 6/4/3/3/3 为 −1.12%（mcf −3.2%、omnetpp −4.3%），不合格。
- **已知问题**：omnetpp 全量 −0.94%；INT 7、LD 6 比发射口数还宽，能否再降没试；未测时序。LD/STA 合并 IQ 版本（`exp/ldsta-merge`）留到以后。
- **没跑**：小 LLC 检查；SPEC 的 RTL 侧；时序综合。

### 2026-11-08 分级 LSU（含 IPC 修复）+ 流水化 S+R BPU（EXP-015）

- **内容**：LSU_PIPE 分级 LSU（L1/PL12/L2，默认 `CUT=127`、`L2=115`、`DRAIN=3`、`DCAND=4`、`RP=4`）；流水化 BPU（`BPU_PIPE=3`、历史修复、jalr rd=ra 当 call、单张 256 项 ITT 取代 TC/BHT）；isu 的死取消逻辑改成 generate 条件（181 级，原 199）。
- **SPEC 30 点（精确预热）**：几何平均 IPC 比 main **+2.87%**（最小 −6.3%，最大 +19.1%）。
- **SPEC 全量（580 点，快速预热）**：580/580 成功，无崩溃、死锁、不一致；对 main 的 555 个公共点几何平均 IPC **−1.20%**，估算分数 9.54 → 9.42。
- **已知问题**：bzip2 −10.2%、libquantum −5.6%、hmmer −5.3%、h264ref −5.1%、sjeng −2.5%；xalancbmk +7.8%、mcf +6.3%。TMA：bad-spec 降，前端空槽升（S+R 取指气泡）。快速预热对新 BPU 的偏差**未排除**（24 点精确预热诊断没跑成）。RTL 参考周期用 `LSU_PIPE_NOWD=1` 生成（RTL 没有 LDQ/STQ 看门狗），与默认模型在预取开 1 个程序、关 2 个程序上不同。DCW 看门狗事件（RP=4）根因未明。
- **没跑**：SPEC 的 TMA（`PMU=1` 未开，已写入 WORKFLOW 第 6 节第 5 步为默认）；RTL 上的 SPEC；时序综合（1 GHz 未标定）。

### 2026-11-07 PMU（EXP-013）

**配置变化**：无新配置参数；trace-model 环境变量 `PMU`（默认关）、`PMU_OUT`、`PMU_INTERVAL`、`PMU_PCPROF`。周期不变。

**设计改动**
- trace-model：`include/pmu_events.def`（唯一事件表）、`back-end/Pmu*.cpp`、`BackTop::pmu_sample()`、`Dispatch::pmu_slots()`、`Rob::pmu_head_incomplete()`；`scripts/pmu/`（报告、SPEC 逐程序 TMA）；顺带修 `RealLsu::load_miss_mask` 的 64 位掩码（ROB 有 128 项）。
- rtl：`rtl/pmu/`（`pmu.sv` 计数器块 + HPM CSR、`pmu_ev_core.sv` 事件总线 tier 1、`pmu_ev_pkg.sv` 由 `scripts/gen_pmu_pkg.py` 从事件表生成）；dispatch 新输出 `slot_valid`；back_top 新导出 `dis2rob_dis_fire`、`rob_bcast_interrupt`；`tools/gen_backtop.py` 现在能原样生成 `back_top.sv`（补了 `spec/lsu.io` 的 replay 输出）；SoC 测试平台累加事件总线，`scripts/pmu_parity.sh` 逐事件对比。

**验证范围**
- 跑了：见上表"正确性"。另：12 个 SPEC 点（每个程序权重最高的 SimPoint）的 TMA，见 PMU.md 第 7 节。
- 没跑 / 未完成：trace-model 的 Linux 整段启动（只做了 RTL 的 13 段）；RTL 上 SPEC；计数器块接 CSR（软件可见，要改 function-model/OpenSBI 看到的 ISA 约定）；二级以下事件的 RTL 实现（取指延迟/访存拆分、前端、访存、占用）；工艺库综合与 WNS。

**已知问题（不是本次引入）**：前门恢复的 SPEC 点里 `cycle_base` 在预热结束后没清零，`sim-time(cycle)` 比测量窗口少恢复程序用的周期（mcf 点 −0.04%）；dhrystone 的两条 `ret`（打印路径）预测错误率约 100%，原因未确认。

### 2026-11-07 L1D 数据预取器 h1（EXP-009）

**配置变化**（trace-model `DataPrefetcher.h`、`config.h`；rtl `soc_top` 参数 `PF_EN`）

| 参数 | 旧值 | 新值 |
|---|---|---|
| `PF_ENABLE`（trace-model 环境变量）/ `PF_EN`（RTL 参数） | 无（功能不存在） | 1（0 时周期与合入前 main 逐个相等：trace-model 62/62，RTL 67/67） |

**设计改动**
- trace-model：`DataPrefetcher`（步长表项 1 个、度 8、距离 2、页内、深度 8 的请求 FIFO）、LLC-only next-line 引擎、L1D stage1 在空闲 load 口上探测 tag、MSHR 的 `is_prefetch`/`no_fill`、被 demand 命中的在途预取提升为 demand、每行 pf 位；LSU 重发请求带 `replay` 标志，不参与训练。
- rtl：`dcache_pf.sv`（新）+ dcache s1/s2/mshr/arr 等的接线，LSU 到 dcache 的 `replay` 信号；`docs/modules/dcache_pf.md`。
- 评测：稀疏检查点恢复（function-model `refcpu_sync_*` 只拷变化的页）；`scripts/pf/` 全量 SPEC 脚本；`scripts/linux_segments.sh`。

**验证范围**
- 跑了：trace-model gate 63/63（新基线），关预取对 main 基线 62/62；RTL `fm_gate.sh` 67/67（开、关各一遍，周期与 trace-model 逐个相等，0 个函数模型不一致）；lint、lint_chip；Linux 13 段 0 不一致（合并后的树）；pf-stress；SPEC full 580 点（fast warmup）；12 个最差点精确预热重跑。
- 没跑 / 未完成：RTL 上的 SPEC；工艺库综合与 WNS；`axi_llc` 读响应队列深度 RQD=8 在预取下的重新测量；跨页预取的 DTLB 代价。

**已知回退**：5 个 SPEC 点低于 −10%（最差 omnetpp sp22 −40.7%），gobmk/hmmer/sjeng 分别 −0.8%/−1.6%/−3.0%；LLC-only 引擎在预取几乎不被用到的程序上浪费 DRAM 带宽和 MSHR（见 EXPLORATION EXP-009 第 11 节）。新增触发器约 1,460 个（`dcache_pf` 422 + 阵列 pf 位 1,024 + MSHR 16），`dcache_pf` 4,172 个单元、`dcache_mshr` +635 个单元（2026-11-07 重测）。

### 2026-11-06 mov 消除（EXP-012）

**配置变化**（trace-model `include/config.h` 新增两项；rtl `ttg_cfg_pkg.sv` 由 `make cfg` 生成，与之逐字节相同）

| 参数 | 旧值 | 新值 |
|---|---|---|
| `CFG_MOVE_ELIM` / rtl `MOVE_ELIM` | 无（功能不存在） | 1（0 时周期与逐条对比与合入前完全相同，RTL 不生成新逻辑） |
| `CFG_MOVE_ELIM_REFS` / rtl `MOVE_ELIM_MAX_REFS` | 无 | 7（架构引用计数 3 位） |

**设计改动**
- Ren：`addi rd, rs, 0` 不取空闲寄存器，rd 共用 rs 的物理寄存器；提交时用架构引用计数 `arch_cnt` 决定旧寄存器何时放回空闲表（冲刷无需回滚计数）；`free_head_commit` 跳过被消除的 mov。
- 引用上限：源来自推测 RAT 且 RAT 引用数 + 组内更老写者 + 1 ≤ 7 才消除（`Ren::elim_refs_ok` / `ren_elim_sel`）。
- Dispatch/ROB：被消除的 mov 不产生 uop、不置 busy 位，ROB 条目 dispatch 时完成；`me_elim` 一位贯穿 Ren → Dispatch → ROB → Ren。
- 新增 `scripts/tm_cycles.sh`（用 trace-model 重新生成 `ref_cycles.txt`）；trace-model `ME_CHECK=1` 不变量检查（计数、泄漏）。

**验证范围**
- 跑了：trace-model gate 62/62（对新基线）、大程序、trace-model 与 RTL（逐条对比）Linux 从复位到登录、`ME_CHECK=1`；RTL `lint.sh`/`lint_chip.sh` 0 警告（开、关两种）、`fm_gate.sh` 66/66（开：周期与 trace-model 逐个相等；关：与原 `ref_cycles.txt` 逐个相等）；quick SPEC（trace-model，开/关各一遍，129 点）。
- 没跑 / 未完成：Linux 启动的"N 条指令已检查"汇总；RTL 上的 SPEC；时序综合；整机面积；`add rd, rs, x0`（不处理）；同拍提交带目的寄存器的指令与分支误预测（ME 模式下 `Assert`，从未触发）。

**已知回退**：`ren` +24.8k 单元（+12.0%，含 384 个计数器触发器）；`ren` 最长组合路径 63 → 130 级（消除判定串在分配之前，见 EXPLORATION EXP-012），没有工艺库、未评估真实时序。收益只有 coremark −1.15% 周期、quick SPEC 几何平均 IPC +0.06%，在噪声量级，这是有意按负责人决定合入的。

**对应记录**：[EXPLORATION.md](EXPLORATION.md) EXP-012；[LOG.md](LOG.md) 2026-11-06 各行；各仓库 commit：trace-model `767c25f`、rtl `1e5d656`。

### 2026-11-06 DRAMsim3 DDR、去掉 AXI 子系统分频（EXP-006）

**配置变化**（trace-model `include/config.h`、`Makefile` 的默认值；rtl `ttg_cfg_pkg.sv` 由 `make cfg` 生成，与之逐字节相同）

| 参数 | 旧值 | 新值 |
|---|---|---|
| `CONFIG_AXI_SUBSYSTEM_FREQ_DIV` | 16 | 1（每个核心周期一个子系统 tick；rtl `mem_top` 的 tick 数取自它） |
| `CONFIG_CPU_FREQ_MHZ` | 500 | 1000（可用 `CPU_FREQ_MHZ` 环境变量运行时覆盖） |
| DDR 模型 | 固定 60 tick 读延迟的 SimDDR | DRAMsim3 `DDR4_8Gb_x16_3200`，非核心附加延迟 60 ns（SOC 20 + CDC 12 + CTL 15 + PHY 13，`DS3_EXTRA_NS` 可改）；`gmake DS3=0` 仍可用旧模型 |
| 平均读延迟（AXI 口到数据返回） | 60 tick = 3.75 个核心周期 | 小程序约 85–87 ns，memory-stress-small 约 105 ns |
| LLC 读响应队列 `RQD` | 4 | 8（Linux 启动实测峰值总占用 4，trace-model 为 32 项） |
| LSU store 提交窗口（RTL） | 20（误用 load 窗口） | 15（`LSU_STORE_WINDOW_WIDTH`，与 trace-model 相同） |

**设计改动与修掉的问题**
- trace-model：`SimDDR` 增加 DRAMsim3 后端（`SimDDR_DS3.h`，`DS3_EXTRA_NS`、`DS3_CONFIG`、`DS3_STATS`）；DRAMsim3 作为固定版本子模块 `third_party/DRAMsim3`（`2981759`），由 Makefile 编成静态库（`gmake dramsim3`），缺子模块时报错并提示 `git submodule update --init`；`config.h` 导出 `AXI_SUBSYSTEM_FREQ_DIV`；`baseline.csv` 与 `PROJECT.md` 标准周期重新生成。
- rtl：`mem_top` 的 `phase_q` 在 `TICKS-1` 回零，`TICKS == 1` 时 `phase0`/`phase_last` 编译期恒为 1；测试平台 `soc_tb` 的 tick 数取自配置，空闲 tick 跳过仅在 16 tick 时启用，复位期间不推进 DDR；平台 SimDDR 换成 trace-model 的版本（加 `SIM_DDR_DATA` 数据服务）；`build.sh` 链接子模块的静态库；`ref_cycles.txt` 重新生成。
- **rtl 潜在错误（第 3 批改端口后遗留，被 16 倍分频掩盖）**：LSU store 提交窗口误用 load 窗口（20 对 15），链头 store 被重放卡住时会提前发出窗口外的 store（pascal 第 1031 周期 vs trace-model 1038）；`wait_mmu_stq`、`mmu_done_stq` 经通用 `ring_apply` 仍按 20 处理（`exp/lsu-stwin` 的 `b94b4f5` 已完整修复，尚未合入，后面单独做）。
- rtl 另一个被分频掩盖的问题：LLC 读响应队列 `RQD=4` 在不分频下被 Linux 启动溢出（断言停机）。
- 速度：RTL 仿真由约 4.4 千周期/秒提到约 35 千周期/秒（约 8 倍，每周期 1 个 tick）；trace-model 约 16–19 万周期/秒。

**验证范围**
- 跑了：trace-model gate 62/62、大程序、Linux 到登录；RTL `lint.sh`/`lint_chip.sh` 0 警告、`fm_gate.sh` 66/66（周期与 trace-model 全部相等）、Linux 从复位到登录全程逐条对比（`RQD=8`，32 ns 和 60 ns 两个基线各一次）；SPEC full 580 点；受影响模块的 yosys 面积代理。
- 没跑：16 倍分频配置（**不再支持，也没有回归**）；RTL 上的 SPEC；时序综合（没有工艺库和约束）；Linux 启动的"N 条指令已检查"汇总；store 数据仍不在逐条对比范围内。
- 估算 SPEC 分数用的参考时间是凭记忆写的，没有核对官方表；附加延迟 60 ns 取自 `config.h`，没有按目标芯片校准。

**已知回退**：所有程序周期变多（gate 63 个程序周期相对 32 ns 版平均 +23%，相对第 3 批基线 dhrystone +7.7%、coremark +9.4%、memory-stress-small +83.6%），SPEC 几何平均 IPC 相对旧基线 −30%（quick 6 个程序，2.204 → 1.550）；这是旧数字偏乐观的修正，不是设计退步。面积：LLC +33.3k 单元（`RQD`）、LSU −23.4k 单元（store 窗口），净约 +9.9k。

**对应记录**：[EXPLORATION.md](EXPLORATION.md) EXP-006；[LOG.md](LOG.md) 2026-11-05、2026-11-06 各行。

### 2026-11-05 第 3 批面积配置（EXP-005）

第一次按 [WORKFLOW.md](WORKFLOW.md) 第 6 节把架构探索的结论合入 main。

**配置变化**（trace-model `include/config.h` 的默认值；rtl `ttg_cfg_pkg.sv` 由 `make cfg` 生成）

| 参数 | 旧值 | 新值 |
|---|---|---|
| `BACKEND_FETCH_WIDTH` | 16 | 8（= `FETCH_WIDTH`，16 是遗留值） |
| `MAX_BR_NUM`（在飞分支） | 64 | 32（`BR_MASK_WIDTH` 32、`BR_TAG_WIDTH` 5） |
| `IDU_INST_BUFFER_SIZE`（ibuf） | 128 | 64（`FTQ_OFFSET_WIDTH` 3） |
| `FRONT2BACK_FIFO_SIZE` | 32 | 8 |
| IQ INT / LD / STA / STD / BR | 128 / 64 / 64 / 64 / 64 | 64 / 64 / 64 / 16 / 32（共 240 项，原 384） |
| 发射端口 ALU / LD / STA / STD / BR | 6 / 4 / 4 / 4 / 4 | 6 / 4 / 3 / 3 / 2（`ISSUE_WIDTH` 22 → 18） |

**设计改动与修掉的问题**
- trace-model：尺寸改为 `CFG_*` 开关（先以原值提交、周期不变，再单独改默认值）；`IQ_*_SIZE` 标量供 RTL 参数生成器使用。
- rtl：IQ 大小、FIFO 深度、字段位宽（br_mask、br_id、ftq_offset、ready_num）、LSU 通道数、FU 表都改为从配置推出；`gen_cfg_pkg.py` 读前端 FIFO 深度；`dimmap.py` 增加位宽规则。
- rtl 潜在错误：`lsu_core` 的 store MMU 请求端口按 load 端口数声明（两者相等时不暴露）。
- 测试平台错误：按写死的位偏移读 STQ 字段，br_mask 变窄后外设收到错字节（串口乱码、中断不来），逐条对比没有报——现在偏移由配置推出。
- 新脚本：`rtl/scripts/fm_gate.sh`、`lint_chip.sh`、`synth_cfg.sh`；function-model `scripts/spec/`（SPEC 检查点流程）一并合入。

**验证范围**
- 跑了：trace-model gate 62/62、大程序、Linux 到登录；RTL `lint.sh`/`lint_chip.sh` 0 警告、66 个程序逐条对比、Linux 从复位到登录全程逐条对比、原配置下回归（周期逐个不变）；quick SPEC 6 个程序。
- 没跑：full SPEC；RTL 上的 SPEC；时序综合；store 数据仍不在逐条对比范围内（以串口输出对比补充）。

**已知回退**：coremark +2.9% 周期、quick SPEC −0.5% IPC（gcc −1.3%），换取约 17% 的门数和 27% 的触发器。

**对应记录**：[EXPLORATION.md](EXPLORATION.md) EXP-001…005；[LOG.md](LOG.md) 2026-11-05 各行。

---

### 2026-11-20（EXP-048：L1 硬件 Berti + LLC BOP + MSHR 16/16）

- **版本**：trace-model `6df4312`、rtl `6e2d188`、function-model `55affa0`。
- **正确性**：RTL `lint_chip.sh`（Verilator 5.052）0 警告；`fm_gate.sh` 64/64 PASS（0 FM 不一致、与默认 `trace-model` 0 周期差）；trace-model 单次从复位启动 rv64gc Linux 5.15.170 直达 `rv64 login:` PASS（135M 指令，IPC `0.8594`）；27 窗 5M 步长 rv64gc Linux（`s00..s26`，每窗 ≥5.1M 指令，无缝覆盖 `0 → 135.1M` 共 1.377 亿条指令）RTL vs `trace-model` **27/27 `PT`/`UP` 指纹逐周期相等、0 FM 不一致**（`s00` 仅 PMU 恢复计数归类差异，执行流零分歧）。
- **性能**：
  - **SPEC CPU2006 INT（12 程序 386/386 点）**：`11.37 → 12.11 /GHz`（**`+0.75 分/GHz`，`+6.58%`**，零回退；`462.libquantum +37.14%`、`429.mcf +28.14%`、`403.gcc +7.90%`、`473.astar +3.35%`、`471.omnetpp +2.33%`、`401.bzip2 +2.13%`）。
  - **固定负载（默认 `trace-model` = RTL，0 周期差）**：`coremark` `290,676`（0.00%）、`dhrystone` `109,797`（+0.82%）、`memory-stress-small` `343,714`（+0.07%）、`pf-stress` `487,806`（−15.6%）、`dcache-conflict-writeback` `4,533`（−24.7%）、`dcache-mshr-pressure` `1,487`（−5.1%）。
- **综合**：未做（后续统一切换 DC 综合）。

**变化**
- **配置变化**：`DCACHE_MSHR_ENTRIES` `8 → 16`；`AXI_LLC_MSHR` `8 → 16`；`AXI_LLC VQD` `8 → 32`（`NVL` `27 → 51`）；L1 预取 `h1 → 硬件 Berti (PF_KIND=4, DTLB 跨页翻译)`；LLC 预取 `关 → Best-Offset (LLC_BOP=1)`；`trace-model` 默认配置同步对齐 RTL（无需 `-D` 与环境变量）。
- **设计改动与修掉的 bug**：
  - RTL M1/M2/M3（`a48d2ec` / `b6f56ea` / `bc42c5e`）：16/16 MSHR、`axi_llc_bop`、`dcache_pf_berti_*` 及 DTLB 空闲口跨页翻译、`dcache_s1` 隐藏重试保留 `rty_pc_q`/`rty_va_q`；
  - `axi_llc_pkg.sv`：`VQD` 8→32，消除 16-MSHR + BOP 下 `s01`/`s07` victim queue 满断言；
  - `idu_ctrl_decode.sv` + `InstDecode.cpp`：补全 RV64IM+Zba/Zbb `OP-32` 精确合法性检查，消除 `s03` 错误路径非法 `OP-32` 改写寄存器分歧；
  - `LsuPipeInternal.h`：`ms_load_value` 删除 `off + lw > XB` 早退并按 RTL `lsu_pkg.sv:extract_data` 统一右移 `8*off` 扩展，消除 `s20` 跨 dword 非对齐陈旧 load 分歧。
- **验证范围**：跑了全量 SPEC06 INT 386/386、RTL `lint_chip.sh` + `fm_gate.sh` 64/64、trace-model 单次从 0 启动 Linux 到 `rv64 login:`、27 窗全量 Linux 对齐；未跑综合（换 DC）及 3 个缺 `vm/` 构建的裸机程序（`fence-i-self-modify`、`unalign`、`wanshu`）。
- **对应记录**：[EXPLORATION.md](EXPLORATION.md) EXP-048；[LOG.md](LOG.md) 2026-11-20；[LINUX_ALIGN.md](../trace-model/docs/LINUX_ALIGN.md)。
