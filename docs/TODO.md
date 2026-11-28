# 待办事项

全项目唯一的待办清单。每条写清为什么、做到什么算完；做完删掉，在 [LOG.md](LOG.md) 里留一行。（2026-11-23 阶段性清理：删除 EXP-029..061 已完成/已取代的条目，收敛为当前有效待办。）风险（验证缺口、变异存活）记在 [rtl/docs/08-risk-register.md](../rtl/docs/08-risk-register.md)，不在这里重复。

## 待做：TSMC 28nm DC 时序收敛（第六轮目标：无黑盒真实 SRAM 整核提频 + 后端 `Issue/RegRead` 拆拍 + 大存储体宏重构）

权威口径：**Synopsys DC `W-2024.09-SP2` + TSMC 28nm HPC+（`ssg0p81v125c`, 12T SVT+LVT, `compile_ultra`）**，**全面禁用 `SRAM_BLACKBOX`、统一采用 `SYNTH_TSMC28_SRAM` 真实 TSMC 28nm SRAM 宏时序/面积签核**；日常快速迭代统一使用四层 PPA 入口 `rtl/scripts/fast_ppa.sh`（Tier 0 秒级 SRAM 估算 + Tier 1 `Yosys+PT` 提速 `14×–49×` + Tier 2a/2b DC 快速与 `.ddc` 增量拼装，详见 [rtl/docs/09-synthesis-report.md](../rtl/docs/09-synthesis-report.md) §15–22 与 [exp/EXP-071-fast-ppa-eval.md](exp/EXP-071-fast-ppa-eval.md)）。
- **前五轮已完成**：EXP-062..065（全核 23 模块单模块突破 ≥1.12 GHz）+ EXP-068（`rob_ptr` 冲刷，`idu` 2.70 GHz）+ EXP-069（全核 100% 严格同步 1R1W/1RW SRAM 化，三后端模块净省 `1.97 mm²`）+ **EXP-070（Unified FTQ-64 删 `ptab_bypass` + LSU/DTLB `paddr_p1/m1` 消除 `back_top` 1.24 ns 往返链 + Clean BPU v11 + 同页双取 + A1/A2/B1 切链 + 零黑盒真实 TSMC 28nm SRAM 综合：`bpu` 156 真实宏达 `877 MHz` / +83%、纯逻辑面积 −59.1%）**。
- **下一阶段待攻克瓶颈按优先级排序**：

| 方向 / 模块 | 当前状态与关键路径线索 | 优化方向 / 做完标准 |
|---|---|---|
| **后端 `Issue / RegRead` 拆拍与 `lsu → isu` 唤醒解耦** | `back_top_bb`（`0.50 ns`）消除 DTLB/LSU `1.24 ns` 往返链后，新顶路径转为 **`u_lsu/u_ldq → u_isu/g_iq[5]`（`1.16 ns / 833 MHz`）**，且当前 `isu` 选择/唤醒与 `prf` 读寄存器紧耦合限制后端进一步冲高频 | ① 拆解 `Issue → RegRead` 流水级，评估 `trace-model` SPEC06 386 点 IPC 代价与唤醒/旁路时序；② 解耦 `lsu` L2 唤醒/取消至 `isu` 路径并拆解 `lp_wk` STLF 数据合并，将 `back_top` 真实 SRAM DC 推上 `≥ 1.0~1.2 GHz` |
| **大存储体物理 SRAM 宏重构与无黑盒整核 DC 签核** | 无黑盒真实 TSMC 28nm SRAM 综合暴露三类面积/布线放大：① `icache_arr` 4×8×`16×512b` 映射到 64-depth 宏存在 ~4× 深度浪费；② `axi_llc` 4 MiB 数据/标签用 1R1W 翻倍面积；③ BPU 8-bank 切分导致 156 颗宏（`1.69 mm²`）且高扇出到 `u_spec`；④ `prf` 多读写口 FF 占比高 | ① 重构 `icache_arr` 阵列形状匹配 64-depth 真宏；② `axi_llc` 数据/标签评估 1R1W→1RW；③ BPU 8-bank 合并为 2~4 bank 压降宏数与布线拥塞；④ 评估分簇 PRF 与剩余 CAM 瘦身；⑤ 完成 `back_top` / `mem_top` / `core_top` 零黑盒真实 SRAM 28nm DC 全签核 |
| **前端无黑盒 `front_top` 进一步冲 1.0+ GHz** | Clean BPU v11 + A1/A2/B1 已将实宏 `bpu` 拉升至 `877 MHz`（顶路径 `u_ftb1` 真宏 → `u_spec/st_q` `1.09 ns`），`front_top` 仍受 `icache`/`front_fetch_buf` 与 `u_ftb1 → u_spec` 约束 | 结合 BPU 降 bank 与 `u_ftb1 → u_spec` 预计算切分、清理 `front_top` 剩余实宏关键路径，将无黑盒 `front_top` 推上 `≥ 1.0 GHz`；同步优化 Clean BPU v11 缺失的 SC/取指带宽以挽回 SPEC06 分数 |

