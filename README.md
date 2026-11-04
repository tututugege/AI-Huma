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
| **function-model** | `function-model/` | 功能模型：只管指令执行的结果（寄存器、访存、CSR、分页），不管时序。基于 tututugege/GenSimpoint，库名 `librefcpu`。 |
| **trace-model** | `trace-model/` | 时序模型：由 tututugege/simulator 蒸馏而来，不再计算数据值，分支方向/目标、地址、store 数据、CSR 写数据都来自功能模型提供的"事实"，只保留周期精确的时序行为。 |
| **rtl** | `rtl/` | 把各个模块翻成 SystemVerilog（约 300 个文件、3 万行），每个模块边界逐拍对照，并有整核闭环测试平台（Verilator）。 |

三者的关系：function-model 产生执行事实，trace-model 在事实驱动下给出每一拍的时序，rtl 在同样的输入下必须与它每一拍都一致。

## 仓库结构

`AI-Huma` 本身是**总仓库**，只放文档和忽略规则；三个子项目是各自独立的 git 仓库，作为 **git 子模块**引用（子模块 URL 现在是本地相对路径，发布时再改成真实地址）。

```bash
git clone <AI-Huma 地址>
cd AI-Huma
git submodule update --init          # 取出 function-model、trace-model、rtl
```

- 子模块指针记录的是各子仓库已提交的 commit，三个仓库现在都指向各自的 `main`（11-04 把 `exp/frontdoor-ckpt` 快进合入了 `main`，分支保留）。分支规则见 [docs/WORKFLOW.md](docs/WORKFLOW.md)。
- 构建产物、trace、参考模拟器副本等本地生成物（合计几个 GB）都被忽略，不进任何仓库；源码本身三个仓库加起来约 12 MB。

## 文档

- [docs/WORKFLOW.md](docs/WORKFLOW.md)：分支与提交规则、harness 要求、实验流程。
- [docs/LOG.md](docs/LOG.md)：每次 commit 做了什么。
- [trace-model/docs/PROJECT.md](trace-model/docs/PROJECT.md)：trace-model 的架构、gate 和验证手段。
- [rtl/docs/README.md](rtl/docs/README.md)：rtl 的文档索引（编码规范、开发流程、模块进度表、路线图）。
- [rtl/docs/08-risk-register.md](rtl/docs/08-risk-register.md)：**rtl 的风险登记簿**：变异存活与未运行、覆盖缺口、未验证项、最近改动的验证范围。

## 核心原则

- **周期一致是唯一的正确性标准**。每次修改都要保持周期数完全不变，通过 gate（62 个测试）和大程序来检查。大程序固定为 dhrystone 64 次迭代（150,838 周期）、coremark 2 次迭代（226,991 周期），再加 memory-stress（1,541,195）等；源码和二进制在 `rtl/programs/big/`。
- **重写加差分测试，不靠覆盖率裁剪**。每个重写的模块都对着冻结的原版做 lockstep 或随机差分；只靠覆盖率删代码曾经误删过 DDR 写路径，所以不采用。
- **变异检查不是门禁**：不要求存活变异清零，改为如实登记风险（见上面的风险登记簿）。
- **目标是方法，而不只是代码**：能否把一个周期精确模型系统地变得更小、更快，并留下可复用的验证手段。

## 当前状态（2026-11-04）

**trace-model**

- 代码量从约 84k 行降到约 43k 行。后端各模块、BPU、LLC、AXI 互联、前端 `front_comb_calc`、`rv_simu_mmu_v2.cpp` 都已重写或整理。
- 速度（2026-11-03 的单次测量，机器有负载，仅供参考）：dhrystone 约 237 k cycles/s（原模型约 186 k），coremark10 约 140 k cycles/s。
- 验证：gate 62/62（11-04 加入 `load-store-aligned`，原 `load-store` 在参考核里遇到未对齐 load 直接退出，没有基线）。
- 未覆盖：MemSubSystem 外设（无测试覆盖）、两条没有测试能走到的 Ren 路径。front-door checkpoint 恢复已合入 `main`（默认关闭；用 `--restore-stub`）。

**function-model**

- 保持上游行为，我们加了一个"无副作用的虚实地址翻译"接口，供 trace-model 的桥使用；另有速度优化、front-door checkpoint 恢复，以及指令上限和 BBV 间隔的环境变量（`REF_MAX_INSTS`、`REF_INTERVAL`），均已在 `main`。

**rtl**

- 前端、后端、访存子系统和整核都已翻成 SystemVerilog：lint 干净；整核闭环（RTL 核 + RTL 访存子系统 + 参考的 DDR/外设模型）跑 66 个程序，周期数与参考一致；与 trace-model 的 63 个 smoke 程序周期数、指令数全部一致。
- 边界对照是在**整程序周期数和指令数**层面，**模块边界与 trace-model 的逐拍对照还没做**（各模块是对着原参考模型的录制做的逐拍对照）。
- **没有做过综合**；变异存活没有清零；`memory-stress`、`float_test` 没在闭环里跑过。这些和其他已知风险都登记在风险登记簿里。

## 下一步

1. 给总仓库和三个子仓库配置远程地址，把子模块 URL 改成真实地址，推送。
2. 在小模块上做一次受限的综合检查（限制内存和时间），确认可综合。
3. rtl 与 trace-model 的模块边界逐拍对照。
4. 补跑 `memory-stress`、`float_test` 的闭环，以及完整的 68 个程序整程序锁步。
5. 扩大 gate：现在的测试程序都很小。
6. trace-model 里剩下的小优化（每项不到 3%）和状态标志的整理。

## 复现

细节见 `trace-model/docs/PROJECT.md` 和 `rtl/docs/README.md`。要点：

```bash
# trace-model 依赖同级的 function-model（trace-model/function-model 是指向 ../function-model 的符号链接）
gmake -C function-model librefcpu.a LDFLAGS="-lz"
cd trace-model
gmake LDFLAGS="-lz" -j8
bash scripts/run_gate.sh build/simulator results/gate

# rtl：lint、整核闭环、与 trace-model 对比（需要先构建 trace-model 和测试程序）
cd rtl
bash scripts/lint.sh
bash tb/soc/build.sh && bash scripts/soc_smoke.sh 250000
bash scripts/cmp_trace_model.sh
```
