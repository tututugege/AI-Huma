# AI-Huma 工作流程与 harness 要求

适用于 `function-model`、`trace-model`、`rtl` 三个仓库。项目已经过了“复刻原模型”的阶段，现在的工作是在自己的 base 上做优化：本文规定一个想法怎样被量化（第 4–5 节）、怎样同步到 RTL 并合入 main（第 6 节）。

## 1. 分支与提交规则

1. **`main` 上只有已验证、已对齐的东西。**
2. **探索实验一律放分支**，分支名 `exp/<名字>`（RTL 模块用 `rtl/<模块>`）。实验没有结论、或者 RTL 与模型还没对齐之前，不进 `main`。
3. **合入 `main` 的条件**：RTL 和 trace-model 同时跑通，周期逐拍对齐，gate 和 harness 全部通过，并且这次合入的内容在 LOG 里有记录。三个仓库按这个条件一起合，不单独把某一边先放进 `main`。
4. **没有明确要求不提交、不推送。** 修改先留在工作区或分支，让负责人确认。
5. **每个 commit 只做一件事**，标题写清楚做了什么；提交之后在 [LOG.md](LOG.md) 追加一行记录。
6. **所有改动都要附带验证结果**（周期数、通过的 harness；变异检查按下面第 3 节的规定，不再是必须项），写在 commit 说明和 LOG 里，不写"应该没问题"。

## 2. 正确性标准

- **trace-model**：周期数与原模型完全一致，是唯一的正确性标准。开关默认关闭的实验，关闭时也必须保持完全一致。
- **rtl**（2026-11-04 起，见 `rtl/docs/06-equivalence-policy.md`）：正确性 = 整核测试平台逐条提交与 function-model 一致（提交 PC + 目的寄存器值）。周期数是性能指标；**合入 main 时**要求同一配置下 RTL 与 trace-model 整程序周期逐个相等（第 1 节第 3 条）。逐条对比不比较 store 数据和内存，访存/外设路径有改动时还要对比串口输出。
- **function-model**：提交序列与参考模型一致。

## 3. 必须具备的 harness

### 3.1 trace-model

| harness | 作用 | 位置 / 命令 |
|---|---|---|
| gate | 62 个测试，周期与基线一致 | `scripts/run_gate.sh build/simulator results/gate` |
| 大程序 | dhrystone 64 次、coremark 2 次迭代（2026-11-04 起固定为这两个缩短版）、memory-stress、smc-div、smc-addi；当前标准周期见 `trace-model/docs/PROJECT.md` 的 Gate 第 4 条，随配置变化更新 | dhrystone/coremark 在 `rtl/programs/big`，其余在 `trace-model/build/tests`；每次改动后检查 |
| Linux | 镜像 `~/personal/AI-Huma-data/linux/linux.bin`（`function-model/linux/mkimage.sh`，`MEM=0x10000000`），从复位启动到 `rv32 login:` | 合入 main 前必跑 |
| small-LLC 检查 | 默认 8 MiB LLC 在小测试里不会换出，用 64 KiB LLC 检查 DDR 写回路径 | `scripts/llc_small_check.sh $PWD <baseline-sim/src 绝对路径>` |
| lockstep 影子 | 把冻结的原模块和重写的模块在同一模拟里并行跑，每个阶段比较输出和状态摘要，不一致退出码 2 | `scripts/*_shadow.sh`，参考副本在 `tests/*_ref` |
| 随机差分 | 随机激励下比较重写模块和冻结原版：`bpu_diff`、`csr_diff`、`idu_diff`、`pre_diff`、`ddr_diff`；闭环 `llc_diff`、`ic_diff` | `scripts/*_diff.sh` |
| 不变量检查 | 实验特性自带的每周期检查，例如移动消除的 `ME_CHECK=1`（引用计数一致、无物理寄存器泄漏） | 环境变量开启 |

### 3.2 rtl

