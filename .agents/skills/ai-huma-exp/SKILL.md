---
name: ai-huma-exp
description: >-
  Use this skill when designing, implementing, or evaluating a microarchitecture or performance
  experiment in trace-model, checking comb scheduling contracts, or writing an EXP-xxx record
  in docs/EXPLORATION.md.
---

# AI-Huma 架构探索流程（trace-model）

对应 [docs/WORKFLOW.md](../../../docs/WORKFLOW.md) 第 4 节与第 5.1 节。

## 1. 启动探索

1. **先查重**：阅读 [docs/EXPLORATION.md](../../../docs/EXPLORATION.md) 索引与 [docs/TODO.md](../../../docs/TODO.md)，确认类似想法是否已做过（包括负面结论）。
2. **建分支 / worktree**：从 `main` 切出 `exp/<名字>`（需要与主工作区并行时用 `git worktree add ../trace-model-<名字> -b exp/<名字>`）。
3. **默认关闭开关**：实验特性通过编译宏（`CFG_*`）或环境变量控制，默认值保持与 `main` 一致，确保开关关闭时周期零变化。

## 2. `trace-model` 修改与调度核对

`trace-model` 采用声明式组合逻辑调度（所有模块寄存器统一为 `Regs q_, d`，每个 comb 阶段在头文件声明读写信号）：
- 修改模块接口或 comb 阶段后，先重新生成调度顺序（`gen_*_order.py --write`），再运行：
  ```bash
  python3 scripts/comb/comb_graph.py --check
  ```
  必须达到 **0 隐患、模块声明与代码一致**。
- 详细约定见 `trace-model/docs/SCHEDULING.md` 与 `trace-model/docs/ENV_VARS.md`。

## 3. 分层验证

1. **开关关闭（回归基线）**：
   - 本机（`iprc-jump`）跑 gate：`bash scripts/run_gate.sh build/simulator results/gate` 及 `run_gate_c.sh`（当前默认 `RVC=1`），周期必须与基线逐个相等。
2. **开关开启（功能与时序自检）**：
   - gate 全量 difftest Success，打开实验自带的不变量检查。
   - **必跑 Linux 启动**：改动涉及时序/访存/前端行为时，运行 `trace-model/scripts/linux_check.sh <模拟器> ~/rv64spec/linux_j.bin`（67 个小程序抓不到 wrong-path 类时序回归）。
3. **大规模性能评估（上 `eda` 集群）**：
   - 激活 `ai-huma-eda` Skill，在 `eda-04` ~ `eda-10` 跑 SPEC06（先 59 点/抽样，再 386 点 `jobs95.txt`），**必须带 `PMU=1`** 输出 TMA 一级指标。
   - 对比已有 `main` 基线（先查记录和 NFS `res_*`，不重跑未变基线）。

## 4. 撰写探索记录（`docs/EXPLORATION.md`）

无论实验结论正负、是否合入，都必须在 [docs/EXPLORATION.md](../../../docs/EXPLORATION.md) 顶部追加一节（编号 `EXP-<三位数>`）：
- **元信息**：分支名、是否提交、状态（探索中 / 已放弃 / 待合入 / 已合入）、开关名及默认值（附“默认关周期不变”验证）。
- **方法与模型近似**：明确列出哪些地方是近似建模、可能引入多大误差、硬件面积/位宽估算依据。
- **负载与结果表**：负载清单、周期与相对基线变化、TMA 一级差异、复现命令（原始日志不进仓库）。
- **结论与风险**：给出明确结论及未覆盖风险；若提交到实验分支，在 `docs/LOG.md` 追加一行注明“未合入”和 `EXP-xxx` 编号。
