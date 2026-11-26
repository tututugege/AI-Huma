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

- **trace-model**：正确性 = 每个 gate 程序以 difftest Success 结束（与 function-model 提供的“事实”一致）；回归标准是 gate 周期等于 `results/baseline/baseline.csv`。开关默认关闭的实验，关闭时周期必须与基线逐个相同；改默认值时重生成基线（第 6 节第 2 步）。原模型的周期已不再是标准（2026-11-04 起）。
- **rtl**（2026-11-04 起，见 `rtl/docs/06-equivalence-policy.md`）：正确性 = 整核测试平台逐条提交与 function-model 一致（提交 PC + 目的寄存器值）。周期数是性能指标；**合入 main 时**要求同一配置下 RTL 与 trace-model 整程序周期逐个相等（第 1 节第 3 条）。逐条对比不比较 store 数据和内存，访存/外设路径有改动时还要对比串口输出。
- **function-model**：提交序列与参考模型（Spike）一致。
- **位宽（XLEN）**：main 只有 rv64gc（`XLEN=64`、`FP=1`、`RVC=1`；RTL 默认配置包即此配置）。rv32 已于 2026-11-16 从 main 删除，整套保留在各仓库的分支 `rv32-legacy`，不要再在合入清单里加 rv32 门禁。
- **对 RTL 比周期时无需任何环境变量**（2026-11-19 起，见第 3.3 节）：此前模型独有的 LDQ/STQ 63 周期看门狗及 `LSU_PIPE_NOWD` 开关已删除，默认配置即 RTL 配置（见 [../trace-model/docs/ENV_VARS.md](../trace-model/docs/ENV_VARS.md)）。

## 3. 必须具备的 harness

### 3.1 trace-model

| harness | 作用 | 位置 / 命令 |
|---|---|---|
| gate | 62 个基础测试（`results/baseline/baseline.csv`）及 68 个 C 扩展测试（`results/baseline/baseline_c.csv`；当前默认 `RVC=1`），周期与基线一致 | `scripts/run_gate.sh build/simulator results/gate`、`scripts/run_gate_c.sh build/simulator results/gate_c` |
| 大程序 | dhrystone 64 次、coremark 2 次迭代、memory-stress；标准周期见 `trace-model/docs/PROJECT.md` | dhrystone/coremark 在 `rtl/programs/big`，其余在 `trace-model/build/tests` |
| Linux | rv64gc 镜像（本机 `~/rv64spec/linux_j.bin`，集群 `/nfs_global/S/houruyao/linux_ckpt_rv64gc/linux_j.bin`），从复位启动到 `rv64 login:` | `scripts/linux_check.sh <模拟器> ~/rv64spec/linux_j.bin`；合入 main 前必跑 |
| small-LLC 检查 | 默认 4 MiB LLC 在小测试里不会换出，用 64 KiB LLC 检查 DDR 写回路径 | `scripts/llc_small_check.sh` |
| 不变量检查 | 实验特性自带的每周期检查（如 `ME_CHECK=1`、`comb_graph.py --check`） | 环境变量或 `scripts/comb/comb_graph.py --check`（全部环境变量见 [../trace-model/docs/ENV_VARS.md](../trace-model/docs/ENV_VARS.md)） |

### 3.2 rtl（双测试台分工：`core_tb` vs `soc_tb`）

`rtl` 维护职责正交的两套测试台，不互相混用：
- **`tb/core/core_tb`（顶层 `soc_top` = `core_top + mem_top`）**：**核+Cache 微架构研发台**，外设走 C++ `PeripheralModel`、DDR 256b 直连 `SimDDR`，负责与 `trace-model` 逐拍周期对齐、逐条 `function-model` Difftest、SVA/覆盖率、官方 `riscv-tests`、Fuzzer 与 Linux 26 窗检查点回归；**不把片上 `soc_xbar`/外设回灌进 `core_tb` 或 `trace-model`**。
- **`tb/soc/soc_tb`（顶层 `chip_top`）**：**流片/FPGA 全片集成验证台**，仅暴露真实芯片引脚，含双层 Full-AXI4 互联（`soc_xbar` + `soc_axi_downsizer` + `soc_axi_reg_slice` + 在线 ARM IHI 0022E `soc_axi_checker`）与真实片上外设（BootROM、64 KiB SRAM、CLINT、PLIC、NS16550A UART、SysCtrl、CRG）。

