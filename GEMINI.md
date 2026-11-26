# AI-Huma 项目开发规则

AI-Huma 是一个乱序 RISC-V（`rv64gc` + `Sv39`）CPU 设计项目，由总仓库和三个 git 子模块组成：
- `function-model/`（`librefcpu`）：功能模型，定义架构正确性及 SPEC 检查点生成。
- `trace-model/`：周期精确 C++ 时序模型与架构探索平台；`include/config.h` 是核参数的唯一来源。
- `rtl/`：SystemVerilog 实现与 Verilator 整核测试平台。

**权威流程文档**：任何开发、实验、验证、合入或集群操作前，必须遵循 [docs/WORKFLOW.md](docs/WORKFLOW.md)、[docs/SERVER.md](docs/SERVER.md) 与 [docs/GUIDE.md](docs/GUIDE.md)。本文件仅保留每轮对话必须遵守的红线与导航；具体操作请按需激活 `.agents/skills/` 中的对应 Skill。

## 1. 分支、提交与对齐红线

- **`main` 只放三仓对齐且已验证的内容**：`rtl` 架构行为逐条对齐 `function-model`，同配置下周期与 `trace-model` 逐程序完全相等。
- **探索实验一律放分支或独立 worktree**：分支名 `exp/<名字>`（RTL 模块用 `rtl/<模块>`），并行实验用 `git worktree add ../<repo>-<名字>`。
- **未经用户明确要求，禁止 `git commit` 和 `git push`**。提交作者统一为 `tututugege <903306512@qq.com>`，每个 commit 只做一件事，附带实测验证结果（禁止写“应该没问题”）。
- **`main` 仅维护 `rv64gc`**（`XLEN=64`、`FP=1`、`RVC=1`）；`rv32` 已归档在 `rv32-legacy` 分支，不要在 `main` 上新增 `rv32` 门禁。

## 2. 计算资源分工（当前开发机 `iprc-jump` vs `eda` 集群）

- **当前开发机（`iprc-jump`，9950X3D，16C/32T，60 GiB RAM）**：日常代码编辑、阅读、短编译/快速构建、轻量调试、`lint.sh` / `lint_chip.sh`、小规模 gate（`run_gate.sh` / `run_gate_c.sh` / `fm_gate.sh`）以及给 `eda` 静态打包。
  - 跑任何 Verilator 命令前**必须**显式切换 Verilator 5.052：`export PATH="$HOME/rv64spec/verilator_src/bin:$PATH"`（系统 `/usr/bin/verilator` 是 5.020，编不过）。
  - 给 `eda` 集群编译二进制时须改为 `-march=x86-64-v3 -mtune=generic` 并静态链接（`-static`），避免 AMD Zen 5 / Ubuntu glibc 与 `eda` 不兼容。
  - 给 `eda` 集群编译长跑 RTL/Linux 用的 `core_tb`（原 `soc_tb`，核+存储子系统测试台）时**必须默认开 8 线程**（`CORE_VOPT="--threads 8" CORE_COPT="-O2 -march=x86-64-v3 -mtune=generic"`，静态链接多线程需带 `-Wl,--whole-archive -lpthread -Wl,--no-whole-archive -latomic`），严禁编单线程版上集群跑 Linux 26 窗。`rtl` 双测试台分工：`tb/core/core_tb`（`soc_top`）专职微架构与三仓逐拍对齐，`tb/soc/soc_tb`（`chip_top`）专职流片向全片 SoC 与真实 AXI4/外设验证（详见 [docs/WORKFLOW.md](docs/WORKFLOW.md) §3.2）。
- **`eda` 计算集群（`eda-04` ~ `eda-10`，经 `login-inband` 免密直连，挂载 `/nfs_global`）**：**所有大规模测试与综合必须上 `eda` 集群**——包括 SPEC06（386 / 535 点）、多配置 DSE、长时间 RTL/Linux 仿真（`linux_segments_cmp.sh` / `linux_gate.sh`）以及 Yosys / Synopsys DC 综合（本机未装 Yosys）。
- **严禁在 `login-inband` 跑重任务**（仅作中转与 NFS 管理）；**严禁同时跑 Yosys 综合与 Verilator 编译/仿真**（防止 OOM），综合最多 2 个并行，大模块（`lsu`、`bpu`、`front_top`、`back_top`、整芯片）一次只能跑 1 个。

## 3. 配置、开关与文档铁律

- **默认就对（`WORKFLOW.md` §3.3）**：`trace-model` 默认配置必须等于 RTL 配置；不靠记忆环境变量来对齐周期；修改参考数据的唯一入口为 `scripts/write_baseline.sh`（模型）和 `scripts/regen_refs.sh`（RTL）。
- **采纳即删旧开关（`WORKFLOW.md` §7.6）**：优化合入 `main` 时，同批删除旧配置、旧开关和死分支；实验开关只允许留在 `exp/` 分支。
- **参数唯一来源**：核参数只改 `trace-model/include/config.h`，RTL 的 `ttg_cfg_pkg.sv` 必须由 `make cfg` 生成，禁止手写。
- **RTL 文档先行（`WORKFLOW.md` §7）**：改 RTL 前先更新 `rtl/docs/modules/<模块>.md`，提交前逐项核对 §7.3 清单。
- **每类信息只记在一处（`GUIDE.md` §3）**：
  - 规则/流程 → `docs/WORKFLOW.md`
  - 待办事项 → `docs/TODO.md`（唯一待办清单）
  - 实验探索（含负面结果）→ `docs/EXPLORATION.md`（编号 `EXP-xxx`）
  - 合入 `main` 的权威性能/面积 → `docs/MAIN_RECORDS.md`
  - 提交流水 → `docs/LOG.md`（每 commit 一行）
- **门禁不以“产物文件存在”判成功**：先删旧产物，再以命令退出码判断。

## 4. 项目专用 Skills（按需加载）

遇到以下任务时，先加载 `.agents/skills/` 中对应的 Skill：
- `ai-huma-eda`：直连 `login-inband` / `eda` 集群、从本机（`iprc-jump`）跨机静态编译、提交 SPEC06、长跑 RTL/Linux 或 Yosys/DC 综合任务。
- `ai-huma-exp`：在 `trace-model` 上做架构/性能探索、调度检查与撰写 `EXPLORATION.md`。
- `ai-huma-rtl-dev`：按文档先行流程开发/修改 RTL、写等价测试、跑 lint / `fm_gate` / Yosys 深度综合。
- `ai-huma-merge-main`：将实验结论同步并合入三仓 `main`，更新基线、参考周期与全套文档。
