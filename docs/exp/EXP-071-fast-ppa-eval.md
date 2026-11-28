# EXP-071 四层快速 PPA 评估体系（Tier 0 ~ Tier 2b）设计与实测标定

- **日期 / 分支 / 状态**：2026-11-28；总仓库 `main`、`rtl` `main`（`6c42731`）；**已合入 `main`**
- **开关与默认关闭回归**：无微架构、CSR 或周期逻辑改动（`rtl/rtl/*` 零变更）；仅新增工具脚本与评估文档，默认仿真/综合门禁零影响

## 1. 问题与目标

Synopsys DC（`compile_ultra` + TSMC 28nm HPC+）单次签核综合耗时 `0.7–4.4 h`（如 `front_top` `15,774 s`、`lsu` `9,645 s`、`isu` `8,425 s`），无法在构想筛选和日常 RTL 迭代阶段快速给出 **面积（含真实 SRAM 宏与 Padding 开销）+ 时序（WNS / Fmax / 关键路径）** 反馈。本工作在不改动 RTL 的前提下搭建并实测标定了一套分四层的快速 PPA 评估体系，并在 `rtl` `0dceb0d` 基准上以既有 Tier 3 `compile_ultra` 结果为 Ground Truth（GT）量化精度与加速比。

## 2. 四层评估方案架构与工程修复

| 层级 | 工具链路 | 脚本入口 | 适用时机 | 关键实现与工程修复 |
|---|---|---|---|---|
| **Tier 0** | Analytical 零 RTL 公式模型 / `yosys-slang` 仅展开层次 | [scripts/ppa_est.py](../../scripts/ppa_est.py)（经 `fast_ppa.sh --tier 0\|0-elab`） | 改设计前 / 调 SRAM 参数 1 秒内 | 直接在 `eda` 读取 11 颗 TSMC 28nm SRAM `.lib` 面积与 `CLK->Q + setup` 下界，按 `ttg_sram_1rw`/`1r1w` 真实拼装规则算宏颗数与 Padding 浪费比；`elab` 模式仅跑 `read_slang + hierarchy + stat` |
| **Tier 1** | `Yosys`（TSMC28 LVT + 真实 SRAM）→ `buf_high_fanout` → Synopsys `PrimeTime` | [run_tier1_yosys_pt.sh](../../rtl/scripts/run_tier1_yosys_pt.sh)、[buf_high_fanout.py](../../rtl/scripts/buf_high_fanout.py) | **日常改 RTL 主力评估（1–12 分钟）** | ① `dfflegalize + techmap + dfflibmap` 置于 `abc` 前消除带使能触发器引脚不兼容；② `abc -constr` 须使用组合缓冲单元 `BUFFD1BWP12T40P140LVT` + `buffer,-p,-N,16,-S,80`；③ `setundef -zero -undriven` + `splitnets` + `write_verilog -simple-lhs` 消除 PT 解析 `'x` 报错；④ `buf_high_fanout.py` 对 post-ABC 高扇出线网与宏引脚插分级缓冲树，消除了 `bpu` `BWEB` 等数百扇出假违例（`bpu` WNS `−6.50 → −1.99 ns`） |
| **Tier 2a** | Synopsys DC 快速综合（`dc-ultra-relax`） | [run_tier2_dc_fast.sh](../../rtl/scripts/run_tier2_dc_fast.sh) | 需 `<1%` 精准含真宏面积或导出 `.ddc` | 以 `5.00 ns` 宽松时钟运行 `compile_ultra -no_autoungroup -no_boundary_optimization -no_design_rule`，再切换回目标时钟 `update_timing` 报时序并导出 `<mod>.ddc`；预热复制 `alib-52` 至节点本地 `/tmp` 消除 `$HOME` NFS 锁争用；非 SoC 核心模块过滤 `/rtl/soc/` 消除 `soc_axi_checker.sv:16` `string`（`VER-700`/`VER-518`）报错 |
| **Tier 2b** | Synopsys DC 自底向上 `.ddc` 增量拼装 | [run_tier2b_dc_inc.sh](../../rtl/scripts/run_tier2b_dc_inc.sh) | 只改前端胶水或单一子模块（`bpu` / `icache`） | 预加载 `bpu.ddc`（`20M`）与 `icache.ddc`（`18M`）并设 `set_dont_touch`，过滤非包子模块源码仅重编 `front_top` 胶水逻辑 |

- **统一入口**：[rtl/scripts/fast_ppa.sh](../../rtl/scripts/fast_ppa.sh) 统一封装 Tier 0 ~ Tier 2b CLI，支持 `--host eda-XX` 自动 SSH 分发，并显式拦截在无 `/eda-tools/pdk/TSMC28` 主机（如 `iprc-jump`）或 `login-inband` 上直接执行重综合任务。

