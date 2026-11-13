# 待办事项

全项目唯一的待办清单（2026-11-05 起，原 rtl `docs/07-roadmap.md`、README “下一步” 中仍有效的条目已并入）。
每条写清为什么、做到什么算完；做完删掉，在 [LOG.md](LOG.md) 里留一行。（2026-11-12 文档审查：删除已完成或已过时的条目，补上 rv64 之后的收尾和未合入实验。）风险（验证缺口、变异存活）记在 [rtl/docs/08-risk-register.md](../rtl/docs/08-risk-register.md)，不在这里重复。

## 进行中

| 事项 | 状态 | 做完的标准 |
|---|---|---|
| LD/STA IQ 合并、统一 FTQ 的 RTL 试做结果入档 | 两个 RTL 试做都已完成（工作区 `rtl-ldsta`/`trace-model-ldsta`、`rtl-uftq`/`trace-model-uftq`，未提交）：门禁 66/66，66 个程序周期与各自的 trace-model 全部一致 | 在 [EXPLORATION.md](EXPLORATION.md) 记为新实验（含综合数字和未覆盖项）；工作区改动提交到各自的 `exp/` 分支 |

## 待做：验证

| 事项 | 为什么 | 做完的标准 |
|---|---|---|
| **逐条对比加上 store 比较**（rtl V-12） | 现在只比提交 PC 和目的寄存器。第 1 批的 MMIO store 数据错误（串口乱码、中断不来）逐条对比没报，是靠比串口输出发现的；之后还要动 LSU 端口和 LD/STA 合并 | `tb/soc/fm_check.h` 在每条 store 提交时比较物理地址、数据、字节使能（MMIO 和可缓存都比）；门禁重跑通过；再考虑 CSR 写值 |
| RTL 断言 | RTL 里几乎没有 assert；统一 FTQ、LD/STA 合并新加的断言因为测试平台不带 `--assert` 从未执行过 | 测试平台默认带 `--assert`，断言失败算门禁失败；模块笔记里的“假设/不可达”都有对应断言 |
| 闭环补跑 `float_test`；扩大 gate（rv32 `memory-stress` 已在 EXP-029 合入时跑过：230.8 万周期、745 万条指令逐条对比 0 不一致，但还没进回归，见 rv64 收尾） | 现在的 gate 程序都很小（最长 23 万周期） | `float_test` 在 RTL 逐条对比通过；gate / 回归加入更长的定向程序 |
| 去复位存储器的随机初值验证 | 测试平台用 `--x-initial 0`，会掩盖对初值的依赖 | `--x-initial unique` + 运行时随机，门禁通过 |
| 定向短测试补已知覆盖缺口 | front_top：RET 判定 `imm≠0`、SFENCE.VMA 后取指、冲刷与存储侧请求同拍；peripheral AXI 路径、PTW 超级页与 PTE 故障、MSHR_HIT/FULL 路由响应，真实程序基本不走 | 每个缺口一个短程序，进门禁 |
| 覆盖率 | 没有覆盖数据，不知道哪些逻辑从未被测到 | Verilator toggle 覆盖（line 覆盖对 assign 风格无意义），每模块出报告，汇总数字入库 |
| LD/STA 合并、统一 FTQ 的规模确认 | 都只在小程序和 gate 上测过；store 密集程序、48 还是 64 项都没定 | quick SPEC 上对比；决定是否进入主线 |

## 待做：RTL 实现

