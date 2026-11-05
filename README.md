# AI-Huma

一个乱序 RISC-V CPU 的项目：用 AI 和人协作，把一个 RTL 风格的周期精确 C++ 模型，蒸馏成紧凑、快速、周期完全一致的  
trace 模型，再生成并验证与之逐拍一致的 RTL。之后通过三个model协同交互迭代，目标是成为 Agentic CPU 训练大师。

## 名字的由来

AI-Huma 有两层意思：

1. **AI + Human**：项目由人定方向、定验收标准，AI 做大部分重写、验证和翻译工作。
2. **Al-Huma(**アル・ヒューマ**)**：致敬作者最喜欢的动漫角色雷姆（Re:Zero）的魔法。

## 三个部分

| 部分 | 目录 | 作用 |
|---|---|---|
| **function-model** | `function-model/` | 功能模型：只管指令执行的结果（寄存器、访存、CSR、分页），不管时序。基于 tututugege/GenSimpoint，库名 `librefcpu`。也负责 SPEC 的 BBV/SimPoint/检查点生成。 |
| **trace-model** | `trace-model/` | 时序模型：由 tututugege/simulator 蒸馏而来，不再计算数据值，分支方向/目标、地址、store 数据、CSR 写数据都来自功能模型提供的“事实”，只保留周期精确的时序行为。核参数的唯一来源（`include/config.h`），也是架构探索用的模型。 |
| **rtl** | `rtl/` | SystemVerilog 实现（约 270 个 RTL 文件、2.6 万行），整核测试平台（Verilator）逐条提交对比 function-model；参数包由 trace-model 的 `config.h` 生成。 |

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
- **周期数、IPC 是性能指标**。trace-model 是性能参考和架构探索模型；探索的结论（例如第 3 批面积配置）先在 trace-model 上验证，再同步到 RTL，合入 main 时两者周期逐个相等。
- **旧的逐模块锁步 / trace 回放 / 变异检查体系已退役**（代码在 rtl 标签 `legacy-reference`，文档在 `rtl/docs/history/`）。
- **目标是方法，而不只是代码**：能否把一个周期精确模型系统地变得更小、更快，并留下可复用的验证手段。

## 当前状态（2026-11-05）

- **配置**：第 3 批面积配置（EXP-005）正在合入 main：取指宽度 8、在飞分支 32、IQ 总项数 384→240、发射端口 22→18 等。quick SPEC 6 个程序 IPC −0.5%，受影响模块约 −161 万门（整机约 17%）。
- **trace-model**：gate 62/62；Linux 启动到登录约 7–8 千万周期；quick/full SPEC 回放（580 个 rv32imab 检查点）。
- **rtl**：lint 干净（按目录和整芯片）；66 个程序逐条对比全部通过、周期与 trace-model 逐个相等；有面积代理综合（`rtl/docs/09-synthesis-report.md`）；**还没有时序综合**，store 数据不在逐条对比范围内。已知风险见 [rtl/docs/08-risk-register.md](rtl/docs/08-risk-register.md)。
- **在做的实验**：LD/STA IQ 合并、统一 FTQ 的 RTL 试做（见 [docs/TODO.md](docs/TODO.md)）。

## 复现

细节见 `trace-model/docs/PROJECT.md` 和 `rtl/docs/README.md`。要点：

```bash
# trace-model 依赖同级的 function-model（trace-model/function-model 是指向 ../function-model 的符号链接）
gmake -C function-model librefcpu.a LDFLAGS="-lz"
cd trace-model
gmake LDFLAGS="-lz" -j8
bash scripts/run_gate.sh build/simulator results/gate      # 62 个程序，周期等于 results/baseline/baseline.csv

# rtl：lint，带 function-model 逐条对比的整核门禁（需要先构建 trace-model 的测试程序）
cd ../rtl
bash scripts/lint.sh && bash scripts/lint_chip.sh
SOC_FM=1 SOC_OUT=$PWD/build/soc_fm bash tb/soc/build.sh
bash scripts/fm_gate.sh $PWD/build/soc_fm/obj/soc_tb $PWD/build/gate   # 66/66，并报告与 trace-model 周期不同的个数
```
