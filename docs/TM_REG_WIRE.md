# trace-model 组合逻辑整理合入 main（2026-11-16）

分支 `exp/tm-reg-wire`（从 trace-model main `fb471da` 分出，21 个提交）快进合入 trace-model main。目标：comb 只在一拍内按依赖计算、seq 只在时钟沿锁存；comb 阶段按依赖而不是按功能拆分；每个提交周期都与基线逐一相同。详细过程见 trace-model 的 `docs/REG_WIRE.md`。

## 结果

| | 合入前 fb471da | 合入后 |
| --- | --- | --- |
| 后端 comb 阶段（`BackTop::comb()` 的调用） | 69 | 23 |
| 后端模块间连线边 | 44 | 42（BackTop 自身阶段现在也计入；原先扫描为空） |
| 内存子系统 comb 阶段 | 29 | 11 |
| 组合顺序检查覆盖 | 后端 | 后端、前端、内存子系统、顶层 `SimCpu::cycle()` |
| 隐藏寄存器（读到上一拍值的 comb 读） | 后端 0，其余未检查 | 四个域都为 0（AXI 套件内部的少数几处列为已知） |
| rvc-alu / rvc-mem / fd-rvc-mem cycles/s | 338k / 254k / 272k | 355k / 265k / 284k |

## 内容

- 检查工具：`scripts/comb/comb_graph.py` 扩展到前端、内存子系统（按 `in`/`out` 指针绑定）和顶层（按 `SimCpu` 路径展开调用）；`scripts/comb/comb_order.py` 按读写依赖（以及模块私有状态、跨模块直接访问、trace bridge 的约束）排出 comb 顺序。
- 显式寄存器：DCache stage1→stage2（`dcache_s1_q_`）、I-cache 读内存响应的端口寄存器（`icache_axi_q` / `icache_resp_q`）；walk port 输出在 seq 锁存；I-cache 改成 RTL `icache_ctl.sv` 的写法（取指一步 R1，预译码 flush 时 K(R1)，只在时钟沿锁存一次，同拍读表走写转发）。
- 去掉同拍请求/响应线对和多余拷贝：FTQ PC 读端口、CSR 读、DTLB 查询改为直接读；PRF 模块并入 EXU；AXI 主端口由 MSHR / 写缓冲 / MMIO 直接驱动（去掉 8 个中间结构和 bridge）；DCache 响应缓冲合成一个函数；前端 FIFO 改成读口 / 写口（不再每拍算两遍）。
- 按依赖合并：后端每个模块在一拍内连续执行的阶段合成一个方法（如 LSU 的 `comb_outputs / comb_writeback / comb_translate / comb_requests`），内存子系统按模块组织；前后端之间的接口逻辑从 SimCpu 移到 `FrontTop::comb` / `comb_from_back`。

## 和 RTL 的关系

`include/config.h` 未改，用合并后的模型生成的 `ttg_cfg_pkg.sv` 与合入前名字和值完全相同；周期不变，`rtl/scripts/ref_cycles.txt` 不变。一处只在 AXI 端口上可见、无人读取的值变化：MMIO 写数据原先经 bridge 拷贝后恒为 0，现在是真实值（AXI UART 从不输出，控制台日志无变化）。

## 验证（rv64）

每个提交：RVC=0 门禁 62/62、RVC=1 门禁 67/67，周期等于基线；`comb_graph.py --check` 0 隐患；BPU 对齐指纹 `FPR` 在 rvc-alu / rvc-mem / fd-rvc-mem / rvc-flow 上逐字节相同；`TB_TRACE_COMMIT` / `LSU_PIPE_EVT` 在重排后逐字节相同。rv64gc Linux（2 亿周期）控制台输出在每一步都与基线相同；最后两步（I-cache 按 RTL 重写 7e9f34d、顶层 glue 102cc87）在合并时已过登录提示（1.4 亿周期）、控制台与基线一致，2 亿周期的完整比对在合并后完成。I-cache 改写另外验证：FE_IPF=1 在 67 个程序上与基线一致，FE_PAIR=1 在能跑完的 64 个程序上一致（fact / prime / recursion 开 FE_PAIR 时基线本身也跑不完；fact 在 500 万周期内的提交流完全相同）。

未做：`Wire<T>` / `Reg<T>` 和 debug 下的动态写读检查（能查出"只在某些拍写"的信号，如 PMU 读到上一拍 `g_pipe_txn` 的问题）、AXI 套件内部寄存器显式化、RTL 侧删除模型已不实现的变体。
