# WIP 交接记录：`fe-2ahead` + 流程/告警/SRAM 清理（2026-11-28）

> **状态**：工作进行中（WIP checkpoint），已合并最新 `main`（`d7100bd` / `EXP-073`）并推送至独立分支（未改动任何仓库 `main`），用于跨机器无缝接续后续调试、清理与验证。

---

## 1. 仓库、分支与 Commit 索引

| 仓库 | 远端 | 分支 | Commit SHA | 基线（已合入） | 说明 |
|---|---|---|---|---|---|
| 总仓库 `AI-Huma` | `git@github.com:tututugege/AI-Huma.git` | **`exp/fe-2ahead`** | 本交接提交所在 commit | `main` `d7100bd`（EXP-073） | 绑定子模块指针 + 本交接文档（`main` 未动） |
| `trace-model` | `git@github.com:tututugege/AI-Huma-trace.git` | **`exp/fe-2ahead`** | `3a84d70fda076457e344ac968043a25f317eb569` | `main` `c988e43`（EXP-073） | Pure Single-Set 2-Ahead BPU + 64K 2 级 ICache 模型 |
| `rtl` | `git@github.com:tututugege/AI-Huma-rtl.git` | **`rtl/fe-2ahead`** | `4608ddf53a5281447e95c62a63961e4a46792257` | `main` `b753928`（EXP-073） | Pure Single-Set 2-Ahead BPU + 64K 2 级 VIPT ICache + 文档更新 |
| `function-model` | — | `exp/verify-spec386` / `main` | `c2dce72` | 未动 | — |

### 在新机器/新工作区检出命令

```bash
git clone git@github.com:tututugege/AI-Huma.git -b exp/fe-2ahead
cd AI-Huma
git submodule update --init --recursive
git -C trace-model checkout -B exp/fe-2ahead 3a84d70fda076457e344ac968043a25f317eb569
git -C rtl checkout -B rtl/fe-2ahead 4608ddf53a5281447e95c62a63961e4a46792257
```

（若本机已有 `AI-Huma`，也可直接在各仓库 `git fetch origin` 后用 `git worktree add` 检出对应分支。）

---

## 2. 当前代码内容与实测状态

### 2.1 本分支实现内容
- **Pure Single-Set Unified 2-Ahead BPU**（详见 `rtl/docs/modules/bpu.md`）：
  - 单套预测器结构：`uFTB 256`（`64×4` 紧凑 FF）+ `1× Main FTB`（`u_ftb1`，2-Bank 1RW）+ `1× 2-Way 6-Table 2-Ahead ExBlockTage` + `1× 4-Table 2-Ahead ITT` + `RAS` + `self0` A0 复用 + `uFTB FastFill` + `FE_TRAIN_LAT=1`（`T0→T1`）+ `BPU_FAST_OVR=1`。
  - 删去第二套预测器及 `bpu_ftb_tage.sv`，一并消除了 `main` 中 `bpu_ftb_ex_tage.sv` 的 `u_base` `.INIT(8'h55)`。
- **64 KiB（`256×4×64B`）Lo-32B/Hi-32B 2 级串联 VIPT ICache**（详见 `rtl/docs/modules/icache.md`）：
  - `F0 → F1` 两级流水：F0 用寄存 PC 查 ITLB 与按 `idx[0]` 分奇偶 2-Bank FF Tag/Valid 驱动严格单口 `ttg_sram_1rw #(DEPTH=1024, WIDTH=256)`（`16 × TEM5N28HPCPLVTA1024X32M4SWSO`），F1 锁存控制并切片送入 `inst_fifo`。
  - `icache_fdip` 新增 1 项回填缓冲 `fb_v`，严格解耦 `1RW` 写口；VIPT 8-bit 虚拟索引 `VA[13:6]` + 完整 20-bit 物理 PPN `PA[31:12]` 免疫别名。
  - 彻底消除 `main` `front_top` 上跨 `u_icache` ↔ `u_fetch_buf` 的 `ic_read_complete` 结构组合环（DC `OPT-150` / Yosys 44 处 `$abcloop` / Verilator `UNOPTFLAT`）。

