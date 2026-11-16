# trace-model bridge 提速、共用译码、SimCpu 整理、检查点交给功能模型（2026-11-16）

trace-model 分支 `exp/simcpu`（含 `exp/bridge-fast`，从 main `efb0800` 起，7 个提交）快进合入 trace-model main `a127371`；function-model 分支 `exp/step-access`（2 个提交）快进合入 function-model main `55affa0`。两边一起合入：trace-model 用到了 function-model 新增的 API。每一步周期都与基线逐一相同。详细过程见 trace-model 的 `docs/MODULE_CONTRACT.md` 末尾几节。

## 提交

| 仓库 | 提交 | 内容 |
| --- | --- | --- |
| function-model | c845d8d | API 增加单字段读取（`refcpu_gpr / fpr / fcsr / csr / pc / privilege / reservation / store_info`）和 `refcpu_set_pc` |
| function-model | 55affa0 | API 增加 `refcpu_restore_checkpoint`（返回区间长度和文件里的原始状态）、`refcpu_get_io_backing_word`（设备寄存器的存储值）；恢复时内存按页稀疏写入，允许检查点 RAM 比模拟器小 |
| trace-model | 9caaeb6 | trace bridge 每条指令不再拷贝两次功能模型的完整状态（约 0.7 KB），改为单字段读取；条目从空闲链表分配 |
| trace-model | 319e69b | 共用译码器 `decode_inst`（bridge/InstDecode.cpp），IDU 和 bridge 各自的译码合成一份；IDU 只保留时序规则和分支 tag |
| trace-model | 7d361b3 | `rv_simu_mmu_v2.cpp` 改名 `SimCpu.cpp`；去掉 `#define private public`、无用 include、oracle 模式残留；程序退出码改为功能模型的 a0 |
| trace-model | 69e6b87 | `AxiSubsystem` 模块（interconnect、DDR、MMIO、UART）；SimCpu 自己的保持寄存器改为 `Regs q_ / d` |
| trace-model | 9f60d17 | `number_PC` 改为 `restored_pc`（不再每拍由 SimCpu 写）；`restore_pc` 经 `FrontTop / BackTop::restart_at`；提交时的设备写钩子注明为环境动作 |
| trace-model | a127371 | 检查点文件由功能模型读（`refcpu_restore_checkpoint`），trace-model 自己的解析器（BackTopLoad.cpp）删除；加载函数移到 `driver/Load.cpp` |

## 结果

| | 合入前 efb0800 | 合入后 a127371 |
| --- | --- | --- |
| dhrystone 用时（150 万周期，同机交替测） | 8.03 s | 7.62 s（快约 5%；相对重构前 595e4a7 的 8.8 s 快约 14%） |
| bridge 占用时 | 约 8% | 约 4% |
| 指令译码 | IDU、bridge 各一份 | 一份 `decode_inst` |
| 检查点格式解析 | trace-model 与 function-model 各一份 | 只在 function-model |
| 源码行数（.cpp/.h，不含 third_party / function-model） | 30256 | 30039 |

## 过程中发现的问题

- `BackTop::get_reg` 一直返回 0，程序非零退出码从未报出。改为读功能模型的 a0 后重跑门禁，没有程序非零退出。
- `function-model/tools/ckpt2stub.py` 读 format 5 检查点时目标 pc 算成 0x0，前门恢复程序会跳到 0；与本次改动无关（同一恢复程序在新旧两版上行为相同），另开任务修。
- 提交时的设备写（`commit_sync → on_commit_store`）保留为环境动作：RTL 测试平台也在提交周期做（rtl/docs/modules/soc_top.md），它在同一个 back.comb 里影响中断注入，改成端口会晚一拍。

## 双线程评估（未做）

按阶段计时（dhrystone）：back.comb 49%、front.comb 31%（BPU 11%）、各 seq 约 12%。同一周期里前端到后端有三条真实组合路径（PTAB 旁路 + f2b 旁路、BPU 当拍算出的提交额度、I-cache 请求经 LLC 影响访存响应），周期不变前提下只有 seq 能并行，净收益约 3%；先拆 BPU comb 上限约 1.2 倍。数据在 `AI-Huma-data/tm-simplify/dhry/phases_319e69b.txt`。

## 和 RTL 的关系

`include/config.h` 未改，生成的 `ttg_cfg_pkg.sv` 不变；周期不变，`rtl/scripts/ref_cycles.txt` 不变。rtl 里有几处注释仍写 `rv_simu_mmu_v2.cpp`（`rtl/tools/gen_soc_top.py`、`rtl/docs/modules/*.md`），未改。

## 验证（rv64）

每个提交：RVC=0 门禁 62/62、RVC=1 门禁 67/67，周期等于基线；`comb_graph.py --check` 0 隐患、0 声明不一致；FPR（rvc-alu / rvc-mem / fd-rvc-mem / rvc-flow）逐字节相同；`TB_TRACE_COMMIT`、`LSU_PIPE_EVT` 与上一版逐字节相同。rv64gc Linux（2 亿周期）控制台在 9caaeb6、319e69b、69e6b87、9f60d17、a127371 上都与基线相同。检查点路径：功能模型生成的 dhrystone 特殊检查点（第 30 万条指令，后门和前门恢复）和 rv64 Linux 特殊检查点（第 4000 万条指令，后门恢复跑 300 万条指令、2,126,672 周期）输出与上一版相同（只差恢复时的提示信息）。SPEC 检查点未在服务器上验证。

## 注意

trace-model 现在需要 function-model 的新 API：`function-model` 子模块指针一起更新到 `55affa0`。在本地用 trace-model 默认的 `./function-model` 链接编译时，该目录要在 `55affa0` 或之后（或用 `REFCPU_LIB` / `REFCPU_INC` 指向新编的库和头文件）。