## 3. 全量实测对比结果（vs Tier 3 `compile_ultra` GT）

全部原始与汇总输出位于 `eda` 集群 NFS `/nfs_global/S/houruyao/fast_ppa_eval/`（汇总文件 `summary_report.txt` 由 `scripts/summarize.py` 从磁盘报告直采生成）。

### 3.1 分模块耗时、加速比与 PPA 精度

| 模块 (`clk_ns`, 模式) | GT 时间 / TotalArea / WNS / Fmax | **Tier 0** Ana / Elab / TotalArea(误差) | **Tier 1 (`Yosys+PT`)** 时间(提速) / TotalArea(误差) / WNS / Fmax (`GT/T1`) | **Tier 2a (`dc-ultra-relax`)** 时间(提速) / TotalArea(误差) / WNS* | **Tier 2b (`front_top_inc`)** |
|---|---|---|---:|---:|---|
| **`tlb_mmu`** (`0.50`, `bb`) | `2527 s` / `94,793.5` / `−0.03` / `1.887 GHz` | `0.01 ms` / `0.45 s` / `94,793.0` (`−0.0%`) | **`52 s` (`48.6×`)** / `68,494.3` (`−27.7%`) / `−0.31` / `1.235 GHz` (`1.53`) | `319 s` (`7.9×`) / `59,682.2` (`−37.0%`) / `−3.37` | — |
| **`ftq_ibuf`** (`0.50`, `bb`) | `4878 s` / `239,315.2` / `−0.15` / `1.538 GHz` | `0.00 ms` / `0.41 s` / `239,315.0` (`−0.0%`) | **`175 s` (`27.9×`)** / `329,629.4` (`+37.7%`) / `−0.60` / `0.909 GHz` (`1.69`) | `2393 s` (`2.0×`) / `218,098.6` (`−8.9%`) / `−3.98` | — |
| **`isu`** (`0.50`, `none`) | `8425 s` / `467,899.3` / `−0.23` / `1.370 GHz` | `0.00 ms` / `10.94 s` / `467,899.0` (`−0.0%`) | **`331 s` (`25.5×`)** / `526,654.3` (`+12.6%`) / `−0.39` / `1.124 GHz` (`1.22`) | `1617 s` (`5.2×`) / `389,676.3` (`−16.7%`) / `−3.26` | — |
| **`lsu`** (`0.50`, `none`) | `9645 s` / `767,221.2` / `−0.39` / `1.124 GHz` | `0.00 ms` / `9.76 s` / `767,221.0` (`−0.0%`) | **`705 s` (`13.7×`)** / `1,052,504.4` (`+37.2%`) / `−0.87` / `0.730 GHz` (`1.54`) | `2834 s` (`3.4×`) / `621,212.1` (`−19.0%`) / `−4.48` | — |
| **`icache`** (`0.65`, `real`) | GT 子实例：`1,716,827.7`（`256` 宏） | `0.01 ms` / `0.68 s` / `1,716,558.3` (`−0.0%`, `Pad 4.00x`) | — | `2245 s` / **`1,713,504.4` (`−0.2%`)** / `−4.33` | 复用 `.ddc`（`0.00%` 漂移） |
| **`bpu`** (`0.65`, `real`) | `a1a2` (`156`宏)：`4523 s` / `2.076M` / `0.877G`<br>HEAD(`180`宏)：`2,395,127.6` | `0.02 ms` / `4.15 s` / `2,404,871.8` (`+0.4%`, `180`宏) | **`235 s` (`19.2×`)** / `2,504,493.7` (`+4.6%`, `180`宏) / `−1.99` / `0.379G` (`1.75`) | `2320 s` (`1.9×`) / **`2,391,605.1` (`−0.1%`, 逻辑−0.9%)** / `−4.35` | 复用 `.ddc`（`0.00%` 漂移） |
| **`front_top`** (`0.65`, `real`) | `15774 s` (`4.38 h`) / `4,229,477.7` / `−0.86` / `0.662 GHz`（`436`宏） | `0.02 ms` / `5.39 s` / `4,233,430.1` (`+0.1%`, `436`宏) | **`463 s` (`34.1×`)** / `4,372,183.6` (`+3.4%`, `436`宏) / `−2.64` / `0.304G` (`2.18`) | `4593 s` (`3.4×`) / **`4,205,649.1` (`−0.6%`)** / `−4.35` | **`1982 s` (`8.0×` 仅拼装)** / **`4302 s` (`3.7×` 改 bpu+拼装)**<br>`4,208,780.9` (`−0.5%`, `436`宏) / `WNS −5.85` |

