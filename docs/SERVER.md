# 服务器与集群使用说明（iprc-jump + eda 集群）

已停用原阿里云服务器（`47.117.141.194`）和 `fleet.sh` 流程（历史记录见 git 历史与早期 EXP）。当前构建与大规模评估统一使用 **`iprc-jump`（跳板 / 短编译机）+ `eda` 计算集群**，经 Tailscale 与 SSH `ProxyJump` 免密直连。

## 0. 规则

- **分工原则**：
  - **本机**：日常代码编辑、小规模 gate、lint。
  - **`iprc-jump`（9950X3D）**：跳板机，单核与短任务性能极佳，适合平时**短编译、构建、轻量测试与打包**。
  - **`eda` 计算集群（`eda-00` ~ `eda-10`）**：所有**大规模任务**（SPEC06 全量 386 / 535 点、多配置 DSE、长时间 RTL / Linux 仿真、大模块综合）统一在 `eda` 节点上跑。
- **默认带 `PMU=1`**：PMU 不改周期，结果里自带 TMA 数据。
- **已有基线不重跑**：旧配置与当前 `main` 的数字先查 [MAIN_RECORDS.md](MAIN_RECORDS.md)、[EXPLORATION.md](EXPLORATION.md) 以及 NFS `/nfs_global/S/houruyao/spec06_rv64gc/tm/res_*` 中已有的结果目录。
- **不把重任务放登录节点**：`login-inband` 仅用于中转、查看 NFS 和向 `eda-*` 分发任务。
- **存储与清理**：重要结果写入仓库文档；仿真产生的 DRAMsim3 临时目录（`DS3_OUT`）放计算节点本地 `/tmp` 并及时清理，避免把 NFS 写满或拖慢 I/O。`iprc-jump` 根盘余量有限（约 90 GB），不要长期堆积大结果或构建缓存。

## 1. 节点拓扑与 SSH 连接

```text
本机 / WSL ──▶ iprc-jump (100.116.179.124) ──▶ login-inband (10.208.120.12) ──▶ eda-00 ~ eda-10
```

| 别名 | 地址 / 主机名 | 硬件配置 | 角色与用途 |
|---|---|---|---|
| `iprc-jump` | `100.116.179.124`（Tailscale，`ubuntu`） | AMD Ryzen 9 9950X3D（16 核 32 线程）、60 GiB RAM | 跳板机；平时短编译、快速构建、轻量调试 |
| `login-inband` | `10.208.120.12`（`Login-Node2.inband`） | 集群登录节点 | 中转、管理 NFS、分发任务到计算节点 |
| `eda-00` ~ `eda-10` | 内网计算节点（如 `eda-00`） | Intel Xeon Gold 6254（144 线程）、1.5 TB RAM | 大规模 SPEC 评估、并行 DSE、长跑仿真与综合 |

典型 `~/.ssh/config`（需先连入 Tailscale）：

```sshconfig
Host iprc-jump 100.116.179.124
    HostName 100.116.179.124
    User houruyao
    IdentityFile ~/.ssh/id_rsa
    IdentitiesOnly yes
    ServerAliveInterval 30
    ServerAliveCountMax 3
    ControlMaster auto
    ControlPath ~/.ssh/control-%C
    ControlPersist 8h

Host login-inband
    HostName 10.208.120.12
    User houruyao
    ProxyJump iprc-jump
    IdentityFile ~/.ssh/id_rsa
    IdentitiesOnly yes
    ServerAliveInterval 30
    ServerAliveCountMax 3
    ControlMaster auto
    ControlPath ~/.ssh/control-%C
    ControlPersist 8h

Host eda-*
    User houruyao
    ProxyJump login-inband
    IdentityFile ~/.ssh/id_rsa
    IdentitiesOnly yes
    ServerAliveInterval 30
    ServerAliveCountMax 3
    ControlMaster auto
    ControlPath ~/.ssh/control-%C
    ControlPersist 8h
```

配置完成后，`ssh iprc-jump`、`ssh login-inband`、`ssh eda-00` 等均可直接免密登录。

## 2. NFS 共享目录与 SPEC Checkpoint 布局

`login-inband` 与 **`eda-04` ~ `eda-10`** 共享挂载 **`/nfs_global/S/houruyao`**（`eda-01` ~ `eda-03` **不挂载** `/nfs_global`）。

