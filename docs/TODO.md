# 待办事项

全项目唯一的待办清单（2026-11-05 起，原 rtl `docs/07-roadmap.md`、README “下一步” 中仍有效的条目已并入）。
每条写清为什么、做到什么算完；做完删掉，在 [LOG.md](LOG.md) 里留一行。风险（验证缺口、变异存活）记在 [rtl/docs/08-risk-register.md](../rtl/docs/08-risk-register.md)，不在这里重复。

## 进行中

| 事项 | 状态 | 做完的标准 |
|---|---|---|
| LD/STA IQ 合并、统一 FTQ 的 RTL 试做结果入档 | 两个 RTL 试做都已完成（工作区 `rtl-ldsta`/`trace-model-ldsta`、`rtl-uftq`/`trace-model-uftq`，未提交）：门禁 66/66，66 个程序周期与各自的 trace-model 全部一致 | 在 [EXPLORATION.md](EXPLORATION.md) 记为新实验（含综合数字和未覆盖项）；工作区改动提交到各自的 `exp/` 分支 |

## 待做：验证

| 事项 | 为什么 | 做完的标准 |
|---|---|---|
| **逐条对比加上 store 比较**（rtl V-12） | 现在只比提交 PC 和目的寄存器。第 1 批的 MMIO store 数据错误（串口乱码、中断不来）逐条对比没报，是靠比串口输出发现的；之后还要动 LSU 端口和 LD/STA 合并 | `tb/soc/fm_check.h` 在每条 store 提交时比较物理地址、数据、字节使能（MMIO 和可缓存都比）；门禁重跑通过；再考虑 CSR 写值 |
| RTL 断言 | RTL 里几乎没有 assert；统一 FTQ、LD/STA 合并新加的断言因为测试平台不带 `--assert` 从未执行过 | 测试平台默认带 `--assert`，断言失败算门禁失败；模块笔记里的“假设/不可达”都有对应断言 |
| 闭环补跑 `memory-stress`、`float_test`；扩大 gate | 现在的 gate 程序都很小（最长 23 万周期） | 两个程序在 RTL 逐条对比通过；gate 加入更长的定向程序 |
| 去复位存储器的随机初值验证 | 测试平台用 `--x-initial 0`，会掩盖对初值的依赖 | `--x-initial unique` + 运行时随机，门禁通过 |
| 定向短测试补已知覆盖缺口 | front_top：RET 判定 `imm≠0`、SFENCE.VMA 后取指、冲刷与存储侧请求同拍；peripheral AXI 路径、PTW 超级页与 PTE 故障、MSHR_HIT/FULL 路由响应，真实程序基本不走 | 每个缺口一个短程序，进门禁 |
| 覆盖率 | 没有覆盖数据，不知道哪些逻辑从未被测到 | Verilator toggle 覆盖（line 覆盖对 assign 风格无意义），每模块出报告，汇总数字入库 |
| LD/STA 合并、统一 FTQ 的规模确认 | 都只在小程序和 gate 上测过；store 密集程序、48 还是 64 项都没定 | quick SPEC 上对比；决定是否进入主线 |

## 待做：RTL 实现