| harness | 作用 |
|---|---|
| lint | `scripts/lint.sh`（按目录、规范 + `-Wall`）和 `scripts/lint_chip.sh`（以 `soc_top` 为顶的整芯片 `-Wall`）都要 0 警告；改参数前用 `CFG=<配置包> scripts/lint_chip.sh` 预查写死的位宽 |
| 逐条对比门禁 | `scripts/fm_gate.sh`：`ref_cycles.txt` 里 66 个程序（gate + vm + dhrystone + coremark）在整核测试平台上逐条对比 function-model，全部通过；同时报告与 trace-model 周期（`ref_cycles.txt`）不同的个数 |
| Linux | 整核测试平台（`SOC_FM=1`、`SOC_VOPT="--threads 4 -DTTG_EBREAK_TRAP"`），`SOC_TB_FM=1 SOC_TB_SEMIHOST=1` 从复位启动到 `rv32 login:`，全程逐条对比（数小时） |
| 综合对比 | `scripts/synth_cfg.sh`：受影响模块在改动前后各综合一遍（面积代理，见 `rtl/docs/09-synthesis-report.md`） |
| 已退役（2026-11-04） | 模块边界 trace 回放、整程序实时锁步、随机 trace：随旧参考模型退役，脚本在 rtl 标签 `legacy-reference` |
| 变异检查（可选，不是门禁） | 故意改坏 RTL，检查 harness 能否抓到。2026-11-04 起：**不要求把存活变异清零**（跑一遍太慢），改为把存活和未运行的变异、覆盖缺口、未验证项如实记录在 `rtl/docs/08-risk-register.md`，不得默认当作没问题 |

### 3.3 通用要求

- **新模块或新特性要同时带 harness。** 没有测试能区分对错的行为，不算验证过。
- **新 harness 自己要先验证**：植入一个已知 bug，确认能抓到。
- **变异存活要记录**：存活或未运行的变异不要求立刻清零，但必须登记（模块、变异内容、判断是等价还是覆盖缺口、风险等级）；改动过的模块要在登记簿里注明变异结果已过期。
- **覆盖率裁剪不算验证**：只靠覆盖率删代码曾误删 DDR 写路径，所以删代码要靠重写加差分测试。
- **测量要可复核**：写清楚测的是什么、跑了几次、机器负载；速度类的实验单次运行即可，但要标注。

## 4. 实验的流程

1. 从 `main` 切 `exp/<名字>`。
2. 实现，默认关闭（环境变量或编译开关）。
3. 开关关闭时：gate 和大程序周期必须不变。
4. 开关开启时：功能自检（提交指令数一致、不变量检查通过），再记录性能数字。
5. 提交到实验分支，在 LOG 追加记录，写明"未合入"。
6. **在 [EXPLORATION.md](EXPLORATION.md) 写实验记录**（见第 5 节），没有结论的实验也要记。
7. 结论与负责人讨论；要合入时，按第 1 节第 3 条的条件一起合，并在 [MAIN_RECORDS.md](MAIN_RECORDS.md) 记录性能和综合结果。

## 5. 记录要求

项目在持续演进，数字只有记下来才能比较。三类记录各管一件事（全部文档的分工见 [GUIDE.md](GUIDE.md)，待办只记在 [TODO.md](TODO.md)）：

| 文件 | 什么时候写 | 写什么 |
|---|---|---|
| [LOG.md](LOG.md) | 每次 commit | 一行：做了什么、怎么验证、结论 |
| [EXPLORATION.md](EXPLORATION.md) | **每次架构/性能探索**，不论是否合入、不论结论正负 | 一节：问题、方法（开关、模型近似）、负载、结果表、结论、后续 |
| [MAIN_RECORDS.md](MAIN_RECORDS.md) | **每次合入 `main`** | 一行：各仓库 commit、性能数字、综合结果 |

### 5.1 探索记录（EXPLORATION.md）

- 编号 `EXP-<三位数>`，新的写在最上面；LOG 里那一行写上编号。
- 必须写：分支和是否提交；开关名和默认值（默认关闭时周期不变的验证结果）；负载清单和运行上限；**模型近似**（哪些地方不是真实设计，可能带来多大误差）；结果表（周期与相对基线的变化）；面积估算的依据（位宽从哪里来）；结论和未覆盖的风险。
- 负面结果同样要记，免得重复做。
- 原始日志不进仓库；记录里写清楚复现命令。

### 5.2 合入 main 记录（MAIN_RECORDS.md）

每次合入 `main` 追加一行，至少包含：