| harness | 作用 |
|---|---|
| lint | `scripts/lint.sh`（按目录、规范 + `-Wall`）、`scripts/lint_chip.sh`（`soc_top` 为顶）和 `scripts/lint_soc.sh`（`chip_top` 为顶）都要 0 警告；改参数前用 `CFG=<配置包> scripts/lint_chip.sh` 预查写死的位宽（在 `iprc-jump` 上须先 `export PATH="$HOME/rv64spec/verilator_src/bin:$PATH"` 切到 Verilator 5.052） |
| 逐条对比门禁（`core_tb`） | `scripts/fm_gate.sh <core_tb> <outdir>`：`ref_cycles.txt` 里全部程序（当前 77 个）在 `core_tb` 上逐条对比 function-model，检查 SVA/断言报错与周期差；支持构建期开关 `SOC_ASSERT=1` / `SOC_SVA=1` / `SOC_XINIT_UNIQUE=1` / `SOC_COV=1\|all`（默认全关）及运行期 `SOC_TB_FM_STRICT=1`（MMIO/跨字 store + 18 架构 CSR + 特权级） |
| 全片 SoC 回归门禁（`soc_tb`） | `scripts/soc_gate.sh`（可选 `--linux`）：先清旧日志，串行执行 `lint_soc.sh` + `tb/axi_unit`（`--assert` 5 项协议与随机压测）+ `soc_tb`（`DDR_DATA_W=64` 5 项定向裸机测试：`soc_smoke`/`soc_uart_fifo`/`soc_plic_ext`/`soc_reset_boot`/`soc_boot_park` + `DDR_DATA_W=128` 冒烟），0 AXI4/SVA 错误 |
| 官方 ISA 合规（`core_tb`） | `scripts/riscv_tests_gate.sh`：RV64 官方 `riscv-tests`（`ui`/`um`/`ua`/`uf`/`ud`/`uc`/`uzba`/`uzbb`/`uzbc`/`uzbs`，跳过不支持的非对齐 `rv64ui-ma_data`，当前 152/152 PASS） |
| 随机 Fuzzer（`core_tb`） | `tools/fuzz/fuzz_run.py`（支持 `--tb` 对拍 RTL 与 `--spike-fm` 对拍 Spike）+ `minimize.py` 自动二分缩减失败用例 |
| Linux（快速窗口 + 全程） | 开发期在 `core_tb` 跑 `scripts/linux_segments_cmp.sh`（集群 26 段每 5M 指令检查点 `/nfs_global/S/houruyao/linux_ckpt_rv64gc/` 配合 `SOC_TB_MAX_INSTS` 并行比逐条检查和 PT/UP 指纹）；合入前上 `eda` 跑 8 线程静态版（`CORE_VOPT="--threads 8"`）`scripts/linux_gate.sh`；SoC 侧用 `scripts/soc_gate.sh --linux` 验真实 BootROM → OpenSBI → `Linux version` |
| 文档一致性 | 每个 RTL / SVA / 验证改动提交前，对照 diff 逐项核对 `rtl/docs/modules/<模块>.md`（清单见第 7.3 节）并运行 `python3 scripts/doc_lint.py` |
| 综合对比 | 上 `eda-04`~`10` 跑 Yosys 快速代理（`scripts/synth_depth.sh`，`SYNTH_ABC="strash;balance;map"`）或 Synopsys DC TSMC 28nm 签核（见 [SERVER.md](SERVER.md) 与 [../rtl/docs/09-synthesis-report.md](../rtl/docs/09-synthesis-report.md)） |

### 3.3 默认就对：不靠记开关和环境（2026-11-19）

同一天里三次因为"某个开关 / 环境 / 库没设对"浪费时间（模型的 LDQ/STQ 看门狗没关、链到旧的 RVC=0 function-model 库、RTL 脚本默认指向旧 rv32 程序），所以定下：

- **模型的默认配置 = RTL 配置。** 模型里只有 RTL 没有的、会改变周期的机制，删掉（不是加一个"和 RTL 比时要设"的开关）。和 RTL 比、生成参考周期、跑 SPEC，都用不带任何环境变量的默认运行。PMU 默认开（不改周期）。
- **依赖按版本和配置自己构建，不链共享产物。** trace-model 的 Makefile 和 rtl 的 `scripts/fm_lib.sh` 都从 function-model 仓库的固定版本 `FM_REV` 构建 `librefcpu`，目录名带版本和 XLEN/RVC；升级 function-model 就是两处一起改 `FM_REV`。
- **脚本的默认路径指向本仓库自己构建的东西**（rtl：`build/progs`、`build/fm-*`），不指向别的 checkout 里可能过时的产物。
- **会改参考数据的操作只有一个入口**：模型基线 `scripts/write_baseline.sh`，RTL 参考周期 `scripts/regen_refs.sh`。
- 新加开关之前先问：它的另一个取值有人每天跑吗？没有就不要加（7.6）。

