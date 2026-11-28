#!/usr/bin/env python3
"""Tier 0: Sub-second / few-second PPA estimator for AI-Huma.

Reads TSMC 28nm SRAM macro .lib files directly on eda nodes (never caches/exports
raw PDK data outside eda), derives array geometries from RTL configuration
packages (or fast yosys-slang elaboration), computes exact SRAM macro tiling,
area, padding waste, SRAM timing floor (CLK->Q + setup), and calibrated
logic+FF area estimates.

Python 3.6+ compatible.
"""
import argparse
import glob
import math
import os
import re
import subprocess
import sys
import tempfile
import time

DEFAULT_SRAM_BASE = (
    "/eda-tools/pdk/TSMC28/sram/Front_End/timing_power_noise/NLDM/"
    "temn28hpcphssrammacros_110a"
)
DEFAULT_YOSYS = "/nfs_global/S/houruyao/tools/oss-cad-suite/bin/yosys"
DEFAULT_SLANG = "/nfs_global/S/houruyao/tools/oss-cad-suite/share/yosys/plugins/slang.so"

SRAM_MACROS = [
    "tem5n28hpcplvta128x64m4swso_110a",
    "tem5n28hpcplvta256x32m4swso_110a",
    "tem5n28hpcplvta256x64m4swso_110a",
    "tem5n28hpcplvta256x72m4swso_110a",
    "tem5n28hpcplvta512x72m4swso_110a",
    "tem5n28hpcplvta512x8m4swso_110a",
    "tem5n28hpcplvta64x32m4swso_110a",
    "tem5n28hpcplvta64x58m4swso_110a",
    "tem5n28hpcplvta64x64m4swso_110a",
    "tem5n28hpcplvta64x72m4swso_110a",
    "tem5n28hpcplvta1024x32m4swso_110a",
]


