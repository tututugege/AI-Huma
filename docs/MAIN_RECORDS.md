# AI-Huma 合入 main 记录

每次合入 `main` 追加一行，最新的在最上面。规则见 [WORKFLOW.md](WORKFLOW.md) 第 5.2 节。

- 性能数字来自 trace-model，负载固定：dhrystone（64 次，`rtl/programs/big/dhrystone.bin`）、coremark（2 次迭代，`rtl/programs/big/coremark.bin`）、memory-stress-small（`trace-model/build/tests/memory-stress-small`）。
- 变化百分比相对上一行；正数表示周期变多（变慢）。
- 综合还没做时写"未做"和原因，不留空。

## 记录

| 日期 | 版本（总仓库 / function-model / trace-model / rtl） | 正确性 | dhrystone 周期 (IPC) | coremark 周期 (IPC) | memory-stress-small 周期 (IPC) | RTL 周期 | 综合（工具 / 频率 / 面积 / WNS） | 说明 |
|---|---|---|---|---|---|---|---|---|
| 2026-11-08 | 本行所在提交 / `7b8ee1b` / `1d08b15` / `cc90cc2` | trace-model gate 63/63（预取开、关）；旧设计开关串 63/63 与 `legacy_lsu_baseline*.csv` 逐个相同；`LSU_PIPE_NOWD=1` gate 63/63；小 LLC 5/5；RTL 逐条对比 67/67（预取开、关），周期与 trace-model（NOWD=1 表）0 处不同；`lint.sh`/`lint_chip.sh` 0 警告；`ttg_cfg_pkg.sv` 与模型配置逐字节相同；RTL、模型 Linux 均到 `rv32 login:`，RTL 逐条对比 0 不一致 | 123,684 | 295,351 | 331,311 | 见 ref_cycles | 未测 | |
| 2026-11-07 | 本行所在提交 / `7b8ee1b` / `a7960e4` / `5829f07` | trace-model gate 63/63（PMU 关、`PMU=1` 各一遍，都与基线逐个相同）；RTL 逐条对比 67/67，预取开、关（`PF_EN=0`）周期都与参考逐个相等（0 个不同），0 个函数模型不一致；`lint.sh`、`lint_chip.sh` 0 警告；Linux 13 段（s01–s13 接力，每段 1600 万周期，s01–s04 本机、s05–s13 服务器 4 线程）逐条对比 13/13 通过、0 不一致；PMU 的 RTL 与 trace-model 在 dhrystone、coremark 上 18 个 tier-1 事件总数逐个相等；`tests/pmu/run.sh` 30 万拍随机 0 不一致 | 161,183 (1.811)，0% | 251,535 (2.140)，0% | 334,635 (3.232)，0% | 与 trace-model 相同（67 个程序逐个相等，预取开、关都是） | yosys 通用门面积代理（相对数字，无工艺库、无时序，`SYNTH_LIGHT=1 SYNTH_MEM=1`）：`dispatch` 86,637 → 86,637（不变）；新增 `pmu_ev_core` 518 个单元；`pmu` 计数器块（8 个 HPM）约 10.2k 单元，计数器存储按 `$mem` 未计触发器（估计约 750 个触发器），**计数器块没有接到任何东西，综合器会把它整个删掉**；工艺库、WNS：**未做** | PMU（EXP-013）：trace-model `PMU=1`（默认关）51 个事件、TMA 一二级、逐 PC 堵塞画像、相位；RTL 事件总线 tier 1（18 个事件含 TMA 一级）+ 计数器块（未接 CSR，软件不可见）；周期不变 |
| 2026-11-07 | 本行所在提交 / `7b8ee1b` / `b301161` / `9279125` | trace-model gate 63/63（基线更新，预取开；`PF_ENABLE=0` 对 main 基线 62/62 相同，另加 pf-stress）；RTL 逐条对比 67/67，预取开、关两种配置周期都与 trace-model 逐个相等（0 个不同），0 个函数模型不一致；`lint.sh`、`lint_chip.sh` 0 警告；Linux 分 13 段（检查点 s01–s13 接力，每段 1600 万周期，每段检查 630 万到 2400 万条指令，不是一次连续运行、微架构每段冷启动，周期不比较）在**合并后的树**（预取开 + move elimination，rtl `9279125`）上逐条对比，13/13 通过、0 不一致；SPEC full 580/580 点（fast warmup），无 difftest 不一致 | 161,183 (1.811)，−0.52% | 251,535 (2.140)，−0.34% | 334,635 (3.232)，−3.65% | 与 trace-model 相同（67 个程序逐个相等） | yosys 通用门面积代理（相对数字，无工艺库、无时序；合并后的树，2026-11-07 重测，`SYNTH_LIGHT=1`）：新增 `dcache_pf` 4,172 个单元、422 个触发器；`dcache_mshr`（`SYNTH_LIGHT=1 SYNTH_MEM=1`）main 96,296 → 96,931 个单元（+635，+0.7%）、触发器 748 → 764；L1D 阵列新增 pf 位 256×4 = 1,024 个触发器（未重测）；净增触发器约 1,460；工艺库、约束频率、WNS：**未做** | L1D 数据预取器 h1（EXP-009）：单条全局步长表项、度 8、距离 2、页内、LLC-only next-line 引擎、无 PC、无限流；默认开（`PF_ENABLE` / RTL `PF_EN`）。SPEC full 12 个程序几何平均 +8.3%，估算分数 8.12 → 约 8.80 分/GHz（SimPoint 权重，对精确 PF 关基线，分数 = 旧分数 × 加速比，参考时间未核对官方表；libquantum +96.3%、mcf +10.8%、gcc +9.0%、bzip2 +6.2%，gobmk/hmmer/sjeng −0.8%/−1.6%/−3.0%）；低于 −10% 的 5 个点（omnetpp sp22 −40.7%、sp7 −22.8%，gcc sp38 −29.9%，xalancbmk sp34 −22.2%、sp15 −11.8%）是已知回退，原因是 LLC-only 引擎；节流、MSHR 预留、时间片对抗三个修复中，节流（几何平均 +7.2%）和时间片对抗（+7.7%）在全量上都不如 h1（+8.2%，三方案都有结果的 579 个点同口径），MSHR 预留只在抽样点上测过、也没有同时保住 mcf，按负责人决定保持 h1 合入 |
| 2026-11-06 | 本行所在提交 / `d40c588` / `767c25f` / `1e5d656` | trace-model gate 62/62（基线更新，7 个程序周期变化，全部 difftest Success、`ME_CHECK=1` 0 次断言）；RTL 66 个程序逐条对比 66/66，周期与 trace-model 逐个相等（开、关 `MOVE_ELIM` 两种配置都跑了：关闭时与原 `ref_cycles.txt` 逐个相等）；Linux 从复位启动到 `rv32 login:`：trace-model 与 RTL（`SOC_TB_FM=1`，每条提交逐条对比，0 不一致、无断言；登录后手动结束，没有总周期数和"N 条已检查"汇总）都通过；quick SPEC 129 个点无 difftest 不一致 | 162,033 (1.802)，0 | 252,400 (2.133)，−1.15% | 347,305 (3.114)，0 | 与 trace-model 相同 | yosys 通用门面积代理（相对数字，无工艺库、无时序）：`ren` 206,228 → 227,720 个单元（+21.5k，+10.4%；`arch_cnt` 映射成触发器后 → 231,029，+24.8k，+12.0%，触发器 +384），`dispatch` 86,637、`rob` 201,672 不变；`ren` 最长组合路径 63 → 130 级（通用门级数，不是时序）；工艺库、约束频率、WNS：**未做** | mov 消除（EXP-012），默认开启。quick SPEC 6 个程序几何平均 IPC 1.550 → 1.551（+0.06%）：收益在噪声量级，按负责人决定合入 |
| 2026-11-06 | 本行所在提交 / `d40c588` / `88e5254` / `b19a181` | trace-model gate 62/62（基线更新，63 个程序周期全部变化）；RTL 66 个程序逐条对比 66/66，周期与 trace-model 逐个相等；Linux 从复位启动到 `rv32 login:`：trace-model 与 RTL（每条提交逐条对比，无断言、0 不一致；登录后手动结束，没有总周期数和"N 条已检查"汇总）；SPEC full 580 点无失败、无 difftest 不一致 | 162,033 (1.802)，+7.7% | 255,335 (2.108)，+9.4% | 347,305 (3.114)，+83.6% | 与 trace-model 相同 | yosys 通用门面积代理（相对数字，无工艺库、无时序）：`axi_llc` 489,436 → 522,758 个单元（+33.3k）、触发器 22,324 → 30,584；`lsu_dc_req_st` 86,150 → 62,755（−23.4k）；净约 +9.9k 单元（不到整机的 0.2%）、触发器 +8.3k（约 +4.6%）；`mem_top` 太大综合超时，`TICKS=1` 常量化的效果未测到；工艺库、约束频率、WNS：**未做** | DRAMsim3 DDR（EXP-006）：去掉 16 倍 AXI 子系统分频、核心 1 GHz、DDR4-3200 加 60 ns 非核心延迟，见下文“变化”。SPEC full 几何平均 IPC 1.396、估算 8.12 分/GHz；quick 6 个程序 IPC 2.204 → 1.550（−29.7%）。周期变多是因为旧基线靠分频把 DRAM 做快了约 13 倍 |
| 2026-11-05 | 本行所在提交 / `d40c588` / `08e9cfe` / `52d2b84` | trace-model gate 62/62（基线更新，25 个程序周期变化）；RTL 66 个程序逐条对比 66/66，周期与 trace-model 逐个相等；Linux 从复位启动到 `rv32 login:`：trace-model（约 7–8 千万周期）与 RTL（全程逐条对比，0 不一致，约 3.6 小时）| 150,427 (1.941)，−0.27% | 233,515 (2.305)，+2.87% | 189,128 (5.718)，0 | 与 trace-model 相同 | yosys 通用门面积代理（`rtl/docs/09-synthesis-report.md` 第 9 节）：受影响的 14 个模块 3,723,024 → 2,117,024 个单元（约 −161 万，整机约 17%），触发器 123,595 → 73,873；整机推算未按新配置重做；工艺库、约束频率、WNS：**未做**（没有工艺库和时序流程，见 TODO） | 第 3 批面积配置（EXP-005），见下文“变化”。quick SPEC（6 个程序）IPC 2.216 → 2.204（−0.5%）；coremark 变慢来自在飞分支 32 |
| 2026-11-04 | `6210e46` / `4f99467` / `41a5cdd` / `dc46f6d`（rtl 工作区有未提交修改） | gate 62/62；RTL gate+vm 64 个程序逐条对比一致 | 150,838 (1.935) | 226,991 (2.371) | 189,128 (5.718) | 待补 | **未做**：还没有综合流程（见 README"下一步"第 2 条） | 起始记录（本表从这里开始） |

## 变化

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
