# RTL：TLB 口并行化、first_set 对数深度、测试平台去掉对 trace-model 源码的依赖（2026-11-17）

rtl 分支 `exp/tlb-par`（从 main `8abb7ab` 开出）的两个提交，快进合入 rtl main（`261bd67`）。实验记录见 [EXPLORATION.md](EXPLORATION.md) EXP-042。

## 提交

| 提交 | 内容 |
| --- | --- |
| `1d8688e` | **TLB 口并行化**（`tlb_mmu_core.sv`、`tlb_mmu_lane.sv`）：8 个翻译口不再串成一条链。一拍里改共享状态（walk 寄存器、回填、PTW 请求/响应）的口最多两个——A（第一个在当前 walk 页上缺失的口）和 B（walk 空闲或被 A 退休后第一个缺失的口），各口并行算好自己的缺失/同页/权限和两种回填视图下的结果，A、B 用 8 位 first_set 选出，选择只控制末级二选一。行为与串行链逐拍相同。<br>**`ttg_first_set`**：`req & -req` 改为 Kogge-Stone 前缀或（函数相同，`log2 N` 级，37 个模块在用）。<br>**`tests/tlb_par/`**：旧串行核心原样保留为 `*_ref`，与新核心并排随机比较全部输出。 |
| `261bd67` | **测试平台**：自带 `tb/soc/fpr.h`（对齐指纹的 RTL 侧，哈希与 trace-model `front-end/BPU/fpr.h` 逐位相同），不再 include trace-model 源码（trace-model `c984a0c` 删掉 `fpr::set_raw_cycle` 后测试平台编译不过）。<br>**构建提速**：`tb/soc/build.sh` 默认用全部核编译 C++，生成的 C++ 按 5000 条语句拆分；`build_soc64_linux.sh` / `build_soc_vcd.sh` 不再写死 `JOBS=6`。 |

## 结果

| | 合入前 `8abb7ab` | 合入后 |
| --- | --- | --- |
| `tlb_mmu` 深度代理（rv64，`synth_depth.sh`） | 163 | **67** |
| `tlb_mmu` 单元数 | 84,088 | 80,255 |
| `tlb_mmu_lookup` / `icache_itlb` 深度 | 61 / 68 | 33 / 49 |
| first_set 的其他用户 | `lsu_stlf_match` 139、`isu_iq_select` 69、`isu_alloc_chain` 72 | 97、46、55（后两者面积 +0.6k / +1.5k） |
| rv64 Linux 测试平台构建（14 核） | 111 s | 89 s（约 60 s 是 Verilator 单线程前端） |
| 周期、仿真输出、仿真速度 | | 不变 |

完整综合表：`rtl/docs/09-synthesis-report.md` 第 11 节；设计说明：`rtl/docs/modules/tlb_mmu.md` 第 2 节、第 3 节第 6 条、第 5 节。

## 验证（rv64gc）

- `tests/tlb_par/run.sh`：rv64 300 万拍 0 不一致（DTLB 8 口 + ITLB 1 口），3 个人为变异全部抓到；`ttg_first_set` 在 N=1/3/7/8/13/64 上与 `req & -req` 一致；`make prims` PASS。
- `lint.sh` 与 main 相同，`lint_chip.sh` 0 警告。
- fm_gate 67/67 逐条对 function-model 一致，周期与 `scripts/ref_cycles.txt` 0 差异（两个提交各跑一次）。
- Linux 检查点窗口 s03/s07/s11（各 400 万周期，`linux_segments_cmp.sh`，对 trace-model main `5b95b35`、function-model main `55affa0`）：3/3 PASS，与同环境下 rtl main 的 rtl.out / rtl.err 逐字节相同；测试平台改用自带 `fpr.h` 后 s07 再跑一次，输出逐字节相同。
- 没有跑从复位开始的完整 Linux（1.4 亿周期）。

## 顺带发现（记在 [TODO.md](TODO.md)）

- Linux 窗口必须用 function-model main 的检查器：用 `drop32/function-model`（`d12be0c`）构建的测试平台在第 94949 周期误报不一致（rtl main 也一样）。
- 测试平台对 trace-model 还剩两处依赖：DRAMsim3（`$TM_DIR/third_party/DRAMsim3`）、门禁测试程序（`trace-model/build`）。
- trace-model 的 Makefile 链接 `-lstdc++fs`，macOS 本机构建要加 `LDFLAGS=-lz`。
