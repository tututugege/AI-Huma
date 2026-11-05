# AI-Huma 合入 main 记录

每次合入 `main` 追加一行，最新的在最上面。规则见 [WORKFLOW.md](WORKFLOW.md) 第 5.2 节。

- 性能数字来自 trace-model，负载固定：dhrystone（64 次，`rtl/programs/big/dhrystone.bin`）、coremark（2 次迭代，`rtl/programs/big/coremark.bin`）、memory-stress-small（`trace-model/build/tests/memory-stress-small`）。
- 变化百分比相对上一行；正数表示周期变多（变慢）。
- 综合还没做时写"未做"和原因，不留空。

## 记录

| 日期 | 版本（总仓库 / function-model / trace-model / rtl） | 正确性 | dhrystone 周期 (IPC) | coremark 周期 (IPC) | memory-stress-small 周期 (IPC) | RTL 周期 | 综合（工具 / 频率 / 面积 / WNS） | 说明 |
|---|---|---|---|---|---|---|---|---|
| 2026-11-05 | 本行所在提交 / `d40c588` / `08e9cfe` / `52d2b84` | trace-model gate 62/62（基线更新，25 个程序周期变化）；RTL 66 个程序逐条对比 66/66，周期与 trace-model 逐个相等；Linux 从复位启动到 `rv32 login:`：trace-model（约 7–8 千万周期）与 RTL（全程逐条对比，0 不一致，约 3.6 小时）| 150,427 (1.941)，−0.27% | 233,515 (2.305)，+2.87% | 189,128 (5.718)，0 | 与 trace-model 相同 | yosys 通用门面积代理（`rtl/docs/09-synthesis-report.md` 第 9 节）：受影响的 14 个模块 3,723,024 → 2,117,024 个单元（约 −161 万，整机约 17%），触发器 123,595 → 73,873；整机推算未按新配置重做；工艺库、约束频率、WNS：**未做**（没有工艺库和时序流程，见 TODO） | 第 3 批面积配置（EXP-005），见下文“变化”。quick SPEC（6 个程序）IPC 2.216 → 2.204（−0.5%）；coremark 变慢来自在飞分支 32 |
| 2026-11-04 | `6210e46` / `4f99467` / `41a5cdd` / `dc46f6d`（rtl 工作区有未提交修改） | gate 62/62；RTL gate+vm 64 个程序逐条对比一致 | 150,838 (1.935) | 226,991 (2.371) | 189,128 (5.718) | 待补 | **未做**：还没有综合流程（见 README"下一步"第 2 条） | 起始记录（本表从这里开始） |

## 变化

### 2026-11-05 第 3 批面积配置（EXP-005）

第一次按 [WORKFLOW.md](WORKFLOW.md) 第 6 节把架构探索的结论合入 main。

**配置变化**（trace-model `include/config.h` 的默认值；rtl `ttg_cfg_pkg.sv` 由 `make cfg` 生成）

| 参数 | 旧值 | 新值 |
|---|---|---|
| `BACKEND_FETCH_WIDTH` | 16 | 8（= `FETCH_WIDTH`，16 是遗留值） |
| `MAX_BR_NUM`（在飞分支） | 64 | 32（`BR_MASK_WIDTH` 32、`BR_TAG_WIDTH` 5） |
| `IDU_INST_BUFFER_SIZE`（ibuf） | 128 | 64（`FTQ_OFFSET_WIDTH` 3） |
| `FRONT2BACK_FIFO_SIZE` | 32 | 8 |
| IQ INT / LD / STA / STD / BR | 128 / 64 / 64 / 64 / 64 | 64 / 64 / 64 / 16 / 32（共 240 项，原 384） |
| 发射端口 ALU / LD / STA / STD / BR | 6 / 4 / 4 / 4 / 4 | 6 / 4 / 3 / 3 / 2（`ISSUE_WIDTH` 22 → 18） |

**设计改动与修掉的问题**
- trace-model：尺寸改为 `CFG_*` 开关（先以原值提交、周期不变，再单独改默认值）；`IQ_*_SIZE` 标量供 RTL 参数生成器使用。
- rtl：IQ 大小、FIFO 深度、字段位宽（br_mask、br_id、ftq_offset、ready_num）、LSU 通道数、FU 表都改为从配置推出；`gen_cfg_pkg.py` 读前端 FIFO 深度；`dimmap.py` 增加位宽规则。
- rtl 潜在错误：`lsu_core` 的 store MMU 请求端口按 load 端口数声明（两者相等时不暴露）。
- 测试平台错误：按写死的位偏移读 STQ 字段，br_mask 变窄后外设收到错字节（串口乱码、中断不来），逐条对比没有报——现在偏移由配置推出。
- 新脚本：`rtl/scripts/fm_gate.sh`、`lint_chip.sh`、`synth_cfg.sh`；function-model `scripts/spec/`（SPEC 检查点流程）一并合入。

**验证范围**
- 跑了：trace-model gate 62/62、大程序、Linux 到登录；RTL `lint.sh`/`lint_chip.sh` 0 警告、66 个程序逐条对比、Linux 从复位到登录全程逐条对比、原配置下回归（周期逐个不变）；quick SPEC 6 个程序。
- 没跑：full SPEC；RTL 上的 SPEC；时序综合；store 数据仍不在逐条对比范围内（以串口输出对比补充）。

**已知回退**：coremark +2.9% 周期、quick SPEC −0.5% IPC（gcc −1.3%），换取约 17% 的门数和 27% 的触发器。

**对应记录**：[EXPLORATION.md](EXPLORATION.md) EXP-001…005；[LOG.md](LOG.md) 2026-11-05 各行。