### 3.4 通用要求

- **新模块或新特性要同时带 harness。** 没有测试能区分对错的行为，不算验证过。
  - **新特性要补一个短 gate 测试程序**（2026-11-15）：能稳定触发这个特性的小程序，放 rtl `programs/directed/`，rv64，在 `build.sh` 里加一项，周期进 `scripts/ref_cycles*.txt`；判据是逐条检查无不一致 + 模型与 RTL 周期相同（预测器、前端类特性再加 PT/UP 指纹，`scripts/align_check.sh`）。写好后要在**没有该特性的旧实现上确认它会失败**，否则它没有区分力。
  - **不能把 Linux 当作唯一的测试。** 同一天有两个差异（页错误的 load 把出错地址写进目的寄存器；store 的基址寄存器来自读到旧值的 load，数据写到旧地址）都只在 Linux 跑到几百万周期后的推测窗口里出现，定位用了几个小时；一个短程序几秒钟就能复现，也能让以后的改动一直回归到它。
  - 合入 main 时检查：这次改动带来的新行为，在 `programs/directed/` 里有没有对应的短程序；没有就先补，写进 `MAIN_RECORDS.md` 那一节的"验证范围"。
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
4. **在提交后的代码上复验**（不能拿实验时的结果代替；**改了模型时序的任何改动，合入前都要跑一次 Linux 启动**，`trace-model/scripts/linux_check.sh <模拟器> <镜像>`：小程序周期对比抓不到 wrong-path 一类的时序回归）：
   - trace-model：gate 全部通过（默认 `RVC=1`：`results/baseline/baseline.csv` 62/62、`baseline_c.csv` 68/68，周期等于基线），大程序，Linux 从复位启动到 `rv64 login:`；
   - rtl：`lint.sh`、`lint_chip.sh` 0 警告；`fm_gate.sh` 全部通过（以 `ref_cycles.txt` 个数为准），周期与默认配置的 trace-model 逐个相等；关键改动加跑 `SOC_SVA=1 SOC_XINIT_UNIQUE=1` + `SOC_TB_FM_STRICT=1`、`riscv_tests_gate.sh`（152/152）与 `tools/fuzz/` 冒烟；Linux（rv64）先跑 `linux_segments_cmp.sh`（26 窗 PT/UP 一致、逐条检查 0 不一致），合入前确认 `linux_gate.sh`；新特性对应的短 gate 程序已补且通过；
   - 动到位宽相关代码时再验 `XLEN=64`（第 2 节“位宽”）；
   - 原配置参数下的回归：改动若声称“原配置下不变”，用原配置包再跑一遍门禁确认周期逐个相同。
5. **性能和面积**：固定负载（第 5.2 节）+ 集群 SPEC06 INT（`jobs95.txt` 386 点，见 [SERVER.md](SERVER.md)）；受影响模块的 Yosys / DC 28nm 综合前后对比。
   - **旧配置（main）的 SPEC 数字先查记录，不要重跑**：先看 `MAIN_RECORDS.md`、`EXPLORATION.md` 与 NFS `spec06_rv64gc/tm/res_*`。记录里有同一预热方式、同一检查点的结果就直接引用；只有记录缺失，或 main 自那次记录之后周期有变化，才重跑。SPEC 一律上 `eda` 集群，用法见 [SERVER.md](SERVER.md)。
   - **SPEC 默认开 `PMU=1`**：每次跑 SPEC（quick、30 点、全量）都带 `PMU=1`，结果里要有 TMA 一级（retiring / bad-spec / frontend / backend）。PMU 不改周期，开了没有代价；没开的结果事后补不回来。性能对比表里 TMA 一级新旧差异和周期一起给。
6. **记录**：`MAIN_RECORDS.md` 一行 + “变化”一节；`LOG.md` 每个 commit 一行；`EXPLORATION.md` 对应实验的状态改成“已合入”；`TODO.md` 删除已完成项。
7. **合入**：各子仓库把分支快进合入 `main`，总仓库更新子模块指针并提交。提交作者用 `tututugege <903306512@qq.com>`。没有明确要求不推送。

