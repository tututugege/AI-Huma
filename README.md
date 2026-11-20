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
| trace-model 结构整理 | 2026-11-16 至 11-17 | 周期全程不变的四次整理：去掉执行驱动时代的残留（[TM_CLEANUP.md](docs/TM_CLEANUP.md)）；环境变量 77 → 16、开关和变体精简（[TM_SIMPLIFY.md](docs/TM_SIMPLIFY.md)）；comb 只在一拍内按依赖计算、seq 只在时钟沿锁存，后端 comb 阶段 69 → 23（[TM_REG_WIRE.md](docs/TM_REG_WIRE.md)）；模块契约：寄存器统一为 `Regs q_, d`，每个 comb 阶段在头文件声明读写的信号，后端、访存、前端和 `SimCpu::cycle()` 的调度都由声明生成、由工具核对（[TM_MODULE_CONTRACT.md](docs/TM_MODULE_CONTRACT.md)）；一张全局调度表、25 个模块同一种写法、大部分模块的下一状态在 seq 原地更新、uop 只带 id、每拍扫描改查表，dhrystone 模拟快约 20%（[TM_GLOBAL_SCHED.md](docs/TM_GLOBAL_SCHED.md)）。随后整理 TLB、CSR、Dispatch、Rename、ROB、LSU，删掉 PhysMemory（[TM_MODULE_CLEANUP.md](docs/TM_MODULE_CLEANUP.md)）。模型 .cpp/.h 约 3.0 万行。 |

## 三个部分

| 部分 | 目录 | 作用 |
|---|---|---|
| **function-model** | `function-model/` | 功能模型：只管指令执行的结果（寄存器、访存、CSR、分页），不管时序。基于 tututugege/GenSimpoint，库名 `librefcpu`；main 上为 rv64gc（`XLEN=64`、`FP=1`；`RVC=1` 构建带 C 扩展的版本）。也负责 SPEC 的 BBV/SimPoint/检查点生成。 |
| **trace-model** | `trace-model/` | 我们的时序模型和架构探索平台：起点由 tututugege/simulator 蒸馏而来，不计算数据值，分支方向/目标、地址、store 数据、CSR 写数据都来自功能模型提供的“事实”，只保留周期精确的时序行为。核参数的唯一来源（`include/config.h`）；运行时开关全部列在 [trace-model/docs/ENV_VARS.md](trace-model/docs/ENV_VARS.md)（16 个环境变量）。建模方式和代码风格见 trace-model 的 [README](trace-model/README.md)，一拍的调度（模块声明、自动生成、改了模块之后怎么做）见 [trace-model/docs/SCHEDULING.md](trace-model/docs/SCHEDULING.md)（`scripts/comb/comb_graph.py --check` 核对）。 |
| **rtl** | `rtl/` | 我们的 SystemVerilog 实现（283 个 RTL 文件、约 3.6 万行）：起点由原模型逐模块翻译，现在随优化独立迭代；整核测试平台（Verilator）逐条提交对比 function-model；参数包由 trace-model 的 `config.h` 生成。 |

三者的关系：function-model 定义“对不对”（架构行为），trace-model 定义“快不快”（周期）并用来做架构探索；rtl 的架构行为必须与 function-model 一致，合入 main 时同一配置下的周期必须与 trace-model（默认配置即 RTL 配置，无需额外环境变量）逐个程序相等。

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

- 子模块指针记录的是各子仓库 `main` 上已提交的 commit；分支和合入规则见 [docs/WORKFLOW.md](docs/WORKFLOW.md)。推送由用户决定。
- 生成的数据（SPEC 检查点、Linux 镜像与检查点库）不进仓库：当前开发机（`iprc-jump`）上的本地 Linux 镜像在 `~/rv64spec/linux_j.bin`，集群共享的 SPEC06 rv64gc（535 点 / 标准 386 点）与 Linux 26 段检查点库在 `eda` NFS `/nfs_global/S/houruyao/{spec06_rv64gc,linux_ckpt_rv64gc}`（详见 [docs/SERVER.md](docs/SERVER.md)）；构建产物都在各仓库被忽略的 `build*` 目录里。

## 文档

**从 [docs/GUIDE.md](docs/GUIDE.md) 开始**：它列出全部文档、各管什么、遇到什么事该看哪份。最常用的几份：

