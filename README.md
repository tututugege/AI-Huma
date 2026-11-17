# AI-Huma

AI-Huma 是一个乱序 RISC-V CPU 的设计项目：人定方向和验收标准，AI 做大部分设计、验证和实现工作。

我们从一个已有的开源模拟器（tututugege/simulator，RTL 风格、周期精确的 C++ 乱序核）出发，先把它变成自己的起点：蒸馏出快速、可读的时序模型 trace-model，逐模块翻译出 RTL，再配上功能模型 function-model 做正确性对照。这一步在 2026-11-04 完成，**它只是开始**。

现在项目的重心是**自己的优化**：每个想法先在 trace-model 上量化（性能、面积代价），结论再同步到 RTL，用功能模型保证正确，记录下来，合入 main。第一项落地的成果是“第 3 批面积配置”（[EXP-005](docs/EXPLORATION.md)）：IPC 只降 0.5%，受影响模块少了约 17% 的门。长期目标是让三个模型协同迭代，成为 Agentic CPU 训练大师。

## 名字的由来

AI-Huma 有两层意思：

1. **AI + Human**：项目由人定方向、定验收标准，AI 做大部分设计、验证和实现工作。
2. **Al-Huma(**アル・ヒューマ**)**：致敬作者最喜欢的动漫角色雷姆（Re:Zero）的魔法。

## 发展阶段

| 阶段 | 时间 | 做了什么 |
|---|---|---|
| 建立起点 | 至 2026-11-04 | 从 tututugege/simulator 蒸馏出 trace-model（代码从约 8.4 万行降到 4.3 万行、更快，周期与原模型完全一致）；逐模块翻译出 RTL，与原模型逐拍对照；接入 function-model。逐拍对照体系完成使命后退役（rtl `docs/history/`、标签 `legacy-reference`）。 |
| 自主优化 | 2026-11-04 起 | 正确性改为对照 function-model，周期不再要求与原模型一致；建立探索 → 验证 → 合入 main 的流程（[WORKFLOW.md](docs/WORKFLOW.md) 第 4–6 节）；重建 SPEC 检查点。已合入 main 的优化（逐项数字见 [MAIN_RECORDS.md](docs/MAIN_RECORDS.md)）：第 3 批面积配置（EXP-005）、DRAMsim3 DDR 内存模型并去掉 AXI 分频（EXP-006，新基线）、mov 消除（EXP-012）、L1D 数据预取器 h1（EXP-009）、PMU（EXP-013）、分级 LSU + 流水化 BPU（EXP-015）、后端 DSE 支持代码（EXP-016）、IQ 入队宽度（EXP-017）、访存推测与前端快速通路（EXP-019/020/023）、已提交 store 的 write buffer（EXP-024）、多表间接跳转预测 ITT（EXP-025）、删除 0x87f00000 非缓存窗口（EXP-027）、紧凑 ROB（EXP-028）。待做见 [TODO.md](docs/TODO.md)。 |
| rv64 | 2026-11-11 起 | 从 rv32imab 迁移到 rv64imab + Sv39（EXP-029），后加 F/D、C（rv64gc）；**2026-11-16 起 main 只有 rv64gc，rv32 在各仓库分支 `rv32-legacy`**（见 [docs/RV32_REMOVAL.md](docs/RV32_REMOVAL.md)）。 |
| trace-model 结构整理 | 2026-11-16 至 11-17 | 周期全程不变的四次整理：去掉执行驱动时代的残留（[TM_CLEANUP.md](docs/TM_CLEANUP.md)）；环境变量 77 → 16、开关和变体精简（[TM_SIMPLIFY.md](docs/TM_SIMPLIFY.md)）；comb 只在一拍内按依赖计算、seq 只在时钟沿锁存，后端 comb 阶段 69 → 23（[TM_REG_WIRE.md](docs/TM_REG_WIRE.md)）；模块契约：寄存器统一为 `Regs q_, d`，每个 comb 阶段在头文件声明读写的信号，后端、访存、前端和 `SimCpu::cycle()` 的调度都由声明生成、由工具核对（[TM_MODULE_CONTRACT.md](docs/TM_MODULE_CONTRACT.md)）；一张全局调度表、25 个模块同一种写法、大部分模块的下一状态在 seq 原地更新、uop 只带 id、每拍扫描改查表，dhrystone 模拟快约 20%（[TM_GLOBAL_SCHED.md](docs/TM_GLOBAL_SCHED.md)）。模型 .cpp/.h 约 3.0 万行。 |

