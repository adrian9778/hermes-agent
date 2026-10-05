#!/usr/bin/env python3
"""sourceReader 文档库维护工具：符号定位 / 文件骨架 / 文档引用校验。

用法:
  python3 sr_tools.py locate  SYM [SYM ...]        全库定位符号定义
  python3 sr_tools.py outline FILE [--top]         输出文件符号骨架（--top 只看顶层）
  python3 sr_tools.py offset  FILE SYM             输出符号定义行号（用于计算函数内偏移）
  python3 sr_tools.py verify  DOC.md [DOC.md ...]  校验文档中所有文件路径与行号引用

locate 是两遍扫描：先扫生产树（agent/ hermes_cli/ gateway/ tools/ cron/
tui_gateway/ acp_adapter/ plugins/ pm/ hermes_platform/ + 根级 *.py），只对第一遍
没找到的符号再扫 tests/ 与 scripts/。这样既能让测试体系的文档定位到
tests/conftest.py 的 fixture，又不会让生产符号的命中被同名测试替身稀释。

记法约定（见 UPDATE-SPEC.md）: 文件路径 + 符号名 + 函数内相对偏移（+0 = 定义行）。
"""
import os
import re
import sys

SKIP_DIRS = ("/__pycache__", "/node_modules", "/.git", "/.venv", "/dist", "/build",
             "/.mypy_cache", "/.ruff_cache")
# Production trees, searched first.
SEARCH_ROOTS = ["agent", "hermes_cli", "gateway", "tools", "cron", "tui_gateway",
                "acp_adapter", "plugins", "pm", "hermes_platform", "hermes_state_common.py"]
# Searched ONLY for symbols that the production pass could not find. The test
# suite and the CI helper scripts are where a whole class of documented symbols
# lives (`tests/conftest.py` fixtures, `scripts/run_tests_parallel.py`), but they
# also carry same-named doubles of production symbols — so they must not be
# merged into the first pass or every prod hit gets diluted by its test double.
FALLBACK_ROOTS = ["tests", "scripts"]
DEF_RE = re.compile(r"^\s*(?:class|def|async def)\s+(\w+)")
FILE_REF_RE = re.compile(
    r"(?<![A-Za-z0-9_])"                                    # not the tail of an identifier
    r"[A-Za-z0-9_*][A-Za-z0-9_./*-]*\.(?:py|tsx|ts|yaml|yml|json|md|sh)"
    r"(?![A-Za-z0-9_])"                                     # `code_kernel.shutdown_...` is a method, not `code_kernel.sh`
)
LINE_REF_RE = re.compile(r"@(\d+)")
# 出现这些词的上下文视为「说明性引用」（如"该文件已不存在"），不计为待修笔误
NEGATION_HINTS = ("不存在", "已删除", "已清空", "已迁移", "已不在", "无法确定", "不是一回事",
                  "已移除", "已下线", "移除", "删除", "删掉", "已删")


def _walk_py(root):
    """Yield every `.py` under *root* (or *root* itself when it is a file)."""
    if root.endswith(".py"):
        if os.path.isfile(root):
            yield root
        return
    for dp, dn, fn in os.walk(root):
        if any(s in dp for s in SKIP_DIRS):
            continue
        for f in fn:
            if f.endswith(".py"):
                yield os.path.join(dp, f)


def _iter_py(roots, include_root_files=False):
    for root in roots:
        yield from _walk_py(root)
    if include_root_files:
        for f in os.listdir("."):
            if f.endswith(".py"):
                yield f


def _scan(paths, syms):
    hits = {s: [] for s in syms}
    for p in paths:
        try:
            with open(p, encoding="utf-8", errors="replace") as fh:
                for i, l in enumerate(fh, 1):
                    m = DEF_RE.match(l)
                    if m and m.group(1) in hits:
                        hits[m.group(1)].append((p, i))
        except OSError:
            pass
    return hits


def cmd_locate(syms):
    hits = _scan(_iter_py(SEARCH_ROOTS, include_root_files=True), syms)
    # Second pass for whatever the production trees did not answer. A symbol that
    # genuinely lives in `tests/conftest.py` (a fixture) or
    # `scripts/run_tests_parallel.py` (a CI helper) would otherwise report
    # "✗ 未找到", which is how this tool used to lie to anyone maintaining the
    # test-suite docs.
    missing = [s for s in syms if not hits[s]]
    if missing:
        fb = _scan(_iter_py(FALLBACK_ROOTS), missing)
        for s in missing:
            hits[s] = fb[s]
    for s in syms:
        h = hits[s]
        if not h:
            print(f"{s:<40} ✗ 未找到")
        else:
            for p, i in h[:4]:
                print(f"{s:<40} {p}:{i}")
            if len(h) > 4:
                print(f"{'':<40} ... 另 {len(h)-4} 处")


