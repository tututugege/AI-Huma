# 文档导航

AI-Huma 由总仓库和三个子仓库组成，文档分两层：**总仓库 `docs/` 放全项目的规则、记录和待办**；**各子仓库只放“本仓库是什么、怎么跑、模块怎么设计”**。
已退役的文档挪进各仓库的 `docs/history/`，只供查阅。

```
AI-Huma/                     总仓库：全项目文档（本目录）
├── function-model/          功能模型：架构行为的标准；SPEC BBV/SimPoint/检查点
├── trace-model/             时序模型：周期的标准；核参数的唯一来源（include/config.h）；架构探索
└── rtl/                     SystemVerilog 实现 + 整核测试平台
~/personal/AI-Huma-data/     生成的数据（不进仓库）：spec-rv32imab/、linux/、tools/
```

## 1. 我要……看哪份

| 要做的事 | 先看 | 再看 |
|---|---|---|
| 第一次了解项目 | [../README.md](../README.md) | 本文第 2 节 |
| 知道规则：分支、提交、正确性标准、什么时候能合入 main | [WORKFLOW.md](WORKFLOW.md) | rtl [06-equivalence-policy.md](../rtl/docs/06-equivalence-policy.md) |
| 查现在的性能、面积数字 | [MAIN_RECORDS.md](MAIN_RECORDS.md)（最新一行） | rtl [09-synthesis-report.md](../rtl/docs/09-synthesis-report.md) 第 9 节 |
| 查接下来要做什么 | [TODO.md](TODO.md) | — |
| 查某次改动做了什么、怎么验证的 | [LOG.md](LOG.md) | 对应仓库的 git log |
| 做一次架构/性能探索 | [WORKFLOW.md](WORKFLOW.md) 第 4、5.1 节 | [EXPLORATION.md](EXPLORATION.md)（先看有没有人做过） |
| 把探索结论合入 main | [WORKFLOW.md](WORKFLOW.md) 第 6 节（步骤清单） | [MAIN_RECORDS.md](MAIN_RECORDS.md) 的格式 |
| 构建、跑 trace-model 和它的 gate | trace-model [README.md](../trace-model/README.md) | trace-model [docs/PROJECT.md](../trace-model/docs/PROJECT.md)（架构、gate、参数开关） |
| 改核参数（IQ 大小、端口数……） | trace-model [docs/PROJECT.md](../trace-model/docs/PROJECT.md) “Configuration knobs” | rtl [scripts/README.md](../rtl/scripts/README.md)（`make cfg`、`lint_chip.sh`） |
| 写或改 RTL | rtl [docs/README.md](../rtl/docs/README.md) | [01 编码规范](../rtl/docs/01-rtl-coding-standard.md)、[modules/](../rtl/docs/modules/) 里该模块的笔记 |
| 跑 RTL 门禁、Linux、综合 | rtl [scripts/README.md](../rtl/scripts/README.md) | rtl [modules/soc_top.md](../rtl/docs/modules/soc_top.md)（测试平台细节） |
| 评估 RTL 验证的可信度、已知缺口 | rtl [08-risk-register.md](../rtl/docs/08-risk-register.md) | [TODO.md](TODO.md) “待做：验证” |
| 生成或回放 SPEC 检查点 | function-model [scripts/spec/README.md](../function-model/scripts/spec/README.md) | function-model [docs/SIMPOINT_SPECINT2006.md](../function-model/docs/SIMPOINT_SPECINT2006.md)（原理）；trace-model `scripts/spec/replay.sh` |
| 生成 Linux 镜像 | function-model [linux/README.md](../function-model/linux/README.md) | — |
| function-model 的 difftest、检查点恢复 | function-model [docs/DIFFTEST.md](../function-model/docs/DIFFTEST.md) | [FRONTDOOR_RESTORE.md](../function-model/docs/FRONTDOOR_RESTORE.md)、[SPIKE_DIFFTEST.md](../function-model/docs/SPIKE_DIFFTEST.md) |

## 2. 全部文档

### 总仓库 `docs/`（全项目）

| 文档 | 管什么 | 什么时候写 |
|---|---|---|
| [GUIDE.md](GUIDE.md) | 本导航 | 增删文档时 |
| [WORKFLOW.md](WORKFLOW.md) | 全项目的规则和流程：分支与提交、正确性标准、harness、实验流程、记录要求、合入 main 的步骤 | 规则变化时 |
| [TODO.md](TODO.md) | **唯一的**待办清单（进行中 / 待做：验证、RTL 实现、流程与工具） | 随时；做完删除并在 LOG 留一行 |
| [LOG.md](LOG.md) | 每个 commit 一行：做了什么、怎么验证、结论 | 每次提交 |
| [EXPLORATION.md](EXPLORATION.md) | 每次架构/性能探索一节（EXP-编号）：问题、方法、模型近似、结果、结论；不论是否合入 | 每次探索 |
| [MAIN_RECORDS.md](MAIN_RECORDS.md) | 每次合入 main 一行（版本、正确性、性能、RTL 周期、综合）+ 一节“变化”；**当前数字的权威来源** | 每次合入 main |