### 6.1 文档整理

文档和代码一样会过时（已合入的工作还写着“未合入”、已删的开关还在文档里、命令早已跑不通），所以整理文档是合入流程的一部分，不是事后补。

- **(a) 每次合入 main，同一个提交里**检查并更新：总仓库 `README.md`、`MAIN_RECORDS.md`、`EXPLORATION.md`（对应实验的状态和索引行）、`TODO.md`（做完的删掉、新发现的补上）、`LOG.md`，以及受影响模块的文档（子仓库 README、`docs/`、rtl `docs/modules/`、`ENV_VARS.md`）里的过时说法。
- **(b) 定期全面审查四个仓库（总仓库、function-model、trace-model、rtl）的全部文档**：每月一次，另外在大改动之后（例如新的 XLEN / ISA 一步）加做一次。清单：
  1. 过时的分支、状态词（“未合入”“未提交”“待合入”“未推送”）；
  2. 已删除的宏、开关、环境变量（对照 `include/config.h` 和 `trace-model/docs/ENV_VARS.md`）；
  3. 失效的路径和链接（所有相对链接必须能打开）；
  4. 命令还能不能跑（脚本存在、参数正确、示例的程序个数和路径对得上）；
  5. 文档之间数字不一致（README、MAIN_RECORDS、EXPLORATION、TODO、LOG、子仓库文档）；
  6. 已有功能没有文档（新环境变量、新脚本、新配置参数）。
- **(c) 审查结果记在 [LOG.md](LOG.md)：每个仓库一行**（审查了什么、改了什么、没能核实的留给谁）。历史实验记录（EXPLORATION.md）只追加，只改状态列和索引里已经不对的字段，过时内容加“已过时”说明而不是改写历史。

## 7. RTL 的开发流程（文档先行）

**设计文档是 RTL 的设计说明，不是事后总结：改 RTL 之前先改文档，提交 RTL 之前再核对一遍 RTL 和文档。** 每个原子模块（trace-model 的调度单元，加上 RTL 独有的模块）在 `rtl/docs/modules/<模块>.md` 有一份文档，格式以 `rtl/docs/modules/isu.md` 为模板（10 节：职责、配置、接口、结构、一拍内数据流、关键路径与深度、与模型的差异、验证、参数开关、变更记录）。大模块里的子块（例如 LSU 的 `lp_*`、BPU 的 `ubtb` / `updq`）在所属模块的文档里讲，不单独成文档。

### 7.1 步骤

1. **定模块**：要改的是哪个原子模块（改动跨几个模块就一个个来）。
2. **先写文档**：在该模块文档里写清楚这次改什么、为什么改、对配置 / 接口 / 结构 / 一拍内数据流 / 关键路径的影响、与模型的关系。涉及模型行为变化的，先在 trace-model 里按第 4 节做实验，确认性能和周期。文档先于代码，目的是让设计在写代码之前能被讨论和纠正。
3. **按文档改 RTL**：一个提交只做一件事（第 1 节第 5 条）。
4. **验证**：`lint_chip` 0 警告；`fm_gate.sh` 全部通过，周期对同配置的模型参考逐个相等；新行为按第 3.3 节补短 gate 程序；改写组合逻辑结构（为降深度等）时，写一个"新旧并排"的随机等价测试（同一随机输入、对比全部输出；再植入一个已知错误，确认测试能抓到），测试放进 `rtl/tb/`，不要留在临时目录。
5. **提交前核对 RTL 与文档**（7.3 的清单）。
6. **文档和 RTL 在同一个提交里**；提交说明里写验证结果和"文档已核对：<模块>.md"（文档没有需要改的地方也要写"文档已核对，无需改动"）。

### 7.2 文档怎么写

- 事实来源是**当前的代码**（RTL 和模型）。每个数字（大小、位宽、个数、口号）对应一个具名常量，文档里写出常量名；不凭记忆写。
- 从旧文档带过来的说法必须重新对着代码核对；核对不了的，不写进正文，单列"未核对"。
- 用大白话，术语第一次出现时解释；代码里命名混乱、有占位或死分支的地方，如实说它是什么，不照搬混乱。占位和死代码要么删掉，要么在文档里讲清楚为什么留着。
- 与模型不一致的地方（有意的简化、没复刻的部分、模型的疑点）必须写在"与模型的差异"一节，不留隐含的差异。
- 深度数字写综合口径（单模块、`SYNTH_ABC="strash;balance;map"`，生成门代理）和日期；没量过就写"待测"。

