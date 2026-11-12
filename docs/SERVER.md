# 云服务器使用说明（SPEC 一律在服务器上跑）

服务器 47.117.141.194（2026-11-10 起；之前是 106.14.7.26、47.117.9.119，地址写在被忽略的 `hosts.txt` 里，换服务器时以它为准）：64 核、121 GB 内存。本机只做构建、gate、lint、综合和短跑。**直接 `ssh -i` 会被策略拒绝，只能走 `fleet.sh`。**

## 0. 规则

- SPEC（quick、30 点、全量）、长时间 RTL 跑都上服务器；**默认带 `PMU=1`**（PMU 不改周期，结果里有 TMA）。
- **旧配置（main）的数字先查记录，不要重跑**：`trace-model/results/baseline/baseline.csv`、[MAIN_RECORDS.md](MAIN_RECORDS.md)、[LOG.md](LOG.md)，以及下面第 5 节服务器上现成的 main 结果。
- 服务器空闲也计费；跑完不用的进程要停。关机只能用户自己做（我们没有权限）。
- 内存：mcf、gcc 每个进程约 3.3 GB，其余程序小得多。非 mcf 并发 8，mcf 单独一批、并发不超过 12。
- 结果别只留在服务器或 `/tmp`：重要数字写进文档，原始结果拉回 `~/personal/AI-Huma-data/`（`/tmp` 重启会丢）。

## 1. 入口：fleet.sh

脚本和 `hosts.txt` 在主检出：

```bash
cd /Users/ruyaoh/personal/AI-Huma/trace-model/scripts/pf/cloud
```

- `hosts.txt`（服务器 IP）被 `.gitignore` 的 `*.txt` 忽略，**只存在于主检出**，新 worktree 里没有。始终用主检出里的 `fleet.sh`，用 `RTL_SRC` 指向你的 worktree。
- `./fleet.sh all "<远程命令>"`：在每台服务器上执行命令（查进度、编译、起任务都用它）。
- `./fleet.sh rtlsrc`：把**任意检出的已提交内容**（`git archive HEAD`，未提交的不会发）发到服务器目录，trace-model 和 rtl 都能用：`RTL_SRC=<检出路径> RTL_DST=<服务器目录> ./fleet.sh rtlsrc`。
- `pack.sh` 是早期整体打包流程，打包的是主检出，**一般不用**。
- 检查点已经在服务器 `/root/spec`（ckpt、pf_stubs）。

## 2. 把一份 trace-model 源码发到服务器并编译

先把改动提交到你的分支，然后（`<tag>` 取一个自己的目录名，例如 `iqenq`）：

```bash
cd /Users/ruyaoh/personal/AI-Huma/trace-model/scripts/pf/cloud
RTL_SRC=/Users/ruyaoh/personal/AI-Huma/<你的 trace-model worktree> RTL_DST=/root/<tag>/tm ./fleet.sh rtlsrc
./fleet.sh all "cd /root/<tag>/tm && cp /root/lsuipc/tm/libs/softfloat.a libs/ && rm -rf third_party && cp -a /root/lsuipc/tm/third_party . && cp /root/AI-Huma/trace-model/scripts/pf/points_*.txt scripts/pf/ && sed -i 's/-march=native/-march=x86-64-v3/g; s/-mtune=native/-mtune=generic/g' Makefile && ln -sfn /root/AI-Huma/function-model /root/<tag>/function-model && nice make -j16 BUILD_DIR=build > build.log 2>&1; tail -2 build.log; ls -la build/simulator"
```

- 要点：`third_party`、`softfloat.a` 不在 git 里，从 `/root/lsuipc/tm` 拷；`points_*.txt` 被 `*.txt` 忽略，从 `/root/AI-Huma/trace-model/scripts/pf/` 拷；`-march=native` 要改成 `x86-64-v3`（服务器不是同一种 CPU）。
- **编译期宏**（`CFG_*`，`#ifndef` 保护的）用 `make EXTRA_CXXFLAGS='-DCFG_XXX=8 ...' BUILD_DIR=build_w8` 另建构建目录，不同宏各用各的目录。**运行时开关**（环境变量，如 `LSU_PIPE`、`BPU_PIPE`）直接在起任务时用 `env` 传。
- 编译后先校验：`build/simulator /root/AI-Huma/rtl/programs/big/dhrystone.bin`（`trace-model/validate/` 已不存在），周期应与本地同一提交相同（当前 main 为 116,774，见 MAIN_RECORDS 最新行；模型对 RTL 比周期要加 `LSU_PIPE_NOWD=1`，对服务器上的 SPEC 周期比较不需要）。

