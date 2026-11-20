---
name: ai-huma-rtl-dev
description: >-
  Use this skill when creating or modifying SystemVerilog modules in rtl/, syncing ttg_cfg_pkg.sv,
  writing RTL equivalence tests or directed tests, running lint/fm_gate/Yosys depth synthesis,
  or completing the WORKFLOW 7.3 RTL-to-Doc checklist.
---

# AI-Huma RTL 开发流程（文档先行）

对应 [docs/WORKFLOW.md](../../../docs/WORKFLOW.md) 第 3.2、3.4 与第 7 节。

## 1. 文档先行（改 RTL 前必做）

1. **定模块**：明确本次改动属于哪个原子模块（跨多个模块时逐个拆分，一个 commit 只做一件事）。
2. **先改设计文档**：打开 `rtl/docs/modules/<模块>.md`（模板参照 `rtl/docs/modules/isu.md` 的 10 节结构），写清本次改什么、为什么改，以及对配置、接口、结构、一拍内数据流、关键路径和与模型差异的影响。
   - 涉及模型行为/周期变化的，必须先走 `ai-huma-exp` 在 `trace-model` 完成量化。
   - 文档中的每个数字必须对应具名常量（`ttg_cfg_pkg.sv` 或模块 pkg），禁止凭记忆写。

## 2. 配置同步与编码

- 核参数修改自 `trace-model/include/config.h`，RTL 侧通过 `make cfg` 重新生成 `ttg_cfg_pkg.sv`，禁止手写。
- 遵守 `rtl/docs/01-rtl-coding-standard.md` 编码规范；写死的位宽/维度应改成从配置包推导（与改参数分开提交）。

## 3. 验证与门禁

按顺序执行（本机 `iprc-jump` 做 lint、短构建与小门禁，跑任何 Verilator 命令前**必须**先 `export PATH="$HOME/rv64spec/verilator_src/bin:$PATH"` 切到 5.052；长跑 Linux 窗口和 Yosys/DC 综合上 `eda` 集群，见 `ai-huma-eda`）：

1. **Lint（0 警告）**：
   ```bash
   export PATH="$HOME/rv64spec/verilator_src/bin:$PATH"
   cd rtl && bash scripts/lint.sh && bash scripts/lint_chip.sh
   ```
   改参数前先用 `CFG=<配置包> bash scripts/lint_chip.sh` 预查写死位宽。
2. **整核逐条对比门禁**：
   ```bash
   export PATH="$HOME/rv64spec/verilator_src/bin:$PATH"
   SOC_FM=1 SOC_OUT=$PWD/build/soc_fm bash tb/soc/build.sh
   bash scripts/fm_gate.sh $PWD/build/soc_fm/obj/soc_tb $PWD/build/gate
   ```
   要求：全部程序逐条对比 `function-model` 0 不一致，周期与同配置 `ref_cycles.txt` 0 处不同（访存/外设改动同时核对串口输出）。
3. **新增特性 / 改写组合逻辑的专项测试**：
   - **新特性短测试**：在 `rtl/programs/directed/` 补一个 rv64 短程序，接入 `build.sh` 与 `ref_cycles*.txt`，并**确认它在没有该特性的旧实现上会失败**。
   - **组合逻辑降深度改写**：在 `rtl/tb/` 编写“新旧并排”随机等价测试（同随机输入比全部输出），并**植入一个已知 bug 验证测试能抓到**，不要留在 `/tmp`。
4. **Linux 检查点窗口快速对齐**（行为改动后必跑）：
   - 使用 `rtl/scripts/linux_segments_cmp.sh` 对比逐条检查与 PT/UP 指纹（全量 27 窗建议静态打包后上 `eda` 集群并行跑）。
   - 若出现分叉，结合 `FPR=<bin>`、`FPR_DUMP`、`drill_pmu.sh` 和 `SOC_TB_VCD=<起>:<止>:<文件>` + `scripts/vcd_query.py` 定位。
5. **Yosys / DC 面积与深度综合**（在 `eda-04` ~ `eda-10` 执行，本机未装 Yosys）：
   - **防 OOM 红线**：严禁与 Verilator 编译/仿真同时跑；综合最多 2 个并行，大模块（`lsu`、`bpu`、`front_top`、`back_top`、整芯片）一次 1 个。
   - 改了组合逻辑必须重跑 `scripts/synth_depth.sh`（带 `SYNTH_ABC="strash;balance;map"`，大存储模块加 `SYNTH_NO_MEMPRIO=1`）/ `scripts/synth_cfg.sh`，更新模块文档 `depth:` 行与第 6 节。

## 4. 提交前核对清单（`WORKFLOW.md` §7.3）

对照 `git diff` 逐项确认，并与 RTL 放在**同一个提交**中（提交说明必须写明验证结果及“文档已核对：`<模块>.md`”或“文档已核对，无需改动”）：
- [ ] **配置**：文档常量、位宽、大小与 `ttg_cfg_pkg.sv` / 模块 pkg 一致（grep 核对）。
- [ ] **接口**：端口增删改与文档接口表一致。
- [ ] **结构**：文件增删改名与文件表一致。
- [ ] **数据流**：优先级、同拍/寄存、flush 行为、阶段顺序已更新。
- [ ] **关键路径与深度**：组合逻辑改动已重测综合并更新深度数据。
- [ ] **与模型的差异**：新增/消除的差异已登记，配置包与模型同步。
- [ ] **验证**：门禁、定向测试、等价测试结果已写入第 8 节。
- [ ] **变更记录**：第 10 节已追加记录。
