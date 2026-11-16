# trace-model 模块契约合入 main（2026-11-16）

分支 `exp/module-contract`（从 trace-model main `102cc87` 分出，18 个提交）快进合入 trace-model main `47cda8d`。目标：每个模块写法一致，寄存器 / 连线 / 时钟沿一眼可分；每个 comb 阶段在头文件里声明读写的信号，由工具核对代码并生成调度顺序，不再手排；每个提交周期都与基线逐一相同。详细过程见 trace-model 的 `docs/MODULE_CONTRACT.md`。

## 结果

| | 合入前 102cc87 | 合入后 47cda8d |
| --- | --- | --- |
| 寄存器写法 | 后端各模块不一（`_1` 配对、`cur`/`nxt`、直接改） | 全部 `Regs q_`（私有，只在 seq / init 写）+ `Regs d`（comb 写），comb 内 `const Regs &q = q_` 只读 |
| 声明了读写接口的 comb 阶段 | 0 | 后端 23、访存 11（块方法 9 个在各自头文件）、前端 9、SimCpu 顶层 11 |
| 由声明生成的调度 | 无（全部手排） | `BackTop::comb()`、`MemSubsystem::comb_outputs / comb_inputs`、`front_comb_calc()`、`SimCpu::cycle()` 的 comb 部分 |
| 检查 | 读写隐患扫描 | 隐患扫描 + 声明与代码逐项一致 + 一信号一写者 + 生成块未被手改（`comb_graph.py --check`，verify.sh 每次运行） |
| 源码行数（.cpp/.h，不含 third_party / function-model） | 30176 | 30385 |

## 方法

- 每个阶段一行 `CONTRACT <阶段>  in: <读的信号>  out: <写的信号>`，写在被描述代码的头文件里，用那段代码自己的名字（后端模块用 Wires 名，访存块用自己的 `in.*` / `out.*` 端口，由 `MemSubsystem::init` 的绑定换算）。
- 生成规则：同一模块的阶段按头文件顺序；写者在所有读者之前；有代码外副作用的 trace bridge 用户按声明顺序；同序时按固定优先级。
- 层次化：每个顶层用 `EXPORT` 声明对外阶段（`in` / `pre` / `out` / `default`），端口表在 `include/SimCpu.h`。顶层之间出现环时，把一个阶段拆开（如访存的响应 / 请求）；访存的 outputs / inputs 拆分由声明推出，拆不开即真组合环。
- 工具：`scripts/comb/gen_comb_order.py`、`gen_mem_order.py`、`gen_front_order.py`、`gen_top_order.py`（共用 `contract_lib.py`），`--write` 重写生成块，`--emit` 由代码打印声明草稿。

## 过程中找到并改正的问题（周期不变）

- 在 comb 里直接改寄存器：Rename `arch_cnt`、ROB 死锁计数、ISU flush 清流水寄存器、前端 PMU 的函数内 static。
- seq 里带逻辑：PreIduQueue `flush_q`、CSR 的 FS/SD 脏位、PTW 的 walk flush（都改到 comb 里写 d）。
- 一个信号多个写者：BackTop 改写 ROB 的输出（死写）、BackTop 直接写 CSR 内部（改成端口）、MMIO 响应写进后端输入后又拷贝、访存改 MSHR 的 fill 请求 dirty 位（改成单独连线）、I-cache 复位写互联的 accepted（死写）、I-cache K 步覆盖 R1 输出（改写 `ic_k`）、前端预取候选与前端寄存器共用一个请求。
- 扫描看不到的写：指针别名（`back.out.fire`）、局部引用别名（多处），全部改成直接写。
- 结构：前端 BPU 原来有时在读 FIFO 之前、有时在之后跑，现在固定为 control → BPU → 读 FIFO（含 PTAB 写口和队头修正）→ …；BPU 流水的 transaction 归 BpuPipe 自己作为 d。

## 和 RTL 的关系

`include/config.h` 未改，生成的 `ttg_cfg_pkg.sv` 不变；周期不变，`rtl/scripts/ref_cycles.txt` 不变。

## 验证（rv64）

每个提交：RVC=0 门禁 62/62、RVC=1 门禁 67/67，周期等于基线；`comb_graph.py --check` 0 隐患、0 声明不一致；BPU 对齐指纹 `FPR` 在 rvc-alu / rvc-mem / fd-rvc-mem / rvc-flow 上逐字节相同；后端调度重排时 `TB_TRACE_COMMIT` / `LSU_PIPE_EVT` 逐字节相同。rv64gc Linux（2 亿周期）控制台在 f158314、4140c5d、0ab610a、92bfe27、47cda8d 上都与基线相同。前端改动另外验证：FE_IPF=1 在 67 个 RVC 程序上相同，FE_PAIR=1 相同（fact 在基线上也跑不完，前 200 万周期提交流相同；中途发现并改正了一处多块掩码顺序错误）。

## 未做 / 例外

- Exu 功能单元状态原地更新（q/d 拷贝代价 8–13%）；MSHR / 写缓冲在 d 上原地更新。
- AXI 套件内部的隐藏寄存器；顶层 AXI 端口按名字别名区分 master（扫描不保留 master 编号）。
- 前端的 FIFO、I-cache、`bpu_pipe` 仍是文件级全局对象；I-cache 模块内部按 RTL 写，未纳入声明。
- debug 下"本拍读之前已写"的运行时检查未做；顶层 trace bridge 顺序是声明的，未扫描。
