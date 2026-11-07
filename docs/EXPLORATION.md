# AI-Huma 架构探索记录

每次架构/性能探索写一节，最新的在最上面，不论是否合入、结论正负。规则见 [WORKFLOW.md](WORKFLOW.md) 第 5.1 节。

| 编号 | 日期 | 题目 | 分支 | 状态 | 一句话结论 |
|---|---|---|---|---|---|
| [EXP-012](#exp-012-mov-消除move-elimination) | 2026-11-06 | `addi rd, rs, 0` 在重命名时共用源物理寄存器（mov 消除），架构引用计数，3 位计数器 + 引用上限 | trace-model `exp/move-elim-v2`、rtl `exp/move-elim` | 已合入 main（默认开启） | quick SPEC 几何平均 IPC 1.550 → 1.551（+0.06%），coremark −1.15% 周期；`ren` +21.5k 单元（+10%）；收益在噪声量级 |
| [EXP-009](#exp-009-l1d-数据预取器与指令侧预取) | 2026-11-06 | 电路风格的 L1D 数据预取器（步长 + LLC 次级 next-line + 准确度限流）；指令侧 next-line / FDIP | trace-model `exp/prefetch-h1`、rtl `exp/l1d-prefetch` | 已合入 main（2026-11-07） | 20 个访存瓶颈点（14 训练 + 6 留出）几何平均 IPC：训练 +37.9%、留出 +30.4%；计算密集守卫集 +0.5%；指令侧最多 +0.4%，不采用 |
| [EXP-008](#exp-008-decode-宽度-8-降到-6) | 2026-11-05 | decode/rename 宽度 8→6（含 commit 宽度拆分）；前端取指仍为 8 | trace-model `exp/decode6` | 未提交、不合入；保持 8 | quick SPEC 几何平均 IPC −3.1%（hmmer −12%，其余 5 个 −1.1%）；损失来自 hmmer 的高 IPC 阶段，commit 宽度不是原因 |
| [EXP-007](#exp-007-tage-备选提供者计数器更新) | 2026-11-05 | TAGE 训练时也更新备选提供者的计数器（`altpcpn` 的用途） | trace-model `exp/tage-alt`（工作区 `trace-model-tage`） | 未提交、不合入 | 6 个分支难预测的 SPEC 上 MPKI 变化 ±0.6%、IPC 不变；`altpcpn` 可以删除 |
| [EXP-005](#exp-005-opt1-的-spec-对比与不改结构的参数同步到-rtl) | 2026-11-05 | opt1 的 quick SPEC 对比；不改结构的参数（第 1–3 批）同步到 RTL | trace-model `exp/batch3`、rtl `exp/batch3` | **已合入 main**（2026-11-05） | quick SPEC 6 个程序 opt1、第 3 批都慢 0.5%（gcc 1.3%）；第 1–3 批（不改结构的部分）RTL 门禁均 66/66、周期与 trace-model 一致，约省 161 万门、5 万触发器 |
| [EXP-004](#exp-004-组合优化配置-opt1) | 2026-11-04 | 组合优化配置 opt1（MAX_BR 32、INT IQ 64 + 前面所有优化） | trace-model `exp/area-explore` | 未提交、未合入；SPEC 见 EXP-005 | 小程序几何平均持平，coremark 慢 1.8–2.7% |
| [EXP-003](#exp-003-rob-与-prf-扩大到-256) | 2026-11-04 | ROB/PRF 扩大到 192、256 | trace-model `exp/area-explore` | 未提交、未合入 | 都翻倍到 256 只快约 0.8%（coremark 3%），ROB 128 合理 |
| [EXP-002](#exp-002-全核面积浪费排查) | 2026-11-04 | 全核面积浪费排查：各 IQ、ibuf、front2back、分支资源、ALU/BRU 端口 | trace-model `exp/area-explore` | 未提交、未合入 | IQ 总项数 384→192、BRU 4→2 等组合后无性能损失；BPU 存储需大负载评估（“ROB 是瓶颈”的说法已被 EXP-003 否定） |
| [EXP-001](#exp-001-面积优化三个方向) | 2026-11-04 | 面积优化：FTQ 合并、LSU 端口、LD/STA IQ 合并 | trace-model `exp/area-explore` | 未提交、未合入 | 三个方向都能省面积，性能代价 0–1% |

---

## EXP-012 mov 消除（move elimination）

- **日期**：2026-11-06（最早的探索 2026-11-03：trace-model `exp/move-elim`，3 个提交，未合入；2026-11-06 重放到新 main 并做到 RTL）
- **分支**：trace-model `exp/move-elim-v2`（`767c25f`，基于 main `88e5254`）、rtl `exp/move-elim`（`1e5d656`，基于 main `b19a181`）；已快进合入 main。
- **问题**：`addi rd, rs, 0`（rd、rs 都是真寄存器）占提交指令的 3%（dhrystone 64 次）到 9%（coremark），能否在重命名时去掉，省下一个物理寄存器、一个发射槽和一次写回？
- **做法**：
  - Ren：这类指令不取空闲寄存器，rd 直接指向 rs 的物理寄存器（`dest_preg = src1_preg`）；不产生 uop，ROB 条目在 dispatch 时就完成，Dispatch 不置 busy 位、不参与组内 RAW 判断。
  - 寄存器的释放：**提交时**统计架构 RAT 里有多少项指向它（`arch_cnt`），旧寄存器的计数降到 0 才放回空闲表。重命名端不改计数，所以分支误预测和冲刷**不需要回滚计数**；`free_head_commit` 跳过被消除的 mov，空闲表头指针的检查点仍然有效。
  - 计数器上限：某条 mov 提交后的架构状态等于它重命名后的推测 RAT，所以架构计数不会超过重命名时推测 RAT 中指向该寄存器的项数。规则（`Ren::elim_refs_ok`）：源寄存器直接来自推测 RAT（本组内没有更老的指令写同一个源架构寄存器），且（推测 RAT 中指向它的项数）+（本组更老的有目的寄存器的指令数）+ 1 ≤ `CFG_MOVE_ELIM_REFS`（默认 7）。这样计数器只要 3 位，不用维护第二份推测计数，同组内的 mov 链也没有组合依赖。
  - RTL：新增 `ren_elim_sel`（判定）、`ren_arch_cnt`（计数与释放）、`ren_rank`；`me_elim` 一位从 Ren 经 Dispatch、ROB 回到 Ren；`MOVE_ELIM = 0` 时不生成任何新逻辑。
- **开关**：trace-model `CFG_MOVE_ELIM`（默认 1，原 `ME_ELIM` 环境变量）、`CFG_MOVE_ELIM_REFS`（7）；RTL 参数 `MOVE_ELIM`、`MOVE_ELIM_MAX_REFS` 由 `make cfg` 从 config.h 取。运行时 `ME_CHECK=1` 每周期检查：计数等于架构 RAT 指向该寄存器的项数、无物理寄存器泄漏，并打印最大引用数。
- **关闭开关时**：trace-model gate 62/62 与原基线逐个相同，dhrystone 162,033、coremark 255,335 不变；RTL（`MOVE_ELIM=0`）`fm_gate` 66/66，周期与原 `ref_cycles.txt` 逐个相等。
- **结果**（周期，1 GHz + DRAMsim3 基线）：

| 负载 | 关闭 | 开启 | 变化 | 被消除的 mov |
|---|---|---|---|---|
| dhrystone（64 次） | 162,033 | 162,033 | 0 | 129 |
| coremark（2 次迭代） | 255,335 | 252,400 | −1.15% | 34,737 |
| memory-stress | 2,428,470 | 2,425,220 | −0.13% | |
| gate 62 个程序 | | | 7 个程序周期变化 | |

  quick SPEC（6 个程序、129 个点，`replay.sh quick`，每点 1000 万条指令，无 difftest 不一致）：perlbench 2.100 → 2.090、gcc 1.523 → 1.525、mcf 0.420 → 0.420、hmmer 3.770 → 3.771、sjeng 1.830 → 1.831、h264ref 1.497 → 1.507；**几何平均 1.550 → 1.551（+0.06%）**。引用数最大 4（coremark），上限 7 有余量。
  没有引用上限的第一版（旧基线，2026-11-03）：dhrystone −0.77%、coremark10 −1.15%、quick SPEC +0.46%；加上限后 coremark 少消除约 25% 的 mov（组内旁路的源不再消除），周期反而略好（噪声内）。
- **面积**（yosys 通用门面积代理，`scripts/synth_cfg.sh`，原配置 vs 开启）：`ren` 206,228 → 227,720 单元（+21.5k，+10.4%）；`dispatch` 86,637、`rob` 201,672 不变（`me_elim` 一位的存储没有计入）。上面的数字里 `arch_cnt` 被综合脚本（`SYNTH_MEM=1`）当存储，触发器没有计入；把计数器映射成触发器重跑 `ren`（`memory_map`，同一套 abc 脚本）：**206,228 → 231,029 单元（+24.8k，+12.0%），触发器 10,315 → 10,699（+384）**；整机占比不到 0.5%。
- **关键路径（局部 yosys `ltp`，通用门级数，不是时序）**：`ren` 最长组合路径 **63 → 130 级**。开启后最长路径是 流水寄存器 → `ren_elim_sel`（33 项 RAT 比较求和）→ `ren_alloc_sel`（8 级串行选择）→ 目的寄存器选择 → RAT 快照 → 分支检查点；原来消除判定不在分配之前。重命名级的频率风险是实在的，需要有工艺库的综合确认；缓解办法：先分配后判定（被消除的指令不用寄存器，但分配编号对它们无害，只需把「占用」与「判定」解耦）、或放宽上限判定为流水一级。
- **验证**：trace-model gate 62/62、`ME_CHECK=1` 零断言；RTL 开启时 `fm_gate` 66/66、周期与 trace-model 逐个相等；trace-model 与 RTL（逐条对比）Linux 从复位启动到 `rv32 login:`；lint.sh/lint_chip.sh 0 警告（开、关两种配置）。
- **与开源设计的对比（只查到一部分）**：香山 `Rename.scala` / `BaseFreeList.scala`：被消除的 mov 不分配寄存器（`allocateReq := needIntDest && !isMove`），架构头指针 `archHeadPtr` 同样跳过 mov，空闲表头指针靠快照或从架构头指针回走恢复——与本实现的 `free_head_commit` 思路一致；引用计数本身（计数宽度、上限、推测/架构是否分开）在读到的源码里没有找到（`MEFreeList.scala` 里只有一条提到 refCounter 的过期注释），**没有确认**。文献上"重命名时计数"的做法能精确判断上限，但计数是推测的，冲刷时要回滚（快照或回走 ROB）；本实现只数架构表项，免回滚，代价是上限判断保守、提交端每拍要做 8 个提交槽的计数算术（面积的主要来源）。
- **模型近似/未覆盖**：① 同一拍里提交带目的寄存器的指令与分支误预测同拍，ME 模式下会 `Assert`（原空闲表检查本来就当作不可达；门禁、大程序、Linux、SPEC 均未触发）；② `add rd, rs, x0` 不处理（工具链不生成压缩 `c.mv`）；③ 面积没有计入计数器触发器；④ Linux 启动（RTL，逐条对比）已到 `rv32 login:`，0 不一致，没有总周期数；⑤ 没有做真实时序，只有上面的门级数（`ren` 63 → 130 级）；提交端 8 路计数算术没有单独评估。
- **结论**：功能正确、关闭时零影响，但收益在噪声量级（quick SPEC +0.06%，coremark −1.15% 周期），面积 `ren` +10%。按负责人决定默认开启并合入；如果以后面积成为约束，把 `CFG_MOVE_ELIM` 设为 0 即可去掉。
- **后续**：若要提高收益，可放宽"源来自同组旁路不消除"的限制；3 位计数器的面积收益和 `ren` 的关键路径需要有工艺库的综合才能评估。
- **复现**：trace-model `gmake LDFLAGS="-lz"`（默认开）、`ME_CHECK=1 build/simulator rtl/programs/big/coremark.bin`；关闭 `gmake EXTRA_CXXFLAGS="-DCFG_MOVE_ELIM=0" BUILD_DIR=build_off`；quick SPEC `scripts/spec/replay.sh quick`；RTL `make cfg`（取 trace-model 默认）、`scripts/fm_gate.sh`、`scripts/tm_cycles.sh <simulator>`（重新生成 `ref_cycles.txt`）。

---

## EXP-010 BPU 预测延迟：现有模型每个 taken 分支 0 气泡，换成真实延迟后 IPC 掉多少

- **日期**：2026-11-06
- **分支**：trace-model `exp/realistic-timing`（工作区 `trace-model-timing`，基于 main `88e5254`，改动未提交）。
- **问题**：`BPU::comb` 在一拍里完成 type 表 → 8 bank TAGE → BTB → RAS → next_pc（`rtl/docs/modules/bpu.md` 第 3 节），阵列是异步读的寄存器堆，约 10^6 位，NLP/2-ahead 和 SRAM 延迟模型已作为死代码删除（`16a0774`、`e99145a`）。也就是说模型里每个 taken 分支 0 气泡。1 GHz 下做不到；真实设计是"1 周期小表 + 多周期主预测器 override"。这对 IPC 估计偏乐观多少？
- **开关**（默认 0，关闭时 gate 与基线逐个相同：dhrystone 162,033 周期不变）：
  - `BPU_BUBBLE=B`：预测 taken 的取指组之后，BPU 空转 B 个周期（`bpu_instance.bubble()` 让前端的 `bpu_can_run` 为假）；
  - `BPU_UBTB=N`：N 项直接映射、12 位 tag 的 1 周期目标表（索引取取指组基址）；命中且目标与主预测器一致则免气泡；陈旧命中（主预测器说不跳）也吃气泡并失效。
- **微基准**（`tests/ubench/`，`scripts/ubench.sh`，两个迭代数相减）：L1D 命中 load-to-use **4.0 周期**；store→load 转发链 5.0（转发也是 4 周期）；2 条指令的循环、16 个连续跳转、call/ret 都是 **1 周期/taken 分支**（0 气泡）；同目标 `jr` 3 周期/2 个 taken（间接跳转多 1 气泡，基线就有）；50% 随机分支约 **11.6 周期/次误预测**。所以 load-to-use 和误预测恢复延迟本身是合理的，问题只在预测延迟。
- **负载**：8 个程序（perlbench gcc mcf hmmer sjeng gobmk astar h264ref），SimPoint 覆盖 25% 权重，共 30 个点，每点 1000 万预热 + 1000 万测量；基线为现有 `tm/res_dram60`（同一份代码，周期逐点相同）。`scripts/spec/timing_eval.sh`、`timing_eval_all.sh`，结果在 `tm/tim_{b1,b1u64,b2}`。

| 配置（IPC 相对 0 气泡基线） | 几何平均 | perlbench | gcc | sjeng | gobmk | hmmer | astar | mcf | h264ref |
|---|---|---|---|---|---|---|---|---|---|
| 每个 taken +1 气泡，无 uBTB（2 周期预测器） | **−6.8%** | −19.1% | −21.7% | −8.3% | −4.6% | −5.0% | −2.6% | −1.6% | −0.4% |
| +1 气泡，加 64 项 uBTB | **−2.2%** | −5.2% | −6.7% | −4.2% | −2.9% | −0.1% | −0.9% | −0.5% | 0.0% |
| 每个 taken +2 气泡，无 uBTB（3 周期预测器） | **−13.5%** | −33.1% | −34.5% | −17.6% | −10.7% | −12.4% | −6.8% | −3.2% | −1.9% |

- **结论**：现有所有 IPC 数字相对"可实现的预测器"偏乐观；2 周期预测器约 −7%，3 周期约 −13%，perlbench/gcc（代码足迹大、taken 分支多）最敏感，超过 −19%。一个 64 项的 1 周期 uBTB 能拿回约三分之二（−6.8% → −2.2%），但 perlbench、gcc 仍有 −5%~−7%，说明 uBTB 容量值得单独扫（128/256/512）。预测器需要 uBTB 或同类的快速路径，这是便宜且收益确定的方向。
- **模型近似**：① uBTB 用主预测器的输出训练，真实硬件用解析结果训练，命中率偏乐观；② 主预测器的"B 个气泡"是整体常数，没有区分条件分支/间接/返回，也没有 TAGE 在 override 时与 uBTB 方向不一致的重定向惩罚；③ 间接跳转额外那 1 个气泡没有建模；④ 每个程序只有 2~8 个点（perlbench 只有 2 个，范围 −7.8%~−29%），程序级数字噪声大，几何平均较稳。
- **没做**：uBTB 容量/相联度扫描；NLP/2-ahead；LSU 的同拍组合链（`rtl/docs/modules/lsu.md` 第 1.1 节，是时序问题，不影响模型周期）；TAGE 容量与历史长度（4 个表，历史 {8,13,32,119}）。
- **复现**：`gmake LDFLAGS="-lz" BUILD_DIR=build_base DS3_DIR=… DS3_LIB=…`；`BPU_BUBBLE=1 BPU_UBTB=64 bash scripts/spec/timing_eval.sh <tag> BPU_BUBBLE=1 BPU_UBTB=64`；微基准 `bash scripts/ubench.sh $PWD/build_base/simulator`。

---

## EXP-009 L1D 数据预取器与指令侧预取

- **日期**：2026-11-06
- **分支**：trace-model `exp/prefetch`（研究快照 `27a878f`）→ `exp/prefetch-h1`（冻结版，默认开）；rtl `exp/l1d-prefetch`（RTL 实现，`PF_EN`）。`scripts/pf/` 里有评测脚本、`scripts/pf/cloud/` 里有云上批量运行脚本。
- **问题**：在 DRAMsim3、不分频的新基线上，加一个"能在电路上实现、状态能数清楚"的预取器能带来多少性能？分别放在 L1D 数据侧和 I-cache 侧。次要目标：总结用 agent 迭代做架构探索的经验，以及 trace-model 自身的提速方向。

### 1. 先回答"流量建模够不够真实"（预取实验的前提）
- **已经真实**：DRAMsim3 有 bank/行缓冲/刷新/读写切换，实测 mcf 平均读延迟 113 ns（最大 577 ns）、libquantum 85 ns；L1D 的 tag/PLRU 是真的，所以污染看得出来；预取行挤掉的脏行会走写缓冲变成 DRAM 写；模型跟着错误路径访存，错误路径上的预取也会污染。
- **不够真实**：① 单核带宽用不满（mcf 约 1.5 GB/s、libquantum 约 2 GB/s，DDR4-3200 峰值 25.6 GB/s，`rd_stall` 为 0），无用预取"占带宽"测不出来，只能通过延迟体现（按用户要求不做流量注入器）；② 原来预取和普通读完全同级（L1D MSHR 按下标发、互联对 master 轮转），没有优先级；③ L1D 看不到访存指令的 PC；④ 预取跨页要走 DTLB 和页表遍历，没建模，所以预取限定在 4 KiB 页内；⑤ LLC 自带的预取默认关，只在 LLC 完全空闲时发、同时只允许 1 个在飞；⑥ DRAM 是单通道 8 个 bank、60 ns 附加延迟是常数；⑦ 预热长度由检查点间隔固定为 1000 万条，不能缩短（`--restore-stub` 强制要求）。

### 2. 实现（均为 trace-model 的电路风格，可在 RTL 里对应）
- **预取器框架**（`MemSubSystem/include/Prefetch.h`、`DataPrefetcher.h`）：状态只能由带位宽声明的 `PF_ENTRY` 表项、`pf::Table`、`pf::Fifo` 组成；写入时按声明位宽截断；每个表有固定的读/写/CAM 口数，**一周期内超过就直接中止**（这条规则抓出过两个真实的端口冲突）；状态总量自动统计并受 4 KB 预算约束；comb 只读状态、seq 才更新。
- **L1D 侧接入**（`RealDcache.cpp`、`MSHR.cpp`）：
  - 训练事件在 stage2 产生（load 未命中、首次命中预取行），**先打一拍寄存**再用，预取逻辑不在 L1D 命中判断的关键路径上；
  - 预取请求进独立的 8 项 FIFO；**tag 探测借用空闲的 load 口**，和普通访问一样要抢 bank，优先级最低；
  - 探测命中就丢弃，未命中才占 MSHR；MSHR 向 AXI 发请求时**普通读优先**；普通读撞上在飞的预取项时，该项升级为普通填充；
  - L1D 每行加 1 位"预取未用"标记（首次使用时清零并产生训练事件，被换出时产生"无用预取"事件）；
  - **预取目标可选 L1D 或 LLC-only**：LLC-only 的 MSHR 项响应回来直接释放、不进 L1D，释放时给 LSU 发一个"MSHR 空出"事件。
- **算法**（运行期参数 `PF_*`）：`ALGO=1` next-line；`2` 步长（64 项直接映射表，每项 41 位；按 PC 哈希索引，但见上面的 bug，实测过的版本等价于全局步长，`PF_NOPC=1` 可显式选择）；`3` Best-Offset（256 项 RR 表 + 26 个候选偏移的得分）；`4` 步长 + BO；`7` 仅 LLC next-line 引擎。另有与主算法正交的 **LLC 次级 next-line 引擎**（`PF_NLLC`，每次 L1D load 未命中顺带把后 N 行带进 LLC）、**准确度限流**（统计"首次使用"与"未用被换出"两类事件，每 256 个事件调整度数等级）、预取距离 `PF_DIST`、度数 `PF_DEGREE`、MSHR 保留项 `PF_RESERVE`。
- **LSU→L1D 的 PC 哈希**（10 位）：给 `LoadReq`、LDQ 项、L1D 流水寄存器各加一个字段，仅步长预取器使用。**注意（2026-11-06 发现的 bug）**：LSU 里取 PC 用的是 `inst->pc`，这个字段对 load 没有被填，恒为 0，真正的 PC 在 `inst->dbg.pc`。所以下文所有"IP-stride"结果（标 `cl_*`/`a2`/`f3`/`g*`/`h*` 的配置）**实际是"全局步长检测器"**：64 项表只用了第 0 项，所有 load 的 miss 流混在一起判断步长。修复后（`pc_*` 配置，真实 PC）的结果见第 4 节，**没有更好**。
- **指令侧**（`front-end/icache/include/IPrefetch.h`）：I-cache 数组只存 tag/valid，指令数据来自功能内存，所以预取 = 一次独立 AXI id 的读 + 响应回来写 tag/valid。两种候选：`IMODE=0` 对每次需求 miss 顺带预取后续行；`IMODE=1` FDIP，一周期扫一个取指地址 FIFO 里的未来地址，用从需求翻译里学到的小 µTLB 转成物理地址。最多 4 个预取同时在飞（AXI id 12~15），需求 miss 优先。

**模型近似（要记住）**：① 探测"目标行是否已在 L1D"在模型里读 tag 阵列；硬件上是借用空闲 load 口的那一次 tag 读，已按这个写，不再多出端口；② PC 哈希在模型里直接取自 uop 的 `pc`，硬件上要么在 IQ/LDQ 项里多带 10 位、要么从 FTQ 多读一个口，这部分成本记在第 6 节；③ LLC-only 预取占用 L1D 的 MSHR 项但不占 L1D 行，MSHR 在模型里没有数据缓冲，硬件上每个 MSHR 项要配一个 64 B 填充缓冲，所以"MSHR 数量"的成本被低估了；④ DRAM 附加延迟仍是固定的 60 ns；⑤ 指令侧 FDIP 的 µTLB 只学需求路径的翻译，不能预取没翻译过的页（约 24% 候选因此被跳过）。

### 3. 评测方法
- **选点**：从 `res_dram`（580 个 SimPoint）里，在访存重的程序里取"权重×CPI"最大的点，共 20 个：mcf 5、libquantum 4、astar 3、omnetpp 2、xalancbmk 2、bzip2 2、gcc 2；**14 个训练点 + 6 个留出点**（mcf 2、libquantum 1、astar 1、xalancbmk 1、gcc 1），调参只看训练点，留出点只用来确认。另有**守卫集**（计算密集：hmmer 2、h264ref 2，加 perlbench/gcc/gobmk/sjeng 共 14 个点）验证预取不拖累不需要它的程序，指令侧另用 10 个代码重的点。
- **指标**：每个点 IPC 相对"关闭预取"的比值，取几何平均；每个点 2000 万条指令（1000 万预热 + 1000 万测量）。
- **执行**：本机 8 并行 → 后期放到 3 台阿里云（Xeon 6982P-C，32 vCPU）；云上重编了 softfloat（用 git 历史里的 Linux 版）和模拟器，5 个校验程序的周期与 Mac 逐个相等，**云上与本地的 14 个训练点周期逐点完全相同**。

### 4. 结果

**数据侧演进（训练集 14 点，几何平均加速）**

| 配置 | 加速 | 说明 |
|---|---|---|
| next-line 度数 4 | +20.4% | mcf +10% 但 astar/bzip2 变差 |
| IP-stride | +23.2% | |
| Best-Offset | +25.6% | libquantum 最好，mcf +3.6% |
| BO + 准确度限流 | +26.5% | 消除了 astar/bzip2 的亏损 |
| BO + 限流 + 预取可用全部 MSHR（`RESERVE=0`） | +29.9% | 其他程序没受损 |
| BO + 限流 + LLC next-line（1 行） | +32.9% | mcf 收益来自 LLC |
| 步长 + 限流 + 度数 8 + LLC next-line（2 行） | +35.4% | |
| 加距离 2、LLC 行数改 1（**h1**） | **+37.9%** | 最终配置 |

**最终配置 h1**：`ALGO=2 THROTTLE=1 DEGREE=8 RESERVE=0 NLLC=1 DIST=2`（**全局**步长检测器（PC 哈希恒为 0），训练在 load 未命中和预取行首次使用上，距离 2、度数 8，准确度限流，预取可占满 8 个 MSHR，另有 LLC 次级引擎预取后 1 行）。

| | mcf | libquantum | astar | omnetpp | xalancbmk | bzip2 | gcc | 几何平均 |
|---|---|---|---|---|---|---|---|---|
| h1，20 点（云上，当前代码） | 1.145 | 3.399 | 1.038 | 1.037 | 1.166 | 1.007 | 1.003 | **1.3557** |
| 训练 14 点 | | | | | | | | 1.3786 |
| **留出 6 点（调参时没看过）** | | | | | | | | **1.3036** |

训练集的 +37.9% 带有选优偏差，**对没见过的点的估计是 +30%**。留出集上各配置排序不变：h1 +30.4% > g2 +28.1% > g4 +27.9% > f3 +25.6% > Best-Offset +24.0% > 基础步长 +16.4%。

**守卫集（计算密集，14 点，h1 对关闭预取）**：几何平均 **+0.5%**，最差单点 −0.5%（gobmk）；hmmer +0.1%、h264ref +0.1%~+0.6%、gcc +0.5%~+1.0%、sjeng 0%。预取不拖累计算密集的程序。

**几个有结构意义的对比**
- **预取必须填进 L1D（流式）**：BO 的远处几行改成"只填 LLC"，libquantum 从 ×2.65 降到 ×2.27。
- **LLC 次级 next-line 是 mcf 的关键**：只做"LLC next-line"就让 mcf +16%（L1D 里用不上，它们是被换出后命中 LLC 的）；但 LLC 行数从 1 行加到 2、4 行反而更差（mcf 1.190 → 1.168 → 1.140），跳过紧邻的下一行（`NLLC_DIST=2`）也更差。
- **IP-stride 比 Best-Offset 更好**：同样带 1 行 LLC next-line 时，训练集 +36.3%（步长，g4）对 +32.9%（BO，f2）；留出集上 h1 +30.4% 对不带 LLC 引擎的 BO（e0）+24.0%。步长 + BO 的组合反而不如单独步长（训练集 +33.6% 对 +35.4%，−1.8 个百分点）。
- **准确度限流**对阈值不敏感（放宽到 60/25 完全相同），但有无差别很大（astar −3.7% → +1.5%）。
- **libquantum 卡在"在飞请求数"**：BO 配置下所有变体都是 ×2.646，用 6 个可用 MSHR × 64 B / 113 ns ≈ 3.4 GB/s 恰好等于实测带宽。放开保留项（8 个 MSHR 全可用）→ ×2.95，MSHR 总数加到 16 → ×3.54（h1，相对同样 16 个 MSHR 的基线整体 +37.2%，比 8 个时只多 1.6 个百分点），**说明主要瓶颈是在飞预取数**，但翻倍 MSHR 的面积（每项带 64 B 填充缓冲）对整体收益不划算。
- 预取行低优先级插入（不更新 PLRU）：+0.1%，不采用；度数 4（对 8）使 libquantum 从 3.34 掉到 2.79，度数 8 必要。
- **指令侧**：I-cache 的 miss 惩罚周期占总周期 30%~50%（perlbench、gobmk），每次约 13 周期（LLC 命中）。next-line 预取是**负收益**（度数 1/2/4：−0.75%/−0.89%/−1.23%，因为 miss 多在分支目标和调用处，且部分触发来自错误路径，预取的行挤掉了有用行）；FDIP（4 个在飞，µTLB 16 项）把 I-cache miss 降了 21% 但周期只少约 1%，几何平均 **+0.4%**；叠加在 h1 上整体 **−0.1%**。**结论：指令侧预取暂不采用**，I-cache miss 惩罚大部分被后端的访存等待掩盖。

**修复 PC 之后（真实 PC，8 位步长，不跨页，20 点云上重跑）**：真实 PC 版本**没有更好**，略差：h1 20 点 +35.6%（全局）→ +34.9%（真实 PC）；mcf 不变（×1.145 对 ×1.146）；libquantum ×3.399 → ×3.376；xalancbmk ×1.166 → ×1.098（流被按 PC 拆开后训练更慢、哈希冲突）；bzip2 +1.8%。g4/f3/基础步长同样略差。**所以全局步长既更好又不需要从 LSU 传 PC**，设计更便宜（省掉 LDQ 里 64×10 位和 L1D 流水线里的连线）。

**指令侧上限**（把 I-cache 做到几乎无 miss，128 路，`CFG_ICACHE_WAYS`）：10 个代码重的点几何平均 **×1.053**（perlbench ×1.080、gobmk ×1.126、sjeng ×1.023、gcc ×1.001；单点最高 gobmk sp24 ×1.159、perlbench sp25 ×1.148，perlbench sp25 的 miss 309,840 → 11,824）。这就是**阻塞式 I-cache 全部代价的上限**；FDIP 只拿到 +0.4%。

**其他三个云上批次**：MSHR 16 + 预取保留项 2 对比保留项 0：+0.2%（无意义）；h1 叠加 FDIP 的三种参数（4 个在飞 µTLB 16/64 项、2 个在飞 µTLB 32 项）相对 h1：−0.02% ~ −0.13%，指令侧 FDIP 在数据侧预取之上没有增益。

### 4b. 为什么 mcf 的收益低（2026-11-06 研究）

mcf 的 5 个点 h1 的提升只有 ×1.07~×1.25。研究用了一个仅在 `-DPF_STUDY` 下编译的探针（`PfStudy.h`，按完整 PC 统计 load miss、支持"理想 L1D"和"按 PC 理想"）。

- **上限**：理想 L1D（所有 load 命中）sp60 ×2.49、sp71 ×2.85；DRAM 附加延迟 60 ns → 0（平均读延迟 113 → 52 ns）只有 sp60 ×1.28，说明 mcf 的损失**大半在 L1D→LLC 一段**，不是 DRAM 延迟本身。L1D 未命中约 50%，其中约 82% 命中 LLC。
- **sp60 的 miss 几乎全部来自 `primal_bea_mpp` 一个循环里的 6 条 load**（99.8%）：`a5 += t1`（步长 `nr_group × sizeof(arc)`）后读 `arc->ident`（33%，物理行地址差 **+45,548 行 = 2.9 MB 占 77%**）、`arc->tail/head/cost`（约 22%，同一条 arc 的其他字段）、再读 `tail->potential` 和 `head->potential`（24% 和 21%，**依赖前面读出的指针**，行地址差无规律）。
- **按 PC 的理想上限**（只让指定 PC 的 load 命中）：sp60 完美的 arc 字段预取 **×1.91**，完美的 node 间接预取 ×1.21，两者都完美 **×2.49**（等于整体理想 L1D，说明 sp60 的损失全在这个循环）；sp71 里这个循环只占 ×1.32（arc ×1.22、node ×1.04），其余在 `refresh_potential`/`update_tree`/`primal_iminus`（树遍历，纯指针追逐），整体上限 ×2.85。
- **为什么步长预取抓不到**：① 步长 45,548 行远超我的 8 位步长字段（±127 行）；② 预取候选限定在 4 KiB 页内，2.9 MB 的步长必然跨页，全被丢弃；③ （PC bug，见上）；④ MSHR 饱和（h1 在 mcf 上 `probe_mshr_full` 40 万~150 万次，预取经常因 MSHR 被占满而放弃）。h1 在 mcf 上发的 110 万~200 万次预取几乎全是"LLC 后 1 行"引擎发的，步长预取只填了约 300 行。
- **加宽步长字段到 18 位 + 允许跨页（模型近似：假设相邻迭代的物理距离恒定，sp60 里 77% 成立；硬件上需要 DTLB 翻译或按虚拟地址训练）**：sp60 ×1.243 → **×1.343**、sp38 ×1.250 → ×1.361、sp71 ×1.085 → ×1.106、sp16/sp32 ×1.07/×1.09 → ×1.09/×1.11；预取准确度约 90%（sp60 填 131 万行、118 万次被用到）。所以 arc 扫描确实被抓住了，但离 ×1.91 的上限还差一截（预取距离、MSHR 并行度）。（这一组同时带了 PC 修复和负步长修复，20 点全量的拆分验证见 `gw_*`/`pw_x` 配置，云上进行中。）
- **20 点全量验证（云上，同一份代码，只动步长位宽、是否跨页、PC 与全局）**：

| 配置 | mcf | libquantum | xalancbmk | 20 点 | 留出 6 点 |
|---|---|---|---|---|---|
| h1：全局，8 位步长，页内 | 1.145 | 3.399 | 1.166 | +35.6% | +30.4% |
| 全局，18 位步长，页内（`gw_nx`） | 1.144 | 3.399 | 1.166 | +35.5% | +30.4% |
| 全局，18 位，**跨页**（`gw_x`） | 1.127 | 3.773 | 1.186 | +38.2% | +33.2% |
| 真实 PC，18 位，跨页（`pw_x`） | 1.195 | 3.720 | 1.108 | +39.2% | +33.2% |
| 按 PC 表 + 1 个全局表项（混合），18 位，页内（`hy_nx`） | 1.137 | 3.397 | 1.144 | +35.3% | +29.8% |
| 混合，18 位，跨页（`hy_x`） | 1.184 | 3.750 | 1.156 | +39.7% | +33.0% |
| 混合，跨页，预取距离 4（`hy_x4`） | 1.184 | 3.836 | 1.144 | +40.0% | +33.2% |

  结论：**单独加宽步长没有收益（页内发不出去）；决定性的是跨页**：libquantum 的顺序流跨页后 ×3.40 → ×3.75，mcf 的 arc 扫描只有跨页 + 宽步长才能抓到；**页内版本不论是全局、按 PC 还是混合，都停在 +35% 左右**；跨页后三种设计在留出集上几乎一样（+33%），混合多花的一个表项没有换来收益。全局步长对 xalancbmk 好（多流混在一起反而稳），按 PC 对 mcf 好（多个循环各有各的步长），两者互补，但互补的幅度（约 +0.4 个百分点）不值得多一份表。**跨页是模型近似**（用物理地址上的恒定差；硬件上要给预取目标做 DTLB 翻译，或按虚拟地址训练再翻译），成本和时序要单独评估；它能多给约 3 个百分点（留出集），而且是流式程序（libquantum）和大步长扫描（mcf）才受益。
- **剩下的是指针追逐**：node 间接访问（sp60 里 ×1.21）和 sp71 的树遍历需要"读到预取回来的 arc 行里的 tail/head 指针再去预取 node"这类间接预取，需要数据值和虚拟地址翻译，成本大，没做。

### 5. 过程中发现并修复的问题（预取代码和评测流程）
0. **LSU 传给预取器的 PC 恒为 0**（`inst->pc` 对 load 没有被填，应取 `inst->dbg.pc`），导致"IP-stride"实际是全局步长；是在做 mcf 的 PC 访问模式统计时发现的。同时发现步长生成器的负步长被错误地按无符号 8 位累加（下降的流会跑到 +255 行外），已改为有符号。
1. 预取行"是否预取"标志在最常见的填充分支漏传（脚本替换误伤），导致首次使用事件丢失、第一轮结果作废并重跑。
2. "只填 LLC"的预取项释放 MSHR 时没有给 LSU 发"MSHR 空出"事件，预取占满 MSHR 时普通读无人唤醒，ROB 死锁；同时普通读命中在飞预取项时需要升级为普通填充。两处都已修，涉及 LLC-only 的早期结果已删除重跑。
3. 次级生成器和主生成器同周期写 FIFO 超过 1 个写口，被电路规则检查抓住并修正。
4. 云上：中止的并行传输通过 rsync `--partial` 留下了损坏的检查点（只有 bzip2 sp10 一个点），模拟器在 `gzread` 里死循环；新增 `verify` 子命令校验每个检查点（含"空 gzip 也能通过 `gzip -t`"的情况）。已发布的数字不受影响。
5. 本机多次并行超过用户给定的上限（8），影响了用户使用，之后云上做评测、本机只做开发。

### 6. 面积与时序估计（第一步，粗估）

**状态（h1 配置，位数由模型自动统计）**：步长表 2624 位 + 请求 FIFO 232 + 生成器 39+31 + 限流 22 + 输入寄存器 108 = **3056 位（382 B）**，预算 4 KB 的 9%。预取器之外的成本：L1D 每行 1 位标记 256×4 = 1024 位；LSU→L1D 的 PC 哈希 LDQ 64×10 = 640 位 + 流水寄存器/连线约 120 位（**实测全局步长比真实 PC 更好，这 760 位可以整体省掉**，则合计约 4.1 Kb）；MSHR 每项 2 位 + 填充通路 2 位，约 18 位。**合计约 4.9 Kb（约 0.6 KB）**，大约是 L1D 数据阵列（64 KB）的 1%。Best-Offset 版 3546 位，同量级。

**时序（结构分析，没有综合）**：
- 预取逻辑本身：IP-stride 一次决策是"表读 → 标签比较 → 26 位减法 → 与步长比较 → 置信度更新"，训练事件已先寄存一拍，可拆成两拍；生成器每周期只发 1 个候选，没有宽比较器和宽加法。复杂度低。
- 对已有关键路径的影响集中在三处：① **tag 探测借用空闲 load 口**：需要在 load 口的 tag 读地址上多一级选择（LSU 请求地址 vs 预取地址）和"空闲口"判断，这是 L1D 查找路径，最敏感；缓解办法是 LSU 在上一拍就告知下一拍哪个口空闲；② MSHR 向 AXI 发请求从"取最低下标"变成"先取普通读、再取预取"的两级优先选择，8 项很小；③ MSHR 分配**不需要新增分配口**，预取借用空闲 load 口自己的分配槽。
- 综合没有做；这一节要等时序综合流程（TODO 中已有）才能给出 WNS。

### 7. 结论与建议
- **采用 h1 作为数据侧预取器的候选设计**：对访存瓶颈点留出集 +30%，计算密集程序无副作用，状态 0.4 KB、**不需要从 LSU 传 PC**（全局步长），总成本约 0.5 KB，不新增 tag 端口。
- **可选升级：允许预取跨 4 KiB 页**（需要给预取目标做地址翻译）：留出集再多约 3 个百分点（+30% → +33%），主要来自 libquantum 和 mcf；决定做不做取决于 DTLB 多一个探测口的成本。
- **不采用指令侧预取**（+0.4%，叠加后为负）。
- 如果要继续压榨：在飞预取数是 libquantum 的上限，"为预取单独加一小组 MSHR/流缓冲"比"把所有 MSHR 翻倍"更划算；训练也可以扩到 store 未命中。
- **未做/限制**：只测了 12 个 SPEC 程序里的 8 个，没有 Linux 启动、也没有多核；留出集只有 6 个点；FDIP 的 µTLB 太小、没试过用真实 ITLB 端口；没做指针类（CDP）预取——它需要虚拟地址和 DTLB 翻译，成本大；store 未命中没有参与训练；DRAM 单通道 8 bank、60 ns 常数附加延迟；综合与 RTL 都没做。
- **复现**：`gmake LDFLAGS="-lz" DS3_DIR=<DRAMsim3> DS3_LIB=<lib> BUILD_DIR=build_area/x`；运行期用环境变量选算法，如 `PF_ALGO=2 PF_THROTTLE=1 PF_DEGREE=8 PF_RESERVE=0 PF_NLLC=1 PF_DIST=2 PF_STATS=1`（`PF_STATS=1` 打印状态位数和各类计数）；`scripts/pf/run_eval.sh`（评测点集）、`scripts/pf/table.py`、`scripts/pf/cmp_cloud.py`（汇总比对）、`scripts/pf/cloud/fleet.sh`（云上批量运行）；结果在 `~/personal/AI-Huma-data/spec-rv32imab/tm/pfexp{,_cloud}/`。

### 8. 次要任务一：用 agent 迭代做架构探索，哪些经验有用
- **先固定评测，再让 agent 改设计**：点集、基线、汇总脚本、回归检查都不让设计迭代去动；训练/留出拆分和守卫集从第一天就有，否则"选优偏差"会悄悄进到结论里（这次训练 +37.9%、留出 +30.4%）。
- **把"电路约束"做成运行时的硬检查**，而不是靠 agent 自觉：位宽截断、每周期端口数上限、状态预算三条规则让不合理的设计直接中止，而且确实抓出了真问题。
- **每次改动都要有"关闭时与基线逐周期相同"的回归**，并且**把统计和行为分开验证**：这次最大的两个坑（标志漏传、唤醒事件缺失）都靠"统计量对不上"才发现——`issued` 应当等于 `filled`、有用 + 无用应能解释周期变化。
- **看结构性对比，不只看总分**：最有价值的发现（LLC next-line 才是 mcf 的收益来源、libquantum 卡在在飞请求数、远处行必须填 L1D）都来自"同一个旋钮在不同程序上方向相反"，不是来自最高分。
- **工程化的坑也要进经验**：评测一轮 40~50 分钟是迭代的主要成本，上云把它降到约 20 分钟；一旦并行、传输、校验出错，会悄悄污染结果（本次的损坏检查点、被删的结果文件），所以每个脚本都应该幂等、能校验、不覆盖已有结果。
- **子 agent 适合做边界清楚的只读研究**（如仿真提速调研），不适合直接改共享状态。

### 9. 次要任务二：trace-model 自身的提速方向（2026-11-06，子 agent 调研 + 实测）
报告全文在本会话的 scratchpad（`sim_speedup_report.md`），这里记结论。数字里**只有 PGO 是实测并验证了周期的，其余都是估计**。
- **时间分布**（mcf，占总时间）：`back.comb` 51%、前端 BPU/取指 16%、AXI+LLC+DDR 合计约 23%（其中 DRAMsim3 只有 3.4%~4.4%，批量推进最多省 4%）、各 seq 合计约 10%；`back.comb` 内部也很平。`memmove` 7%（很多次小结构体拷贝，单次只有几百字节）。
- **空转周期很少，整核快进收益有限**：严格"全核状态与上一周期相同"的周期 mcf 只有 1.2%、libquantum 0.25%，原因是 LSU 等 miss 时每 4 周期向 L1D 重放一次（`replay_delay_cycles`），请求编号每次递增。按"每 4 周期重复一次"的判据，可预测重复的周期占 mcf 19%、libquantum 35%；但这些周期仍要花活跃周期 60%~70% 的耗时，所以现实的快进收益只有 mcf ×1.13、libquantum ×1.27，而且要给 LSU/MSHR/L1D/TLB/ICache/BPU 各加"推进 k 周期"的接口，AXI 一侧在等 DRAM 时是在确定性演化而不是空闲，相位对齐很绕，**风险高，不建议先做**。
- **PGO（实测）**：同机并排对跑，mcf 快 10.6%~13%、训练里没有的 astar 快 11%，**周期逐位不变**（3 个小程序、完整长度的 mcf/libquantum 点；云上 gcc 构建同样通过 3 个校验程序）。云上构建用 `scripts/pf/cloud/pgo_build.sh`（`fleet.sh pgo <目录> [标志]`）：instrument 构建 → 4 个点各 500 万周期训练 → 同一目录里用 profile 重编 → 校验周期 → 并排计时；mcf 600 万周期用户时间 52.6 s → 47.0 s。thin LTO 单独约 −5%。
- **多线程**：同周期内前端 → 后端 → L1D/MSHR → AXI 是一条组合依赖链，每个活跃周期只有约 5~10 µs，同步开销占一成以上；最大的 `back.comb` 占 51%，两线程上限不到 ×1.6、现实 ×1.2~1.4；GSIM 论文里单线程 GSIM 对 8 线程 Verilator 仍快 ×1.18，说明细粒度多线程 RTL 仿真回报低。**点与点之间的并行（云上每台 20 个进程）才是高效的多核利用。**
- **写法层面的改动（均未实现）**：`Dispatch::is_preg_woken` 改位图（约 2%）、Exu/Isu 的 `comb_begin` 改脏标记（2~3%）、`TlbMmu` 备忘（2~4%）、BPU 备忘（3~6%）、去掉 `SimCpu::cycle`/`back2front` 里的冗余结构体拷贝（1~2%）、`Bridge::find` 改直接索引（约 1%）、LLC 备忘扩展（1~2%）、DRAMsim3 关 epoch 打印（≤1%）；合计估计 ×1.1~1.15。再往上是模块级"输入没变就不求值"的活动门控（GSIM/ESSENT 思路，估计再 ×1.1~1.25，中风险）。
- **允许误差时的选项**（未测）：用功能模型做预热代替 1000 万条详细预热（约 ×1.8，误差通常 1%~2%）；筛选阶段缩短测量窗口、只跑敏感点；AXI/LLC/DRAM 放另一个线程并加固定一拍延迟（×1.2~1.3，延迟可补偿）；区间/解析模型误差过大不适用。验收线建议：近似版本的"提升比"偏差 <0.5 个百分点且配置排序不变。

迟 `CONFIG_SIM_DDR_LATENCY_CALC` = 86 ns。改成 60 ns 后 dhrystone/coremark 的平均读延迟约 85–87 ns，与 86 ns 吻合（32 ns 时 56–58 ns，memory-stress-small 81 ns → 105 ns）。`DS3_EXTRA_NS` 仍可覆盖。

DDR 配置：DRAMsim3 `DDR4_8Gb_x16_3200`（tCK 0.63 ns，CL/tRCD/tRP 22，1 通道、64 位、2 bank group × 4 bank、BL8、open page、地址映射 `rochrababgco`、rank 级交错刷新），与 `config.h` 里原来的 CL 22 / tRCD 22 / tRP 22 / 1600 MHz 一致。

| 程序 | 32 ns | 60 ns |
|---|---|---|
| dhrystone | 158,756 | 162,033 |
| coremark | 250,658 | 255,335 |
| memory-stress | 2,425,029 | 2,428,470 |
| smc-div | 11,096 | 11,348 |
| smc-addi | 10,966 | 11,218 |
| memory-stress-small | 343,975 | 347,305 |

`baseline.csv` 63 个程序：周期平均 +23%、中位 +28%、最大 +36%；gate 62/62。RTL：`ref_cycles.txt` 重新生成，`fm_gate.sh` 66/66、66 个周期与 trace-model 全部相等；Linux 从复位启动到 `rv32 login:`（`RQD=8`，无断言、无不一致）。trace-model 上 LLC 读响应队列峰值：master 1 排队 3 + 输出寄存器（32 ns 时 4 + 1），`RQD=8` 仍够用，延迟变高反而排队更少。

SPEC 全量回放（580 点，无失败，无 difftest 不一致；`tm/res_dram60`，12 路并行）：

| 程序 | 加权 IPC | 估算分数@1GHz | 32 ns 的 IPC |
|---|---|---|---|
| 400.perlbench | 2.092 | 8.08 | 2.131 |
| 401.bzip2 | 1.600 | 7.13 | 1.645 |
| 403.gcc | 1.474 | 9.32 | 1.590 |
| 429.mcf | 0.405 | 12.62 | 0.463 |
| 445.gobmk | 1.763 | 8.85 | 1.783 |
| 456.hmmer | 3.720 | 9.75 | 3.718 |
| 458.sjeng | 1.834 | 8.44 | 1.858 |
| 462.libquantum | 0.663 | 4.73 | 0.857 |
| 464.h264ref | 1.475 | 6.08 | 1.489 |
| 471.omnetpp | 1.333 | 6.92 | 1.508 |
| 473.astar | 0.928 | 7.00 | 0.975 |
| 483.xalancbmk | 1.873 | 12.04 | 1.959 |
| **几何平均** | **1.396** | **8.12** | 1.487（分数 8.66） |

quick 的 6 个程序（旧基线 `tm/b3` 同一批点）：几何平均 IPC 旧（16 倍分频）2.204 → 32 ns 1.613 → 60 ns 1.550。分数的换算方法和局限见上面"估算分数"一段（参考时间是凭记忆写的，未核对官方表）。

综合前后对比（2026-11-06，Yosys + yosys-slang 的相对面积代理，`scripts/synth_module.sh`，`SYNTH_LIGHT=1 SYNTH_MEM=1`；改动前 = `main`/`exp/batch3` 的 rtl，改动后 = `exp/dram-sim`；**不是工艺库面积、没有时序**）：

| 模块 | 改动前 | 改动后 | 变化 | 原因 |
|---|---|---|---|---|
| `axi_llc_rq`（每个读主设备一份） | 10,439 单元 / 2,584 触发器 | 18,768 / 4,649 | +8,329 / +2,065（+80%） | `RQD` 4 → 8 |
| `axi_llc`（整个 LLC，`NR=4` 个读主设备） | 489,436 / 22,324 | 522,758 / 30,584 | **+33,322 / +8,260（+6.8% / +37%）** | 4 × `axi_llc_rq` 的增量，吻合 |
| `lsu_dc_req_st` | 86,150 / 0 | 62,755 / 0 | **−23,395（−27%）** | store 窗口 20 → 15 |
| `dcache_resp`、`axi_cpu_port_chan` | 14,113 / 38；59 / 24 | 相同 | 0 | 单独综合时 `phase0`、`phase_last` 是悬空输入，看不出常量化的效果 |

净变化约 +9.9k 单元（+33.3k − 23.4k），相对整机推算的约 952 万个门不到 0.2%；触发器 +8,260，相对整机约 18.1 万是 +4.6%，全部来自 `RQD`。`mem_top` 的 `TICKS == 1` 常量化（去掉 16 tick 折叠逻辑）预计是减量，但 `mem_top` 太大，Yosys 超时，没有测到。每增加一项 `RQD`，4 个队列合计约 +8.3k 单元（`RQD=5` 即最小可用值约 +8.3k，`RQD=6` 约 +16.7k，`RQD=8` 为 +33.3k）。

### 10. 冻结版 h1 与 RTL 实现（2026-11-06）
- **冻结版**：trace-model `exp/prefetch-h1`（从研究快照 `exp/prefetch` `27a878f` 切出，`0eb258c`；默认开 `1fe92b5`）。单表项全局步长（8 位有符号步长，2 位置信度，度 8、距离 2，页内）+ 1 行 LLC-only next-line + 8 项请求 FIFO；无 PC、无限流、无 BOP、无 I 侧预取、无研究开关。`PF_ENABLE=0` 关闭。状态约 0.4 KB（FIFO 8×27 位、步长表项、两个生成器、训练输入寄存器）+ L1D 每行 1 位（1,024 位）。
- **与研究版 rv_s2 的差别**：步长 8 位有符号（研究版曾把负步长截成无符号）；因此冻结版的 20 点数字不会与 rv_s2 逐位一致，**云上 20 点复跑尚未做**（服务器已关），引用的 +35.5% / +30.6% 仍是研究版 rv_s2 的数字。
- **关闭时周期不变**：trace-model gate 62/62 与旧基线逐个相同（`results/baseline/baseline_nopf.csv`）；64 KiB LLC 的 5 个测试与 main 相同。
- **开启时**（默认）：gate 62/62 对照新 `baseline.csv`；dhrystone 162,033 → 161,183（−0.5%），coremark 255,335 → 256,573（+0.5%），memory-stress 2,428,470 → 2,383,063（−1.9%），memory-stress-small 347,305 → 334,635（−3.6%；64 KiB LLC 下 971,687 → 632,880）。小程序里 25 个周期有变化。
- **RTL**（rtl `exp/l1d-prefetch`，规格 `rtl/docs/modules/dcache_pf.md`）：新 `dcache_pf`、L1D stage1 探测槽、stage2 事件、MSHR 的 `is_prefetch/no_fill`/提升/两遍 AXI 选择/无填充释放、阵列 pf 位、LSU 到 L1D 的 `replay` 位（训练要排除 LSU 重放；原 RTL 接口里没有）。`PF_EN=1`（默认）：门禁 66/66 逐条对比通过，**66 个程序周期与 trace-model 逐个相等**；`PF_EN=0`：66/66，周期与旧基线相同。面积代理：`dcache_pf` 3,334 单元、422 触发器，阵列 +1,024 触发器，`dcache_mshr` 95,540 → 95,020（噪声内）；工艺库、WNS 未做。
- **RTL 里发现的实现错误**：`always_comb` 多驱动（预取器从不入队）、`no_fill` 标志没有和 `pf` 相与（需求项被误标，dhrystone 差 2 周期）。逐周期定位办法：两边各打印 `take/alloc/relnf` 事件序列后对比。
- **未做**：`axi_llc` 读响应队列 RQD（现 8）在预取下的重测；冻结版 SPEC 20 点复跑；跨页预取（要 DTLB 翻译）；时序。

### 11. 全量 SPEC、坏点原因与控制实验、合入（2026-11-07）

- **全量 SPEC（579/580 点，fast warmup，对比 2026-11-05 精确 PF 关基线）**：按 SimPoint 权重的 12 个程序几何平均 **+8.2%**（libquantum +96.3%、mcf +10.8%、gcc +9.0%、bzip2 +6.2%、h264ref +2.7%、perlbench +2.7%、astar +2.3%、omnetpp +0.9%、xalancbmk −0.2%、gobmk −0.8%、hmmer −1.6%、sjeng −3.0%）；579 个点不加权的几何平均 +11.2%。fast warmup 的系统偏差约 −0.5%（绝对 IPC）、对"预取加速比"约 −0.3 个百分点，方案之间的差异同口径可比。缺 1 个点：`400.perlbench ckpt_sp11_target184332`（服务器端 stub 恢复失败，本地 gz 完好），未补。
- **坏点是真的，不是 fast warmup 的假象**：12 个最差点用精确预热重跑，omnetpp sp22 −40.7%（fast −40.9%）、gcc sp38 −29.9%、xalancbmk sp34 −22.2%；只有 hmmer、sjeng 和 xalancbmk sp30 的约 −5% 是 fast warmup 造成的（精确预热下约 0%）。全量里低于 −10% 的点共 5 个（约 0.9%）。
- **原因**：LLC-only 的 next-line 引擎在这些点上发出几十万个预取、真正被用到的只有几百个（omnetpp sp22：发出 50 万、用到约 500）；关掉该引擎后 12 个点中 10 个回到 0% 附近。omnetpp 的伤害是 MSHR 争抢（`probe_mshr_full` 52 万次），gcc sp38 是 DRAM 带宽或 LLC 污染（MSHR 预留无效）。xalancbmk sp15 例外：关掉引擎反而更差（−11.8% → −21.3%）。但引擎也是 mcf（+10.8%）、gcc、bzip2 收益的主要来源。
- **控制实验（都没有进入源码树，补丁在 trace-model `docs/experiments/exp009_llc_engine_control.patch`，开关 `PF_LLC_THR/PF_LLC_WIN`、`PF_RES_LLC`、`PF_DUEL_SLICE/PF_DUEL_EXPLOIT`）**：
  1. 准确率节流（256 位过滤器记"本该预取的行"，每窗口命中数低于阈值则关）：THR=6、窗口 32 最好，最坏点压到 omnetpp sp22 −1.2%、gcc sp38 −8.1%，但 mcf 只剩 +2.1%（第一版 64 位过滤器假命中约 40%，永远不关，无效）。
  2. LLC 预取探测时预留 MSHR：预留 6 才修好 omnetpp sp22（−4.4%），mcf 同时降到 +0.6%；对 gcc sp38 基本无效。
  3. 时间片对抗（轮流开/关 LLC 引擎，比较 demand 访问数/周期）：片长 131072 周期、生效 8 片，mcf +7.7%，但 gcc sp38 仍 −28%、omnetpp sp22 −14%。
  全量对比：h1 **+8.2%**，THR=6 +7.2%，对抗 +7.7%；低于 −10% 的点 5 / 2 / 4 个，最差点 −40.9% / −23.6% / −28.3%。**结论：平均收益 h1 最高、硬件最简单，保持 h1 原样合入**；mcf 与坏点此消彼长，没有哪个静态阈值或简单反馈能同时保住。xalancbmk sp34（−22%）原因与 LLC 引擎无关，未查。
- **评测基础设施**：稀疏检查点恢复（只恢复非零页，RSS −62% 到 −96%，结果逐字节相同；function-model `exp/sparse-mem`）；fast warmup（EXP-011 的 `--fast-warmup`）并入后单点墙钟约 1.75 倍快；云服务器 32 核/121 GB 全量约 1 小时；并发超过内存（40 以上的 4.7 GB 进程）会 OOM（rc=137）。
- **合入**：2026-11-07 合入本地 main（未推送）。合并时 main 已有 move elimination（EXP-012），基线用合并后的树重新生成；预取关与 main 基线 62/62 相同。

### 后续

- **已决定（2026-11-05）：不分频 + DRAMsim3 + 默认 1 GHz 作为新基线**（trace-model 侧已完成：`config.h` 默认 `FREQ_DIV=1`、`CPU_FREQ_MHZ=1000`，Makefile 默认 `DS3=1`，`baseline.csv` 已重生成，gate 62/62，大程序标准周期见 trace-model `docs/PROJECT.md`）。新旧基线周期对比：gate 平均 +146%、中位 +135%，dhrystone 150,427 → 158,756，coremark 233,515 → 250,658，memory-stress 1,541,195 → 2,425,029，memory-stress-small 189,128 → 343,975。RTL 侧已同步（见下一节），66 个程序周期与 trace-model 全部相等。
- 开启 difftest 逐条比较重跑 gate；用 Linux 启动片段、SPEC 检查点（不要用 cjpeg/linear_alg/parser/sha）测带宽和 bank 冲突敏感的负载。
- 校准附加延迟，或与 RTL 闭环里的 SimDDR 对齐；试 DRAMsim3 的地址映射和 open/close page。
- RTL 其他 store 队列窗口（`wait_mmu_stq`、`mmu_done_stq`）与 trace-model 的 15 不一致，需给 `ring_apply` 带窗口参数。
- RTL 侧合入 `main` 前还要跑 Linux 启动（`SOC_FM=1 SOC_TB_SEMIHOST=1`，数小时）和综合对比。
- Ramulator 2.0 作为后备，未试。

## EXP-008 decode 宽度 8 降到 6

- **日期**：2026-11-05
- **分支**：trace-model `exp/decode6`（改动未提交，工作区 `trace-model`）
- **问题**：前端一次给 8 条，后端 decode/rename 改成 6 宽（issue 宽度由 FU 个数决定，本实验未动 FU），性能代价多大？
- **方法**：`config.h` 新增 `CFG_DECODE_WIDTH`（默认 8）、`CFG_ROB_BANK_NUM`（ROB 行宽 = commit 宽度，默认等于 decode 宽度，可以更大）；放宽两处断言。**顺带修了 `make_rob_idx`**：原来用 `(line*BANK)|bank`，BANK 不是 2 的幂时索引错、ROB 死锁，改为 `+`（BANK=8 时等价，gate 62/62 不变）。ROB 每行放一个 decode 组，容量按行数算：6 宽时 ROB=126（21 行）；行宽 8 时 ROB=176（22 行），使行数相近。默认配置 gate 62/62；两种 decode=6 配置 62 个小程序 difftest 全过、无死锁。
- **负载**：quick SPEC（6 个程序，129 个点），基线为第 3 批（EXP-005）。

| 程序 | decode 8 | decode 6（commit 6，ROB 126） | 变化 |
|---|---|---|---|
| perlbench | 2.468 | 2.414 | −2.2% |
| gcc | 2.566 | 2.570 | +0.2% |
| mcf | 1.327 | 1.315 | −0.9% |
| hmmer | 4.007 | 3.513 | −12.3% |
| sjeng | 2.027 | 2.008 | −0.9% |
| h264ref | 1.677 | 1.648 | −1.7% |
| 几何平均 | 2.204 | 2.136 | −3.1% |

- **拆分实验**（只跑 hmmer，24 个点）：decode 6、commit 8、ROB 176 → IPC 3.434（−14.3%），没有比 commit 6 更好。commit 宽度不是原因；那 2% 的差别原因未查（推测行宽 8 时每行有空槽）。
- **原因**（埋点 `CFG_DW_HIST`：每拍 decode 取走几条；每拍被计两次，已按 IPC 校准，只看占比）：hmmer 有基线 IPC 5.8–6.4 的点，这些点掉 19–21%；sp5（IPC 6.42→5.07）decode 8 时 77% 的周期取满 8 条，6 宽就是硬上限；sp4（3.52→3.14）呈“取满 8 或取 0”的双峰，后端停顿后 decode 追赶变慢。两个点里队列积压超过 12 条的周期都 >90%，前端不是瓶颈。decode 取 0 条的周期占 20–40%（后端反压），具体哪项资源满了未查。
- **结论**：decode 6 对多数程序约 −1%，对 hmmer 这类高 IPC 程序 −12% 以上，无廉价补救。**不合入，保持 8。** 未做：decode 7；FU 裁剪（瓶颈在 decode，单独裁 FU 只会更差）；其余程序的拆分实验。
- **复现**：`gmake EXTRA_CXXFLAGS="-DCFG_DECODE_WIDTH=6 -DCFG_ROB_NUM=126" BUILD_DIR=build_area/dw6 LDFLAGS="-lz"`；拆分用 `-DCFG_DECODE_WIDTH=6 -DCFG_ROB_BANK_NUM=8 -DCFG_ROB_NUM=176`；回放结果在 `~/personal/AI-Huma-data/spec-rv32imab/tm/{dw6,dw6b8}`。

---

## EXP-007 TAGE 备选提供者计数器更新

- **日期**：2026-11-05
- **分支**：trace-model `exp/tage-alt`（工作区 `trace-model-tage`，从 `exp/batch3` 切出），改动未提交
- **问题**：BPU 预测时算出“备选提供者”的表号 `altpcpn`，一路存进 PTAB、FTQ、更新队列，但训练（`Tage::update`）从不读它。标准 TAGE（Seznec）在提供者的有用位为 0 时也训练备选提供者的计数器——补上这一步，分支预测会不会更准？
- **方法**：开关 `CFG_TAGE_ALT_UPDATE`（默认 0，关闭时 gate 62/62 与基线逐个相同）。打开后，提供者有用位为 0 时，备选提供者表的计数器（没有备选时是基础表）也向实际方向更新一步；备选表号小于提供者，与分配新项的表不重叠。打开时 gate 15 个程序周期变化，全部 difftest Success、无不一致。
- **负载**：第 3 批配置，quick SPEC（覆盖 90% 权重的点）里分支预测差的 6 个程序，共 176 个点；基线 perlbench/gcc/mcf/sjeng 用 EXP-005 的第 3 批结果，gobmk/astar 补跑。

| 程序 | MPKI 基线 | MPKI 加更新 | IPC 基线 | IPC 加更新 |
|---|---|---|---|---|
| perlbench | 8.53 | 8.53 | 2.468 | 2.471 |
| gcc | 9.30 | 9.30 | 2.566 | 2.565 |
| mcf | 16.61 | 16.62 | 1.327 | 1.327 |
| sjeng | 18.73 | 18.69 | 2.027 | 2.029 |
| gobmk | 16.26 | 16.35 | 2.130 | 2.126 |
| astar | 26.90 | 26.95 | 1.253 | 1.252 |
| 几何平均 IPC | | | 1.889 | 1.889 |

（MPKI 按 SimPoint 权重加权，分母含 1000 万条预热。）

- **结论**：没有收益（MPKI ±0.6%，有升有降）。推测原因：备选预测只在“提供者弱 + 有用位低 + `use_alt` 倾向备选”时才被采用，稳态下很少；备选表项多分支共享，额外更新也可能干扰。**不合入**；`altpcpn` 的存储可以删除（统一 FTQ 的 RTL 试做里已删，周期不变）。
- **顺带**：gobmk（16.3）、astar（26.9）的 MPKI 高于 quick 集合里的程序，做分支预测相关实验时应一起测。
- **复现**：`gmake EXTRA_CXXFLAGS="<第 3 批默认> -DCFG_TAGE_ALT_UPDATE=1" BUILD_DIR=build_area/alt`，`replay_one.sh` 回放，结果在 `~/personal/AI-Huma-data/spec-rv32imab/tm/{b3,tagealt}`。

---

## EXP-006 用 DRAMsim3 替换固定延迟的 SimDDR，去掉 AXI 子系统分频

日期 2026-11-05。分支 `trace-model` 的 `exp/dram-sim`（工作目录 `trace-model-dram`，基于 `exp/batch3` 的 `08e9cfe`，未提交、未合入）。

**状态：已合入 `main`（2026-11-06）**：trace-model `88e5254`、rtl `b19a181`，两边都是从 `exp/dram-sim` 快进合入；记录见 [MAIN_RECORDS.md](MAIN_RECORDS.md)。

> **2026-11-06 更新：附加延迟默认值由 32 ns 改为 60 ns，基线已重做**（见下面"基线重做"一节）。本节前面各表（结果 1–4、SPEC、估算分数、`RQD` 测量）都是 32 ns 版本的数字，保留作为历史；当前基线的数字以"基线重做"一节和 trace-model `docs/PROJECT.md` 为准。

### 动机

现有 `SimDDR` 只有固定 60 个 tick 的读延迟（`CONFIG_SIM_DDR_LATENCY`），不看地址：没有 bank/row、刷新、读写争用。后续要去掉"DDR 分频"、外接开源 DRAM 模拟器，先在 trace-model 上验证接入方式和影响。

### 现有的"分频"是什么

`CONFIG_AXI_SUBSYSTEM_FREQ_DIV = 16`（trace-model 与 `rtl/tb/soc/platform` 的 `config.h` 里都有）：AXI 互联、LLC、DDR、MMIO 每个核心周期跑 16 个 tick（`run_extra_axi_subsystem_ticks`，全空闲时提前跳过）。所以基线的"60 周期 DDR 延迟"其实是 60 个子系统 tick = 3.75 个核心周期，远小于真实 DRAM 延迟。这个分频让存储相对核心快 16 倍。

### 方法

- 选 DRAMsim3（umd-memsys，C++，tick 驱动，克隆到 `AI-Huma-data/third_party/DRAMsim3`，编成 `libdramsim3.dylib`；macOS 上 cmake 需加 `-DCMAKE_POLICY_VERSION_MINIMUM=3.5`）。
- 开关：`gmake DS3=1 BUILD_DIR=build_ds3 LDFLAGS="-lz"`（编译宏 `SIM_DDR_DS3`），默认关闭。**DS3 构建同时把 `CONFIG_AXI_SUBSYSTEM_FREQ_DIV` 定为 1（不分频）**，一次 `SimDDR::seq()` 就是一个核心周期。关闭 DS3 时代码与基线完全相同：dhrystone 150,427、coremark 233,515、memory-stress-small 189,128，gate 62/62 通过。
- **核心频率可配置**：编译期 `gmake CPU_FREQ_MHZ=1000`（`CONFIG_CPU_FREQ_MHZ`，默认 500），运行期环境变量 `CPU_FREQ_MHZ=1000` 覆盖。它决定 DRAM 时钟与核心时钟的比例，以及附加延迟（ns）折算成多少个核心周期。
- 实现：`sim_ddr/include/SimDDR_DS3.h`（后端）加 `SimDDR.cpp/.h`、`rv_simu_mmu_v2.cpp` 里 `#ifdef` 的几处改动。AXI 前端（AR/AW 队列、W FIFO、R burst 排放）不变。
  - 读：每个 AR 拆成 64 B 的 DRAM 读，按序送入 DRAMsim3；所有行返回后，再加固定附加延迟才允许吐数据。
  - 写：W FIFO 排空后拆成 64 B 写送入 DRAMsim3；被接收后返回 B（posted 写）。
  - 时钟：按飞秒累计时间，每个 tick 补足所需的 DRAM `ClockTick`（DDR4-3200 的 tCK = 0.63 ns）。保留分频时，被跳过的空闲 tick 也会推进 DRAM 时间。
  - 读写数据相的互斥和 turnaround 在该模式下关闭（总线由 DRAMsim3 负责）。
- 其他环境变量：`DS3_CONFIG`（ini，默认 DDR4_8Gb_x16_3200）、`DS3_EXTRA_NS`（默认 SOC+CDC = 32 ns）、`DS3_OUT`、`DS3_STATS=1`（退出时打印读数、平均/最大读延迟、写数、反压次数）。

### 模型近似（要记住）

- 附加延迟是常数：SoC、CDC 以及 PHY 路径 DRAMsim3 不建模。默认 32 ns 只取 SOC+CDC，CTL 与 PHY 的 28 ns 假定已被 DRAMsim3 自身的控制器延迟和 CL/tRCD 覆盖，没有校准过。
- 读按 AR 顺序整笔发出；SimDDR 前端仍按事务 round-robin 排放数据。
- 数据不存在 DRAMsim3 里，功能内存仍在 trace bridge。

### 勘误

本记录的第一版（同日早些时候）把每个 `seq()` 当成一个完整核心周期，没有计入 16 倍分频，延迟换算偏小，结论"小负载对 DRAM 不敏感、周期变化 ±1%"是错的，已作废。下面的数字是修正后的。另有一次增量编译混用了不同分频的目标文件，已用干净构建重测。

### 结果 1：分频的影响（原 SimDDR，不用 DS3）

| 程序 | 分频 16（基线） | 不分频（`FREQ_DIV=1`） | 变化 |
|---|---|---|---|
| dhrystone | 150,427 | 159,053 | +5.7% |
| coremark | 233,515 | 250,834 | +7.4% |
| memory-stress-small | 189,128 | 342,754 | +81% |
| gate 62 个 | — | 平均 +151%，中位 +146% | 最大 +441% |

不分频后固定 60 周期延迟才是真正的 60 个核心周期（120 ns）。基线的数字是靠分频"偷"来的。

### 结果 2：不分频，DRAMsim3 对比原 SimDDR（CPU 500 MHz，DDR4-3200，附加 32 ns）

| 程序 | 原 SimDDR | DS3 | DS3 平均读延迟 |
|---|---|---|---|
| dhrystone | 159,053 | 155,600 | 62.0 ns |
| coremark | 250,834 | 246,150 | 57.7 ns |
| memory-stress-small | 342,754 | 342,452 | 89.9 ns |
| gate 62 个（对 baseline.csv） | 平均 +151% | 平均 +80%，中位 +78% | — |

DS3 的读延迟 58–90 ns 比固定的 120 ns 低，所以周期更少；memory-stress-small 的差别小，因为它的瓶颈是带宽而不是延迟。

### 结果 3：核心频率（不分频，DS3，DDR4-3200）

| CPU 频率 | dhrystone | coremark | memory-stress-small | memory-stress-small（64 KiB LLC） |
|---|---|---|---|---|
| 500 MHz | 155,600 | 246,150 | 342,452 | 571,850 |
| 1000 MHz | 158,756 | 250,658 | 343,975 | 799,040 |
| 2000 MHz | 164,862 | 260,914 | 366,989 | 1,335,536 |

频率翻倍，DRAM 延迟折合的核心周期数翻倍：dhrystone 每翻倍约 +2–4%，访存密集的 memory-stress-small（64 KiB LLC，约 2.3 万次读、1.1 万次写）约 +40–67%。

### 结果 4：gate 全集（不分频 DS3，500 MHz）

62 个测试里 61 个正常退出；`dcache-conflict-writeback` 超过 gate 的 4 倍基线周期上限（3,616）而被判超时，原 SimDDR 不分频时同样超限。提交指令数 58 个与基线相同，另 4 个不同：3 个是中断类（`interrupt-vectored`、`supervisor-external-interrupt-vectored`、`timer-interrupt-mask`，中断到达点随周期变化，预期）以及上面那个超时的。默认的 `[TB_CHECK]` 没开比较（compared=0），所以正确性只靠提交数一致和正常退出，没有跑 difftest 逐条比较。

### 结论

- 接入可行：AXI 端口不变，只换时序；关闭 DS3 与基线逐周期相同。
- 现有 16 倍分频掩盖了 DRAM 延迟：不分频后原模型就比基线慢 5–80%（gate 平均 +151%）。以后凡是不分频，基线周期数、gate 的 baseline.csv、docs 里的标准周期都要重新生成。
- DRAMsim3 给出 58–90 ns 的平均读延迟，比固定 60 周期（120 ns）更合理，并且随地址和读写争用变化。
- 核心频率会明显改变结果，需要在记录里标明频率；默认 500 MHz。

### RTL 侧同步（2026-11-05，`rtl` 的 `exp/dram-sim`，工作目录 `rtl-dram`，基于 `exp/batch3` 的 `52d2b84`，未提交）

RTL 里的 16 倍分频是 `mem_top` 的 4 位 `phase_q`（每 CPU 周期 16 个快 tick，`phase0` 是 tick 0、`phase_last` 是 tick 15），`axi_cpu_port_adapter`、`dcache_resp`、`mem_axi` 的累积/锁存逻辑都按 `phase0`/`phase_last` 写，所以把它参数化即可，不需要改这些模块：

- `trace-model/include/config.h` 新增 `constexpr int AXI_SUBSYSTEM_FREQ_DIV`，`gen_cfg.sh` 把它带进 `ttg_cfg_pkg.sv`（用 `SIM_SRC=<trace-model-dram 的绝对路径> scripts/gen_cfg.sh` 重新生成；新包只多这一项，并更新了 `CONFIG_CPU_CYCLE_FS` / `CONFIG_SIM_DDR_LATENCY_CALC` 两个随频率变化的派生值）。
- `mem_top.sv`：`phase_q` 在 `TICKS-1` 后回 0，`phase_last = (phase_q == TICKS-1)`；`TICKS = AXI_SUBSYSTEM_FREQ_DIV`，取 16 时与原来逐位相同，取 1 时 `phase0` 和 `phase_last` 恒为 1。
- `tb/soc/soc_tb.cpp`：`kTicks` 取自平台 `config.h`（`CONFIG_AXI_SUBSYSTEM_FREQ_DIV`，现为 1）；空闲 tick 跳过只在 16 tick 时启用；`ddr_idle` 改用 `idle_quiescent()`；复位期间不推进 DDR 模型（否则 DRAMsim3 的时钟比 trace-model 早 3 个周期，所有程序差 1 周期）。
- 平台模型 `tb/soc/platform`：`config.h` 改为不分频、1 GHz；`SimDDR.cpp/.h` 换成 trace-model 的版本加 DRAMsim3 后端，再加编译宏 `SIM_DDR_DATA`（读数据取自、写数据落到 `PhysMemory`，复刻原 `do_memory_read/do_memory_write`；trace-model 构建不开它）。
- `tb/soc/build.sh`：默认带 DRAMsim3（`DS3=0` 退回固定延迟，`DS3_DIR` 指向 DRAMsim3 目录），并一律定义 `SIM_DDR_DATA`。
- `scripts/ref_cycles.txt`：66 项参考周期用新基线的 trace-model 重新生成。

结果（整核测试平台，带功能模型逐条比对）：

| 检查 | 结果 |
|---|---|
| `fm_gate.sh`（66 个程序） | 66/66 通过，没有功能模型不一致 |
| 周期与新 trace-model 逐个相等 | 修复 store 窗口后 66/66 相等（修复前 62/66，见下） |
| 不相等的 4 个 | dcache-conflict-writeback 4,271（tm 4,293）、matmul_fpu 43,242（43,256）、memory-stress-small 343,543（343,975）、pascal 1,785（1,747） |
| `DS3=0`（固定延迟）、同样不分频 | RTL 与 trace-model 在 add、dummy、fib、crc32 上逐个相等；同样那 4 个程序也不相等（pascal 1,823 对 1,748 等），所以差异**与 DRAMsim3 无关**，来自不分频本身 |

RTL 仿真速度（同一台机器、单次运行、未做负载控制）：不分频后 dhrystone 36.0 s → 4.4 s、coremark 50.9 s → 6.9 s，约快 8 倍（周期数不同，折算每秒仿真周期约 4.2 千 → 36 千，也是约 8.6 倍）。原因是每个 CPU 周期只需 1 个 tick，不再是 16 个，也不再需要空闲 tick 跳过。旧数字用 `rtl/build/soc_fm_b3`（16 tick，固定延迟 SimDDR），新数字用 DRAMsim3 版本。

**原因已查清并修复**：RTL 的 LSU 把所有队列扫描窗口都写成 `WIN = LSU_LOAD_WINDOW_WIDTH`（注释写"== `LSU_STORE_WINDOW_WIDTH`"），第 3 批把端口改成 LD 4 / STA 3 之后，load 窗口是 4×5 = 20，store 窗口是 3×5 = 15，两者不再相等；trace-model 的 store 提交窗口 `comb_lsu2dcache_stq` 用 `LSU_STORE_WINDOW_WIDTH`（15），RTL 的 `lsu_dc_req_st` 却看 20 个。链头的 store 因 DCache 重放卡住时，RTL 会提前发出窗口 15 之外的 store（pascal 在 cycle 1031 发出 `0x80000178`，trace-model 到 1038 才发）。16 倍分频时 store 响应在额外 tick 里很快回来，链头不会卡住，所以这个差别一直没有被周期对比抓到。定位办法：逐周期打印 LSU 到 DCache 的 load/store 端口请求与响应、`mshr_fill`，两边第一个不同的输入就是这个 store 请求，再对照 `RealLsu.cpp` 的窗口。

修复：`lsu_pkg.sv` 新增 `STWIN = LSU_STORE_WINDOW_WIDTH`，`lsu_dc_req_st.sv` 的窗口成员改为 `stq_ccount > q && q < STWIN`。修复后固定延迟（`DS3=0`）下 4 个程序全部与 trace-model 相等（pascal 1,748、matmul_fpu 43,272、memory-stress-small 342,754、dcache-conflict-writeback 4,454），DRAMsim3 下 `fm_gate.sh` 66/66 通过，**66 个程序周期与新 trace-model 全部相等**；`lint.sh` 和 `lint_chip.sh` 通过。

仍有隐患：RTL 的其他 store 队列窗口（`wait_mmu_stq`、`mmu_done_stq` 等，经 `lsu_pkg.sv` 里的通用 `ring_apply` 用 `WIN`）同样按 20 处理，trace-model 用 15；这 66 个程序没有触发，修它需要给 ring 操作带上窗口参数，尚未做，已记入风险。（后来在 rtl 分支 `exp/lsu-stwin`（`b94b4f5`）里修了全部 store 侧队列窗口，包含这两个 ring，尚未合入；本分支的 `0fce9a6` 只修了提交窗口，是它的子集。）

RTL 仿真提速试验（同日，dhrystone 158,756 周期，墙钟秒；机器上同时跑着另一个 4 线程的 Linux 启动，数字有噪声，每项重复 2–3 次）：

| 变化 | 墙钟 | 说明 |
|---|---|---|
| 基线（`--threads 4`，`-O2`） | 4.5–4.7 | |
| `mem_top` 在 `TICKS==1` 时把 `phase0`/`phase_last` 做成编译期常量 | 4.4–4.5 | 约 2–3%，周期不变；`fm_gate` 66/66、周期全部相等 |
| 再加 `-O3 -march=native`（`SOC_COPT`） | 4.2–4.3 | 再约 4–5% |
| `--threads 1 / 2 / 4 / 6 / 8` | 10.5 / 6.4 / 4.5 / 5.0 / 7.4 | 4 线程最好，线程更多反而慢（本机 14 核，被另一个进程占去 4 个） |

结论：模型很大，多线程收益显著（1 → 4 线程快 2.3 倍），但 4 线程已是拐点；剩下的收益要靠减少每周期的 `eval()` 次数、DRAMsim3 空闲快进和缩小设计状态，本次未做。`phase0` 常量化已保留在 `mem_top.sv`；`-O3` 未改默认值，用 `SOC_COPT="-O3 -march=native"` 打开。

Linux 启动（RTL，不分频 + DRAMsim3 + 1 GHz，`SOC_TB_FM=1 SOC_TB_SEMIHOST=1`，镜像 `AI-Huma-data/linux/linux.bin`）：

- 第一次在内核初始化末尾被 `axi_llc_rq.sv:95` 的断言（读响应队列满）中止。该队列深度 `RQD=4` 是按 16 tick 下"程序最多 1、随机测试最多 3"定的；不分频后互联每个核心周期只排空一次，Linux 的 DCache 重填并发更高，于是溢出。trace-model 的对应队列是 32 项，且没有溢出断言，所以没有报错；不分频的 trace-model 没有跑过 Linux，实际最大占用未知。
- 先把 `RQD` 改为 32（与 trace-model 一致）后重跑：启动到 `rv32 login:`，日志（`rtl_dram_boot2.log`）没有断言、没有功能模型不一致行；到登录后手动结束进程，因此没有 `[FM] N instructions checked` 汇总行，也没有总周期数。
- 在不分频 trace-model（DRAMsim3、1 GHz）上加临时占用探针跑 Linux 启动到 `rv32 login:`：master 0 排队峰值 1、master 1（DCache MSHR）排队峰值 4，加输出寄存器后的总占用分别为 2 和 5；dhrystone、coremark、memory-stress、memory-stress-small 的队列都没被用到。RTL 的断言是 `总占用 ≤ RQD`，原 `RQD=4` 正好在总占用到 5 时溢出，与实测吻合。**决定 `RQD = 8`**（最小可用 5，留 3 的余量，比 32 省约四分之三的队列存储）。RTL 一侧的同样探针测量被我中途结束，没有出结果。
- 遗留：`RQD=8` 只按 Linux 启动一个大负载定；SPEC 等其他大负载未测。其他按 16 tick 下的小程序测出来的小深度队列可能同样不够，尚未逐个检查。

SPEC CPU2006 整数 checkpoint 回放（trace-model，新基线：不分频、DRAMsim3 DDR4-3200、1 GHz；`scripts/spec/replay.sh full`，12 个程序、580 个 SimPoint、每点预热后测 1000 万条指令，8 路并行，用时约 1 小时 45 分，结果在 `AI-Huma-data/spec-rv32imab/tm/res_dram`）：

| 程序 | 点数 | 加权 IPC |
|---|---|---|
| 400.perlbench | 44 | 2.131 |
| 401.bzip2 | 76 | 1.645 |
| 403.gcc | 55 | 1.590 |
| 429.mcf | 79 | 0.463 |
| 445.gobmk | 50 | 1.783 |
| 456.hmmer | 34 | 3.718 |
| 458.sjeng | 28 | 1.858 |
| 462.libquantum | 51 | 0.857 |
| 464.h264ref | 37 | 1.489 |
| 471.omnetpp | 40 | 1.508 |
| 473.astar | 35 | 0.975 |
| 483.xalancbmk | 51 | 1.959 |
| **几何平均** | 580 | **1.487** |

580 个点全部完成，没有失败，没有 difftest 不一致（mismatch-points 全为 0）。

与旧基线（`tm/b3`，第 3 批配置、16 倍分频、固定 60 tick 延迟；只有 quick 的 6 个程序、覆盖 90% 权重的点，所以用同一批点比较；该目录的配置我没有逐项核对，按目录名和日期判断）：

| 程序 | 旧 IPC | 新 IPC | 变化 |
|---|---|---|---|
| 400.perlbench | 2.468 | 2.135 | −13.5% |
| 403.gcc | 2.566 | 1.631 | −36.4% |
| 429.mcf | 1.327 | 0.480 | −63.8% |
| 456.hmmer | 4.007 | 3.767 | −6.0% |
| 458.sjeng | 2.027 | 1.853 | −8.6% |
| 464.h264ref | 1.677 | 1.511 | −9.9% |
| **几何平均** | 2.204 | 1.613 | **−26.8%** |

结论：去掉 16 倍分频、换成 DRAMsim3 之后，访存密集的程序掉得最多（mcf −64%、gcc −36%），计算密集的掉得少（hmmer −6%），符合"分频让 DRAM 相对核心快了约 13 倍"的判断。旧数字是偏乐观的，新数字才反映 1 GHz 核心配 DDR4 的情况。附加延迟 32 ns 仍未校准，绝对值会随它变。

DRAMsim3 依赖（同日）：改为 trace-model 仓库的固定版本子模块 `third_party/DRAMsim3`（`2981759`）；Makefile 把它的 12 个源文件直接编成 `build_dramsim3/libdramsim3.a`（`gmake dramsim3`，不用 cmake、不用动态库、不设 rpath、不往子模块里写文件），RTL 的 `tb/soc/build.sh` 链接同一个静态库（`TM_DIR` 指定 trace-model 目录）。克隆后要 `git submodule update --init third_party/DRAMsim3`。验证：全新 `BUILD_DIR` 构建后 gate 62/62、dhrystone 158,756、coremark 250,658（与动态库版相同）；`DS3=0` 仍可不带 DRAMsim3 构建；RTL `fm_gate.sh` 66/66、66 个周期与 trace-model 全部相等。

### 基线重做：非核心延迟 60 ns（2026-11-06）

原因：32 ns 只取了 SOC+CDC，理由是控制器和 PHY 已被 DRAMsim3 覆盖；这个假设不成立（DRAMsim3 只建模命令调度和 DRAM 时序，不含控制器流水线和 PHY）。`config.h` 里本来的非核心路径是 SOC 20 + CDC 12 + CTL 15 + PHY 13 = 60 ns，设计读延迟 `CONFIG_SIM_DDR_LATENCY_CALC` = 86 ns。改成 60 ns 后 dhrystone/coremark 的平均读延迟约 85–87 ns，与 86 ns 吻合（32 ns 时 56–58 ns，memory-stress-small 81 ns → 105 ns）。`DS3_EXTRA_NS` 仍可覆盖。

DDR 配置：DRAMsim3 `DDR4_8Gb_x16_3200`（tCK 0.63 ns，CL/tRCD/tRP 22，1 通道、64 位、2 bank group × 4 bank、BL8、open page、地址映射 `rochrababgco`、rank 级交错刷新），与 `config.h` 里原来的 CL 22 / tRCD 22 / tRP 22 / 1600 MHz 一致。

| 程序 | 32 ns | 60 ns |
|---|---|---|
| dhrystone | 158,756 | 162,033 |
| coremark | 250,658 | 255,335 |
| memory-stress | 2,425,029 | 2,428,470 |
| smc-div | 11,096 | 11,348 |
| smc-addi | 10,966 | 11,218 |
| memory-stress-small | 343,975 | 347,305 |

`baseline.csv` 63 个程序：周期平均 +23%、中位 +28%、最大 +36%；gate 62/62。RTL：`ref_cycles.txt` 重新生成，`fm_gate.sh` 66/66、66 个周期与 trace-model 全部相等；Linux 从复位启动到 `rv32 login:`（`RQD=8`，无断言、无不一致）。trace-model 上 LLC 读响应队列峰值：master 1 排队 3 + 输出寄存器（32 ns 时 4 + 1），`RQD=8` 仍够用，延迟变高反而排队更少。

SPEC 全量回放（580 点，无失败，无 difftest 不一致；`tm/res_dram60`，12 路并行）：

| 程序 | 加权 IPC | 估算分数@1GHz | 32 ns 的 IPC |
|---|---|---|---|
| 400.perlbench | 2.092 | 8.08 | 2.131 |
| 401.bzip2 | 1.600 | 7.13 | 1.645 |
| 403.gcc | 1.474 | 9.32 | 1.590 |
| 429.mcf | 0.405 | 12.62 | 0.463 |
| 445.gobmk | 1.763 | 8.85 | 1.783 |
| 456.hmmer | 3.720 | 9.75 | 3.718 |
| 458.sjeng | 1.834 | 8.44 | 1.858 |
| 462.libquantum | 0.663 | 4.73 | 0.857 |
| 464.h264ref | 1.475 | 6.08 | 1.489 |
| 471.omnetpp | 1.333 | 6.92 | 1.508 |
| 473.astar | 0.928 | 7.00 | 0.975 |
| 483.xalancbmk | 1.873 | 12.04 | 1.959 |
| **几何平均** | **1.396** | **8.12** | 1.487（分数 8.66） |

quick 的 6 个程序（旧基线 `tm/b3` 同一批点）：几何平均 IPC 旧（16 倍分频）2.204 → 32 ns 1.613 → 60 ns 1.550。分数的换算方法和局限见上面"估算分数"一段（参考时间是凭记忆写的，未核对官方表）。

综合前后对比（2026-11-06，Yosys + yosys-slang 的相对面积代理，`scripts/synth_module.sh`，`SYNTH_LIGHT=1 SYNTH_MEM=1`；改动前 = `main`/`exp/batch3` 的 rtl，改动后 = `exp/dram-sim`；**不是工艺库面积、没有时序**）：

| 模块 | 改动前 | 改动后 | 变化 | 原因 |
|---|---|---|---|---|
| `axi_llc_rq`（每个读主设备一份） | 10,439 单元 / 2,584 触发器 | 18,768 / 4,649 | +8,329 / +2,065（+80%） | `RQD` 4 → 8 |
| `axi_llc`（整个 LLC，`NR=4` 个读主设备） | 489,436 / 22,324 | 522,758 / 30,584 | **+33,322 / +8,260（+6.8% / +37%）** | 4 × `axi_llc_rq` 的增量，吻合 |
| `lsu_dc_req_st` | 86,150 / 0 | 62,755 / 0 | **−23,395（−27%）** | store 窗口 20 → 15 |
| `dcache_resp`、`axi_cpu_port_chan` | 14,113 / 38；59 / 24 | 相同 | 0 | 单独综合时 `phase0`、`phase_last` 是悬空输入，看不出常量化的效果 |

净变化约 +9.9k 单元（+33.3k − 23.4k），相对整机推算的约 952 万个门不到 0.2%；触发器 +8,260，相对整机约 18.1 万是 +4.6%，全部来自 `RQD`。`mem_top` 的 `TICKS == 1` 常量化（去掉 16 tick 折叠逻辑）预计是减量，但 `mem_top` 太大，Yosys 超时，没有测到。每增加一项 `RQD`，4 个队列合计约 +8.3k 单元（`RQD=5` 即最小可用值约 +8.3k，`RQD=6` 约 +16.7k，`RQD=8` 为 +33.3k）。

### 后续

- **已决定（2026-11-05）：不分频 + DRAMsim3 + 默认 1 GHz 作为新基线**（trace-model 侧已完成：`config.h` 默认 `FREQ_DIV=1`、`CPU_FREQ_MHZ=1000`，Makefile 默认 `DS3=1`，`baseline.csv` 已重生成，gate 62/62，大程序标准周期见 trace-model `docs/PROJECT.md`）。新旧基线周期对比：gate 平均 +146%、中位 +135%，dhrystone 150,427 → 158,756，coremark 233,515 → 250,658，memory-stress 1,541,195 → 2,425,029，memory-stress-small 189,128 → 343,975。RTL 侧已同步（见下一节），66 个程序周期与 trace-model 全部相等。
- 开启 difftest 逐条比较重跑 gate；用 Linux 启动片段、SPEC 检查点（不要用 cjpeg/linear_alg/parser/sha）测带宽和 bank 冲突敏感的负载。
- 校准附加延迟，或与 RTL 闭环里的 SimDDR 对齐；试 DRAMsim3 的地址映射和 open/close page。
- RTL 其他 store 队列窗口（`wait_mmu_stq`、`mmu_done_stq`）与 trace-model 的 15 不一致，需给 `ring_apply` 带窗口参数。
- RTL 侧合入 `main` 前还要跑 Linux 启动（`SOC_FM=1 SOC_TB_SEMIHOST=1`，数小时）和综合对比。
- Ramulator 2.0 作为后备，未试。

## EXP-005 opt1 的 SPEC 对比与不改结构的参数同步到 RTL

- **日期**：2026-11-05
- **分支**：trace-model `exp/area-explore`（未提交）；rtl `exp/batch1-params`（未提交）；function-model `exp/spec-rv32imab`（SPEC 脚本，未提交）
- **问题**：opt1 在 SPEC 上的性能代价多大？其中零风险的参数部分能否直接同步到 RTL，面积省多少？

### SPEC 检查点重建（rv32imab）

- 原检查点放在 `/tmp` 里，重启后丢失（见 EXP-004）。按原流程重建，改为 rv32imab（GCC 13.3，`-march=rv32ima_zicsr_zifencei_zba_zbb_zbs`），数据放在 `~/personal/AI-Huma-data/spec-rv32imab`。流程、参数、耗时见 `function-model/scripts/spec/README.md`。
- 12 个程序的 BBV 全部跑完、输出与 SPEC 参考一致；检查点共约 60 GB。
- 发现并修正 `pipeline.sh` 的误判：模拟器的 BBV 打印会插进 `RUN ... rc=0` 行中间，perlbench 和 sjeng 因此被判为“退出码非零”。现在先删掉这些插入的打印再校验。
- 因为编译选项（加了 B 扩展、换了 GCC）变了，新的 IPC 不能和旧的 rv32ima 数字（quick 几何平均 2.356）直接比。

### quick SPEC：基线 vs opt1（90% 权重的点，前门恢复，测 1000 万条）

| 程序 | 点数 | 基线 IPC | opt1 | 变化 | opt1 + 统一 FTQ 上限 64 | 第 3 批（RTL 配置） |
|---|---|---|---|---|---|---|
| perlbench | 21 | 2.487 | 2.473 | −0.6% | — | 2.468（−0.8%） |
| gcc | 31 | 2.600 | 2.568 | −1.2% | 2.567 | 2.566（−1.3%） |
| mcf | 53 | 1.333 | 1.328 | −0.4% | 1.328 | 1.327（−0.5%） |
| hmmer | 24 | 4.018 | 4.005 | −0.3% | 4.005 | 4.007（−0.3%） |
| sjeng | 21 | 2.038 | 2.022 | −0.8% | — | 2.027（−0.5%） |
| h264ref | 28 | 1.677 | 1.677 | 0.0% | 1.677 | 1.677（0.0%） |
| 几何平均（4 个：gcc mcf hmmer h264ref） | | 2.198 | 2.187 | −0.5% | 2.187 | 2.187（−0.5%） |
| **几何平均（6 个）** | | **2.216** | **2.204** | **−0.5%** | — | **2.204（−0.5%）** |

- 所有点都跑完，无比对不一致。第 3 批（LD/STA IQ 不合并、各 64）与 opt1 几乎相同，说明 opt1 的 SPEC 损失来自第 1–3 批的参数，不来自 LD/STA 合并。统一 FTQ 的上限近似（`UFTQ_CAP=64`）和 opt1 结果相同。
- gcc 损失最大的三个点原因各不同：在飞分支数顶到 32、STD IQ（16 项）满、STA 端口 3 个占满。只在 gcc 上逐项放宽验证：在飞分支回到 64 不起作用（2.568），STD IQ 32 只回到 2.572。差距不大，按用户决定不再追。

### 第 1 批同步到 RTL：BACKEND_FETCH_WIDTH 8、MAX_BR_NUM 32、ibuf 64

只改参数，RTL 结构不动。参数包由 `make cfg` 从 trace-model `config.h` 生成（这次用 `gen_cfg.sh -DCFG_BACKEND_FETCH_WIDTH=8 -DCFG_MAX_BR_NUM=32 -DCFG_IBUF_SIZE=64`），连带 `BR_MASK_WIDTH` 64→32、`BR_TAG_WIDTH` 6→5、`FTQ_OFFSET_WIDTH` 4→3。

要修的地方（都是字段位宽写死成数字）：
- 生成的 `back_top.sv`、`exu.sv` 以及手写的 `dispatch.sv`、`lsu.sv`、`rob.sv` 端口：`tools/dimmap.py` 加了字段位宽规则（`br_mask`/`clear_mask` 64 → `BR_MASK_WIDTH`，`br_id` 6 → `BR_TAG_WIDTH`，`ftq_offset` 4 → `FTQ_OFFSET_WIDTH`），`gen_backtop.py` 生成时用同一规则。改之前确认了重新生成与仓库里的文件完全一致。
- 测试平台 `tb/soc/soc_tb.cpp` 按写死的位偏移从 LSU 的 `st_fld_q` 取 MMIO store 的地址/数据（88/91/155）。br_mask 变窄后字段前移，外设模型收到错字节：串口输出乱码，`supervisor-external-interrupt-vectored` 等不到中断。function-model 逐条对比不比较 store 数据，所以没报错。现在 `gen_soc_probe.py` 从参数包读出位宽，偏移按结构体布局计算。

验证：
- 新旧两套参数下，整芯片 Verilator `-Wall` 0 条警告，`lint.sh` 通过。
- 整核测试平台 + function-model 逐条对比，66 个程序（gate、vm、dhrystone、coremark）两种参数都全部通过，串口输出逐字节一致。
- 周期数：66 个里 3 个变化，与同参数的 trace-model 完全一致。

| 程序 | 基线 | 第 1 批（RTL = trace-model） |
|---|---|---|
| coremark | 226,991 | 232,353（+2.36%，来自在飞分支 32） |
| dhrystone | 150,838 | 150,582 |
| prime | 11,760 | 11,591 |

综合（`synth_module.sh`，`SYNTH_LIGHT=1 SYNTH_MEM=1`，与 `rtl/docs/09-synthesis-report.md` 同流程；基线数字与报告一致）：

| 模块 | 基线单元数 | 第 1 批 | 变化 | 触发器 基线→第 1 批 |
|---|---|---|---|---|
| isu | 2,119,233 | 1,727,421 | −18% | 73,204 → 60,052 |
| ren | 345,198 | 206,193 | −40% | 18,203 → 10,315 |
| pre_idu_queue | 188,943 | 50,225 | −73% | 36 → 33 |
| idu | 97,352 | 30,640 | −69% | 4,213 → 1,108 |
| dispatch | 104,827 | 86,586 | −17% | 1,896 → 1,624 |
| exu_ctrl | 22,016 | 14,129 | −36% | 5,486 → 4,586 |
| prf | 376,833 | 372,609 | −1% | 2,310 → 1,606 |
| rob | 235,182 | 234,791 | 0% | 17,802 → 17,674 |
| 合计 | | | 约 −77 万（整机约 952 万的 8%） | 约 −2.4 万 |

- 单元数不含存储阵列（保留为 `$mem`）。存储按位宽手算：FTQ 每项 1824→912 位，64 项省约 5.8 万位；ibuf 128×44 → 64×43，省约 2.8 千位。
- `lsu_ring`、`lsu_stlf`、`idu_br_cp` 不变。

### 第 2、3 批同步到 RTL：IQ 大小、front2back 深度、端口数

- **第 2 批**（在第 1 批之上）：INT IQ 64、BR IQ 32、STD IQ 16、front2back FIFO 8。LD/STA IQ 仍分开各 64（合并要改结构，不在这一批）。
- **第 3 批**（在第 2 批之上）：端口 LD/STA/STD/BRU 4/3/3/2。`ISSUE_WIDTH` 22→18、FU 总数 28→24、AGU 8→7、DCache miss 数 8→7、store 窗口 20→15 等随之变化。

要改的地方：
- trace-model `config.h` 新增标量 `IQ_INT_SIZE`、`IQ_LD_SIZE` 等（生成器只导出标量常量）；`gen_cfg_pkg.py` 同时读取 `frontend_feature_config.h` 的 FIFO 深度。`isu_pkg::iq_size()`（原来写死 128/64）和 `front_pkg` 的 FIFO 深度改为读参数包。
- `dimmap.py` 新增规则：`ready_num` 8 位 → `IQ_READY_NUM_WIDTH`，`ftq_prf_pc_req/resp` 10 → `FTQ_PRF_PC_PORT_NUM`。
- `lsu.sv`：20 个通道向量宽度、18 个循环上界写死为 4，改为按通道类型用 `LSU_LDU_COUNT`/`LSU_STA_COUNT`/`LSU_SDU_COUNT`/`LSU_LOAD_WB_WIDTH`。
- **潜在 bug**：`lsu_core.sv` 的 store MMU 请求端口（`mmu_st_req_*`）按 load 端口数 `NLD` 声明，应为 `NST`。两者原来都是 4，所以一直没暴露。
- `exu_ctrl_pkg::xc_fu_kind()` 中 LD/STA/STD 的 FU 编号区段写死，改为按端口基址推出；`isu.sv` 的配置自检从“发射宽度必须是 22”改为“ALU 组在端口 0–5”。

验证（三批都做了）：
- 基线、第 1、2、3 批四套参数：整芯片 Verilator `-Wall` 0 警告，`lint.sh` 通过。
- 整核测试平台 + function-model 逐条对比：四套参数各 66/66 通过。改完 RTL 后用基线参数重跑，66 个程序的周期与改前逐个相同，串口输出逐字节一致。
- 各批周期有变化的程序（第 1 批 3 个、第 2 批 9 个、第 3 批 26 个），RTL 与同参数的 trace-model 逐周期一致。`timer-mmio` 打印计时器读数，周期变了读数就变，属于正常差异。

| 5 个小程序（RTL 周期） | 基线 | 第 1 批 | 第 2 批 | 第 3 批 |
|---|---|---|---|---|
| dhrystone | 150,838 | −0.17% | −0.42% | −0.27% |
| coremark | 226,991 | +2.36% | +3.00% | +2.87% |
| memory-stress-small | 189,128 | 0 | 0 | 0 |
| matmul_fpu | 42,253 | 0 | +0.16% | +0.28% |
| prime | 11,760 | −1.44% | −2.64% | −1.89% |
| 几何平均 | | +0.14% | 0.00% | +0.19% |

综合（同一流程，三套参数各综合一遍；`lsu`、`dcache` 等综合不出来的聚合模块没有算，所以是下限）：

| 模块 | 基线 | 第 2 批 | 第 3 批 |
|---|---|---|---|
| isu | 2,119,233 | 1,072,997 | 1,029,239 |
| prf | 376,833 | 372,609 | 282,121 |
| ren | 345,198 | 206,193 | 206,193 |
| rob | 235,182 | 234,791 | 201,297 |
| pre_idu_queue | 188,943 | 50,225 | 49,764 |
| exu（含 exu_ctrl 和各 FU） | 107,137 | 97,364 | 91,509 |
| dispatch | 104,827 | 86,598 | 86,598 |
| idu | 97,352 | 30,640 | 30,640 |
| lsu_dc_req_st | 87,426 | 87,426 | 86,150 |
| tlb_mmu | 60,793 | 60,793 | 53,454 |
| 合计（上述 11 个，含 front2back） | 3,723,024 | 2,299,695 | 2,117,024 |
| 触发器（同上范围） | 123,595 | 74,883 | 73,873 |

- 第 3 批相比基线：约 −161 万门（整机约 952 万的 17%），约 −5 万触发器（整机约 18.1 万的 27%）。isu 减半，来自 IQ 总项数 384→240 和 br_mask 64→32。
- 存储阵列另算：FTQ 约 −5.8 万位，ibuf 约 −2.8 千位，front2back 32→8 项约 −2.3 万位。
- 端口减少还会缩小 DCache 写口、LSU 的 STA 通路，这部分在 `lsu`/`dcache` 聚合模块里，没有数字。

### 后续

- 第 1–3 批要合入 main，需要先把 trace-model 的 `CFG_*` 开关合入并改默认值（RTL 参数包从 main 的 `config.h` 生成），并按规则记录性能和综合结果。
- LD/STA IQ 真合并、PTAB/front2back/FTQ 真统一：在 trace-model 里按真实硬件结构实现，再给 RTL 方案（进行中）。

---

## EXP-004 组合优化配置 opt1

- **日期**：2026-11-04
- **分支**：trace-model `exp/area-explore`，改动**未提交**
- **问题**：在飞分支缩到 32、INT IQ 用 64，再叠加前面所有优化，整体性能怎样？
- **配置 opt1**（构建命令在 `scripts/area/build_variants2.sh` 末尾）：

| 项 | 原设计 | opt1 |
|---|---|---|
| `BACKEND_FETCH_WIDTH` | 16 | 8 |
| MAX_BR_NUM（在飞分支） | 64 | 32 |
| INT IQ | 128 | 64 |
| BR IQ | 64 | 32（在飞分支只有 32 个，BR IQ 再大也用不上） |
| LD / STA IQ | 64 / 64 | 合并为 64 |
| STD IQ | 64 | 16 |
| ibuf | 128 | 64 |
| front2back FIFO | 32 | 8 |
| 端口 LD/STA/STD/BRU | 4/4/4/4 | 4/3/3/2 |
| 统一 FTQ（`UFTQ_CAP`，近似） | — | 分别测了不开和开 64 两种 |

- IQ 总项数 384 → 176（64+64+16+32）；重命名检查点 64 份 → 32 份；br_mask 64 位 → 32 位（IQ、LDQ、STQ 每项都省 32 位）。

### 结果

**正确性**：gate 的 62 个程序全部跑完，逐条提交 difftest 无不一致。周期数和基线不同是预期的，因为配置变了。

| 配置 | dhrystone | coremark | memory-stress-small | matmul_fpu | prime | 几何平均 |
|---|---|---|---|---|---|---|
| lean2（EXP-002，MAX_BR 64、INT 48、BR IQ 64） | −0.23% | −1.16% | 0 | +0.28% | −2.76% | −0.78% |
| opt1 | −0.23% | +2.74% | 0 | +0.28% | −1.89% | +0.17% |
| opt1 + 统一 FTQ 64 | −0.23% | +1.79% | 0 | +0.28% | −1.89% | −0.02% |

- coremark 的损失来自在飞分支 32 和 BR IQ 32，和 EXP-002 的单项结果一致（单项各约 +2.4%）。其余负载不受影响。
- 小程序几何平均基本持平。在飞分支 32 的代价集中在分支密集、长依赖的程序上，需要用 SPEC 确认。

### quick SPEC 没有跑：检查点丢失

- `scripts/spec/replay.sh quick` 需要 `/tmp/specref/ckpt/<bench>/*.gz` 和 `sp/<bench>.weights`，`function-model/mem/*.bin` 的 SPEC 镜像也不在了。
- 原因：机器在 2026-11-04 15:30 重启过，macOS 重启时会清空 `/tmp`。这些检查点是生成的数据，不在任何仓库里。
- `/tmp` 里还留着重启之后生成的东西：Linux 特殊检查点 `/tmp/ckpt`（595 MB）、`/tmp/linux_check.bin`、模块级综合结果 `/tmp/synth_results.txt`。下次重启也会丢，应该挪到持久目录。
- **教训**：生成的检查点、镜像、综合结果不能只放在 `/tmp`，要放到持久目录，并在文档里写明位置和生成命令。

### 后续

- 重新生成 SPEC 检查点后，跑 quick SPEC：基线、opt1、opt1 + 统一 FTQ 64，另加 opt1 配 MAX_BR 64 作对照。

---

## EXP-003 ROB 与 PRF 扩大到 256

- **日期**：2026-11-04
- **分支**：trace-model `exp/area-explore`，改动**未提交**
- **问题**：EXP-002 看到 ROB（128 项 = 16 行×8）经常是满的。扩大 ROB 能换来多少性能？
- **开关**：`CFG_ROB_NUM`（默认 128）、`CFG_PRF_NUM`（默认 128），写在 `include/config.h`；构建命令在 `scripts/area/build_variants2.sh` 末尾。
- **负载和方法**：同 EXP-001。所有变体都开着逐条提交 difftest 跑完，ROB 192（12 行）也能正常运行。

| 配置 | dhrystone | coremark | memory-stress-small | matmul_fpu | prime | 几何平均 |
|---|---|---|---|---|---|---|
| ROB 256、PRF 128 | +0.64% | −1.89% | +0.97% | +0.18% | +0.16% | +0.01% |
| ROB 128、PRF 256 | +0.01% | −0.78% | −0.00% | +1.28% | 0 | +0.10% |
| ROB 192、PRF 192 | −0.01% | −0.44% | −0.00% | −0.04% | −1.49% | −0.40% |
| ROB 256、PRF 256 | −0.73% | −3.07% | −0.00% | +1.11% | −1.36% | −0.82% |
| ROB 256、PRF 256 + lean2（EXP-002） | −1.38% | −1.56% | −0.00% | +1.03% | −3.04% | −1.00% |

### 结论

- 只加 ROB 不加 PRF 没有用：可重命名的寄存器只有 96 个，ROB 填不满。
- ROB 和 PRF 都翻倍，几何平均只快约 0.8%，coremark 快 3%，matmul_fpu 反而慢 1%。ROB 256 时占用 p99 仍是满的（32 行），说明这些程序是依赖链和延迟受限，窗口再大也帮不上多少。
- **ROB 128 是合理的**：EXP-002 里"ROB 经常满"只说明它是后端最先满的结构，不代表扩大它收益很大。
- lean2 加上 ROB/PRF 256，比基线快 1%，但 ROB 和 PRF 都翻倍的面积代价远大于这点收益，不建议。
- 局限：负载很小；大负载（工作集更大、访存延迟更长）下窗口的收益可能更高，需要复核。

---

## EXP-002 全核面积浪费排查

- **日期**：2026-11-04
- **分支**：trace-model `exp/area-explore`，在 EXP-001 的基础上继续，改动**未提交**
- **问题**：除 EXP-001 的三个方向外，设计里还有哪些结构明显过大、存在面积浪费？

### 方法

在 EXP-001 的插桩和开关上新增以下内容，默认值都和原设计一致：

| 开关 / 统计 | 默认 | 作用 |
|---|---|---|
| `CFG_INT_IQ_SIZE` / `CFG_BR_IQ_SIZE` | 128 / 64 | INT、BR 两个 IQ 的容量 |
| `CFG_IBUF_SIZE` | 128 | pre-IDU 指令缓冲（`IDU_INST_BUFFER_SIZE`） |
| `FRONT2BACK_FIFO_SIZE`（已有宏） | 32 | front2back FIFO 深度 |
| `CFG_MAX_BR_NUM` | 64 | 在飞分支数上限，决定重命名检查点份数和 br_mask 位宽 |
| `CFG_PLAIN_ALU_PORTS` | 2 | 只做 ALU 的端口数（前 4 个兼做 MUL/DIV/FP/CSR 的端口不变） |
| `CFG_BR_PORTS` | 4 | 分支执行端口数 |
| `[AS] br_inflt` / `rob_lines` | — | 在飞分支数（`now_br_mask` 置位数）、ROB 占用的行数（每行 8 项，共 16 行） |

- 新增改动：`back-end/Idu.cpp`、`back-end/Rob.cpp`（统计）、`include/config.h`（开关）、`scripts/area/build_variants2.sh`。
- **默认配置验证**：gate 62/62，周期与基线一致。
- **负载、运行上限、复现方式**：同 EXP-001（`run_set.sh`、`summarize.sh`）。
- **位宽来源**：IQ 项按 RTL `isu_pkg.sv` 的 uop 结构手算，约 189b/项；BPU 按 `bpu_pkg.sv`、`bpu_btb_pkg.sv`、`bpu_*bank.sv` 手算。

### 模型近似和局限

- 负载和 EXP-001 一样小。coremark 对时序变化敏感，单项结果有约 ±1% 的噪声（例如 INT IQ 64 比 48 还慢 1.2%）；prime 只有 1.2 万拍，噪声更大。
- 分支预测器容量问题，小程序**完全测不出来**（代码体量太小），这里只做存储量统计，不下性能结论。
- 端口减少带来的频率、布线收益没有建模。

### 基线观察（`ARCH_STATS=1`）

| 结构 | 容量 | dhrystone 占用 p99 | coremark 占用 p99 | 说明 |
|---|---|---|---|---|
| ROB（行） | 16 | 16（p50=15） | 16 | **经常满，是真正的瓶颈** |
| INT IQ | 128 | 27 | 57 | 与 ROB(128) 一样大 |
| LD IQ / STA IQ | 64 / 64 | 12 / 11 | 61 / 17 | 分别受 LDQ、STQ 限制 |
| STD IQ | 64 | 34 | 16 | |
| BR IQ | 64 | 12 | 41 | |
| 在飞分支 | 64 | 13 | 48（最大 51） | |
| ibuf | 128 | 128 | 128 | 反压时被填满 |
| front2back | 32 | 32 | 32 | 反压时被填满 |

- 基线下分派从未因 IQ 满而阻塞。前端 FIFO 和 ibuf 被填满，是 ROB 满之后层层反压的结果，并不是需要这么深。
- 前端到译码之间能缓存约 512 条指令（指令 FIFO 16 组 + front2back 32 组 + ibuf 128 条），是 ROB 容量的 4 倍。
- IQ 总项数 384，是 ROB 的 3 倍。

### 结果：单项扫描（周期变化，相对基线）

| 变体 | dhrystone | coremark | memory-stress-small | matmul_fpu | 几何平均 | 判断 |
|---|---|---|---|---|---|---|
| INT IQ 64 | +0.00% | +1.20% | 0 | 0 | +0.24% | 噪声 |
| INT IQ 48 | +0.00% | −0.20% | 0 | 0 | −0.04% | **可缩** |
| INT IQ 32 | −0.05% | +1.66% | 0 | +0.04% | +0.38% | 边缘 |
| BR IQ 32 | 0 | +2.43% | 0 | 0 | +0.16% | 不缩 |
| BR IQ 16 | 0 | +4.71% | 0 | 0 | +0.82% | 不缩 |
| STD IQ 32 | −0.37% | 0 | 0 | 0 | −0.07% | 可缩 |
| STD IQ 16 | −0.41% | −0.55% | 0 | +0.02% | −0.19% | **可缩** |
| ibuf 64 | −0.17% | −0.21% | 0 | 0 | −0.93% | **可缩** |
| ibuf 32 | +0.13% | +1.65% | 0 | 0 | +0.23% | 边缘 |
| front2back 16 | 0 | 0 | 0 | 0 | −0.46% | 可缩 |
| front2back 8 | 0 | 0 | 0 | 0 | −0.55% | **可缩** |
| MAX_BR_NUM 32 | 0 | +2.36% | 0 | 0 | +0.08% | 不缩 |
| MAX_BR_NUM 16 | 0 | +6.15% | 0 | 0 | +1.24% | 不缩 |
| 纯 ALU 端口 2→1 | +0.06% | +1.11% | +0.59% | +0.01% | +0.09% | 边缘 |
| 纯 ALU 端口 2→0 | −0.06% | −0.46% | +8.04% | −0.12% | +1.67% | 不缩 |
| BRU 4→3 | 0 | +0.28% | 0 | 0 | +0.06% | 可缩 |
| BRU 4→2 | −0.13% | −0.34% | 0 | 0 | −0.48% | **可缩** |
| BRU 4→1 | +1.75% | +8.79% | 0 | −0.08% | +1.58% | 不缩 |

### 结果：组合配置

| 配置 | 内容 | dhrystone | coremark | memory-stress-small | matmul_fpu | 几何平均 |
|---|---|---|---|---|---|---|
| lean | INT48、BR IQ 32、STD32、LD+STA 合并 64、ibuf 64、front2back 16、MAX_BR 32、端口 4/3/3 | −0.29% | +2.12% | 0 | +0.11% | +0.20% |
| **lean2** | INT48、BR IQ 64、STD16、LD+STA 合并 64、ibuf 64、front2back 8、MAX_BR 64、BRU 2、端口 4/3/3 | −0.23% | −1.16% | 0 | +0.28% | −0.78% |
| lean2 + 统一 FTQ 64 | 同上，加 `UFTQ_CAP=64` | −0.23% | −1.16% | 0 | +0.28% | −0.78% |

lean 的 coremark 损失来自 BR IQ 32 和 MAX_BR 32；lean2 保留两者为 64 后，与基线持平。

**lean2 节省（只算存储，手算）**：
- IQ 384→192 项（48+64+16+64；2026-11-05 更正，原写 176 是 opt1 的数）：约 36 Kb；唤醒比较器按 项数×2 源×15 个唤醒口 算，从 11,520 个降到 5,760 个。
- ibuf 64 项：约 2.8 Kb。
- front2back 24 项：约 23 Kb（若同时做 EXP-001 的 FTQ 合并，按 278b/项算约 6.7 Kb）。
- 端口：BRU 2 个，含配套的 FTQ PC 读口和 PRF 读口；STA、STD 各 1 个。
- 再加上 EXP-001 的 FTQ 改造（约 105 Kb）。

### 没有用 trace model 验证、但值得排查的设计问题

1. **每个 IQ 项都存完整 uop（约 189b）**：imm 32b、csr_idx 12b、func7、ftq_idx/offset、ldq_idx 等。STD IQ 实际只需要 src preg、stq_idx、rob_idx 和 br_mask。按 IQ 专门化字段，还能再省不少。
2. **br_mask 64 位**：每个 IQ 项、LDQ/STQ 项都带，约占 IQ 项的三分之一。性能上 MAX_BR 需要保持 64，可以考虑 ROB 区间等其他编码方式。
3. **BPU 存储约 1.1 Mb，比 L1D 数据阵列（64KB = 524 Kb）还大**：
   - TAGE：8 bank ×（1024×2b 基表 + 4×1024×13b）≈ 442 Kb
   - BTB：8×4 路×256×44b ≈ 360 Kb
   - TC：8×2 路×128×46b，加上同样大小的 pre 表 ≈ 188 Kb
   - 类型预测器：2 路×4096×14b ≈ 115 Kb
   - 类型预测器带 **16 个读口、8 个写口**，多端口阵列代价远大于存储本身。预测侧 8 个读口 + 提交侧 8 个读口，可以考虑提交侧改成从 FTQ 带回的信息更新，或只在分支上更新。
   - 容量是否合理需要用 Linux、SPEC 等大负载评估。
4. **ROB 经常满**：它是后端最先满的结构。EXP-003 实测把 ROB 和 PRF 都翻倍到 256 只快约 0.8%，所以 ROB 128 是合理的，不值得把面积挪过去。
5. **BPU 更新队列（`Q_DEPTH=2`，每 bank 一个，约 16×142b ≈ 2.3 Kb）**：它是 BPU 里另一个 FIFO，训练数据来自 FTQ。可以和 FTQ 合并成"提交时直接从 FTQ 读训练信息"，但体量很小，收益有限。

### 后续

- 在大负载上复核 lean2，并评估 BPU 容量（TAGE/BTB 每 bank 项数、类型预测器端口）。
- IQ 项按队列类型专门化字段，用 RTL 估算位宽。
- 实验：lean2 省下的面积挪给 ROB（160/192）。

---

## EXP-001 面积优化三个方向

- **日期**：2026-11-04
- **分支**：trace-model `exp/area-explore`（从 `main` `41a5cdd` 切出；改动**未提交**）
- **问题**：
  1. BPU 侧的预测 FIFO（PTAB）能否与 pre-IDU 的 FTQ 合并？
  2. LSU 端口（4 LD + 4 STA + 4 STD）是否过多？
  3. LD IQ 和 STA IQ（各 64 项）能否合并？

### 方法

插桩和开关，默认全部关闭：

| 开关 | 类型 | 默认 | 作用 |
|---|---|---|---|
| `ARCH_STATS=1` | 环境变量 | 关 | 每拍统计 FIFO/FTQ/IQ 占用、各类端口每拍发射数、分派阻塞原因，结束时打印 `[AS]` 行 |
| `UFTQ_CAP=N` | 环境变量（需 `ARCH_STATS=1`） | 关 | 模拟统一 FTQ：PTAB + front2back + 保持寄存器 + FTQ 总占用 ≥ N−1 时 BPU 停顿 |
| `CFG_LD_PORTS` / `CFG_STA_PORTS` / `CFG_STD_PORTS` | 编译宏 | 4/4/4 | 访存发射端口数（1–4） |
| `CFG_LD_IQ_SIZE` / `CFG_STA_IQ_SIZE` / `CFG_STD_IQ_SIZE` | 编译宏 | 64/64/64 | 各 IQ 容量 |
| `CFG_MERGE_LDSTA` + `CFG_MEM_IQ_SIZE` | 编译宏 | 0 / 64 | LD 和 STA uop 进同一个 IQ，向 LD 端口和 STA 端口发射（端口仍分开） |

- 改动的文件：`include/ArchStats.h`（新）、`include/config.h`、`front-end/front_top.cpp`、`back-end/PreIduQueue.cpp`、`back-end/Isu.cpp`、`back-end/include/IssueQueue.h`、`back-end/Dispatch.cpp`（IQ 合并时的路由 `route_iq`，ROB 完成掩码仍按原 IQ 计算）、`rv_simu_mmu_v2.cpp`、`main.cpp`；脚本 `scripts/area/{build_variants,run_set,summarize}.sh`。
- **默认配置验证**：开关关闭和 `ARCH_STATS=1` 两种情况 gate 都是 62/62，周期与基线完全一致。
- **负载**：dhrystone（150,838 拍）、coremark（226,991）、memory-stress-small（189,128）、matmul_fpu（42,253）、prime（11,760）。大程序（cjpeg、linear_alg、parser、sha、memory-stress、Linux）**没有跑**。
- **复现**：
  ```bash
  cd trace-model
  bash scripts/area/build_variants.sh                    # 各变体编进 build_area/<名字>
  bash scripts/area/run_set.sh build/simulator <out>/base
  bash scripts/area/run_set.sh build/simulator <out>/uftq64 UFTQ_CAP=64
  bash scripts/area/run_set.sh build_area/m64/simulator <out>/m64
  bash scripts/area/summarize.sh <out> uftq64 m64 ...
  ```

### 模型近似（结论的局限）

- `UFTQ_CAP` 不是真正的统一 FTQ：PTAB(16) 和 front2back(32) 的原有容量限制还在，只是在其上加一个总量上限；用上一拍的占用判断，有一拍滞后；取指地址 FIFO 没有并入。
- 端口数只改了发射端口和由它派生的 LSU/DCache/DTLB 端口数，**没有建模**端口减少后可能带来的频率提升或流水线变化。
- 负载都很小：prime 只有 1.2 万拍，±1.5% 以内基本是错误路径造成的噪声；memory-stress-small 是合成测试。
- 面积只按存储位数估算，**没有综合**；端口带来的多端口读写、比较器、选择逻辑只做定性分析。

### 基线观察（`ARCH_STATS=1`）

- 前端各 FIFO 经常打满（dhrystone：PTAB p90=14/16，front2back p90=31/32，FTQ p90=58/64）。原因是后端 ibuf(128) 满了在反压，并不是真需要这么多缓冲。三处加起来的预测信息占用 p99 = 111（上限 112）。
- 访存发射：dhrystone 平均每拍 LD 0.76 条、STA 0.53 条、STD 0.48 条；每拍发 3–4 条 LD 的周期约占 6.5%，3–4 条 STA 约占 8%。
- 基线下**分派从未因 IQ 满而阻塞**；coremark 有 4.5% 的周期因 LDQ 满阻塞。LD IQ 的占用受 LDQ(64) 限制，STA IQ 的占用受 STQ(64) 限制。

### 结果 1：PTAB + front2back + FTQ 合并为统一 FTQ

位宽来自 RTL（`rtl/rtl/frontend/front_pkg.sv`、`rtl/rtl/backend/pre_idu_queue/`），手算，未编译确认：

| 结构 | 现状 | 合并后 |
|---|---|---|
| PTAB | 16 × 704b = 11,264b | 去掉 |
| front2back FIFO | 32 × 976b = 31,232b（预测相关 22,528b） | 32 × 278b = 8,896b（指令 + ftq_idx） |
| FTQ | 64 × 1824b = 116,736b | 64 × 704b = 45,056b |
| 合计 | 159,232b | 53,952b（−66%） |

- **与合并无关、零性能风险的部分**：FTQ 每项按 `BACKEND_FETCH_WIDTH=16` 存 16 个槽，但前端每组最多 8 条（`FETCH_WIDTH=8`），第 8–15 槽永远无效。每个槽又各存一份 PC，其实就是 base+4i。只把 FTQ 改成 8 槽、存 base pc，就从 116,736b 降到 45,056b。PC 数组有 19 个读端口（ALU/BR 10 + ROB 1 + 提交 8），改成只读 32 位 base 后读口也会小很多。
- **已验证**（2026-11-04）：`BACKEND_FETCH_WIDTH=16` 是遗留参数，前端都按 8 来。新增开关 `CFG_BACKEND_FETCH_WIDTH`（默认 16），设成 8 后 gate 62/62，5 个负载的周期全部不变。可以直接把它改成 8（或等于 `FETCH_WIDTH`），FTQ、ibuf 偏移位、前后端接口随之减半。
- 合并后 FTQ 要多一个写端口，供预译码检查器回写纠正后的方向和下一取指地址。

| 统一 FTQ 容量 | dhrystone | coremark | memory-stress-small | matmul_fpu | prime | 几何平均 |
|---|---|---|---|---|---|---|
| 96 | +0.00% | +0.00% | 0 | 0 | +0.00% | +0.00% |
| 80 | +0.00% | +0.00% | 0 | 0 | −0.36% | −0.07% |
| 64 | +0.00% | +0.00% | 0 | 0 | −1.45% | −0.29% |
| 48 | +0.06% | +0.98% | 0 | +0.01% | −0.17% | +0.18% |
| 32 | +1.22% | +1.53% | 0 | +0.11% | −1.51% | +0.26% |

**结论**：统一 FTQ 64 项性能不变，建议做。

### 结果 2：LSU 端口数（LD/STA/STD）

| 端口 | dhrystone | coremark | memory-stress-small | matmul_fpu | 几何平均 |
|---|---|---|---|---|---|
| 4/4/4（基线） | 150,838 | 226,991 | 189,128 | 42,253 | — |
| 4/3/3 | +0.10% | +0.00% | 0 | +0.11% | +0.04% |
| 4/3/2 | +0.16% | +0.77% | 0 | +0.18% | +0.22% |
| 4/2/2 | +1.57% | +0.93% | 0 | +0.28% | +0.56% |
| 3/3/3 | +1.07% | +1.08% | 0 | +0.11% | +0.45% |
| 3/2/2 | +2.56% | +0.55% | 0 | +0.28% | +0.68% |
| 2/2/2 | +7.12% | +1.71% | 0 | +0.28% | +1.79% |
| 4/1/1 | +12.66% | −0.58% | +10.25% | +0.75% | +4.47% |
| 3/1/1 | +13.91% | +0.95% | +10.25% | +0.75% | +5.02% |
| 2/1/1 | +20.42% | +1.29% | +10.25% | +0.75% | +6.26% |

每个端口牵动：LD → AGU、DTLB 查找口（现在共 8 个）、DCache 读口、STQ 转发比较、load 写回和唤醒广播（每个 IQ 项的源操作数都要比较）；STA → AGU、DTLB 查找口、DCache 写口、LDQ 顺序检查比较；STD → PRF 读口、STQ 数据写口。

**结论**：4/3/3 基本免费（省 2 个端口）；4/2/2 代价 0.6–1.6%（省 4 个端口）。LD 不要降到 2，STA/STD 不要降到 1。

### 结果 3：LD IQ 与 STA IQ 合并

| 配置 | 总项数 | dhrystone | coremark | 其余三个 | 几何平均 |
|---|---|---|---|---|---|
| 分开 64+64（基线） | 128 | — | — | — | — |
| 合并 64 | 64 | −0.03% | −0.05% | 0 | −0.02% |
| 合并 48 | 48 | −0.03% | +0.54% | 0 | +0.10% |
| 分开 32+32 | 64 | +0.00% | +3.38% | 0 | +0.67% |
| 合并 32 | 32 | −0.03% | +3.61% | 0 | +0.71% |
| 分开 16+16 | 32 | −0.09% | +5.94% | ≈0 | +1.15% |
| 合并 48 + 端口 3/2/2 | 48 | +2.45% | +2.55% | ≈0 | +1.05% |
| 合并 32 + 端口 3/2/2 | 32 | +2.45% | +2.89% | ≈0 | +1.12% |

**结论**：合并成 64 项，IQ 项数减半，没有性能损失；同样的总容量下合并明显比分开好。入队写端口从 8+8 降到 8。可以在共享存储上保留两个独立选择器（只挑 LD / 只挑 STA），选择复杂度不变。与端口裁剪叠加有交互：合并 48 + 3/2/2 在 coremark 上比单独减端口差 2 个百分点；合并 64 + 减端口的组合还没测。

### 后续

- 在大负载（Linux 启动片段、SPEC 检查点）上复核三组结论。
- 测合并 64 项 IQ + 端口 4/3/3、4/2/2 的组合。
- 真正实现统一 FTQ（去掉 PTAB、front2back 只存指令和 ftq_idx），替代 `UFTQ_CAP` 近似。
- 有综合流程后，用面积数字代替存储位数估算。