### function-model

| 文档 | 管什么 |
|---|---|
| [README.md](../function-model/README.md) | 功能模型是什么、怎么构建和运行、接口 |
| [docs/DIFFTEST.md](../function-model/docs/DIFFTEST.md) | difftest 接口 |
| [docs/SPIKE_DIFFTEST.md](../function-model/docs/SPIKE_DIFFTEST.md) | 与 Spike 的对比 |
| [docs/FRONTDOOR_RESTORE.md](../function-model/docs/FRONTDOOR_RESTORE.md) | 前门检查点恢复（`ckpt2stub`） |
| [docs/SIMPOINT_SPECINT2006.md](../function-model/docs/SIMPOINT_SPECINT2006.md) | SimPoint 原理；现行流程与上游流程的对照 |
| [scripts/spec/README.md](../function-model/scripts/spec/README.md) | 现行 SPEC 检查点流程（rv32imab、Linux 镜像、ref 输入、参数、耗时） |
| [linux/README.md](../function-model/linux/README.md) | Linux 镜像（OpenSBI + 内核 + initramfs）的生成 |

### trace-model（英文）

| 文档 | 管什么 |
|---|---|
| [README.md](../trace-model/README.md) | 是什么、构建、gate |
| [docs/PROJECT.md](../trace-model/docs/PROJECT.md) | 架构、来历、gate 和大程序标准周期、参数开关（`CFG_*`）、验证手段 |
| `front-end/*.md` | 上游带来的前端写法规范和训练函数清单（前端代码的参考） |
| `docs/history/` | 蒸馏计划 `PLAN.md` 和各阶段记录（P0–P3），已完成 |

### rtl

| 文档 | 管什么 |
|---|---|
| [docs/README.md](../rtl/docs/README.md) | rtl 文档索引、常用命令、目录结构 |
| [00-scope-and-decisions.md](../rtl/docs/00-scope-and-decisions.md) | 范围、参考、技术决策 |
| [01-rtl-coding-standard.md](../rtl/docs/01-rtl-coding-standard.md) | 编码规范（lint 检查） |
| [04-cpp-to-rtl-mapping.md](../rtl/docs/04-cpp-to-rtl-mapping.md) | C++ 构造到 SV 的写法对照 |
| [05-module-tracker.md](../rtl/docs/05-module-tracker.md) | 模块进度表（自动生成） |
| [06-equivalence-policy.md](../rtl/docs/06-equivalence-policy.md) | 正确性原则：现行门禁、不比较什么 |
| [08-risk-register.md](../rtl/docs/08-risk-register.md) | 风险登记簿（只记风险） |
| [09-synthesis-report.md](../rtl/docs/09-synthesis-report.md) | 面积代理综合的方法和逐模块数字 |
| [modules/](../rtl/docs/modules/) | 每个模块的设计笔记（“验证”一节多为旧体系结果） |
| [analysis/](../rtl/docs/analysis/README.md) | 边界与结构分析（设计内容仍可参考） |
| [deviations.md](../rtl/docs/deviations.md) | 旧体系的差异登记（不再新增，S 编号仍被引用） |
| [scripts/README.md](../rtl/scripts/README.md) | 脚本索引 |
| `docs/history/` | 已退役：逐模块开发流程、逐拍对照 harness、翻译阶段路线图、翻译任务书、录制点 |

## 3. 每类信息只记在一处

| 信息 | 只记在 | 别处怎么做 |
|---|---|---|
| 规则、流程 | [WORKFLOW.md](WORKFLOW.md) | 子仓库只写本仓库的具体命令，链接过来 |
| 待办 | [TODO.md](TODO.md) | 风险登记簿只记风险；README 不再列“下一步” |
| 当前性能、面积 | [MAIN_RECORDS.md](MAIN_RECORDS.md) | README 只写一句概况；trace-model `PROJECT.md` 只放 gate 要用的标准周期 |
| 实验数字和结论 | [EXPLORATION.md](EXPLORATION.md) | LOG 那一行写 EXP 编号 |
| 某次提交做了什么 | [LOG.md](LOG.md) + commit 说明 | — |
| 核参数 | trace-model `include/config.h` | rtl 的 `ttg_cfg_pkg.sv` 由 `make cfg` 生成，不手写 |
| 验证缺口、风险 | rtl [08-risk-register.md](../rtl/docs/08-risk-register.md) | 要补的动作写进 TODO |
| 生成的数据在哪、怎么生成 | 生成它的脚本的 README（如 `scripts/spec/README.md`） | 不放 `/tmp` |

## 4. 维护约定

- 新增或挪动文档时更新本导航；挪动后检查相对链接（所有仓库都不应有坏链接）。
- 退役的文档不删，挪进本仓库的 `docs/history/`，并在索引里注明。
- 新写的文档用中文；trace-model 已有的英文文档暂不翻译。
- 子 agent 交回的设计文档（如 `LDSTA_MERGE.md`、`UNIFIED_FTQ.md`）跟着它所在的实验分支提交，结论摘要写进 [EXPLORATION.md](EXPLORATION.md)。