核心评估数据位于 **`/nfs_global/S/houruyao/spec06_rv64gc/`**（12 个 SPEC CPU2006 INT rv64gcb 程序，ref 输入，共 535 个 SimPoint checkpoint，约 57 GB，详细说明见该目录 `README.md`）：

| 路径 | 内容 |
|---|---|
| `spec06_rv64gc/ckpt/<编号.程序>/ckpt_sp<id>_target<N>_warmup1.gz` | function-model 格式版本 5（rv64 + F/D）检查点；保存在 interval N-1 起点（10M 预热 + 10M 测量） |
| `spec06_rv64gc/sp/<程序>.{points,weights,labels}` | SimPoint 编号与权重 |
| `spec06_rv64gc/tools/ckpt2stub.py` | 前门恢复 stub 生成脚本 |
| `spec06_rv64gc/tm/bin/` | 各实验构建好的 `trace-model` 可执行文件 |
| `spec06_rv64gc/tm/jobs95.txt` | 覆盖约 95% 权重的 **386 点**标准评估任务表 |
| `spec06_rv64gc/tm/ds3cfg/configs/DDR4_8Gb_x16_3200.ini` | DRAMsim3 配置文件 |
| `spec06_rv64gc/tm/res_<tag>/` | 各实验的逐点输出（`.res`、`.pmu_*.csv`、`.log.gz`、`fail.txt`） |
| `spec06_rv64gc/tm/cmp_ev5.py`、`agg_spec.py` | SimPoint 调和加权 CPI / IPC 汇总对比脚本 |

### 2.1 可复用 rv64gc Linux 启动检查点库（`/nfs_global/S/houruyao/linux_ckpt_rv64gc/`）

| 路径 | 内容 |
|---|---|
| `linux_j.bin` | OpenSBI v1.2 + Linux 5.15.170 + rootfs + DTB（0 → ~130M 指令到 `rv64 login:`） |
| `ck/ckpt_special_s01_inst5000000.gz` ~ `s26_inst130000000.gz` | 按 **每 5M 指令** 切分的 26 个可复用检查点（覆盖完整启动流程，配合 `s00` 从复位可 100% 无缝覆盖） |
| `tools/{ckpt2image.py,ckpt2stub.py,align_check.py,pmu_events.def}` | 恢复镜像/stub 生成与比对工具（`align_check.py` 已去掉 `:=` 兼容 `eda` 的 Python 3.6.8） |
| `DDR4_8Gb_x16_3200.ini` | DRAMsim3 配置（运行时通过 `DS3_CONFIG` 传入） |
| `/nfs_global/S/houruyao/lin38/a.out` | 静态链接 rv64gc `function-model`（切检查点务必显式传 `--image <img.bin>`，不可省略 flag） |
| `/nfs_global/S/houruyao/spec06_rv64gc/tm/bin/sim64_bop14` | 静态链接 rv64gc `trace-model`（含 `PF_KIND=4` 硬件 Berti + `LLC_BOP=1`） |

## 3. 编译与部署到 `eda` 集群

1. **短编译 / 快速验证**：可直接在 `iprc-jump`（9950X3D）上进行（如 `~/rv64spec/` 下的源码与构建目录）。
2. **给 `eda` 集群准备可执行文件（关键注意事项）**：
   - **CPU 指令集兼容**：`iprc-jump` 是 AMD Zen 5（9950X3D），`eda` 是 Intel Xeon（Cascade Lake），跨机使用时务必把 `Makefile` 中的 `-march=native` / `-mtune=native` 改为 `-march=x86-64-v3 -mtune=generic`，避免在 `eda` 上触发 `SIGILL`。
   - **glibc 兼容**：`iprc-jump`（Ubuntu）的 glibc 版本高于 `eda`（CentOS 7 / Rocky），给 `eda` 跑的二进制应**静态链接**，或将源码拷到 NFS 后直接在某台 `eda` 节点上编译。
   - **编译期宏与运行时开关**：`CFG_*` 编译期宏通过 `make EXTRA_CXXFLAGS="-DCFG_...=..." BUILD_DIR=build_<tag>` 分别编译；运行时开关（如 `LLC_REPL`、`PF_ENABLE`、`PMU` 等）在起任务时通过 `env` 传入。
