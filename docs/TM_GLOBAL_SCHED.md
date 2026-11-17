# trace-model 全局调度、统一模块写法、下一状态在 seq、提速（2026-11-17）

trace-model 分支 `exp/global-sched`（从 main `a127371` 起，43 个提交）快进合入 trace-model main `83af731`。除最后一处 LSU 建模修复外，每一步周期都与基线逐一相同。trace-model 里的详细说明：`docs/MODULE_CONTRACT.md`（全局调度部分）、`docs/FRONT_MODULES.md`、`docs/UNIFIED_MODULES.md`、`docs/NEXT_STATE.md`。

## 做了什么

| 阶段 | 提交 | 内容 |
| --- | --- | --- |
| 一张调度表 | 1c0ed36 … 7efc68c | 各层的 comb 阶段放进一张依赖图；后端、访存、前端的阶段都提到 `SimCpu::cycle()` 一级，顺序由声明生成；BackTop / MemSubsystem 自己的 comb 函数去掉 |
| 顶层胶合逻辑成模块 | bf8800b … 48dfac3 | `Front2Back`、`Back2Front` 两个模块（对应 RTL 的 core_front2back / core_back2front）；SimCpu 自己不再有寄存器 |
| 每拍默认值 | 74bb5a6 … 7127469 | 每拍只清 valid / 使能位，不清整个大结构（前端更新请求 3.1 KB、AXI 主端口、D-cache 等） |
| 前端拆成模块 | 7f59e8c … b444ed5 | FrontControl、BpuPipe、四个 FIFO 端口、ICacheTop、FrontChecker；FrontComb 和 FrontUpdateRequest 删除 |
| 统一写法 | 9038906 … c9539a3 | 所有模块同一种写法：In / Out 端口、头文件里用自己的端口名写 CONTRACT、父模块一行绑一个端口；一个扫描器 `scripts/comb/modules.py`、一个生成器 `gen_top_order.py`；访存、AXI、I-cache / TLB 遍历端口都成为模块端口；删除 gen_mem_order / gen_comb_order / gen_front_order / comb_order / global_graph |
| 删死代码 | c984a0c | 用 -O0 构建找出定义了但没有被任何目标文件用到的 13 个函数 |
| 去掉 d | 9706b0d … d01f58e | ROB、IDU、Dispatch、EXU、ISU / 发射队列、Rename、PreIdu / FTQ、访存路由、PeripheralAxi、Back2Front、Front2Back：comb 只算输出和几个具名线信号，seq 原地更新寄存器（需要旧值时取局部快照），不再有整份 d 的拷贝和脏位跟踪 |
| 前端 FIFO 不拷条目 | 3f81a6e | 读数据和请求改为指向条目的指针，只在时钟沿拷贝队头输出和压入的条目 |
| CSR 成为共享状态 | 46216dd | CSR 不再是模块：状态视图和待处理中断在 seq 由寄存器导出，trap / xRET 目标是 `trap_out()` 常函数；`csr_status`、`CsrRobIO`、`CsrFrontIO` 端口删除 |
| BPU 历史压入 | f11f934 | TAGE 配置和环形掩码每次压入只读一次 |
| uop 只带 id | f533fa8 | 只写一次的字段（`dest_preg`、`rob_idx/flag`、`stq/ldq` 下标、`expect_mask`、TMA）放进 `uop_pool[id]`，uop 和 LSU 写回只带 id 和自己的动态位 |
| 每拍扫描改查表 | 301ecce | LSU 看门狗改为发送时间戳、只在最早到期那拍扫描；trace bridge 按 uid 直接映射查找；唤醒总线成员改为每个物理寄存器的 epoch 标记 |
| BPU 原地更新 | 51e64d4 | BPU 寄存器不再双缓冲（每拍省约 5 KB 拷贝）；PTAB 检查点、uBTB 训练队列改为环形；事务只清使能 |
| LSU 建模修复 | cb80789 | LSU_MS_DATA：比基准 store 年轻、已完成的 store 也叠加到 load 的值上（来自 main-check 的 `ms_done_fix.patch`） |
| 文档 | 72f472b、b444ed5、83af731 | UNIFIED_MODULES.md、FRONT_MODULES.md、NEXT_STATE.md |

## 结果

| | 合入前 a127371 | 合入后 83af731 |
| --- | --- | --- |
| dhrystone 用时（1,526,122 周期，同机交替测） | 7.85 s | 6.3 s（快约 20%） |
| SimCpu 一级的 comb 阶段 | 各 top 内部手写调度 | 48 个，全部由模块声明生成、由 `comb_graph.py --check` 核对 |
| 模块 | 后端 / 前端 / 访存各一套写法 | 25 个模块同一种写法（后端 8、前端 8、访存 6、顶层 3） |
| 源码行数（.cpp/.h，不含 third_party / function-model） | 30039 | 30070（另删 5 个调度脚本） |
| dhrystone / memory-stress-small 周期（IPC） | 1,526,122 (2.98) / 327,170 (3.21) | 相同 |

## 验证（rv64gc）

- 每几步一次完整比对（`AI-Huma-data/tm-simplify/vbin.sh`）：RVC=0 门禁 62/62、RVC=1 门禁 67/67，周期等于基线；FPR（rvc-alu / rvc-mem / fd-rvc-mem / rvc-flow）逐字节相同；`TB_TRACE_COMMIT`、`LSU_PIPE_EVT` 逐字节相同；Linux 检查点（第 4000 万条指令，300 万条）相同；FE_PAIR=1、FE_IPF=1 在 67 个程序上周期相同。最后一次完整比对在 51e64d4 上全部相同。
- 看门狗、bridge 查表、唤醒标记三处先和旧代码并存、逐拍断言比较（两个门禁和 Linux 检查点），再删掉旧代码。
- Linux 窗口和 RTL 对比（`linux_segments_cmp.sh` 的 13 个窗口，复用 main-check 在 main 上跑的 RTL 输出，只重跑模型一侧）：**13/13 PASS**。12 个窗口的模型指纹和 main 的模型逐字节相同；s03 在 main 上 PT / UP 指纹从第 2545 个 bin 起和 RTL 不同，加上 LSU 修复后和 RTL 相同（不含修复的 51e64d4 在 s03 上和 main 的模型逐字节相同，差异只来自修复）。
- rv64gc Linux 2 亿周期控制台（`scripts/linux_check.sh`，cb80789）：登录成功、无 oops / panic，控制台文本与基线 595e4a7 相同；只有每 1000 万周期的进度标记插在控制台输出里的位置挪了一个字符（第 1.1 亿周期附近一个字符早晚一点输出），来自 LSU 修复对 Linux 时序的影响，与 s03 的变化一致。
- `comb_graph.py --check`：0 隐患、0 声明不一致。

## 和 RTL 的关系

`include/config.h` 未改，生成的 `ttg_cfg_pkg.sv` 不变；门禁程序周期不变，`rtl/scripts/ref_cycles*.txt` 不变。LSU 修复让模型在 Linux 窗口 s03 上与 RTL 一致，RTL 未改。

## 没做的

- 同一模块内 comb 阶段合并（取址 / 指令 / f2b 端口、I-cache、rename、dispatch、LSU 的 translate 和 requests）。
- D-cache、MSHR、写缓冲、LSU 的 d：它们的 d 是真正的同拍线信号，要逐个改成具名线信号。
- BPU 的 S1 原始读数据（每块 2.7 KB）仍整块存进流水寄存器：表在 S1 读，之后可能被写。