### 7.3 提交 RTL 之前的核对清单（RTL ↔ 文档，每次改 RTL / SVA / 验证设施必查）

**铁律**：只要改动了 `rtl/` 下的模块 RTL、非侵入式 SVA（`rtl/sva/`）或验证门禁/测试平台，提交前**必须**逐项对照 `git diff` 检查对应模块文档 `rtl/docs/modules/<模块>.md`（以及 `rtl/scripts/README.md`、`rtl/docs/08-risk-register.md`）是否已同步更新，不得遗漏：

- [ ] **配置**：文档里的每个常量、大小、位宽、个数与 `ttg_cfg_pkg.sv` / 模块 pkg 一致（逐个 grep，不靠眼看）；
- [ ] **接口**：端口增删改与文档的接口表一致；
- [ ] **结构**：新增、删除、改名的文件与文档的文件表（文件、行数、职责）一致；
- [ ] **数据流**：这次改动涉及的优先级、同拍 / 寄存、flush 行为、阶段顺序，文档里的描述已更新；
- [ ] **关键路径与深度**：改了组合逻辑的模块要重新综合（一次一个，见 7.5），更新 `depth:` 和第 6 节；
- [ ] **与模型的差异**：新增或消除的差异已登记；模型的开关、配置同步（`ref_cycles` 参考文件、`make cfg` 与 `ttg_cfg_pkg.sv` 是否一致）；
- [ ] **验证与 SVA**：新增或修改的 SVA 断言/cover 点（`rtl/sva/` 或模块内断言）、定向测试、等价测试、门禁结果（周期对哪个参考文件）已写进对应模块文档第 8 节；"待补"项有没有被这次提交补掉；
- [ ] **变更记录**：第 10 节追加一行（提交号在提交后补，或写日期和主题）。

### 7.4 例外

- **紧急修 bug**可以先改 RTL，但文档必须在同一天补上，提交说明里写明"文档待补"。
- **探索分支上的原型**也适用 7.3；原型阶段允许文档写得短，但合入 `main` 之前必须补到完整，并且按 6.1 一起检查。
- 没有任何文档改动的 RTL 提交，说明里要写"文档已核对，无需改动"，不能留空。

### 7.5 综合与仿真的机器负载

Yosys / Synopsys DC 综合统一在 `eda-04` ~ `eda-10` 集群节点执行（本机未装 Yosys）。同一节点上综合与整核 Verilator 编译/仿真不要同时跑（防止 OOM）；综合一次最多 2 个并行，大模块（`lsu`、`bpu`、`front_top`、`back_top`、整芯片）一次 1 个。

### 7.6 采纳优化就删旧开关（不留旧配置）

**一个优化被采纳进 `main`，同一次改动里就把旧的做法、旧的配置、旧的开关和宏一起删掉；开关只允许存在于还没有结论的 `exp/` 分支上。** 留着旧开关等于留着一条没人测的路径：代码里多一个分支，文档里多一段说明，每次改动都要想"另一个取值会不会坏"，日积月累就是屎山。具体做法：

- 合入 main 之前，对分支里引入的每个开关问一句"另一个取值还有人用吗"：没有，就把唯一取值写死、删开关、删另一条分支、删文档里的说明（第 6 节第 1 条"只合结论"的延伸）。
- 一个常量或宏在整个仓库里只剩一种取值，就不是开关，直接删掉；`SOC_*` 一类测试台宏同理（只服务调试的除外，比如波形、`--public-flat-rw`，它们会让仿真变慢，所以必须能关）。
- 模型和 RTL 同步：模型里的开关也一样，采纳之后删；模型 default 配置随之变化，参考周期文件重新生成，并在记录里写明。
- 确实要保留的选项（例如模型和 RTL 都要支持两种取值做对照），必须有各自的回归（周期参考和门禁），并在文档的"参数与开关"一节写明为什么留、谁在测。
- 清理本身也走 7.1 的流程（先改文档、提交前核对）；只删了"只剩一种取值的分支"这类不改变综合结果的改动，可以只跑 `lint_chip`、测试台重新构建和几个小程序的冒烟，不用跑完整回归，提交说明里写明这一点。
- 门禁脚本不要用"产物文件存在"当成功的判据（构建失败时会拿到上一次的旧产物，2026-11-18 就踩过）：先删旧产物，再用构建的退出码判断。