- [docs/WORKFLOW.md](docs/WORKFLOW.md)：规则和流程（分支与提交、正确性标准、harness、实验流程、合入 main 的步骤、文档整理）。
- [docs/TODO.md](docs/TODO.md)：全项目唯一的待办清单。
- [docs/MAIN_RECORDS.md](docs/MAIN_RECORDS.md)：每次合入 main 的性能、面积和“变化”；**当前数字以这里为准**。
- [docs/EXPLORATION.md](docs/EXPLORATION.md)：架构探索记录；[docs/LOG.md](docs/LOG.md)：每个 commit 一行。
- [docs/PMU.md](docs/PMU.md)：性能监控单元与 TMA；[docs/SERVER.md](docs/SERVER.md)：`iprc-jump` 与 `eda` 集群怎么编译、跑 SPEC。
- [trace-model/docs/ENV_VARS.md](trace-model/docs/ENV_VARS.md)：时序模型的全部环境变量（默认值、用途）；[trace-model/docs/SCHEDULING.md](trace-model/docs/SCHEDULING.md)：模块写法、接口声明、调度生成和工具看不见的共享状态（[MODULE_CONTRACT.md](trace-model/docs/MODULE_CONTRACT.md) 是过程记录）。

## 核心原则

- **正确性 = 架构行为与 function-model 一致**（2026-11-04 起）。RTL 整核测试平台每提交一条指令，function-model 执行一条，比较提交 PC 和目的寄存器的值；Linux 从复位启动到登录提示符是整机检查。
- **周期数、IPC 是性能指标，也是优化的对象**。原模型的周期只是起点，不再是标准；探索的结论先在 trace-model 上验证，再同步到 RTL，合入 main 时两者周期逐个相等。
- **旧的逐模块锁步 / trace 回放 / 变异检查体系已退役**（代码在 rtl 标签 `legacy-reference`，文档在 `rtl/docs/history/`）。
- **目标是方法，而不只是代码**：AI 和人能否系统地做 CPU 架构优化——每个想法先在模型上量化，再落到 RTL，保证正确，留下可复用的验证手段和完整记录（包括负面结果）。

## 当前状态（2026-11-21）

README 只写概况，**各次合入的数字、配置变化和已知回退以 [docs/MAIN_RECORDS.md](docs/MAIN_RECORDS.md) 与 [docs/EXPLORATION.md](docs/EXPLORATION.md) 为准**，在做的事见 [docs/TODO.md](docs/TODO.md)。

