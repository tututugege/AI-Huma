# 待办事项

全项目唯一的待办清单。每条写清为什么、做到什么算完；做完删掉，在 [LOG.md](LOG.md) 里留一行。（2026-11-23 阶段性清理：删除 EXP-029..061 已完成/已取代的条目，收敛为当前有效待办。）风险（验证缺口、变异存活）记在 [rtl/docs/08-risk-register.md](../rtl/docs/08-risk-register.md)，不在这里重复。

## 待做：TSMC 28nm DC 时序收敛（第二轮目标：全核 ≥ 1.3–1.5 GHz）

权威口径：**Synopsys DC `W-2024.09-SP2` + TSMC 28nm HPC+（`ssg0p81v125c`, 12T SVT+LVT, `CLK=0.50ns / 2.0GHz`, `compile_ultra`）**，Yosys（`strash;balance;map`）仅作分钟级快速迭代代理（详见 [rtl/docs/09-synthesis-report.md](../rtl/docs/09-synthesis-report.md) §15）。第一轮（EXP-062）已完成 `dcache_pf`（0.37→1.18 GHz）、`axi_llc_bop`（1.05→1.47 GHz）、`bpu_spec`（0.73→0.86 GHz）、`ren`（1.05→1.16 GHz）、`dcache_mshr`（Yosys 123→99 层）。第二轮待攻克瓶颈按 DC Fmax 排序：

| 模块 | 当前 DC 28nm WNS / Fmax / 级数 | 关键路径线索 | 优化方向 / 做完标准 |
|---|---|---|---|
| **`lsu`** | **−0.71 ns / 0.83 GHz / 55 lvl**（829k um²；Yosys 101 层） | `#1` `u_rp/rp_ldq_q → u_l1b/pl12_q[cand]`（1.16 ns）；`#2` `sta_info_q → u_ldq/f_q[rwait]`（1.17 ns） | 拆解 `lp_rp → l1b` 与 `sta_info_q → ldq` 违例/唤醒组合链（必要时可评估流水切分），冲 ≥ 1.3 GHz |
| **`bpu_eval`**（连带 `bpu` / `front_top`） | **−0.69 ns / 0.84 GHz / 69 lvl**（26k um²；Yosys `bpu` 197 / `front_top` 216 层） | S2 双块 `fin → fin_b` 校验与选择链 | 并行化或拆拍 `bpu_eval` S2 校验链并压低 `front_top` 跨模块路径，冲 ≥ 1.3 GHz |
| **`bpu_spec`**（余下瓶颈） | **−0.66 ns / 0.86 GHz / 41 lvl**（156k um²） | `aras_q[cnt] → st_q` 在 `M_ARCH` 上的 32 项全栈拷贝 | 消除 `M_ARCH` 全栈 32→64 拷贝（改为环形指针/指针切换），冲 ≥ 1.4 GHz |
| **`ren`**（两级流水评估） | **−0.36 ns / 1.16 GHz / 48 lvl**（144k um²；Yosys 91 层） | `inst_q → u_rat/spec_q`（重命名核心 + 依赖检查 + 移动消除） | 评估 2 级流水化 `ren`（SPEC06 IPC 代价 vs 频率冲 1.5+ GHz 收益） |
| **`exu_ctrl`** DC `(VER-37)` | 未出数 | `exu_ctrl_pkg.sv:205` 触发 DC 内部断言 `(VER-37)` | 改写触发 Presto 断言的写法，补齐 `exu_ctrl` 及整块 `exu` / `core_top` DC 28nm 报告 |
| **`axi_llc`** / **`icache`** / **`dcache`** 整块 DC | 未单跑整块 DC（子模块 `bop` 1.47 / `mshr` 1.15 / `wb` 1.49 / `s1/s2` ≥2.0 GHz） | SRAM 宏黑盒化后跑子系统级 DC 综合 | 为大阵列补齐 SRAM 宏/黑盒脚本，跑通 `axi_llc`、`icache`、`dcache`、`front_top`、`back_top`、`core_top` DC 综合 |

## 待做：验证与对齐

