---
name: ai-huma-eda
description: >-
  Use this skill whenever running large-scale tests, SPEC06 evaluations, multi-config DSE,
  long RTL/Linux simulations, or large-module synthesis on the iprc-jump and eda compute cluster,
  or when cross-compiling binaries from iprc-jump for eda nodes.
---

# AI-Huma 集群与大规模测试指南（iprc-jump + eda）

完整权威说明见 [docs/SERVER.md](../../../docs/SERVER.md)。本机只做日常编辑、lint 和小规模 gate；所有大规模评估统一上 `eda` 集群。

## 1. 节点拓扑与分工

```text
本机 / WSL ──▶ iprc-jump (100.116.179.124) ──▶ login-inband (10.208.120.12) ──▶ eda-00 ~ eda-10
```

- **`iprc-jump`**（9950X3D，16C/32T，60 GiB）：跳板机，用于短编译、快速构建与静态打包。根盘余量有限（约 90 GB），勿长期堆积大产物。
- **`login-inband`**（`10.208.120.12`）：仅用于中转、查看 NFS、分发任务；**禁止跑重任务**。
- **`eda-04` ~ `eda-10`**：挂载 `/nfs_global/S/houruyao`（注意 **`eda-01` ~ `eda-03` 不挂载 `/nfs_global`**）。大任务优先在 `eda-04` ~ `eda-10` 间平摊。

## 2. 选节点与连接前检查

1. **WSL Tailscale 冷启动预热**（自动化脚本开头必加）：
   ```bash
   for i in $(seq 1 15); do
     tailscale ping -c 1 --timeout=2s 100.116.179.124 >/dev/null 2>&1 && break
     sleep 1
   done
   ```
   同步源码用 `rsync -az` 或 `tar -czf` + `scp`，不要用 `tar | ssh` 管道。

2. **起任务前先通过 `login-inband` 一次性并行查 `eda-04` ~ `eda-10` 负载与空闲内存**（`04`~`10` 默认都挂 `/nfs_global`，无需反复测 NFS；不要在本机串行三跳 `ProxyJump`）：
   ```bash
   ssh -o ConnectTimeout=5 -o BatchMode=yes login-inband 'for n in eda-04 eda-05 eda-06 eda-07 eda-08 eda-09 eda-10; do
     (out=$(ssh -n -o ConnectTimeout=3 -o BatchMode=yes $n "uptime | sed \"s/.*load average/load/\" | tr -d \"\n\"; free -g | awk \"NR==2{printf \\\" avail=%sG\\\", \\\$7}\"" 2>/dev/null) || out="unreachable"
      echo "$n: $out") &
   done; wait' | sort
   ```
   - **派发原则**：从 `eda-04` ~ `eda-10` 中挑空闲节点，**在不 OOM 和不过载的前提下尽力多发**（`mcf` / `gcc` 单进程约占 3 GB RSS，按可用内存与剩余核数给足 `-P` 并发度并跨节点平摊）。

## 3. 跨机编译红线（`iprc-jump` → `eda`）

- **指令集兼容**：`iprc-jump` 是 AMD Zen 5，`eda` 是 Intel Xeon Cascade Lake。编译给 `eda` 跑的程序必须把 `-march=native` / `-mtune=native` 改为 **`-march=x86-64-v3 -mtune=generic`**，否则触发 `SIGILL`。
- **glibc 兼容**：`iprc-jump`（Ubuntu）glibc 高于 `eda`（CentOS 7 / Rocky），给 `eda` 的二进制必须**静态链接**（`-static`），或拷源码到 NFS 后直接在 `eda` 节点编译。
- **Verilator 路径**：`iprc-jump` 非交互 SSH 不读 `~/.bashrc`，构建 RTL TB 前必须显式：
  ```bash
  export PATH="$HOME/rv64spec/verilator_src/bin:$PATH"
  ```
  （使用 5.052，系统 `/usr/bin/verilator` 5.020 编不过。）
- **Python 兼容**：`eda` 节点默认 `python3` 是 **Python 3.6.8**，脚本中禁止使用 `:=`、`match` 等 3.8+ 语法。

## 4. NFS 关键目录与 SPEC06 运行口径

- **SPEC06 rv64gc（535 点，标准 386 点表 `jobs95.txt`）**：`/nfs_global/S/houruyao/spec06_rv64gc/`
  - 可执行文件放 `tm/bin/<sim_name>`
  - 结果输出放 `tm/res_<tag>/`（不要留在 `/tmp`，节点重启会清空）
  - 汇总脚本：`tm/cmp_ev5.py`、`tm/agg_spec.py`
