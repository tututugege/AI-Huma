# PMU：性能监控单元（EXP-013，已合入 main 2026-11-07）

分两层，共用一张事件表：

| 层 | 放在哪 | 能做什么 | 不能做什么 |
|---|---|---|---|
| **硬件 PMU** | rtl `rtl/pmu/`（计数器块 + HPM CSR），事件由核内已有信号产生 | 每个事件是“某个信号每拍加几”；64 位计数器；软件能读；顶层 TMA 一、二级只靠这些计数器就能算 | 看不到“是哪条指令”；计数器个数有限（8 个可编程 + cycle/instret） |
| **trace-model 分析层** | trace-model `back-end/Pmu*.cpp`、`scripts/pmu/pmu_report.py` | 同样的计数器（全部同时计）+ 谁堵住了提交的逐 PC 画像、直方图（每拍提交数、ROB/LDQ/STQ 占用、未完成缺失数）、按时间的相位曲线 | 不是硬件，不能随 RTL 上芯片 |

事件表 [trace-model `include/pmu_events.def`](../trace-model/include/pmu_events.def) 是**唯一来源**：trace-model 的事件向量、RTL 的 `pmu_ev_pkg.sv`（`rtl/scripts/gen_pmu_pkg.py` 生成）、分析脚本都读它，事件号在三处含义相同。

## 1. 事件与 TMA

槽位 = dispatch 级的 `DECODE_WIDTH`（8）个槽，每拍每个槽恰好落进一个桶（每拍 `PMU=1` 检查这个恒等式，违反次数打印在报告里）：

```
slots = SLOT_FIRE + SLOT_KILLED + SLOT_FE_EMPTY + SLOT_BE   （SLOT_BE = 下面各 SLOT_BE_* 原因之和）
```

- 派发出去的（FIRE）：最终提交的是 Retiring（`INSTRET`），没提交的是 Bad Speculation 里的“错误路径工作”（`FIRE − INSTRET`）。
- 本拍被冲刷/误预测杀掉的有效槽（KILLED），以及重定向之后到第一条指令到达 dispatch 之前的空槽（`FE_RECOV_MISPRED/FLUSH`）也算 Bad Speculation。
- 其余空槽是 Frontend Bound：ICache 缺失 / ITLB 缺失（取指延迟），其余（取指宽度、taken 分支气泡）是取指带宽。
- 第一个被后端拒绝的槽起，该拍所有剩下的槽都是 Backend Bound（和 Intel 的做法一样），原因取第一个挡住它的资源：ROB 满 / ROB 头是冲刷类指令 / CSR-AMO 串行化 / LDQ 满 / STQ 满 / IQ 满。（重命名没有空闲物理寄存器时，指令到不了 dispatch，槽记为前端空槽。）
- Backend Bound 另有“看 ROB 头”的第二种切法（`SLOT_BE_HEAD_*`）：最老未完成指令是 L1D 缺失的访存、普通访存、非访存，或者头已完成（提交带宽 / ROB 行粒度限制）。访存 = Memory Bound，其余 = Core Bound。

事件分组（完整列表和含义见 .def）：`cyc`/`commit`（INSTRET、按类型提交数、已提交的误预测按 BR/JALR/RET 分）、`slot`（上面的桶）、`flow`（误预测重定向、冲刷分类、恢复中的周期、mov 消除）、`front`（ICache/ITLB）、`mem`（L1D 命中/缺失、未完成缺失数用于 MLP、预取）、`occ`（ROB/LDQ/STQ 占用逐拍累加，平均占用 = 事件/周期）。

## 2. 硬件 PMU（rtl `rtl/pmu/pmu.sv`）

```
事件总线 ev_inc[52][8] ──► mcycle  ┐  +ev[CYCLES]
                          minstret │  +ev[INSTRET]
                          HPM 3..10│  各自 mhpmevent 选一路（52:1 × 8 位）+ 64 位加法器
CSR 口 (addr, wen, wdata, prv) ◄──►  mcountinhibit / mcounteren / mhpmeventN / 计数器高低半 / user 影子
```