## 待做：验证与对齐

| 事项 | 为什么 | 做完的标准 |
|---|---|---|
| **LR/SC 遇异步中断的保留位对齐（R-7 根因）** | `lp_rsv.sv` 在 `sc` 推测执行时即通过 `sc_clr` 清零 `rsv_valid_q`，若随后异步中断冲刷未提交的 `sc`，`mret` 重执时 RTL 返回 1（保留失效），而 `function-model` 在 `refcpu_take_forced_interrupt` 未清 `reserve_valid` 返回 0，引发 Difftest 分歧（即 `08-risk-register.md` R-7 悬案） | 统一三仓口径：中断/异常冲刷时 RTL 与 `function-model` 同步清保留位（或 `sc_clr` 推迟至提交/非推测态），并用 `lr.d`/`sc.d` + 高频中断回归验证通过 |
| **逐条对比补全 AMO store 比较**（rtl V-12 剩余） | `SOC_TB_FM_STRICT=1` 已补齐 MMIO/跨字 store 数据及 18 个架构 CSR + 特权级对比（77/77 + 152/152 通过），仅剩 AMO 指令写回数据与字节使能未纳入 store 比较 | `tb/core/fm_check.h` 补齐 AMO 写回数据与字节使能对比，严格门禁通过 |
| **收敛 RTL vs `trace-model` 在 120/386 SPEC06 点上的对称周期微差异** | 全量 386/386 SPEC06 INT（10M+10M + 逐条 FM，~77.2 亿指令）已 **0 fail / 0 FM diff 全通**，12 项基准 geomean **`+0.00%`**，266/386（68.9%）实现 0-cycle 完全对齐；剩余 120 点（主要为 `458.sjeng` 0/27、`471.omnetpp` 1/25、`483.xalancbmk` 25/34）呈对称 `±` 周期微差（最大单点 `2.65%`） | 抽 1 个 `458.sjeng` 点做 commit-trace 定位首个分歧周期，确认原因并决定是否对齐至 386/386 0-cycle |
| **从复位 140M 周期 Linux 全程 RTL vs 模型对齐** | EXP-040 时期在 3000–3050 万周期起出现 PMU 区间偏差（+0.29%），近期合入均用 26 段检查点验证，尚未在最新 `main` 跑完整复位对比 | 在 `eda` 跑 8 线程静态 `core_tb` 从复位到 `rv64 login:`，确认逐条 0 不一致并排查是否仍有区间分歧 |
| 检查点窗口比 PMU 区间（`PMU_CMP=1`） | 检查点恢复程序在 RTL 与模型上耗时不同，按绝对周期切 PMU 区间会错位 | 两边在恢复结束处对齐计数，`PMU_CMP=1` 通过 |
| 补齐剩余覆盖缺口、形式等价（CEC）与 toggle 覆盖率 | 已补 `rtl/sva/` 20 个功能覆盖点（100% 命中）、152 官方 `riscv-tests`、8 个定向短测试（行覆盖 `96.44%`）及 RV64GC Fuzzer；尚缺：① `lp_ovl`/`bpu_ub_track_ser`/`bpu_updq`/`bpu_ub_look`/`front_fetch_buf` 等降深度模块的 Yosys CEC / 等价测试；② 集群全量 `--coverage-toggle`（`SOC_COV=all`）与 26 窗 Linux 下的 `SOC_SVA=1` 回归；③ `dcache_resp` `fwd_st`/`fwd_st_full` 与 `lp_ldq_ent` `L2_WBP` 覆盖 | 接入 Yosys CEC 形式等价并上 `eda` 集群跑 `SOC_COV=all` + 夜间万级 seed Fuzzer 扫雷 |
| 扩大 gate（加入 `float_test` / `memory-stress` 等长程序） | 现有 69 个 gate 程序最长仅 ~31 万周期 | `float_test` 及更长定向程序进入常规门禁 |
| F/D 性能标定（SPECfp / PolyBench） | 当前 386 点均为 SPEC06 INT，FP 队列大小/延迟/STD FP 数据口尚未在浮点大负载上标定 | 建 rv64gc SPECfp 或 PolyBench 评测并标定 FP 后端参数 |