- **Linux 检查点库（26 段，每 5M 指令）**：`/nfs_global/S/houruyao/linux_ckpt_rv64gc/`
- **已有基线不重跑**：先查 `docs/MAIN_RECORDS.md`、`docs/EXPLORATION.md` 及 `/nfs_global/S/houruyao/spec06_rv64gc/tm/res_*`。
- **默认开 `PMU=1`**：每次跑 SPEC 必带 `PMU=1`，输出带 TMA 一级指标。
- **DRAMsim3 并发隔离**：必须传 `DS3_CONFIG=<ini>`，且每个并发 worker 分配独立的计算节点本地 `/tmp/<tag>_ds3out_$$` 作为 `DS3_OUT`，用完立即删除，避免拖慢或写满 NFS。
- **后台分片启动模板**：
  ```bash
  ssh eda-06 'cd /nfs_global/S/houruyao/spec06_rv64gc/tm && \
    (setsid nohup sh -c "xargs -P 32 -L 1 bash ./<run_one>.sh < <jobs_part>" > <tag>_eda06.log 2>&1 < /dev/null &)'
  ```
- **检查进度**：
  ```bash
  ssh login-inband 'cd /nfs_global/S/houruyao/spec06_rv64gc/tm && \
    find res_<tag> -name "*.res" | wc -l; \
    [ -f res_<tag>/fail.txt ] && wc -l res_<tag>/fail.txt'
  ```

## 5. 集群综合工具（Yosys 与 Synopsys DC）

- **快速代理综合（Yosys + `yosys-slang`，默认首选）**：已部署到 NFS，所有 `eda-04` ~ `eda-10` 直接可用，无 glibc 兼容问题：
  ```bash
  export PATH="/nfs_global/S/houruyao/tools/oss-cad-suite/bin:$PATH"
  export SLANG="/nfs_global/S/houruyao/tools/oss-cad-suite/share/yosys/plugins/slang.so"
  SYNTH_ABC="strash;balance;map" JOBS=2 bash scripts/synth_depth.sh <tag> <module...>
  ```
  **避坑**：
  - 务必传 `SYNTH_ABC="strash;balance;map"`（不要用 `synth_depth.sh` 默认带 `dc2` 的 `SYNTH_DEPTH=1`，`dc2` 会把加法器/比较器重写成长串行进位链，导致算术逻辑级数虚高 2~4 倍）。
  - 综合多写口大存储模块（`bpu`、`front_top`、`dcache`、`mem_top`）时必须加 **`SYNTH_NO_MEMPRIO=1`**，跳过 `memory -nomap` 里 $O(W^2)$ 卡死的 `opt_mem_priority` 子 pass。
  - 临时工作目录放节点本地 `/tmp`，结果（`.stat` / `.ltp`）拷回 NFS；遵守 `WORKFLOW.md` §7.5（最多 2 并发，大模块一次 1 个，不与 Verilator 并发）。
- **工艺库时序综合（Synopsys DC `W-2024.09-SP2`，需要真实 WNS / 面积 / 功耗 时使用）**：
  - 环境初始化：`source /eda-tools/modulefiles/init.sh && export PATH="/eda-tools/synopsys/syn/W-2024.09-SP2/bin:$PATH"`
  - 常用 PDK（`/eda-tools/pdk/`）：TSMC 28nm HPC+ 标准单元库位于 `/eda-tools/pdk/TSMC28/digital/Front_End/timing_power_noise/NLDM/tcbn28hpcplusbwp12t40p140_180a/`（如 `ssg0p81v125c.db` / `tt0p9v25c.db`），另有 `TSMC40`、`HL28`、`OpenRPDK28`、`s12LGP`、`NanGate 15nm` 等。

## 6. 算分与回退判据

- **程序内 CPI（调和加权）**：$\text{CPI} = \sum w_i' \cdot (\text{cycles}_i / \text{insts}_i)$，$\text{IPC} = 1 / \text{CPI}$（禁止对 IPC 直接加权平均）。
- **跨程序汇总**：12 个程序相对基线的加速比取**几何平均**。
- **回退判据**：全量 386 点几何平均 IPC 相对 `main` 低于 **−1.0%** 时，必须查清原因再决定是否合入。
