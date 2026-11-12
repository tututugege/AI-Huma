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
| rv64 | 2026-11-11 起 | 从 rv32imab 迁移到 rv64imab + Sv39（EXP-029，2026-11-12 合入本地 main）：三个层次都支持，XLEN 是构建参数，默认 32 保持原行为；F/D、C、SPEC rv64 检查点未做。 |

## 三个部分

| 部分 | 目录 | 作用 |
|---|---|---|
| **function-model** | `function-model/` | 功能模型：只管指令执行的结果（寄存器、访存、CSR、分页），不管时序。基于 tututugege/GenSimpoint，库名 `librefcpu`；`XLEN` 编译期参数（默认 32，`-DXLEN=64` 为 rv64imab + Sv39）。也负责 SPEC 的 BBV/SimPoint/检查点生成。 |
| **trace-model** | `trace-model/` | 我们的时序模型和架构探索平台：起点由 tututugege/simulator 蒸馏而来，不计算数据值，分支方向/目标、地址、store 数据、CSR 写数据都来自功能模型提供的“事实”，只保留周期精确的时序行为。核参数的唯一来源（`include/config.h`）；运行时开关全部列在 [trace-model/docs/ENV_VARS.md](trace-model/docs/ENV_VARS.md)（103 个环境变量）。 |
| **rtl** | `rtl/` | 我们的 SystemVerilog 实现（352 个 RTL 文件、约 3.8 万行）：起点由原模型逐模块翻译，现在随优化独立迭代；整核测试平台（Verilator）逐条提交对比 function-model；参数包由 trace-model 的 `config.h` 生成。 |

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

- 子模块指针记录的是各子仓库 `main` 上已提交的 commit；分支和合入规则见 [docs/WORKFLOW.md](docs/WORKFLOW.md)。推送由用户决定（截至 2026-11-12，EXP-029 及其后的清理提交只在本地 main，没有推送）。
- 生成的数据（SPEC 检查点、Linux 镜像）放在 `~/personal/AI-Huma-data/`（如 `spec-rv32imab/`、`linux/`、`linux_rv64/`），构建产物都在各仓库被忽略的 `build*` 目录里，都不进仓库。

## 文档

**从 [docs/GUIDE.md](docs/GUIDE.md) 开始**：它列出全部文档、各管什么、遇到什么事该看哪份。最常用的几份：

- [docs/WORKFLOW.md](docs/WORKFLOW.md)：规则和流程（分支与提交、正确性标准、harness、实验流程、合入 main 的步骤、文档整理）。
- [docs/TODO.md](docs/TODO.md)：全项目唯一的待办清单。
- [docs/MAIN_RECORDS.md](docs/MAIN_RECORDS.md)：每次合入 main 的性能、面积和“变化”；**当前数字以这里为准**。
- [docs/EXPLORATION.md](docs/EXPLORATION.md)：架构探索记录；[docs/LOG.md](docs/LOG.md)：每个 commit 一行。
- [docs/PMU.md](docs/PMU.md)：性能监控单元与 TMA；[docs/SERVER.md](docs/SERVER.md)：云服务器怎么跑 SPEC。
- [trace-model/docs/ENV_VARS.md](trace-model/docs/ENV_VARS.md)：时序模型的全部环境变量（默认值、用途）。

## 核心原则

- **正确性 = 架构行为与 function-model 一致**（2026-11-04 起）。RTL 整核测试平台每提交一条指令，function-model 执行一条，比较提交 PC 和目的寄存器的值；Linux 从复位启动到登录提示符是整机检查。
- **周期数、IPC 是性能指标，也是优化的对象**。原模型的周期只是起点，不再是标准；探索的结论先在 trace-model 上验证，再同步到 RTL，合入 main 时两者周期逐个相等。
- **旧的逐模块锁步 / trace 回放 / 变异检查体系已退役**（代码在 rtl 标签 `legacy-reference`，文档在 `rtl/docs/history/`）。
- **目标是方法，而不只是代码**：AI 和人能否系统地做 CPU 架构优化——每个想法先在模型上量化，再落到 RTL，保证正确，留下可复用的验证手段和完整记录（包括负面结果）。

## 当前状态（2026-11-12）

README 只写概况，**各次合入的数字、配置变化和已知回退以 [docs/MAIN_RECORDS.md](docs/MAIN_RECORDS.md) 为准**，在做的事见 [docs/TODO.md](docs/TODO.md)。