def cmd_outline(path, top_only):
    try:
        lines = open(path, encoding="utf-8", errors="replace").read().split("\n")
    except OSError as e:
        print(f"读取失败: {e}")
        return
    for i, l in enumerate(lines):
        m = re.match(r"^(\s*)(class|def|async def)\s+(\w+)", l)
        if not m:
            continue
        indent = len(m.group(1))
        if top_only and indent > 0:
            continue
        if indent > 4:
            continue
        doc = ""
        if i + 1 < len(lines):
            s = lines[i + 1].strip()
            if s.startswith(('"""', "'''")):
                doc = s.strip("\"'").strip() or (lines[i + 2].strip() if i + 2 < len(lines) else "")
        doc_clean = re.sub(r"\s+", " ", doc)[:76]
        print(f"{i+1:>6}  {'  '*(indent//4)}{m.group(3):<44}{doc_clean}")


def cmd_offset(path, sym):
    try:
        lines = open(path, encoding="utf-8", errors="replace").read().split("\n")
    except OSError as e:
        print(f"读取失败: {e}")
        return
    hits = [i + 1 for i, l in enumerate(lines) if DEF_RE.match(l) and DEF_RE.match(l).group(1) == sym]
    print(f"{path} · {sym} → " + (", ".join(f"{h} (+0)" for h in hits) if hits else "✗ 未找到"))


def _ref_exists(ref, doc):
    """Resolve *ref* against the repo root AND the doc's own directory chain.

    Docs are written against different bases: `docs/sourceReader/*.md` uses
    repo-root-relative paths (`agent/turn_facade.py`), while nested upstream
    files like `apps/desktop/AGENTS.md` use file-relative ones
    (`src/store/composer.ts`). Testing only the CWD false-flags the latter.
    """
    bases, d = [".", os.path.dirname(doc)], os.path.dirname(doc)
    while d and d != ".":
        bases.append(d)
        d = os.path.dirname(d)
    return any(os.path.exists(os.path.join(b, ref)) for b in bases if b)


_PRUNED = {"node_modules", ".git", "__pycache__", ".venv", "dist", "build", ".next"}


def _build_name_index():
    """Map basename -> repo-wide occurrence count, for bare-name classification.

    Overview docs (`AGENTS.md`) routinely abbreviate: they say `jobs.py` or
    `app.tsx` meaning "the file of that name somewhere in this area". A bare
    name that exists *somewhere* is a style choice, not a broken path — only a
    bare name that exists *nowhere* is a real typo. Path-shaped refs (with a
    `/`) are always judged by resolution, never by this index.
    """
    idx: dict[str, int] = {}
    for dp, dn, fn in os.walk("."):
        dn[:] = [d for d in dn if d not in _PRUNED]
        for f in fn:
            idx[f] = idx.get(f, 0) + 1
    return idx


def cmd_verify(docs):
    name_index = _build_name_index()
    real, explanatory, nonrepo, abbrev, total_lines = {}, {}, {}, {}, 0
    for d in docs:
        lines = open(d, encoding="utf-8", errors="replace").read().split("\n")
        for ln in lines:
            for n in LINE_REF_RE.findall(ln):
                total_lines += 1
            for m in FILE_REF_RE.finditer(ln):
                ref = m.group(0)
                # `test_<skill>_skill.py` — the match is the tail of a
                # placeholder; the real name is user-supplied, so skip it.
                if m.start() and ln[m.start() - 1] == ">":
                    continue
                if ref.startswith(("http", "www")) or "*" in ref or _ref_exists(ref, d):
                    continue
                key = (ref, d)
                if any(h in ln for h in NEGATION_HINTS):
                    explanatory[key] = ln.strip()[:70]
                elif "/" not in ref and name_index.get(ref):
                    abbrev[key] = ln.strip()[:70]
                elif "/" not in ref and ref.rsplit(".", 1)[-1] in ("yaml", "yml", "json"):
                    nonrepo[key] = ln.strip()[:70]
                else:
                    real[key] = ln.strip()[:70]

    print(f"文档数: {len(docs)}")
    print(f"@行号 引用总数: {total_lines}  （应为 0 —— 记法已迁移到「符号+偏移」）")
    print()
    print(f"✗ 疑似失效路径（需要修）: {len(real)}")
    for (ref, doc), ctx in sorted(real.items()):
        print(f"    {ref:<48} [{doc}]")
        print(f"      … {ctx}")
    print()
    print(f"· 说明性引用（正文已声明不存在，非错误）: {len(explanatory)}")
    for (ref, doc), ctx in sorted(explanatory.items()):
        print(f"    {ref:<48} [{doc}]")
    print()
    print(f"· 非仓库文件名（config.yaml 这类运行期配置名）: {len(nonrepo)}")
    for (ref, doc), _ in sorted(nonrepo.items()):
        print(f"    {ref:<48} [{doc}]")
    print()
    print(f"· 裸名缩写（仓库里存在同名文件，属写法风格，非错误）: {len(abbrev)}")
    for (ref, doc), _ in sorted(abbrev.items()):
        print(f"    {ref:<48} [{doc}]")
    return len(real)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd, rest = sys.argv[1], sys.argv[2:]
    if cmd == "locate":
        cmd_locate(rest)
    elif cmd == "outline":
        cmd_outline(rest[0], "--top" in rest)
    elif cmd == "offset":
        cmd_offset(rest[0], rest[1])
    elif cmd == "verify":
        cmd_verify(rest)
    else:
        print(__doc__)
        sys.exit(1)