- 总线：每个事件一条 `PMU_INC_W`（8）位的通道，值 = 这拍的增量；事件号 = 通道号；`mhpmevent[7:0] = 事件号 + 1`（0 = 不计数，RISC-V 惯例）。
- 标准 CSR 地址：`mcycle/minstret/mhpmcounter3..10`（0xB00/B02/B03..，高半 0xB80..）、`mhpmevent3..10`（0x323..）、`mcountinhibit`（0x320，位 0 CY、位 2 IR、位 3+k HPM k）、`mcounteren`（0x306）、user 只读影子 `cycle/instret/hpmcounter`（0xC00..，非 M 态由 mcounteren 放行）。写和同拍增量冲突时写赢；写 mcountinhibit 之后计数立刻停。
- 没有溢出中断（64 位，用不着）。没有 `time`。
- 面积：每个 HPM 约 64 个触发器 + 8 个事件选择位 + 一个 52:1 的 8 位选择器 + 64 位加法器；整个 PMU（8 个 HPM）约 750 个触发器。**还没综合**，数字是估计。
- 验证：`tests/pmu/run.sh`——对 C++ 模型做 30 万拍随机（随机事件增量、随机 CSR 读写、M/非 M 特权、跨 32 位进位），逐拍比较 hit/illegal/rdata，最后比较全部计数器；`PMU_TB_MUTATE=1` 故意改坏模型，必须报错（已确认能抓到）。lint 干净。

### 状态

`pmu` 计数器块完整、测过；tier 1 事件总线已接进 `core_top`（第 4 节）；**计数器块还没接到 CSR 单元**，所以软件读不到计数值，目前只有测试平台能读事件总线做对齐。

## 3. trace-model 分析层

```bash
PMU=1 build/simulator prog.bin                      # 打印计数器表 + TMA + 衍生指标（MPKI、MLP、占用……）
PMU=1 PMU_OUT=out/dhry PMU_INTERVAL=5000 build/simulator prog.bin   # 另写 4 个 CSV，每 5000 拍一行相位曲线
python3 scripts/pmu/pmu_report.py out/dhry --elf prog.elf           # 谁堵住了提交 / 误预测热点 / 相位
```

- 默认关（`PMU` 未设置）：不采样、不打印；开关与否周期数逐个相同（见第 5 节）。检查点模式只统计测量窗口（预热结束或前门恢复的 mret 处清零）。
- 输出：`<prefix>_events.csv`（全部计数）、`_hist.csv`（直方图）、`_pc.csv`（逐 PC：提交数、做最老未完成指令的周期数、其中等 L1D 缺失的周期数、因它丢掉的 dispatch 槽数、误预测数）、`_series.csv`（区间增量）。
- `pmu_report.py` 把逐 PC 汇总成：堵塞最多的指令（带符号）、按指令类型、按代码页、误预测热点（前 1/5/20 条分支占多少）、相位表、直方图。
- 与旧的 TMA（2026-11-02 随统计套件删除，在 `488efe8^`）的区别：旧版逐项重复计数且口径随便（例如 IQ 是兜底桶）；新版恒等式严格成立、每个事件都是“一个信号每拍加几”、可以原样搬进 RTL。

## 4. RTL 接线：只做简单的一档（tier 1）

分工：**RTL 只做硬件简单、不用大改端口的事件，TMA 一级必须有；二级能顺手就做；“哪个队列满 / 谁堵住 / 逐 PC”这类细粒度只在 trace-model。**

RTL tier 1（`rtl/pmu/pmu_ev_core.sv`，`core_top` 里实例化，事件总线 `pmu_ev_inc` 给测试平台读）共 18 个事件，名单写在 `pmu_events.def` 开头：

| 组 | 事件 | 信号来源 |
|---|---|---|
| 周期/提交 | CYCLES、INSTRET、COMMIT_LOAD/STORE/BRANCH/JUMP、CYC_COMMIT_ZERO/FULL | 提交口的 valid + type（`rob_commit_*`），中断拍不算（新增 `rob_bcast_interrupt` 输出口）；AMO 同时算 load 和 store |
| 重定向 | BR_MISPRED、FLUSH_EXCEPTION、FLUSH_OTHER | `out_mispred`（冲刷也会拉高，所以 BR_MISPRED = redirect 且非 flush）、`rob_bcast_flush/exception` |
| **TMA 一级** | SLOT_FIRE、SLOT_KILLED、SLOT_FE_EMPTY、SLOT_FE_RECOV_MISPRED/FLUSH、SLOT_BE、CYC_RECOVERING | dispatch 新增输出 `slot_valid`（阶段寄存器里每槽是否有指令），`back_top` 导出 `dis2rob_dis_fire`；恢复状态是 2 个触发器 |

一级公式（全部由这些计数器算出）：Retiring = INSTRET；Bad Speculation = (FIRE − INSTRET) + KILLED + RECOV_*；Frontend = FE_EMPTY − RECOV_*；Backend = SLOT_BE；总槽 = 8 × CYCLES。其中 `SLOT_BE`（后端拒绝的槽，从第一个没发射的有效槽起到最后）在 RTL 里只有总数，trace-model 里拆成 ROB 满 / IQ 满 / LDQ / STQ / 冲刷等待 / 串行化，并且这些子项的和等于 `SLOT_BE`。

