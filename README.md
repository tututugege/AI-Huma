# AI-Huma

AI-Huma 是一个乱序 RISC-V CPU 的设计项目：人定方向和验收标准，AI 做大部分设计、验证和实现工作。

我们从一个开源模拟器（tututugege/simulator）出发建立起点，随后完成了向 `rv64gc` + `Sv39` 的全面演进与 60 余项体系结构探索。经过前端块级预测与双块融合、后端扩窗与稀疏检查点重构、L2 TLB / Berti / BOP / Bingo 访存层次升级、Load L2 推测唤醒、Radix-4 Booth 乘法 / Radix-16 Early-out 除法以及**全套自研可综合 RV64FD FPU** 的全栈落地，项目在 SPEC06 INT 386 点上已突破 **`15.33 分/GHz`**，且 `function-model` / `trace-model` / `rtl` 三仓逐程序周期 100% 对齐。

当前项目已进入**物理实现与时序收敛新阶段**：在保持 15+ 分/GHz 架构竞争力的同时，集中推进剩余超 100 层模块的逻辑深度压缩与 Synopsys DC 工艺库时序/面积/功耗综合，持续探索人机协同的 Agentic CPU 设计范式。

## 名字的由来

AI-Huma 有两层意思：

1. **AI + Human**：项目由人定方向、定验收标准，AI 做大部分设计、验证和实现工作。
2. **Al-Huma(**アル・ヒューマ**)**：致敬作者最喜欢的动漫角色雷姆（Re:Zero）的魔法。

## 发展阶段

| 阶段 | 时间 | 做了什么 |
|---|---|---|
| 建立起点 | 至 2026-11-04 | 从 tututugege/simulator 蒸馏出 trace-model（代码从约 8.4 万行降到 4.3 万行、更快，周期与原模型完全一致）；逐模块翻译出 RTL，与原模型逐拍对照；接入 function-model。逐拍对照体系完成使命后退役（rtl 标签 `legacy-reference`）。 |
| 自主优化 | 2026-11-04 至 11-11 | 正确性改为对照 function-model，建立“探索 → 验证 → 合入 main”流程（[WORKFLOW.md](docs/WORKFLOW.md)）；落地 DRAMsim3 DDR4 模型、L1D 预取器、PMU、分级 LSU、访存推测、write buffer、多表 ITT、紧凑 ROB 等基础优化（EXP-005..028）。 |
| rv64gc 迁移与模型重构 | 2026-11-11 至 11-17 | 从 rv32imab 全面迁移至 `rv64gc` + `Sv39`（含 F/D、C 扩展；rv32 归档于各仓 `rv32-legacy` 分支）；随后完成 trace-model 四轮零周期差结构重构（统一 `In/Out` + `CONTRACT` 声明与自动调度生成 `comb_graph.py`、精简环境变量、提速 ~20%，详见 [trace-model/docs/SCHEDULING.md](trace-model/docs/SCHEDULING.md)）。 |
| 体系结构冲刺与 15+ 分里程碑 | 2026-11-18 至 11-23 | **从 11.37 分/GHz 演进至 `15.33 分/GHz`（+34.8%，SPEC06 INT 386/386 点），三仓全量对齐**：① 默认配置 = RTL 配置，删看门狗与旧开关，建立模块级文档先行与 Yosys 深度代理综合基线（EXP-044..046）；② 访存与前端大升级：L1 硬件 Berti + LLC BOP/Bingo 双优先级空间预取（EXP-048/058）、块级 1-Ahead FTB + `2-taken` + 2-Ahead B + 真 4-Bank ICache + 实 AXI FDIP 与前端重构（EXP-050/051/053）、统一 L2 TLB + Sv39 PWC（EXP-056）；③ 后端性能与面积协同：`c.mv` 1-hop 移动消除（EXP-052）、`PRF=256 / ROB=256` 扩窗（EXP-055）、唤醒驱动 6b EXU Bypass 与 `isu`/`ren` 公共原语平衡树降深度、`ren` 稀疏 K=4 检查点 + `ren_log` 前向 Walk（`ren` 面积 −73.2%，EXP-059）、**Load L2 推测唤醒（`load-to-use 4→3`）突破 15 分大关（`15.25 /GHz`，EXP-060）**；④ 执行单元物理化与自研可综合 FPU：Radix-4 Booth 乘法 + 1× Radix-16 Early-out 变延迟除法与 EXU 动态唤醒 + **全套自研可综合 RV64FD FPU（5 核心 `<100` 层，235 万条 SoftFloat 0 差，`-DFPU_REAL` 整核 69/69）**（`15.33 /GHz`，EXP-061）。下一阶段重点：剩余超 100 层模块降深度与 Synopsys DC 工艺库时序综合（见 [TODO.md](docs/TODO.md)）。 |