| 事项 | 为什么 | 做完的标准 |
|---|---|---|
| **mov 消除拉长了 `ren` 的关键路径**（EXP-012，已合入 main，默认开启） | 局部 yosys（通用门级数，不是时序）：`ren` 最长组合路径 63 → 130 级；开启后路径是 流水寄存器 → `ren_elim_sel`（33 项 RAT 比较求和）→ `ren_alloc_sel`（8 级串行选择）→ 目的寄存器选择 → RAT 快照 → 分支检查点，消除判定串在分配之前；收益只有 quick SPEC +0.06%、coremark −1.15% 周期，`ren` +12% 单元 | 先做有工艺库的综合量出真实 `ren` 时序（依赖下面“时序综合流程”）；若超标，按下面顺序试：① 判定与分配解耦（所有请求目的寄存器的槽先分配，被消除的槽丢弃分到的寄存器，不让判定进入分配链；会少用空闲寄存器，trace-model 要同步，周期要重新对齐）；② 判定拆成流水一级（用上一拍的 RAT 引用数，上限判定更保守）；③ 放宽到只按“RAT 引用数”不数组内写者；④ 都不行则 `CFG_MOVE_ELIM` 默认改 0（trace-model 与 RTL 一起改，基线、`ref_cycles.txt` 重生成）。每一步 trace-model 先量 quick SPEC，RTL 门禁 66/66 周期对齐 |
| AMO 改为“特殊 store、在 DCache 里读改写”（BOOM/香山式） | 现在 AMO 和 C910 一样拆成 LOAD + STA + STD（运算在 STD 里，rd=x0 借 32 号寄存器），同时占 LDQ 和 STQ；LD/STA 队列合并后一条 AMO 要在同一拍进 MEM 队列两次，dispatch 为此专留了一条通路（暂时保留这种做法） | trace-model 和 RTL：AMO 只占 STQ（一个地址 uop + STD），在 STQ 头、ROB 已排空时发给 DCache，DCache 流水线内做读改写（AMOALU），旧值经写回口送 rd；dispatch 的 AMO 双写口通路删除；门禁和 Linux 通过。可与 LD/STA 共享 AGU 一起考虑 |
| 统一 FTQ 的提交读口按块读 | 统一 FTQ 现在每条提交指令一个读口（PC 8 口 + 元数据 8 口，各从 64 项×8 槽里选），是 `ftq_top` 面积的大头。trace-model 统计（2026-11-05，SPEC 6 个最大权重点 + 5 个小程序）：一拍提交跨的 FTQ 块数超过 4 的周期最多 0.06%，超过 3 的在 gcc 上有 9.5% | decode 组队时限制一组最多跨 K 个块（trace-model IDU 与 RTL `pre_idu` 同步，参数 `CFG_DECODE_MAX_BLOCKS`，建议 K=4）；`ftq_top` 提交读口改为从 commit 指针读 K 个连续块整行再按块号/偏移选；quick SPEC 比较 K=3/4；RTL 门禁 66/66、周期与 trace-model 相等；提交读口选择器预计元数据 −44%、PC −50%（K=4） |
| `front_stall` 接回 | core_top 里写死为 0；BPU 更新队列会满时必须接回 | 接回后门禁通过，有触发它的测试 |
| LLC 旁路写、部分行写 miss | 未实现（断言保留）；随机流量会触发，真实程序不走 | 实现并通过随机流量测试 |
| RealLsu 手写结构 | 3 个脚本生成的 SSA 展开文件（约 890 行）应改为手写结构 | 改写后门禁通过 |
| 整数组次态写法排查 | `isu_iq_store`、`rob_store`、`dispatch`、`idu` 里是否还有整数组次态写法未核实 | 逐个确认或改写 |
| `axi_subsys` 的 UNOPTFLAT | `axi_llc.in_w` 经结构体的组合环，`lint.sh` 对它只做规范检查 | 确认是误报还是真环，消除后纳入 `-Wall` |
| 端口样板由 spec 生成；非压缩数组端口统一 | `axi_llc`/`axi_interconnect`/`axi_subsys`/`mem_axi` 端口仍是非压缩数组 | 生成器覆盖这些模块 |

## 待做：已提交 store 的 write buffer（EXP-024 合入 main 后）

EXP-024 合入的是"STQ 内分组"的简化版 write buffer：4 个条目、每条目最多 2 个同 line 的 store，store 仍留在 STQ 里等响应，load 的转发只查 STQ。香山（昆明湖）和 BOOM 的做法对照见 EXPLORATION EXP-024。

