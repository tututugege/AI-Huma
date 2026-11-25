#!/usr/bin/env python3
"""Lightweight documentation hygiene linter for AI-Huma.

Checks:
  1. Broken relative markdown links across living docs
  2. Stale/deleted keywords lingering in living docs (excludes archive/, LOG.md, MAIN_RECORDS.md)
  3. Oversized living docs (> 450 lines) that may need splitting/archiving
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

LIVING_DIRS = [
    "docs",
    "rtl/docs",
    "rtl/scripts",
    "rtl/sva",
    "rtl/tools/fuzz",
    "trace-model/docs",
    "function-model/docs",
]

# Historical / append-only files exempt from stale-keyword and size checks
EXEMPT_STALE = {
    "docs/LOG.md",
    "docs/MAIN_RECORDS.md",
    "docs/EXPLORATION.md",
    "rtl/docs/deviations.md",
    "rtl/docs/09-synthesis-report.md",
    "trace-model/docs/LSU_PIPE.md",
    "trace-model/docs/LSU_PIPE_IPC.md",
    "trace-model/docs/LSU_TIMING.md",
}

STALE_PATTERNS = [
    (r"\bLSU_PIPE_NOWD\b", "deleted env var LSU_PIPE_NOWD (default config now equals RTL)"),
    (r"\bROB_COMPACT\b", "deleted switch ROB_COMPACT (compact ROB is now the only ROB)"),
    (r"47\.117\.141\.194", "decommissioned Aliyun server IP"),
]

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
CODE_SPAN_RE = re.compile(r"`[^`]*`")
HISTORICAL_NOTE_RE = re.compile(r"已删除|删掉|已停用|已退役|并不存在|已改正|此前|曾|原")


def collect_md():
    files = []
    for d in LIVING_DIRS:
        p = os.path.join(ROOT, d)
        if not os.path.isdir(p):
            continue
        for dp, dns, fns in os.walk(p):
            # Skip archive/ completely
            dns[:] = [x for x in dns if x != "archive"]
            for fn in sorted(fns):
                if fn.endswith(".md"):
                    files.append(os.path.join(dp, fn))
    return files


def main():
    broken = []
    stale = []
    oversized = []

    for path in collect_md():
        rel = os.path.relpath(path, ROOT)
        with open(path, encoding="utf-8", errors="ignore") as fp:
            lines = fp.readlines()

        # 1. Relative link check (skip historical logs & inline code spans)
        if rel not in ("docs/LOG.md", "docs/MAIN_RECORDS.md"):
            for idx, line in enumerate(lines, 1):
                clean = CODE_SPAN_RE.sub("", line)
                for m in LINK_RE.finditer(clean):
                    target = m.group(1).strip()
                    if not target or target.startswith(("http://", "https://", "mailto:", "#", "file://")):
                        continue
                    target_file = target.split("#", 1)[0]
                    if not target_file:
                        continue
                    resolved = os.path.normpath(os.path.join(os.path.dirname(path), target_file))
                    if not os.path.exists(resolved):
                        broken.append((rel, idx, target))

        # 2. Stale keyword check (living docs only; skip lines explicitly noting removal/deprecation)
        if rel not in EXEMPT_STALE and not rel.startswith("rtl/docs/modules/"):
            for idx, line in enumerate(lines, 1):
                if HISTORICAL_NOTE_RE.search(line):
                    continue
                for pat, msg in STALE_PATTERNS:
                    if re.search(pat, line):
                        stale.append((rel, idx, msg))

        # 3. Size check (living docs only)
        if rel not in EXEMPT_STALE and len(lines) > 450:
            oversized.append((rel, len(lines)))

    print(f"doc_lint: scanned {len(collect_md())} living markdown files")
    if broken:
        print(f"\n[BROKEN LINKS] ({len(broken)}):")
        for rel, idx, t in broken[:30]:
            print(f"  {rel}:{idx} -> {t}")
    if stale:
        print(f"\n[STALE KEYWORDS] ({len(stale)}):")
        for rel, idx, msg in stale[:30]:
            print(f"  {rel}:{idx} -> {msg}")
    if oversized:
        print(f"\n[OVERSIZED LIVING DOCS >450 lines] ({len(oversized)}):")
        for rel, n in oversized:
            print(f"  {rel}: {n} lines")

    if not broken and not stale:
        print("doc_lint: OK (0 broken links, 0 stale keywords)")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
