# EXP-030 第二步：trace-model 的 F/D 方案

> **2026-11-12 更新：第一版已按本方案实现（trace-model `exp/fd` `2c1d166`），与方案不同之处和验证结果见 `EXPLORATION.md` 的 EXP-030。下面保持写方案时的原文。**

2026-11-12，读完 trace-model（`main`，`4cf9b6b`）后写的方案，**还没有改任何代码**。function-model 的 F/D 已在 `main`（`e0078bc`）。

## 1. 读到的现状（决定方案的几点）

- **模型不算值。** 分支方向/目标、地址、store 数据、CSR 写数据、`rd_value` 都来自 trace bridge（`diff/TraceBridge.*`，用 `librefcpu` 跟着模型的派发流执行，含错误路径）。PRF 只剩标签：`Prf.cpp` 的 `comb_write` 是空的，剩下的是写回流水寄存器，用来驱动 load 唤醒和旁路时序。所以浮点要建模的是**重命名、发射队列、唤醒、功能单元时序和 LSU 的数据流**，不是数据通路。
- **重命名**（`Ren.cpp`）：一张 `ARF_NUM+1 = 33` 项的 RAT（x0 占一项）、一个环形空闲表（`PRF_NUM = 128`）、每个分支一份 RAT 检查点（`MAX_BR_NUM = 32`）、提交时按旧目的寄存器回收；还有 move elimination（`arch_cnt` 引用计数）。
- **发射**（`Isu.cpp`、`IssueQueue.h`、`config.h`）：五个队列 INT 64 / LD 64 / STA 64 / STD 16 / BR 32，入队宽度 7/6/4/4/5；发射口 `GLOBAL_ISSUE_PORT_CONFIG` 共 18 个（INT 6、BR 2、LD 4、STA 3、STD 3），按能力掩码绑定。唤醒是**统一的标签广播**：load 写回、MUL 流水、DIV/FP 倒计时、单周期快速唤醒、LSU 提前唤醒各占通道；队列项只比较源标签。Dispatch 里有 `busy_table[PRF_NUM]`。
- **已有一个 FP 的雏形**，但它是 rv32 **Zfinx** 用的：`UOP_FP` 走 INT 队列的 1 号口，`FuKind::FPU` 是**迭代单元（一次一条，3 到 10 周期）**，延迟只认 `.s` 的 funct7。rv64 的 F/D 不能沿用，要换掉（`FP` 编译开关打开时让出这个口）。
- **译码**（`Idu.cpp`）：`OP-FP` 现在只有 `number_12_opcode_float` 一支，`fmadd` 族、`flw/fld/fsw/fsd`（opcode 0x07/0x27）按非法指令处理；`fflags/frm/fcsr` 当 NOP（没有时序影响）；`AREG_IDX_WIDTH = 6`（33 个整数寄存器加 AMO 的虚拟目的寄存器）。
- **派发拆分**（`Dispatch.cpp::decompose_inst`）：一条指令最多 3 个 uop（store = STA + STD，JALR = INT + BR，AMO 三个）；STD 用 `src2_preg` 当数据源。
- **trace bridge 是手写译码的**：`dispatch()` 里按 opcode 0x03/0x23/0x2f 算 `vaddr`、`size`、`store_data`；撤销日志（`rd_old`、`kTrapCsr` 8 个 CSR）只还原整数寄存器和少数 CSR；`RefCpuState` 没有浮点寄存器。difftest（`diff/diff.cpp`）比较 `gpr` 和 21 个 CSR。`FastWarm.cpp` 只认 0x03/0x23/0x2f。
- **`MsData.h`**（内存相关推测的值通路）：有按物理寄存器编号的污染表 `taint[PRF_NUM]`，对 FP 等不建模的指令返回"不建模"。

**没读透、实现时要核对的**：`RealLsuPipe.cpp` 里 load 写回/提前唤醒/取消的细节、`Rob.cpp` 的完成掩码和异常提交、PMU 的分类、`BackTopLoad.cpp`（检查点装载）。

## 2. 设计决策（带推荐）

**D1 标签空间：模型里用统一编号，RTL 里分开。**
FP 物理寄存器编号接在整数之后：整数 `0..PRF_NUM-1`，浮点 `PRF_NUM..PRF_NUM+FPRF_NUM-1`。这样队列项、`busy_table`、唤醒广播、`MsData` 污染表的代码几乎不用改，只是数组变大、`PRF_IDX_WIDTH` 多一位。RTL 实现时是两套寄存器堆各自的编号加一个域位，唤醒总线按域分开，这个对应关系写进 RTL 文档。

**D2 浮点重命名：单独一套。**
新增 FP RAT（32 项，没有 x0）、FP 空闲表、每个分支一份 FP RAT 检查点、提交时回收旧目的寄存器。译码给每个 uop 加 `dest_fp` / `src1_fp` / `src2_fp / src3_fp` 域位，重命名按域选 RAT 和空闲表，每个域各自停顿。**FMA 有第三个源**：`UopS` 要加 `src3_preg`，三源的 uop 进 FP 队列，每项存 3 个标签。move elimination 不做 FP（`fsgnj.d f,f,f` 不消除）。
FP 物理寄存器数默认 96（32 架构 + 64 重命名，`CFG_FPRF_NUM`），后面扫。