| 事项 | 为什么 | 做完的标准 |
|---|---|---|
| **香山式独立 SBuffer**（提交即搬进缓冲区，STQ 项马上释放） | 现在 STQ 项要等响应才释放；香山的 SBuffer 是 64B 整行条目加字节掩码，StoreQueue 每周期最多送 2 个，按阈值排空（积累更多 store 再写），load 同时查 StoreQueue 和 SBuffer（优先级 StoreQueue > SBuffer > DCache） | 模型：条目数据 + 字节掩码、load 对缓冲区的字节级转发和部分命中、fence / 原子 / 同 line 冲突触发的排空、按阈值排空；用同样 5 个点重扫条目数和阈值，收益不低于 EXP-024；再做 RTL 并与模型逐周期对齐 |
| 阈值式排空是否比"立即排空"更好 | 现在条目一有空口就发，积累的 store 少；香山等占用到阈值才发 | 模型里加阈值参数，比较 gcc/h264ref/hmmer/perlbench |
| EXP-024 的参数只在 5 个点上扫过 | 全量 580 点已对比（+0.68%），但条目数、口数、插入宽度、粒度是在 gcc、h264ref、hmmer、perlbench、gobmk 各 1 个点上选的；perlbench、h264ref、bzip2 个别点有 −4.6% 到 −6.3% 的回退，没有分析 | 在全量 SPEC 上重扫关键参数（条目数、口数、插入宽度）；逐个看最差的几个点为什么回退 |
| Linux `s04` 的 SC 不一致（原因未定位） | 第一版配对 RTL 在 `s04` 有 1 处 `sc.w` 判失败（function-model 判成功），SC 的成功在自己的写回拍按预约状态判定，时序变化可能暴露原有竞争；write buffer 版 13/13 通过，说明在新时序下没有再触发，不等于原因已排除 | 用第一版配对 RTL（rtl `b1e0335`）重现 `s04`，波形看 LR 写回与 SC 判定的先后；确认是原有竞争还是合并逻辑 |

## 待做：访存推测与前端快速通路的收尾（EXP-019 / 020 / 023，2026-11-09 合入 main 后）

| 事项 | 为什么 | 做完的标准 |
|---|---|---|
| **RTL 上的 SPEC**（逐点周期与 trace-model 相等） | +11.02% 只是 trace-model 的数；模型与 RTL 的相等只在 68 个小程序和 Linux 上验证过 | 抽样的 SPEC 点（至少 12 个程序各 1 个高权重点）RTL 周期 = 模型周期，逐条对比通过 |
| 小 LLC 检查（模型 + RTL） | 本次合入没跑 | `scripts/llc_small_check.sh` 通过 |
| `FE_RFAST` 的 BPU 面积和 `front_pred_path` 深度（+6% 超判据） | 前端笔记的 `bpu` +19%（`RFAST=15` vs 关，平衡 ABC）和合并综合表（−9.5%，轻量 ABC）互相矛盾；`front_pred_path` 深度 134 → 142 | 同一综合流程对合并后的树做 `FE_RFAST=0` 与 15 的对比；若深度必须回到 5% 内：用 `spec_r1` 推导 `spec_r2`（省面积、费深度）或拆 `front_pred_path` 的关键链 |
| `FE_BFAST` 的深度（+34%） | 收益 +1.2~1.8%（RFAST 之上约 +2.4%），关着；是否值得取决于时钟目标 | 有时序库流程后量 `bpu` 关键路径；只有当时钟周期被更深的路径决定才开 bit1（+1.8%） |
| `FE_PAIR`（一拍两块）的 RTL | 模型 +2.9%（RFAST+BFAST 之上）；RTL 要改写 BPU 前端（第二次 uBTB 读、第二套历史/RAS/TAGE 索引、主阵列第二读口、PTAB 项 +50%），估计 3–4 周，前端面积 +30% 以上，S0 双查在当前深度放不进一个周期 | 先用模型量"第二块放到 S1 用寄存的首块猜测查"的变体（稳态两块、重定向后一个气泡）；再决定是否做 RTL，见 EXPLORATION EXP-023 |
| `FE_IPF`（I$ 预取）走真实内存通路 | 模型的预取不经过 LLC/AXI/DRAM（只对此前被需求 miss 填过的行预取，固定 12 周期，无带宽建模），+1.75% 是上界 | 模型里让预取走真实 LLC/AXI/DRAM 路径后重测；RTL 需要新通路，量收益再决定 |
| FTQ 读口面积没计入综合表 | 给 dispatch 读 PC 的 64 选 1 块基 PC + 偏移（+16.9k 单元，`$mem` 读口在流程里不计单元）不在 `pre_idu_queue` 的数里 | 综合表里把 FTQ 读口单独列出来 |
| `spec/*.io` 没更新 | 已退役的逐模块边界描述，访存推测（`spec_ok`、`unk`、`defer`、`flush_pipe` 等）没写进去 | 要么更新，要么在文档里明确这些文件已不再维护 |
| 访存推测的值路径覆盖 | `LSU_MS_DATA` 里旧地址的 load/store、CSR/FP/AMO 消费者没有 RTL 验证 | 找到能触发的程序（或定向测试）并在 RTL 上对比 |
| 访存推测的面积代价归因 | `lsu` −7.7% 里"推测本身的代价"和"`lp_ovl` 重写的收益"没拆开 | 在同一流程里分别综合：关推测 + 旧重叠判断 / 关推测 + `lp_ovl` / 开推测 |