3. **放到 NFS**：将校验过 gate 的模拟器二进制放到 `/nfs_global/S/houruyao/spec06_rv64gc/tm/bin/<sim_name>`。

### 3.1 常用工具链与精确路径速查

| 机器 | 工具 / 目录 | 精确路径与用法 |
|---|---|---|
| **本机 WSL** | 代码仓库 | `~/AI-Huma`（总控文档）、`~/AI-Huma-rtl`（RTL）、`~/AI-Huma-trace`（trace-model）、`~/AI-Huma-func`（function-model） |
| **本机 WSL** | Verilator | `/usr/local/bin/verilator`（5.046，本地 `lint_chip.sh` / `fm_gate.sh` 直接使用） |
| **`iprc-jump`** | **Verilator 5.052** | `~/rv64spec/verilator_src/bin/verilator`（**必须** `export PATH="$HOME/rv64spec/verilator_src/bin:$PATH"`；系统 `/usr/bin/verilator` 是 5.020，编不过！） |
| **`iprc-jump`** | **DRAMsim3 静态库（`TM_DIR`）** | `~/rv64spec/fe2t_g/tm` 或 `~/rv64spec/llcplru1/tm`（下含 `build_dramsim3/libdramsim3.a`） |
| **`iprc-jump`** | **RTL Linux TB 构建** | `cd ~/rv64spec/rtl_pf && PATH="$HOME/rv64spec/verilator_src/bin:$PATH" TM_DIR=~/rv64spec/fe2t_g/tm bash scripts/build_soc64_linux.sh $PWD/build/soc64lin_m3` |
| **`iprc-jump`** | **静态链接 `soc_tb` 给 `eda`** | 在 `build/soc64lin_m3/obj` 下：`g++ -static -pthread soc_tb.o fp_dpi.o verilated.o verilated_threads.o [verilated_dpi.o] Vsoc_top__ALL.a ../SimDDR.o ../PhysMemory.o "$FMDIR/librefcpu.a" "$FMDIR/lib/softfloat/softfloat.a" "$DS3_LIB" -lz -lpthread -latomic -o ../soc_tb_m3_static && scp ../soc_tb_m3_static ../skipmask.txt 10.208.120.12:/nfs_global/S/houruyao/linux_ckpt_rv64gc/` |
| **`eda` 集群** | Python 版本 | 默认 `python3` 为 **Python 3.6.8**（不支持 3.8+ 海象运算符 `:=` / `match`） |
| **`eda` 集群** | NFS 与节点规格 | 仅 **`eda-04` ~ `eda-10`** 挂载 `/nfs_global`：`eda-04`（144C/1.5TB）、`eda-05`（72C）、`eda-06..10`（各 **256C**，常有数百 GB 空闲内存）；大任务优先多节点平摊，起前先查 `uptime` 与 `free -h` |

## 4. 在 `eda` 集群起 SPEC 批量任务

### 4.1 选择空闲节点
起任务前先抽查 `eda-00` ~ `eda-10` 的负载与空闲内存，避开满载节点：

```bash
for n in eda-00 eda-01 eda-02 eda-03 eda-04 eda-05 eda-06 eda-07 eda-08 eda-09 eda-10; do
  echo -n "$n: "
  ssh -n -o ConnectTimeout=3 $n 'uptime | sed "s/.*load average/load/"; free -g | awk "NR==2{printf \" avail=%sG\n\", \$7}"' 2>/dev/null || echo "unreachable"
done
```

### 4.2 单点运行口径（参考 `tm/llc1_one.sh` / `tm/wbp_one.sh`）
- 使用前门 stub 恢复：`--mode ckpt --restore-stub <stub> -c 10000000 <ckpt.gz>`（10M 详细预热 + 10M 测量；`*nowarmup*` 点加 `-w 0`）。
- 默认开 `PF_ENABLE=1 PMU=1`，并将 `PMU_OUT` 指向结果目录、`DS3_OUT` 指向计算节点本地 `/tmp/<tag>_ds3out_$$`。
- 每个点完成后写出 `<点名> <指令数> <周期数> <耗时>` 到 `.res` 并压缩日志；失败写入 `fail.txt`。

