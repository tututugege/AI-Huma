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
| 自主优化 | 2026-11-04 起 | 正确性改为对照 function-model，周期不再要求与原模型一致；建立探索 → 验证 → 合入 main 的流程（[WORKFLOW.md](docs/WORKFLOW.md) 第 4–6 节）；重建 SPEC 检查点。已合入 main 的优化：第 3 批面积配置（EXP-005）、DRAMsim3 DDR 内存模型并去掉 AXI 分频（EXP-006，新基线）、mov 消除（EXP-012）、**L1D 数据预取器 h1（EXP-009，SPEC 估算 8.12 → 约 8.80 分/GHz）**。以及 EXP-015/017/019/020/023/024/025（分级 LSU + 流水化 BPU、IQ 入队宽度、访存推测、前端快速通路、已提交 store 的 write buffer、多表间接跳转预测 ITT，见 MAIN_RECORDS）。待做：LD/STA 发射队列合并、统一 FTQ 的 RTL 试做结果入档，香山式独立 SBuffer、RTL 上的 SPEC 等（[TODO.md](docs/TODO.md)）。 |

## 三个部分

| 部分 | 目录 | 作用 |
|---|---|---|
| **function-model** | `function-model/` | 功能模型：只管指令执行的结果（寄存器、访存、CSR、分页），不管时序。基于 tututugege/GenSimpoint，库名 `librefcpu`。也负责 SPEC 的 BBV/SimPoint/检查点生成。 |
| **trace-model** | `trace-model/` | 我们的时序模型和架构探索平台：起点由 tututugege/simulator 蒸馏而来，不计算数据值，分支方向/目标、地址、store 数据、CSR 写数据都来自功能模型提供的“事实”，只保留周期精确的时序行为。核参数的唯一来源（`include/config.h`）。 |
| **rtl** | `rtl/` | 我们的 SystemVerilog 实现（约 350 个 RTL 文件、3.7 万行）：起点由原模型逐模块翻译，现在随优化独立迭代；整核测试平台（Verilator）逐条提交对比 function-model；参数包由 trace-model 的 `config.h` 生成。 |

三者的关系：function-model 定义“对不对”（架构行为），trace-model 定义“快不快”（周期）并用来做架构探索；rtl 的架构行为必须与 function-model 一致，合入 main 时同一配置下的周期必须与 trace-model 逐个程序相等。

## 仓库结构

`AI-Huma` 本身是**总仓库**，只放全项目文档和忽略规则；三个子项目是各自独立的 git 仓库，作为 **git 子模块**引用（子模块 URL 现在是本地相对路径，发布时再改成真实地址）。

```bash
git clone <AI-Huma 地址>
cd AI-Huma
git submodule update --init          # 取出 function-model、trace-model、rtl
```

- 子模块指针记录的是各子仓库 `main` 上已提交的 commit；分支和合入规则见 [docs/WORKFLOW.md](docs/WORKFLOW.md)。
- 生成的数据（SPEC 检查点、Linux 镜像）放在 `~/personal/AI-Huma-data/`，构建产物都在各仓库被忽略的 `build*` 目录里，都不进仓库。

## 文档

**从 [docs/GUIDE.md](docs/GUIDE.md) 开始**：它列出全部文档、各管什么、遇到什么事该看哪份。最常用的几份：

- [docs/WORKFLOW.md](docs/WORKFLOW.md)：规则和流程（分支与提交、正确性标准、harness、实验流程、合入 main 的步骤）。
- [docs/TODO.md](docs/TODO.md)：全项目唯一的待办清单。
- [docs/MAIN_RECORDS.md](docs/MAIN_RECORDS.md)：每次合入 main 的性能、面积和“变化”；**当前数字以这里为准**。
- [docs/EXPLORATION.md](docs/EXPLORATION.md)：架构探索记录；[docs/LOG.md](docs/LOG.md)：每个 commit 一行。

## 核心原则

- **正确性 = 架构行为与 function-model 一致**（2026-11-04 起）。RTL 整核测试平台每提交一条指令，function-model 执行一条，比较提交 PC 和目的寄存器的值；Linux 从复位启动到登录提示符是整机检查。
- **周期数、IPC 是性能指标，也是优化的对象**。原模型的周期只是起点，不再是标准；探索的结论先在 trace-model 上验证，再同步到 RTL，合入 main 时两者周期逐个相等。
- **旧的逐模块锁步 / trace 回放 / 变异检查体系已退役**（代码在 rtl 标签 `legacy-reference`，文档在 `rtl/docs/history/`）。
- **目标是方法，而不只是代码**：AI 和人能否系统地做 CPU 架构优化——每个想法先在模型上量化，再落到 RTL，保证正确，留下可复用的验证手段和完整记录（包括负面结果）。