- **版本**：总仓库和三个子仓库的 commit。
- **正确性**：gate 通过数；RTL 整核逐条对比通过数。
- **性能**（trace-model，固定负载）：dhrystone（64 次）、coremark（2 次迭代）、memory-stress-small 的周期数和 IPC；有变化时写相对上一条的百分比。
- **RTL 周期**：同样负载在 RTL 上的周期数（与 trace-model 的差距用来发现性能回退）。
- **综合**：工具和版本、工艺/库、约束频率、面积（总面积和主要模块）、时序裕量（WNS）。**还没做综合时写"未做"和原因**，不留空。
- 有意的性能或面积回退要在"说明"里写原因。
- **表下面每次合入另写一节“变化”**：配置变化表（参数、旧值、新值）；设计改动和修掉的 bug（每条一句）；验证范围（跑了什么、没跑什么）；已知回退；对应的 EXP 编号和各仓库 commit。只看表里一行看不出这次合入改了什么，这一节就是为此而写。

## 6. 探索成果合入 main 的步骤

第一次走这个流程是 2026-11-05（EXP-005 的第 3 批面积配置），下面的步骤按那次的做法整理。

1. **只合结论**。实验插桩、近似实现、实验脚本留在 `exp/<名字>` 分支并提交保存，不进 `main`；进 `main` 的是干净的实现。从 `main` 切新分支（例如 `exp/batch3`）放要合入的内容。
2. **trace-model 分两步提交**：先加开关、默认值保持原设计（gate 与基线逐个相同、大程序周期不变）；再单独提交新的默认值，同时更新 `results/baseline/baseline.csv`（每个 gate 程序都以 difftest Success 结束、无不一致）和 `docs/PROJECT.md` 的大程序标准周期。
3. **rtl 跟着 trace-model 的默认值走**：`make cfg` 不带 `-D`，生成的 `ttg_cfg_pkg.sv` 必须与实验时用的配置包逐字节相同；`scripts/ref_cycles.txt` 换成新周期，并与 trace-model 的 `baseline.csv` 交叉核对。写死的位宽、维度改成从配置推出，和改参数分开提交。
4. **在提交后的代码上复验**（不能拿实验时的结果代替）：
   - trace-model：gate 62/62，大程序，Linux 从复位启动到 `rv32 login:`；
   - rtl：`lint.sh`、`lint_chip.sh` 0 警告；`fm_gate.sh` 66/66，周期与 trace-model 逐个相等；串口输出与上一版一致（打印计时器的 `timer-mmio` 除外）；Linux 从复位启动到 `rv32 login:`，全程逐条对比；
   - 原配置参数下的回归：改动若声称“原配置下不变”，用原配置包再跑一遍门禁确认周期逐个相同。
5. **性能和面积**：固定负载（第 5.2 节）+ quick SPEC（`trace-model/scripts/spec/replay.sh quick`）；受影响模块的综合前后对比。
   - **旧配置（main）的 SPEC 数字先查记录，不要重跑**：先看 `trace-model/results/baseline/baseline.csv`、`MAIN_RECORDS.md`、`LOG.md`（例如 `deb15b4` 已记录合并后全量 580/580）。记录里有同一预热方式、同一检查点的结果就直接引用；只有记录缺失，或 main 自那次记录之后周期有变化（改了模型默认值），才重跑，且只重跑缺的点或抽样核对。SPEC 一律上服务器（`fleet.sh`），新配置才需要全量跑。
   - **SPEC 默认开 `PMU=1`**：每次跑 SPEC（quick、30 点、全量）都带 `PMU=1`，结果里要有 TMA 一级（retiring / bad-spec / frontend / backend）。PMU 不改周期，开了没有代价；没开的结果事后补不回来。性能对比表里 TMA 一级新旧差异和周期一起给。
6. **记录**：`MAIN_RECORDS.md` 一行 + “变化”一节；`LOG.md` 每个 commit 一行；`EXPLORATION.md` 对应实验的状态改成“已合入”；`TODO.md` 删除已完成项。
7. **合入**：各子仓库把分支快进合入 `main`，总仓库更新子模块指针并提交。提交作者用 `tututugege <903306512@qq.com>`。没有明确要求不推送。
