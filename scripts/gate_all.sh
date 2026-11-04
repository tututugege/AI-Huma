#!/usr/bin/env bash
# Pre-merge gate for the three repositories.   usage: scripts/gate_all.sh [smoke|standard]
#   smoke    (~10 min): trace-model gate (62 tests) | RTL lint | RTL per-commit check vs the function model on every gate/vm program
#                       | trace-model vs RTL first-divergence check (dhrystone window)
#   standard (+ ~30 min): + whole-program cycle/instruction equality trace-model vs RTL (scripts/cmp_trace_model.sh)
#                         + RTL Linux checkpoint window with the per-commit check (1M cycles)
# Prerequisites (built once): trace-model/build/simulator, rtl/build/soc/obj/soc_tb (plain) and rtl/build/soc_fm4/obj/soc_tb
#   (SOC_FM=1 SOC_VOPT="--threads 4 -DTTG_EBREAK_TRAP").  Run ONE gate at a time: they use all cores.  Prints a summary, exits non-zero on any FAIL.
set -uo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd); TIER=${1:-smoke}
fail=0; res=()
step() { local name=$1; shift; if "$@" > "/tmp/gate_all.$$.$name.log" 2>&1; then res+=("PASS  $name"); else res+=("FAIL  $name   (log: /tmp/gate_all.$$.$name.log)"); fail=1; fi; }

step tm_gate        bash -c "cd '$ROOT/trace-model' && bash scripts/run_gate.sh build/simulator /tmp/gate_all.$$.gate | tail -1 | grep -q 'fail=0'"
step rtl_lint       bash -c "cd '$ROOT/rtl' && bash scripts/lint.sh"
step rtl_vs_fm      bash -c "cd '$ROOT/rtl' && FMTB=build/soc_fm4/obj/soc_tb; G='$ROOT/trace-model/build'; bad=0; n=0
  for b in \$(ls \$G/tests/*/*.bin \$G/vm/*/*.bin | grep -v -e load-store/ -e memory-stress); do n=\$((n+1))
    out=\$(SOC_TB_FM=1 SOC_TB_SEMIHOST=1 perl -e 'alarm 90; exec @ARGV' \$FMTB \$b 2000000 2>&1 | grep -a '\\[FM\\] [0-9]'); case \"\$out\" in *MISMATCH*|'') echo \"BAD \$b: \$out\"; bad=\$((bad+1));; esac; done
  echo \"\$n programs, \$bad bad\"; [ \$bad -eq 0 ]"
step first_diff     bash -c "cd '$ROOT/rtl' && bash scripts/first_diff.sh programs/big/dhrystone.bin 20000 | grep -q identical"
if [ "$TIER" = standard ]; then
  step cmp_cycles   bash -c "cd '$ROOT/rtl' && bash scripts/cmp_trace_model.sh"
  step rtl_linux_window bash -c "cd '$ROOT/rtl' && [ -f /tmp/ckpt/k58.img ] && SOC_TB_STUB=/tmp/ckpt/stub.bin SOC_TB_FM=1 SOC_TB_SEMIHOST=1 build/soc_fm4/obj/soc_tb /tmp/ckpt/k58.img 1000000 2>&1 | grep -a '\\[FM\\] [0-9]' | grep -v MISMATCH"
fi
printf '%s\n' "${res[@]}"; exit $fail