- **当前配置**（默认开，trace-model 默认配置 = RTL 配置）：第 3 批面积配置（取指宽度 8、在飞分支 32）→ DRAMsim3 DDR4-3200 + 60 ns 非核心延迟、核心 1 GHz、无 AXI 分频 → mov 消除 → 分级 LSU → 两个 INT 发射队列（各 32 项、每个 4 条入队）+ 合并的访存队列（load + STA，入队 6）+ 5 个 AGU（共 6 个发射队列）→ 访存推测（`LSU_MEMSPEC`）+ 前端快速通路（`FE_RFAST=15`）→ 已提交 store 的 write buffer（4 项 × 2 store）→ 紧凑 ROB（128 项，按序分配、前缀提交）+ 寄存器版 BPU 提交额度 → 全局 flush 晚一拍（`FLUSH_REG`）、取指地址 FIFO 晚一拍读、STA/STD 事件和写缓冲合并寄存（EXP-044）→ LLC / L1I SRRIP 替换（EXP-045）+ 发射前查完成周期与写回口压缩（EXP-046）→ L1 硬件 Berti（`PF_KIND=4` + DTLB 跨页翻译）+ LLC Best-Offset 预取（`LLC_BOP=1`）+ L1D/LLC MSHR 16/16（EXP-048）→ **块级 1-Ahead FTB + S2 Block-TAGE/ITT 分支预测器**（EXP-050 里程碑 A：`ah1_4k_a2k1k` + 1-branch/cycle `brq[16]`，取代旧 16-bank 逐指令槽 BPU）。
- **ISA**：main 只有 rv64gc（rv64imafdc + Sv39，默认 `XLEN=64`、`FP=1`、`RVC=1`），rv32 在各仓库分支 `rv32-legacy`。
- **性能**：rv64gc SPEC06 INT 全量 386 点（约 95% 权重，`eda` 集群 `/nfs_global/S/houruyao/spec06_rv64gc`）：EXP-048 估算 `12.11 分/GHz`；EXP-050 块级 1-Ahead FTB 相对 EXP-048 几何平均 IPC 再增 **+8.48%**（12/12 全正，`FE.bw 31.23% → 22.85%`），估算达 **13.14 分/GHz**（详见 [docs/EXPLORATION.md](docs/EXPLORATION.md) EXP-050）。**RTL 没有跑过 SPEC**；Yosys 深度代理（[rtl/docs/09-synthesis-report.md](rtl/docs/09-synthesis-report.md) 第 12/13 节）：`bpu` 单元数 `549,458 → 274,811`（**−50.0%**）、深度 `134 → 131` 层，`front_top` `898,333` 单元 / `153` 层；工艺库时序综合（Synopsys DC）待接。
- **C 扩展与 rv64gc 的 RTL**：`RVC=1`（C910 式携带）和 rv64gc 的 RTL 与 trace-model 逐周期对齐，含 Linux。EXP-050 已完成 26 段 rv64gc Linux 检查点窗口（`s01..s26`，每段 400 万周期，合计 1.04 亿周期、132,473,668 条指令）全量 RTL vs trace-model **26/26 PASS、0 FM 不一致、PT（103,974 bins）与 UP（103,144 bins）指纹 0 差异**；快速检查用 `rtl/scripts/linux_segments_cmp.sh`，从复位的完整 Linux gate 是最后确认（[docs/WORKFLOW.md](docs/WORKFLOW.md) 第 3.2 节）。
- **trace-model**：默认 `RVC=1` 门禁（`run_gate.sh` 62/62、`run_gate_c.sh` 68/68），周期等于基线；`comb_graph.py --check` 0 隐患、模块声明与代码一致；rv64gc Linux 启动到 `rv64 login:` PASS。
- **rtl**：lint 干净（按目录和整芯片）；`fm_gate.sh` 67/67 逐条对比，周期与默认配置 trace-model 逐个相等；store 数据不在逐条对比范围内。已知风险见 [rtl/docs/08-risk-register.md](rtl/docs/08-risk-register.md)。
- **未合入的实验**：sdip 预取器（EXP-026，`exp/sdip`）、BC_CORE 预取（EXP-043，`exp/pf-l1l2`）、统一 FTQ 的 RTL 试做（见 TODO）、其余探索见 [docs/EXPLORATION.md](docs/EXPLORATION.md) 索引。

## 复现

细节见 `trace-model/docs/PROJECT.md`、`rtl/docs/README.md` 与 [docs/SERVER.md](docs/SERVER.md)。要点（当前开发机 `iprc-jump`，Ubuntu / rv64gc 默认 `XLEN=64 FP=1 RVC=1`）：

```bash
# trace-model：Makefile 会自动按固定版本 FM_REV 从 ../function-model 构建匹配的 librefcpu.a
cd trace-model
make -j8
bash scripts/run_gate.sh build/simulator results/gate      # 62 个基础程序，周期等于 results/baseline/baseline.csv
bash scripts/run_gate_c.sh build/simulator results/gate_c  # 68 个 C 扩展程序，周期等于 results/baseline/baseline_c.csv
python3 scripts/comb/comb_graph.py --check                 # comb 调度与模块声明一致（改了模块后先跑 gen_*_order.py --write）

# rtl：在 iprc-jump 上必须先切到 Verilator 5.052（系统 /usr/bin/verilator 5.020 编不过）
export PATH="$HOME/rv64spec/verilator_src/bin:$PATH"
cd ../rtl
bash scripts/lint.sh && bash scripts/lint_chip.sh
SOC_FM=1 SOC_OUT=$PWD/build/soc_fm bash tb/soc/build.sh    # 自动经 scripts/fm_lib.sh 构建匹配的 librefcpu.a
bash scripts/fm_gate.sh $PWD/build/soc_fm/obj/soc_tb $PWD/build/gate   # 67/67，并报告与 trace-model 周期不同的个数
```

- **默认配置即 RTL 配置（不靠环境变量对齐）**：2026-11-19 起已删除 `LSU_PIPE_NOWD` 看门狗开关，trace-model 与 RTL 默认均为 `XLEN=64 FP=1 RVC=1`，比周期和跑 SPEC 均不需要额外环境变量；PMU 默认开（`PMU=0` 关闭）。
- **Linux 镜像与大规模集群任务**：本机 Linux 镜像在 `~/rv64spec/linux_j.bin`；SPEC06、全量 27 窗 Linux 对齐和 Yosys/DC 综合统一上 `eda` 集群，见 [docs/SERVER.md](docs/SERVER.md)。
