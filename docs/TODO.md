# 待办事项

全项目唯一的待办清单（2026-11-05 起，原 rtl `docs/07-roadmap.md`、README “下一步” 中仍有效的条目已并入）。
每条写清为什么、做到什么算完；做完删掉，在 [LOG.md](LOG.md) 里留一行。（2026-11-10 清理：删除已完成的“快速 warmup”，DRAMsim3 一条收窄为只剩 `exp/lsu-stwin`。）风险（验证缺口、变异存活）记在 [rtl/docs/08-risk-register.md](../rtl/docs/08-risk-register.md)，不在这里重复。

## 进行中

| 事项 | 状态 | 做完的标准 |
|---|---|---|
| rtl `exp/lsu-stwin`（旧 LSU 的 store 侧队列窗口修复，`b94b4f5`，未合入） | DRAMsim3（EXP-006）已合入 main（DRAMsim3 已是子模块），main 的 `lsu_dc_req_st` 已按 `STWIN` 修了提交窗口；这个分支另外修了旧 LSU（`LSU_PIPE=0`）里 `wait_mmu_stq`、`mmu_done_stq` 经通用 `ring_apply` 仍按 load 窗口 20 处理的部分，默认的分级 LSU（`lp_*`）不受影响 | 决定合入还是删除：只对 `LSU_PIPE=0` 的旧路径有意义；合入的话在不分频 + STA 端口 1 的配置下对照修复前后 RTL 与 trace-model 周期（修复后 66/66 相等） |
| LD/STA IQ 合并、统一 FTQ 的 RTL 试做结果入档 | 两个 RTL 试做都已完成（工作区 `rtl-ldsta`/`trace-model-ldsta`、`rtl-uftq`/`trace-model-uftq`，未提交）：门禁 66/66，66 个程序周期与各自的 trace-model 全部一致 | 在 [EXPLORATION.md](EXPLORATION.md) 记为新实验（含综合数字和未覆盖项）；工作区改动提交到各自的 `exp/` 分支 |

## 待做：验证

| 事项 | 为什么 | 做完的标准 |
|---|---|---|
| **逐条对比加上 store 比较**（rtl V-12） | 现在只比提交 PC 和目的寄存器。第 1 批的 MMIO store 数据错误（串口乱码、中断不来）逐条对比没报，是靠比串口输出发现的；之后还要动 LSU 端口和 LD/STA 合并 | `tb/soc/fm_check.h` 在每条 store 提交时比较物理地址、数据、字节使能（MMIO 和可缓存都比）；门禁重跑通过；再考虑 CSR 写值 |
| RTL 断言 | RTL 里几乎没有 assert；统一 FTQ、LD/STA 合并新加的断言因为测试平台不带 `--assert` 从未执行过 | 测试平台默认带 `--assert`，断言失败算门禁失败；模块笔记里的“假设/不可达”都有对应断言 |
| 闭环补跑 `memory-stress`、`float_test`；扩大 gate | 现在的 gate 程序都很小（最长 23 万周期） | 两个程序在 RTL 逐条对比通过；gate 加入更长的定向程序 |
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
| 删除分开式结构里的 `altpcpn` 存储 | BPU 训练从不读它（EXP-007 补上标准 TAGE 的备选更新也无收益）；现在 PTAB、front2back、后端 FTQ 每个槽都白存 3 位 | trace-model 与 RTL 删掉这份存储和连线，周期不变（门禁 66/66、gate 62/62 逐个相同）；统一 FTQ 若合入则随之消失 |
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
| **合并后的 RTL 树从复位连续跑到 `rv32 login:`** | 合入时只做了 13 段检查点接力（微架构每段冷启动），推测和前端快速通路都是时序相关的状态 | RTL 测试平台 `SOC_FM=1 SOC_TB_FM=1` 从复位到登录，逐条对比 0 不一致（约 3–4 小时，服务器） |
| **RTL 上的 SPEC**（逐点周期与 trace-model 相等） | +11.02% 只是 trace-model 的数；模型与 RTL 的相等只在 68 个小程序和 Linux 上验证过 | 抽样的 SPEC 点（至少 12 个程序各 1 个高权重点）RTL 周期 = 模型周期，逐条对比通过 |
| 小 LLC 检查（模型 + RTL） | 本次合入没跑 | `scripts/llc_small_check.sh` 通过 |
| `FE_RFAST` 的 BPU 面积和 `front_pred_path` 深度（+6% 超判据） | 前端笔记的 `bpu` +19%（`RFAST=15` vs 关，平衡 ABC）和合并综合表（−9.5%，轻量 ABC）互相矛盾；`front_pred_path` 深度 134 → 142 | 同一综合流程对合并后的树做 `FE_RFAST=0` 与 15 的对比；若深度必须回到 5% 内：用 `spec_r1` 推导 `spec_r2`（省面积、费深度）或拆 `front_pred_path` 的关键链；(`front_pred_path.sv` 的 slang 声明顺序已在 `exp/integ` 里改好，main 上现在合并了，`lint.sh` 能综合它，此项已完成) |
| `FE_BFAST` 的深度（+34%） | 收益 +1.2~1.8%（RFAST 之上约 +2.4%），关着；是否值得取决于时钟目标 | 有时序库流程后量 `bpu` 关键路径；只有当时钟周期被更深的路径决定才开 bit1（+1.8%） |
| `FE_PAIR`（一拍两块）的 RTL | 模型 +2.9%（RFAST+BFAST 之上）；RTL 要改写 BPU 前端（第二次 uBTB 读、第二套历史/RAS/TAGE 索引、主阵列第二读口、PTAB 项 +50%），估计 3–4 周，前端面积 +30% 以上，S0 双查在当前深度放不进一个周期 | 先用模型量"第二块放到 S1 用寄存的首块猜测查"的变体（稳态两块、重定向后一个气泡）；再决定是否做 RTL，见 EXPLORATION EXP-023 |
| `FE_IPF`（I$ 预取）走真实内存通路 | 模型的预取不经过 LLC/AXI/DRAM（只对此前被需求 miss 填过的行预取，固定 12 周期，无带宽建模），+1.75% 是上界 | 模型里让预取走真实 LLC/AXI/DRAM 路径后重测；RTL 需要新通路，量收益再决定 |
| FTQ 读口面积没计入综合表 | 给 dispatch 读 PC 的 64 选 1 块基 PC + 偏移（+16.9k 单元，`$mem` 读口在流程里不计单元）不在 `pre_idu_queue` 的数里 | 综合表里把 FTQ 读口单独列出来 |
| `spec/*.io` 没更新 | 已退役的逐模块边界描述，访存推测（`spec_ok`、`unk`、`defer`、`flush_pipe` 等）没写进去 | 要么更新，要么在文档里明确这些文件已不再维护 |
| 访存推测的值路径覆盖 | `LSU_MS_DATA` 里旧地址的 load/store、CSR/FP/AMO 消费者没有 RTL 验证 | 找到能触发的程序（或定向测试）并在 RTL 上对比 |
| 访存推测的面积代价归因 | `lsu` −7.7% 里"推测本身的代价"和"`lp_ovl` 重写的收益"没拆开 | 在同一流程里分别综合：关推测 + 旧重叠判断 / 关推测 + `lp_ovl` / 开推测 |