## 三个部分

| 部分 | 目录 | 作用 |
|---|---|---|
| **function-model** | `function-model/` | 功能模型：只管指令执行的结果（寄存器、访存、CSR、分页），不管时序。基于 tututugege/GenSimpoint，库名 `librefcpu`；main 上为 rv64gc（`XLEN=64`、`FP=1`；`RVC=1` 构建带 C 扩展的版本）。也负责 SPEC 的 BBV/SimPoint/检查点生成。 |
| **trace-model** | `trace-model/` | 我们的时序模型和架构探索平台：起点由 tututugege/simulator 蒸馏而来，不计算数据值，分支方向/目标、地址、store 数据、CSR 写数据都来自功能模型提供的“事实”，只保留周期精确的时序行为。核参数的唯一来源（`include/config.h`）；运行时开关全部列在 [trace-model/docs/ENV_VARS.md](trace-model/docs/ENV_VARS.md)（16 个环境变量）。模块写法和 comb 调度的规则见 [trace-model/docs/MODULE_CONTRACT.md](trace-model/docs/MODULE_CONTRACT.md)（调度由模块声明生成，`scripts/comb/comb_graph.py --check` 核对）。 |
| **rtl** | `rtl/` | 我们的 SystemVerilog 实现（346 个 RTL 文件、约 3.9 万行）：起点由原模型逐模块翻译，现在随优化独立迭代；整核测试平台（Verilator）逐条提交对比 function-model；参数包由 trace-model 的 `config.h` 生成。 |

三者的关系：function-model 定义“对不对”（架构行为），trace-model 定义“快不快”（周期）并用来做架构探索；rtl 的架构行为必须与 function-model 一致，合入 main 时同一配置下的周期必须与 trace-model（设 `LSU_PIPE_NOWD=1`）逐个程序相等。

## 仓库结构

`AI-Huma` 本身是**总仓库**，只放全项目文档（`docs/`）、脚本（`scripts/`）和忽略规则；三个子项目是各自独立的 git 仓库，作为 **git 子模块**引用（`.gitmodules` 指向 `git@github.com:tututugege/AI-Huma-{func,trace,rtl}.git`）。

```text
AI-Huma/
├── README.md, docs/          总仓库文档（导航见 docs/GUIDE.md）
├── function-model/           子模块：功能模型（librefcpu）
├── trace-model/              子模块：时序模型 / 架构探索平台
├── rtl/                      子模块：SystemVerilog + 整核测试平台
├── scripts/gate_all.sh       三个仓库的合入前门禁串联脚本（trace-model / lint / RTL 对 function-model；数字可能落后于当前 gate，用前先看脚本头注释）
└── rtl-*/ trace-model-*/     被 .gitignore 忽略：各实验分支的 git worktree（git worktree add ../<repo>-<名字>）
```

```bash
git clone <AI-Huma 地址>
cd AI-Huma
git submodule update --init          # 取出 function-model、trace-model、rtl
```

- 子模块指针记录的是各子仓库 `main` 上已提交的 commit；分支和合入规则见 [docs/WORKFLOW.md](docs/WORKFLOW.md)。推送由用户决定（2026-11-16：四个仓库的 main 都已推送，总仓库到 `badc3de`）。
- 生成的数据（SPEC 检查点、Linux 镜像）放在 `~/personal/AI-Huma-data/`（如 `linux_rv64/`；rv32 时代的 `spec-rv32imab/`、`linux/` 只对 `rv32-legacy` 有效），构建产物都在各仓库被忽略的 `build*` 目录里，都不进仓库。

