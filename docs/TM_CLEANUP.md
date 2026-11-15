# trace-model 清理合入 main（2026-11-16）

trace-model 是纯性能模型（只要求周期一致），分支 `exp/tm-cleanup`（ea1dde1，从 rvc-carry b97a325 分出，10 个提交）去掉执行驱动时代的残留，已合到 rv64-only 的 main（trace-model `e354755`）。合并只有 `back-end/Lsu/RealLsuPipe.cpp` 一处冲突（分支冻结了 `lp_l2`，main 加了 "faulting load 不写 rd"，两边都保留）。

## 内容（模型 C++ 42.9k → 约 36.8k 行，整体 192 个文件、-25.8k 行）

- 删除：`TB_POISON`、`tests/*_ref`、`*_diff`、`<MOD>_SHADOW`、`BEGIN_EQ`；difftest 的 compare / dut_cpu / `--no-diff`、`br_oracle.cpp`、`TB_NO_INJECT`；旧 LSU 和 `LSU_PIPE` 开关（阶段名去掉 `_p`）；运行模式 fast / ref / flash / sdcard；未用文件（baremetal 程序、训练文档、softfloat 头文件等）；从未调用的函数和未用配置常量。
- 冻结：26 个 LSU 消融开关（CUT 127、L2 115、WBUF 开）、LLC 固定模式 1，AXI 除频多拍和 L1D 快速时钟域（`FREQ_DIV=1`）。保留 `LSU_MEMSPEC` / `LSU_MS_DATA`（RTL 的 kill-switch 表依赖）和调试开关。
- 重组：`driver/`（main、BackTopLoad、RefCore、FastWarm）、`bridge/`（TraceBridge、trace_hook，原 diff/）；单 function-model 核（RefCore 用 `pmem_core_ctx`）。
- 保留：`Uop.result` / CSR 文件 / MMIO 数据（CSR 读和 MMIO load 要 patch_rd 回 function-model）、STQ 数据、`SIM_DDR_DATA`、RTL 参数化的变体（ROB_COMPACT、MOVE_ELIM、FE_RFAST/BFAST）、`FE_PAIR` / `FE_IPF`。
- 未做：17 个 `BPA_/BPO_/BPU_*` 开关（当时 rvc-carry 还在改前端）。

## 验证（合入前，rv64）

`run_gate` 62/62、`PF_ENABLE=0` 62/62、`run_gate_c`（RVC=1）67/67，周期等于现有基线；用合并后的模型重新生成 RTL 的 `scripts/ref_cycles.txt`，与已提交的表逐行相同。分支自己的 rv64gc Linux 检查（f311d18 与 b97a325 日志一致）在合并前做的，合并后没重跑。

注意：清理删了 7 个 RTL 不用的配置常量（`VIRTUAL_MEMORY_LENGTH`、`DCACHE_MISS_NUM`、`UART_ADDR_MASK` 等），重新 `make cfg` 时配置包里这几行会消失，不影响功能。
