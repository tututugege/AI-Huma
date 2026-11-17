# trace-model 模块整理：TLB、CSR、PhysMemory、Dispatch、Rename、ROB、LSU（2026-11-17）

trace-model 分支 `exp/global-sched` 在上次合入（main `83af731`，见 [TM_GLOBAL_SCHED.md](TM_GLOBAL_SCHED.md)）之后又做了 10 个提交，再加一个文档提交（`f1cfb1d`），合并进 trace-model main，合并提交 `e971e79`（main 上另有中文文档提交 `d8aef0a`，与本分支不改同一文件，故用合并提交而不是快进）。每一步周期都与基线逐一相同。trace-model 里的说明：`docs/MODULE_CLEANUP.md`。

## 提交

| 提交 | 内容 |
| --- | --- |
| 0d85e4a | TLB 归使用者所有：LSU 的 DTLB、I-cache 的 ITLB 改为普通成员，不再用指针、不再懒创建；删掉一直绑定着的指针判空 |
| 3db6de5 | 删掉 PhysMemory：功能模型 core 实例由 `driver/RefCore` 管理；设备寄存器改为 `IoBacking`；地址判断移到 `mmio_address_map.h` |
| 5680dca | Dispatch 拆出的 uop 只拷贝自己的动态位（池条目本来就是指令那份的拷贝） |
| 9033d61 | CSR 写入改在提交时由 ROB 给出（CSR 编号、命令、事实里的值），删掉执行时锁存和 `ExeCsrIO / TopCsrIO`；先让新旧并存逐次比较，0 次不一致 |
| d4c1787 | CSR 文件成为 `SimCpu::csr`，全 CPU 通过 `csr_state()` 只读访问；删掉一路传递 `csr_status` 的端口和各模块的 CSR 指针 |
| cd729be | Dispatch 一遍派发：先决定是否发出再放请求，不再"放出去再收回"；发给 LSU 的请求只带 id |
| 3cfd37e | Rename：整数和浮点共用一个 `RenDomain`；ROB：队头只扫描一遍，只拷贝真正提交的槽，`comb_redirect` 拆成两段 |
| ae74f7a | TLB 重写为一个 `comb()` 加一个 `seq()`；请求和响应变薄；页表遍历端口改为普通结构体，删掉虚函数接口和适配器 |
| 648c309 | LSU：LSU_MS_DATA 的状态挪到旁路数组；LDQ 表项不再存和 uop 池重复的字段 |
| 8c80c1f | LSU：长函数按用途拆开命名；`RealLsuPipe.h` 开头加 pcur/pnxt 读法说明和缩写对照表 |

## 结果

| | 合入前 83af731 | 合入后 |
| --- | --- | --- |
| 源码行数（.cpp/.h，不含 third_party / function-model） | 30070 | 29096 |
| TLB 加页表遍历端口 | 约 900 行，三层函数、8 个结构体、5 个入口 | 382 行，一个 comb 一个 seq |
| CSR 状态 | 后端模块，经端口传到 LSU、前端、I-cache | SimCpu 成员，`csr_state()` 只读访问 |
| Rename | 整数、浮点各一份 | 共用一个模板 |
| 周期 | | 与合入前逐一相同 |

## 验证（rv64gc）

- 每个提交：RVC=0 门禁 62/62、RVC=1 门禁 67/67，TB 一致，`comb_graph.py --check` 通过（调度仍为 48 个阶段、25 个模块）。
- 每一两步一次完整比对（`vbin.sh`）：FPR、TB / LSU 轨迹、Linux 检查点、FE_PAIR / FE_IPF 全部相同。
- 每一两步跑一次 13 个 Linux 窗口（`linux_segments_cmp.sh`，复用 main-check 的 RTL 输出，只重跑模型一侧）：每次都是 13/13 PASS，且模型指纹和上一步逐字节相同。
- TLB 与 LSU：开启分页的 Linux 检查点上，LSU 逐拍事件打印（含每拍每个 DTLB 请求的结果和物理地址）md5 与改动前相同。
- Dispatch、Rename / ROB、LSU：dhrystone、memory-stress-small、Linux 检查点三处的 PMU 输出（事件、直方图、按 PC 统计）逐字节相同。
- rv64gc Linux 2 亿周期控制台（`scripts/linux_check.sh`，8c80c1f）：登录成功、无 oops / panic，输出与合入前（cb80789）逐字节相同，包括进度标记的位置。

## 和 RTL 的关系

`include/config.h` 未改，`ttg_cfg_pkg.sv` 不变；周期不变，`rtl/scripts/ref_cycles*.txt` 不变。RTL 测试平台使用自己的冻结副本 `rtl/tb/soc/platform`（含 PhysMemory），不受影响。

## 没做的

- LSU：每一步注明读 `pcur` 还是 `pnxt`，并在调试构建下检查（建议在下次改 LSU 之前做）；彻底去掉 `pnxt`（不建议：同拍依赖都要改成具名线信号，收益只是写法统一）。
