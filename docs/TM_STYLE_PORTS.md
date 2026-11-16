# trace-model 前端对象化、风格统一、模块端口合入 main（2026-11-16）

分支 `exp/front-io`（从 trace-model main `47cda8d` 起，9 个提交，依次经过 exp/front-obj、exp/style、exp/back-ports）快进合入 trace-model main `efb0800`。目标：在模块契约的基础上，让每个模块的写法、命名、端口和状态归属一致，去掉遗留写法；每个提交周期都与基线逐一相同。规则写在 trace-model 的 `docs/STYLE.md`，各步过程见 `docs/MODULE_CONTRACT.md`。

## 提交

| 提交 | 内容 |
| --- | --- |
| 9dc8789 | 前端对象化：`FrontCore` 持有前端寄存器、BPU 流水、FIFO、I-cache（`ICacheTop`）、预取器，前端不再有文件作用域状态 |
| 9a71bd8 | 机械风格统一（新增 `docs/STYLE.md`）：只用 `wire<N>` / `reg<N>`、类型 CamelCase、comb 阶段名 `comb_*`、错误统一 `fatal()`、代码注释英文、所有权用 `unique_ptr` |
| 57820f7 | 后端模块自带端口：`struct In`（const 指针）/ `struct Out`（自己驱动），在 `BackTop::init` 绑定；共享的 `Wires` 改为只剩顶层几项的 `BackPorts` |
| 0e5edb7 | 结构体不再 `memset`：改为 `= {}`、成员初始化或循环；整型数组、LSU 的 0xA5 毒化填充（调试手段）和内存页保留 memset |
| e27c5f2 | `FrontTopIn` 分组：`ctrl`（reset / itlb_flush / fence_i / fifo_read_enable）、`redirect`、`train[COMMIT_WIDTH]` |
| 8bb2d4e | 前端各条目 FIFO 的输入统一为 `FifoIn<Entry>`：控制（reset / refetch / read_enable / write_enable）+ 写入条目 |
| 1cfa98b | 环境变量集中在 `include/env.h`（`SimEnv`，`docs/ENV_VARS.md` 列出全部）；其余文件作用域状态移入所属模块 |
| 8b1f2a2 | D-cache 的 tag / valid / dirty / PLRU 数组归 `DcacheArrays`，由 `RealDcache` 持有 |
| efb0800 | LSU 按阶段拆文件：`RealLsuPipe.cpp`（时钟沿、组合）+ `LsuPipeOutputs` / `Writeback` / `Translate` / `Requests.cpp`，公共函数在 `LsuPipeInternal.h` |

## 结果

| | 合入前 47cda8d | 合入后 efb0800 |
| --- | --- | --- |
| 模块间信号 | 后端各模块直接读写共享 `Wires` | 每个模块 `In` / `Out` 端口，父模块 init 绑定 |
| 文件作用域可变状态 | 前端、ISU 忙表、LSU 访存依赖预测器、D-cache 数组、各处 getenv | 只剩 uop 池、功能内存绑定、`sim_time`、PMU 事件总线（STYLE.md 列为例外） |
| 结构体 memset | 多处 | 无（例外见上） |
| 源码行数（.cpp/.h，不含 third_party） | 30385 | 30256 |

契约检查（`comb_graph.py --check`）对端口写法同样适用：扫描器把 `in.x` / `out.x` 换算回信号名后核对，生成的调度不变。

## 和 RTL 的关系

`include/config.h` 未改，生成的 `ttg_cfg_pkg.sv` 不变；周期不变，`rtl/scripts/ref_cycles.txt` 不变。

## 验证（rv64）

每个提交：RVC=0 门禁 62/62、RVC=1 门禁 67/67，周期等于基线；`comb_graph.py --check` 0 隐患；`FPR`（rvc-mem / fd-rvc-mem，前端改动加 rvc-alu / rvc-flow）逐字节相同；后端端口与 LSU 改动时 `TB_TRACE_COMMIT`（md5 d170a8a9…）/ `LSU_PIPE_EVT`（md5 5b630b50…）逐字节相同。FE_PAIR=1、FE_IPF=1 全量比较相同（fact 除外，基线上也跑不完）。rv64gc Linux（2 亿周期）控制台在前端对象化、风格统一、后端端口、FIFO 输入、LSU 拆分（efb0800）各步都与基线相同。

## 未做

- 长函数拆分、运行时写后读检查。
- 性能：trace bridge 改为单字段读取和条目池（exp/bridge-fast + function-model exp/step-access），以及共用译码器 `decode_inst`，另行验证后合入。