> **说明**：`Tier 0 Analytical` 的纯逻辑+FF 面积基于既有同类模块面积权重估算；`Tier 0` 的 SRAM 宏数量（`180`/`256`/`436`）、Macro 面积（`2,019,486.8`/`1,476,358.3`/`3,495,845.1`）与 Padding 倍率均由真实 `.lib` 与配置/RTL 展开直接导出，误差 `0.000%`。

### 3.2 汇总精度、负向对照与链路校验

- **Tier 1 (`Yosys + PrimeTime`) 统计（`n=6`）**：全流程耗时仅 `52–705 s`（**提速 `13.7×–48.6×`**）；总面积 `MAPE = 20.5%`、**`Spearman(Area) = 1.000`**、**`Spearman(Fmax) = 0.929`**，缩放系数稳定为 **`Fmax_GT / Fmax_Tier1 = 1.65 ± 0.29`（CV = `17.6%`）**；`PT_LINK_STATUS=1`、未映射单元 `0`、`$mem_v2` `0`。`reg->reg` 分组 `WNS_r2r` 为 `tlb_mmu −0.28`、`isu −0.38`、`ftq_ibuf −0.56`、`lsu −0.87`、`bpu −1.99`、`front_top −2.13`。
- **Tier 2a (`dc-ultra-relax`) 统计（`n=6`）**：提速 `1.9×–7.9×`；`MAPE(TotalArea) = 13.7%`、**`Spearman(Area) = 1.000`**、`Spearman(Fmax) = 0.829`；含真宏前端模块总面积误差仅 **`−0.1% ~ −0.6%`**。纯逻辑模块因 `5.00 ns` + `-no_design_rule` 选用最小驱动 SVT D1 单元，纯逻辑面积偏小（`−8.9% ~ −37.0%`）且回放时序 `WNS*` 偏悲观（`−3.26 ~ −4.48 ns`），仅适用于精准面积估计与结构瓶颈定位。
- **Tier 2b (`front_top_inc`) 校验**：`DC_LINK_STATUS=1`、`VER_ERR=0`、`436` 宏零丢失、`u_pred_path/u_bpu`（`2,391,605.1`）与 `u_icache`（`1,713,504.4`）面积与输入 `.ddc` 误差 **`0.00%`**（`set_dont_touch` 有效），总面积 `4,208,780.9`（`−0.5%`）。
- **负向实测记录（Synopsys DC `W-2024.09-SP2`）**：
  1. `compile -map_effort low` 已废弃（`OPT-1303` 自动回退 `medium`）：`tlb_mmu dc-low` 运行 `26m36s+` 仍未结束且面积膨胀至 `139,774.7`（`WNS −0.28`）；`bpu dc-low-relax` 在 `2.00 ns` 下 `12m30s+` 仍卡单线程 Pass 1，均已中止。
  2. `compile_use_low_timing_effort` 已被忽略（`INFO-100`）；紧约束 `tlb_mmu dc-ultra-fast`（`0.50 ns`）运行至 `28m30s` 仍未收尾（`area=85,318.6, WNS −0.10`），较 GT `42m` 提速不足 2 倍，证明现代 DC 只有放松约束或转 Tier 1 才能获得数量级提速。

## 4. 复现命令与日常推荐使用工作流

```bash
# 1. 调 SRAM / 表项参数前（<1s）：在 iprc-jump 自动转发至 eda 看宏颗数、面积、Padding 浪费与访问下界
bash rtl/scripts/fast_ppa.sh --tier 0 --mod all --host eda-05
bash rtl/scripts/fast_ppa.sh --tier 0-elab --mod front_top --host eda-05

# 2. 改 RTL 后日常主力评估（1–12 min，提速 14x-49x）：看面积变化、关键路径与按 1.65x 估算 Fmax
bash rtl/scripts/fast_ppa.sh --tier 1 --mod front_top --host eda-05

# 3. 需验证含真宏精准面积或局部重编拼装（~30–76 min）：Tier 2a / Tier 2b
bash rtl/scripts/fast_ppa.sh --tier 2a --effort dc-ultra-relax --mod bpu --host eda-06 --out /nfs_global/S/houruyao/out/bpu_relax
bash rtl/scripts/fast_ppa.sh --tier 2b --mod front_top --bpu-ddc ... --icache-ddc ... --host eda-06 --out /nfs_global/S/houruyao/out/ft_inc
```

**结论**：日常优化建议采用 **「Tier 0 预筛宏与 Padding → Tier 1（Yosys+PT）分钟级 RTL 迭代与排序 → Tier 2a/2b 确认含真宏前端精准面积与拼装 → 合入 `main` 前跑 Tier 3 `compile_ultra` 签核」** 的四层工作流，详细对比表与脚本口径同步见 [../../rtl/docs/09-synthesis-report.md](../../rtl/docs/09-synthesis-report.md) §22 与 [../SERVER.md](../SERVER.md)。