## 待做：前端与间接跳转的收尾（EXP-025）

| 事项 | 为什么 | 做完的标准 |
|---|---|---|
| 多表 ITT 之后 −3% 到 −5% 的点 | perlbench sp13 −4.5%、gcc sp29 −3.8%、xalancbmk sp31 −3.3%，没查原因 | 看是 JALR 误预测变多还是别的；必要时调表数、表大小或分配策略 |
| **`BPO_LOOP=1` 循环预测器**（模型里已有，默认关） | 9 点几何平均 +0.60%，几乎全来自 xalancbmk +4.79%，gobmk +0.61%（EXPLORATION EXP-025） | 在更多 SPEC 点上量（全量或 30 点）；评估 RTL 代价（S0 单块循环退出判断，在关键路径上）；有净收益再做 |
| I$ 容量问题（gobmk 热代码约 95 KB） | 替换策略、victim buffer 在全量上收益有限（EXPLORATION EXP-025） | 只有在更大的 I$ 或跨行取指有明确收益时再做；记录结论即可，不预设要做 |

## 待做：紧凑 ROB 的收尾（EXP-028，2026-11-11 合入 main 后）

| 事项 | 为什么 | 做完的标准 |
|---|---|---|
| 分支密集短循环被 BPU 更新带宽卡住 | 紧凑 ROB 的额度不让提交冲爆 BPU 更新队列，但队列每拍只能写回不到 1 条：gcc sp48/sp21/sp12/sp2 慢约 37%、sp5 −26%，dhrystone 周期 +1.8%、coremark +0.6%；行式 ROB 时这些更新 89% 被丢掉，预测照样好 | 额度不够时不挡提交、只丢预测正确且计数器饱和的分支的更新（或其他办法）；这几个点回到行式 ROB 的水平，SPEC 全量不低于 +2.74%，模型、RTL 同步 |
| PMU：分发被 ROB 空闲项数挡住时记成 `SLOT_BE_SERIAL` | 紧凑模式下 `rob2dis.ready` 仍为 1，分发由 `free_cnt` 限制，`Dispatch::pmu_slots` 落到兜底的 SERIAL；gcc sp48 有 609 万个槽被错记 | 这种情况记成 `SLOT_BE_ROB_FULL`，gate 周期不变 |
| `rob` 深度 53（行式 46） | 最长路径：读出 → 旋转 → 指令分类与额度比较 → 前缀 → 新队头选择 | 把"完成 / 冲刷类 / 分支 / 块结束"在项里算好存下，深度回到行式 +5% 以内，或说明不做的理由 |

## 待做：rv64 的收尾（EXP-029，2026-11-12 合入 main 后）