**二级只拿现成的**：Bad Speculation 里“误预测恢复 vs 冲刷恢复”是免费的（上表）。需要 ICache/ITLB（取指延迟 vs 带宽）、ROB 头状态（Memory vs Core）、LSU 队列状态的二级拆分，要给 icache/rob/lsu 加输出端口，**暂不做，只在 trace-model**（`SLOT_FE_ICACHE`、`SLOT_BE_HEAD_*` 等）。其余 trace-model 独有的事件（前端、访存、占用、按类型的误预测）同理。

趁手可补的二级（需要新端口，以后按需）：ROB 满（`rob2dis_ready` 已进 dispatch）、冲刷等待（`rob2dis_stall`）。

验收：`scripts/pmu_parity.sh <prog.bin>` 跑 RTL SoC 测试平台（`SOC_TB_PMU=1`，在测试平台里对总线逐拍累加）和 trace-model `PMU=1`，**tier 1 的 18 个事件总数必须逐个相等**。

### 软件可见性：一个要先决定的约定

现在 function-model、trace-model IDU、RTL CSR 都把 `mcycle/minstret/mhpm*/mcountinhibit/mcounteren` **当作不存在**（访问 → 非法指令，OpenSBI 靠这个探测并关闭相关功能，见 `Idu.cpp` 里 `is_known_csr` 的注释）。让软件读到计数器 = 改 ISA 约定：

1. function-model 要实现这些 CSR（计数值与周期有关，function-model 没有周期）→ 逐条对比对这些 CSR 读要用 RTL 值覆盖（Spike 那边已有 `force_sync` 类似机制）。
2. OpenSBI/Linux 探测到计数器后行为会变（可能打开 perf 相关路径），Linux 13 段重新跑。
3. trace-model IDU 的 `is_known_csr` 加这些地址。

建议先**不做**软件可见：用测试平台直接读总线做 RTL 对齐（第 4 节验收），软件可见作为单独一步（需要你决定要不要改这个约定）。

## 5. 已验证

| 项 | 结果 |
|---|---|
| 关闭时周期不变 | dhrystone 161,183、coremark 251,535、mcf 检查点 sp0（10M+10M）27,764,655 周期，与 main 的 `build/simulator` 逐个相同；`PMU=1` 时也相同（计数只读信号；mcf 点 `PMU=1` 慢约 2%）。合入前在提交后的代码上复验：trace-model gate 63/63（PMU 关、开）、RTL fm_gate 67/67（预取开、关）、Linux 13 段 13/13、lint 0 警告（见 MAIN_RECORDS）；没跑 SPEC 全量 |
| 恒等式 | dhrystone、coremark、mcf 检查点（10M+10M）：违反 0 次；`INSTRET` 等于 `commit_num`（检查点模式停在拍中间，最多多计 COMMIT_WIDTH−1 条） |
| 顺带发现的缺陷 | `RealLsu::load_miss_mask` 用 `uint64_t` 掩码和 `1ULL << rob_idx`，ROB 有 128 项：rob_idx ≥ 64 的缺失标记丢失/移位越界。它只喂旧的 TMA 元数据（不影响周期），已改成 `bitset<ROB_NUM>` |
| RTL 计数器块 | 30 万拍随机对模型，0 不一致；变异检查有效；lint 干净 |

## 6. 已知口径与限制

- `DC_LD_HIT/MISS`、`PF_*` 目前取自 L1D 的模型内统计结构（`g_pf_stats`，每拍取差值），RTL 对应要用同一个 stage-2 条件；只统计 LSU 的首次（非重放）访问。
- 恢复（recovery）气泡用“重定向 → 第一条有效指令到达 dispatch”近似，没有区分取指流水线的深度。
- `ICACHE`/`ITLB` 归因是看空槽出现这拍前端有没有在处理缺失，缺失发生得早、队列还有存货时会把一部分延迟记到“其它”。
- 没有 L2/LLC/DRAM 级的计数（trace-model 里 LLC 和 DDR 的事件还没引出）；Memory Bound 目前只分到 L1D 缺失 / 其它。
- 逐 PC 画像把等待记在“最老未完成指令”身上，不做关键路径分析；多条指令并行等待时只算最老那条。

## 7. SPEC 的 TMA（每个程序权重最高的 SimPoint，10M 预热 + 10M 测量，trace-model，2026-11-07）

`trace-model-pmu/scripts/pmu/spec_tma.sh <outdir>` 跑、`spec_summary.py <outdir>` 出表；原始 CSV 在 `~/personal/AI-Huma-data/pmu_spec/`。每个程序一个点，只看“瓶颈是什么”，不是该程序的整体数字；12 个点槽位恒等式违反都是 0。