**D3 FP 发射队列：新增 `IQ_FP`。**
起始配置（`CFG_FP_*` 可扫）：队列 32 项，入队宽度 4，3 个发射口：
- FP0：`fadd/fsub/fmul/fmadd` 族（FMA 流水）+ `fsgnj/fmin/fmax` + `fcmp`、`fclass`、FP→INT 的搬移和转换；
- FP1：同样的 FMA 流水；
- FP2：`fdiv/fsqrt`（非流水迭代）+ `fcvt` 的浮点内部转换。
FP→INT 的结果写**整数**标签，唤醒 INT 队列。端口能力用新的 `OP_MASK_*` 表达，原来的 `OP_MASK_FP`（Zfinx）仍只在 `FP` 关闭且 XLEN=32 时留在 INT 口上。

**D4 浮点 load / store：复用现有 LSU。**
- `flw/fld`：走 LD IQ，地址源是整数标签，目的是浮点标签（`dest_fp`）；LSU 的写回和唤醒按标签工作，统一编号后不用改。`func3` 2/3 和 `lw/ld` 一样，大小逻辑不变。
- `fsw/fsd`：STA 走 STA IQ（整数基址）；**STD 的数据源是 FP 标签**。推荐的第一版：STD IQ 里 `src2` 可以是 FP 标签，只让 **STD 的 0 号口**能发射 FP 数据（能力掩码区分），其他口只收整数数据。这样 LSU 和 STQ 一行不动，RTL 代价是 FP 寄存器堆多 1 个读口。备选（BOOM 的做法）：FP store 的 STD 放进 FP IQ 自己的发射口，STQ 多一个来自 FP 域的写口；以后当单独实验比较。

**D5 跨域指令。**
- INT→FP（`fmv.d.x/w.x`、`fcvt.{s,d}.{w,wu,l,lu}`）：走 INT IQ，在 INT 口上执行，目的是 FP 标签，延迟 2 到 3（`CFG_FP_I2F_LAT`）。
- FP→INT（`fmv.x.*`、`fcvt.{w,wu,l,lu}.*`、`feq/flt/fle`、`fclass`）：走 FP IQ，目的是整数标签。
- 模型里写回口没有数量限制；RTL 需要给整数/FP 寄存器堆各加跨域写口，先在模型里统计每周期跨域写回的数量，作为 RTL 决策的依据（PMU 加一个计数）。

**D6 功能单元延迟（起始值，全部是 `CFG_FP_*` 参数）。**
`fadd/fsub/fmul/fmadd` 4（S 和 D 相同）；`fsgnj/fmin/fmax/fcmp/fclass` 2；`fcvt` 浮点内部 3，整数↔浮点 4；`fmv` 2；`fdiv` S 12 / D 20，`fsqrt` S 14 / D 24（非流水，一次一条，占住 FP2）。后面用 SPECfp 或 PolyBench 的热点来标定，不是定值。

**D7 CSR 与 fcsr。**
`fflags/frm/fcsr` 的读写变成真正的 CSR uop（和别的 CSR 一样串行化），否则在途 FP 指令会读到旧的 `frm`；`mstatus.FS=Off` 的非法指令由 function-model 的事实给出（trace bridge 已经处理 `trapped`），不用在模型里判断。`fflags` 累积和 FS 置 Dirty 都是值的行为，模型不管。

**D8 trace bridge 和接口。**
- `RefCpuState` 在 FP 构建下加 `uint64_t fpr[32]` 和 `fcsr`（`refcpu_api.cpp` 的 `export_state/import_state` 同步）。
- `Bridge::dispatch`：opcode 0x07/0x27 算 `vaddr/size/store_data`（`fsd/fsw` 的数据取 `fpr[rs2]`）；`Fact` 加 `rd_is_fp`、浮点 `rd_value`（64 位）、`rs2_value` 对 FP store 取 `fpr`；撤销日志加 `fpr` 旧值和 `fcsr` 旧值；`kTrapCsr` 已包含 `mstatus`，FS/SD 随它还原。
- difftest：`diff.cpp` 比较加 `fpr` 和 `fcsr`。
- `FastWarm.cpp`：加 0x07/0x27。
- 检查点装载：`BackTopLoad.cpp` 和 `--mode ckpt` 要认版本 5（`CPU_state` 带 `fpr`）。

**D9 `MsData`（内存相关推测的值通路）。**
污染表按统一编号放大；FP 消费者按"不建模"处理（和现在对 FP/AMO 一样）。已知近似：一个过早的 FP load 的陈旧值经 `fcmp` 影响分支，这条链不会翻转分支结果，只会少算一点推测错误。写进文档，不当 bug。

