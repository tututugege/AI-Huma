# AI-Huma 提交日志（LOG）

记录三个仓库里**每一次 commit 做了什么**。规则见 [WORKFLOW.md](WORKFLOW.md)：

- 每次 commit 之后，在本文件最上面的"新记录"一节追加一行：日期、仓库、分支、commit、做了什么、怎么验证的、结论。
- 探索实验的 commit 也要记，分支名要写清楚，没合入 `main` 的标明"未合入"。
- 一个月或一个阶段结束后，把"新记录"整理进下面的历史表里。

## 新记录（从这里往下追加，最新的在最上面）

| 日期 | 仓库 / 分支 | commit | 做了什么 | 验证 | 结论 |
|---|---|---|---|---|---|
| 2026-11-04 | rtl `main`; trace-model `b028a20` | — | **Linux 从头启动打通 + 断开旧参考的最后联系**：核对不认识的 CSR 触发非法指令（trace-model `Idu.cpp` 与 RTL `idu_ctrl_decode.sv` 同步），OpenSBI 不再误测出 sstc，trace-model 从头启动到 `rv32 login:`（130M 提交、115M 周期），gate 62/62，RTL 64 个 gate/vm 程序逐条一致；RTL 新增检查点启动（`SOC_TB_STUB`、`tools/ckpt2image.py`）；`gen_cfg.sh` 改读 `trace-model/include/config.h`，去掉 `BASELINE_SRC` 及 `baseline/` 程序前缀，`ref_cycles.txt` 改记为 trace-model gate 基线 | RTL 从 5800 万处检查点到登录的长跑进行中 |
| 2026-11-04 | rtl `main` | — | **退役逐模块锁步体系**：删除 117 个文件（锁步/录制/回放/变异脚本、各模块 rand_trace/mutants、replay harness、selftest、refhook），只保留 lint、整核闭环、逐条提交对比、`tests/fpu`、`tests/common`、`tests/dcache`；文档改为"function-model 逐条提交一致是门禁，周期数是性能指标"（`06-equivalence-policy.md` 重写，旧文档加退役提示；风险 V-12 登记新门禁覆盖缺口） | 未重跑整核构建（只改脚本/文档/测试文件）；旧内容在标签 `legacy-reference` |
| 2026-11-04 | rtl `94608cc` / tag `legacy-reference`; trace-model `main` | — | **参考改为 function-model**：整核测试平台新增逐条提交对比（`SOC_FM=1` 构建、`SOC_TB_FM=1` 运行：提交 PC + 目的寄存器值，设备读值取 RTL，中断强制注入），gate+vm 64 个程序全部一致；trace-model 的 `mtime` 现在跟周期走（gate 62/62）。本地清掉旧参考副本 `refsim*`、`traces/` 和多余的构建目录（约 5.5 GB，可由 `scripts/refsim_setup.sh` 和旧参考源码重新生成）；依赖旧参考的逐模块锁步/录制脚本仍在仓库里，打了标签 `legacy-reference` | Linux 启动到登录提示符的确认仍在后台进行 |
| 2026-11-04 | function-model / trace-model / rtl `main` | — | 去掉 GenSimpoint 这个名字：trace-model 里的符号链接改为 `function-model`，各脚本和文档的路径同步改，function-model 的 upstream 远程删除（来源只在文档里留作溯源） | `make -n` 路径通；未重编（Linux 长跑进行中） |
| 2026-11-04 | rtl `a3f212d` / `main` | — | **参考模型退役**（用户决定）：闭环测试平台不再依赖参考模拟器源码——`tb/soc/platform/` 收进 19 个冻结的平台模型文件（SimDDR、PhysMemory、PeripheralModel 及头文件，约 300 KB），`gen_cfg.sh` 改取其中的配置，4 个额外程序移到 `programs/extra/`。记录后果：周期对 trace-model、架构值对 function-model；模块级锁步（`refsim*` 与 `traces/`）降为冻结的回归工具、不再扩展，新增行为（如 S-27）无法用它验证（风险 V-11） | `gen_cfg.sh` 重新生成配置包与原来完全一致；用收进来的文件重新构建测试平台；短程序闭环 51/51 | 重建 `refsim*` 仍需要原参考源码（AI-Huma 之外、未被任何仓库跟踪）；本地 `refsim*`、`traces/` 被 git 忽略，丢了无法重建 |
| 2026-11-04 | trace-model `42b43db` / rtl `c4d70a0` / `main` | — | **Linux 启动：ebreak 断点异常**。OpenSBI 1.2 探测 semihosting 的 `slli x0,x0,0x1f; ebreak; srai x0,x0,7` 需要一次断点异常，原来 trace-model、RTL 和原参考模型都把任何 ebreak 当作程序结束，所以 Linux 镜像在第 62,061 周期（205,443 条提交）就退出。现在与 function-model（`2191b77`）规则相同：夹在标记序列之间的 ebreak 触发 cause 3（`mepc` = `mtval` = 该 pc，`medeleg[3]` 仅非 M 态委托），其余 ebreak 仍结束仿真。trace-model：`RobBroadcastIO.breakpoint`、`Rob::comb_commit`、`Csr::comb_exception`。RTL：编译宏 `TTG_EBREAK_TRAP`（默认关闭，关闭时与参考逐位一致）、`rob_trap_ctrl`、`csr_trap_class`、规格 `rob.io`/`csr.io`、测试平台 `SOC_TB_SEMIHOST`；登记偏差 S-27。另修一个我自己引入的 bug：`env.sh` 不应默认导出 `REFSIM`（覆盖了各脚本自己的 refsim/refsim_tap 默认） | trace-model：gate 62/62；同一 Linux 镜像（运行模式）跑过原停止点，100 万条提交在第 247,399 周期，桥比对 0 不一致。RTL：lint；短程序闭环 51/51；rob/csr/back_top 锁步 3 个程序 9/9；**RTL（TTG_EBREAK_TRAP 构建）与 trace-model 在同一 Linux 镜像上逐周期一致**：第 62,061 / 107,585 / 247,399 周期的提交数 205,443 / 400,002 / 1,000,007 完全相同 | 只对照到前 100 万条提交（RTL 每秒约 4–5 千周期，完整启动要 7 小时以上）；检查点恢复是下一步 |
| 2026-11-04 | rtl / `main` | 见子模块 | 路径统一：新增 `scripts/env.sh`、`scripts/ttg_env.py`，原来 58 个文件里 245 处写死的绝对路径全部改为由仓库位置推出、可用环境变量覆盖；程序清单改写相对条目（`tests/`、`vm/`、`big/`、`tm/`、`baseline/`）；`float_test.bin` 与 dhrystone/coremark 构建脚本改用 trace-model/baremetal（重编的二进制与原来逐字节相同）；`progs.txt` 去掉已非标准的 coremark10 | 只做了小检查：`gen_cfg.sh` 重新生成配置包与原来完全一致；短程序闭环 51/51；与 trace-model 对比 5 个程序一致；所有清单条目均能解析到存在的文件。**没有重跑锁步或整套闭环** | 仅整理；参考模型源码仍在 AI-Huma 之外，由 `BASELINE_SRC` 指定 |
| 2026-11-04 | trace-model `00e02fc` / function-model `4f9fd4e` / `main` | — | **更正并修复一个验证缺口**：trace-model 的 `GenSimpoint` 子模块一直固定在 function-model `354664a`，落后 `main` 14 个提交，所以此前 gate 跑的是旧版 function-model。现在 `GenSimpoint/` 改为指向 `../function-model` 的符号链接（只有一份 function-model，所有 Makefile/脚本路径不变），并移除 `.gitmodules`；trace-model 的阶段性历史文档（`P0..P3`、`STEP_*`）归档到 `docs/history/`。function-model：`DIFFTEST.md`、`SIMPOINT_SPECINT2006.md` 移到 `docs/`，`run_bbv.sh`、`run_ckpt.sh` 移到 `scripts/`（在仓库根目录运行） | 用 function-model `b1be24a` 完整重编 trace-model 后：`run_gate.sh` 62/62；dhrystone 64 次 150,838、coremark 2 次 226,991、memory-stress 1,541,195、smc-div 8,996、smc-addi 8,866，与之前完全一致 | 无行为变化；此前"function-model 新提交已被 trace-model gate 间接验证"的说法不成立，现已用新版直接验证 |
| 2026-11-04 | 三个子仓库 `main` | function-model `b1be24a` / rtl 见子模块 | 仓库整理：删除已并入 `main` 的 31 个旧分支（rtl 26 个 `rtl/*`、function-model 3 个 `exp/*`、trace-model 2 个 `exp/*`），保留未合入的 `exp/move-elim`、`exp/move-elim-pre-rebase`；function-model 取消跟踪生成文件 `compile_commands.json`；rtl 文档改为默认直接在 `main` 上工作、不再为每个模块单开工作树；删除 trace-model 本地生成的 `build_small/` | 被删分支均 `git branch -d`（已并入才允许删）；无代码改动 | 仅整理，无行为变化 |
| 2026-11-04 | trace-model `65affb3` / function-model `2ed1eb6` / `main`（快进合入 `exp/frontdoor-ckpt`） | — | 三个仓库的 `main` 现在都是各自最新：trace-model 领先 `main` 7 个提交（front-door 检查点恢复、bridge 回退修复、PeripheralAxi 修复、SPEC 检查点回放脚本、gate 加入 load-store-aligned、上游遗留清理），function-model 领先 14 个提交（速度优化、front-door 恢复、环境变量开关等）；rtl 的 `main` 本来就是主线。分支 `exp/frontdoor-ckpt` 保留 | **trace-model**：gate 62/62；dhrystone 64 次 150,838、coremark 2 次 226,991、memory-stress 1,541,195、smc-div 8,996、smc-addi 8,866、memory-stress-small 189,128 均与标准一致；小 LLC（64 KiB）检查 4 个程序基线与新版周期相同（load-store 因基线无数字为已知失败）。**function-model**：用 `main` 版和分支版各自编译的独立运行结果，在 62 个 gate 程序上执行的指令数完全一致（4 个中断程序与 trace-model 的计数不同，但 `main` 版本身就是这个值，非本次引入）。bridge 修复（`8e5daf0`）解决了 libquantum@125M 检查点上被污染的寄存器导致的提前退出 | 满足 `main` 合入条件；rtl 与 trace-model 的模块边界逐拍对照仍未做，见 `rtl/docs/08-risk-register.md` |
| 2026-11-04 | trace-model / `exp/frontdoor-ckpt`（未合入） | `65affb3` | 清理上游遗留：`.github`、`ci`、`.codex`、`.claude`、`doc/`（原执行驱动模块设计文档）、`script/`（原 SPEC 评分/画图/回归脚本）、`baremetal/riscv-tests`、预编译基准、`.o`、`tmp.md`、`compile_commands.json`、`tree.dts`、`tools/`、vendored axi kit 的 demos 与 `*_test.cpp`；`README.md` 换成指向 `docs/PROJECT.md` 的简短版。共删 486 个文件，历史里仍可找回 | 删除的文件均无构建、脚本、测试、文档引用；`gmake -n -B` 所需的 46 个源文件/库全部存在；`run_gate.sh` 62/62 | 未合入 `main` |
| 2026-11-04 | rtl / `main` | `fb96e66` | 删除依赖已清理的 per-module 工作树的复核脚本 `extra_check.sh`、`review_front.sh`、`review_exu_int.sh`，并更新 `scripts/README.md` | 无其他文件引用它们 | — |
| 2026-11-04 | AI-Huma（总仓库）/ `main` | 文档更新 | `README.md`：补充总仓库/子模块结构与克隆方法、文档索引（含 rtl 风险登记簿）、gate 62 个与大程序固定标准、更新 rtl 当前状态和下一步、复现步骤加入 rtl；`WORKFLOW.md`：变异检查改为可选、存活变异改为登记而不要求清零 | 文档改动；README 里的数字（62 个 gate、66 个闭环程序、63 个与 trace-model 一致、rtl 约 300 个文件/3 万行）已逐项核对 | 仅文档 |
| 2026-11-04 | trace-model / `exp/frontdoor-ckpt`（未合入） | `97a8589` | gate 加入 `load-store-aligned`（原 `load-store` 在参考核里遇到未对齐 load 直接退出，基线无周期数；新程序用对齐的逐字节读取拼出同样的字）；`run_gate.sh` 的排除规则收窄为只排除 `load-store/` 目录；`PROJECT.md`：gate 62 个、大程序固定为 dhrystone 64 次 / coremark 2 次、rtl 的位置 | `run_gate.sh` 62/62 通过；基线 536 周期 / 144 条指令，trace-model 与 RTL 闭环一致 | 未合入 `main`（该分支为 front-door checkpoint 实验） |
| 2026-11-04 | function-model / `exp/frontdoor-ckpt`（未合入） | `2ed1eb6` | `ref.h`：指令上限与 BBV/检查点间隔改为环境变量（`REF_MAX_INSTS`、`REF_INTERVAL`），默认不设上限、间隔仍为 1e8 | `refcpu_api.cpp`、`exec.cpp` 语法检查无错误；未跑功能回归 | 未合入 `main`；该改动是工作区里已有的未提交内容，本次只做提交 |
| 2026-11-04 | AI-Huma（总仓库）/ `main` | 初始提交 | 新建总仓库：根目录 `.gitignore`、`README.md`、`docs/`，三个子项目 function-model / trace-model / rtl 作为 git 子模块引用（URL 暂为本地路径，发布时再改）。子模块只记录各自已提交的 commit：function-model `215140b`、trace-model `4f601ca`（均在 `exp/frontdoor-ckpt`，工作区各有未提交改动，不在本次提交里）、rtl `01e31e4`（`main`） | 无代码改动；`git submodule status` 三个子模块均解析到上述 commit | 仅建立仓库结构，不涉及 `main` 合入条件 |
| 2026-11-04 | rtl / `main` | `339adce`..`01e31e4` | rtl 从 `~/personal/tututugege-rtl` 搬到 `AI-Huma/rtl`（旧的 28 个工作树清理）；路径统一；测试程序改取自 trace-model/build；`programs/big/` 固定 dhrystone 64 次、coremark 2 次；取消跟踪 coremark/dhrystone 编译产物 | lint 290 个文件干净；闭环 66 个程序周期数与参考一致；与 trace-model 63 个 smoke 程序周期数、指令数一致；模块级 / LLC 随机 / 16 tick 锁步抽查通过 | 与 trace-model 的模块边界逐拍对照、综合检查未做，变异存活按决定不清零而改为记录，见 `rtl/docs/08-risk-register.md` |
| 2026-11-03 | function-model / `exp/frontdoor-ckpt`（未合入） | `84afef3` | 前门检查点恢复：`--restore-mem-only` 只恢复内存，`tools/ckpt2stub.py` 从检查点生成恢复程序（写定时器、UART、CSR、31 个寄存器，最后 `mret`），第一条 `mret` 之后才开始计数；`REF_STATE_DIGEST_FULL`；`tools/frontdoor_check.sh` | 与后门恢复逐点比较完整状态摘要：6 个 S/U 态检查点各 2000 万条指令、4 个 M 态检查点各 500 万条全部相同；M 态陷阱入口第一条指令处不一致（`mret` 清掉 MPP、MPIE、mepc，已知限制）；原有回归不变 | 前门恢复在 function-model 里验证通过 |
| 2026-11-03 | trace-model / `exp/ckpt-bridge-state`（未合入） | `565f059` | 检查点恢复时，把 CPU 状态和设备寄存器也写入桥使用的函数核心（`pmem_core_ctx()`）；原来只写了参考核心 `ref_cpu_ctx`，桥的核心停在复位状态，地址全错，运行变成陷阱风暴 | 6 个由 function-model 生成的 SPEC 检查点各跑 300 万条提交全部正常（IPC 1.14 到 4.25）；TB_CHECK 的分支、地址、目标比对 0 不匹配；同一检查点在旧版和提速版 function-model 上周期数相同（289,084）；gate 61/61 | function-model 加 trace-model 联合跑 SPEC 的流程跑通 |
| 2026-11-03 | function-model / `exp/fm-speed`（未合入） | `cb8f78d` | 快速路径接入 BBV、SimPoint 检查点、特殊检查点和恢复模式：预算少留一条让最后一条由 `RISCV()` 执行以保证停点状态精确；区间边界处理抽成共用的 lambda，快速路径在完成区间的 U 态分支后退出；BBV 在每个 U 态分支处写回块长度并调 `bbv_commit()`；检查点生成模式下维护最后一次存储的三个字段 | 同一二进制开关快速路径各跑一次：BBV 文件和输出逐字节相同（libquantum 5 个区间、omnetpp 33 个区间）；2 个 SimPoint 检查点和 3 个特殊检查点逐字节相同；恢复模式 3999 个块摘要相同；原有回归不变，用此库重建 trace-model gate 61/61、周期一致 | BBV 生成约 3.7 倍（omnetpp 45 s 到 12 s）；检查点生成主要时间在写 2 GiB 内存；普通模式速度不变 |
| 2026-11-03 | function-model / `exp/fm-speed`（未合入） | `af7bb1e` | 访存指令内联 TLB 命中检查（未命中才调 `va2pa`）；融合 29 对相邻指令（`LW+LW`、`SW+SW`、`ADDI+ADDI`、`LW+ADDI`、`ANDI+BEQ`、`AUIPC+JALR` 等，按真实动态频率选），融合处理分支是第一条指令的执行体、指针加一、第二条的执行体，回退位置保持精确；`REF_FAST_STATS` 增加相邻指令对统计 | 块边界摘要与原路径逐点相同（xalancbmk 92.1 万点、libquantum 36.9 万点，另有 9973 和 100003 间隔），逐指令摘要相同，trace-model 65 个测试一致，用此库重建 trace-model gate 61/61、周期一致 | 相对上一个提交 libquantum +20%、omnetpp +18%、xalancbmk +15%、紧凑循环 +8%；试过 ThinLTO、PGO、clang 23、O2 等编译选项，没有稳定收益，未采用 |
| 2026-11-03 | function-model / `exp/fm-speed`（未合入） | `bd5d957` | CSR 指令走快速路径（作为块的最后一条，调用同一个 `RV32CSR()`，之后只在 satp、特权级、mie、mip、数据访问特权变化或有中断变得可递交时退出）；入口的中断前置条件改为 `evaluate_interrupts` 的精确判断；块缓存 1024 到 16384 块 | 块边界摘要与原路径逐点相同（libquantum 11.1 万点、omnetpp 3.9 万点、xalancbmk 9200 点），逐指令摘要相同，trace-model 65 个测试一致，用此库重建 trace-model gate 61/61、周期一致 | 紧凑循环约 980 MIPS；libquantum 352 到 418 MIPS，xalancbmk 262 到 313，omnetpp 253 到 337；块重建 1.488 亿次降到 1376 万次 |
| 2026-11-03 | function-model / `exp/fm-speed`（未合入） | `b682b86` | 基本块缓存加计算跳转分发，取代逐指令译码缓存：块内连续的整数指令一次译码、入口校验一次（虚拟 PC、satp 加特权级、纪元号），块内 `goto *` 直接跳转；U 态块和区间计数按块批量；写代码页或页表页时整体失效并放弃块的剩余部分；新增调试选项 `REF_STATE_DIGEST_BLOCK`、`REF_DIGEST_LIST` | 块边界摘要与原路径逐点相同（libquantum 11.1 万点、omnetpp 3.9 万点、xalancbmk），逐指令摘要相同，trace-model 65 个测试一致，用此库重建 trace-model gate 61/61、周期一致 | 紧凑循环 939 到 950 MIPS，Spike 为 841 到 876 MIPS；libquantum 约 7.0 倍、xalancbmk 约 5.3 倍、omnetpp 约 5.8 倍；BBV 与检查点生成模式尚未接入 |
| 2026-11-03 | function-model / `exp/fm-speed`（未合入） | `be45942` | 译码缓存加快速路径：常见整数指令（运算、乘除、分支、跳转、访问 DDR 的 load/store）按译码缓存执行，其余（MMIO、缺页、CSR、原子、浮点、中断）在不改状态时回退到 `RISCV()`；缓存按虚拟 PC、(satp, 特权级)、纪元校验，写代码页或页表页时整体失效；调试选项 `REF_NO_FAST`、`REF_STATE_DIGEST`、`REF_FAST_STATS` | 开关快速路径各跑一次，每 10 万条指令比较 PC 与寄存器哈希：libquantum、xalancbmk、omnetpp 共约 5.9 万个点全部相同；trace-model 65 个测试与基线一致（含 smc-*）；用此库重建 trace-model，gate 61/61、周期一致 | 紧凑循环 636 MIPS（约 7.9 倍），libquantum 约 6.3 倍，xalancbmk 约 4.9 倍，omnetpp 约 4.8 倍；BBV 和检查点生成模式尚未接入 |
| 2026-11-03 | function-model / `exp/fm-speed`（未合入） | `58aa5b0` | 软件 TLB（页表页被写则失效）、中断和陷阱的快速判断、普通模式的精简主循环、DDR 取指快路径、冷路径不内联 | 周期数与输出摘要与基线逐项相同（4 个分页测试、7 个裸机程序、3 个 SPEC 镜像） | libquantum 22.3 s → 9.7 s，omnetpp 90 s → 38 s |
| 2026-11-03 | function-model / `exp/linux-boot`（未合入） | `d7624fa` | `linux/`：设备树 `ttg.dts`、镜像脚本 `mkimage.sh`、README；`a.out.nospike` 加入忽略 | Linux 5.15.170 约 0.12 G 条指令启动到 `rv32 login:`；SPECint2006 12 个 test 程序全部输出匹配（libquantum 仅 CRLF 差异，astar 两处相对差约 1e-4，在 1e-3 容差内） | 完成 |
| 2026-11-03 | function-model / `exp/linux-boot`（未合入） | `74d09bf` | 调试环境变量：`REF_PC_EVERY`、`REF_PC_RING`、`REF_TRAP_TRACE`/`REF_TRAP_EVERY`、`REF_UNBUF`；ebreak 退出信息带 pc | 每个阶段 `g++ -fsyntax-only` 通过，HEAD 完整构建，add、libquantum 跑通 | 仅调试用 |
| 2026-11-03 | function-model / `exp/linux-boot`（未合入） | `4bba849` | **偏离 DUT**：`mip` 写掩码去掉 MTIP（0xbbb → 0xb3b） | 原掩码下 OpenSBI 的 `csrs mip, STIP` 把合成的 MTIP 永久写入，Linux 被时钟中断淹没起不来；去掉后正常启动 | 合并前要和 DUT 核对 MTIP 是否可写 |
| 2026-11-03 | function-model / `exp/linux-boot`（未合入） | `003b268` | S 态发出 SBI 关机/复位 ecall（`a7=8` 或 SRST）时结束仿真 | libquantum 镜像在 `Power down` 后立即退出，约 23 s；裸机 add、dhrystone 仍以 ebreak 正常结束 | 完成 |
| 2026-11-03 | function-model / `exp/linux-boot`（未合入） | `2191b77` | 半主机标记序列中的 `ebreak` 触发断点异常（cause 3），M 态陷阱不委托；其他 `ebreak` 仍是退出 | OpenSBI 1.2 能越过半主机探测并打印横幅；裸机测试退出不受影响 | 完成 |
| 2026-11-03 | trace-model / `exp/move-elim`（未合入） | `60a1ee8` | `ME_CHECK=1` 额外打印每周期最大引用数 | 开启后 dhrystone、coremark10 各跑一次；gate 61/61 | 架构态最多 4 份引用（coremark 仅 15 周期），dhrystone 最多 2 份；3 位计数器够用 |
| 2026-11-03 | trace-model / `exp/move-elim`（未合入） | `7b6c42e` | `ME_CHECK=1`：每周期检查引用计数等于架构映射表项数、无物理寄存器泄漏 | gate 61 个测试 + 4 个大程序开启检查，0 次断言 | 未发现泄漏 |
| 2026-11-03 | trace-model / `exp/move-elim`（未合入） | `32175e1` | mov 消除实验（`ME_ELIM=1`，默认关）：`addi rd,rs,0` 重命名时共用源物理寄存器，不进发射队列，ROB 立即完成；提交时引用计数 | 关闭时 gate 61/61、5 个大程序周期不变；开启时提交指令数不变 | dhrystone −0.77%，coremark10 −1.15% 周期 |
| 2026-11-03 | trace-model / `main` | `502fa18` | docs：AI-Huma 三仓库布局 | 无代码改动 | — |
| 2026-11-03 | trace-model / `main` | `9ff02eb` | GenSimpoint 改为 function-model 仓库的子模块 | 从零构建，gate 61/61，5 个大程序周期与原模型一致 | 完成 |
| 2026-11-03 | function-model / `main` | `354664a` | macOS 版 SoftFloat 构建，忽略构建产物 | 随 trace-model 一起验证 | 完成 |
| 2026-11-03 | trace-model / `main` | `e53cd45`, `b23dfd1` | 并入 axi-interconnect-kit 与 GenSimpoint，导入 tests、scripts、docs、gate 基线，写 `docs/PROJECT.md` | 从零构建：gate 61/61，small-LLC 与原模型一致 | 完成 |