## 3. 起 SPEC 任务

```bash
./fleet.sh all "cd /root/<tag>; nohup env SPEC=/root/spec POINTS=points_30.txt PF_ENABLE=1 PMU=1 bash /root/<tag>/tm/scripts/pf/run_eval.sh /root/<tag>/tm/build/simulator /root/<tag>/res/p30 all 3 > /root/<tag>/p30.log 2>&1 < /dev/null &"
```

- 30 点精确预热：`POINTS=points_30.txt`，并发 3。
- 全量 580 点快速预热：`POINTS=points_full.txt FASTWARM=1000000`，并发 8；mcf 单独一批 `POINTS=points_full_429.mcf.txt`（并发 ≤12），不要和其它程序混在一起（OOM）。去掉 mcf 的列表：`grep -v ' 429.mcf ' points_full.txt`。
- 运行时开关用 `env LSU_PIPE=0 BPU_PIPE=0 ...` 放在 `bash run_eval.sh` 前面。
- 任务用 `nohup ... &` 放在后台；远程命令里的 `$` 要转义成 `\$`。

## 4. 看进度、取结果

```bash
./fleet.sh all "for d in p30 full; do echo \$d \$(find /root/<tag>/res/\$d -name '*.res' | wc -l); done; uptime; free -g | sed -n 2p"
```

- 每个点一个 `.res`，第一行是“点名 指令数 周期”，IPC = 指令数 / 周期。
- 失败点在 `<res>/fail.txt`。
- 拉回本地：`./fleet.sh pull`（默认进 `pfexp_cloud`），或在 `all` 里 `tar czf` 后 rsync 取。

## 5. 服务器上现成的 main 结果（不要重跑）

> **已过时的部分**：下表是 EXP-015 时期的 main（2026-11-08）。之后 main 又变了多次（EXP-019/020/023/024/025/027/028），最近一次合入（EXP-028 紧凑 ROB，2026-11-11）的 SPEC 全量 580 点数字和分数见 [MAIN_RECORDS.md](MAIN_RECORDS.md)，原始结果在本机 `~/personal/AI-Huma-data/robc/full/`（含 `score2.py`），服务器上的目录是否还在未核实；比较新实验时先用这些，不要用下表。

| 内容 | 位置 | 说明 |
|---|---|---|
| main（EXP-015，trace-model `1d08b15`）全量 580 点，快速预热 | `/root/lsubpu/res/full_new` | `PF_ENABLE=1 FASTWARM=1000000`，未开 PMU（周期不受影响） |
| main（EXP-015）30 点精确预热 | `/root/lsubpu/res/p30_new` | 同上 |
| EXP-015 之前的 main（`a7960e4`，旧设计开关串）全量 / 30 点 | `/root/lsubpu/res/full_old`（555 点）、`p30_old` | 全量 580 点的记录见 MAIN_RECORDS 的 `deb15b4` 行 |
| 带 `PMU=1` 的 30 点新旧 TMA | `/root/lsubpu/res/pmu_new`、`pmu_old` | 补跑，格式见 PMU.md 第 7 节 |

比较口径：以全量几何平均 IPC 为准；新改动比 main 低超过 1.0% 算有问题。

## 6. 常见坑

- 直接 `ssh -i` 被拒：走 `fleet.sh all`。
- `fleet.sh` 找不到 `hosts.txt`：你在 worktree 里跑了，改用主检出的脚本。
- `rtlsrc` 后服务器上没有你的新改动：没提交（只发 HEAD）。
- 编译失败找不到 `third_party` / `softfloat.a`：第 2 节的拷贝没做。
- mcf OOM：并发超过 12，或和其它程序混跑。
- 服务器重启会清 `/tmp`：别把数据放 `/tmp`。