- **当前配置**（默认开）：第 3 批面积配置（取指宽度 8、在飞分支 32）→ DRAMsim3 DDR4-3200 + 60 ns 非核心延迟、核心 1 GHz、无 AXI 分频 → mov 消除 → L1D 预取器 h1 → 分级 LSU + 流水化 BPU → IQ 入队宽度 INT7/LD6/STA4/STD4/BR5 → 访存推测（`LSU_MEMSPEC`）+ 前端快速通路（`FE_RFAST=15`）→ 已提交 store 的 write buffer（4 项 × 2 store）→ 3 张 × 64 项间接跳转目标表 → 紧凑 ROB（128 项，按序分配、前缀提交）+ 寄存器版 BPU 提交额度。
- **性能**：SPEC 估算分数（官方参考时间直接换算，580 个检查点、快速预热）11.53 分/GHz（EXP-028 合入时）；各次合入对上一次 main 的几何平均 IPC：EXP-027 +10.75%、EXP-028 +2.74%。**RTL 没有跑过 SPEC**；没有工艺库综合和时序（WNS），只有 yosys 通用门面积代理。
- **rv64（EXP-029，2026-11-12 合入本地 main）**：`XLEN_BITS=64` / `-DXLEN=64` 可选，rv64imab + Sv39；RTL 上 53 个 rv64 程序和 Linux 到 `rv64 login:` 逐条对比 0 不一致；默认 XLEN=32 周期不变。未做：F/D、C、SPEC rv64 检查点、`back_top.sv`/`exu.sv`/`soc_top.sv` 生成器同步（见 TODO）。
- **trace-model**：gate 64/64（`run_gate.sh`，周期等于 `results/baseline/baseline.csv`）；Linux 启动到登录；SPEC 回放（580 个 rv32imab 检查点）。
- **rtl**：lint 干净（按目录和整芯片，XLEN=32 和 64）；`fm_gate.sh` 69/69 逐条对比，周期与 trace-model（`LSU_PIPE_NOWD=1`）逐个相等；Linux 从复位一次连续启动到 `rv32 login:`（rv64 到 `rv64 login:`）逐条对比 0 不一致；store 数据不在逐条对比范围内。已知风险见 [rtl/docs/08-risk-register.md](rtl/docs/08-risk-register.md)。
- **未合入的实验**：sdip 预取器（EXP-026，`exp/sdip`）、LD/STA IQ 合并与统一 FTQ 的 RTL 试做（见 TODO）、其余探索见 [EXPLORATION.md](docs/EXPLORATION.md) 索引。

## 复现

细节见 `trace-model/docs/PROJECT.md` 和 `rtl/docs/README.md`。要点（默认 rv32）：

```bash
# trace-model 依赖同级的 function-model（trace-model/function-model 是指向 ../function-model 的符号链接）
gmake -C function-model librefcpu.a LDFLAGS="-lz"
cd trace-model
gmake LDFLAGS="-lz" -j8
bash scripts/run_gate.sh build/simulator results/gate      # 64 个程序，周期等于 results/baseline/baseline.csv（默认配置）

# rtl：lint，带 function-model 逐条对比的整核门禁（需要先构建 trace-model 的测试程序）
cd ../rtl
bash scripts/lint.sh && bash scripts/lint_chip.sh
SOC_FM=1 SOC_OUT=$PWD/build/soc_fm bash tb/soc/build.sh
bash scripts/fm_gate.sh $PWD/build/soc_fm/obj/soc_tb $PWD/build/gate   # 69/69，并报告与 trace-model 周期不同的个数
```

**rv64**（`XLEN=64`）：function-model 的 `.o` 在源码目录里，rv64 库要在单独的检出（如 `git worktree`）里 `gmake XLEN=64 librefcpu.a`，得到的 `librefcpu.a` 用路径传给其他两个仓库；trace-model 用 `gmake XLEN=64 REFCPU_LIB=<rv64 librefcpu.a> BUILD_DIR=build64 LDFLAGS="-lz"`；rtl 测试平台用 `SOC_XLEN=64 SOC_FM=1 FMLIB=<rv64 librefcpu.a> SOC_OUT=<绝对路径> bash tb/soc/build.sh`（整芯片 lint：`CFG=<XLEN_BITS=64 的配置包> bash scripts/lint_chip.sh`）。rv64 的 Linux 镜像在 `~/personal/AI-Huma-data/linux_rv64/`。详见 [rtl/scripts/README.md](rtl/scripts/README.md) 的 rv64 段和 [EXPLORATION.md](docs/EXPLORATION.md) EXP-029。

**比周期**：对 RTL 或 `ref_cycles.txt` 比周期时，模型要设 `LSU_PIPE_NOWD=1`（关掉 63 周期看门狗，RTL 没有它）。