## 当前状态（2026-11-10）

- **配置与基线**：第 3 批面积配置（取指宽度 8、在飞分支 32、IQ 384→240）→ DRAMsim3 DDR4-3200 + 60 ns 非核心延迟、核心 1 GHz、去掉 AXI 子系统分频（EXP-006，周期基线重做）→ mov 消除（EXP-012）→ **L1D 数据预取器 h1（EXP-009，默认开）**：单条全局步长表项、度 8、距离 2、页内、LLC-only next-line 引擎、无 PC，约 1,460 个触发器 → 分级 LSU + 流水化 BPU（EXP-015）→ issue queue 入队宽度（EXP-017）→ 访存推测与前端快速通路（EXP-019/020/023）→ 已提交 store 的 write buffer（EXP-024，4 项、每项最多 2 个同 line 的 store、排空口 2）→ **间接跳转目标表 1 张 256 项改为 3 张 × 64 项（EXP-025，ITT 存储 86 Kb → 64.5 Kb）**。
- **rv64（EXP-029，2026-11-12 合入本地 main）**：`XLEN_BITS=64` 可选配置，三个层次都支持 rv64imab + Sv39（F/D、C、SPEC 重新生成未做）；RTL 上 53 个 rv64 程序和 Linux 到 `rv64 login:` 逐条对比 0 不一致；默认 XLEN=32 周期不变。
- **性能（最近一次合入 EXP-028，2026-11-11）**：紧凑 ROB（按序分配、前缀提交，ROB 仍 128 项）+ 寄存器版 BPU 提交额度，默认开；SPEC 全量 580 点（快速预热、本机、`PMU=1`）对合入前 main 几何平均 IPC **+2.74%**，12 个程序全部提升，分数（官方参考时间直接换算）**11.23 → 11.53 分/GHz**；已知回退：分支密集短循环被 BPU 更新带宽卡住（gcc 4 个短点约 −37%、dhrystone 周期 +1.8%）。RTL Linux 从复位一次连续跑到登录，逐条对比 0 不一致；RTL 没跑 SPEC。
- **性能（EXP-025，SPEC 全量 580 点、快速预热、服务器、对 main）**：几何平均 IPC **+0.67%**（sjeng +3.77%、perlbench +3.16%、h264ref +0.53%、gcc +0.38%，其余基本不变，3 个点低于 −2%、未查）；RTL 没跑 SPEC。
- **性能（前两次合入，SPEC 全量 580 点、快速预热、对上一次合入的 main）**：EXP-019/020/023 几何平均 IPC **+11.02%**（trace-model，服务器）；EXP-024 **+0.68%**（本机，gcc +4.8%、hmmer +1.5%、gobmk +1.1%，其余基本不变，最差点 −6.25%）；估算分数：2026-11-11 用官方参考时间直接换算（EXP-027，`AI-Huma-data/mmio/score.py`），main + write buffer 10.06、当前 main（+ 多表 ITT）10.13 分/GHz；此前连乘得到的约 10.53 偏高。**EXP-027（2026-11-11 合入）**：删除 0x87f00000 非缓存窗口（Linux 把用户页分在这里，普通 load 走 MMIO），SPEC 全量几何平均 IPC +10.75%（h264ref +137%、hmmer +35%、perlbench +6.3%），分数约 11.2 分/GHz（当前 main 的全量待在服务器补跑）。RTL 没有跑过 SPEC。
- **性能（EXP-009 的 SPEC full，对精确的预取关基线，历史）**：12 个程序几何平均 IPC 加速 **+8.3%**（580 个点），估算分数 8.12 → 约 8.80 分/GHz（libquantum +96%、mcf +11%、gcc +9%、bzip2 +6%；gobmk/hmmer/sjeng −1% 到 −3%）。已知回退：5 个 SPEC 点低于 −10%（最差 omnetpp −41%），原因是 LLC-only 引擎；三个修复方案（节流、MSHR 预留、时间片对抗）在全量上都不如原样 h1，见 [EXPLORATION.md](docs/EXPLORATION.md) EXP-009 第 11 节。
- **EXP-019 / EXP-020 / EXP-023（2026-11-09 合入本地 main，未推送）**：LSU 访存相关推测（`LSU_MEMSPEC` 默认开：load 越过地址未知的更老 store，PC 哈希等待表 64 × 1 位、每 2000 周期清零，违例重做并在提交时冲刷；模型的值路径 `LSU_MS_DATA` 使模型周期等于 RTL）+ 前端重定向快速通路（`FE_RFAST=15` 写死，`FE_BFAST` 默认关）。**trace-model 的 SPEC 全量 580 点（快速预热，`PMU=1`，对同一服务器上构建的 main）12 个程序几何平均 IPC +11.02%**，估算分数 9.42 → 约 10.46 分/GHz（参考时间未核对官方表，9.42 是 EXP-015 的记录、EXP-016/017 在其后合入，起点是近似值）；最差点 −4.3%。**RTL 没有跑 SPEC**，模型与 RTL 在 68 个程序上周期逐个相等、Linux 13 段 13/13；`front_pred_path` 深度 +6%（超过 5% 判据）、`FE_RFAST` 的 BPU 面积 +19%（和合并综合表不一致，见 MAIN_RECORDS）；`FE_PAIR`、`FE_IPF` 只在模型里（默认关），旧的模型组合 +20.16% 不是 RTL 能得到的数字。
- **EXP-024（2026-11-09 合入本地 main，未推送）**：已提交 store 的 write buffer（`CFG_LSU_PIPE_WBUF=4` 默认开）：4 个条目、每条目最多 2 个同 cache line 的 store，STQ 内分组，一个条目一个 DCache 请求，排空口 3 → 2。**trace-model SPEC 全量 580 点（快速预热，本机）12 个程序几何平均 IPC +0.68%**（gcc +4.8%、hmmer +1.5%、gobmk +1.1%，其余基本不变，最差点 −6.25%）；RTL 没跑 SPEC；RTL 68 个程序逐条对比 68/68、周期与模型逐个相等、Linux 13/13；`lsu` 深度 125（main 130），`lp_drain` 模块级深度 +17%（超过判据，整体达标，作为例外记录）。香山式独立 SBuffer（提交即释放 STQ 项、字节掩码、按阈值排空）记在 TODO。
- **EXP-017（2026-11-08 合入）**：issue queue 入队宽度 INT7/LD6/STA4/STD4/BR5（原来全 8，写口 40→26）；SPEC 全量 −0.05%，`isu` 综合单元 −18.8%。
- **EXP-015（2026-11-08 合入）**：分级 LSU + 流水化 S+R BPU；30 点精确预热 IPC +2.87%，全量 580 点快速预热 −1.20%（已知回退，见 MAIN_RECORDS）。
- **trace-model**：gate 64/64（`run_gate.sh`，含 `itt-dispatch`；，预取、访存推测、`FE_RFAST`、write buffer 默认开，基线 2026-11-09 重生成）；`LSU_PIPE_WBUF=0 LSU_PIPE_DRAIN=3` 对 EXP-024 之前的 main 基线 63/63 逐个相同（`LSU_MEMSPEC=0 FE_RFAST=0` 对更早的 main 基线也相同）；Linux 启动到登录；full SPEC 回放（580 个 rv32imab 检查点）。
- **rtl**：lint 干净（按目录和整芯片）；69 个程序（68 + 定向测试）逐条对比全部通过，周期与 trace-model 逐个相等（write buffer 默认开）；Linux 分 13 段（检查点接力）逐条对比 13/13、0 不一致；EXP-025 的树上从复位连续启动到 `rv32 login:` 也通过（0 不一致）；有面积代理综合（`rtl/docs/09-synthesis-report.md`）；**还没有工艺库综合和时序（WNS）**，store 数据不在逐条对比范围内。已知风险见 [rtl/docs/08-risk-register.md](rtl/docs/08-risk-register.md)。
- **每次合入 main 的数字**以 [docs/MAIN_RECORDS.md](docs/MAIN_RECORDS.md) 为准；在做的实验见 [docs/TODO.md](docs/TODO.md)。

## 复现

细节见 `trace-model/docs/PROJECT.md` 和 `rtl/docs/README.md`。要点：

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