| 事项 | 为什么 | 做完的标准 |
|---|---|---|
| **逐条对比加上 store 比较**（rtl V-12） | 目前 `fm_check.h` 只比提交 PC 和目的寄存器，MMIO/缓存 store 数据错误只能靠串口或后续 load 间接发现 | `tb/soc/fm_check.h` 在每条 store 提交时比较物理地址、数据、字节使能（MMIO 与可缓存都比），门禁通过；再考虑 CSR 写值 |
| **RTL 抽样跑 SPEC06 点** | 当前 15.33 分/GHz 仅来自 trace-model；RTL 与模型周期相等只在 69 个小程序和 Linux 26 窗口验证过 | 12 个 SPEC06 INT 程序各抽至少 1 个高权重点，RTL 周期 = trace-model 周期且逐条对比 0 不一致 |
| **从复位 140M 周期 Linux 全程 RTL vs 模型对齐** | EXP-040 时期在 3000–3050 万周期起出现 PMU 区间偏差（+0.29%），近期合入均用 26 段检查点验证，尚未在最新 `main` 跑完整复位对比 | 在 `eda` 跑 8 线程静态 `soc_tb` 从复位到 `rv64 login:`，确认逐条 0 不一致并排查是否仍有区间分歧 |
| 检查点窗口比 PMU 区间（`PMU_CMP=1`） | 检查点恢复程序在 RTL 与模型上耗时不同，按绝对周期切 PMU 区间会错位 | 两边在恢复结束处对齐计数，`PMU_CMP=1` 通过 |
| RTL 断言与去复位随机初值 | 测试平台未默认开 `--assert`，且用 `--x-initial 0` 可能掩盖未初始化依赖 | 测试平台开启 `--assert` 及 `--x-initial unique` 跑通门禁 |
| 补齐覆盖缺口与 toggle 覆盖率 | `front_top`（RET `imm≠0`、SFENCE.VMA 后取指）、peripheral AXI、PTW 超级页/故障、MSHR_HIT/FULL、新旧降深度模块等价测试（`lp_ovl`、`bpu_ub_track_ser`、`bpu_updq`、`bpu_ub_look`、`front_fetch_buf`）缺回归 | 补定向测试与模块级等价测试进 `rtl/tb/`，并统计 Verilator toggle 覆盖率 |
| 扩大 gate（加入 `float_test` / `memory-stress` 等长程序） | 现有 69 个 gate 程序最长仅 ~31 万周期 | `float_test` 及更长定向程序进入常规门禁 |
| F/D 性能标定（SPECfp / PolyBench） | 当前 386 点均为 SPEC06 INT，FP 队列大小/延迟/STD FP 数据口尚未在浮点大负载上标定 | 建 rv64gc SPECfp 或 PolyBench 评测并标定 FP 后端参数 |

## 待做：微架构与 RTL 设计演进

