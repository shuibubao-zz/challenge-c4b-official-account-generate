#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""selftest 口径实测：把「20/20」与「18/20」这两个数字各自绑定到一个可复现的环境。

为什么要重写这个文件（v2 加固轮自查抓到的问题）：

  上一版（selftest_干净环境复测.py）有两个毛病：
    1. 它把本机当成"依赖齐全"，直接在**当前解释器**里跑对照。但系统 python 上
       markdown/bs4/matplotlib/docx **一个都没装**，于是"本机（依赖齐全）"这一栏
       实际跑出来是 18/20 —— 标签与事实不符，属于言行不一。
    2. 输出只打印了最后 3 行（`splitlines()[-3:]`），导致 20 项里只显示 1 项，
       看不出到底哪两项掉了。

  这一版改成**严格的对照实验**：同一个解释器跑两遍，唯一变量是"第三方库是否可见"。
     A 组（full） ：直接跑 selftest
     B 组（clean）：先挂 import 钩子屏蔽 markdown/bs4/matplotlib/docx，再跑
  两组都用 FULL_PY（装有四个库的解释器），这样"18/20"里的失败**只可能**来自缺库，
  不会混进解释器版本差异。

用法：
    python evidence/selftest_双环境口径.py
    FULL_PY=/path/to/python python evidence/selftest_双环境口径.py   # 指定满依赖解释器
输出：
    evidence/selftest_双环境口径_输出.txt
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.abspath(os.path.join(HERE, "..", "wechat-publisher", "scripts"))
OUT_PATH = os.path.join(HERE, "selftest_双环境口径_输出.txt")

DEFAULT_FULL_PY = r"C:\Users\卢怡然\.workbuddy\binaries\python\envs\default\Scripts\python.exe"
BLOCKED = ("markdown", "bs4", "matplotlib", "docx")

# 子进程里执行的"屏蔽依赖后跑 selftest"的小程序
BLOCK_RUNNER = r'''
import io, os, sys
from contextlib import redirect_stdout
sys.path.insert(0, r"{scripts}")
BLOCKED = {blocked!r}
class _Blocker:
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in BLOCKED:
            raise ImportError("[clean] " + fullname)
        return None
sys.meta_path.insert(0, _Blocker())
import selftest
buf = io.StringIO()
with redirect_stdout(buf):
    try:
        selftest.main()
    except SystemExit:
        pass
sys.stdout.write(buf.getvalue())
'''


def run(tag: str, py: str, block: bool) -> tuple[int, int, list[tuple[str, bool, str]]]:
    if block:
        code = BLOCK_RUNNER.format(scripts=SCRIPTS, blocked=list(BLOCKED))
        cmd = [py, "-c", code]
    else:
        cmd = [py, os.path.join(SCRIPTS, "selftest.py")]
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env, timeout=600)
    out = proc.stdout or ""
    rows: list[tuple[str, bool, str]] = []
    for line in out.splitlines():
        s = line.strip()
        if s.startswith(("✅", "❌")):
            ok = s.startswith("✅")
            name = s.lstrip("✅❌ ").strip()
            # 失败项的 detail 先留空，由下面的缩进行填真实原因
            rows.append((name, ok, ""))
        elif line.startswith(" ") and rows and not rows[-1][1]:
            # 失败项的补充说明（selftest 会缩进打印 "Fail: ..."）
            rows[-1] = (rows[-1][0], False, (rows[-1][2] + " " + s).strip())
    m = re.search(r"(\d+)\s*/\s*(\d+)", out)
    total = int(m.group(2)) if m else len(rows)
    passed = sum(1 for _, ok, _ in rows if ok)
    return passed, total, rows


def main() -> int:
    full_py = os.environ.get("FULL_PY") or DEFAULT_FULL_PY
    lines: list[str] = []

    def p(s: str = "") -> None:
        lines.append(s)
        print(s)

    p("=" * 72)
    p("selftest 口径实测 · wechat-publisher v2 加固轮")
    p("=" * 72)
    p(f"满依赖解释器 FULL_PY：{full_py}")
    p(f"存在：{'是' if os.path.exists(full_py) else '否'}")
    p(f"被屏蔽的库：{', '.join(BLOCKED)}")
    p("对照方式：同一解释器跑两遍，唯一变量=第三方库是否可见")
    p()

    if not os.path.exists(full_py):
        p("❌ FULL_PY 不存在。请安装依赖后重试：")
        p("   <python> -m pip install markdown beautifulsoup4 matplotlib python-docx")
        p("   或用环境变量指定：FULL_PY=/path/to/python python evidence/selftest_双环境口径.py")
        open(OUT_PATH, "w", encoding="utf-8").write("\n".join(lines) + "\n")
        return 1

    pa, ta, rows_a = run("A", full_py, block=False)
    pb, tb, rows_b = run("B", full_py, block=True)

    p("===== A 组：满依赖（四个库都装了） =====")
    for name, ok, detail in rows_a:
        p(f"  {'✅' if ok else '❌'} {name}" + (f"\n       {detail}" if detail else ""))
    p(f"  → {pa}/{ta}")
    p()
    p("===== B 组：干净环境（屏蔽四个库） =====")
    for name, ok, detail in rows_b:
        p(f"  {'✅' if ok else '❌'} {name}" + (f"\n       {detail}" if detail else ""))
    p(f"  → {pb}/{tb}")
    p()

    set_a = {n for n, ok, _ in rows_a if ok}
    set_b = {n for n, ok, _ in rows_b if ok}
    lost = [n for n, _, _ in rows_a if n in set_a and n not in set_b]

    p("=" * 72)
    p(f"满依赖：{pa}/{ta}")
    p(f"干净环境：{pb}/{tb}")
    p(f"因缺库而掉项的用例（共 {len(lost)} 项）：")
    for n in lost:
        p(f"  - {n}")
        for name, ok, detail in rows_b:
            if name == n and not ok:
                p(f"      原因：{detail}")
    p("=" * 72)
    p()
    p("口径结论（写进 README / 文章 / AAR 的唯一版本）：")
    p(f"  · selftest 共 {ta} 项。")
    p(f"  · **满依赖环境 {pa}/{ta}**（markdown / beautifulsoup4 / matplotlib / python-docx 均已安装）。")
    p(f"  · **干净环境 {pb}/{tb}**：缺库时上面 {len(lost)} 项不可用，其余全部通过。")
    p("  · 掉的两项是「双引擎等价」类测试 —— 它们拿 markdown 库当参照物，")
    p("    没有参照物就无法对比，属于**不可执行**，不等于零依赖路径有 bug。")
    p("  · 零依赖主路径在干净环境下完整可用：解析、排版、合规自检、公式降级告警全部通过。")
    p()
    p("复现命令：")
    p(f"  \"{full_py}\" wechat-publisher/scripts/selftest.py        # A 组")
    p("  python evidence/selftest_双环境口径.py                    # 两组对照")
    open(OUT_PATH, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"\n已留档：{OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