| 事项 | 为什么 | 做完的标准 |
|---|---|---|
| AMO 改为“特殊 store、在 DCache 里读改写”（BOOM/香山式） | 现在 AMO 和 C910 一样拆成 LOAD + STA + STD（运算在 STD 里，rd=x0 借 32 号寄存器），同时占 LDQ 和 STQ；LD/STA 队列合并后一条 AMO 要在同一拍进 MEM 队列两次，dispatch 为此专留了一条通路（暂时保留这种做法） | trace-model 和 RTL：AMO 只占 STQ（一个地址 uop + STD），在 STQ 头、ROB 已排空时发给 DCache，DCache 流水线内做读改写（AMOALU），旧值经写回口送 rd；dispatch 的 AMO 双写口通路删除；门禁和 Linux 通过。可与 LD/STA 共享 AGU 一起考虑 |
| 统一 FTQ 的提交读口按块读 | 统一 FTQ 现在每条提交指令一个读口（PC 8 口 + 元数据 8 口，各从 64 项×8 槽里选），是 `ftq_top` 面积的大头。trace-model 统计（2026-11-05，SPEC 6 个最大权重点 + 5 个小程序）：一拍提交跨的 FTQ 块数超过 4 的周期最多 0.06%，超过 3 的在 gcc 上有 9.5% | decode 组队时限制一组最多跨 K 个块（trace-model IDU 与 RTL `pre_idu` 同步，参数 `CFG_DECODE_MAX_BLOCKS`，建议 K=4）；`ftq_top` 提交读口改为从 commit 指针读 K 个连续块整行再按块号/偏移选；quick SPEC 比较 K=3/4；RTL 门禁 66/66、周期与 trace-model 相等；提交读口选择器预计元数据 −44%、PC −50%（K=4） |
| 删除分开式结构里的 `altpcpn` 存储 | BPU 训练从不读它（EXP-007 补上标准 TAGE 的备选更新也无收益）；现在 PTAB、front2back、后端 FTQ 每个槽都白存 3 位 | trace-model 与 RTL 删掉这份存储和连线，周期不变（门禁 66/66、gate 62/62 逐个相同）；统一 FTQ 若合入则随之消失 |
| `front_stall` 接回 | core_top 里写死为 0；BPU 更新队列会满时必须接回 | 接回后门禁通过，有触发它的测试 |
| LLC 旁路写、部分行写 miss | 未实现（断言保留）；随机流量会触发，真实程序不走 | 实现并通过随机流量测试 |
| RealLsu 手写结构 | 3 个脚本生成的 SSA 展开文件（约 890 行）应改为手写结构 | 改写后门禁通过 |
| 整数组次态写法排查 | `isu_iq_store`、`rob_store`、`dispatch`、`idu` 里是否还有整数组次态写法未核实 | 逐个确认或改写 |
| `axi_subsys` 的 UNOPTFLAT | `axi_llc.in_w` 经结构体的组合环，`lint.sh` 对它只做规范检查 | 确认是误报还是真环，消除后纳入 `-Wall` |
| 端口样板由 spec 生成；非压缩数组端口统一 | `axi_llc`/`axi_interconnect`/`axi_subsys`/`mem_axi` 端口仍是非压缩数组 | 生成器覆盖这些模块 |

## 待做：流程与工具

| 事项 | 为什么 | 做完的标准 |
|---|---|---|
| 性能计数（PMU）专项 | 探索要靠队列占用、端口使用、阻塞原因统计。现在只有 trace-model `exp/area-explore` 上的 ArchStats（`ARCH_STATS=1`），夹杂实验专用的东西，暂不进 main | 统一的计数器框架：trace-model 和 RTL 都有（RTL 可对应 HPM CSR）、关闭时周期不变；以 ArchStats 的统计项为起点 |
| 时序综合流程 | MAIN_RECORDS 要求记 WNS，但现在只有 yosys 通用门面积代理，没有工艺库、时序约束和静态时序分析；整机面积推算也只在旧配置下做过（第 3 批只综合了受影响模块） | 选定开源工艺库（如 ASAP7/Nangate45）+ 约束频率，主要模块能出面积和 WNS；整机推算可按需重跑 |
| SPEC 检查点生成提速 | 生成检查点要把整个程序顺序再跑一遍（sjeng 约 3.7 小时，单线程） | BBV 时顺带存粗粒度检查点，生成 SimPoint 检查点时从最近的粗检查点并行起跑 |
| `/tmp` 里的其他生成数据 | Linux 特殊检查点 `/tmp/ckpt`、综合中间结果等重启会丢（SPEC 检查点已因此丢过一次） | 挪到 `~/personal/AI-Huma-data/`，文档写明位置和生成命令 |
| 远程仓库 | 子模块 URL 还是本地相对路径 | 配好总仓库和三个子仓库的远程地址，改子模块 URL；推送由用户决定 |
| trace-model 剩余小优化 | 每项不到 3%；状态标志整理 | 逐项做，gate 周期不变 |