### 4.3 分片并行启动与查进度
将任务表（如 386 点 `jobs95.txt` 或 59 点访存子集）按节点数拆分后，通过 `setsid nohup` + `xargs -P` 在多台 `eda` 节点后台启动：

```bash
# 在目标 eda 节点上启动分片任务
ssh eda-06 'cd /nfs_global/S/houruyao/spec06_rv64gc/tm && \
  (setsid nohup sh -c "xargs -P 32 -L 1 bash ./<run_one>.sh < <jobs_part>" > <tag>_eda06.log 2>&1 < /dev/null &)'
```

查看进度与失败点：

```bash
ssh login-inband 'cd /nfs_global/S/houruyao/spec06_rv64gc/tm && \
  find res_<tag> -name "*.res" | wc -l; \
  [ -f res_<tag>/fail.txt ] && wc -l res_<tag>/fail.txt'
```

## 5. 算分与对比口径

- **程序内 CPI（调和加权）**：`CPI = Σ w_i' × (周期_i / 指令_i)`（权重在已有结果的点上重新归一），`IPC = 1 / CPI`。**不要对 IPC 直接加权平均，也不要连乘比例。**
- **跨程序汇总**：12 个程序相对基线的加速比取**几何平均**（参考 `tm/cmp_ev5.py`、`spec06_rv64gc/README.md` 第 6 节）。
- **回退判据**：新改动在全量 386 点上的几何平均 IPC 若相对 `main` 低于 −1.0%，须排查原因后再决定是否合入。

## 6. 常见坑

- **9950X3D 编的二进制在 `eda` 跑崩（`SIGILL` / `GLIBC_2.3x not found`）**：去掉 `-march=native` 改 `-march=x86-64-v3`，或静态链接 / 直接在 `eda` 节点编译。
- **DRAMsim3 找不到配置文件**：每个计算节点先将 `tm/ds3cfg/configs/DDR4_8Gb_x16_3200.ini` 拷到对应 `/tmp` 路径或确保运行目录可见，`DS3_OUT` 指向本地 `/tmp` 避免 NFS 竞争。
- **`mcf` / `gcc` 内存峰值较高**：单个进程约占 3 GB RSS，并发数按节点可用内存留足余量。
- **不要把持久化数据留在 `/tmp`**：节点重启会清空 `/tmp`，正式结果统一写回 `/nfs_global/S/houruyao/spec06_rv64gc/tm/res_<tag>/`。
- **WSL Tailscale 冷启动**：Windows 空闲约 8s 会休眠 WSL，唤醒后 `tailscaled` 需要 3–5s 建立到 `100.116.179.124` 的 DERP 隧道；自动化脚本开头应加 `for i in $(seq 1 15); do tailscale ping -c 1 --timeout=2s 100.116.179.124 >/dev/null 2>&1 && break; sleep 1; done`。同步源码用 `rsync -az` 或 `tar -czf` + `scp`，不要用 `tar | ssh` 管道（DERP 下易卡死或截断）。
- **`iprc-jump` 非交互 SSH 找不到新版 Verilator**：非交互 shell 不读 `~/.bashrc`，务必显式 `export PATH="$HOME/rv64spec/verilator_src/bin:$PATH"`。
- **`function-model` (`a.out`) 切检查点漏 `--image`**：多参数模式下不会把位置参数当镜像，漏 `--image <bin>` 会静默从全零内存 `pc=0x0` 切出假检查点；切完务必抽检 `slice.log`（有 `OpenSBI`/`Linux version`）和 `ckpt2stub.py`（非零内核 PC）。
- **DRAMsim3 并发冲突**：运行 `soc_tb` 或 `trace-model` 时，必须传 `DS3_CONFIG=<ini>` 并为每个并发 worker 分配独立的本地 `/tmp/.../ds3_{tm,rtl}` 作为 `DS3_OUT`，用完即删。
- **RTL 与 `trace-model` 按指令数对齐停机**：`soc_tb` 支持可选环境变量 `SOC_TB_MAX_INSTS=<N>`（按 `committed` 精确停机），配合 `trace-model -c <N+50000>` 可按指令数无缝覆盖每个检查点段，无需按 IPC 估算周期。