## 历史（按仓库，从最早到最新）

以下由 git 历史一次性生成，是各 commit 的原始标题。

### trace-model / `main`（上游 tututugege/simulator 2f31e8d 之后）

共 87 个 commit。

| 日期 | commit | 做了什么 |
|---|---|---|
| 2026-11-02 | `a74ba7d` | IssueQueue/PreIduQueue: dirty-tracked seq copies, drop redundant comb_begin copies (exact) |
| 2026-11-02 | `6a0f887` | P1b: trace bridge taps (dispatch/mispredict/commit/flush/exec) and check mode (TB_CHECK=1) |
| 2026-11-02 | `8fedc6a` | P2a: facts drive BRU/AGU/SDU/CSR write data (TB_INJECT), poison and perturb controls, boot ROM fetch, control-flow evaluation in bridge |
| 2026-11-02 | `78616f8` | P2b: bridge-native commit-time traps/interrupts (no difftest ref state), controls |
| 2026-11-02 | `8879110` | P3.1: delete ALU/MUL/DIV/FP value compute, FPU softfloat and generated FADD/FMUL (23k lines); facts mandatory, difftest off |
| 2026-11-02 | `522c60c` | P3.2: delete PRF register file, operand fields and value consumers (facts only); skip idle LLC table write payloads |
| 2026-11-02 | `348a99f` | P3.3a: ROB-commit-time functional memory writes from facts; DDR no longer writes pmem |
| 2026-11-02 | `845363d` | P3.3b/c: LLC and L1D line data deleted; instruction/PTE/LLC data from pmem; SIM_MAX_CYCLES guard |
| 2026-11-02 | `6f58162` | P3.4a: one Uop for every pipeline stage; per-stage structs are aliases, converters are identity |
| 2026-11-02 | `0d8e240` | P3.4b: shrink AXI/LLC wide data payloads |
| 2026-11-02 | `dbf2e41` | P3.5: id-indexed uops: create-once fields live in a pool, pipeline entries hold id + mutable fields |
| 2026-11-02 | `c0c1f64` | Cleanup: remove host profile and frontend stats infrastructure |
| 2026-11-02 | `488efe8` | Cleanup: strip the statistics suite (PerfCount 1404 -> 33 lines, TMA blocks, LLC/L1D/LSU counters) |
| 2026-11-02 | `d2f73ab` | Single configuration: drop small/medium/large profiles and prune dead #if branches with unifdef |
| 2026-11-02 | `454bba6` | ICache S1: remove generated bool-array kernel and pack/unpack glue; keep native comb_core (front-end/icache 7.9k -> 3.3k lines) |
| 2026-11-02 | `5d34398` | ICache S2: drop the data table; hit lines are read from pmem by (tag, index) |
| 2026-11-02 | `e0ef1df` | ICache S3: refill returns line words from pmem; drop table_write.data, dcache probe data, step line copies |
| 2026-11-02 | `e1b3c43` | AXI idle-tick skip: stop the 16x extra subsystem ticks once AXI/LLC/DDR/MMIO and the L1D fast domain are quiescent |
| 2026-11-02 | `9aec0cb` | BPU: write UpdateRequest in place, pass ReadData by reference to the NLP stage, in-place GHR/FH update |
| 2026-11-02 | `6162e2b` | PreIduQueue: sync only touched instruction-buffer slots and the allocated FTQ slot at seq |
| 2026-11-02 | `5f0ac3e` | IssueQueue: sync only dirty entry slots at seq |
| 2026-11-02 | `16a0774` | front-end: prune dead preprocessor branches (2-ahead, TAGE-SC-L, ideal icache, SRAM model) and the falcon/front stats counters |
| 2026-11-02 | `c312fb2` | front-end: remove debug logging and focus-dump code |
| 2026-11-02 | `f397569` | front-end: drop the unused simple ICache top, bit helpers and dead train_IO declarations |
| 2026-11-02 | `e99145a` | BPU: remove the disabled NLP / 2-ahead predictor state and wrappers |
| 2026-11-02 | `b6aee7b` | front-end: remove mini-flush / dummy PTAB entries and the 2-ahead outputs (always off) |
| 2026-11-02 | `d7ef9ac` | BPU: inline the history and update-queue comb wrappers |
| 2026-11-02 | `e516b98` | BPU: merge the pre-read comb and data read into bpu_data_read |
| 2026-11-02 | `321def0` | BPU: inline post-read and submodule-bind wrappers |
| 2026-11-02 | `f52df65` | BPU: inline the predict-main wrapper (all BPU top-level comb wrappers are gone) |
| 2026-11-02 | `59f6290` | front_top: build the BPU input once and inline the global-control / read-enable glue |
| 2026-11-02 | `381c5c3` | front-end: carry the prediction metadata as one PredMeta through BPU, PTAB and the front2back FIFO |
| 2026-11-02 | `f2be766` | IssueQueue: reuse scheduling scratch buffers; TLB: skip the bit-vector kernel round trip when translation is off (verified against the kernel) |
| 2026-11-02 | `b2166ae` | TraceBridge: translate virtual addresses before the RAM / undo checks (fixes paging programs) |
| 2026-11-02 | `4a0d3fb` | TLB: run the native core_comb/top_comb; remove the bit-vector kernel (TlbMmuKernel.h) and codec |
| 2026-11-02 | `5d628c0` | PTW: remove the packed compact-core kernel and the bit-vector codec (dead at runtime) |
| 2026-11-02 | `837f506` | top level: remove the dead difftest hooks, config banner and unused tick helpers |
| 2026-11-02 | `bf2f966` | back-end IO.h: replace zeroing-only constructors with default member initializers |
| 2026-11-02 | `812a286` | PredMeta templated by width: front_top_out, FrontPreIO and the FTQ train meta carry the bundle as one struct |
| 2026-11-02 | `31b2ac5` | Exu: one table-driven Fu class (single/pipelined/iterative) replaces the AbstractFU hierarchy and the per-unit classes |
| 2026-11-02 | `6cc2323` | Lsu/debug: remove RealLsuPerf, all dump_debug functions, the deadlock/diff trace infra and the TLB trace ring |
| 2026-11-02 | `0564418` | Lsu: remove the dead load/store value computations (STLF forward data, dcache load data, store-port data) and helpers |
| 2026-11-02 | `2d60f6b` | Memory subsystem: remove the dead line-data chain (store data, MSHR merged store data, fill/victim line data, write-buffer data and AXI write data) |
| 2026-11-02 | `4612b36` | Memory: instruction words and page-table entries are read from the core's memory; commit-time pmem writes and the LLC/MemSubsystem read-data payload are gone |
| 2026-11-02 | `fcde828` | ICache: no line words in the module or the AXI response; the glue reads the fetch group from the core's memory by physical address |
| 2026-11-02 | `b74a841` | pmem RAM is the core's RAM: one copy, the loader and DMA write straight into it; no unused difftest reference core in RUN mode |
| 2026-11-02 | `7842d97` | Remove the remaining functional-memory leftovers: SimDDR read/write memory, the DDR functional-write flag, the PeripheralModel/MemSubsystem RAM pointer; AXI read payload… |
| 2026-11-02 | `54d736c` | MemSubsystem: remove the unused internal AXI runtime (interconnect/DDR/router/MMIO/UART copies) |
| 2026-11-02 | `c8202b2` | AXI kit pointer: debug/perf strip |
| 2026-11-02 | `7159e64` | Update kit: AXI/LLC line-data removal |
| 2026-11-02 | `a3c7bb5` | Kit pointer: dead function deletion |
| 2026-11-02 | `0d0daeb` | Kit pointer: block emptying |
| 2026-11-02 | `8a6d78e` | Kit pointer: orphan function deletion |
| 2026-11-02 | `395c944` | Kit pointer: coverage-driven pruning done |
| 2026-11-02 | `ac1697d` | BPU: compact rewrite (TAGE/BTB/type predictor/history/RAS/queue), 4.7k -> 0.76k lines, cycle-exact |
| 2026-11-02 | `7b03801` | Lsu: compact rewrite (generic ring queues, merged phases), 1.6k -> 0.97k lines, cycle-exact; lockstep shadow hook |
| 2026-11-02 | `56db2bb` | Rob: dirty-slot sync instead of whole-array copies |
| 2026-11-02 | `907276b` | IssueQueue: maintain ready bitmap in seq |
| 2026-11-02 | `bd0ca81` | LLC table_out reset without allocator, drop zero data row |
| 2026-11-02 | `3de4d3a` | comb_begin: drop redundant working-copy copies (checked by BEGIN_SELFCHECK) |
| 2026-11-02 | `0fdb4ad` | Kit pointer: revert block emptying |
| 2026-11-03 | `9f27ae8` | back-end tidy: drop identity Uop converters and stage-specific Uop aliases |
| 2026-11-03 | `5f5948f` | BackTop::comb split into documented dependency stages |
| 2026-11-03 | `8a18a33` | back-end: Wires struct replaces per-module in/out pointer wiring |
| 2026-11-03 | `c70d962` | Rob: rewrite (761 -> 364 lines), lockstep-verified; ROB_SHADOW build hook |
| 2026-11-03 | `604fdde` | Dispatch: rewrite (712 -> 372 lines), table-driven decomposition, lockstep-verified; DIS_SHADOW hook |
| 2026-11-03 | `30961ac` | Exu: rewrite (577 -> 306 lines), lockstep-verified; EXU_SHADOW hook |
| 2026-11-03 | `be0aff5` | Isu: rewrite (525 -> 247 lines), lockstep-verified; ISU_SHADOW hook |
| 2026-11-03 | `24ab6e3` | Idu: rewrite (505 -> 302 lines), lockstep-verified; IDU_SHADOW hook |
| 2026-11-03 | `03c7bb4` | Ren: rewrite (400 -> 220 lines), lockstep-verified; REN_SHADOW hook |
| 2026-11-03 | `5705496` | Csr: rewrite (420 -> 222 lines), lockstep + random differential verified; CSR_SHADOW hook |
| 2026-11-03 | `1fd7461` | PreIduQueue: rewrite (351 -> 245 lines), lockstep + random differential verified; PRE_SHADOW hook |
| 2026-11-03 | `78189ec` | BackTop: split loaders/checkpoint into BackTopLoad.cpp, shadow hooks into ShadowHooks.h, dedupe state install, extract comb_outputs (850 -> 366 + 422 lines) |
| 2026-11-03 | `53de287` | Update axi-interconnect-kit: LLC rewrite |
| 2026-11-03 | `1cf984d` | Update axi-interconnect-kit (interconnect tidy); drop the dead read_req_drop_warned snapshot |
| 2026-11-03 | `d0d746e` | front-end: ring-buffer FIFO models, no CombIn copies, in-place read data, drop write-only deadlock snapshot and out_regs |
| 2026-11-03 | `b8550c0` | SimCpu: skip copying the all-zero front2back hold register |
| 2026-11-03 | `901b3eb` | Ren: copy only the RAT checkpoint rows written this cycle |
| 2026-11-03 | `76ee03b` | IssueQueue: skip the grant clear and scheduling when nothing is ready |
| 2026-11-03 | `53b38ce` | Isu: write enqueue slots in place instead of zeroing them every cycle |
| 2026-11-03 | `5b64663` | front_comb_calc: split the 560-line function into stages (FrontComb), drop the dead bypass/second-slot paths and the IO wrapper structs |
| 2026-11-03 | `5c22d19` | rv_simu_mmu_v2: dedupe the AXI bridges, drop the idle-verify scaffolding, empty counters and commented-out code (1020 -> 841 lines) |
| 2026-11-03 | `af95139` | Update axi-interconnect-kit (LLC comb memo, quiescence shortcut, read/write arbiter split) |
| 2026-11-03 | `b23dfd1` | Vendor axi-interconnect-kit (382cb6f) and GenSimpoint (637537f) as plain directories |
| 2026-11-03 | `e53cd45` | Import tests, scripts, docs and gate baseline from tututugege-trace; add docs/PROJECT.md |
| 2026-11-03 | `9ff02eb` | GenSimpoint is now the AI-Huma function-model repository (submodule) |
| 2026-11-03 | `502fa18` | docs: AI-Huma layout (function-model, trace-model, rtl) |