## 待做：微架构与 RTL 设计演进

| 事项 | 为什么 | 做完的标准 |
|---|---|---|
| **DCache S1/S2 随 `rob_ptr` 冲刷并移除 LDQ `epoch`** | 当前靠 per-port `epoch` 过滤在飞 DCache 陈旧响应（已在 `lp_core.sv`/`lp_ldq.sv` 补齐），后续若扩大 LDQ/重发深度需担心 `epoch` 位宽回绕 | DCache S1/S2 流水级携带 9-bit `rob_ptr` 并在 `flush_br`/`flush_all` 时直接作废年轻查询，移除 LDQ `epoch` 字段与比较逻辑，通过全量门禁与 SPEC06 回归 |
| **访存违例改为从违例 load 本身冲刷重取** | 当前违例 load 在 LSU 重执行后第二次写回（占 PRF 写口且增加 `lp_wb`/`MsData.h` `early_clean` 复杂度） | 违例 load 随冲刷从自身 PC 重取，第二次写回不占 PRF 写口；删除 `MsData.h` `early_clean` 补丁；SPEC06 量化净收益，模型与 RTL 同步对齐 |
| **香山式独立 SBuffer** | EXP-024 的 STQ 内分组 write buffer 仍占着 STQ 项等响应 | 独立 64B 整行+字节掩码 SBuffer，提交即释放 STQ、按阈值排空、load 查 STQ > SBuffer > DCache；全量 SPEC06 量化收益后再做 RTL |
| **AMO 改为 DCache 内读改写（AMOALU）** | 当前 AMO 拆成 LOAD + STA + STD 同占 LDQ/STQ | AMO 仅占 STQ，队头排空 ROB 后发 DCache 读改写，删除 dispatch AMO 双写口特例 |
| 分支密集短循环 BPU 更新额度优化（EXP-028 遗留） | 紧凑 ROB 为防 BPU 更新队列溢出而限流提交，导致少量分支密集短循环变慢 | 额度不足时不挡提交、仅丢弃已饱和且预测正确的分支更新；模型与 RTL 同步 |
| `front_stall` 接回 & LLC 旁路写/部分行写 miss | `core_top` `front_stall` 写死 0；LLC 旁路写/部分行写仅留断言 | 接回并补定向/随机流量测试 |
| PMU 软件可见性（CSR 接入）与过期测试修复 | RTL PMU 计数器块尚未实例化接 CSR；`tests/pmu/pmu_tb.cpp`（`NUM_EV=52`）与 `core_tb.cpp`（`kPmuEv=51`）落后于当前 66 事件 | 决定是否开放 CSR；更新 PMU 测试；补齐二级 TMA 事件 |
| **SoC v2：SD 卡存储控制器（`soc_ocsdc`）+ `Zicbom` Cache 一致性 + JTAG Debug** | SoC v1 已打通真实双层 Full-AXI4、BootROM、SRAM、CLINT、PLIC、UART、SysCtrl；从外部非易失介质（SD 卡）经 DMA 搬运 OpenSBI/Linux 到 DDR 需要 SD/DMA 控制器以及软件可控 Cache 刷洗/失效（`cbo.clean`/`cbo.inval`） | 接入 SD/DMA 主口至 Tier-1 System Xbar，补齐 `Zicbom` 指令或在无硬件一致性下完成软件维护，`soc_gate.sh` 补 SD 卡启动回归 |
| 仿真速度双版本评估（`` `ifdef SYNTHESIS ``） | 已有 `mul_core`、公共原语、FPU 走双版本；`bpu_ub_track_ser`（`rem_of` 建表）等低深度模块尚未 profile | `--prof-cfuncs` 定位最慢模块，只对热点补快速仿真路径与等价测试 |

## 已知 trace-model vs RTL 细微差异（备忘，待按需收敛）

- **全量 386 点 SPEC06 INT（10M warmup + 10M ROI）RTL vs `trace-model` 对齐实测（2026-11-26，`exp/verify-spec386`）**：
  - 386/386 架构正确性 **0 fail / 0 FM diff**（累计 ~77.2 亿条指令逐条比对），12 项基准 geomean **`+0.00%`**，**266/386（68.9%）实现 2000 万指令后 0-cycle 完全一致**。
  - 分基准精确 0-cycle 统计：`456.hmmer` **23/23 (100%)**、`462.libquantum` **36/36 (100%)**、`464.h264ref` **35/35 (100%)**、`473.astar` **26/26 (100%)**、`429.mcf` 37/45（`−0.04%`，最大单点 `0.41%`）、`400.perlbench` 20/24（`−0.00%`，`0.26%`）、`445.gobmk` 23/29（`−0.03%`，`0.19%`）、`401.bzip2` 26/48（`−0.05%`，`0.71%`）、`403.gcc` 14/34（`+0.00%`，`0.34%`）、`483.xalancbmk` 25/34（`+0.36%`，`1.89%`）、`471.omnetpp` 1/25（`−0.14%`，`2.65%`）、`458.sjeng` 0/27（`−0.05%`，`1.09%`）。
  - 访存/计算密集基准均 100% 0-cycle 对齐；剩余 120 点集中于高分支误预测/间接跳转负载（`sjeng`/`omnetpp`/`xalancbmk`），呈对称 `±` 波动（geomean 抵消为 `+0.00%`）。
  - 同期修复 `trace-model` `PerfCount::perf_reset()` 漏清 `cycle_base`（`--restore-stub` 重复扣减 ~25k 周期），修复后 12 项基准真实 2 GHz 分数回调 `−0.78%`，消除原先 RTL 相对 TM 稳定偏慢 ~1%~2% 的假象。
- **变延迟 Early-out DIV 错路操作数差 & Linux `s19` 既有微差（2026-11-23 EXP-061）**：① wrong-path 上 `trace-model` 无操作数事实（固定 2 拍），RTL 用寄存器堆脏值算 `clz`（2..17 拍），极少数误预测解析前完成的错路 DIV 可能在 Port 1 `wb_next` 阻塞差 1 拍；② 26 窗 Linux 检查点 26/26 0 FM 不一致、25/26 PT/UP 全等，仅 `s19` 在 `cyc=2372697`（距最近 DIV 17,548 拍）存在 1 处与 EXP-052 `s17` / EXP-056 `s02` 同类的既有错路陷入边界微差。
- **其余静态小差异（EXP-044 盘点）**：
  - `prf_awake` 在写回级唤醒所有 load；模型跳过 `early_woken`。
  - CSR 异常优先级：RTL 非法指令先于断点，模型相反；`mstatus` 输出无 SD 位（19 vs 22 个 CSR）。
  - `peripheral_axi_fmt` 对 lb/lh/lw 做 64 位符号扩展，模型 `extract_read_data` 对高 32 位零扩展。
  - `ptw_walk` 静默截断 >32 位 PPN，模型 `exit(2)`；路由号 RTL 4 位、模型 32 位。
  - `ldq_alloc_valid` 在 `dispatch_lsu_alloc` 未使用；ROB 独立算 F/D `fs_*`/`fflags`（模型从 bridge 取）。

## 待做：代码卫生、生成器与文档债

- **生成器同步**：`tools/gen_backtop.py`、`gen_soc_top.py`、`gen_cfg_pkg.py` 与手改的 `back_top.sv`/`exu.sv`/`soc_top.sv`/`ttg_cfg_pkg.sv` 补齐同步（让 `make cfg` 与提交包逐字节一致，不再输出已删常量）。
- **`axi_subsys` UNOPTFLAT**：确认 `axi_llc.in_w` 组合环是否为误报，消除后纳入 `-Wall`。
- **死代码与过期注释清理**：`rob.sv` `pf_inst` 恒 0；`lsu_pipe.sv` 孤立 `lint_on`；`tests/tlb_par` 过期接口；`exu_fu` 单周期单元无用端口；LLC `hz_wctx`/`hz_wresp`；`mem_axi` 桩口 2；`tlb_mmu_pkg`/`fp_pkg` rv32 残留；`ptw_walk` L1/L2 误导命名；各模块旧注释（`27 FUs`、`14 wake channels`、`16 tick`、`8->16 lane` 等）。
- **可选架构清理**：是否删除默认关闭且不再使用的 `bpu_ub_track.sv`（`RVC=0`）和 `FE_BFAST` 分支；`RealLsu` 3 个 SSA 展开文件手写化；`spec/*.io` 明确退役或更新。
- **RTL 文档补全**：全模块压到 ≤100 层后补齐 `rtl/docs/DEPTH_OPT.md`，清理各 `rtl/docs/modules/*.md` 末尾的“未核对”项，核对 `pmu`/`common` 的 `area` 字段。
- **未决定是否合入的历史探索**：`BPO_LOOP=1` 循环预测器（EXP-025）、`exp/sdip`（EXP-026），如需重启须在当前 15.33 分/GHz `main` 上重测。
- **合入流程自动化**：把 `scripts/linux_check.sh` 正式写进 `WORKFLOW.md` 检查清单。