## 文档

**从 [docs/GUIDE.md](docs/GUIDE.md) 开始**：它列出全部文档、各管什么、遇到什么事该看哪份。最常用的几份：

- [docs/WORKFLOW.md](docs/WORKFLOW.md)：规则和流程（分支与提交、正确性标准、harness、实验流程、合入 main 的步骤、文档整理）。
- [docs/TODO.md](docs/TODO.md)：全项目唯一的待办清单。
- [docs/MAIN_RECORDS.md](docs/MAIN_RECORDS.md)：每次合入 main 的性能、面积和“变化”；**当前数字以这里为准**。
- [docs/EXPLORATION.md](docs/EXPLORATION.md)：架构探索记录；[docs/LOG.md](docs/LOG.md)：每个 commit 一行。
- [docs/PMU.md](docs/PMU.md)：性能监控单元与 TMA；[docs/SERVER.md](docs/SERVER.md)：云服务器怎么跑 SPEC。
- [trace-model/docs/ENV_VARS.md](trace-model/docs/ENV_VARS.md)：时序模型的全部环境变量（默认值、用途）；[trace-model/docs/MODULE_CONTRACT.md](trace-model/docs/MODULE_CONTRACT.md)：模块写法、接口声明和调度生成。

## 核心原则

- **正确性 = 架构行为与 function-model 一致**（2026-11-04 起）。RTL 整核测试平台每提交一条指令，function-model 执行一条，比较提交 PC 和目的寄存器的值；Linux 从复位启动到登录提示符是整机检查。
- **周期数、IPC 是性能指标，也是优化的对象**。原模型的周期只是起点，不再是标准；探索的结论先在 trace-model 上验证，再同步到 RTL，合入 main 时两者周期逐个相等。
- **旧的逐模块锁步 / trace 回放 / 变异检查体系已退役**（代码在 rtl 标签 `legacy-reference`，文档在 `rtl/docs/history/`）。
- **目标是方法，而不只是代码**：AI 和人能否系统地做 CPU 架构优化——每个想法先在模型上量化，再落到 RTL，保证正确，留下可复用的验证手段和完整记录（包括负面结果）。

## 当前状态（2026-11-16）

README 只写概况，**各次合入的数字、配置变化和已知回退以 [docs/MAIN_RECORDS.md](docs/MAIN_RECORDS.md) 为准**，在做的事见 [docs/TODO.md](docs/TODO.md)。

