# AI-Huma 架构探索记录

每次架构/性能探索写一节，最新的在最上面，不论是否合入、结论正负。规则见 [WORKFLOW.md](WORKFLOW.md) 第 5.1 节。

| 编号 | 日期 | 题目 | 分支 | 状态 | 一句话结论 |
|---|---|---|---|---|---|
| [EXP-003](#exp-003-rob-与-prf-扩大到-256) | 2026-11-04 | ROB/PRF 扩大到 192、256 | trace-model `exp/area-explore` | 未提交、未合入 | 都翻倍到 256 只快约 0.8%（coremark 3%），ROB 128 合理 |
| [EXP-002](#exp-002-全核面积浪费排查) | 2026-11-04 | 全核面积浪费排查：各 IQ、ibuf、front2back、分支资源、ALU/BRU 端口 | trace-model `exp/area-explore` | 未提交、未合入 | IQ 总项数 384→176、BRU 4→2 等组合后无性能损失；ROB 才是瓶颈；BPU 存储需大负载评估 |
| [EXP-001](#exp-001-面积优化三个方向) | 2026-11-04 | 面积优化：FTQ 合并、LSU 端口、LD/STA IQ 合并 | trace-model `exp/area-explore` | 未提交、未合入 | 三个方向都能省面积，性能代价 0–1% |

---

## EXP-003 ROB 与 PRF 扩大到 256

- **日期**：2026-11-04
- **分支**：trace-model `exp/area-explore`，改动**未提交**
- **问题**：EXP-002 看到 ROB（128 项 = 16 行×8）经常是满的。扩大 ROB 能换来多少性能？
- **开关**：`CFG_ROB_NUM`（默认 128）、`CFG_PRF_NUM`（默认 128），写在 `include/config.h`；构建命令在 `scripts/area/build_variants2.sh` 末尾。
- **负载和方法**：同 EXP-001。所有变体都开着逐条提交 difftest 跑完，ROB 192（12 行）也能正常运行。

| 配置 | dhrystone | coremark | memory-stress-small | matmul_fpu | prime | 几何平均 |
|---|---|---|---|---|---|---|
| ROB 256、PRF 128 | +0.64% | −1.89% | +0.97% | +0.18% | +0.16% | +0.01% |
| ROB 128、PRF 256 | +0.01% | −0.78% | −0.00% | +1.28% | 0 | +0.10% |
| ROB 192、PRF 192 | −0.01% | −0.44% | −0.00% | −0.04% | −1.49% | −0.40% |
| ROB 256、PRF 256 | −0.73% | −3.07% | −0.00% | +1.11% | −1.36% | −0.82% |
| ROB 256、PRF 256 + lean2（EXP-002） | −1.38% | −1.56% | −0.00% | +1.03% | −3.04% | −1.00% |

### 结论

- 只加 ROB 不加 PRF 没有用：可重命名的寄存器只有 96 个，ROB 填不满。
- ROB 和 PRF 都翻倍，几何平均只快约 0.8%，coremark 快 3%，matmul_fpu 反而慢 1%。ROB 256 时占用 p99 仍是满的（32 行），说明这些程序是依赖链和延迟受限，窗口再大也帮不上多少。
- **ROB 128 是合理的**：EXP-002 里"ROB 经常满"只说明它是后端最先满的结构，不代表扩大它收益很大。
- lean2 加上 ROB/PRF 256，比基线快 1%，但 ROB 和 PRF 都翻倍的面积代价远大于这点收益，不建议。
- 局限：负载很小；大负载（工作集更大、访存延迟更长）下窗口的收益可能更高，需要复核。

---

## EXP-002 全核面积浪费排查

- **日期**：2026-11-04
- **分支**：trace-model `exp/area-explore`，在 EXP-001 的基础上继续，改动**未提交**
- **问题**：除 EXP-001 的三个方向外，设计里还有哪些结构明显过大、存在面积浪费？

### 方法

在 EXP-001 的插桩和开关上新增以下内容，默认值都和原设计一致：

| 开关 / 统计 | 默认 | 作用 |
|---|---|---|
| `CFG_INT_IQ_SIZE` / `CFG_BR_IQ_SIZE` | 128 / 64 | INT、BR 两个 IQ 的容量 |
| `CFG_IBUF_SIZE` | 128 | pre-IDU 指令缓冲（`IDU_INST_BUFFER_SIZE`） |
| `FRONT2BACK_FIFO_SIZE`（已有宏） | 32 | front2back FIFO 深度 |
| `CFG_MAX_BR_NUM` | 64 | 在飞分支数上限，决定重命名检查点份数和 br_mask 位宽 |
| `CFG_PLAIN_ALU_PORTS` | 2 | 只做 ALU 的端口数（前 4 个兼做 MUL/DIV/FP/CSR 的端口不变） |
| `CFG_BR_PORTS` | 4 | 分支执行端口数 |
| `[AS] br_inflt` / `rob_lines` | — | 在飞分支数（`now_br_mask` 置位数）、ROB 占用的行数（每行 8 项，共 16 行） |

- 新增改动：`back-end/Idu.cpp`、`back-end/Rob.cpp`（统计）、`include/config.h`（开关）、`scripts/area/build_variants2.sh`。
- **默认配置验证**：gate 62/62，周期与基线一致。
- **负载、运行上限、复现方式**：同 EXP-001（`run_set.sh`、`summarize.sh`）。
- **位宽来源**：IQ 项按 RTL `isu_pkg.sv` 的 uop 结构手算，约 189b/项；BPU 按 `bpu_pkg.sv`、`bpu_btb_pkg.sv`、`bpu_*bank.sv` 手算。

### 模型近似和局限

- 负载和 EXP-001 一样小。coremark 对时序变化敏感，单项结果有约 ±1% 的噪声（例如 INT IQ 64 比 48 还慢 1.2%）；prime 只有 1.2 万拍，噪声更大。
- 分支预测器容量问题，小程序**完全测不出来**（代码体量太小），这里只做存储量统计，不下性能结论。
- 端口减少带来的频率、布线收益没有建模。

### 基线观察（`ARCH_STATS=1`）

| 结构 | 容量 | dhrystone 占用 p99 | coremark 占用 p99 | 说明 |
|---|---|---|---|---|
| ROB（行） | 16 | 16（p50=15） | 16 | **经常满，是真正的瓶颈** |
| INT IQ | 128 | 27 | 57 | 与 ROB(128) 一样大 |
| LD IQ / STA IQ | 64 / 64 | 12 / 11 | 61 / 17 | 分别受 LDQ、STQ 限制 |
| STD IQ | 64 | 34 | 16 | |
| BR IQ | 64 | 12 | 41 | |
| 在飞分支 | 64 | 13 | 48（最大 51） | |
| ibuf | 128 | 128 | 128 | 反压时被填满 |
| front2back | 32 | 32 | 32 | 反压时被填满 |

- 基线下分派从未因 IQ 满而阻塞。前端 FIFO 和 ibuf 被填满，是 ROB 满之后层层反压的结果，并不是需要这么深。
- 前端到译码之间能缓存约 512 条指令（指令 FIFO 16 组 + front2back 32 组 + ibuf 128 条），是 ROB 容量的 4 倍。
- IQ 总项数 384，是 ROB 的 3 倍。

### 结果：单项扫描（周期变化，相对基线）

| 变体 | dhrystone | coremark | memory-stress-small | matmul_fpu | 几何平均 | 判断 |
|---|---|---|---|---|---|---|
| INT IQ 64 | +0.00% | +1.20% | 0 | 0 | +0.24% | 噪声 |
| INT IQ 48 | +0.00% | −0.20% | 0 | 0 | −0.04% | **可缩** |
| INT IQ 32 | −0.05% | +1.66% | 0 | +0.04% | +0.38% | 边缘 |
| BR IQ 32 | 0 | +2.43% | 0 | 0 | +0.16% | 不缩 |
| BR IQ 16 | 0 | +4.71% | 0 | 0 | +0.82% | 不缩 |
| STD IQ 32 | −0.37% | 0 | 0 | 0 | −0.07% | 可缩 |
| STD IQ 16 | −0.41% | −0.55% | 0 | +0.02% | −0.19% | **可缩** |
| ibuf 64 | −0.17% | −0.21% | 0 | 0 | −0.93% | **可缩** |
| ibuf 32 | +0.13% | +1.65% | 0 | 0 | +0.23% | 边缘 |
| front2back 16 | 0 | 0 | 0 | 0 | −0.46% | 可缩 |
| front2back 8 | 0 | 0 | 0 | 0 | −0.55% | **可缩** |
| MAX_BR_NUM 32 | 0 | +2.36% | 0 | 0 | +0.08% | 不缩 |
| MAX_BR_NUM 16 | 0 | +6.15% | 0 | 0 | +1.24% | 不缩 |
| 纯 ALU 端口 2→1 | +0.06% | +1.11% | +0.59% | +0.01% | +0.09% | 边缘 |
| 纯 ALU 端口 2→0 | −0.06% | −0.46% | +8.04% | −0.12% | +1.67% | 不缩 |
| BRU 4→3 | 0 | +0.28% | 0 | 0 | +0.06% | 可缩 |
| BRU 4→2 | −0.13% | −0.34% | 0 | 0 | −0.48% | **可缩** |
| BRU 4→1 | +1.75% | +8.79% | 0 | −0.08% | +1.58% | 不缩 |

### 结果：组合配置

| 配置 | 内容 | dhrystone | coremark | memory-stress-small | matmul_fpu | 几何平均 |
|---|---|---|---|---|---|---|
| lean | INT48、BR IQ 32、STD32、LD+STA 合并 64、ibuf 64、front2back 16、MAX_BR 32、端口 4/3/3 | −0.29% | +2.12% | 0 | +0.11% | +0.20% |
| **lean2** | INT48、BR IQ 64、STD16、LD+STA 合并 64、ibuf 64、front2back 8、MAX_BR 64、BRU 2、端口 4/3/3 | −0.23% | −1.16% | 0 | +0.28% | −0.78% |
| lean2 + 统一 FTQ 64 | 同上，加 `UFTQ_CAP=64` | −0.23% | −1.16% | 0 | +0.28% | −0.78% |

lean 的 coremark 损失来自 BR IQ 32 和 MAX_BR 32；lean2 保留两者为 64 后，与基线持平。

**lean2 节省（只算存储，手算）**：
- IQ 384→176 项：约 39 Kb；唤醒比较器按 项数×2 源×15 个唤醒口 算，从 11,520 个降到 5,280 个。
- ibuf 64 项：约 2.8 Kb。
- front2back 24 项：约 23 Kb（若同时做 EXP-001 的 FTQ 合并，按 278b/项算约 6.7 Kb）。
- 端口：BRU 2 个，含配套的 FTQ PC 读口和 PRF 读口；STA、STD 各 1 个。
- 再加上 EXP-001 的 FTQ 改造（约 105 Kb）。

### 没有用 trace model 验证、但值得排查的设计问题

1. **每个 IQ 项都存完整 uop（约 189b）**：imm 32b、csr_idx 12b、func7、ftq_idx/offset、ldq_idx 等。STD IQ 实际只需要 src preg、stq_idx、rob_idx 和 br_mask。按 IQ 专门化字段，还能再省不少。
2. **br_mask 64 位**：每个 IQ 项、LDQ/STQ 项都带，约占 IQ 项的三分之一。性能上 MAX_BR 需要保持 64，可以考虑 ROB 区间等其他编码方式。
3. **BPU 存储约 1.1 Mb，比 L1D 数据阵列（64KB = 524 Kb）还大**：
   - TAGE：8 bank ×（1024×2b 基表 + 4×1024×13b）≈ 442 Kb
   - BTB：8×4 路×256×44b ≈ 360 Kb
   - TC：8×2 路×128×46b，加上同样大小的 pre 表 ≈ 188 Kb
   - 类型预测器：2 路×4096×14b ≈ 115 Kb
   - 类型预测器带 **16 个读口、8 个写口**，多端口阵列代价远大于存储本身。预测侧 8 个读口 + 提交侧 8 个读口，可以考虑提交侧改成从 FTQ 带回的信息更新，或只在分支上更新。
   - 容量是否合理需要用 Linux、SPEC 等大负载评估。
4. **ROB 经常满**：它是后端最先满的结构。EXP-003 实测把 ROB 和 PRF 都翻倍到 256 只快约 0.8%，所以 ROB 128 是合理的，不值得把面积挪过去。
5. **BPU 更新队列（`Q_DEPTH=2`，每 bank 一个，约 16×142b ≈ 2.3 Kb）**：它是 BPU 里另一个 FIFO，训练数据来自 FTQ。可以和 FTQ 合并成"提交时直接从 FTQ 读训练信息"，但体量很小，收益有限。

### 后续

- 在大负载上复核 lean2，并评估 BPU 容量（TAGE/BTB 每 bank 项数、类型预测器端口）。
- IQ 项按队列类型专门化字段，用 RTL 估算位宽。
- 实验：lean2 省下的面积挪给 ROB（160/192）。

---

## EXP-001 面积优化三个方向

- **日期**：2026-11-04
- **分支**：trace-model `exp/area-explore`（从 `main` `41a5cdd` 切出；改动**未提交**）
- **问题**：
  1. BPU 侧的预测 FIFO（PTAB）能否与 pre-IDU 的 FTQ 合并？
  2. LSU 端口（4 LD + 4 STA + 4 STD）是否过多？
  3. LD IQ 和 STA IQ（各 64 项）能否合并？

### 方法

插桩和开关，默认全部关闭：

| 开关 | 类型 | 默认 | 作用 |
|---|---|---|---|
| `ARCH_STATS=1` | 环境变量 | 关 | 每拍统计 FIFO/FTQ/IQ 占用、各类端口每拍发射数、分派阻塞原因，结束时打印 `[AS]` 行 |
| `UFTQ_CAP=N` | 环境变量（需 `ARCH_STATS=1`） | 关 | 模拟统一 FTQ：PTAB + front2back + 保持寄存器 + FTQ 总占用 ≥ N−1 时 BPU 停顿 |
| `CFG_LD_PORTS` / `CFG_STA_PORTS` / `CFG_STD_PORTS` | 编译宏 | 4/4/4 | 访存发射端口数（1–4） |
| `CFG_LD_IQ_SIZE` / `CFG_STA_IQ_SIZE` / `CFG_STD_IQ_SIZE` | 编译宏 | 64/64/64 | 各 IQ 容量 |
| `CFG_MERGE_LDSTA` + `CFG_MEM_IQ_SIZE` | 编译宏 | 0 / 64 | LD 和 STA uop 进同一个 IQ，向 LD 端口和 STA 端口发射（端口仍分开） |

- 改动的文件：`include/ArchStats.h`（新）、`include/config.h`、`front-end/front_top.cpp`、`back-end/PreIduQueue.cpp`、`back-end/Isu.cpp`、`back-end/include/IssueQueue.h`、`back-end/Dispatch.cpp`（IQ 合并时的路由 `route_iq`，ROB 完成掩码仍按原 IQ 计算）、`rv_simu_mmu_v2.cpp`、`main.cpp`；脚本 `scripts/area/{build_variants,run_set,summarize}.sh`。
- **默认配置验证**：开关关闭和 `ARCH_STATS=1` 两种情况 gate 都是 62/62，周期与基线完全一致。
- **负载**：dhrystone（150,838 拍）、coremark（226,991）、memory-stress-small（189,128）、matmul_fpu（42,253）、prime（11,760）。大程序（cjpeg、linear_alg、parser、sha、memory-stress、Linux）**没有跑**。
- **复现**：
  ```bash
  cd trace-model
  bash scripts/area/build_variants.sh                    # 各变体编进 build_area/<名字>
  bash scripts/area/run_set.sh build/simulator <out>/base
  bash scripts/area/run_set.sh build/simulator <out>/uftq64 UFTQ_CAP=64
  bash scripts/area/run_set.sh build_area/m64/simulator <out>/m64
  bash scripts/area/summarize.sh <out> uftq64 m64 ...
  ```

### 模型近似（结论的局限）

- `UFTQ_CAP` 不是真正的统一 FTQ：PTAB(16) 和 front2back(32) 的原有容量限制还在，只是在其上加一个总量上限；用上一拍的占用判断，有一拍滞后；取指地址 FIFO 没有并入。
- 端口数只改了发射端口和由它派生的 LSU/DCache/DTLB 端口数，**没有建模**端口减少后可能带来的频率提升或流水线变化。
- 负载都很小：prime 只有 1.2 万拍，±1.5% 以内基本是错误路径造成的噪声；memory-stress-small 是合成测试。
- 面积只按存储位数估算，**没有综合**；端口带来的多端口读写、比较器、选择逻辑只做定性分析。

### 基线观察（`ARCH_STATS=1`）

- 前端各 FIFO 经常打满（dhrystone：PTAB p90=14/16，front2back p90=31/32，FTQ p90=58/64）。原因是后端 ibuf(128) 满了在反压，并不是真需要这么多缓冲。三处加起来的预测信息占用 p99 = 111（上限 112）。
- 访存发射：dhrystone 平均每拍 LD 0.76 条、STA 0.53 条、STD 0.48 条；每拍发 3–4 条 LD 的周期约占 6.5%，3–4 条 STA 约占 8%。
- 基线下**分派从未因 IQ 满而阻塞**；coremark 有 4.5% 的周期因 LDQ 满阻塞。LD IQ 的占用受 LDQ(64) 限制，STA IQ 的占用受 STQ(64) 限制。

### 结果 1：PTAB + front2back + FTQ 合并为统一 FTQ

位宽来自 RTL（`rtl/rtl/frontend/front_pkg.sv`、`rtl/rtl/backend/pre_idu_queue/`），手算，未编译确认：

| 结构 | 现状 | 合并后 |
|---|---|---|
| PTAB | 16 × 704b = 11,264b | 去掉 |
| front2back FIFO | 32 × 976b = 31,232b（预测相关 22,528b） | 32 × 278b = 8,896b（指令 + ftq_idx） |
| FTQ | 64 × 1824b = 116,736b | 64 × 704b = 45,056b |
| 合计 | 159,232b | 53,952b（−66%） |

- **与合并无关、零性能风险的部分**：FTQ 每项按 `BACKEND_FETCH_WIDTH=16` 存 16 个槽，但前端每组最多 8 条（`FETCH_WIDTH=8`），第 8–15 槽永远无效。每个槽又各存一份 PC，其实就是 base+4i。只把 FTQ 改成 8 槽、存 base pc，就从 116,736b 降到 45,056b。PC 数组有 19 个读端口（ALU/BR 10 + ROB 1 + 提交 8），改成只读 32 位 base 后读口也会小很多。
- **已验证**（2026-11-04）：`BACKEND_FETCH_WIDTH=16` 是遗留参数，前端都按 8 来。新增开关 `CFG_BACKEND_FETCH_WIDTH`（默认 16），设成 8 后 gate 62/62，5 个负载的周期全部不变。可以直接把它改成 8（或等于 `FETCH_WIDTH`），FTQ、ibuf 偏移位、前后端接口随之减半。
- 合并后 FTQ 要多一个写端口，供预译码检查器回写纠正后的方向和下一取指地址。

| 统一 FTQ 容量 | dhrystone | coremark | memory-stress-small | matmul_fpu | prime | 几何平均 |
|---|---|---|---|---|---|---|
| 96 | +0.00% | +0.00% | 0 | 0 | +0.00% | +0.00% |
| 80 | +0.00% | +0.00% | 0 | 0 | −0.36% | −0.07% |
| 64 | +0.00% | +0.00% | 0 | 0 | −1.45% | −0.29% |
| 48 | +0.06% | +0.98% | 0 | +0.01% | −0.17% | +0.18% |
| 32 | +1.22% | +1.53% | 0 | +0.11% | −1.51% | +0.26% |

**结论**：统一 FTQ 64 项性能不变，建议做。

### 结果 2：LSU 端口数（LD/STA/STD）

| 端口 | dhrystone | coremark | memory-stress-small | matmul_fpu | 几何平均 |
|---|---|---|---|---|---|
| 4/4/4（基线） | 150,838 | 226,991 | 189,128 | 42,253 | — |
| 4/3/3 | +0.10% | +0.00% | 0 | +0.11% | +0.04% |
| 4/3/2 | +0.16% | +0.77% | 0 | +0.18% | +0.22% |
| 4/2/2 | +1.57% | +0.93% | 0 | +0.28% | +0.56% |
| 3/3/3 | +1.07% | +1.08% | 0 | +0.11% | +0.45% |
| 3/2/2 | +2.56% | +0.55% | 0 | +0.28% | +0.68% |
| 2/2/2 | +7.12% | +1.71% | 0 | +0.28% | +1.79% |
| 4/1/1 | +12.66% | −0.58% | +10.25% | +0.75% | +4.47% |
| 3/1/1 | +13.91% | +0.95% | +10.25% | +0.75% | +5.02% |
| 2/1/1 | +20.42% | +1.29% | +10.25% | +0.75% | +6.26% |

每个端口牵动：LD → AGU、DTLB 查找口（现在共 8 个）、DCache 读口、STQ 转发比较、load 写回和唤醒广播（每个 IQ 项的源操作数都要比较）；STA → AGU、DTLB 查找口、DCache 写口、LDQ 顺序检查比较；STD → PRF 读口、STQ 数据写口。

**结论**：4/3/3 基本免费（省 2 个端口）；4/2/2 代价 0.6–1.6%（省 4 个端口）。LD 不要降到 2，STA/STD 不要降到 1。

### 结果 3：LD IQ 与 STA IQ 合并

| 配置 | 总项数 | dhrystone | coremark | 其余三个 | 几何平均 |
|---|---|---|---|---|---|
| 分开 64+64（基线） | 128 | — | — | — | — |
| 合并 64 | 64 | −0.03% | −0.05% | 0 | −0.02% |
| 合并 48 | 48 | −0.03% | +0.54% | 0 | +0.10% |
| 分开 32+32 | 64 | +0.00% | +3.38% | 0 | +0.67% |
| 合并 32 | 32 | −0.03% | +3.61% | 0 | +0.71% |
| 分开 16+16 | 32 | −0.09% | +5.94% | ≈0 | +1.15% |
| 合并 48 + 端口 3/2/2 | 48 | +2.45% | +2.55% | ≈0 | +1.05% |
| 合并 32 + 端口 3/2/2 | 32 | +2.45% | +2.89% | ≈0 | +1.12% |

**结论**：合并成 64 项，IQ 项数减半，没有性能损失；同样的总容量下合并明显比分开好。入队写端口从 8+8 降到 8。可以在共享存储上保留两个独立选择器（只挑 LD / 只挑 STA），选择复杂度不变。与端口裁剪叠加有交互：合并 48 + 3/2/2 在 coremark 上比单独减端口差 2 个百分点；合并 64 + 减端口的组合还没测。

### 后续

- 在大负载（Linux 启动片段、SPEC 检查点）上复核三组结论。
- 测合并 64 项 IQ + 端口 4/3/3、4/2/2 的组合。
- 真正实现统一 FTQ（去掉 PTAB、front2back 只存指令和 ftq_idx），替代 `UFTQ_CAP` 近似。
- 有综合流程后，用面积数字代替存储位数估算。
