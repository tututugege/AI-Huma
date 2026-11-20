---
name: ai-huma-merge-main
description: >-
  Use this skill when preparing to merge an experimental branch into main across function-model,
  trace-model, and rtl, cleaning up adopted switches, regenerating baselines/ref_cycles,
  and updating MAIN_RECORDS.md, LOG.md, EXPLORATION.md, and TODO.md.
---

# AI-Huma 合入 `main` 清单

对应 [docs/WORKFLOW.md](../../../docs/WORKFLOW.md) 第 1、6、6.1、7.6 节。**三仓一起合，不单独把某一边先放进 `main`；未经用户明确要求不提交、不推送。**

## 1. 清理与收口（只合结论）

1. **实验代码留在分支**：插桩、近似实现、临时脚本保留在 `exp/<名字>` 分支并提交保存，不进 `main`。
2. **采纳即删旧开关（`WORKFLOW.md` §7.6）**：
   - 检查分支引入的每个开关/宏，若另一个取值不再需要每日回归，直接写死新行为、删除旧开关、旧分支及对应文档说明。
   - 确认 `trace-model/include/config.h` 默认值 = RTL 配置；RTL 侧 `make cfg` 不带 `-D` 生成的 `ttg_cfg_pkg.sv` 必须逐字节一致。
3. **检查短 gate 程序**：确认新行为在 `rtl/programs/directed/` 已有对应的短测试程序并进回归表。

## 2. 更新基线与参考周期（唯一入口）

- `trace-model` 分两步提交（如先加实现再切默认值），切默认值时通过 `scripts/write_baseline.sh` 重生成 `results/baseline/baseline*.csv`，并更新 `trace-model/docs/PROJECT.md` 的大程序标准周期。
- `rtl` 通过 `scripts/regen_refs.sh` 更新 `scripts/ref_cycles.txt`，并与 `trace-model` 基线交叉核对。

## 3. 在提交后的代码上全量复验（不得拿实验期旧结果代替）

- **`trace-model`**：
  - `python3 scripts/comb/comb_graph.py --check` 0 隐患。
  - `RVC=0`（`run_gate.sh`）与 `RVC=1`（`run_gate_c.sh`）门禁全部通过且周期等于新基线。
  - 大程序（`dhrystone`、`coremark`、`memory-stress`、`smc-*`）核对通过。
  - **必跑 Linux 启动**：`scripts/linux_check.sh <模拟器> <镜像>` 到 `rv64 login:` 无 oops/panic。
- **`rtl`**：
  - `scripts/lint.sh`、`scripts/lint_chip.sh` 0 警告。
  - `scripts/fm_gate.sh` 全部通过（0 不一致，周期与 `ref_cycles.txt` 0 处不同，串口输出核对一致）。
  - Linux 检查点窗口 `scripts/linux_segments_cmp.sh` 全部 PASS（PT/UP 指纹全程相等，逐条检查 0 不一致），合入前最终确认完整从复位启动 `scripts/linux_gate.sh`（上 `eda` 集群）。
- **性能与面积**：
  - 固定负载（dhrystone 64 次、coremark 2 次、memory-stress-small）+ `eda` 集群 SPEC06（带 `PMU=1`；旧基线先查记录不重跑）。
  - 受影响模块 Yosys 前后综合对比（遵守防 OOM 红线）。

## 4. 同步文档（同一合入提交内完成）

按 [docs/WORKFLOW.md](../../../docs/WORKFLOW.md) §6.1 逐一检查并更新：
1. [docs/MAIN_RECORDS.md](../../../docs/MAIN_RECORDS.md)：表顶部追加一行（四仓 commit、正确性、固定负载、RTL 周期、综合结果）+ 表下新增一节“变化”（配置变化表、设计改动与修 bug、验证范围含跑了/没跑什么、已知回退、对应 EXP 编号）。
2. [docs/EXPLORATION.md](../../../docs/EXPLORATION.md)：对应 `EXP-xxx` 状态改为“已合入”（历史正文不改写）。
3. [docs/TODO.md](../../../docs/TODO.md)：删除已完成项，补充新发现的遗留或收尾项。
4. [docs/LOG.md](../../../docs/LOG.md)：每个 commit 追加一行（做了什么、验证结果、结论、EXP 编号）。
5. [README.md](../../../README.md) 及受影响子仓库文档（`rtl/docs/modules/<模块>.md`、`ENV_VARS.md`、`docs/GUIDE.md`）：清理过时的状态词、已删开关、失效链接与不一致数字。

## 5. 更新总仓库指针

各子仓库分支快进合入 `main` 后，总仓库更新三个子模块指针并提交（等待用户确认后再执行 commit / push）。