```
benchmark          IPC |   Ret BadSp    FE    BE | mispr wrong |  fLat   fBW |   Mem   L1m  Core |   ROB    IQ   LSQ | brMPKI L1dMPKI iMPKI  MLP
400.perlbench     3.13 |  39.1  19.3  18.0  23.6 |   8.9   9.1 |   0.2  17.8 |   6.8   0.0  16.7 |  23.1   0.0   0.0 |    3.1     0.1  0.10  1.5
401.bzip2         3.76 |  47.1   1.3   5.8  45.9 |   0.5   0.4 |   0.0   5.8 |  18.9   8.5  27.0 |  45.3   0.0   0.1 |    0.2    21.8  0.02  2.6
403.gcc           1.46 |  18.3   1.7  32.9  47.1 |   0.8   0.4 |   1.0  31.9 |  22.9   0.9  24.2 |   1.7   0.0  45.0 |    0.7     1.4  0.73  2.0
429.mcf           0.35 |   4.3  17.0   4.8  73.8 |   6.6   9.3 |   0.0   4.8 |  66.7  35.4   7.1 |  73.3   0.0   0.0 |   24.7   225.8  0.14  4.6
445.gobmk         1.63 |  20.3  35.0  35.1   9.6 |  21.9  11.3 |  16.5  18.6 |   4.7   3.0   4.8 |   8.6   0.2   0.5 |   16.6     1.6 13.21  2.2
456.hmmer         5.43 |  67.9   2.0  16.9  13.2 |   1.0   0.5 |   0.5  16.4 |   4.6   0.5   8.5 |   8.5   0.0   4.3 |    0.3     2.5  0.10  1.3
458.sjeng         1.79 |  22.4  39.4  23.1  15.1 |  21.9  15.3 |   2.6  20.5 |   8.0   4.1   7.1 |  14.6   0.1   0.0 |   15.2     1.6  2.11  1.6
462.libquantum    2.29 |  28.6   0.9   8.5  62.0 |   0.3   0.2 |   0.0   8.4 |  52.4  32.1   9.6 |  61.6   0.0   0.0 |    0.2    21.6  0.02  6.3
464.h264ref       2.36 |  29.5   7.3  15.7  47.5 |   3.9   2.6 |   1.2  14.5 |  31.8   0.1  15.7 |  43.4   2.8   0.9 |    2.0     0.3  0.98  2.1
471.omnetpp       1.44 |  18.0  14.2  12.6  55.3 |   8.3   4.7 |   2.3  10.3 |  48.1  40.5   7.2 |  54.7   0.1   0.0 |    7.3    14.8  0.87  2.8
473.astar         1.59 |  19.9  16.9  12.2  51.0 |   7.7   8.0 |   0.0  12.2 |  18.9   4.5  32.1 |  50.5   0.0   0.0 |    6.2    10.1  0.03  1.8
483.xalancbmk     2.65 |  33.2  25.3  31.5  10.1 |  16.5   7.2 |   0.0  31.5 |   4.1   1.4   5.9 |   9.6   0.0   0.0 |    8.0     2.8  0.03  2.3

columns (% of slots): Ret/BadSp/FE/BE = level 1; mispr = mispredict recovery bubbles, wrong = wrong-path dispatches (both in BadSp);
 fLat = ICache+ITLB miss bubbles, fBW = other frontend bubbles (in FE); Mem/L1m/Core = by ROB head (Mem = head is a load/store, L1m = that load missed L1D);
 ROB/IQ/LSQ = by the full resource (in BE)
```

读法：
- **后端/访存型**：mcf（BE 74%，L1 缺失 35%，225 MPKI）、libquantum（BE 62%，L1 缺失 32%，MLP 6.3，预取收益大户）、omnetpp（BE 55%，L1 缺失 40%）。
- **ROB 满型**：bzip2（ROB 满 45%，头是非访存/其它）、astar（ROB 51%）、h264ref（ROB 43%）。
- **gcc 是 STQ 满**：BE 47% 里 **STQ 满占 45% 的槽**（LDQ 为 0），STQ 平均占用 58/64；这是 store 排空的问题（不是 load 缺失，L1 缺失只占 0.9%），值得单独看（STQ 大小、提交后写入 L1D 的速度、store 合并）。
- **分支型**：gobmk（Bad Spec 35%）、sjeng（39%）、xalancbmk（25%）：误预测恢复气泡 16–22%，brMPKI 15–17；gobmk 另有 ICache 缺失 13 MPKI（取指延迟 16.5%）。
- **接近满带宽**：hmmer（IPC 5.43，Retiring 68%）、perlbench、bzip2（Retiring 39–47%）。
- 口径提醒：“前端”里含取指带宽（taken 分支气泡等）这一大块，gcc/hmmer/perlbench 的 FE 基本都是它；重命名没有物理寄存器的槽记为前端（第 1 节）。