### function-model / `main`（上游 tututugege/GenSimpoint fee6fdb 之后）

共 2 个 commit。

| 日期 | commit | 做了什么 |
|---|---|---|
| 2026-11-02 | `637537f` | refcpu API: side-effect-free virtual-to-physical probe for fetch/load/store (used by the trace bridge) |
| 2026-11-03 | `354664a` | macOS SoftFloat build; ignore build products |

### rtl（`~/personal/tututugege-rtl`）/ `main`

共 67 个 commit，含各模块分支的合并。

| 日期 | commit | 做了什么 |
|---|---|---|
| 2026-11-03 | `abf7b1b` | Initial: docs (scope, RTL standard, flow, harness, mapping, tracker), trace-replay harness, svlint, cfg_pkg generator, selftest |
| 2026-11-03 | `d339482` | Recording pipeline (refsim hook + spec @expr plugins), structure rules S10-S12, common primitives, strong RTL design principles |
| 2026-11-03 | `d885e34` | docs: agent brief for per-module translation |
| 2026-11-03 | `6faeb5a` | rtl/backend: prf (green: 67 traces, mutants: 15/15) |
| 2026-11-03 | `2123c51` | hbuild: raise verilator replication limit for wide wrapper outputs |
| 2026-11-03 | `b6b6a2f` | rtl/backend: idu (green: 72 traces, mutants: 12/12) |
| 2026-11-03 | `6145c80` | iogen: tbwrap drives out_bits per element (no wide clear), review/mutcheck coordinator scripts; drop replication-limit workaround |
| 2026-11-03 | `79704a1` | rtl/backend: ren (green: 64 traces, mutants: 7/7 effective; 4 survive on uncovered paths) |
| 2026-11-03 | `c32b1a1` | docs: equivalence policy (don't mimic C++ quirks), hash excludes compare rules, package-first file ordering |
| 2026-11-03 | `a325cf9` | rtl/backend: dispatch (green: 64 traces, mutants: 14/14) |
| 2026-11-03 | `13bc3f8` | scripts: rehash trace headers after hash definition change |
| 2026-11-03 | `bc0c632` | merge main |
| 2026-11-03 | `ebd3931` | merge main |
| 2026-11-03 | `8d7e17c` | merge main |
| 2026-11-03 | `9d8c78c` | Merge branch 'main' into rtl/dispatch |
| 2026-11-03 | `f602a9b` | rtl/backend: idu simplified per 06 (green: 72 traces, mutants: 9/9) |
| 2026-11-03 | `329ee8d` | rtl/backend: prf simplified per 06 (green: 67 traces, mutants: 10/10) |
| 2026-11-03 | `44de394` | rtl/backend: dispatch simplified per 06 (green: 66 traces incl. 3 random, mutants: 16/17 valid, M9 equivalent) |
| 2026-11-03 | `7417760` | rtl/backend: ren simplified per 06 (green: 68 traces incl. 4 random, mutants: 12/12) |
| 2026-11-03 | `aaa773d` | dispatch notes: fix trace size |
| 2026-11-03 | `b84eca5` | rtl/backend: rob (green: 69 traces, mutants: 10/11) |
| 2026-11-03 | `2b4145a` | scripts: standard program set now includes vm tests and extra baremetal programs; caps from progs.txt |
| 2026-11-03 | `d7cc418` | scripts: smaller caps for extra programs, SKIP_EXISTING |
| 2026-11-03 | `c4402f1` | merge main (program set update) |
| 2026-11-03 | `8e4ca0c` | merge main (program set update) |
| 2026-11-03 | `5ae45da` | merge main (program set update) |
| 2026-11-03 | `3121a8b` | merge main (program set update) |
| 2026-11-03 | `4b788bb` | untrack .DS_Store |
| 2026-11-03 | `909e469` | merge main |
| 2026-11-03 | `62fefd6` | merge main |
| 2026-11-03 | `2c375e6` | merge main (program set update) |
| 2026-11-03 | `1754f49` | merge main |
| 2026-11-03 | `e8216be` | merge main |
| 2026-11-03 | `2d5be44` | docs: brief supplement for batch 2; svlint comparison fix; lint exemption rules |
| 2026-11-03 | `496b699` | rtl/backend: csr (green: 77 traces, mutants: 15/15) |
| 2026-11-03 | `ab197ea` | harness: when may reference an input field; lint exemption doc fix |
| 2026-11-03 | `26d3290` | rtl/backend: pre_idu_queue (green: 77 traces, mutants: 18/18) |
| 2026-11-03 | `43a0f6a` | rtl/backend: isu (green: 77 traces, mutants: 16/16 + 1 equivalent) |
| 2026-11-03 | `85dc87f` | Merge rtl/prf: prf translated to SV (green, reviewed) |
| 2026-11-03 | `321dc35` | Merge rtl/idu: idu translated to SV (green, reviewed) |
| 2026-11-03 | `eb1ba57` | Merge rtl/ren: ren translated to SV (green, reviewed) |
| 2026-11-03 | `a1c1664` | Merge rtl/dispatch: dispatch translated to SV (green, reviewed) |
| 2026-11-03 | `19b0168` | Merge rtl/rob: rob translated to SV (green, reviewed) |
| 2026-11-03 | `e6ad69a` | Merge rtl/csr: csr translated to SV (green, reviewed) |
| 2026-11-03 | `a7fa41b` | Merge rtl/pre_idu_queue: pre_idu_queue translated to SV (green, reviewed) |
| 2026-11-03 | `740fe6a` | Merge rtl/isu: isu translated to SV (green, reviewed) |
| 2026-11-03 | `28046d5` | docs: tracker (8 backend modules green), suspect list, hidden-dependency table, assertion rule; merge script |
| 2026-11-03 | `12a2669` | analysis: frontend/Exu module boundaries, front record tap patch, coverage data |
| 2026-11-03 | `668f3b2` | Merge rtl/ana: frontend and Exu boundary analysis |
| 2026-11-03 | `9fc9632` | refhook: front-end recording tap (from analysis), REFSIM_DIR override |
| 2026-11-03 | `9be57f1` | svlint: generated files exempt from size limits |
| 2026-11-03 | `97440a9` | rtl/backend: tlb_mmu (green: 79 traces, mutants: 34/34) |
| 2026-11-03 | `5354ec1` | lint.sh: lint per module directory (linear cost) instead of per file against the whole repo |
| 2026-11-03 | `4af361e` | rtl/frontend: front_basic (green: 8 modules x 73 programs + generated traces, mutants: 34/34) |
| 2026-11-03 | `483129b` | rtl/backend: exu_int FUs (alu bru agu sdu csr_fu mul div) (green: 7 specs ~76 traces each, mutants: 47/47) |
| 2026-11-03 | `6e0f83c` | rtl/backend: fpu (green: 81 traces, mutants: 33/33 non-equivalent) |
| 2026-11-03 | `5dc008c` | Merge rtl/tlb_mmu: tlb_mmu translated to SV (green, reviewed) |
| 2026-11-03 | `3537ca4` | Merge rtl/fpu: fpu translated to SV (green, reviewed) |
| 2026-11-03 | `592b44d` | Merge rtl/front_basic: front_basic translated to SV (green, reviewed) |
| 2026-11-03 | `29248af` | Merge rtl/exu_int: exu_int translated to SV (green, reviewed) |
| 2026-11-03 | `e3c5fe7` | docs: tracker (TlbMmu, FU, FPU, front basics merged), suspects S-12..S-21; record_all keeps generated traces; review scripts |
| 2026-11-03 | `6d64313` | rtl/backend: exu_ctrl (green: 77 traces, mutants: 11/11) |
| 2026-11-03 | `78693ea` | harness: live lock-step co-simulation (RTL plugin in the reference simulator, whole-program comparison) |
| 2026-11-03 | `84fd4f2` | Merge rtl/exu_ctrl: exu_ctrl translated to SV (green, reviewed) |
| 2026-11-03 | `9cb3db2` | rtl/backend: lsu (green: 85 traces, mutants: 15/25 caught) |
| 2026-11-03 | `06fea7d` | scripts: lockstep_batch |
| 2026-11-03 | `d3e825f` | Merge rtl/lsu: lsu translated to SV (green, reviewed) |


说明：trace-model 早期的补丁队列（patches 0001–0061）记在旧仓库 `~/personal/tututugege-trace` 的 `docs/` 里。
| 2026-11-03 | function-model exp/frontdoor-ckpt | ckpt2stub writes timer last (mtime skew ~tens of cycles) | function model identical 20M instr on all 6 ckpts |
| 2026-11-03 | trace-model exp/frontdoor-ckpt | `--restore-stub` front-door restore through the pipeline | 5/6 ckpts within 0.3% of back-door cycles; lq125m hits a latent timer-interrupt bug (exits at 773,834 commits; timer shifts also trigger it) |
| 2026-11-03 | trace-model exp/frontdoor-ckpt | Bridge fix: position-based rewind + kill_older_than (wrong-path stragglers kept their register writes) | gate 61/61, perf cycles unchanged; lq125m no longer Oopses (old back-door baseline 2,623,210 was corrupt; now 1,552,165); other 5 ckpts unchanged |
| 2026-11-04 | trace-model exp/frontdoor-ckpt | `bdd30dd` PeripheralAxi: uncached-RAM stores no longer written into the shared core RAM (the 0x87f00000 window clobbered newer reference stores) | gate 61/61; dhrystone 150,838 / coremark 226,991 cycles unchanged; SPEC full replay 496/496 points, 0 crashes (before: 36 segfaults) | xalancbmk IPC 2.441 -> 2.786; perlbench -0.4%, hmmer +0.07%, other 9 programs identical; SPECint2006 geomean 13.0 -> 13.2 /GHz (estimate) |
| 2026-11-04 | trace-model exp/frontdoor-ckpt | `4f601ca` scripts/spec: replay.sh quick (6 programs, 90% weight, 129 points, ~20 min) / full (496 points, ~75 min) | quick+full ran | mov elimination (exp/move-elim rebased onto this branch, not merged): quick geomean IPC 2.356 -> 2.367 (+0.46%) |