### 2.2 合并前 PPA 与验证（基于 `6c42731`）
- **Lint & 环路**：`front_top` `verilator --lint-only -Wall`（不加 `-Wno-UNOPTFLAT`）**0 warning**；Yosys `$abcloop = 0`。
- **`eda-07` Tier 1**（TSMC 28nm LVT + PrimeTime STA，`clk = 0.65 ns`、`unc = 0.05`、`io = 0.12`、真实 SRAM 宏，`PT_LINK_STATUS = 1`）：
  - `icache`（64K 2 级）：Total `490,495.9`（Macro `213,657.9` / Logic+FF `276,838.0`，`16` 颗 `1024×32` 宏），`WNS_total = -1.24 ns` / `WNS_r2r = -1.12 ns`（`pt_timing_reg2reg = -1.18 ns`、`arrival = 1.76 ns`），`Levels = 77`、`CPL = 1.82 ns`、`Fmax_T1 = 0.529 GHz`（reg2reg `0.546 GHz`）。
  - `front_top`（64K 2 级 + 2-Ahead BPU）：Total `2,682,267.5`（**-38.7%** vs `main` `4,372,183.6`；**-32.2%** vs `fe-2ahead 32K` `3,955,776.8`），**`116` 宏**（vs `main` `436`），`WNS_total = -1.82 ns` / `WNS_r2r = -1.82 ns`、`Levels = 64`、`CPL = 2.30 ns`、`Fmax_T1 = 0.405 GHz`（`+33.2%` vs `main` `0.304 GHz`）。
  - 第一关键路径已完全退出 `u_icache`，移至 BPU：`u_pred_path.u_bpu.u_arrays.u_ftb1.u_wrb.rd_key[8] -> bk_addr[9] -> u_pred_path.u_bpu.u_arrays.u_ftb1.u_mem.g_bk[0].u_sram.g_512x72.g_t[0].u_macro/A[0]`。
- **门禁**：合并前 `fm_gate` **77/77 PASS（0 周期差）**。

### 2.3 合并 `main`（EXP-073）后复验现状
- **通过项**：
  - `trace-model`：`make -j16` 成功；`tm_cycles.sh` 77/77 行 `0 FAIL`；77 程序模型周期相对 `main` `ref_cycles.txt` 几何平均 `+0.27%`（`coremark` `280,555 → 282,510`、`dhrystone` `102,117 → 102,150`）。SPEC06 386 尚未运行。
  - `rtl`：`gen_cfg.sh` `180` 常量（仅 ICache 3 项差异）；`svlint.py` 0 错；`lint.sh rtl/frontend/bpu`（19 files）、`lint.sh rtl/frontend/front_top`（3 files）、`lint_chip.sh` 均 0 告警/错；`front_top` 不加 `-Wno-UNOPTFLAT` `-Wall` 0 告警；`core_tb`（`SOC_FM=1`）构建与运行通过。
- **待定位的回退项**：
  - **`fm_gate` 77/77 功能全部 PASS（0 FM diff），但 `cycles different from ref_cycles.txt: 44`**。

---

## 3. 44/77 周期分歧调试线索（第一优先级）

截至交接时已确认的精准现场：

1. **`first_diff.sh add.bin`**（显式传分支模型 `trace-model/build/simulator` 不可混用，已用 `trace-model-fe-2ahead` 复核）：
   - 首个周期分歧发生在 commit #62（`tm cyc=1783` vs `rtl cyc=1782` @ `pc=80000078`）：循环第 2 次迭代时 `beq@0x60` 重定向一致，随后 **`beq@0x78` 在 RTL 中被预测跳转（0 空泡），而模型仍预测不跳（~11–12 拍误预测空泡）**；合并前模型与 RTL 在此处均为误预测。
2. **`align_check.sh add.bin`**（`DRILL=1 BIN=16 MAXCYC=3000`）：
   - **`UP` 流**：从一开始 `cyc` 即差 1 拍（正常常量偏移：`UP cyc=1634` vs `1635` @ `pc=80000060`，`1650/1651` @ `pc=80000078`，`1667/1668` @ `pc=80000090` `idx=0080000084 tag=00000006`）。
   - **`PT` 流首个分叉（cycles 1664..1679，`bin 104`）**：
     - **`cyc=1678 base=80000084`**：TM 输出 `next=800000a4 dir=0000`；**RTL 输出 `next=8000009c dir=0040`**（随后 `cyc=1679 base=8000009c next=800000bc dir=0000`）。
     - 同样发生在 `cyc=1694 base=80000084`（RTL 命中 `next=8000009c dir=0040`）。
3. **已排除**：`main` `c988e43` 对 `BpuFtb.h::update_tab` 的改动（实测回退该处后 TM 周期不变）。
4. **排查方向**：对照 `cyc 1630..1680` 的 RTL BPU 波形（`build_soc_vcd.sh`）与模型调试打印，查清 EXP-073 提交/重定向时序改动（如 `core_top`/`back_top`/`ftq` 对 BPU 更新或 S0/S1/S2 修复/FastFill 的时机）为何使 RTL 的 `u_ftb0` / `u_ftb1` 比模型早生效或命中 `0x80000084` 块。

---

## 4. 已批准的「干净版本」后续行动清单

按顺序执行（每项独立提交，未完成并核实不合入 `main`）：

### A. 修合并后 44/77 周期分歧（阻塞项）
- 利用第 3 节线索对齐 RTL 与模型至 `fm_gate 77/77` 0 周期差。
- 顺手加固 `rtl/scripts/first_diff.sh`：若未显式传入 `TM`（或指向与当前 RTL 不匹配的模型），报错退出而不再静默退回 `main` 模型。