**D10 配置和默认值。**
新开关 `CFG_FP`（默认 0；只能和 `XLEN=64` 一起开，对应 function-model 的 `FP=1`），所有 `CFG_FP_*` 都是整型标量，进 RTL 的配置包生成器。**`CFG_FP=0` 时周期和现有基线逐个相同**；`CFG_FP=1` 跑纯整数程序时周期也必须逐个相同（FP 结构空转）。

## 3. 改动清单（按文件）

| 文件 | 改动 |
|---|---|
| `include/config.h` | `CFG_FP`、`CFG_FPRF_NUM`、`CFG_FP_IQ_SIZE/ENQ_WIDTH`、FP 口、`CFG_FP_*_LAT`；`IQ_FP` 进 `GLOBAL_IQ_CONFIG`；`PRF_IDX_WIDTH` 按总标签数 |
| `back-end/include/base_types.h`、`types.h` | `UOP_FPU / UOP_F2I / UOP_I2F`（或按能力掩码细分）、`IQ_FP`；`UopS` 加 `dest_fp`、`src*_fp`、`src3_areg/src3_preg`、`rm` |
| `Idu.cpp` | 译码 OP-FP（S/D 全部）、四个融合乘加、`flw/fld/fsw/fsd`、FP CSR；设域位 |
| `Ren.cpp`、`include/Ren.h` | FP RAT / 空闲表 / 检查点 / 回收 / 停顿；提交时按域回收 |
| `Dispatch.cpp` | `decompose_inst` 的 FP 分支、三源 busy、`busy_table` 放大、FP IQ 路由和反压 |
| `Isu.cpp`、`IssueQueue.h` | FP IQ 实例、三源唤醒、FP 口的快速唤醒/倒计时唤醒、FP 唤醒通道 |
| `Exu/Exu.cpp`、`Exu/include/Fu.h` | FP 流水单元（FMA，固定延迟）和 `fdiv/fsqrt` 迭代单元，延迟表；去掉 Zfinx 的 `FPU` 在 rv64 FP 下的使用 |
| `Prf.cpp`、`Wires.h`、`IO.h` | 写回/唤醒通道数、FP 口的 `iss2prf` 项 |
| `Lsu/*`、`MemSubSystem` | 预期不改；核对 load 写回的 `dest_preg` 位宽和 `func3` 用法 |
| `Rob.cpp`、`Pmu*.cpp` | 完成掩码核对；PMU 加 FP 发射数、FP IQ 满、FP 空闲表空、跨域写回数 |
| `diff/*`、`function-model/include/api`、`refcpu_api.cpp` | D8 |
| `MsData.h` | 污染表放大、FP 不建模 |
| `docs/PROJECT.md`、`docs/ENV_VARS.md`、`rtl/docs` | 配置、域标签对应关系 |

## 4. 分阶段和验证

1. **接口和基线不变。** `RefCpuState`/bridge/difftest/FastWarm/检查点加 FP；`CFG_FP=0` 下 gate 64/64 周期与基线逐个相同。
2. **译码 + 重命名 + 空 FP 队列。** 浮点指令能译码、重命名、派发、在 FP 队列里发射（先统一 4 周期），load/store 通，difftest 无不一致；`CFG_FP=1` 的纯整数程序周期不变。
3. **功能单元和跨域。** FMA 流水、迭代的 `fdiv/fsqrt`、`F2I/I2F`、FP CSR 串行化；加空闲表泄漏检查（仿 `ME_CHECK`：FP 空闲表 + 在途 + 架构寄存器 = `FPRF_NUM`）。
4. **测试负载。** `rv64uf/ud` 官方用例（改成能在 trace-model 跑）、`fp-kernels`、PolyBench 的 rv64 FP 版本（`scripts/wl` 现在只有 rv32imab，要补）；全部要求 difftest 通过、无死锁（`SIM_MAX_CYCLES` 兜底）。
5. **标定和实验。** 延迟、FPRF 大小、FP IQ 大小和口数、STD 方案扫一遍，结果记进 EXPLORATION；合 main 时按规则更新 `baseline.csv` 和 MAIN_RECORDS（`CFG_FP` 默认仍 0，基线不变）。

## 5. 风险和要你定的事

- **三源操作数**会碰到 `UopS` 布局、IQ 项宽度和 `src*_busy` 的每一处；这是改动里最散的一块，先做完再接别的。
- **统一编号**对 RTL 不是现成的：RTL 要有域位和分开的唤醒总线，需要在 RTL 文档里写清楚，避免模型和 RTL 的周期对不上。
- **没有 FP 工作负载**之前，延迟和队列大小只能是经验值；步骤 4 的负载要先准备。
- 待定：(a) FP 物理寄存器 96、FP IQ 32、3 个口、STD 0 号口兼 FP 这组起始值是否接受；(b) 先做 `CFG_FP` 默认关，是否同意；(c) RTL 的 F/D 放在 trace-model 标定之后。