- 生成文件欠债：`back_top.sv` / `exu.sv` / `soc_top.sv` 是手改的，`tools/gen_backtop.py`、`gen_soc_top.py`、`spec/*.io` 和 `gen_cfg_pkg.py`（`XLEN_BITS`）要同步，否则重新生成会丢 rv64 位宽。
- 对周期必须用 `LSU_PIPE_NOWD=1` 跑模型（否则 63 周期看门狗会让 store 重发，`crc32` 等程序差几十周期）；考虑把它设成 trace-model 默认或在 `cyc*.sh` 里写死。
- 把 rv32 `memory-stress` 加进回归（rv32 子集 ≤15 万周期测不出大数组写回 bug）。
- F/D（rv32 和 rv64，EXP-030…036 已合 main，模型和 RTL 逐周期一致，rv64g Linux 在 RTL 上到登录且 `fptest: PASS`；还没做：RTL 的可综合 FP 单元（现在是 DPI softfloat，S7）、PolyBench/SPECfp 上标定延迟和队列大小、STD 口 FP 数据口数、F/D 的 SPEC 验证、`BpuPipe` 剩余拷贝热点）、C、bitmanip 边界测试、SPEC rv64 检查点流程、FastWarm 的 Sv39、function-model rv64 的 MMIO `sd`/`ld` 回读、交互式登录测试。

## 待做：乘除法器的物理实现优化（2026-11-12，EXP-029 综合代理对比后）

现状（`rtl/rtl/backend/exu_fu/`，数字见 `rtl/docs/09-synthesis-report.md` 第 10 节，yosys 通用门，相对值）：

- **乘法器 `mul_core`**：一行 `a * b`（33×33 / 65×65 有符号，四种变体共用，每次都算满 2×XLEN 位积），**单周期纯组合**。`mul_pipe` 只是 `MUL_MAX_LATENCY`（rv32 为 2、rv64 为 3）深的结果延迟线，周期上和模型对齐，物理上整个乘法器在第一级寄存器之前的一拍里：深度 rv32 120 级 → rv64 213 级，面积 7,565 → 28,411 单元（`exu.sv` 里 `MUL_NUM = 2`）。没有 Booth，没有压缩树，也没有重定时。
- **除法器 `div_core`**：迭代恢复除法，每周期 2 步（`XLEN / DIV_MAX_LATENCY`），rv64 为 32 周期、`divw` 16 周期；每周期的路径是两级 64 位减法加选择，深度 96 → 215；有符号运算先取绝对值、最后修正符号（两处 64 位取反）。面积 1,822 → 4,951。

要做的事（周期数保持不变，除非明确说明；任何改动之后都要重跑 `fm_gate`（周期与 `ref_cycles.txt` 0 处不同）、rv64 的 53 个程序和 lint，并用 `scripts/synth_depth.sh` 对比每级的深度和面积）：

1. **乘法器真正流水化**：把乘法器拆成 `MUL_MAX_LATENCY` 级，接口和延迟不变：第 1 级 Booth radix-4 编码 + 部分积 + 部分压缩，第 2 级 Wallace / Dadda 压缩树，第 3 级最终加法器和 `mul` / `mulh*` / `mulw` 选位。rv32（2 级）和 rv64（3 级）各给出切法。`mul_pipe` 的延迟线改成真实的级间寄存器（带 flush / `br_mask` 清除），不再另存一份完成结果。
2. **乘法器面积**：评估两个乘法单元里让其中一个只做 `mul` / `mulw`（只需低 XLEN 位，部分积少一半）；或 `mulh*` 多周期完成、只保留一个全宽乘法器（后者改变 `mulh*` 的延迟，要先在 trace-model 里建模并重新标定 `ref_cycles.txt`，不是纯 RTL 改动）。
3. **除法器每周期深度**：评估 radix-4 / SRT（每周期 2 位商，进位保存的余数，避免每步 64 位进位传播），把每周期路径降到一级小的选择 + 一个 CSA；评估有符号修正（取绝对值 / 结果取反）是否落在关键路径上，必要时单独占一拍或用预计算。
4. **除法器延迟**：`DIV_MAX_LATENCY` rv64 为 32 周期偏长；高基数或提前终止（除数 / 被除数前导零）可以缩短，但这会改周期，需要模型 `CONFIG_DIV_LATENCY` 同步、重新标定、重跑 SPEC 对比，和第 3 项分开做。
5. **验证**：乘除法器各加定向测试（符号 / 零除数 / `INT_MIN / -1` / 溢出 / `mulh*` 四种变体 / `*W` 变体，rv32 和 rv64），用函数模型逐条对比；综合代理记录写进 `09-synthesis-report.md` 和 MAIN_RECORDS。
6. 真实频率 / 工艺库面积 / WNS 仍然要在有工艺库的流程里做（见 `rtl/docs/08-risk-register.md` V-7），代理里的深度不能代替。