- **当前配置**（默认开）：第 3 批面积配置（取指宽度 8、在飞分支 32）→ DRAMsim3 DDR4-3200 + 60 ns 非核心延迟、核心 1 GHz、无 AXI 分频 → mov 消除 → L1D 预取器 h1 → 分级 LSU + 流水化 BPU → IQ 入队宽度 INT7/LD6/STA4/STD4/BR5 → 访存推测（`LSU_MEMSPEC`）+ 前端快速通路（`FE_RFAST=15`）→ 已提交 store 的 write buffer（4 项 × 2 store）→ 3 张 × 64 项间接跳转目标表 → 紧凑 ROB（128 项，按序分配、前缀提交）+ 寄存器版 BPU 提交额度。
- **ISA**：main 只有 rv64gc（rv64imafdc + Sv39；`RVC=0` / `RVC=1` 两种构建），rv32 在各仓库分支 `rv32-legacy`。
- **性能**：rv32 时代的 SPEC 估算分数（官方参考时间直接换算，580 个 rv32imab 检查点、快速预热）11.53 分/GHz（EXP-028 合入时）；各次合入对上一次 main 的几何平均 IPC：EXP-027 +10.75%、EXP-028 +2.74%。**rv64 main 还没有 SPEC 分数**（SPEC06 rv64gc 检查点在重建，原 580 个 rv32imab 检查点只能用于 `rv32-legacy`）。**RTL 没有跑过 SPEC**；没有工艺库综合和时序（WNS），只有 yosys 通用门面积代理。
- **C 扩展与 rv64gc 的 RTL（EXP-038、EXP-040，2026-11-15 合入）**：`RVC=1`（C910 式携带）和 rv64gc 的 RTL 与 trace-model 逐周期对齐，含 Linux。快速检查用 `rtl/scripts/linux_segments_cmp.sh`（检查点窗口并行，RTL 对 trace-model），从复位的完整 Linux gate 是最后确认（[docs/WORKFLOW.md](docs/WORKFLOW.md) 第 3.2 节）。
- **trace-model**：gate `RVC=0` 62/62（`run_gate.sh`）、`RVC=1` 67/67（`run_gate_c.sh`），周期等于基线；`comb_graph.py --check` 0 隐患、模块声明与代码一致；rv64gc Linux 启动到 `rv64 login:`（2 亿周期控制台与基线一致）。
- **rtl**：lint 干净（按目录和整芯片）；`fm_gate.sh` 67/67 逐条对比，周期与 trace-model（`LSU_PIPE_NOWD=1`）逐个相等；Linux 从复位一次连续启动到 `rv64 login:`逐条对比 0 不一致；store 数据不在逐条对比范围内。已知风险见 [rtl/docs/08-risk-register.md](rtl/docs/08-risk-register.md)。
- **未合入的实验**：sdip 预取器（EXP-026，`exp/sdip`）、LD/STA IQ 合并与统一 FTQ 的 RTL 试做（见 TODO）、其余探索见 [EXPLORATION.md](docs/EXPLORATION.md) 索引。

## 复现

细节见 `trace-model/docs/PROJECT.md` 和 `rtl/docs/README.md`。要点（rv64）：

```bash
# trace-model 依赖同级的 function-model（trace-model/function-model 是指向 ../function-model 的符号链接）
gmake -C function-model librefcpu.a LDFLAGS="-lz"
cd trace-model
gmake LDFLAGS="-lz" -j8
bash scripts/run_gate.sh build/simulator results/gate      # 62 个程序，周期等于 results/baseline/baseline.csv（默认配置）
python3 scripts/comb/comb_graph.py --check                 # comb 调度与模块声明一致（改了模块后先跑 gen_*_order.py --write）

# rtl：lint，带 function-model 逐条对比的整核门禁（需要先构建 trace-model 的测试程序）
cd ../rtl
bash scripts/lint.sh && bash scripts/lint_chip.sh
SOC_FM=1 SOC_OUT=$PWD/build/soc_fm bash tb/soc/build.sh
bash scripts/fm_gate.sh $PWD/build/soc_fm/obj/soc_tb $PWD/build/gate   # 67/67，并报告与 trace-model 周期不同的个数
```

**C 扩展**（`RVC=1`）：function-model 的 `.o` 在源码目录里，`RVC=1` 的库要在单独的检出（如 `git worktree`）里 `gmake RVC=1 librefcpu.a`，得到的 `librefcpu.a` 用路径传给其他两个仓库；trace-model 用 `gmake RVC=1 REFCPU_LIB=<RVC=1 librefcpu.a> BUILD_DIR=build_rvc LDFLAGS="-lz"`，门禁 `bash scripts/run_gate_c.sh build_rvc/simulator results/gate_c`（67 个程序）。rtl 的 rv64gc / `RVC=1` 构建和 Linux 检查见 [rtl/scripts/README.md](rtl/scripts/README.md)。Linux 镜像在 `~/personal/AI-Huma-data/linux_rv64/`。

**比周期**：对 RTL 或 `ref_cycles.txt` 比周期时，模型要设 `LSU_PIPE_NOWD=1`（关掉 63 周期看门狗，RTL 没有它）。