## 三个部分

| 部分 | 目录 | 作用 |
|---|---|---|
| **function-model** | `function-model/` | 功能模型：只管指令执行的结果（寄存器、访存、CSR、分页），不管时序。基于 tututugege/GenSimpoint，库名 `librefcpu`；main 上为 rv64gc（`XLEN=64`、`FP=1`；`RVC=1` 构建带 C 扩展的版本）。也负责 SPEC 的 BBV/SimPoint/检查点生成。 |
| **trace-model** | `trace-model/` | 我们的时序模型和架构探索平台：起点由 tututugege/simulator 蒸馏而来，不计算数据值，分支方向/目标、地址、store 数据、CSR 写数据都来自功能模型提供的“事实”，只保留周期精确的时序行为。核参数的唯一来源（`include/config.h`）；运行时开关全部列在 [trace-model/docs/ENV_VARS.md](trace-model/docs/ENV_VARS.md)（13 个环境变量）。建模方式和代码风格见 trace-model 的 [README](trace-model/README.md)，一拍的调度（模块声明、自动生成、改了模块之后怎么做）见 [trace-model/docs/SCHEDULING.md](trace-model/docs/SCHEDULING.md)（`scripts/comb/comb_graph.py --check` 核对）。 |
| **rtl** | `rtl/` | 我们的 SystemVerilog 实现（286 个 RTL 文件、约 3.86 万行）：起点由原模型逐模块翻译，现在随优化独立迭代；整核测试平台（Verilator）逐条提交对比 function-model；参数包由 trace-model 的 `config.h` 生成。 |

三者的关系：function-model 定义“对不对”（架构行为），trace-model 定义“快不快”（周期）并用来做架构探索；rtl 的架构行为必须与 function-model 一致，合入 main 时同一配置下的周期必须与 trace-model（默认配置即 RTL 配置，无需额外环境变量）逐个程序相等。

## 仓库结构

`AI-Huma` 本身是**总仓库**，只放全项目文档（`docs/`）和忽略规则；三个子项目是各自独立的 git 仓库，作为 **git 子模块**引用（`.gitmodules` 指向 `git@github.com:tututugege/AI-Huma-{func,trace,rtl}.git`）。

