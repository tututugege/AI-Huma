# AI-Huma

一个乱序 RISC-V CPU 的项目：用 AI 和人协作，把一个 RTL 风格的周期精确 C++ 模型，蒸馏成紧凑、快速、周期完全一致的
trace 模型，再生成并验证与之逐拍一致的 RTL。

## 名字的由来

AI-Huma 有两层意思：

1. **AI + Human**：项目由人定方向、定验收标准，AI 做大部分重写、验证和翻译工作。
2. **Huma**：致敬作者最喜欢的动漫角色雷姆（Re:Zero）的魔法。

## 三个部分

| 部分 | 目录 | 作用 |
|---|---|---|
| **function-model** | `function-model/` | 功能模型：只管指令执行的结果（寄存器、访存、CSR、分页），不管时序。基于 tututugege/GenSimpoint，库名 `librefcpu`。 |
| **trace-model** | `trace-model/` | 时序模型：由 tututugege/simulator 蒸馏而来，不再计算数据值，分支方向/目标、地址、store 数据、CSR 写数据都来自功能模型提供的"事实"，只保留周期精确的时序行为。 |
| **rtl** | `rtl/`（2026-11-04 起在此，原 `~/personal/tututugege-rtl`） | 把各个模块翻成 SystemVerilog，对着 trace-model 的输出逐拍比对。 |

三者的关系：function-model 产生执行事实，trace-model 在事实驱动下给出每一拍的时序，rtl 在同样的输入下必须与它每一拍都一致。

## 文档

- [docs/WORKFLOW.md](docs/WORKFLOW.md)：分支与提交规则、harness 要求、实验流程。
- [docs/LOG.md](docs/LOG.md)：每次 commit 做了什么。

## 核心原则

- **周期一致是唯一的正确性标准**。每次修改都要保持周期数完全不变，通过 gate（61 个测试）和几个大程序来检查。
- **重写加差分测试，不靠覆盖率裁剪**。每个重写的模块都对着冻结的原版做 lockstep 或随机差分；只靠覆盖率删代码曾经误删过 DDR 写路径，所以不采用。
- **目标是方法，而不只是代码**：能否把一个周期精确模型系统地变得更小、更快，并留下可复用的验证手段。

## 当前状态（2026-11-03）

**trace-model**
- 代码量从约 84k 行降到约 43k 行。后端各模块、BPU、LLC、AXI 互联、前端 `front_comb_calc`、`rv_simu_mmu_v2.cpp` 都已重写或整理。
- 速度：dhrystone 约 237 k cycles/s（原模型约 186 k，快约 27%），coremark10 约 140 k cycles/s。单次测量，机器有负载，仅供参考。
- 验证：gate 61/61；dhrystone 3,911,612、coremark10 976,652、memory-stress 1,541,195、smc-div 8,996、smc-addi 8,866 周期，均与原模型一致。
- 未覆盖：MemSubSystem 外设（无测试覆盖）、checkpoint 恢复、两条没有测试能走到的 Ren 路径。

**function-model**
- 保持上游行为，我们只加了一个"无副作用的虚实地址翻译"接口，供 trace-model 的桥使用。已独立成仓库。

**rtl**
- 进行中，由多个 agent 分模块并行。TlbMmu 已完成：lint 干净，vm 测试、dhrystone 和随机 trace 逐拍一致。
- LSU、整数执行单元、FPU、执行控制、前端基础等模块在做，尚未提交，没有最终报告。
- 前端分析的结论：一些 full/empty 锁存位是队列大小的纯函数，RTL 里不需要建；若干双请求和旁路路径是死代码。
- 模块间接口（事件加事实协议）目前只有文档，尚未冻结，这是下一阶段的关键。

## 下一步

1. 把 rtl 搬进本目录，三个仓库推到 GitHub。
2. 冻结 trace-model 与 rtl 之间的接口协议。
3. 扩大 gate：现在的测试程序都很小。
4. trace-model 里剩下的小优化（每项不到 3%）和状态标志的整理。

## 复现

细节见 `trace-model/docs/PROJECT.md`。要点：

```bash
cd trace-model
git submodule update --init
gmake -C GenSimpoint librefcpu.a LDFLAGS="-lz"
gmake LDFLAGS="-lz" -j8
bash scripts/run_gate.sh build/simulator results/gate
```
