#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""外部依据核验器（wechat-publisher · v2 加固轮）。

做两件事：

  A. 联网核验：把《外部依据_官方原文摘录.md》里逐字摘录的官方原文，拿到官方文档页面上
     重新抓一遍，断言"这句话现在还在页面上"。
     —— 抓不到网时不会假装通过，会明确打印 SKIP 并说明原因。

  B. 回归护栏：断言已被证伪的断言（"单篇不超过 100 张"）没有悄悄回到文章里。
     —— 这是本轮真正的收获：补依据的过程抓出了我自己写错的一条规则，
        护栏保证它不会在后续编辑中被不小心写回去。

用法：
    cd evidence && python 外部依据_核验.py
输出：
    evidence/外部依据_核验_输出.txt
"""

from __future__ import annotations

import html
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT_PATH = os.path.join(HERE, "外部依据_核验_输出.txt")

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) evidence-verifier/1.0"

# (来源标签, URL, [必须仍然出现在页面上的原文片段])
SOURCES = [
    (
        "L1-① 新增草稿接口 content 字段",
        "https://developers.weixin.qq.com/doc/service/api/draftbox/draftmanage/api_draft_add.html",
        [
            "必须少于2万字符",
            "此处会去除JS",
            "外部图片url将被过滤",
            "涉及图片url必须来源",
        ],
    ),
    (
        "L1-② 上传永久素材接口",
        "https://developers.weixin.qq.com/doc/service/api/material/permanent/api_addmaterial",
        [
            "图片（image）: 10M，支持bmp/png/jpeg/jpg/gif格式",
            "微信后台将过滤外部的图片链接",
            "图文消息素材、图片素材上限为100000",
        ],
    ),
    (
        "L1-③ 新增临时素材接口",
        "https://developers.weixin.qq.com/doc/service/api/material/temporary/api_uploadtempmedia",
        [
            "图片（image）: 10M，支持PNG\\JPEG\\JPG\\GIF格式",
            "缩略图（thumb）：64KB，支持JPG格式",
            "文件大小限制：图片2MB/视频10MB",
        ],
    ),
]

# B 段：被证伪、已删除的断言 —— 不得作为"建议"回到文章里。
# 说明：诚实交代"这里曾经写错"是允许且应该的，所以判定规则不是"禁止出现"，
#      而是"出现的每一行必须同时带解释性标记（已删/查无出处等）"，
#      防止它以正式建议的身份悄悄回归。
REGRESSION_GUARDS = [
    ("卢怡然_C4B_文章源文件.md", ["单篇不超过 100 张", "单篇不超过100张"]),
    (
        os.path.join("wechat-publisher", "references", "wechat_restrictions.md"),
        ["≤ 100 张", "不超过 100 张", "不超过100张"],
    ),
]

# 含有被证伪短语的行，必须带有这些标记之一，否则视为"重新主张"，判失败
EXPLANATION_MARKERS = ("已删", "查无出处", "未找到官方", "证伪", "查不到", "曾写")


def fetch_text(url: str, timeout: int = 25) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    raw = urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "ignore")
    t = re.sub(r"<script.*?</script>", "", raw, flags=re.S)
    t = re.sub(r"<style.*?</style>", "", t, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    t = re.sub(r"[ \t]+", " ", t)
    return "\n".join(l.strip() for l in t.split("\n") if l.strip())


def squeeze(s: str) -> str:
    """去掉所有空白后再比对，避免官方文档排版空格造成的假阴性。"""
    return re.sub(r"\s+", "", s)


def main() -> int:
    lines: list[str] = []
    hard_fail = 0
    skipped = 0

    def p(s: str = "") -> None:
        lines.append(s)
        print(s)

    p("=" * 70)
    p("外部依据核验器 · wechat-publisher v2 加固轮")
    p("=" * 70)
    p()
    p("[A] 联网核验：官方原文是否仍在页面上")
    p("-" * 70)

    for label, url, quotes in SOURCES:
        p(f"\n来源：{label}")
        p(f"  URL: {url}")
        try:
            text = fetch_text(url)
        except Exception as e:  # 网络不可达 / 超时 / 被拦
            skipped += 1
            p(f"  ⚠️ SKIP —— 未能抓取页面：{type(e).__name__}: {e}")
            p("     本项按【未核验】计，不计入通过。离线机器上这是预期结果。")
            continue
        if len(text) < 200:
            skipped += 1
            p(f"  ⚠️ SKIP —— 页面正文只有 {len(text)} 字符，疑似 JS 渲染/需登录，无法核验。")
            continue
        sq = squeeze(text)
        for q in quotes:
            ok = squeeze(q) in sq
            p(f"  {'✅' if ok else '❌'} {'在页面上' if ok else '未在页面上找到'}: {q}")
            if not ok:
                hard_fail += 1

    p()
    p("[B] 回归护栏：被证伪的断言不得悄悄回来")
    p("-" * 70)
    for rel, bad_phrases in REGRESSION_GUARDS:
        path = os.path.join(ROOT, rel)
        p(f"\n文件：{rel}")
        if not os.path.exists(path):
            p("  ⚠️ SKIP —— 文件不存在")
            skipped += 1
            continue
        content = open(path, encoding="utf-8").read()
        for phrase in bad_phrases:
            hits = [l.strip() for l in content.splitlines() if phrase in l]
            if not hits:
                p(f"  ✅ 未出现: 「{phrase}」")
                continue
            bad_lines = [l for l in hits if not any(m in l for m in EXPLANATION_MARKERS)]
            if bad_lines:
                p(f"  ❌ 以【正式建议】的身份重新出现（缺解释性标记）: 「{phrase}」")
                for l in bad_lines[:3]:
                    p(f"       {l[:80]}")
                hard_fail += 1
            else:
                p(f"  ✅ 仅在解释/勘误语境中出现（{len(hits)} 处均带标记）: 「{phrase}」")

    p()
    p("=" * 70)
    if hard_fail:
        p(f"结论：❌ 存在 {hard_fail} 项失败（另有 {skipped} 项因环境原因未核验）")
    elif skipped:
        p(f"结论：⚠️ 无失败项，但有 {skipped} 项【未核验】（离线/需登录），不算全绿")
    else:
        p("结论：✅ 全部通过（所有来源均联网核验成功，护栏无回归）")
    p("=" * 70)

    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"\n已留档：{OUT_PATH}")
    return 1 if hard_fail else 0


if __name__ == "__main__":
    sys.exit(main())