### B. 解决 SRAM 上电初值依赖（`-DSYNTHESIS` 周期差根因 & 硅片风险修复）
- **根因**：设计依赖 SRAM 上电初值；普通仿真走 `initial`、`-DSYNTHESIS` 由 Verilator 置 0、真实芯片随机上电，三者不一致。仅靠 XOR 编码不能解决真实硅片问题。
- **审计发现的严重隐患**：`rtl/rtl/memsys/axi_llc/axi_llc_tables.sv` 将 `LLC_VALID`、`LLC_DIRTY`、`LLC_PF`、`LLC_REPL` 存在 `ttg_sram_1r1w` 中且**无复位清零扫描**；硅片随机上电会产生假命中与脏行乱写回 DDR，是真实功能 bug。
- **方案**：
  1. 在 `ttg_sram_1rw` / `ttg_sram_1r1w` 增加可选 `INIT_SWEEP` 状态机，复位释放后按 `INIT_VAL` 顺序清零整张表，汇总 `init_done` 后再释放核复位（约 4K 拍；测试台从 `init_done` 起计周期，模型周期不变）。
  2. 移除包装内的 `` `ifndef SYNTHESIS `` `initial` 阵列赋值，使仿真行为与硅片一致。
  3. 补齐新门禁：`-DSYNTHESIS` + `SOC_XINIT_UNIQUE=1`（随机上电）跑 `fm_gate 77/77` 0 周期差（先确认现况可复现失败，再修通）。

### C. 清零后端 `UNOPTFLAT` 与 `main` `lint.sh` 告警
- **`ren_elim_sel.sv`（4 条）**：`split_var` 因动态索引失效，改用每级独立 generate 作用域信号（`g_jump[s].*_o`）并裁剪末级未用输出（原型已通过 200 万次随机新旧对拍 0 差，且 `^→~^` 变异抓出 `169,957` 错）。同时修复已编译不过的 `tests/ren_elim_sel/run.sh`。
- **`isu_iq_select.sv` / `isu_iq.sv`（1 条，开 `split_var` 后暴露跨 `g_iq[1/4/5]` 共 11 条）**：拆解跨端口信号聚合为无数组粒度反馈的分层信号，用等价测试 + Tier 1（`$abcloop=0`）验证。
- 全部清零后，从 `lint_chip.sh`、`lint_soc.sh`、`lint.sh` 及 `tb/*/build.sh` 移除 `-Wno-UNOPTFLAT`。
- 修掉 `main` 上 `lint.sh` 失败项：`back_top_glue.sv` 3 处超 120 列折行、`exu.sv` 补 `// Ref:` 头，并解决 `back_top.sv`（802 行）/ `exu.sv`（491 行）超 400 行告警（拆分或明确生成文件豁免规则）。

### D. `fe-2ahead` 清理与全量验证
- 删除 `trace-model-fe-2ahead` 中 20 个 `FE_*` 运行时实验开关并更新 `trace-model/docs/ENV_VARS.md`。
- 用 `write_baseline.sh` 与 `regen_refs.sh` 重生成正式基线（消除 `/tmp` 临时参考表）。
- 本地全过：`62+62+68`、Linux 到 `login:`、`comb_graph --check`、`fm_gate`（常规 + `-DSYNTHESIS SOC_XINIT_UNIQUE=1` + strict/SVA）、`riscv_tests_gate` 152/152、fuzz 冒烟、`soc_gate`。
- 集群（`eda`）：SPEC06 386 点（`PMU=1`，核实 IPC 损益）、8 线程 `core_tb` Linux 26 窗、`soc_gate --linux`，以及 **统一 SDC（`clk=0.65 ns`、真实 SRAM、`unc=0.05`、`io=0.12`）** 下的 `front_top`/`back_top`/`mem_top` Tier 1 与 Tier 2a/3 PPA 实测对比。

### E. 文档与流程规范化
- `docs/WORKFLOW.md`：补入「§8 时序开发流程」（统一 SDC、`L0–L3` 分级与合入门槛）、SRAM 初值规则，禁止 `-Wno-UNOPTFLAT` 且要求全量 `lint.sh` exit 0。
- `docs/TIMING.md`：建立统一口径的时序计分板，回填 EXP-072 `isu_new`（`-0.22 ns`、`area 452,162`）与 EXP-073 NFS 上遗漏的 Tier 1 数据。
- 修正 `.agents/skills/ai-huma-rtl-dev/SKILL.md` 中过时甚至错误的 `tb/soc/build.sh` `SOC_FM` 命令（应为 `tb/core/build.sh` `core_tb`）与 `synth_depth` 口径；修正 `docs/GUIDE.md` 失效的「09 报告第 9 节」链接；升级 `scripts/doc_lint.py` 检查规则；清理 `docs/TODO.md`；合入前撰写 `EXP-074`。