```text
AI-Huma/
├── README.md, docs/          总仓库文档（导航见 docs/GUIDE.md）
├── function-model/           子模块：功能模型（librefcpu）
├── trace-model/              子模块：时序模型 / 架构探索平台
├── rtl/                      子模块：SystemVerilog + 整核测试平台
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
- [trace-model/docs/ENV_VARS.md](trace-model/docs/ENV_VARS.md)：时序模型的全部环境变量（默认值、用途）；[trace-model/docs/SCHEDULING.md](trace-model/docs/SCHEDULING.md)：模块写法、接口声明、调度生成和工具看不见的共享状态。

## 核心原则

- **正确性 = 架构行为与 function-model 一致**（2026-11-04 起）。RTL 整核测试平台每提交一条指令，function-model 执行一条，比较提交 PC 和目的寄存器的值；Linux 从复位启动到登录提示符是整机检查。
- **周期数、IPC 是性能指标，也是优化的对象**。原模型的周期只是起点，不再是标准；探索的结论先在 trace-model 上验证，再同步到 RTL，合入 main 时两者周期逐个相等。
- **旧的逐模块锁步 / trace 回放 / 变异检查体系已退役**（归档在 rtl 标签 `legacy-reference`）。
- **目标是方法，而不只是代码**：AI 和人能否系统地做 CPU 架构优化——每个想法先在模型上量化，再落到 RTL，保证正确，留下可复用的验证手段和完整记录（包括负面结果）。

## 🏆 里程碑：SPEC06 INT 突破 **15 分/GHz**（当前 `main`：**`15.33 分/GHz`**，2026-11-23）

> 在 `rv64gc` + `Sv39` + 真实 DRAMsim3 DDR4-3200（1 GHz、60 ns 非核心延迟、无 AXI 分频）口径下，全量 SPEC06 INT **386/386 SimPoint（~95% 权重，0 失败）** 已从 `11.37 分/GHz` 演进至 **`15.33 分/GHz`（+34.8%）**，且三仓（`function-model` / `trace-model` / `rtl`）逐程序周期 100% 对齐，包含可综合 RV64FD FPU 与全量 26 窗 Linux（~1.33 亿指令）逐条对拍 0 差异！

### 性能演进路线（SPEC06 INT 386 点，分/GHz）

| 阶段 / 编号 | 核心微架构特性 | SPEC06 INT | 相对上一版 |
|---|---|---:|---:|
| 基线（EXP-046） | 宽发射乱序核 + 紧凑 ROB 128 + 访存推测 + 写缓冲 + LLC/L1I SRRIP | `11.37 /GHz` | — |
| **EXP-048** | L1 硬件 Berti 预取 + LLC Best-Offset (BOP) + L1D/LLC MSHR 16/16 | `12.11 /GHz` | +6.58% |
| **EXP-050** | 块级 1-Ahead FTB + S2 Block-TAGE / Block-ITT 分支预测器（BPU 面积 −50%） | `13.14 /GHz` | +8.48% |
| **EXP-051 / 053** | 前端 `2-taken` 双块融合 + 2-Ahead B + 真 4-Bank 1R1W ICache + 2 读口 ITLB + 实 AXI FDIP + 前端去补丁清理（`front_top` 面积 −26.8% / 深度 −39.3%） | `13.48 /GHz` | +2.60% |
| **EXP-052** | RV64GC 16-bit `c.mv` 规范化 + 组内 1-hop 关键链移动消除 | `13.49 /GHz` | +0.55% |
| **EXP-055** | 后端指令窗口扩展 `PRF=256 / ROB=256` + `ren` 公共原语降深度（`91` 层） | `14.24 /GHz` | +5.64% |
| **EXP-056** | 统一 L2 TLB（1024 项 4 路 1RW SRAM + 8 项大页 CAM）+ 16 项 Sv39 PWC（`ptw_walk` 仅 5.4k cells / 44 层） | `14.69 /GHz` | +3.17% |
| **EXP-058** | 硬件忠实版 LLC Bingo 4KB 空间预取器（1RW SRAM `~26.75 KiB`，与 BOP 双优先级协同，48 层） | `14.88 /GHz` | +1.26% |
| **EXP-059** | `ren` 稀疏 K=4 单写口检查点 + 本地 256×25b `ren_log` 8 宽前向 Walk + 8-bank `free_list`（`ren` 面积 **−73.22%**，省 44.6 万单元） | `14.85 /GHz` | −0.18% |
| **EXP-060** | **突破 15 分！** Load L2 推测唤醒（`load-to-use 4→3` 拍）+ STLF `data_v` 纳入 L2 唤醒 + WBP 同拍唤醒（`5→4` 拍）+ 4 路直接比较 cancel + 整数 `lsu_byp` | **`15.25 /GHz`** | **+2.64%** |
| **EXP-061** | **当前 `main`**：Radix-4 Booth 乘法（面积 −31.4%）+ 1× Radix-16 双 Radix-4 Early-out 变延迟除法（2..17 拍，EXU 动态唤醒）+ **全套自研可综合 RV64FD FPU**（5 核心全 `<100` 层） | **`15.33 /GHz`** | **+0.53%** |

## 当前状态（2026-11-23）

README 只写概况，**各次合入的数字、配置变化和已知回退以 [docs/MAIN_RECORDS.md](docs/MAIN_RECORDS.md) 与 [docs/EXPLORATION.md](docs/EXPLORATION.md) 为准**，在做的事见 [docs/TODO.md](docs/TODO.md)。

- **当前微架构配置**（`trace-model` 默认配置 = `rtl` 配置，零环境变量）：
  - **ISA**：`rv64gc`（`rv64imafdc` + `Sv39`，默认 `XLEN=64`、`FP=1`、`RVC=1`；`rv32` 归档在各仓 `rv32-legacy` 分支）。
  - **前端**：块级 1-Ahead FTB + S2 Block-TAGE/ITT + `2-taken` 双块融合 + 2-Ahead B + 真 4-Bank 1R1W ICache + 2 读口 ITLB + 实 AXI S2 确认 2-slot FDIP，8 宽译码。
  - **重命名与后端窗口**：`PRF=256`（INT）+ `FPRF=96`（FP）、紧凑 `ROB=256`、`MAX_BR=32`；稀疏 `K=4` 单写口检查点 + 本地 256×25b `ren_log` 8 宽前向 Walk + 8-bank 1R1W `free_list` + `c.mv` 组内 1-hop 移动消除。
  - **发射与执行**：6 发射队列（双 32 项 INT + 合并 MEM + STD + BR + FP）、5 物理 AGU、唤醒驱动 6 位二维 EXU Bypass；6 ALU + 2 BRU + 2 Radix-4 Booth 3 拍流水 MUL + **1× Radix-16 双 Radix-4 Early-out 变延迟 DIV（2..17 拍，EXU 完成前 1 拍动态唤醒）** + **全套自研可综合 RV64FD FPU**（2 FMA 3 拍流水 + 3 FMISC/FCVT + 2 I2F + 1 迭代 FDIV/FSQRT，默认仿真走快速 DPI、`SYNTHESIS`/`-DFPU_REAL` 走真可综合 RTL）。
  - **访存与缓存体系**：分级 LSU + 访存推测（`LSU_MEMSPEC`）+ **Load L2 推测唤醒（`load-to-use=3` 拍）& STLF/WBP 同拍唤醒** + 已提交 store write buffer + L1 硬件 Berti 预取 + 4 MiB 16 路 SRRIP LLC（BOP + Bingo 4KB 双优先级空间预取）+ L1D/LLC MSHR 16/16 + **统一 L2 TLB（1024×4 1RW SRAM + 8 项大页 CAM）+ 16 项 Sv39 PWC** + DRAMsim3 DDR4-3200。
- **综合与面积（Yosys 通用门代理，`SYNTH_ABC="strash;balance;map"`）**：`ren` `157k` / `91` 层、`rob` `881k` / `65` 层、`prf` `640k` / `25` 层、`isu` `1,071k` / `60` 层、`dispatch` `212k` / `57` 层、`lsu` `1,240k` / `101` 层、`ptw_walk` `5.4k` / `44` 层、`axi_llc_bingo` `41k` / `48` 层、`exu`（含全套真可综合 FPU + 优化乘除法）`305k` / `98` 层；工艺库时序综合（Synopsys DC）待统一接入。
- **验证状态**：
  - `trace-model`：`comb_graph.py --check` 0 隐患；`run_gate.sh` 62/62、`PF_ENABLE=0` 62/62、`run_gate_c.sh` 68/68；rv64gc Linux 从复位启动到 `rv64 login:` PASS（0 oops/panic）。
  - `rtl`：`lint_chip.sh` 0 告警；`mul_check` 400 万 / `div_check` 10.3 万 / `fp_synth_check` 235 万全 0 不一致；`-DFPU_REAL` 整核 `fm_gate.sh` **69/69 PASS（0 FM 差、0 周期差）**；`eda` 集群 26 窗 rv64gc Linux 检查点（~1.33 亿指令）0 FM 不一致。
- **未合入的探索**：sdip 预取器（EXP-026）、BC_CORE 预取（EXP-043）、1MB L2 + 16MB L3 层级探索（EXP-057，`+4.11%`）、其余探索见 [docs/EXPLORATION.md](docs/EXPLORATION.md) 索引。

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
bash scripts/fm_gate.sh $PWD/build/soc_fm/obj/soc_tb $PWD/build/gate   # 69/69，并报告与 trace-model 周期不同的个数
```

- **默认配置即 RTL 配置（不靠环境变量对齐）**：2026-11-19 起已删除 `LSU_PIPE_NOWD` 看门狗开关，trace-model 与 RTL 默认均为 `XLEN=64 FP=1 RVC=1`，比周期和跑 SPEC 均不需要额外环境变量；PMU 默认开（`PMU=0` 关闭）。
- **Linux 镜像与大规模集群任务**：本机 Linux 镜像在 `~/rv64spec/linux_j.bin`；SPEC06、全量 27 窗 Linux 对齐和 Yosys/DC 综合统一上 `eda` 集群，见 [docs/SERVER.md](docs/SERVER.md)。