| 事项 | 为什么 | 做完的标准 |
|---|---|---|
| **访存违例改为从违例 load 本身冲刷重取** | 当前违例 load 在 LSU 重执行后第二次写回（占 PRF 写口且增加 `lp_wb`/`MsData.h` `early_clean` 复杂度） | 违例 load 随冲刷从自身 PC 重取，第二次写回不占 PRF 写口；删除 `MsData.h` `early_clean` 补丁；SPEC06 量化净收益，模型与 RTL 同步对齐 |
| **拆解 ROB `diag_val`（64b × 256 项）** | `diag_val` 身兼指令字、分支目标、访存虚址、trap tval 多职，占 ROB 面积与 8×64b 提交读线 | 访存地址改由 LDQ/STQ 提供、分支目标改放 FTQ、非法指令字改用小旁表，最终删掉 ROB `diag_val` 列 |
| **香山式独立 SBuffer** | EXP-024 的 STQ 内分组 write buffer 仍占着 STQ 项等响应 | 独立 64B 整行+字节掩码 SBuffer，提交即释放 STQ、按阈值排空、load 查 STQ > SBuffer > DCache；全量 SPEC06 量化收益后再做 RTL |
| **AMO 改为 DCache 内读改写（AMOALU）** | 当前 AMO 拆成 LOAD + STA + STD 同占 LDQ/STQ | AMO 仅占 STQ，队头排空 ROB 后发 DCache 读改写，删除 dispatch AMO 双写口特例 |
| 分支密集短循环 BPU 更新额度优化（EXP-028 遗留） | 紧凑 ROB 为防 BPU 更新队列溢出而限流提交，导致少量分支密集短循环变慢 | 额度不足时不挡提交、仅丢弃已饱和且预测正确的分支更新；模型与 RTL 同步 |
| `front_stall` 接回 & LLC 旁路写/部分行写 miss | `core_top` `front_stall` 写死 0；LLC 旁路写/部分行写仅留断言 | 接回并补定向/随机流量测试 |
| PMU 软件可见性（CSR 接入）与过期测试修复 | RTL PMU 计数器块尚未实例化接 CSR；`tests/pmu/pmu_tb.cpp`（`NUM_EV=52`）与 `soc_tb.cpp`（`kPmuEv=51`）落后于当前 66 事件；前门恢复 `cycle_base` 未清零 | 决定是否开放 CSR；更新 PMU 测试；补齐二级 TMA 事件 |
| 仿真速度双版本评估（`` `ifdef SYNTHESIS ``） | 已有 `mul_core`、公共原语、FPU 走双版本；`bpu_ub_track_ser`（`rem_of` 建表）等低深度模块尚未 profile | `--prof-cfuncs` 定位最慢模块，只对热点补快速仿真路径与等价测试 |

## 已知 trace-model vs RTL 细微差异（备忘，待按需收敛）

- **变延迟 Early-out DIV 错路操作数差 & Linux `s19` 既有微差（2026-11-23 EXP-061）**：① wrong-path 上 `trace-model` 无操作数事实（固定 2 拍），RTL 用寄存器堆脏值算 `clz`（2..17 拍），极少数误预测解析前完成的错路 DIV 可能在 Port 1 `wb_next` 阻塞差 1 拍；② 26 窗 Linux 检查点 26/26 0 FM 不一致、25/26 PT/UP 全等，仅 `s19` 在 `cyc=2372697`（距最近 DIV 17,548 拍）存在 1 处与 EXP-052 `s17` / EXP-056 `s02` 同类的既有错路陷入边界微差。
- **其余静态小差异（EXP-044 盘点）**：
  - `prf_awake` 在写回级唤醒所有 load；模型跳过 `early_woken`。
  - CSR 异常优先级：RTL 非法指令先于断点，模型相反；`mstatus` 输出无 SD 位（19 vs 22 个 CSR）。
  - `peripheral_axi_fmt` 对 lb/lh/lw 做 64 位符号扩展，模型 `extract_read_data` 对高 32 位零扩展。
  - `ptw_walk` 静默截断 >32 位 PPN，模型 `exit(2)`；路由号 RTL 4 位、模型 32 位。
  - `ldq_alloc_valid` 在 `dispatch_lsu_alloc` 未使用；ROB 独立算 F/D `fs_*`/`fflags`（模型从 bridge 取）。

## 待做：代码卫生、生成器与文档债

- **生成器同步**：`tools/gen_backtop.py`、`gen_soc_top.py`、`gen_cfg_pkg.py` 与手改的 `back_top.sv`/`exu.sv`/`soc_top.sv`/`ttg_cfg_pkg.sv` 补齐同步（让 `make cfg` 与提交包逐字节一致，不再输出已删常量）。
- **`axi_subsys` UNOPTFLAT**：确认 `axi_llc.in_w` 组合环是否为误报，消除后纳入 `-Wall`。
- **死代码与过期注释清理**：`rob.sv` `pf_inst` 恒 0；`lsu_pipe.sv` 孤立 `lint_on`；`tests/tlb_par` 过期接口；`exu_fu` 单周期单元无用端口；LLC `hz_wctx`/`hz_wresp`；`mem_axi` 桩口 2；`tlb_mmu_pkg`/`fp_pkg` rv32 残留；`ptw_walk` L1/L2 误导命名；各模块旧注释（`27 FUs`、`14 wake channels`、`16 tick`、`8->16 lane` 等）。
- **可选架构清理**：是否删除默认关闭且不再使用的 `bpu_ub_track.sv`（`RVC=0`）和 `FE_BFAST` 分支；`RealLsu` 3 个 SSA 展开文件手写化；`spec/*.io` 明确退役或更新。
- **RTL 文档补全**：全模块压到 ≤100 层后补齐 `rtl/docs/DEPTH_OPT.md`，清理各 `rtl/docs/modules/*.md` 末尾的“未核对”项，核对 `pmu`/`common` 的 `area` 字段。
- **未决定是否合入的历史探索**：`BPO_LOOP=1` 循环预测器（EXP-025）、`exp/sdip`（EXP-026），如需重启须在当前 15.33 分/GHz `main` 上重测。
- **合入流程自动化**：把 `scripts/linux_check.sh` 正式写进 `WORKFLOW.md` 检查清单。