## 待做：未合入的实验

| 事项 | 为什么 | 做完的标准 |
|---|---|---|
| sdip（Breadcrumbs）预取器（EXP-026，`exp/sdip`）是否合入 | 模型完成：SPEC 全量 580 点 `PF_SDIP=2`（sdip 在前、h1 在后）几何平均 IPC +1.74%，`PF_SDIP=1`（替换 h1）只有 +0.10%（libquantum −11.9%）；RTL 没做 | 决定是否做 RTL；需要时先在最新 main 上重测（合入 EXP-027/028 后基线已变） |
| 旧的串联脚本 `scripts/gate_all.sh` | 头注释还写 trace-model gate 62 个测试，还在 `/tmp` 写日志，没有 XLEN=64 一档；最近几次合入的记录里都没有用到它（合入流程按 WORKFLOW 第 6 节的步骤） | 更新成当前的 gate（64 / `fm_gate.sh` 69）或删掉 |

## 待做：流程与工具

| 事项 | 为什么 | 做完的标准 |
|---|---|---|
| 性能计数（PMU）后续（EXP-013 已合入 main：trace-model `PMU=1`、RTL tier 1 事件总线 + 计数器块） | RTL 计数器块还没接 CSR（软件不可见）；RTL 只有 18 个事件；详见 [PMU.md](PMU.md) 第 4 节 | ① 决定软件是否可见（改 function-model / trace-model IDU / RTL CSR 的"这些 CSR 不存在"约定，OpenSBI 会探测，Linux 要重跑）；② 需要时给 icache/rob/lsu 加输出，补二级事件（取指延迟/带宽、Memory/Core）；③ 综合 `pmu`（接上后）；④ 前门恢复 `cycle_base` 未清零（`sim-time` 少报恢复程序的周期，mcf 点 −0.04%，改它会动所有 SPEC 基线）（⑤ dhrystone `ret` 预测错误率约 100% 一条已过时：现在约 1%，见 EXPLORATION EXP-025） |
| 时序综合流程 | MAIN_RECORDS 要求记 WNS，但现在只有 yosys 通用门面积代理，没有工艺库、时序约束和静态时序分析；整机面积推算也只在旧配置下做过（第 3 批只综合了受影响模块） | 选定开源工艺库（如 ASAP7/Nangate45）+ 约束频率，主要模块能出面积和 WNS；整机推算可按需重跑 |
| SPEC 检查点生成提速 | 生成检查点要把整个程序顺序再跑一遍（sjeng 约 3.7 小时，单线程） | BBV 时顺带存粗粒度检查点，生成 SimPoint 检查点时从最近的粗检查点并行起跑 |
| `/tmp` 里的其他生成数据 | `/tmp/ckpt` 已不存在，Linux 检查点现在在 `~/personal/AI-Huma-data/linux/`（`ck_s01_13`、`ckpt`）；综合中间结果等放在 `/tmp` 的东西重启会丢（SPEC 检查点已因此丢过一次） | 确认没有数据还只在 `/tmp`；文档写明 Linux 检查点位置和生成命令 |
| 推送 EXP-029 及之后的提交 | 远程已配好（`.gitmodules` 指向 `tututugege/AI-Huma-{func,trace,rtl}`），main 已推到 EXP-028；EXP-029 的合入、之后的宏/环境变量清理和文档审查只在本地 main（2026-11-12：总仓库领先 origin 7 个提交，trace-model 16、rtl 9、function-model 7） | 推送由用户决定；推送前总仓库子模块指针要指向各子仓库已推送的 commit |
| trace-model 剩余小优化 | 每项不到 3%；状态标志整理 | 逐项做，gate 周期不变 |
| EXP-015 的已知回退 | 全量 −1.20%：bzip2 −10.2%、libquantum −5.6%、hmmer −5.3%、h264ref −5.1% | 先用精确预热确认是不是快速预热对新 BPU 的偏差；真实回退看 TMA（前端空槽）；推测唤醒（模型 +2.9pp，硬件代价未测）；DCW 看门狗事件根因；SPEC 开 `PMU=1` 补 TMA |