def parse_sram_lib(lib_path):
    """Extract cell name, area, CLK->Q (nominal/worst) and setup (nominal/worst) from .lib."""
    with open(lib_path, "r", encoding="utf-8", errors="ignore") as fh:
        txt = fh.read()

    m_cell = re.search(r"\bcell\s*\(\s*(\w+)\s*\)", txt)
    cell_name = m_cell.group(1) if m_cell else os.path.basename(lib_path).split("_")[0].upper()

    m_area = re.search(r"^\s*area\s*:\s*([0-9.]+)\s*;", txt, re.MULTILINE)
    area = float(m_area.group(1)) if m_area else 0.0

    m_dim = re.search(r"(\d+)x(\d+)", cell_name.lower())
    depth = int(m_dim.group(1)) if m_dim else 0
    width = int(m_dim.group(2)) if m_dim else 0

    # Parse Q CLK->Q rising_edge cell_rise/cell_fall tables
    q_idx = txt.find("bus( Q )")
    q_end = txt.find("end of bus  Q", q_idx) if q_idx != -1 else -1
    q_block = txt[q_idx:q_end] if (q_idx != -1 and q_end != -1) else ""
    ck2q_vals = []
    for m in re.finditer(
        r'timing_type\s*:\s*rising_edge\s*;.*?cell_(?:rise|fall)\s*\([^)]*\)\s*\{\s*values\s*\((.*?)\)\s*;',
        q_block,
        re.DOTALL,
    ):
        nums = [float(x) for x in re.findall(r"[-+]?\d*\.\d+|\d+", m.group(1))]
        ck2q_vals.extend(nums)

    # Parse A / D / CEB setup_rising constraints
    a_idx = txt.find("bus( D )")
    clk_idx = txt.find("pin( CLK )")
    in_block = txt[a_idx:clk_idx] if (a_idx != -1 and clk_idx != -1) else ""
    setup_vals = []
    for m in re.finditer(
        r'timing_type\s*:\s*setup_rising\s*;.*?(?:rise|fall)_constraint\s*\([^)]*\)\s*\{\s*values\s*\((.*?)\)\s*;',
        in_block,
        re.DOTALL,
    ):
        nums = [float(x) for x in re.findall(r"[-+]?\d*\.\d+|\d+", m.group(1))]
        setup_vals.extend(nums)

    # Typical mid-table index [1][1] (~15-30ps slew, ~10-20fF load) and max
    ck2q_typ = sorted(ck2q_vals)[len(ck2q_vals) // 4] if ck2q_vals else 0.0
    ck2q_max = max(ck2q_vals) if ck2q_vals else 0.0
    setup_typ = sorted(setup_vals)[len(setup_vals) // 2] if setup_vals else 0.0
    setup_max = max(setup_vals) if setup_vals else 0.0

    return {
        "cell": cell_name,
        "depth": depth,
        "width": width,
        "area": area,
        "ck2q_typ": ck2q_typ,
        "ck2q_max": ck2q_max,
        "setup_typ": setup_typ,
        "setup_max": setup_max,
    }


def load_sram_catalog(sram_base):
    """Load all 11 TSMC28 SRAM macros keyed by (depth, width) and cell name."""
    by_dw = {}
    by_cell = {}
    for m in SRAM_MACROS:
        p = os.path.join(sram_base, m, "%s_ssg0p81v125c.lib" % m)
        if not os.path.isfile(p):
            raise FileNotFoundError("Missing TSMC28 SRAM lib (run on eda node): %s" % p)
        info = parse_sram_lib(p)
        by_dw[(info["depth"], info["width"])] = info
        by_cell[info["cell"].upper()] = info
    return by_dw, by_cell


def tile_1rw(depth, width):
    """Exact tiling rule from rtl/rtl/common/sram/ttg_sram_1rw.sv."""
    if depth <= 16:
        return ("FF", 0, depth * width)
    if depth == 1024 and width <= 8:
        return ((512, 8), 2, 0)
    if depth == 512 and width <= 8:
        return ((512, 8), 1, 0)
    if depth == 512:
        return ((512, 72), (width + 71) // 72, 0)
    if depth == 256 and width > 64:
        return ((256, 72), (width + 71) // 72, 0)
    if depth == 256:
        return ((256, 64), (width + 63) // 64, 0)
    if depth == 128:
        return ((128, 64), (width + 63) // 64, 0)
    if depth <= 64 and width <= 32:
        return ((64, 32), 1, 0)
    if depth <= 64 and width <= 58:
        return ((64, 58), 1, 0)
    if depth <= 64:
        return ((64, 64), (width + 63) // 64, 0)
    return ("FALLBACK_BB", 0, width)


def tile_1r1w(depth, width):
    """Exact tiling rule from rtl/rtl/common/sram/ttg_sram_1r1w.sv."""
    if depth * width <= 1024:
        return ("FF", 0, depth * width)
    eff_depth = 64 if depth < 64 else depth
    return tile_1rw(eff_depth, width)


def parse_localparams(sv_files):
    """Extract simple integer localparams from *_pkg.sv files."""
    vals = {}
    pat = re.compile(r"localparam\s+(?:int|longint\s+unsigned|logic\s*\[[^\]]+\])\s+(\w+)\s*=\s*([^;]+);")
    for f in sv_files:
        if not os.path.isfile(f):
            continue
        with open(f, "r", encoding="utf-8", errors="ignore") as fh:
            txt = fh.read()
        for m in pat.finditer(txt):
            k, expr = m.group(1), m.group(2).strip()
            expr = re.sub(r"//.*", "", expr).strip()
            expr = re.sub(r"\b\d+'d", "", expr)
            if expr.isdigit():
                vals[k] = int(expr)
    return vals


def build_analytical_arrays(cfg):
    """Derive per-module SRAM array specs directly from RTL config constants."""
    ic_sets = cfg.get("ICACHE_SET_NUM", 64)
    ic_ways = cfg.get("ICACHE_WAY_NUM", 8)
    ic_line_w = cfg.get("ICACHE_WORD_NUM", 16) * 32
    ic_banks = 4
    ic_bsets = ic_sets // ic_banks

    ftb_s1_sets = cfg.get("FTB_S1_SETS", 1024)
    ftb_s1_ways = cfg.get("FTB_S1_WAYS", 4)
    ftb_s1_tag_w = cfg.get("FTB_S1_TAG_W", 14)
    ftb_va_bits = cfg.get("FTB_VA_BITS", 38)
    ftb_slots = cfg.get("FTB_SLOTS", 4)
    ftb_slot_w = 1 + 4 + 1 + 1 + 3 + 2 + ftb_va_bits  # 50
    ftb1_w = ftb_s1_ways * (1 + ftb_s1_tag_w + ftb_slots * ftb_slot_w)  # 4 * 215 = 860

    ftb_ah_sets = cfg.get("FTB_AH_SETS", 256)
    ftb_ah_ways = cfg.get("FTB_AH_WAYS", 8)
    ftb_ah_tag_w = cfg.get("FTB_AH_TAG_W", 22)
    aftb_w = ftb_ah_ways * (1 + ftb_ah_tag_w + ftb_slots * ftb_slot_w)  # 8 * 223 = 1784

    ex_tn = cfg.get("EX_TN", 6)
    ex_tage_n = cfg.get("EX_TAGE_N", 4096)
    tn = cfg.get("TN", 4)
    ah_tage_n = cfg.get("FTB_AH_TAGE_N", 1024)
    itt_n = cfg.get("FTB_ITT_N", 256)
    nitt = cfg.get("NITT", 3)

    bpu_ftb1_banks = cfg.get("BPU_FTB1_BANKS", 2)
    bpu_s2_base_banks = cfg.get("BPU_S2_BASE_BANKS", 4)
    bpu_s2_tage_banks = cfg.get("BPU_S2_TAGE_BANKS", 8)
    bpu_itt_banks = cfg.get("BPU_ITT_BANKS", 2)
    bpu_ah1_banks = cfg.get("BPU_AH1_BANKS", 2)

    ftb_rec_n = cfg.get("FTB_REC_N", 512)
    ftb_rf_rec_n = cfg.get("FTB_RF_REC_N", 256)
    ftb_blk_id_w = cfg.get("FTB_BLK_ID_W", 10)
    ex_fh_bits = 3 * ex_tn * 12  # 216
    itt_ent_w = 1 + 10 + 2 + 1 + ftb_va_bits  # 52
    ftb_ent_w = 1 + 22 + ftb_slots * ftb_slot_w  # 223
    s2_meta_w = (1 + 2 + ftb_ent_w) + ftb_slots * (4 + 1 + 1 + 2 + 3 + 2 + ex_tn * 2) + (1 + 2 + 2 + nitt + nitt + ftb_va_bits)
    ah_meta_w = (1 + 3 + ftb_ent_w) + ftb_slots * (3 + 1 + 1 + 3 + 2 + tn * 2) + (1 + 2 + 2 + nitt + nitt + ftb_va_bits)
    rec_w = 1 + ftb_blk_id_w + 64 + ex_fh_bits + 1 + 64 + ex_fh_bits + s2_meta_w + ah_meta_w  # 1295
    rf_rec_w = 1 + ftb_blk_id_w + 8 + 64 + (8 + ex_fh_bits) + (6 + 6 + 6 + 64)  # 389

    bpu_arrays = [
        ("u_ftb1", "1rw", ftb_s1_sets // bpu_ftb1_banks, ftb1_w, bpu_ftb1_banks),
        ("u_s2_tage/base", "1rw", ex_tage_n // bpu_s2_base_banks, 8, bpu_s2_base_banks),
        ("u_s2_tage/tbl", "1rw", ex_tage_n // bpu_s2_tage_banks, 64, ex_tn * bpu_s2_tage_banks),
        ("u_s2_itt", "1rw", itt_n // bpu_itt_banks, itt_ent_w, nitt * bpu_itt_banks),
        ("u_aftb", "1rw", ftb_ah_sets // bpu_ah1_banks, aftb_w, bpu_ah1_banks),
        ("u_atage", "1rw", ah_tage_n // bpu_ah1_banks, 60, tn * bpu_ah1_banks),
        ("u_aitt", "1rw", itt_n // bpu_ah1_banks, itt_ent_w, nitt * bpu_ah1_banks),
        ("u_brq/u_rec", "1r1w", ftb_rec_n, rec_w, 1),
        ("u_rf_rec", "1r1w", ftb_rf_rec_n, rf_rec_w, 1),
    ]

    icache_arrays = [
        ("icache_arr/u_data_sram", "1r1w", ic_bsets, ic_line_w, ic_banks * ic_ways),
    ]

    ftq_size = cfg.get("FTQ_SIZE", 64)
    ftq_banks = 8
    ftq_meta_w = 10 + 1 + 4 + cfg.get("BACKEND_FETCH_WIDTH", 16) * (1 + 3)  # 79
    ftq_ibuf_arrays = [
        ("u_meta/u_sram", "1r1w", ftq_size // ftq_banks, ftq_meta_w, ftq_banks),
    ]

    rob_num = cfg.get("ROB_NUM", 256)
    rob_banks = cfg.get("ROB_BANK_NUM", 8)
    rob_arrays = [
        ("u_inst_sram", "1r1w", rob_num // rob_banks, 32, rob_banks),
    ]

    dcache_sets = cfg.get("DCACHE_SETS_NUM", 256)
    dcache_ways = cfg.get("DCACHE_WAYS_NUM", 4)
    dcache_banks = cfg.get("DCACHE_BANK_NUM", 16)
    dcache_rows = dcache_sets // dcache_banks
    dcache_arrays = [
        ("dcache_tag", "1r1w", dcache_rows, cfg.get("DCACHE_TAG_BITS", 18), dcache_banks * dcache_ways),
        ("dcache_data", "1r1w", dcache_rows, cfg.get("DCACHE_WORD_NUM", 16) * 32, dcache_banks * dcache_ways),
    ]

    l2tlb_sets = cfg.get("L2TLB_ENTRIES", 1024) // cfg.get("L2TLB_WAYS", 4)
    ptw_arrays = [
        ("l2tlb_stlb", "1rw", l2tlb_sets, 76, cfg.get("L2TLB_WAYS", 4)),
    ]

    return {
        "tlb_mmu": [],
        "ftq_ibuf": ftq_ibuf_arrays,
        "isu": [],
        "lsu": [],
        "rob": rob_arrays,
        "icache": icache_arrays,
        "bpu": bpu_arrays,
        "front_top": bpu_arrays + icache_arrays,
        "dcache": dcache_arrays,
        "ptw_walk": ptw_arrays,
    }


def calibrated_logic_area(mod, cfg, sram_mode):
    """Calibrated TSMC 28nm HPC+ logic+FF area model (µm²) from EXP-069/070 baselines."""
    rob_n = cfg.get("ROB_NUM", 256)
    iq_int = cfg.get("IQ_INT_SIZE", 32)
    iq_mem = cfg.get("IQ_MEM_SIZE", 64)
    iq_br = cfg.get("IQ_BR_SIZE", 64)
    iq_std = cfg.get("IQ_STD_SIZE", 16)
    fp_iq = cfg.get("FP_IQ_SIZE", 32)
    iq_total = iq_int + iq_mem + iq_br + iq_std + fp_iq
    ldq = cfg.get("LDQ_SIZE", 64)
    stq = cfg.get("STQ_SIZE", 64)
    ftq = cfg.get("FTQ_SIZE", 64)
    ibuf = cfg.get("IDU_INST_BUFFER_SIZE", 64)
    itlb = cfg.get("ITLB_ENTRIES", 64)
    dtlb = cfg.get("DTLB_ENTRIES", 64)
    ic_sets = cfg.get("ICACHE_SET_NUM", 64)
    ic_ways = cfg.get("ICACHE_WAY_NUM", 8)

    base = {
        "tlb_mmu": 94793.0 * (itlb + dtlb) / 128.0,
        "ftq_ibuf": 135000.0 * (ftq / 64.0) + 104315.0 * (ibuf / 64.0),
        "isu": 467899.0 * (iq_total / 208.0),
        "lsu": 767221.0 * ((ldq + stq) / 128.0),
        "rob": 121413.0 * (rob_n / 256.0),
        "icache": 125000.0 + 1800.0 * ic_sets * ic_ways / 8.0,
        "bpu": 385385.0 if sram_mode == "real" else 425000.0,
    }
    base["front_top"] = base["bpu"] + base["icache"] + 112000.0
    return base.get(mod, 0.0)


def eval_analytical(mod, cfg, arrays, by_dw, sram_mode):
    t0 = time.time()
    macro_cnt = 0
    macro_area = 0.0
    phys_bits = 0
    log_bits = 0
    worst_sram_ns = 0.0
    details = []

    for name, port_kind, depth, width, insts in arrays:
        log_bits += depth * width * insts
        if sram_mode == "none":
            continue
        if sram_mode == "bb":
            continue
        res = tile_1rw(depth, width) if port_kind == "1rw" else tile_1r1w(depth, width)
        kind, per_inst, ff_bits = res
        if kind == "FF":
            details.append((name, "%dx%d x%d" % (depth, width, insts), "FF(%db)" % ff_bits, 0, 0.0, 0.0))
            continue
        if kind == "FALLBACK_BB":
            details.append((name, "%dx%d x%d" % (depth, width, insts), "FALLBACK_BB", 0, 0.0, 0.0))
            continue
        info = by_dw.get(kind)
        cnt = per_inst * insts
        area = cnt * info["area"]
        pbits = cnt * info["depth"] * info["width"]
        sram_ns = info["ck2q_typ"] + info["setup_typ"]
        worst_sram_ns = max(worst_sram_ns, sram_ns)
        macro_cnt += cnt
        macro_area += area
        phys_bits += pbits
        details.append((
            name,
            "%dx%d x%d" % (depth, width, insts),
            info["cell"],
            cnt,
            area,
            sram_ns,
        ))

    logic_area = calibrated_logic_area(mod, cfg, sram_mode)
    total_area = logic_area + macro_area
    waste_ratio = (float(phys_bits) / float(log_bits)) if (log_bits > 0 and phys_bits > 0) else 1.0
    elapsed = time.time() - t0
    return {
        "module": mod,
        "mode": "analytical",
        "time_s": elapsed,
        "macro_cnt": macro_cnt,
        "macro_area": macro_area,
        "logic_area": logic_area,
        "total_area": total_area,
        "log_bits": log_bits,
        "phys_bits": phys_bits,
        "waste_ratio": waste_ratio,
        "sram_floor_ns": worst_sram_ns,
        "details": details,
    }


def eval_elab(mod, files_f, by_cell, yosys_bin, slang_so, sram_mode, sram_base):
    t0 = time.time()
    with open(files_f, "r") as fh:
        files = " ".join(line.strip() for line in fh if line.strip())

    sram_read = ""
    defs = "-DSYNTHESIS"
    if sram_mode == "real":
        defs += " -DSYNTH_TSMC28_SRAM"
        for sm in SRAM_MACROS:
            lf = os.path.join(sram_base, sm, "%s_ssg0p81v125c.lib" % sm)
            sram_read += "read_liberty -lib %s\n" % lf
    elif sram_mode == "bb":
        defs += " -DSRAM_BLACKBOX"

    with tempfile.NamedTemporaryFile("w", suffix=".ys", delete=False) as tf:
        ys_path = tf.name
    stat_path = ys_path + ".stat"
    ys_cmd = (
        "{sram_read}"
        "read_slang --top {top} --keep-hierarchy --unroll-limit 100000 "
        "-Wno-error=index-oob {defs} {files}\n"
        "hierarchy -check -top {top}\n"
        "tee -o {stat_path} stat\n"
    ).format(sram_read=sram_read, top=mod, defs=defs, files=files, stat_path=stat_path)

    with open(ys_path, "w") as tf:
        tf.write(ys_cmd)

    try:
        proc = subprocess.run(
            [yosys_bin, "-m", slang_so, "-q", "-s", ys_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        stat_txt = ""
        if os.path.isfile(stat_path):
            with open(stat_path, "r") as sf:
                stat_txt = sf.read()
    finally:
        if os.path.exists(ys_path):
            os.remove(ys_path)
        if os.path.exists(stat_path):
            os.remove(stat_path)

    elapsed = time.time() - t0
    if proc.returncode != 0:
        raise RuntimeError("yosys elab failed for %s: %s" % (mod, proc.stderr[-500:]))

    # Parse final Design/module stat block for cell counts
    macro_counts = {}
    fallback_cnt = 0
    idx = stat_txt.rfind("=== design hierarchy ===")
    section = stat_txt[idx:] if idx != -1 else stat_txt
    for line in section.splitlines():
        m = re.match(r"^\s+(\d+)\s+(TEM5N28\w+)\s*$", line)
        if m:
            cnt = int(m.group(1))
            cell = m.group(2).upper()
            macro_counts[cell] = macro_counts.get(cell, 0) + cnt
        elif "g_fallback_bb" in line:
            fallback_cnt += 1

    total_macros = sum(macro_counts.values())
    total_macro_area = 0.0
    phys_bits = 0
    worst_sram_ns = 0.0
    breakdown = []
    for cell, cnt in sorted(macro_counts.items()):
        info = by_cell.get(cell)
        if not info:
            continue
        area = cnt * info["area"]
        total_macro_area += area
        phys_bits += cnt * info["depth"] * info["width"]
        sram_ns = info["ck2q_typ"] + info["setup_typ"]
        worst_sram_ns = max(worst_sram_ns, sram_ns)
        breakdown.append((cell, cnt, area, sram_ns))

    return {
        "module": mod,
        "mode": "elab",
        "time_s": elapsed,
        "macro_cnt": total_macros,
        "macro_area": total_macro_area,
        "phys_bits": phys_bits,
        "sram_floor_ns": worst_sram_ns,
        "fallback_cnt": fallback_cnt,
        "breakdown": breakdown,
    }


def main():
    ap = argparse.ArgumentParser(description="Tier 0 fast PPA estimator for AI-Huma")
    ap.add_argument("--module", default="all", help="Module name or 'all'")
    ap.add_argument("--mode", choices=["analytical", "elab", "both"], default="analytical")
    ap.add_argument("--sram-mode", choices=["real", "bb", "none"], default="real")
    ap.add_argument("--rtl-root", default=None, help="Path containing rtl/ and files.f")
    ap.add_argument("--files-f", default=None, help="Path to files.f for elab mode")
    ap.add_argument("--sram-base", default=DEFAULT_SRAM_BASE)
    ap.add_argument("--yosys", default=DEFAULT_YOSYS)
    ap.add_argument("--slang", default=DEFAULT_SLANG)
    args = ap.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    if args.rtl_root:
        rtl_root = os.path.abspath(args.rtl_root)
    else:
        cand1 = os.path.join(os.path.dirname(script_dir), "rtl")
        cand2 = "/nfs_global/S/houruyao/fast_ppa_eval"
        rtl_root = cand1 if os.path.isdir(os.path.join(cand1, "rtl")) else cand2

    by_dw, by_cell = load_sram_catalog(args.sram_base)

    pkg_files = glob.glob(os.path.join(rtl_root, "rtl", "**", "*_pkg.sv"), recursive=True)
    cfg = parse_localparams(pkg_files)
    arrays_map = build_analytical_arrays(cfg)

    mods = (
        ["tlb_mmu", "ftq_ibuf", "isu", "lsu", "icache", "bpu", "front_top"]
        if args.module == "all"
        else [args.module]
    )

    if args.mode in ("analytical", "both"):
        print("=== Tier 0 Analytical Mode (Zero-RTL) ===")
        print(
            "%-12s %8s %7s %11s %11s %11s %8s %9s"
            % ("Module", "Time(ms)", "Macros", "MacroArea", "Logic+FF", "TotalArea", "PadRatio", "SRAM_ns")
        )
        for m in mods:
            sm = "bb" if m in ("tlb_mmu", "ftq_ibuf") else ("none" if m in ("isu", "lsu") else args.sram_mode)
            r = eval_analytical(m, cfg, arrays_map.get(m, []), by_dw, sm)
            print(
                "%-12s %8.2f %7d %11.1f %11.1f %11.1f %7.2fx %9.3f"
                % (
                    r["module"],
                    r["time_s"] * 1000.0,
                    r["macro_cnt"],
                    r["macro_area"],
                    r["logic_area"],
                    r["total_area"],
                    r["waste_ratio"],
                    r["sram_floor_ns"],
                )
            )
            if r["details"]:
                for name, shape, cell, cnt, area, sns in r["details"]:
                    print(
                        "    %-24s %-18s -> %3dx %-30s area=%10.1f sram_ns=%.3f"
                        % (name, shape, cnt, cell, area, sns)
                    )

    if args.mode in ("elab", "both"):
        files_f = args.files_f or os.path.join(rtl_root, "files.f")
        if not os.path.isfile(files_f):
            raise FileNotFoundError("Missing files.f for elab mode: %s" % files_f)
        print("\n=== Tier 0 Fast RTL-Elaboration Mode (yosys-slang hierarchy only) ===")
        print("%-12s %8s %7s %11s %9s %8s" % ("Module", "Time(s)", "Macros", "MacroArea", "SRAM_ns", "Fallback"))
        for m in mods:
            sm = "bb" if m in ("tlb_mmu", "ftq_ibuf") else ("none" if m in ("isu", "lsu") else args.sram_mode)
            r = eval_elab(m, files_f, by_cell, args.yosys, args.slang, sm, args.sram_base)
            print(
                "%-12s %8.2f %7d %11.1f %9.3f %8d"
                % (r["module"], r["time_s"], r["macro_cnt"], r["macro_area"], r["sram_floor_ns"], r["fallback_cnt"])
            )
            for cell, cnt, area, sns in r["breakdown"]:
                print("    %3dx %-32s area=%10.1f sram_ns=%.3f" % (cnt, cell, area, sns))


if __name__ == "__main__":
    main()
