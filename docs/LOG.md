# AI-Huma 提交日志（LOG）

记录三个仓库里**每一次 commit 做了什么**。规则见 [WORKFLOW.md](WORKFLOW.md)：

- 每次 commit 之后，在本文件最上面的"新记录"一节追加一行：日期、仓库、分支、commit、做了什么、怎么验证的、结论。
- 探索实验的 commit 也要记，分支名要写清楚，没合入 `main` 的标明"未合入"。
- 一个月或一个阶段结束后，把"新记录"整理进下面的历史表里。

## 新记录（从这里往下追加，最新的在最上面）

| 日期 | 仓库 / 分支 | commit | 做了什么 | 验证 | 结论 |
|---|---|---|---|---|---|
| 2026-11-12 | 总仓库 `main` | 本行所在提交 | 文档审查（总仓库 `README.md`、`docs/*.md`）：README 当前状态改成概况 + 指向 MAIN_RECORDS，补 rv64 / ENV_VARS / 仓库结构 / 子模块真实 URL / rv64 构建命令；WORKFLOW 修正 trace-model 正确性标准（不再是“与原模型周期一致”）、gate / `fm_gate` 个数（64 / 69）、已不存在的 diff 脚本，加 XLEN 与 `LSU_PIPE_NOWD=1` 说明和 6.1“文档整理”；GUIDE 补 ENV_VARS / SERVER；PMU 事件数 52 → 66（RTL）/ 85（模型）；SERVER 去掉不存在的 `validate/dhrystone.bin`、标过时的现成结果表；TODO 删已完成项、补“未合入的实验”和推送；EXPLORATION 索引状态更正、补 EXP-006/010/016 行；LOG 把误追加在文件末尾的 47 行挪回“新记录”表并改正 rv64 分支行的“未合入” | 所有相对链接可打开；命令、脚本、路径逐项对过 main 上的文件 | 未核实：`scripts/gate_all.sh` 是否还能跑（已记入 TODO）；服务器上 `/root/...` 的现成结果；子仓库文档由其他审查负责 |
| 2026-11-12 | trace-model `main` | 见总仓库提交 | `docs/ENV_VARS.md` 补全：模型读取的 99 个环境变量 + 4 个影子测试变量，按运行控制 / PMU / 对拍调试 / 前端与 BPU / 访存 / DDR 与 AXI / 影子测试分组，写默认值、作用和位置；改正 `config.h` 里 `ROB_COMPACT` 环境变量的过时注释（源码并不读它） | 重新编译，dhrystone 116,774、coremark 284,902 不变；文档里的变量名与源码扫描结果逐个对上 | 已推送 |
| 2026-11-12 | trace-model `main` | 见总仓库提交 | 14 个无文档的环境变量：8 个补进新文档 `docs/ENV_VARS.md`（`FAST_WARMUP`、`FE_COMMIT_TRACE`、`LSU_PIPE_WBTRACE`、`TB_NO_INJECT`、`TB_PERTURB_BR`、`TB_SAMPLE_PC`、`TB_TRACE_COMMIT`、`TB_TRACE_TRAP`），6 个删除（`CKPT_TRACE_PC`、`TB_DEBUG_DDR` / `FLUSH` / `PATCH`、`LSU_PIPE_RPREG`、`FE_IPF_MAX` 改为常量 4） | 重新编译，dhrystone 116,774、coremark 284,902 不变，TB_CHECK 0 不一致 | 已推送 |
| 2026-11-12 | trace-model `main` | 见总仓库提交 | 删 `config.h` 里没人用的 DDR 延迟推算链：`CONFIG_DDR_CORE_FREQ_MHZ` / `CL` / `TRCD` / `TRP` / `BURST_TRANSFER_BEATS` / `PAGE_*_RATE_PCT`、各 `*_FS` 常量、`CONFIG_SIM_DDR_LATENCY_CALC`、`div_round_u64`（`CONFIG_SIM_DDR_LATENCY` 本来就固定为 60，推算行早已注释掉）；`SOC/CDC/CTL/PHY_LATENCY_NS` 和 `CPU_FREQ_MHZ` 被 SimDDR 引用，保留 | 重新编译，dhrystone 116,774、coremark 284,902 不变 | 已推送 |
| 2026-11-12 | trace-model `main` / rtl `main` | 见总仓库提交 | 删 5 个无引用的模型宏（`CONFIG_DIFFTEST` / `PERF_COUNTER` / `BPU` / `TLB_MMU` / `ORACLE_STEADY_FETCH_WIDTH`）；RTL `rob_pkg` 的 `XLEN` 改名 `ROB_XLEN`（与 `-DXLEN` 重名，`DEBUG=1` 的 rv64 测试平台因此编不过） | 模型 dhrystone 116,774、coremark 284,902 不变；RTL lint XLEN=32 / 64 与整芯片 0 警告；`DEBUG=1` rv64 测试平台直接编过，`crc32` 2306 不变 | 已推送 |
| 2026-11-12 | 总仓库 `main` | 本行所在提交 | EXP-029 合入后查 rv64 `crc32` / `memory-stress` 周期差：逐提交周期 + `LSU_PIPE_EVT` 对比，首个分歧是 store 在 63 周期后被模型看门狗重发（`RealLsuPipe.cpp` `wd == 63`，`LSU_PIPE_NOWD` 未设）；MAIN_RECORDS、TODO 更正 | 模型加 `LSU_PIPE_NOWD=1` 后 `crc32` 2306、`memory-stress` 2,260,146，与 RTL 完全相同，rv64 53/53 周期一致 | 已推送 |
| 2026-11-12 | 总仓库 `main` | 本行所在提交 | **合入 main**：function-model `b388f39`、trace-model `ccc2d0c`、rtl `8dbb7cd`（EXP-029 rv64imab）；MAIN_RECORDS、EXPLORATION、LOG、README、TODO | 见 MAIN_RECORDS 2026-11-12 行：XLEN=32 fm_gate 69/69 周期不变；rv64 53 程序 + Linux login、rv32 Linux login 均 0 不一致 | 已推送 |
| 2026-11-12 | rtl `exp/rv64` | `9071b89` `fb05807` `72f2cd9` `f21cebf` | EXP-029：XLEN_BITS 进配置包、后端 XLEN 数据通路 + `is_word`；LSU / dcache 8 字节数据；Sv39 TLB 和页表遍历；前端 / BPU PC 加宽 | 每一步：整颗芯片 lint（XLEN=32、64）0 警告，XLEN=32 fm_gate 64 / 64、周期与参考表相同 | 已合入本地 main（2026-11-12） |
| 2026-11-12 | rtl `exp/rv64` | `cff4afe` `f0bd79d` `9807660` | EXP-029：测试平台 XLEN 化（rv64 启动桩、64 位逐条对比、`SOC_XLEN` / `FMLIB`、`SOC_TB_LOG`）；跑 rv64 程序发现并修的 4 个 RTL bug（dcache 填充转发 / 写回缓冲 4 字节写死、DIV 唤醒倒计时、`lp_ovl` 宽度）；8 字节 MMIO | rv64 53 个 cpu-tests 逐条对比通过，周期与模型 52 / 53 相同；`rv64-sv39`、`mmio64` 通过；XLEN=32 64 / 64、rv32 `memory-stress` 0 不一致；**Linux 从复位到 `rv64 login:`，约 1.05 亿周期，0 不一致** | 已合入本地 main（2026-11-12） |
| 2026-11-12 | trace-model `exp/rv64-on-main` | `0764457` … `4b07931`（11 个） | EXP-029：rv64 的 trace-model（接口层、译码、Sv39 MMU、64 位 CSR、PC 加宽、外设 8 字节、乘除延迟、`addiw` 不当 move）；基于 `07d567c`；最后一个提交修 `sstatus` 视图丢 UXL | rv64 53 个程序周期与 RTL 52 / 53 相同；rv32 `add` 1276（与参考表相同） | 已合入本地 main（2026-11-12）（旧 `exp/rv64` 作废） |
| 2026-11-12 | function-model `exp/rv64` | `7157dc7` … `b388f39`（7 个） | EXP-029：RV64IMAB（`-DXLEN=64`）、Sv39、Spike 对拍、rv64 Linux 镜像、通用快速通路、检查点 v4 / BBV | Spike 52 / 54（2 个已知平台差异）；Sv39 变异 9 / 9；rv64 Linux 在函数模型上启动到登录 | 已合入本地 main（2026-11-12） |
| 2026-11-11 | 总仓库 `main` | 本行所在提交 | **合入 main**：trace-model `a11b1ca`、rtl `a905acd`（EXP-028）；MAIN_RECORDS、EXPLORATION、LOG、README、TODO | 见 MAIN_RECORDS 2026-11-11 第一行 | 未推送 |
| 2026-11-11 | rtl `exp/rob-compact` | `4e954d7`、`a905acd` | EXP-028 RTL：`rob_core_cpt.sv`、分发编号、BPU 占用连线；删非缓存窗口通路、`altpcpn`；`ttg_cfg_pkg.sv` `ROB_COMPACT=1`、`ref_cycles.txt` 37 个程序 | lint 0 警告；`fm_gate` 69/69、周期 0 处不同；Linux 从复位连续到 login，0 不一致 | 已合入 main |
| 2026-11-11 | trace-model `merge/rob-compact` | `35b3af4`、`a11b1ca` | EXP-028：紧凑 ROB（`CFG_ROB_COMPACT`，先默认关再默认开）+ 寄存器 BPU 额度；删剩余非缓存窗口与通路、前端 PMU `FEO_*`、删 `altpcpn`/`sc_used`、删 A 组开关；`baseline.csv` 32 个程序、`PROJECT.md` 大程序 | 默认关 gate 64/64 与旧基线相同、大程序不变；默认开 gate 64/64 全部 Success；Linux 到 login；SPEC 全量 +2.74% | 已合入 main |
| 2026-11-11 | 总仓库 `main` | 本行所在提交 | EXP-027 合入后补跑：RTL Linux 13 段（s01–s13，本机 13 个并行，每段 1600 万周期，逐提交与函数模型对比）13/13 通过，每段检查 692 万到 2424 万条指令，0 不一致；MAIN_RECORDS、EXPLORATION 更新，TODO 删除该项 | 13/13 | 未推送 |
| 2026-11-11 | 总仓库 `main` | 本行所在提交 | **合入 main**：trace-model `07d567c`、rtl `de8d0aa`（EXP-027）；MAIN_RECORDS、EXPLORATION、LOG、README、TODO | 见 MAIN_RECORDS 2026-11-11 行 | 未推送 |
| 2026-11-11 | rtl `exp/no-uncwin` | `1205bff`、`de8d0aa` | EXP-027 RTL：`lsu_pkg::is_mmio_addr` 两段、`ttg_cfg_pkg.sv` 重生成、tb 地址表、`ref_cycles.txt` 3 个程序；`tm_cycles.sh` 导出 `ROOT` | lint 0 警告；`fm_gate` 69/69、周期与模型 0 处不同 | 已合入 main |
| 2026-11-11 | trace-model `exp/no-uncwin` | `62e4a8b`、`07d567c` | EXP-027：删除 0x87f00000 非缓存窗口（`config.h`、`mmio_address_map.h`、`baseline.csv` 3 个程序）；PMU TMA 缺失标记改为 `bitset<ROB_NUM>` | gate 64/64、大程序不变、Linux 到 login；SPEC 全量 +10.75% | 已合入 main |
| 2026-11-10 | 总仓库 `main` | 本行所在提交 | **合入 main**：trace-model `e84e53a`、rtl `1c0d110`（EXP-025 多表 ITT）；MAIN_RECORDS、EXPLORATION（EXP-025）、LOG、README、TODO、SERVER、WORKFLOW | 见 MAIN_RECORDS 2026-11-10 行 | 推送见下 |
| 2026-11-10 | rtl `exp/itt-multi` | `6bc0508`、`efaa350`、`1c0d110` | EXP-025 RTL：`NITT=3`、`ITT_TBL`、`bpu_btb_bank/upd/sel`、`bpu_main_lane/sel`、`bpu_banks`、`bpu`；`itt-dispatch` 定向程序；`ref_cycles.txt` 重生成；文档程序数 69 | `fm_gate` 69/69、周期与模型相等；Linux 13/13；综合深度在 5% 内 | 已合入 main |
| 2026-11-10 | trace-model `exp/itt-multi` | `5d8cf66`、`e84e53a` | EXP-025：ITT 默认 3 张 × 64 项（`CFG_ITT_H`、`CFG_ITT_SIZE`），`itt-dispatch` 测试进 gate，`PROJECT.md` 大程序标准周期更新 | gate 64/64；SPEC 全量 580 点 +0.67% | 已合入 main |
| 2026-11-09 | rtl `exp/store-wb` | `b1e0335`、`b44ab4c`（in-drain 配对，已被替换）；`80ac631`、`ef6da65`（write buffer） | EXP-024 RTL：`lp_wbuf`、`lp_wbstep`、`lp_stq` 的"已处理"标记、`lp_drain` 只留 MMIO 路径；DCache 每个 store 口的第二字通路（`st2_t`）和并行合并 `line_merge_n`；`scripts/ref_cycles.txt` 重生成（`LSU_PIPE_NOWD=1`，缓冲区默认） | `lint.sh`/`lint_chip.sh` 0 警告；`fm_gate.sh` 68/68，周期与 trace-model 逐个相等；Linux 13/13；综合：`lsu` 深度 125（main 130）、`lp_drain` 模块级 +17% | 已合入本地 main，未推送；第一版配对 RTL 的 Linux `s04` SC 不一致原因未定位（TODO） |
| 2026-11-09 | trace-model `exp/store-wb` | `46d2d76`、`5fab5be`、`281076b`、`8dd18fd`（探索）；`9c2fff6`、`7fa8eaf`、`a29fda6`、`55c9f64`（write buffer） | EXP-024：容量上限实验（`CFG_STQ_UNC`，已删）、同 line 合并上限（`LSU_PIPE_MERGE`/`MGRAN`/`MADJ`/`MSPEC`，默认关）、write buffer（`CFG_LSU_PIPE_WBUF=4` 默认开，`WBMAX=2`、`WBINS=4`、`WBSCAN=4`、`DRAIN=2`）；STQ 事件掩码 128 位；`baseline.csv`/`baseline_nopf.csv` 重生成 | gate 63/63（17 个程序周期小幅变化）；12 个程序最高权重点几何平均 IPC +2.85%（gcc sp42 +29.6%）；5 点参数扫描 4 项/2 条目/2 口 +6.95% | 已合入本地 main，未推送 |
| 2026-11-09 | 总仓库 `main` | 本行所在提交 | **合入 main**：trace-model `31bfb03`、rtl `29e535b`（EXP-019 / EXP-020 / EXP-023）；文档 MAIN_RECORDS、EXPLORATION、LOG、README、TODO | 见 MAIN_RECORDS 2026-11-09 行 | 已合入本地 main，**未推送** |
| 2026-11-09 | rtl `exp/integ` | `1b6db9a`（合并）、`66aed1a`、`1cfbae4`、`bd6ba1d`；main 上再加 `RTL_FE_NOTES.md` 提交 `71468eb` 的 cherry-pick | 合并两条 RTL 分支；`LSU_MDP_BITS`/`LSU_MDP_CLR`/`FE_RFAST` 改为 `gen_cfg_pkg.py` 的写死常量，只导出 `LSU_MEMSPEC`、`FE_BFAST`；`ref_cycles.txt`（默认）与 `ref_cycles_nomemspec.txt`；`RTL_INTEG_NOTES.md` | lint/lint_chip 0；fm_gate 68/68，`LSU_MEMSPEC=0` 68/68，周期与模型相等；Linux 13 段 13/13、0 不一致；综合表见 MAIN_RECORDS | **已合入 main（快进 + 1 个 cherry-pick，`29e535b`）** |
| 2026-11-09 | rtl `exp/memspec-rtl`、`exp/fe-rtl` | `f6daf0a`..`598f4f9`（访存推测）、`6251c84`..`dbc1fa7`（前端）；`71468eb` 只改 `RTL_FE_NOTES.md` | EXP-019：LSU 访存推测的 RTL（`lp_ent_ms`、`lp_ms`、`lp_mdp`、ROB `defer/flush_pipe`、`lp_ovl`）；EXP-023：`FE_RFAST`/`FE_BFAST` 的 RTL（`bpu`、`front_fifo`、`icache_kill`、`pre_idu_ibuf`） | 各自 lint 0；fm_gate 68/68（推测）、67/67（前端），周期与模型相等；Linux 13 段 13/13 | 已合入 main（随 `exp/integ`） |
| 2026-11-09 | trace-model `exp/integ` | `8ee4c9e`、`207957a`（合并）、`8d647a8`（基线）、`451c9dc`、`31bfb03` | 合并 main `7f8456e` + `exp/memspec-refs` + `exp/fe-refs`；默认 `LSU_MEMSPEC=1`、`LSU_MS_DATA=1`、`FE_RFAST=15`、`FE_BFAST=0`；`baseline.csv` 重生成；`INTEG_NOTES.md`、`scripts/integ/spec_cmp.py` | gate 64/64 difftest Success，旧配置（`LSU_MEMSPEC=0 FE_RFAST=0`）对 main 基线 63/63 相同；Linux 到 `rv32 login:`；SPEC 全量 580/580，几何平均 +11.02%（估算 9.42 → 约 10.46 分/GHz，参考时间未核对） | **已合入 main（快进，`31bfb03`）** |
| 2026-11-09 | trace-model `exp/fe-refs` | `b02eaf6`（`exp/frontend` `c8b92cf`→`exp/combo` `2e1a27c`） | EXP-023：`FE_RFAST`/`FE_BFAST`/`FE_PAIR`/`FE_IPF` 与诊断（`FE_DIAG`、`FE_TRACE`、`FE_FUSE_DIAG`）；`CFG_FE_RFAST/BFAST` 编译期默认；`FE_PAIR` 的 512 位历史环 | 开关关时 gate 63/63；`RFAST=15 BFAST=3` 63 个程序 difftest Success；25 点 `RFAST=15` +2.61% | 已合入 main（随 `exp/integ`，只有 RFAST=15 默认开） |
| 2026-11-09 | trace-model `exp/memspec-refs` | `b8b6069`..`ef02c4c`（含 `exp/mem-spec` 的 4 个提交，提交说明里写 EXP-018/019/020） | EXP-019/020：访存推测 `LSU_MEMSPEC`（等待表、SPD 延迟写回、违例重做与冲刷）、`LSU_MS_DATA` 值路径、`LSU_MDP_HW=2`、`CFG_LSU_MDP_BITS=6`、`LSU_MS_SLOTS`、违例代价统计；`L_RPW` 违例检查修复 | 开关关时周期不变；开：68 个程序模型 = RTL（dhrystone 115,896、vm_pagefault_test 19,271）；30 点精确预热 +5.35% | 已合入 main（随 `exp/integ`） |
| 2026-11-08 | rtl `exp/iq-enq` | `66f7096`、`121324c` | EXP-017（已合入 main）：isu 按 IQ 入队宽度实例化通道；cfg、PMU 包、`ref_cycles.txt` 同步 | lint 0；fm_gate 67/67 周期与模型相等；Linux 逐条对比到 `rv32 login:`，不一致 0；`isu` 综合单元 1,039,339 → 843,910（−18.8%） |
| 2026-11-08 | trace-model `exp/iq-enq` | `5851e1d`、`9da2f6e`、`e0d7375`、`cefaee4` | EXP-017（已合入 main）：每个 IQ 的入队宽度开关，默认 7/6/4/4/5；PMU 分 IQ 的没空位/宽度停顿和占用；基线重生成 | gate 63/63；全量 580 点 IPC −0.05% |
| 2026-11-08 | rtl `lsu-bpu` | `cc90cc2`（`5829f07..`，16 个提交） | EXP-015：RTL 实现分级 LSU 与流水化 BPU；`ref_cycles*.txt` 用 `LSU_PIPE_NOWD=1` 生成；isu/dispatch 的死取消逻辑改 generate | fm_gate 67/67 周期与模型相等；lint 0；Linux 到登录 |
| 2026-11-08 | rtl `exp/backend-dse` | `edf9d3b` | EXP-016（已合入 main）：`gen_pmu_pkg.py` 跳过标 `// model-only` 的事件（要求在表尾）；生成的 PMU 包不变（66 个事件） | 包与 `ttg_cfg_pkg.sv` 与 main 逐字节相同；中间版本（68 个事件）lint 0 警告、fm_gate 67/67 周期 0 处不同 |
| 2026-11-08 | trace-model `exp/backend-dse` | `1e43fdf`、`7f8456e`（已合入 main，含 main 的合并提交） | EXP-016：后端资源 DSE（PRF/ROB/LDQ/STQ/在飞分支/IQ/MSHR，46 个配置，SPEC 点 + PMU）；新增 `CFG_LDQ_SIZE`、trace-model 专用 PMU 事件 `SLOT_FE_OTHER_NOPREG/NOBRTAG`、`scripts/dse/` | 默认周期不变：gate 63/63、7 个大程序与 main 相同、quick SPEC 178 点逐点周期相同、Linux 到登录；结论见 EXPLORATION.md EXP-016 |
| 2026-11-08 | trace-model `lsu-bpu` | `1d08b15`（`a7960e4..`，13 个提交） | EXP-015：分级 LSU（含 IPC 修复：DRAIN=3、DCAND=4、RP=4、CUT=127、L2=115）+ 流水化 S+R BPU，`baseline*.csv`、`legacy_lsu_baseline*.csv`、`PROJECT.md` 更新 | gate 63/63；旧开关串 63/63 与 legacy 基线相同 |
| 2026-11-07 | 总仓库 `main` | 本行所在提交 | **合入 main**：trace-model `ee988d0`、`a7960e4`，rtl `b5a299a`、`5829f07`（EXP-013 PMU）；文档 PMU.md、EXPLORATION、MAIN_RECORDS、GUIDE、TODO | 见 MAIN_RECORDS 2026-11-07 PMU 行 | 已合入 |
| 2026-11-07 | rtl `exp/pmu` | `5829f07` | EXP-013：`pmu_ev_core` 事件总线 tier 1（提交流、重定向、TMA 一级槽事件），dispatch `slot_valid`、back_top 导出，`gen_backtop.py` 重新对齐，测试平台累加 + `pmu_parity.sh` | fm_gate 67/67（预取开、关），lint 0，Linux 13 段 13/13，dhrystone/coremark 18 个事件逐个相等 | 已合入 |
| 2026-11-07 | rtl `exp/pmu` | `b5a299a` | EXP-013：`rtl/pmu`（计数器块 + HPM CSR、生成的事件包）、`tests/pmu` | 30 万拍随机 0 不一致，变异能被抓到，lint 0 | 已合入（未接 CSR） |
| 2026-11-07 | trace-model `exp/pmu` | `a7960e4` | EXP-013：`PMU=1` 事件计数、TMA、逐 PC 画像、直方图、相位、SPEC 脚本 | gate 63/63（PMU 关、开），dhrystone/coremark/mcf 点周期不变，恒等式 0 违反 | 已合入 |
| 2026-11-07 | trace-model `exp/pmu` | `ee988d0` | `RealLsu::load_miss_mask` 改为 `bitset<ROB_NUM>`（64 位掩码丢 ROB 项 ≥64） | gate 63/63 周期不变 | 已合入 |
| 2026-11-07 | 总仓库 `main`（trace-model `exp/prefetch-h1`、rtl `exp/l1d-prefetch`、function-model `exp/sparse-mem` 合入 main） | 本次 | EXP-009 L1D 预取器 h1 合入本地 main（未推送）：先把 main 的 move elimination 合进两个分支（只有基线/参考周期/PROJECT.md 有冲突），用合并后的树重新生成 `baseline.csv`、`ref_cycles.txt`、`ref_cycles_nopf.txt`；函数模型稀疏拷贝；LLC 引擎控制实验作为补丁保存 | trace-model gate 63/63，关预取对 main 基线 62/62；RTL 逐条对比 67/67（开、关各一遍，周期与 trace-model 相等）；lint 0 警告；SPEC full 580/580（fast warmup）几何平均 +8.3% | 已合入 main；合并后的树上 Linux 13 段 0 不一致（2026-11-07 补跑） |
| 2026-11-07 | trace-model `exp/prefetch-h1` | `c2e2d67` | 全量 SPEC 脚本；节流、MSHR 预留、时间片对抗实验存为补丁 `docs/experiments/exp009_llc_engine_control.patch`，源码树保持冻结的 h1 | 全量 579 点：h1 +8.2%，节流 +7.2%，对抗 +7.7%（几何平均，SimPoint 权重） | 不采用 |
| 2026-11-06 | rtl `exp/move-elim` | `1e5d656` | EXP-012：`ttg_cfg_pkg`（`MOVE_ELIM` 1，`make cfg` 取 trace-model 默认）和 `ref_cycles.txt` 跟随 trace-model | 配置包与 `make cfg` 逐字节一致；`ref_cycles.txt` 与 trace-model 默认 66 个程序逐个相等；lint 0 警告 | 合入 main，见 MAIN_RECORDS |
| 2026-11-06 | rtl `exp/move-elim` | `a089838` | EXP-012：RTL 实现 mov 消除（`ren_elim_sel`、`ren_arch_cnt`、`ren_rank`；Ren/Dispatch/ROB/back_top 贯穿 `me_elim`；参数 `MOVE_ELIM`，默认关）；`scripts/tm_cycles.sh` 重新生成 ref_cycles | lint.sh / lint_chip.sh 0 警告（开、关）；关闭：`fm_gate` 66/66，周期与原 `ref_cycles.txt` 逐个相等；开启：66/66，周期与 trace-model 逐个相等 | `ren` +21.5k 单元（+10.4%），`dispatch`、`rob` 不变 |
| 2026-11-06 | trace-model `exp/move-elim-v2` | `1321fe5`、`767c25f`（rebase 到含 EXP-011 --fast-warmup 的 main `95c72d8` 之后；本系列较早提交的说明里写的是 EXP-010/011） | EXP-012：`CFG_MOVE_ELIM` 默认 1；`results/baseline/baseline.csv` 重新生成（7 个程序变化）；PROJECT.md 大程序标准周期更新（coremark 252,400、memory-stress 2,425,220）；文档编号改为 EXP-012 | gate 62/62 对新基线；dhrystone 162,033 不变，smc-div / smc-addi / memory-stress-small 不变 | quick SPEC 几何平均 IPC 1.550 → 1.551 |
| 2026-11-06 | trace-model `exp/move-elim-v2` | `8ecfaee` | EXP-012：mov 消除的开关 `CFG_MOVE_ELIM`（取代环境变量 `ME_ELIM`，默认关）和引用上限 `CFG_MOVE_ELIM_REFS`=7（`Ren::elim_refs_ok`：源来自推测 RAT、RAT 引用数 + 组内更老写者 + 1 ≤ 上限） | 关闭：gate 62/62，dhrystone 162,033、coremark 255,335 不变；开启（`-DCFG_MOVE_ELIM=1`，`ME_CHECK=1`）：gate 62/62 全部 Success、0 次不变量断言，coremark 252,400，引用数最大 4 | 上限只少消除约 25% 的 mov，周期不变差 |
| 2026-11-06 | rtl / `exp/l1d-prefetch`（已于 2026-11-07 合入 main） | `17ffdf7`、`a03ad5e`、`96f67c8`、`3df9dda` | **L1D 预取器 h1 的 RTL**（EXP-009）：新 `dcache_pf`；stage1 探测槽、stage2 训练事件、MSHR 预取标志/晋升/无填充释放、阵列 pf 位、LSU 到 L1D 的 `replay` 位；参数 `PF_EN`（默认 1）；`fm_gate.sh` 加 `REF_CYCLES`，`ref_cycles.txt` = 预取开，`ref_cycles_nopf.txt` = 旧基线 | `PF_EN=1`：`fm_gate.sh` 66/66 逐条对比通过且 **66 个程序周期与 trace-model 全部相等**（25 个因预取而变）；`PF_EN=0`：66/66、周期与旧基线相同；`lint.sh`、`lint_chip.sh` 0 警告；Linux 启动进行中 | 未合入 main；RQD 重测、冻结版 SPEC 复跑、WNS 未做 |
| 2026-11-06 | trace-model / `exp/prefetch-h1`（已于 2026-11-07 合入 main） | `0eb258c`（冻结版）、`1fe92b5`（默认开 + 新基线） | **L1D 预取器 h1 冻结**（EXP-009）：单表项全局步长 + LLC-only next-line，去掉研究开关/PC 管道/I 侧预取；默认开（`PF_ENABLE=0` 关）；gate 基线重新生成，旧基线存为 `baseline_nopf.csv` | 关：gate 62/62 与旧基线相同，64 KiB LLC 5 个测试与 main 相同；开：gate 62/62 对新基线；dhrystone 161,183、coremark 256,573、memory-stress 2,383,063、memory-stress-small 334,635 | 未合入 main；研究快照在 `exp/prefetch`（`27a878f`） |
| 2026-11-06 | trace-model、rtl `exp/dram-sim`（已合入 main） | trace-model `88e5254`、rtl `b19a181` | **基线重做**（EXP-006）：DRAMsim3 的非核心附加延迟 32 → 60 ns（SOC+CDC+CTL+PHY），`baseline.csv` 与 `ref_cycles.txt` 重新生成；此前还有 `ab44728`/`965347b`（DRAMsim3 子模块 + 静态库） | trace-model gate 62/62；RTL `fm_gate.sh` 66/66、周期全部相等；两边 Linux 启动到 `rv32 login:`；SPEC 全量 580 点无失败 | 周期平均 +23%；SPEC 几何平均 IPC 1.487 → 1.396，估算分数 8.66 → 8.12（@1 GHz）；`RQD=8` 仍够；受影响模块的 Yosys 面积代理已对比（见 EXPLORATION）：`RQD` 8 使 LLC +33k 单元、LSU store 窗口 −23k 单元；未做 16 分频配置回归 |
| 2026-11-05 | **合入 main**：trace-model `fcef337`..`08e9cfe`（5 个提交）、rtl `4a54ee1`..`52d2b84`（8 个）、function-model `b5c5ea0`..`d40c588`（3 个），均为分支快进 | 第 3 批面积配置（EXP-005）+ 文档整理 + SPEC 流程 | trace-model gate 62/62、Linux 到登录；RTL lint 0 警告、逐条对比 66/66 且周期与 trace-model 相等、Linux 从复位到登录全程逐条对比 0 不一致（约 3.6 小时） | 记录见 MAIN_RECORDS 2026-11-05 |
| 2026-11-05 | trace-model exp/tage-alt（未提交） | EXP-007：TAGE 训练时也更新备选提供者计数器（`CFG_TAGE_ALT_UPDATE`） | 关闭时 gate 62/62 不变；打开时 gate 全部 Success 无不一致；quick SPEC 6 个分支难预测程序 176 点 | 无收益（MPKI ±0.6%，几何平均 IPC 1.889 不变），不合入；`altpcpn` 可删 |
| 2026-11-05 | 各仓库（未合入） | 文档整理：总仓库新增 `docs/GUIDE.md`（导航）、`docs/TODO.md` 成为唯一待办（并入 rtl 旧路线图和 README “下一步”中仍有效的条目）；README 重写现状；WORKFLOW 补充合入 main 步骤；rtl 退役文档挪到 `docs/history/`、索引重写；trace-model `PLAN.md` 挪到 `docs/history/`、`PROJECT.md` 写明现行 gate 和参数开关；function-model SPEC 文档合并（现行流程 / 上游流程对照） | 四个仓库的相对链接检查无坏链接（vendored `axi-interconnect-kit` 除外） | — |
| 2026-11-05 | trace-model exp/area-explore（未提交） | quick SPEC 补齐 perlbench、sjeng | 6 个程序 151 点 × 3 组，0 失败 0 不一致 | 几何平均 IPC：基线 2.216，opt1 2.204，第 3 批 2.204（均 −0.5%） |
| 2026-11-05 | rtl exp/batch1-params（未提交）；trace-model exp/area-explore | 第 2、3 批：IQ 大小（INT 64/BR 32/STD 16）、front2back 8、端口 4/3/3/2 同步到 RTL；IQ 大小、FIFO 深度、LSU 通道、FU 表改为从参数推出；修 `lsu_core` store MMU 端口按 NLD 声明的潜在错误 | 4 套参数 lint 0 警告；FM 逐条对比各 66/66；基线参数下周期与改前全同 | 周期与 trace-model 一致；第 3 批 5 个小程序 +0.19%；综合约 −161 万门、−5 万触发器 |
| 2026-11-05 | rtl exp/batch1-params（未提交） | 第 1 批参数同步到 RTL：BFW 8、MAX_BR 32、ibuf 64；`dimmap.py`/`gen_backtop.py` 字段位宽参数化；测试平台 MMIO store 字段偏移改为由参数推出 | lint 两套参数 0 警告；FM 逐条对比 66/66（两套参数），串口输出一致 | 周期与 trace-model 一致（coremark 226,991→232,353）；相关模块约 −77 万门、−2.4 万触发器 |
| 2026-11-05 | trace-model exp/area-explore（未提交） | EXP-005：quick SPEC 基线 vs opt1 | gcc/mcf/hmmer/h264ref 136 点 0 不一致 | opt1 几何平均 −0.5%（gcc −1.2%）；统一 FTQ 上限 64 与 opt1 相同；perlbench/sjeng 待补 |
| 2026-11-05 | function-model exp/spec-rv32imab（未提交） | SPEC 检查点按原流程重建为 rv32imab（GCC 13.3，B 扩展），数据放 `~/personal/AI-Huma-data/spec-rv32imab`；`pipeline.sh` 校验前先去掉插进 RUN 行的 BBV 打印 | 12 个程序 BBV 输出与参考一致，检查点全部生成 | 旧 `/tmp/specref` 检查点因重启丢失 |
| 2026-11-05 | rtl / `exp/dram-sim`（已合入 main，工作目录 `rtl-dram`） | `0fce9a6`（store 窗口）、`e7fd5e0`（RQD 8）、`2d96516`（tick 参数化 + 配置包）、`947a2e0`（测试平台）| **RTL 同步新基线**（EXP-006）：`mem_top` 的 tick 数取自 `AXI_SUBSYSTEM_FREQ_DIV`（现为 1），`ttg_cfg_pkg` 重新生成，测试平台 `soc_tb`/`build.sh` 支持 1 tick 与 DRAMsim3，平台 SimDDR 换成带 `SIM_DDR_DATA` 的 trace-model 版本，`ref_cycles.txt` 用新 trace-model 重新生成；**修复 LSU store 提交窗口**：`lsu_dc_req_st` 误用 load 窗口（20），改为 `STWIN = LSU_STORE_WINDOW_WIDTH`（15） | `fm_gate.sh`：66/66 通过功能模型逐条比对，**66 个程序周期与 trace-model 全部相等**（修复前 62/66）；`lint.sh`、`lint_chip.sh` 通过；RTL 仿真约 34–37 千周期/秒（旧 16 tick 约 4.2–4.6 千） | 窗口不一致是第 3 批改端口后遗留的 RTL 缺陷，16 倍分频下被掩盖；`wait_mmu_stq`/`mmu_done_stq` 窗口仍为 20，未触发；Linux 启动到 `rv32 login:`（`RQD=8`）；未做综合 |
| 2026-11-05 | trace-model / `exp/dram-sim`（已合入 main） | `7bfe7d0`（开关，默认不变）、`f6a7589`（新基线）| **新基线**（EXP-006）：`config.h` 默认不分频（`FREQ_DIV` 1）、核心 1 GHz（`CPU_FREQ_MHZ` 1000），Makefile 默认带 DRAMsim3（`DS3=0` 退回旧 SimDDR），`baseline.csv` 重新生成（63 项），PROJECT.md 标准周期更新 | 新 `build/simulator` 跑 gate 62/62；大程序 dhrystone 158,756、coremark 250,658、memory-stress 2,425,029、smc-div 11,096、smc-addi 10,966、memory-stress-small 343,975 | 比旧基线周期多：gate 平均 +146%；RTL 侧未同步（仍 `FREQ_DIV=16`、固定延迟 SimDDR），与 trace-model 周期暂不相等，不能合入 `main`；未跑 Linux 与 small-LLC |
| 2026-11-05 | trace-model / `exp/dram-sim`（已合入 main） | `7bfe7d0`（开关，默认不变）、`f6a7589`（新基线）| EXP-006：`SimDDR` 增加 DRAMsim3 后端（`DS3=1` 编译开关，`SimDDR_DS3.h`），DS3 构建去掉 AXI 子系统 16 倍分频（`FREQ_DIV=1`），核心频率可配（`CPU_FREQ_MHZ`，编译期或环境变量）；首版时间换算漏计分频，结论作废并更正 | DS3 关闭：dhrystone/coremark/memory-stress-small 与基线一致、gate 62/62；不分频：原 SimDDR gate 平均 +151%，DS3 平均 +80%，61/62 正常退出（1 个超 4 倍周期上限），提交数除中断类外一致 | 16 倍分频掩盖了 DRAM 延迟（基线 60 tick = 3.75 核心周期）；DS3 平均读延迟 58–90 ns；若不分频作新基线，需重生成 baseline.csv 并同步 RTL；未做 difftest、大负载 |
| 2026-11-04 | trace-model exp/frontdoor-ckpt | `4f601ca` scripts/spec: replay.sh quick (6 programs, 90% weight, 129 points, ~20 min) / full (496 points, ~75 min) | quick+full ran | mov elimination (exp/move-elim rebased onto this branch, not merged): quick geomean IPC 2.356 -> 2.367 (+0.46%) |
| 2026-11-04 | trace-model exp/frontdoor-ckpt | `bdd30dd` PeripheralAxi: uncached-RAM stores no longer written into the shared core RAM (the 0x87f00000 window clobbered newer reference stores) | gate 61/61; dhrystone 150,838 / coremark 226,991 cycles unchanged; SPEC full replay 496/496 points, 0 crashes (before: 36 segfaults) | xalancbmk IPC 2.441 -> 2.786; perlbench -0.4%, hmmer +0.07%, other 9 programs identical; SPECint2006 geomean 13.0 -> 13.2 /GHz (estimate) |
| 2026-11-04 | trace-model `exp/area-explore`（未提交、未合入） | — | **EXP-004 组合优化配置 opt1**：MAX_BR 32、INT IQ 64、BR IQ 32 加上 EXP-001/002 的全部优化；详见 [EXPLORATION.md](EXPLORATION.md#exp-004-组合优化配置-opt1) | gate 62 个程序全部跑完、difftest 无不一致；5 个小负载 | 小程序几何平均持平，coremark 慢 1.8–2.7%；quick SPEC 没跑：`/tmp/specref` 检查点在 15:30 重启时被清空 |
| 2026-11-04 | trace-model `exp/area-explore`（未提交、未合入） | — | **EXP-003 ROB/PRF 扩大**：新增 `CFG_ROB_NUM`、`CFG_PRF_NUM` 开关；测 ROB/PRF 192、256 及与 lean2 的组合；详见 [EXPLORATION.md](EXPLORATION.md#exp-003-rob-与-prf-扩大到-256) | 5 个小负载，difftest 全部跑完 | ROB+PRF 都翻倍只快约 0.8%（coremark 3%），ROB 128 合理 |
| 2026-11-04 | trace-model `exp/area-explore`（未提交、未合入） | — | `CFG_BACKEND_FETCH_WIDTH` 开关；确认 `BACKEND_FETCH_WIDTH=16` 是遗留参数（前端都按 8） | 设为 8：gate 62/62、5 个负载周期全部不变 | 可直接改成 8，见 EXP-001 结果 1 |
| 2026-11-04 | trace-model `exp/area-explore`（未提交、未合入） | — | **EXP-002 全核面积浪费排查**：新增 INT/BR IQ 容量、ibuf、MAX_BR_NUM、纯 ALU/BRU 端口数开关和在飞分支、ROB 占用统计；详见 [EXPLORATION.md](EXPLORATION.md#exp-002-全核面积浪费排查) | 默认配置 gate 62/62 周期不变；5 个小负载扫描 19 个单项变体和 2 个组合 | 组合配置 lean2（IQ 384→176 项、BRU 4→2、STA/STD 4→3、ibuf 64、front2back 8）无性能损失；ROB 是瓶颈；BPU 存储约 1.1 Mb 待大负载评估 |
| 2026-11-04 | 总仓库 `docs/` | — | **记录规则**：WORKFLOW 新增第 5 节，每次探索写 [EXPLORATION.md](EXPLORATION.md)，每次合入 `main` 写 [MAIN_RECORDS.md](MAIN_RECORDS.md)（性能 + 综合，未做综合写"未做"）；MAIN_RECORDS 以当前 `main` 作起始行 | 只改文档 | — |
| 2026-11-04 | trace-model `exp/area-explore`（未提交、未合入） | — | **EXP-001 面积探索**：统计插桩（`ARCH_STATS`）、统一 FTQ 容量上限（`UFTQ_CAP`）、访存端口数/IQ 容量/LD+STA IQ 合并编译开关；详见 [EXPLORATION.md](EXPLORATION.md#exp-001-面积优化三个方向) | 默认配置及 `ARCH_STATS=1` 下 gate 62/62 周期不变；5 个小负载扫描 | 统一 FTQ 64 项、端口 4/3/3、LD+STA 合并 64 项均几乎无性能损失 |
| 2026-11-04 | function-model / trace-model / rtl `main` | — | **中断 CSR 按规范**：`mie`/`mip` 去掉用户级位（0xAAA），`mideleg` 只留 SSI/STI/SEI，`sie`/`sip` 按 `mideleg` 屏蔽，`sip` 只写 SSIP；三处同步（function-model `exec.cpp`、trace-model `Csr.cpp`、RTL `csr_*.sv`）。Spike 对比 66 个程序 64 个一致（`csr-alias-boundary` 现在一致）。`csr-alias-boundary` 周期 736 → 709（gate 基线和 `ref_cycles.txt` 已更新） | gate 62/62；RTL 64 个程序逐条对比一致；Linux 从头启动在 trace-model 上验证中 |
| 2026-11-04 | function-model `main` | — | **Spike 逐条对比接通**：适配当前 riscv-isa-sim，`scripts/build_spike.sh`（仓库外构建）；Linux 启动 1.35 亿条指令到登录无不一致；66 个 gate/vm 程序 63 个一致，3 个已知差异（`sie` 按 0x333 而非 `mideleg` 屏蔽，`mip` 的 MTIP/MSIP 来自平台）见 `docs/SPIKE_DIFFTEST.md` | 未改 ISA 行为 |
| 2026-11-04 | rtl `main`; trace-model `b028a20` | — | **Linux 从头启动打通 + 断开旧参考的最后联系**：核对不认识的 CSR 触发非法指令（trace-model `Idu.cpp` 与 RTL `idu_ctrl_decode.sv` 同步），OpenSBI 不再误测出 sstc，trace-model 从头启动到 `rv32 login:`（130M 提交、115M 周期），gate 62/62，RTL 64 个 gate/vm 程序逐条一致；RTL 新增检查点启动（`SOC_TB_STUB`、`tools/ckpt2image.py`）；`gen_cfg.sh` 改读 `trace-model/include/config.h`，去掉 `BASELINE_SRC` 及 `baseline/` 程序前缀，`ref_cycles.txt` 改记为 trace-model gate 基线 | RTL 从 5800 万处检查点到登录的长跑进行中 |
| 2026-11-04 | rtl `main` | — | **退役逐模块锁步体系**：删除 117 个文件（锁步/录制/回放/变异脚本、各模块 rand_trace/mutants、replay harness、selftest、refhook），只保留 lint、整核闭环、逐条提交对比、`tests/fpu`、`tests/common`、`tests/dcache`；文档改为"function-model 逐条提交一致是门禁，周期数是性能指标"（`06-equivalence-policy.md` 重写，旧文档加退役提示；风险 V-12 登记新门禁覆盖缺口） | 未重跑整核构建（只改脚本/文档/测试文件）；旧内容在标签 `legacy-reference` |
| 2026-11-04 | rtl `94608cc` / tag `legacy-reference`; trace-model `main` | — | **参考改为 function-model**：整核测试平台新增逐条提交对比（`SOC_FM=1` 构建、`SOC_TB_FM=1` 运行：提交 PC + 目的寄存器值，设备读值取 RTL，中断强制注入），gate+vm 64 个程序全部一致；trace-model 的 `mtime` 现在跟周期走（gate 62/62）。本地清掉旧参考副本 `refsim*`、`traces/` 和多余的构建目录（约 5.5 GB，可由 `scripts/refsim_setup.sh` 和旧参考源码重新生成）；依赖旧参考的逐模块锁步/录制脚本仍在仓库里，打了标签 `legacy-reference` | Linux 启动到登录提示符的确认仍在后台进行 |
| 2026-11-04 | function-model / trace-model / rtl `main` | — | 去掉 GenSimpoint 这个名字：trace-model 里的符号链接改为 `function-model`，各脚本和文档的路径同步改，function-model 的 upstream 远程删除（来源只在文档里留作溯源） | `make -n` 路径通；未重编（Linux 长跑进行中） |
| 2026-11-04 | rtl `a3f212d` / `main` | — | **参考模型退役**（用户决定）：闭环测试平台不再依赖参考模拟器源码——`tb/soc/platform/` 收进 19 个冻结的平台模型文件（SimDDR、PhysMemory、PeripheralModel 及头文件，约 300 KB），`gen_cfg.sh` 改取其中的配置，4 个额外程序移到 `programs/extra/`。记录后果：周期对 trace-model、架构值对 function-model；模块级锁步（`refsim*` 与 `traces/`）降为冻结的回归工具、不再扩展，新增行为（如 S-27）无法用它验证（风险 V-11） | `gen_cfg.sh` 重新生成配置包与原来完全一致；用收进来的文件重新构建测试平台；短程序闭环 51/51 | 重建 `refsim*` 仍需要原参考源码（AI-Huma 之外、未被任何仓库跟踪）；本地 `refsim*`、`traces/` 被 git 忽略，丢了无法重建 |
| 2026-11-04 | trace-model `42b43db` / rtl `c4d70a0` / `main` | — | **Linux 启动：ebreak 断点异常**。OpenSBI 1.2 探测 semihosting 的 `slli x0,x0,0x1f; ebreak; srai x0,x0,7` 需要一次断点异常，原来 trace-model、RTL 和原参考模型都把任何 ebreak 当作程序结束，所以 Linux 镜像在第 62,061 周期（205,443 条提交）就退出。现在与 function-model（`2191b77`）规则相同：夹在标记序列之间的 ebreak 触发 cause 3（`mepc` = `mtval` = 该 pc，`medeleg[3]` 仅非 M 态委托），其余 ebreak 仍结束仿真。trace-model：`RobBroadcastIO.breakpoint`、`Rob::comb_commit`、`Csr::comb_exception`。RTL：编译宏 `TTG_EBREAK_TRAP`（默认关闭，关闭时与参考逐位一致）、`rob_trap_ctrl`、`csr_trap_class`、规格 `rob.io`/`csr.io`、测试平台 `SOC_TB_SEMIHOST`；登记偏差 S-27。另修一个我自己引入的 bug：`env.sh` 不应默认导出 `REFSIM`（覆盖了各脚本自己的 refsim/refsim_tap 默认） | trace-model：gate 62/62；同一 Linux 镜像（运行模式）跑过原停止点，100 万条提交在第 247,399 周期，桥比对 0 不一致。RTL：lint；短程序闭环 51/51；rob/csr/back_top 锁步 3 个程序 9/9；**RTL（TTG_EBREAK_TRAP 构建）与 trace-model 在同一 Linux 镜像上逐周期一致**：第 62,061 / 107,585 / 247,399 周期的提交数 205,443 / 400,002 / 1,000,007 完全相同 | 只对照到前 100 万条提交（RTL 每秒约 4–5 千周期，完整启动要 7 小时以上）；检查点恢复是下一步 |
| 2026-11-04 | rtl / `main` | 见子模块 | 路径统一：新增 `scripts/env.sh`、`scripts/ttg_env.py`，原来 58 个文件里 245 处写死的绝对路径全部改为由仓库位置推出、可用环境变量覆盖；程序清单改写相对条目（`tests/`、`vm/`、`big/`、`tm/`、`baseline/`）；`float_test.bin` 与 dhrystone/coremark 构建脚本改用 trace-model/baremetal（重编的二进制与原来逐字节相同）；`progs.txt` 去掉已非标准的 coremark10 | 只做了小检查：`gen_cfg.sh` 重新生成配置包与原来完全一致；短程序闭环 51/51；与 trace-model 对比 5 个程序一致；所有清单条目均能解析到存在的文件。**没有重跑锁步或整套闭环** | 仅整理；参考模型源码仍在 AI-Huma 之外，由 `BASELINE_SRC` 指定 |
| 2026-11-04 | trace-model `00e02fc` / function-model `4f9fd4e` / `main` | — | **更正并修复一个验证缺口**：trace-model 的 `GenSimpoint` 子模块一直固定在 function-model `354664a`，落后 `main` 14 个提交，所以此前 gate 跑的是旧版 function-model。现在 `GenSimpoint/` 改为指向 `../function-model` 的符号链接（只有一份 function-model，所有 Makefile/脚本路径不变），并移除 `.gitmodules`；trace-model 的阶段性历史文档（`P0..P3`、`STEP_*`）归档到 `docs/history/`。function-model：`DIFFTEST.md`、`SIMPOINT_SPECINT2006.md` 移到 `docs/`，`run_bbv.sh`、`run_ckpt.sh` 移到 `scripts/`（在仓库根目录运行） | 用 function-model `b1be24a` 完整重编 trace-model 后：`run_gate.sh` 62/62；dhrystone 64 次 150,838、coremark 2 次 226,991、memory-stress 1,541,195、smc-div 8,996、smc-addi 8,866，与之前完全一致 | 无行为变化；此前"function-model 新提交已被 trace-model gate 间接验证"的说法不成立，现已用新版直接验证 |
| 2026-11-04 | 三个子仓库 `main` | function-model `b1be24a` / rtl 见子模块 | 仓库整理：删除已并入 `main` 的 31 个旧分支（rtl 26 个 `rtl/*`、function-model 3 个 `exp/*`、trace-model 2 个 `exp/*`），保留未合入的 `exp/move-elim`、`exp/move-elim-pre-rebase`；function-model 取消跟踪生成文件 `compile_commands.json`；rtl 文档改为默认直接在 `main` 上工作、不再为每个模块单开工作树；删除 trace-model 本地生成的 `build_small/` | 被删分支均 `git branch -d`（已并入才允许删）；无代码改动 | 仅整理，无行为变化 |
| 2026-11-04 | trace-model `65affb3` / function-model `2ed1eb6` / `main`（快进合入 `exp/frontdoor-ckpt`） | — | 三个仓库的 `main` 现在都是各自最新：trace-model 领先 `main` 7 个提交（front-door 检查点恢复、bridge 回退修复、PeripheralAxi 修复、SPEC 检查点回放脚本、gate 加入 load-store-aligned、上游遗留清理），function-model 领先 14 个提交（速度优化、front-door 恢复、环境变量开关等）；rtl 的 `main` 本来就是主线。分支 `exp/frontdoor-ckpt` 保留 | **trace-model**：gate 62/62；dhrystone 64 次 150,838、coremark 2 次 226,991、memory-stress 1,541,195、smc-div 8,996、smc-addi 8,866、memory-stress-small 189,128 均与标准一致；小 LLC（64 KiB）检查 4 个程序基线与新版周期相同（load-store 因基线无数字为已知失败）。**function-model**：用 `main` 版和分支版各自编译的独立运行结果，在 62 个 gate 程序上执行的指令数完全一致（4 个中断程序与 trace-model 的计数不同，但 `main` 版本身就是这个值，非本次引入）。bridge 修复（`8e5daf0`）解决了 libquantum@125M 检查点上被污染的寄存器导致的提前退出 | 满足 `main` 合入条件；rtl 与 trace-model 的模块边界逐拍对照仍未做，见 `rtl/docs/08-risk-register.md` |
| 2026-11-04 | trace-model / `exp/frontdoor-ckpt`（未合入） | `65affb3` | 清理上游遗留：`.github`、`ci`、`.codex`、`.claude`、`doc/`（原执行驱动模块设计文档）、`script/`（原 SPEC 评分/画图/回归脚本）、`baremetal/riscv-tests`、预编译基准、`.o`、`tmp.md`、`compile_commands.json`、`tree.dts`、`tools/`、vendored axi kit 的 demos 与 `*_test.cpp`；`README.md` 换成指向 `docs/PROJECT.md` 的简短版。共删 486 个文件，历史里仍可找回 | 删除的文件均无构建、脚本、测试、文档引用；`gmake -n -B` 所需的 46 个源文件/库全部存在；`run_gate.sh` 62/62 | 未合入 `main` |
| 2026-11-04 | rtl / `main` | `fb96e66` | 删除依赖已清理的 per-module 工作树的复核脚本 `extra_check.sh`、`review_front.sh`、`review_exu_int.sh`，并更新 `scripts/README.md` | 无其他文件引用它们 | — |
| 2026-11-04 | AI-Huma（总仓库）/ `main` | 文档更新 | `README.md`：补充总仓库/子模块结构与克隆方法、文档索引（含 rtl 风险登记簿）、gate 62 个与大程序固定标准、更新 rtl 当前状态和下一步、复现步骤加入 rtl；`WORKFLOW.md`：变异检查改为可选、存活变异改为登记而不要求清零 | 文档改动；README 里的数字（62 个 gate、66 个闭环程序、63 个与 trace-model 一致、rtl 约 300 个文件/3 万行）已逐项核对 | 仅文档 |
| 2026-11-04 | trace-model / `exp/frontdoor-ckpt`（未合入） | `97a8589` | gate 加入 `load-store-aligned`（原 `load-store` 在参考核里遇到未对齐 load 直接退出，基线无周期数；新程序用对齐的逐字节读取拼出同样的字）；`run_gate.sh` 的排除规则收窄为只排除 `load-store/` 目录；`PROJECT.md`：gate 62 个、大程序固定为 dhrystone 64 次 / coremark 2 次、rtl 的位置 | `run_gate.sh` 62/62 通过；基线 536 周期 / 144 条指令，trace-model 与 RTL 闭环一致 | 未合入 `main`（该分支为 front-door checkpoint 实验） |
| 2026-11-04 | function-model / `exp/frontdoor-ckpt`（未合入） | `2ed1eb6` | `ref.h`：指令上限与 BBV/检查点间隔改为环境变量（`REF_MAX_INSTS`、`REF_INTERVAL`），默认不设上限、间隔仍为 1e8 | `refcpu_api.cpp`、`exec.cpp` 语法检查无错误；未跑功能回归 | 未合入 `main`；该改动是工作区里已有的未提交内容，本次只做提交 |
| 2026-11-04 | AI-Huma（总仓库）/ `main` | 初始提交 | 新建总仓库：根目录 `.gitignore`、`README.md`、`docs/`，三个子项目 function-model / trace-model / rtl 作为 git 子模块引用（URL 暂为本地路径，发布时再改）。子模块只记录各自已提交的 commit：function-model `215140b`、trace-model `4f601ca`（均在 `exp/frontdoor-ckpt`，工作区各有未提交改动，不在本次提交里）、rtl `01e31e4`（`main`） | 无代码改动；`git submodule status` 三个子模块均解析到上述 commit | 仅建立仓库结构，不涉及 `main` 合入条件 |
| 2026-11-04 | rtl / `main` | `339adce`..`01e31e4` | rtl 从 `~/personal/tututugege-rtl` 搬到 `AI-Huma/rtl`（旧的 28 个工作树清理）；路径统一；测试程序改取自 trace-model/build；`programs/big/` 固定 dhrystone 64 次、coremark 2 次；取消跟踪 coremark/dhrystone 编译产物 | lint 290 个文件干净；闭环 66 个程序周期数与参考一致；与 trace-model 63 个 smoke 程序周期数、指令数一致；模块级 / LLC 随机 / 16 tick 锁步抽查通过 | 与 trace-model 的模块边界逐拍对照、综合检查未做，变异存活按决定不清零而改为记录，见 `rtl/docs/08-risk-register.md` |
| 2026-11-03 | trace-model exp/frontdoor-ckpt | Bridge fix: position-based rewind + kill_older_than (wrong-path stragglers kept their register writes) | gate 61/61, perf cycles unchanged; lq125m no longer Oopses (old back-door baseline 2,623,210 was corrupt; now 1,552,165); other 5 ckpts unchanged |
| 2026-11-03 | trace-model exp/frontdoor-ckpt | `--restore-stub` front-door restore through the pipeline | 5/6 ckpts within 0.3% of back-door cycles; lq125m hits a latent timer-interrupt bug (exits at 773,834 commits; timer shifts also trigger it) |
| 2026-11-03 | function-model exp/frontdoor-ckpt | ckpt2stub writes timer last (mtime skew ~tens of cycles) | function model identical 20M instr on all 6 ckpts |
| 2026-11-03 | function-model / `exp/frontdoor-ckpt`（未合入） | `84afef3` | 前门检查点恢复：`--restore-mem-only` 只恢复内存，`tools/ckpt2stub.py` 从检查点生成恢复程序（写定时器、UART、CSR、31 个寄存器，最后 `mret`），第一条 `mret` 之后才开始计数；`REF_STATE_DIGEST_FULL`；`tools/frontdoor_check.sh` | 与后门恢复逐点比较完整状态摘要：6 个 S/U 态检查点各 2000 万条指令、4 个 M 态检查点各 500 万条全部相同；M 态陷阱入口第一条指令处不一致（`mret` 清掉 MPP、MPIE、mepc，已知限制）；原有回归不变 | 前门恢复在 function-model 里验证通过 |
| 2026-11-03 | trace-model / `exp/ckpt-bridge-state`（未合入） | `565f059` | 检查点恢复时，把 CPU 状态和设备寄存器也写入桥使用的函数核心（`pmem_core_ctx()`）；原来只写了参考核心 `ref_cpu_ctx`，桥的核心停在复位状态，地址全错，运行变成陷阱风暴 | 6 个由 function-model 生成的 SPEC 检查点各跑 300 万条提交全部正常（IPC 1.14 到 4.25）；TB_CHECK 的分支、地址、目标比对 0 不匹配；同一检查点在旧版和提速版 function-model 上周期数相同（289,084）；gate 61/61 | function-model 加 trace-model 联合跑 SPEC 的流程跑通 |
| 2026-11-03 | function-model / `exp/fm-speed`（未合入） | `cb8f78d` | 快速路径接入 BBV、SimPoint 检查点、特殊检查点和恢复模式：预算少留一条让最后一条由 `RISCV()` 执行以保证停点状态精确；区间边界处理抽成共用的 lambda，快速路径在完成区间的 U 态分支后退出；BBV 在每个 U 态分支处写回块长度并调 `bbv_commit()`；检查点生成模式下维护最后一次存储的三个字段 | 同一二进制开关快速路径各跑一次：BBV 文件和输出逐字节相同（libquantum 5 个区间、omnetpp 33 个区间）；2 个 SimPoint 检查点和 3 个特殊检查点逐字节相同；恢复模式 3999 个块摘要相同；原有回归不变，用此库重建 trace-model gate 61/61、周期一致 | BBV 生成约 3.7 倍（omnetpp 45 s 到 12 s）；检查点生成主要时间在写 2 GiB 内存；普通模式速度不变 |
| 2026-11-03 | function-model / `exp/fm-speed`（未合入） | `af7bb1e` | 访存指令内联 TLB 命中检查（未命中才调 `va2pa`）；融合 29 对相邻指令（`LW+LW`、`SW+SW`、`ADDI+ADDI`、`LW+ADDI`、`ANDI+BEQ`、`AUIPC+JALR` 等，按真实动态频率选），融合处理分支是第一条指令的执行体、指针加一、第二条的执行体，回退位置保持精确；`REF_FAST_STATS` 增加相邻指令对统计 | 块边界摘要与原路径逐点相同（xalancbmk 92.1 万点、libquantum 36.9 万点，另有 9973 和 100003 间隔），逐指令摘要相同，trace-model 65 个测试一致，用此库重建 trace-model gate 61/61、周期一致 | 相对上一个提交 libquantum +20%、omnetpp +18%、xalancbmk +15%、紧凑循环 +8%；试过 ThinLTO、PGO、clang 23、O2 等编译选项，没有稳定收益，未采用 |
| 2026-11-03 | function-model / `exp/fm-speed`（未合入） | `bd5d957` | CSR 指令走快速路径（作为块的最后一条，调用同一个 `RV32CSR()`，之后只在 satp、特权级、mie、mip、数据访问特权变化或有中断变得可递交时退出）；入口的中断前置条件改为 `evaluate_interrupts` 的精确判断；块缓存 1024 到 16384 块 | 块边界摘要与原路径逐点相同（libquantum 11.1 万点、omnetpp 3.9 万点、xalancbmk 9200 点），逐指令摘要相同，trace-model 65 个测试一致，用此库重建 trace-model gate 61/61、周期一致 | 紧凑循环约 980 MIPS；libquantum 352 到 418 MIPS，xalancbmk 262 到 313，omnetpp 253 到 337；块重建 1.488 亿次降到 1376 万次 |
| 2026-11-03 | function-model / `exp/fm-speed`（未合入） | `b682b86` | 基本块缓存加计算跳转分发，取代逐指令译码缓存：块内连续的整数指令一次译码、入口校验一次（虚拟 PC、satp 加特权级、纪元号），块内 `goto *` 直接跳转；U 态块和区间计数按块批量；写代码页或页表页时整体失效并放弃块的剩余部分；新增调试选项 `REF_STATE_DIGEST_BLOCK`、`REF_DIGEST_LIST` | 块边界摘要与原路径逐点相同（libquantum 11.1 万点、omnetpp 3.9 万点、xalancbmk），逐指令摘要相同，trace-model 65 个测试一致，用此库重建 trace-model gate 61/61、周期一致 | 紧凑循环 939 到 950 MIPS，Spike 为 841 到 876 MIPS；libquantum 约 7.0 倍、xalancbmk 约 5.3 倍、omnetpp 约 5.8 倍；BBV 与检查点生成模式尚未接入 |
| 2026-11-03 | function-model / `exp/fm-speed`（未合入） | `be45942` | 译码缓存加快速路径：常见整数指令（运算、乘除、分支、跳转、访问 DDR 的 load/store）按译码缓存执行，其余（MMIO、缺页、CSR、原子、浮点、中断）在不改状态时回退到 `RISCV()`；缓存按虚拟 PC、(satp, 特权级)、纪元校验，写代码页或页表页时整体失效；调试选项 `REF_NO_FAST`、`REF_STATE_DIGEST`、`REF_FAST_STATS` | 开关快速路径各跑一次，每 10 万条指令比较 PC 与寄存器哈希：libquantum、xalancbmk、omnetpp 共约 5.9 万个点全部相同；trace-model 65 个测试与基线一致（含 smc-*）；用此库重建 trace-model，gate 61/61、周期一致 | 紧凑循环 636 MIPS（约 7.9 倍），libquantum 约 6.3 倍，xalancbmk 约 4.9 倍，omnetpp 约 4.8 倍；BBV 和检查点生成模式尚未接入 |
| 2026-11-03 | function-model / `exp/fm-speed`（未合入） | `58aa5b0` | 软件 TLB（页表页被写则失效）、中断和陷阱的快速判断、普通模式的精简主循环、DDR 取指快路径、冷路径不内联 | 周期数与输出摘要与基线逐项相同（4 个分页测试、7 个裸机程序、3 个 SPEC 镜像） | libquantum 22.3 s → 9.7 s，omnetpp 90 s → 38 s |
| 2026-11-03 | function-model / `exp/linux-boot`（未合入） | `d7624fa` | `linux/`：设备树 `ttg.dts`、镜像脚本 `mkimage.sh`、README；`a.out.nospike` 加入忽略 | Linux 5.15.170 约 0.12 G 条指令启动到 `rv32 login:`；SPECint2006 12 个 test 程序全部输出匹配（libquantum 仅 CRLF 差异，astar 两处相对差约 1e-4，在 1e-3 容差内） | 完成 |
| 2026-11-03 | function-model / `exp/linux-boot`（未合入） | `74d09bf` | 调试环境变量：`REF_PC_EVERY`、`REF_PC_RING`、`REF_TRAP_TRACE`/`REF_TRAP_EVERY`、`REF_UNBUF`；ebreak 退出信息带 pc | 每个阶段 `g++ -fsyntax-only` 通过，HEAD 完整构建，add、libquantum 跑通 | 仅调试用 |
| 2026-11-03 | function-model / `exp/linux-boot`（未合入） | `4bba849` | **偏离 DUT**：`mip` 写掩码去掉 MTIP（0xbbb → 0xb3b） | 原掩码下 OpenSBI 的 `csrs mip, STIP` 把合成的 MTIP 永久写入，Linux 被时钟中断淹没起不来；去掉后正常启动 | 合并前要和 DUT 核对 MTIP 是否可写 |
| 2026-11-03 | function-model / `exp/linux-boot`（未合入） | `003b268` | S 态发出 SBI 关机/复位 ecall（`a7=8` 或 SRST）时结束仿真 | libquantum 镜像在 `Power down` 后立即退出，约 23 s；裸机 add、dhrystone 仍以 ebreak 正常结束 | 完成 |
| 2026-11-03 | function-model / `exp/linux-boot`（未合入） | `2191b77` | 半主机标记序列中的 `ebreak` 触发断点异常（cause 3），M 态陷阱不委托；其他 `ebreak` 仍是退出 | OpenSBI 1.2 能越过半主机探测并打印横幅；裸机测试退出不受影响 | 完成 |
| 2026-11-03 | trace-model / `exp/move-elim`（未合入） | `60a1ee8` | `ME_CHECK=1` 额外打印每周期最大引用数 | 开启后 dhrystone、coremark10 各跑一次；gate 61/61 | 架构态最多 4 份引用（coremark 仅 15 周期），dhrystone 最多 2 份；3 位计数器够用 |
| 2026-11-03 | trace-model / `exp/move-elim`（未合入） | `7b6c42e` | `ME_CHECK=1`：每周期检查引用计数等于架构映射表项数、无物理寄存器泄漏 | gate 61 个测试 + 4 个大程序开启检查，0 次断言 | 未发现泄漏 |
| 2026-11-03 | trace-model / `exp/move-elim`（未合入） | `32175e1` | mov 消除实验（`ME_ELIM=1`，默认关）：`addi rd,rs,0` 重命名时共用源物理寄存器，不进发射队列，ROB 立即完成；提交时引用计数 | 关闭时 gate 61/61、5 个大程序周期不变；开启时提交指令数不变 | dhrystone −0.77%，coremark10 −1.15% 周期 |
| 2026-11-03 | trace-model / `main` | `502fa18` | docs：AI-Huma 三仓库布局 | 无代码改动 | — |
| 2026-11-03 | trace-model / `main` | `9ff02eb` | GenSimpoint 改为 function-model 仓库的子模块 | 从零构建，gate 61/61，5 个大程序周期与原模型一致 | 完成 |
| 2026-11-03 | function-model / `main` | `354664a` | macOS 版 SoftFloat 构建，忽略构建产物 | 随 trace-model 一起验证 | 完成 |
| 2026-11-03 | trace-model / `main` | `e53cd45`, `b23dfd1` | 并入 axi-interconnect-kit 与 GenSimpoint，导入 tests、scripts、docs、gate 基线，写 `docs/PROJECT.md` | 从零构建：gate 61/61，small-LLC 与原模型一致 | 完成 |

## 历史（按仓库，从最早到最新）

以下由 git 历史一次性生成，是各 commit 的原始标题。

### trace-model / `main`（上游 tututugege/simulator 2f31e8d 之后）

共 87 个 commit。

| 日期 | commit | 做了什么 |
|---|---|---|
| 2026-11-02 | `a74ba7d` | IssueQueue/PreIduQueue: dirty-tracked seq copies, drop redundant comb_begin copies (exact) |
| 2026-11-02 | `6a0f887` | P1b: trace bridge taps (dispatch/mispredict/commit/flush/exec) and check mode (TB_CHECK=1) |
| 2026-11-02 | `8fedc6a` | P2a: facts drive BRU/AGU/SDU/CSR write data (TB_INJECT), poison and perturb controls, boot ROM fetch, control-flow evaluation in bridge |
| 2026-11-02 | `78616f8` | P2b: bridge-native commit-time traps/interrupts (no difftest ref state), controls |
| 2026-11-02 | `8879110` | P3.1: delete ALU/MUL/DIV/FP value compute, FPU softfloat and generated FADD/FMUL (23k lines); facts mandatory, difftest off |
| 2026-11-02 | `522c60c` | P3.2: delete PRF register file, operand fields and value consumers (facts only); skip idle LLC table write payloads |
| 2026-11-02 | `348a99f` | P3.3a: ROB-commit-time functional memory writes from facts; DDR no longer writes pmem |
| 2026-11-02 | `845363d` | P3.3b/c: LLC and L1D line data deleted; instruction/PTE/LLC data from pmem; SIM_MAX_CYCLES guard |
| 2026-11-02 | `6f58162` | P3.4a: one Uop for every pipeline stage; per-stage structs are aliases, converters are identity |
| 2026-11-02 | `0d8e240` | P3.4b: shrink AXI/LLC wide data payloads |
| 2026-11-02 | `dbf2e41` | P3.5: id-indexed uops: create-once fields live in a pool, pipeline entries hold id + mutable fields |
| 2026-11-02 | `c0c1f64` | Cleanup: remove host profile and frontend stats infrastructure |
| 2026-11-02 | `488efe8` | Cleanup: strip the statistics suite (PerfCount 1404 -> 33 lines, TMA blocks, LLC/L1D/LSU counters) |
| 2026-11-02 | `d2f73ab` | Single configuration: drop small/medium/large profiles and prune dead #if branches with unifdef |
| 2026-11-02 | `454bba6` | ICache S1: remove generated bool-array kernel and pack/unpack glue; keep native comb_core (front-end/icache 7.9k -> 3.3k lines) |
| 2026-11-02 | `5d34398` | ICache S2: drop the data table; hit lines are read from pmem by (tag, index) |
| 2026-11-02 | `e0ef1df` | ICache S3: refill returns line words from pmem; drop table_write.data, dcache probe data, step line copies |
| 2026-11-02 | `e1b3c43` | AXI idle-tick skip: stop the 16x extra subsystem ticks once AXI/LLC/DDR/MMIO and the L1D fast domain are quiescent |
| 2026-11-02 | `9aec0cb` | BPU: write UpdateRequest in place, pass ReadData by reference to the NLP stage, in-place GHR/FH update |
| 2026-11-02 | `6162e2b` | PreIduQueue: sync only touched instruction-buffer slots and the allocated FTQ slot at seq |
| 2026-11-02 | `5f0ac3e` | IssueQueue: sync only dirty entry slots at seq |
| 2026-11-02 | `16a0774` | front-end: prune dead preprocessor branches (2-ahead, TAGE-SC-L, ideal icache, SRAM model) and the falcon/front stats counters |
| 2026-11-02 | `c312fb2` | front-end: remove debug logging and focus-dump code |
| 2026-11-02 | `f397569` | front-end: drop the unused simple ICache top, bit helpers and dead train_IO declarations |
| 2026-11-02 | `e99145a` | BPU: remove the disabled NLP / 2-ahead predictor state and wrappers |
| 2026-11-02 | `b6aee7b` | front-end: remove mini-flush / dummy PTAB entries and the 2-ahead outputs (always off) |
| 2026-11-02 | `d7ef9ac` | BPU: inline the history and update-queue comb wrappers |
| 2026-11-02 | `e516b98` | BPU: merge the pre-read comb and data read into bpu_data_read |
| 2026-11-02 | `321def0` | BPU: inline post-read and submodule-bind wrappers |
| 2026-11-02 | `f52df65` | BPU: inline the predict-main wrapper (all BPU top-level comb wrappers are gone) |
| 2026-11-02 | `59f6290` | front_top: build the BPU input once and inline the global-control / read-enable glue |
| 2026-11-02 | `381c5c3` | front-end: carry the prediction metadata as one PredMeta through BPU, PTAB and the front2back FIFO |
| 2026-11-02 | `f2be766` | IssueQueue: reuse scheduling scratch buffers; TLB: skip the bit-vector kernel round trip when translation is off (verified against the kernel) |
| 2026-11-02 | `b2166ae` | TraceBridge: translate virtual addresses before the RAM / undo checks (fixes paging programs) |
| 2026-11-02 | `4a0d3fb` | TLB: run the native core_comb/top_comb; remove the bit-vector kernel (TlbMmuKernel.h) and codec |
| 2026-11-02 | `5d628c0` | PTW: remove the packed compact-core kernel and the bit-vector codec (dead at runtime) |
| 2026-11-02 | `837f506` | top level: remove the dead difftest hooks, config banner and unused tick helpers |
| 2026-11-02 | `bf2f966` | back-end IO.h: replace zeroing-only constructors with default member initializers |
| 2026-11-02 | `812a286` | PredMeta templated by width: front_top_out, FrontPreIO and the FTQ train meta carry the bundle as one struct |
| 2026-11-02 | `31b2ac5` | Exu: one table-driven Fu class (single/pipelined/iterative) replaces the AbstractFU hierarchy and the per-unit classes |
| 2026-11-02 | `6cc2323` | Lsu/debug: remove RealLsuPerf, all dump_debug functions, the deadlock/diff trace infra and the TLB trace ring |
| 2026-11-02 | `0564418` | Lsu: remove the dead load/store value computations (STLF forward data, dcache load data, store-port data) and helpers |
| 2026-11-02 | `2d60f6b` | Memory subsystem: remove the dead line-data chain (store data, MSHR merged store data, fill/victim line data, write-buffer data and AXI write data) |
| 2026-11-02 | `4612b36` | Memory: instruction words and page-table entries are read from the core's memory; commit-time pmem writes and the LLC/MemSubsystem read-data payload are gone |
| 2026-11-02 | `fcde828` | ICache: no line words in the module or the AXI response; the glue reads the fetch group from the core's memory by physical address |
| 2026-11-02 | `b74a841` | pmem RAM is the core's RAM: one copy, the loader and DMA write straight into it; no unused difftest reference core in RUN mode |
| 2026-11-02 | `7842d97` | Remove the remaining functional-memory leftovers: SimDDR read/write memory, the DDR functional-write flag, the PeripheralModel/MemSubsystem RAM pointer; AXI read payload… |
| 2026-11-02 | `54d736c` | MemSubsystem: remove the unused internal AXI runtime (interconnect/DDR/router/MMIO/UART copies) |
| 2026-11-02 | `c8202b2` | AXI kit pointer: debug/perf strip |
| 2026-11-02 | `7159e64` | Update kit: AXI/LLC line-data removal |
| 2026-11-02 | `a3c7bb5` | Kit pointer: dead function deletion |
| 2026-11-02 | `0d0daeb` | Kit pointer: block emptying |
| 2026-11-02 | `8a6d78e` | Kit pointer: orphan function deletion |
| 2026-11-02 | `395c944` | Kit pointer: coverage-driven pruning done |
| 2026-11-02 | `ac1697d` | BPU: compact rewrite (TAGE/BTB/type predictor/history/RAS/queue), 4.7k -> 0.76k lines, cycle-exact |
| 2026-11-02 | `7b03801` | Lsu: compact rewrite (generic ring queues, merged phases), 1.6k -> 0.97k lines, cycle-exact; lockstep shadow hook |
| 2026-11-02 | `56db2bb` | Rob: dirty-slot sync instead of whole-array copies |
| 2026-11-02 | `907276b` | IssueQueue: maintain ready bitmap in seq |
| 2026-11-02 | `bd0ca81` | LLC table_out reset without allocator, drop zero data row |
| 2026-11-02 | `3de4d3a` | comb_begin: drop redundant working-copy copies (checked by BEGIN_SELFCHECK) |
| 2026-11-02 | `0fdb4ad` | Kit pointer: revert block emptying |
| 2026-11-03 | `9f27ae8` | back-end tidy: drop identity Uop converters and stage-specific Uop aliases |
| 2026-11-03 | `5f5948f` | BackTop::comb split into documented dependency stages |
| 2026-11-03 | `8a18a33` | back-end: Wires struct replaces per-module in/out pointer wiring |
| 2026-11-03 | `c70d962` | Rob: rewrite (761 -> 364 lines), lockstep-verified; ROB_SHADOW build hook |
| 2026-11-03 | `604fdde` | Dispatch: rewrite (712 -> 372 lines), table-driven decomposition, lockstep-verified; DIS_SHADOW hook |
| 2026-11-03 | `30961ac` | Exu: rewrite (577 -> 306 lines), lockstep-verified; EXU_SHADOW hook |
| 2026-11-03 | `be0aff5` | Isu: rewrite (525 -> 247 lines), lockstep-verified; ISU_SHADOW hook |
| 2026-11-03 | `24ab6e3` | Idu: rewrite (505 -> 302 lines), lockstep-verified; IDU_SHADOW hook |
| 2026-11-03 | `03c7bb4` | Ren: rewrite (400 -> 220 lines), lockstep-verified; REN_SHADOW hook |
| 2026-11-03 | `5705496` | Csr: rewrite (420 -> 222 lines), lockstep + random differential verified; CSR_SHADOW hook |
| 2026-11-03 | `1fd7461` | PreIduQueue: rewrite (351 -> 245 lines), lockstep + random differential verified; PRE_SHADOW hook |
| 2026-11-03 | `78189ec` | BackTop: split loaders/checkpoint into BackTopLoad.cpp, shadow hooks into ShadowHooks.h, dedupe state install, extract comb_outputs (850 -> 366 + 422 lines) |
| 2026-11-03 | `53de287` | Update axi-interconnect-kit: LLC rewrite |
| 2026-11-03 | `1cf984d` | Update axi-interconnect-kit (interconnect tidy); drop the dead read_req_drop_warned snapshot |
| 2026-11-03 | `d0d746e` | front-end: ring-buffer FIFO models, no CombIn copies, in-place read data, drop write-only deadlock snapshot and out_regs |
| 2026-11-03 | `b8550c0` | SimCpu: skip copying the all-zero front2back hold register |
| 2026-11-03 | `901b3eb` | Ren: copy only the RAT checkpoint rows written this cycle |
| 2026-11-03 | `76ee03b` | IssueQueue: skip the grant clear and scheduling when nothing is ready |
| 2026-11-03 | `53b38ce` | Isu: write enqueue slots in place instead of zeroing them every cycle |
| 2026-11-03 | `5b64663` | front_comb_calc: split the 560-line function into stages (FrontComb), drop the dead bypass/second-slot paths and the IO wrapper structs |
| 2026-11-03 | `5c22d19` | rv_simu_mmu_v2: dedupe the AXI bridges, drop the idle-verify scaffolding, empty counters and commented-out code (1020 -> 841 lines) |
| 2026-11-03 | `af95139` | Update axi-interconnect-kit (LLC comb memo, quiescence shortcut, read/write arbiter split) |
| 2026-11-03 | `b23dfd1` | Vendor axi-interconnect-kit (382cb6f) and GenSimpoint (637537f) as plain directories |
| 2026-11-03 | `e53cd45` | Import tests, scripts, docs and gate baseline from tututugege-trace; add docs/PROJECT.md |
| 2026-11-03 | `9ff02eb` | GenSimpoint is now the AI-Huma function-model repository (submodule) |
| 2026-11-03 | `502fa18` | docs: AI-Huma layout (function-model, trace-model, rtl) |

### function-model / `main`（上游 tututugege/GenSimpoint fee6fdb 之后）

共 2 个 commit。

| 日期 | commit | 做了什么 |
|---|---|---|
| 2026-11-02 | `637537f` | refcpu API: side-effect-free virtual-to-physical probe for fetch/load/store (used by the trace bridge) |
| 2026-11-03 | `354664a` | macOS SoftFloat build; ignore build products |

### rtl（`~/personal/tututugege-rtl`）/ `main`

共 67 个 commit，含各模块分支的合并。

| 日期 | commit | 做了什么 |
|---|---|---|
| 2026-11-03 | `abf7b1b` | Initial: docs (scope, RTL standard, flow, harness, mapping, tracker), trace-replay harness, svlint, cfg_pkg generator, selftest |
| 2026-11-03 | `d339482` | Recording pipeline (refsim hook + spec @expr plugins), structure rules S10-S12, common primitives, strong RTL design principles |
| 2026-11-03 | `d885e34` | docs: agent brief for per-module translation |
| 2026-11-03 | `6faeb5a` | rtl/backend: prf (green: 67 traces, mutants: 15/15) |
| 2026-11-03 | `2123c51` | hbuild: raise verilator replication limit for wide wrapper outputs |
| 2026-11-03 | `b6b6a2f` | rtl/backend: idu (green: 72 traces, mutants: 12/12) |
| 2026-11-03 | `6145c80` | iogen: tbwrap drives out_bits per element (no wide clear), review/mutcheck coordinator scripts; drop replication-limit workaround |
| 2026-11-03 | `79704a1` | rtl/backend: ren (green: 64 traces, mutants: 7/7 effective; 4 survive on uncovered paths) |
| 2026-11-03 | `c32b1a1` | docs: equivalence policy (don't mimic C++ quirks), hash excludes compare rules, package-first file ordering |
| 2026-11-03 | `a325cf9` | rtl/backend: dispatch (green: 64 traces, mutants: 14/14) |
| 2026-11-03 | `13bc3f8` | scripts: rehash trace headers after hash definition change |
| 2026-11-03 | `bc0c632` | merge main |
| 2026-11-03 | `ebd3931` | merge main |
| 2026-11-03 | `8d7e17c` | merge main |
| 2026-11-03 | `9d8c78c` | Merge branch 'main' into rtl/dispatch |
| 2026-11-03 | `f602a9b` | rtl/backend: idu simplified per 06 (green: 72 traces, mutants: 9/9) |
| 2026-11-03 | `329ee8d` | rtl/backend: prf simplified per 06 (green: 67 traces, mutants: 10/10) |
| 2026-11-03 | `44de394` | rtl/backend: dispatch simplified per 06 (green: 66 traces incl. 3 random, mutants: 16/17 valid, M9 equivalent) |
| 2026-11-03 | `7417760` | rtl/backend: ren simplified per 06 (green: 68 traces incl. 4 random, mutants: 12/12) |
| 2026-11-03 | `aaa773d` | dispatch notes: fix trace size |
| 2026-11-03 | `b84eca5` | rtl/backend: rob (green: 69 traces, mutants: 10/11) |
| 2026-11-03 | `2b4145a` | scripts: standard program set now includes vm tests and extra baremetal programs; caps from progs.txt |
| 2026-11-03 | `d7cc418` | scripts: smaller caps for extra programs, SKIP_EXISTING |
| 2026-11-03 | `c4402f1` | merge main (program set update) |
| 2026-11-03 | `8e4ca0c` | merge main (program set update) |
| 2026-11-03 | `5ae45da` | merge main (program set update) |
| 2026-11-03 | `3121a8b` | merge main (program set update) |
| 2026-11-03 | `4b788bb` | untrack .DS_Store |
| 2026-11-03 | `909e469` | merge main |
| 2026-11-03 | `62fefd6` | merge main |
| 2026-11-03 | `2c375e6` | merge main (program set update) |
| 2026-11-03 | `1754f49` | merge main |
| 2026-11-03 | `e8216be` | merge main |
| 2026-11-03 | `2d5be44` | docs: brief supplement for batch 2; svlint comparison fix; lint exemption rules |
| 2026-11-03 | `496b699` | rtl/backend: csr (green: 77 traces, mutants: 15/15) |
| 2026-11-03 | `ab197ea` | harness: when may reference an input field; lint exemption doc fix |
| 2026-11-03 | `26d3290` | rtl/backend: pre_idu_queue (green: 77 traces, mutants: 18/18) |
| 2026-11-03 | `43a0f6a` | rtl/backend: isu (green: 77 traces, mutants: 16/16 + 1 equivalent) |
| 2026-11-03 | `85dc87f` | Merge rtl/prf: prf translated to SV (green, reviewed) |
| 2026-11-03 | `321dc35` | Merge rtl/idu: idu translated to SV (green, reviewed) |
| 2026-11-03 | `eb1ba57` | Merge rtl/ren: ren translated to SV (green, reviewed) |
| 2026-11-03 | `a1c1664` | Merge rtl/dispatch: dispatch translated to SV (green, reviewed) |
| 2026-11-03 | `19b0168` | Merge rtl/rob: rob translated to SV (green, reviewed) |
| 2026-11-03 | `e6ad69a` | Merge rtl/csr: csr translated to SV (green, reviewed) |
| 2026-11-03 | `a7fa41b` | Merge rtl/pre_idu_queue: pre_idu_queue translated to SV (green, reviewed) |
| 2026-11-03 | `740fe6a` | Merge rtl/isu: isu translated to SV (green, reviewed) |
| 2026-11-03 | `28046d5` | docs: tracker (8 backend modules green), suspect list, hidden-dependency table, assertion rule; merge script |
| 2026-11-03 | `12a2669` | analysis: frontend/Exu module boundaries, front record tap patch, coverage data |
| 2026-11-03 | `668f3b2` | Merge rtl/ana: frontend and Exu boundary analysis |
| 2026-11-03 | `9fc9632` | refhook: front-end recording tap (from analysis), REFSIM_DIR override |
| 2026-11-03 | `9be57f1` | svlint: generated files exempt from size limits |
| 2026-11-03 | `97440a9` | rtl/backend: tlb_mmu (green: 79 traces, mutants: 34/34) |
| 2026-11-03 | `5354ec1` | lint.sh: lint per module directory (linear cost) instead of per file against the whole repo |
| 2026-11-03 | `4af361e` | rtl/frontend: front_basic (green: 8 modules x 73 programs + generated traces, mutants: 34/34) |
| 2026-11-03 | `483129b` | rtl/backend: exu_int FUs (alu bru agu sdu csr_fu mul div) (green: 7 specs ~76 traces each, mutants: 47/47) |
| 2026-11-03 | `6e0f83c` | rtl/backend: fpu (green: 81 traces, mutants: 33/33 non-equivalent) |
| 2026-11-03 | `5dc008c` | Merge rtl/tlb_mmu: tlb_mmu translated to SV (green, reviewed) |
| 2026-11-03 | `3537ca4` | Merge rtl/fpu: fpu translated to SV (green, reviewed) |
| 2026-11-03 | `592b44d` | Merge rtl/front_basic: front_basic translated to SV (green, reviewed) |
| 2026-11-03 | `29248af` | Merge rtl/exu_int: exu_int translated to SV (green, reviewed) |
| 2026-11-03 | `e3c5fe7` | docs: tracker (TlbMmu, FU, FPU, front basics merged), suspects S-12..S-21; record_all keeps generated traces; review scripts |
| 2026-11-03 | `6d64313` | rtl/backend: exu_ctrl (green: 77 traces, mutants: 11/11) |
| 2026-11-03 | `78693ea` | harness: live lock-step co-simulation (RTL plugin in the reference simulator, whole-program comparison) |
| 2026-11-03 | `84fd4f2` | Merge rtl/exu_ctrl: exu_ctrl translated to SV (green, reviewed) |
| 2026-11-03 | `9cb3db2` | rtl/backend: lsu (green: 85 traces, mutants: 15/25 caught) |
| 2026-11-03 | `06fea7d` | scripts: lockstep_batch |
| 2026-11-03 | `d3e825f` | Merge rtl/lsu: lsu translated to SV (green, reviewed) |


说明：trace-model 早期的补丁队列（patches 0001–0061）记在旧仓库 `~/personal/tututugege-trace` 的 `docs/` 里。
| 2026-11-12 | 总仓库 `main` | 本行所在提交 | 四个仓库文档整理后更新子模块指针：function-model `d129f0e`、trace-model、rtl `543f817`（各仓库 README / 入口文档重写、rv64 与紧凑 ROB 的模块文档补注、已删宏与环境变量清理、链接检查）；顺手改 3 处过时注释（`agu.sv`、`llc_small_check.sh`、`BPU_pipe.h`） | 各仓库 lint / 编译不受影响（仅文档与注释） | 已推送 |
| 2026-11-12 | trace-model `main` | 见总仓库提交 | 删除 `baremetal/x0-bypass-test`（`host-test` 引用已删的 `RealLsuPerf.cpp` 和不存在的 `LsuState` 成员，早已不能构建；需要时从 git 历史恢复）；README 同步 | 仅删除 | 已推送 |
| 2026-11-12 | function-model `main` | 见总仓库提交 | 提交非 SPEC 负载流水线 `scripts/wl/`（`mk_wl.sh`、`run_bbv.sh`、`pipeline.sh`）并补 README（EXP-022 的 GAP / PolyBench / Ligra 数据用它，只支持 rv32imab）；删除 9 个空的 `ol_*` 目录、失败状态文件 `ol_voronoi.txt` 和指向自身的 `function-model` 软链接；EXPLORATION EXP-026 一节加指向 | 仅文档和脚本入库，脚本没有重跑 | 已推送 |
| 2026-11-12 | rtl `main` / 总仓库 | 见总仓库提交 | EXP-029 rv64 综合代理对比：24 个模块在 `XLEN_BITS=32` / `64` 下各跑 yosys 通用门面积 + 深度代理，写进 `rtl/docs/09-synthesis-report.md` 第 10 节和 MAIN_RECORDS；`synth_depth.sh` 修 macOS xargs 命令行过长 | 18 个互不重叠模块合计 +31% 单元；`dcache_bank` rv64 超内存未出数；仍无工艺库 / 时序 | 已推送 |
| 2026-11-12 | 总仓库 `main` | 本行所在提交 | TODO 新增「乘除法器的物理实现优化」：乘法器目前单周期纯组合（`a * b`，`mul_pipe` 只是结果延迟线）、除法器每周期两级 64 位减法；计划乘法器真流水化（Booth + 压缩树）、面积优化、除法器 radix-4 / SRT 与延迟评估 | 仅文档 | 已推送 |
| 2026-11-12 | 四个仓库 `main` | function-model `607229e`、trace-model `4cf9b6b`、rtl `3ca4677`、总仓库 | **推送本轮**：EXP-029 rv64 合入、死宏与环境变量清理、`ENV_VARS.md`、四仓库文档整理、非 SPEC 流水线入库、rv64 综合代理对比、乘除法器 TODO；全部为 fast-forward，先推三个子模块再推总仓库 | 推送前各 `main` 与指针一致、均领先 `origin/main`、落后 0 | 已推送 |
| 2026-11-12 | function-model `exp/fd` / 总仓库 | function-model `a5674d9`、总仓库本行所在提交 | **EXP-030 rv64 F/D 第一步（function-model）**：`FP=1` 编译开关（浮点寄存器堆、fcsr、mstatus.FS/SD、OP-FP、融合乘加、flw/fld/fsw/fsd、检查点版本 5、前门恢复），Spike 逐条对拍：约 35 万条指令的定向测试、FS/保留编码测试、编译器生成的浮点代码全部一致；顺带修 `csrrwi csr,0` 不写 CSR 的老 bug。未合入 main，trace-model / RTL 未开始 |
| 2026-11-12 | function-model `main` / 总仓库 | function-model `e0078bc`、总仓库本行所在提交 | **EXP-030 function-model 合入 main**（快进，未推送）：`FP=1` F/D、官方 rv64uf/ud 23/23；MAIN_RECORDS 加一行，总仓库子模块指针更新 |
| 2026-11-12 | trace-model `exp/fd` / function-model `exp/fd-tm` / 总仓库 | trace-model `2c1d166`、function-model `cdcb74d`、总仓库本行所在提交 | **EXP-030 trace-model 的 F/D（`FP=1`）第一版**：FP 重命名、FP 发射队列和三个 FP 发射口、FMA/MISC/FDIV/I2F 单元、FP load/store 走现有 LSU、按事实产生非法指令、mstatus.FS/SD、bridge/检查点 v5；`FP=0` gate 62/62 与 rv64 整数程序周期不变，26 个 FP 程序（含官方 rv64uf/ud）跑到结束，微基准延迟符合配置。未合入、未推送 |
| 2026-11-12 | function-model `main` / trace-model `main` / 总仓库 | function-model `cdcb74d`、trace-model `2c1d166`、总仓库本行所在提交 | **EXP-030 合入 main**（两个子模块都是快进，未推送）：trace-model `FP=1` 第一版；大程序周期不变（dhrystone 116,774、coremark 284,902、memory-stress-small 325,458）；MAIN_RECORDS 加一行，子模块指针更新 |
| 2026-11-12 | function-model / trace-model / rtl 的分支 / 总仓库 | function-model `exp/fd-all` `eca7c83`、trace-model `exp/fd-all` `8017ffb`、rtl `exp/no-zfinx` `3ff0253`、总仓库本行所在提交 | **EXP-031 删除 Zfinx，rv32 也改用标准 F/D**：function-model 的 rv32 F/D、trace-model 的 F/D 默认开启并删除 Zfinx（Zfinx 测试换成 `fd-*`，基线更新）、RTL 删除 Zfinx 的 FPU；rv32 gate 64/64、RTL soc_smoke 56/56、dhrystone/coremark 与模型逐周期相同。三个分支未合入 |
| 2026-11-13 | function-model / trace-model / rtl `main` / 总仓库 | function-model `0323bd9`、trace-model `195dad4`、rtl `15af4b4`、总仓库本行所在提交 | **EXP-031…036 合入 main 并推送**（三个子模块都是快进）：Zfinx 删除与 rv32/rv64 标准 F/D、EXP-032/033 FP 写口与 fcsr、EXP-034 Exu 重写、EXP-035 写回口预约（模型 + RTL `isu_wb_gate`）、EXP-036 仿真提速约 24%、RTL 标准 F/D S1–S6；rv64g Linux 在 RTL 上从复位到登录，`fptest: PASS`，171,931,468 条指令逐条对比 0 不一致。记录见 EXPLORATION.md、MAIN_RECORDS.md。Linux 中段检查点（会话临时目录）已丢失，可重生成 |
| 2026-11-13 | function-model `exp/rvc` / 总仓库 | function-model 见分支（未合入）、总仓库本行所在提交 | **EXP-037 C 扩展（function-model）**：`RVC=1` 开关（rv32/rv64），取指按半字、16 位指令展开、`ilen`、跨页第二半字缺页、`misa.C`、`medeleg[0]`；定向测试（全部 16 位编码、访存、跳转、跨行跨页、Sv39 缺页）、`rv*uc`、cpu-tests 带 C、带 C 的 rv64 Linux 前 2.5 亿条指令与 Spike 逐条一致；`RVC=0` 回归不变。快速路径暂不处理压缩指令。未合入、未推送 |
| 2026-11-13 | function-model `main` / 总仓库 | function-model `6bf6c59`、总仓库本行所在提交 | **EXP-037 合入 main 并推送**（快进）：`exp/rvc` + `exp/rvc-fast`；`RVC=0` 回归（rv32 / rv64 Spike 对拍、快速路径摘要）不变；MAIN_RECORDS 加一行，EXPLORATION 状态更新 |
| 2026-11-13 | trace-model `exp/rvc` / 总仓库 | trace-model `4db3277`（未合入）、总仓库本行所在提交 | **EXP-038 C 扩展（trace-model）S0**：后端和 bridge 的指令长度通路（`is_rvc` 位、`pc+ilen`、`Bridge::dispatch` 带长度），`RVC` 开关默认 0，周期不变（gate 64/64）；方案参考香山和 BOOM：2 字节预测位置、跨界指令归起始块（`lastHalf`）、按指令的取指缓冲。S1–S5 未开始 |
| 2026-11-13 | trace-model `exp/rvc` / 总仓库 | trace-model S1 提交（未合入）、总仓库本行所在提交 | **EXP-038 S1**：取指几何按 slot 宽度参数化（`FETCH_BYTES` / `SLOT_SHIFT` / `SLOT_BYTES`，BPU 的索引和 slot↔pc 换算、I$ 每行 slot 数和半字对齐取指窗口），`RVC=0` 周期不变（gate 64/64），`RVC=1` 能编译（16 个 2 字节 slot）但还不能运行；`RVC=1` 能运行移到 S2（前端多处假定有效 slot 是连续前缀，要和预译码边界一起改） |
| 2026-11-13 | trace-model `exp/rvc` / function-model `main` / 总仓库 | trace-model `5bd7a75`（未合入）、function-model `c602794`（本地，未推送）、总仓库本行所在提交 | **EXP-038 S2**：`RVC=1` 的前端能运行：预译码展开和起点链、`lastHalf`、有 slot 空洞的有效位、`is_rvc` 到后端；`RVC=0` 不变（gate 64/64）；`RVC=1` 不带 C 的程序 0 不一致（周期约 ±5%）、cpu-tests 带 C 58/62（4 个是 4 字节假定的测试源码）、`gen_rvc.py` 的全部定向测试 0 不一致；`rvc.h` 改成沿用编译开关的 XLEN / FP（function-model main 本地提交） |
| 2026-11-13 | trace-model `exp/rvc` / 总仓库 | trace-model 见分支（未合入）、总仓库本行所在提交 | **EXP-038 变慢的程序**：BPU 训练和 RAS 路径的 `pc+4` 改成按指令长度（uBTB 块跟踪器、架构 / 推测 RAS、误预测修复、类型预测器和 uBTB 项记 call 的长度），块尾跨界指令时跟踪器的块起点取块尾；C 编译 + `RVC=1` 对 不带 C + `RVC=0` 的周期几何平均 0.975 → 0.920，`itt-dispatch` / `recursion` 不再慢；`RVC=0` 不变（gate 64/64），5 个定向压力测试 0 不一致 |
| 2026-11-13 | function-model / trace-model `main` / 总仓库 | function-model `c602794`、trace-model `74e6827`、总仓库本行所在提交 | **EXP-038 S0–S2 合入 main 并推送**（快进）：trace-model `exp/rvc` + function-model 的 `rvc.h` 小改动；`RVC=1` 测试流程进仓库（`scripts/build_rvc_tests.sh`、`scripts/run_gate_c.sh`、`baseline_c.csv` 62/62），4 个假定 4 字节指令的测试源码加了 `.option norvc`；`RVC=0` gate 64/64 不变 |
