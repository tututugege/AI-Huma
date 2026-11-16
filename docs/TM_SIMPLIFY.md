# trace-model 简化合入 main（2026-11-16）

分支 `exp/tm-simplify`（从 rv64-only 的 trace-model main `75c8141` 分出，38 个提交，到 `fb471da`）快进合入 trace-model main。目标：代码大幅减少、速度略快、跨模块组合调用更少；每个提交周期都与基线逐一相同。详细过程见 trace-model 的 `docs/SIMPLIFY.md`，环境变量见 `docs/ENV_VARS.md`。

## 结果

| | 合入前 75c8141 | 合入后 fb471da |
| --- | --- | --- |
| 模型 C/C++ 行数 | 37,269 | 30,452（-18.3%） |
| 运行时读取的环境变量 | 77 | 16 |
| rvc-alu / rvc-mem / fd-rvc-mem cycles/s | 271.9k / 206.1k / 218.6k | 338k / 254k / 272k（1.24x） |
| 后端组合顺序隐患（`scripts/comb/comb_graph.py`） | 1 处真实 | 0 |

## 内容

- 冻结：BPU 的 `BPU_*` / `BPO_*` / `BPA_*` 实验开关（loop 预测器删除）、`FE_RFAST`=15 / `FE_BFAST`=0、`LSU_MEMSPEC`=1 / `LSU_MS_DATA`=7、`FP_WB_PORTS`=2、DRAMsim3 运行时覆盖；编译期变体 FP=0、行式 ROB、MOVE_ELIM=0、无 LLC、固定延迟 SimDDR 删除。
- 删除：没人读的统计和调试打印、`TB_CHECK` 值比较及其阳性 / 阴性对照、编译期关掉的日志、370+ 未用常量 / 宏 / 类型、约 60 个没人调用的函数、SD 卡控制器模型、只写不读的 IO 字段。
- 重组：指令 FIFO / PTAB / 前后端 FIFO 一个模板；I-cache 栈 2,961 → 1,689 行（`icache/icache_top.cpp` 一个文件）；所有 TLB 走内存子系统的共享 PTW（TLB 本地 walker 删除）；前端自身寄存器合成 `FrontRegs`（q / d）；PreIduQueue 读上一拍 ROB flush 改成显式寄存器。
- 保留：PMU / TMA、`FE_PAIR`、`FE_IPF`、`PF_ENABLE`、`DS3_OUT`，以及 RTL 对齐用的 `LSU_PIPE_NOWD`、`FPR` / `FPR_DUMP`、`TB_TRACE_COMMIT`（`rtl/scripts/first_diff.sh`）、`LSU_PIPE_EVT`（和 tb 的 `SOC_TB_LSUEVT` 对比）。

## 和 RTL 的关系

- `include/config.h` 末尾保留 RTL 专用参数块（`XLEN_BITS`、`ROB_COMPACT`、`MOVE_ELIM`、`LSU_MEMSPEC`、`FE_BFAST`、BPU meta 宽度、IQ 大小、LSU 窗口宽度）：模型不读它们，但 `gen_cfg_pkg.py` 导出、RTL 使用。用合并后的模型生成的 `ttg_cfg_pkg.sv` 与用合入前 main 生成的 170 个名字和值完全相同（只是顺序不同）。
- RTL 的变体开关（`gen_cfg.sh -DCFG_LSU_MEMSPEC=0` 等）还能生成，但模型只实现默认值，这些变体不再有模型参考；`rtl/scripts/ref_cycles_nomemspec.txt` 无法再用模型重新生成。
- 周期与合入前相同，`rtl/scripts/ref_cycles.txt` 不变。RTL 里仍有模型已删掉的变体（行式 ROB、MOVE_ELIM=0、LSU_MEMSPEC=0、FE_RFAST/BFAST 位、rv32），没有改。

## 验证（rv64）

每个提交：`run_gate` 62/62、`run_gate_c`（RVC=1）67/67，周期等于基线；`comb_graph.py --check` 0 隐患。BPU 对齐指纹 `FPR` 在 rvc-alu / rvc-mem / fd-rvc-mem / rvc-flow 上与基线逐字节相同；`TB_TRACE_COMMIT` / `LSU_PIPE_EVT` 的输出与基线逐字节相同。rv64gc Linux（200M 周期）控制台输出在 595e4a7、7b249c1、099143b、13166f4、b94f881 上都与基线相同。

未做：AXI 互连 / LLC 的剩余通用性、前端和内存子系统的组合检查、表驱动的组合调度和 Reg / Wire 写法规则。
