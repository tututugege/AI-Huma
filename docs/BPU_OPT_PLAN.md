# AI-Huma BPU 与前端微架构优化路线图（按块 FTB → 2-ahead → 2-fetch → 2-taken）

**创建日期**：2026-11-20（2026-11-21 更新：里程碑 A 模型探索 `EXP-050` 已完成）  
**起点基线**：`trace-model` `6df4312` / `rtl` `1913518`（已合入 EXP-045/046/048：L1 硬件 Berti + LLC BOP + MSHR 16/16，SPEC06 386 点估算 **12.11 分/GHz**）  
**当前进展**：里程碑 A（Phase 1 块级 FTB + Phase 2 1-ahead/2-ahead）已在 `trace-model-ftb`（`exp/ftb-bpu`）完成全量 SPEC06 INT 验证，零组合旁路实测 **+8.48%（`13.14 分/GHz`，`ah1_4k_a2k1k`）** / **+8.17%（`13.10 分/GHz`，`ah2_4k_a2k1k`）** / **+6.85%（`12.94 分/GHz`，174 KB 轻量档）**，详数据见 [EXPLORATION.md](EXPLORATION.md#exp-050-块级-ftb--1-ahead2-ahead-bpu里程碑-a-模型探索)；下一步进入里程碑 A 的 RTL 实现与 DC 综合。  
**最终目标**：将 AI-Huma 前端从遗留的“16-bank 逐指令槽预测”升级为现代高性能核的**按块预测（FTB）+ S1 主力/S2 兜底 + 2-ahead + 2-fetch + 2-taken** 体系，同时大幅压低 BPU 面积与组合逻辑深度（解决 `docs/TODO.md` 中 `bpu` 134 层超标问题），在 8 宽后端上释放完整前端带宽。

---

## 0. 现状诊断：为什么必须先重构为“按块预测”

当前 `main` 的前端存在三类结构性瓶颈（详见 `docs/EXPLORATION.md`、`trace-model` `origin/exp/fe2t:docs/experiments/exp049_fe2t.md`、`rtl/docs/modules/bpu.md`）：

1. **16-bank 逐槽预测过度冗余（面积与时序包袱）**：
   - `RVC=1` 下 32B 取指块有 16 个 2B 槽，现行 BPU 将 **Type（~30 KB）+ BTB（~155 KB）+ TAGE（~110 KB）+ ITT（~29 KB）** 整套复制了 **16 份**，总存储约 **325 KB**。
   - 每拍 16 个 bank 并行读出几千 bit 锁进 `r1_raw_q`，S2 的 `bpu_main_sel` 做 16 路选路（~70 层逻辑、8.7 万门）；整个 `bpu` 综合高达 **55 万门 / 134 层**，单模块 Yosys 综合耗时长达 51 分钟。
   - 实际每个 32B 块平均只有 1–2 条分支，超过 85% 的读口与选路逻辑每拍在空转；且 PTAB / 后端检查点被迫按 16 槽透传元数据。
2. **BPU 覆盖气泡是当前头号前端瓶颈（7–27% 前端槽位损失）**：
   - 由于 16-bank 主预测器太重只能放在 S2，S0 只有 128 项 uBTB、S1 只有 512 项 L1 uBTB（且无分支历史）。
   - S1/S2 覆盖次数是分支误预测的 10–40 倍（覆盖零气泡上界在 24 个前端受限点上为 **+7.70%**）。
   - 在气泡未消除之前，单独打开 2-taken（`FE_PAIR=1` / `17`）收益仅 **+0.47% ~ +0.89%**。
3. **跨行截断（8.4%）与短基本块截断（28.8%）**：
   - 现行前端受限于 64B cache line 边界与单拍 1-taken，在气泡消除后会成为喂满 8 宽后端的下一阶段瓶颈。
   - 尤其是 EXP-048 合入后访存停顿大幅下降，前端在全量 SPEC06 中的瓶颈占比进一步升高。

---

## 1. 四阶段总体路线图

遵循 `docs/WORKFLOW.md`：每一阶段先在 `trace-model` 独立分支/worktree 实现（开关默认关闭，零回归），在 `eda` 集群完成 24 前端点 → 386 全量 SPEC06 量化与 Linux 启动验证；确认架构收益与硬件代价后再按 `WORKFLOW.md` §7 落 RTL，并用 `eda` 集群 **Synopsys DC（TSMC 28nm HPC+）** 与 Yosys 核实真实面积、WNS 与组合深度。

```text
Phase 1 (当前): 按块预测重构（FTB + S1 主力预测 / S2 2-slot TAGE & ITT 兜底）
    │  收益：存储降 3–4×，bpu 面积/深度大幅下降，S1 拦住 80%+ 覆盖气泡
    ▼
Phase 2: 2-ahead / 1-ahead 超前预测（彻底消除稳态覆盖气泡）
    │  收益：逼近 +7% 覆盖零气泡上界，摆脱同拍覆盖重发的组合环路压力
    ▼
Phase 3: 2-fetch（I-Cache 跨 64B 行边界偶/奇双 bank → 任意双地址双块取指 + FTQ 解耦）
    │  收益：消除 8.4% 行尾截断，并为 2-taken 提供双块 I-Cache 供给能力
    ▼
Phase 4: 2-taken（单拍双跳转 / 超级块预测，喂满 8 宽后端）
       收益：在 0 气泡 + 双块供给前提下打破短基本块 4–6 条/拍上限
```

---

## 2. 各阶段详细设计

### Phase 1：按块预测重构（FTB + S1 主力预测 + S2 兜底）

- **实验分支 / worktree**：`trace-model` `exp/ftb-bpu`（worktree `trace-model-ftb/`），开关 `BPU_FTB=1`（默认 0，周期与 `main` 逐个相同）。
- **核心架构（单拍 1 块、先保持不跨 64B 行，零侵入现有 I-Cache / Predecode / FTQ）**：
  - **FTB 表项结构（每块最多 `FTB_SLOTS=2` 个分支槽）**：
    - 以取指块起点 `base_pc` 索引；每项记录 `valid`、`tag`、替换状态，以及按偏移升序排列的最多 2 个分支槽位 `{valid, offset(4b), is_rvc(1b), type(3b), ctr(2b), target}`。
    - 彻底取消独立的 16-bank **Type 表** 与 16-bank **BTB**。
  - **三级流水职责**：
    - **S0（0 气泡快路径）**：**uFTB**（默认 256 项 × 4 路，支持目标压缩 20b 扫参），当拍给出快猜 `g0` 与下一拍 PC；同时用 `base_pc` 与折叠历史算一次块级索引，送入 S1/S2 SRAM。
    - **S1（主力预测级，1 拍出强预测）**：
      - **主 FTB**（默认 2048 项 × 4 路，扫参 2K/4K，全宽目标）读出该块最多 2 个分支槽位与目标；
      - **S1 2-slot 快速方向预测器**（`FTB_S1_DIR` 可配：0=仅 FTB bimodal，1=2 表短中历史 mini-TAGE，2=4 表 mini-TAGE）给出这 2 个槽位的带历史方向；
      - 仅需 **2 槽选第 1 个 taken**（几层门）产出 `g1`，与 `g0` 比对，不一致立即 **S1 覆盖**（默认 1 气泡，同时提供 `FTB_OVR_FAST` 评估 S1 同拍重发 0 气泡收益）。
    - **S2（高精度兜底级）**：
      - **Block-TAGE（2 槽共用，不再复制 16 份）**：默认 `Base 2048×2` + `4 张标签表 × 2048×2`（约 26 KB，比现行 110 KB 缩小 **4×**；可扫 1024/2048/4096 及 6 张长历史表）；
      - **Single Block-ITT（单套 3 表 × 256 项，~7 KB，比现行 29 KB 缩小 4×）**：只服务块尾的间接跳转（`BR_IDIRECT`/`BR_ICALL`）；
      - **RAS**：复用现有只追加投机队列 `RasQ` + 提交栈 `RasC`；
      - 仅在长历史大 TAGE 推翻 S1 方向或 ITT 修正多态 `jalr` 目标时触发 **S2 兜底覆盖**。
  - **训练路径（按块提交更新）**：
    - 复用并升级提交序块跟踪器 `ftb_track`，每块结束时生成块级训练事件更新 uFTB / Main FTB，并按块内分支槽位精确更新 S1 mini-TAGE、S2 Block-TAGE 与单套 Block-ITT（后续落 RTL 时将大幅缓解 EXP-028 的 `bpu_updq` 提交带宽瓶颈）。
    - 预译码报错（`pd.nb_valid`，预测跳但非分支）直接清除 FTB / uFTB 中对应分支槽。
- **预期硬件收益**：总存储 **~325 KB → ~75–100 KB**（缩减 3–4×），S2 选路从 16 槽压到 2 槽，RTL 落地后目标将 `bpu` 从 **134 层压回 100 层以内**。
- **Phase 1 验收标准**：
  1. `BPU_FTB=0`：`run_gate.sh` 62/62、`run_gate_c.sh` 68/68 与基线周期 0 差异；`comb_graph.py --check` 0 隐患；
  2. `BPU_FTB=1`：全量 gate difftest Success 0 不一致；rv64gc Linux（`~/rv64spec/linux_j.bin`）从复位启动到 `rv64 login:` PASS；
  3. `eda` 集群：24 前端点扫参（FTB 容量、S1 mini-TAGE、Block-TAGE 容量/表数、S1 覆盖模式）→ 优选配置跑全量 **386 点 SPEC06（`PMU=1`）**，对比当前最新 `main`（EXP-048 基线）。

---

### Phase 2：2-ahead / 1-ahead 超前预测（彻底消灭稳态覆盖气泡）

- **前置依赖**：Phase 1 的块粒度 FTB + 2-slot TAGE 已就位（状态紧凑、单块索引，避免 16-bank 下的爆炸复杂度）。
- **设计要点**：
  - 结合 Phase 1 落地后 Synopsys DC 28nm 时序结果决定提前步数：
    - 若主 FTB + 2-slot TAGE 在 S1 末可完成读出并选出结果（总延迟 1 拍）→ 采用 **1-ahead**（用前 1 块 `base_pc` + 滞后 1 块历史索引；此前 `a1pc` 上界实测 **+7.15%**，仅比理想上界低 0.55pp）；
    - 若大 TAGE 仍需 S1 读 + S2 选（总延迟 2 拍）→ 采用 **2-ahead**（用前 2 块 `base_pc` + 滞后 2 块历史索引，或采用香山/EV8 式候选路径选择；此前 `a2` 滞后上界 **+5.75%**）。
  - **冷启动兜底**：后端误预测或预译码重定向后的前 1–2 拍无前序块，由 S0 uFTB 兜底，第 2–3 拍切回 ahead 零气泡稳态流。
  - **训练队列**：FTQ / 训练记录额外保存“发起 ahead 查询时的前驱块 PC 与历史”，确保训练索引与预测索引严格对齐。

---

### Phase 3：2-fetch（I-Cache 跨行与双块取指 + FTQ 解耦）

- **Phase 3a（轻量跨行 2-fetch，优先落地）**：
  - I-Cache 按 64B cache line 奇偶拆为 **Even / Odd 双 bank**，支持同拍读相邻两行并经移位拼接输出完整 32B 连续窗口；
  - 放开 FTB 块的 64B 行尾截断限制，FTB 项显式存 `fall_through_offset`（支持块内超过 2 条分支时提前截断，PredecodeChecker 同步按 FTB `fall_through` 校验）；
  - 加深 `fetch_addr_fifo` 演进为真 **FTQ**，并评估基于 FTQ 的指令预取（FDIP）。
- **Phase 3b（任意双地址 2-fetch，配合 Phase 4）**：
  - I-Cache 扩展为双读口 / 多 bank 交叉（含 bank 冲突仲裁）+ 双 ITLB 查表 + 双段 RVC 指令拼接，支持单拍响应两个不连续取指地址。

---

### Phase 4：2-taken（单拍双跳转 / 超级块预测）

- **设计原则（避开 2-ahead × 2-taken 的组合陷阱）**：
  - 严禁简单把“严格 2-ahead”与“每拍推 2 个独立块”硬拼（会导致 4 块历史滞后与 $2^4$ 候选路径爆炸）。
  - 优先采用 **两种可控形态之一**（在 Phase 2/3 完成后先在模型量化对比）：
    1. **超级块 / 扩展 FTB（2-taken-in-block）**：单 FTB 项在跨 64B 行窗口内支持跨过第 1 个短 taken（或存 2 组目标/尾指针），历史滞后仍按块计数，配合双地址 2-fetch 输出拼接后的 8 宽指令组；
    2. **FTQ 解耦双块发射**：在 1-ahead（滞后可控）+ 跨行 2-fetch 基础上，对高置信度无条件跳转 / 强 taken 后拼接第二块（对应 `FE_PAIR` 演进版）。

---

## 3. 里程碑与文档同步约定

- 每完成一阶段，在 [EXPLORATION.md](EXPLORATION.md) 追加对应 `EXP-xxx` 记录（含面积/存储估算、SPEC06 386 点 IPC 与 TMA 对比、模型近似说明）；
- 合入 `main` 前必须完成 RTL 实现、三仓周期对齐、全量 27 窗 Linux 对齐及 `eda` 集群 Synopsys DC 28nm / Yosys 综合，并按 `WORKFLOW.md` §7.6 同步删除旧 16-bank 开关与死代码。