## 待做：流程与工具

| 事项 | 为什么 | 做完的标准 |
|---|---|---|
| 性能计数（PMU）后续（EXP-013 已合入 main：trace-model `PMU=1`、RTL tier 1 事件总线 + 计数器块） | RTL 计数器块还没接 CSR（软件不可见）；RTL 只有 18 个事件；详见 [PMU.md](PMU.md) 第 4 节 | ① 决定软件是否可见（改 function-model / trace-model IDU / RTL CSR 的"这些 CSR 不存在"约定，OpenSBI 会探测，Linux 要重跑）；② 需要时给 icache/rob/lsu 加输出，补二级事件（取指延迟/带宽、Memory/Core）；③ 综合 `pmu`（接上后）；④ 前门恢复 `cycle_base` 未清零（`sim-time` 少报恢复程序的周期，mcf 点 −0.04%，改它会动所有 SPEC 基线）；⑤ dhrystone 两条 `ret` 预测错误率约 100% 的原因 |
| 时序综合流程 | MAIN_RECORDS 要求记 WNS，但现在只有 yosys 通用门面积代理，没有工艺库、时序约束和静态时序分析；整机面积推算也只在旧配置下做过（第 3 批只综合了受影响模块） | 选定开源工艺库（如 ASAP7/Nangate45）+ 约束频率，主要模块能出面积和 WNS；整机推算可按需重跑 |
| SPEC 检查点生成提速 | 生成检查点要把整个程序顺序再跑一遍（sjeng 约 3.7 小时，单线程） | BBV 时顺带存粗粒度检查点，生成 SimPoint 检查点时从最近的粗检查点并行起跑 |
| `/tmp` 里的其他生成数据 | Linux 特殊检查点 `/tmp/ckpt`、综合中间结果等重启会丢（SPEC 检查点已因此丢过一次） | 挪到 `~/personal/AI-Huma-data/`，文档写明位置和生成命令 |
| 远程仓库 | 子模块 URL 还是本地相对路径 | 配好总仓库和三个子仓库的远程地址，改子模块 URL；推送由用户决定 |
| trace-model 剩余小优化 | 每项不到 3%；状态标志整理 | 逐项做，gate 周期不变 |
| EXP-015 的已知回退 | 全量 −1.20%：bzip2 −10.2%、libquantum −5.6%、hmmer −5.3%、h264ref −5.1% | 先用精确预热确认是不是快速预热对新 BPU 的偏差；真实回退看 TMA（前端空槽）；推测唤醒（模型 +2.9pp，硬件代价未测）；DCW 看门狗事件根因；SPEC 开 `PMU=1` 补 TMA |
