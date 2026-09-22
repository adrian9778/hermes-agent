#!/usr/bin/env python3
"""sourceReader 文档库维护工具：符号定位 / 文件骨架 / 文档引用校验。

用法:
  python3 sr_tools.py locate  SYM [SYM ...]        全库定位符号定义（排除 tests/evals/node_modules）
  python3 sr_tools.py outline FILE [--top]         输出文件符号骨架（--top 只看顶层）
  python3 sr_tools.py offset  FILE SYM             输出符号定义行号（用于计算函数内偏移）
  python3 sr_tools.py verify  DOC.md [DOC.md ...]  校验文档中所有文件路径与行号引用

记法约定（见 UPDATE-SPEC.md）: 文件路径 + 符号名 + 函数内相对偏移（+0 = 定义行）。
"""
import os
import re
import sys

SKIP_DIRS = ("/tests", "/evals", "/__pycache__", "/node_modules", "/.git", "/test")
SEARCH_ROOTS = ["agent", "hermes_cli", "gateway", "tools", "cron", "tui_gateway",
                "acp_adapter", "plugins", "hermes_state_common.py"]
DEF_RE = re.compile(r"^\s*(?:class|def|async def)\s+(\w+)")
FILE_REF_RE = re.compile(r"[A-Za-z0-9_*][A-Za-z0-9_./*-]*\.(?:py|tsx|ts|yaml|yml|json|md|sh)")
LINE_REF_RE = re.compile(r"@(\d+)")
# 出现这些词的上下文视为「说明性引用」（如"该文件已不存在"），不计为待修笔误
NEGATION_HINTS = ("不存在", "已删除", "已清空", "已迁移", "已不在", "无法确定", "不是一回事")


def _iter_py():
    for root in SEARCH_ROOTS:
        if root.endswith(".py"):
            if os.path.isfile(root):
                yield root
            continue
        for dp, dn, fn in os.walk(root):
            if any(s in dp for s in SKIP_DIRS):
                continue
            for f in fn:
                if f.endswith(".py"):
                    yield os.path.join(dp, f)
    for f in os.listdir("."):
        if f.endswith(".py"):
            yield f


def cmd_locate(syms):
    hits = {s: [] for s in syms}
    for p in _iter_py():
        try:
            with open(p, encoding="utf-8", errors="replace") as fh:
                for i, l in enumerate(fh, 1):
                    m = DEF_RE.match(l)
                    if m and m.group(1) in hits:
                        hits[m.group(1)].append((p, i))
        except OSError:
            pass
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


def cmd_verify(docs):
    real, explanatory, nonrepo, total_lines = {}, {}, {}, 0
    for d in docs:
        lines = open(d, encoding="utf-8", errors="replace").read().split("\n")
        for ln in lines:
            for n in LINE_REF_RE.findall(ln):
                total_lines += 1
            for ref in FILE_REF_RE.findall(ln):
                if ref.startswith(("http", "www")) or "*" in ref or os.path.exists(ref):
                    continue
                key = (ref, os.path.basename(d))
                if any(h in ln for h in NEGATION_HINTS):
                    explanatory[key] = ln.strip()[:70]
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
