#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成文章配图（回应评审 P0-1：文章为纯文字无图）。

三张图，全部基于包内真实数据，没有一张是装饰性空图：

  图 1  转换流水线        —— 画的是 convert_to_wechat.py 真实的执行顺序，
                            含"合规自检不过就报错"这条回环（这是本文的核心论点）
  图 2  7 个坑速查表      —— 每张坑标注【依据级别】，直接对应
                            evidence/外部依据_官方原文摘录.md 的裁定
  图 3  依据分级统计      —— 官方明文 2 条 / 由官方推出 1 条 / 未找到官方出处 4 条，
                            并标出本轮因此删掉的 1 条写错的规则

为什么白底：公众号深色模式下，透明底 + 深色字会隐形。
为什么控制体积：官方"新增草稿"接口文档要求 content 小于 1M，图太多会把正文顶爆。

用法（matplotlib 只在满依赖环境里有）：
    <满依赖 python> evidence/生成文章配图.py
输出：images/fig1_pipeline.png / fig2_pitfalls.png / fig3_evidence.png
"""

from __future__ import annotations

import os
import subprocess
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
IMG_DIR = os.path.join(ROOT, "images")

# 中文字体：Windows 优先微软雅黑，找不到就试常见的几个，都没有就报错（绝不画豆腐块）
CJK_CANDIDATES = [
    "Microsoft YaHei", "Microsoft JhengHei", "SimHei", "Noto Sans CJK SC",
    "Source Han Sans SC", "PingFang SC", "SimSun",
]


def setup_font() -> str:
    from matplotlib import font_manager

    have = {f.name for f in font_manager.fontManager.ttflist}
    for name in CJK_CANDIDATES:
        if name in have:
            plt.rcParams["font.sans-serif"] = [name]
            plt.rcParams["axes.unicode_minus"] = False
            return name
    raise SystemExit(
        "找不到中文字体（已试：" + "、".join(CJK_CANDIDATES) + "）。"
        "没有中文字体画出来是豆腐块，宁可不画——请先安装字体或指定 CJK_CANDIDATES。"
    )


# 主题色（与 themes.py 的 accent 主题取色一致，保证图与正文配色不打架）
C_INK = "#1f2937"
C_SUB = "#6b7280"
C_LINE = "#d1d5db"
C_BLUE = "#2563eb"
C_BLUE_L = "#e0edff"
C_AMBER = "#d97706"
C_AMBER_L = "#fef3c7"
C_RED = "#dc2626"
C_RED_L = "#fee2e2"
C_GREEN = "#059669"
C_GREEN_L = "#d1fae5"


def _box(ax, x, y, w, h, text, fc, ec, fs=10.5, bold=False, tc=C_INK):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.03",
        linewidth=1.4, edgecolor=ec, facecolor=fc, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, color=tc, zorder=3,
            fontweight="bold" if bold else "normal", linespacing=1.4)


def _arrow(ax, x1, y1, x2, y2, color=C_SUB, style="-|>", ls="-"):
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2), arrowstyle=style, mutation_scale=13,
        linewidth=1.5, color=color, linestyle=ls, zorder=1,
        shrinkA=2, shrinkB=2))


def fig1_pipeline() -> str:
    fig, ax = plt.subplots(figsize=(9.6, 5.0), dpi=100)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 52)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    ax.text(50, 48.4, "Markdown → 公众号 HTML：转换流水线", ha="center", va="center",
            fontsize=14.5, fontweight="bold", color=C_INK)
    ax.text(50, 45.0, "实线 = 主链路   红色回环 = 合规自检不过就报错，不静默放行",
            ha="center", va="center", fontsize=9.2, color=C_SUB)

    bw, bh = 17.0, 7.6
    y_main = 30.0
    xs = [3.0, 25.4, 47.8, 70.2]
    _box(ax, xs[0], y_main, bw, bh, "Markdown\n源文件", "#f8fafc", C_LINE)
    _box(ax, xs[1], y_main, bw, bh, "解析\n（markdown 库优先\n缺库自动降级）",
         C_BLUE_L, C_BLUE)
    _box(ax, xs[2], y_main, bw, bh, "注入 inline 样式\n+ 中文排版\n（h1→h2 / div→p）",
         C_BLUE_L, C_BLUE)
    _box(ax, xs[3], y_main, bw, bh, "公众号兼容\nHTML", C_GREEN_L, C_GREEN, bold=True)

    for i in range(3):
        _arrow(ax, xs[i] + bw, y_main + bh / 2, xs[i + 1] - 0.4, y_main + bh / 2)

    # 自检环节
    y_chk = 15.0
    _box(ax, 47.8, y_chk, bw, bh, "wechat_check.py\n合规自检\n（标签/属性/CSS/图片）",
         C_AMBER_L, C_AMBER, fs=10)
    _arrow(ax, 47.8 + bw / 2, y_main - 0.2, 47.8 + bw / 2, y_chk + bh + 0.2)

    # 通过 → 输出
    _arrow(ax, 47.8 + bw, y_chk + bh / 2, 70.2 - 0.4, y_main + bh / 2, color=C_GREEN)
    ax.text(62.0, 24.6, "通过", ha="center", fontsize=9.2, color=C_GREEN, fontweight="bold",
            bbox=dict(facecolor="white", edgecolor="none", pad=1.5), zorder=4)

    # 不过 → 报错（红色回环）
    _box(ax, 25.4, y_chk, bw, bh, "终端报出\n违规项与行号\n→ 人去改",
         C_RED_L, C_RED, fs=10, tc=C_RED)
    _arrow(ax, 47.8 - 0.4, y_chk + bh / 2, 25.4 + bw + 0.4, y_chk + bh / 2, color=C_RED)
    ax.text(36.6, y_chk + bh + 1.4, "不过", ha="center", fontsize=9.2,
            color=C_RED, fontweight="bold",
            bbox=dict(facecolor="white", edgecolor="none", pad=1.5), zorder=4)

    ax.text(50, 8.0, "关键不在「多几个样式」，而在把「会不会被平台剥掉」变成一条可执行的检查",
            ha="center", va="center", fontsize=9.6, color=C_SUB)
    ax.text(50, 4.6, "数据来源：wechat-publisher/scripts/convert_to_wechat.py 实际执行顺序",
            ha="center", va="center", fontsize=8.2, color="#9ca3af")

    out = os.path.join(IMG_DIR, "fig1_pipeline.png")
    fig.savefig(out, dpi=100, facecolor="white", bbox_inches="tight",
                pil_kwargs={"optimize": True})
    plt.close(fig)
    return out


# (坑, 现象, 解法, 依据级别)
PITFALLS = [
    ("1", "<style> 与 class 全失效", "每个元素自带 style=\"...\"", "未找到官方出处", C_RED_L),
    ("2", "<h1> 被标题字段征用", "所有标题降一级用", "未找到官方出处", C_RED_L),
    ("3", "<div> 不靠谱", "用多个 <p> 拼「三段式盒子」", "未找到官方出处", C_RED_L),
    ("4", "<script> / <iframe> 一律剥离", "只能用静态图 / 公众号组件", "官方明文", C_GREEN_L),
    ("5", "外链图会裂、SVG 会消失", "转 base64 内嵌；矢量图先导出 PNG", "官方明文", C_GREEN_L),
    ("6", "<pre> 代码块被压成一行", "换行转 <br>、行首空格转 &nbsp;", "未找到官方出处", C_RED_L),
    ("7", "MathJax / KaTeX 全灭", "先渲染成 PNG 再内嵌", "由官方推出", C_AMBER_L),
]


def fig2_pitfalls() -> str:
    n = len(PITFALLS)
    fig_h = 1.5 + 0.62 * n
    fig, ax = plt.subplots(figsize=(10.0, fig_h), dpi=100)
    ax.set_xlim(0, 100)
    ax.set_ylim(-1.1, n + 2.2)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    ax.text(50, n + 1.78, "7 个坑速查表（右侧标注每条的依据级别）",
            ha="center", va="center", fontsize=14, fontweight="bold", color=C_INK)
    ax.text(50, n + 1.18,
            "依据级别裁定见 evidence/外部依据_官方原文摘录.md；「未找到官方出处」= 微信未公开编辑器白名单",
            ha="center", va="center", fontsize=8.6, color=C_SUB)

    col_x = [1.0, 8.0, 42.0, 72.0]
    col_w = [7.0, 34.0, 30.0, 27.0]
    head = ["", "坑：现象", "解法", "依据"]
    for x, w, t in zip(col_x, col_w, head):
        ax.add_patch(FancyBboxPatch((x, n - 0.15), w - 0.6, 0.78,
                                    boxstyle="round,pad=0.006,rounding_size=0.02",
                                    linewidth=0.8, edgecolor=C_BLUE, facecolor=C_BLUE, zorder=2))
        ax.text(x + (w - 0.6) / 2, n + 0.24, t, ha="center", va="center",
                fontsize=10, color="white", fontweight="bold", zorder=3)

    for i, (num, pheno, fix, basis, fc) in enumerate(PITFALLS):
        y = n - 1 - i
        cells = [f"坑 {num}", pheno, fix, basis]
        for j, (x, w, t) in enumerate(zip(col_x, col_w, cells)):
            if j == 3:
                ax.add_patch(FancyBboxPatch((x, y), w - 0.6, 0.82,
                                            boxstyle="round,pad=0.006,rounding_size=0.02",
                                            linewidth=0.9, edgecolor=C_LINE, facecolor=fc, zorder=2))
            else:
                ax.add_patch(FancyBboxPatch((x, y), w - 0.6, 0.82,
                                            boxstyle="round,pad=0.006,rounding_size=0.02",
                                            linewidth=0.9,
                                            edgecolor=C_BLUE if j == 1 else C_LINE,
                                            facecolor=C_BLUE_L if j == 1 else "white", zorder=2))
            ax.text(x + (w - 0.6) / 2, y + 0.41, t, ha="center", va="center",
                    fontsize=9.0 if j != 2 else 8.6,
                    color=C_INK if j != 3 else (C_GREEN if "官方明文" in t
                                                else (C_AMBER if "推出" in t else C_RED)),
                    fontweight="bold" if j in (0, 1, 3) else "normal", zorder=3)

    ax.text(50, -0.75,
            "注：坑 7 的依据是「官方明文：此处会去除 JS」—— MathJax/KaTeX 的载体就是 <script>，"
            "被去除即失效，属推导而非实测猜测",
            ha="center", va="center", fontsize=8.2, color=C_SUB)

    out = os.path.join(IMG_DIR, "fig2_pitfalls.png")
    fig.savefig(out, dpi=100, facecolor="white", bbox_inches="tight",
                pil_kwargs={"optimize": True})
    plt.close(fig)
    return out


def fig3_evidence() -> str:
    fig, ax = plt.subplots(figsize=(9.6, 4.5), dpi=100)
    fig.patch.set_facecolor("white")

    labels = ["官方明文", "由官方推出", "未找到官方出处"]
    values = [2, 1, 4]
    colors = [C_GREEN, C_AMBER, C_RED]
    ypos = list(range(len(labels) - 1, -1, -1))

    bars = ax.barh(ypos, values, color=colors, height=0.52, zorder=3)
    for b, v, lab in zip(bars, values, labels):
        ax.text(v + 0.09, b.get_y() + b.get_height() / 2, f"{v} 条",
                va="center", ha="left", fontsize=11.5, fontweight="bold", color=C_INK)
        ax.text(0.12, b.get_y() + b.get_height() / 2, lab,
                va="center", ha="left", fontsize=10.2, color="white", fontweight="bold", zorder=4)

    ax.set_yticks(ypos)
    ax.set_yticklabels([""] * len(labels))
    ax.set_xlim(0, 5.6)
    ax.set_xticks(range(0, 6))
    ax.set_xlabel("规则条数（共 7 条）", fontsize=10, color=C_SUB)
    ax.set_title("7 个坑的依据分布：只有 2 条能直接引官方原文",
                 fontsize=13.5, fontweight="bold", color=C_INK, pad=12)
    ax.grid(axis="x", linestyle=":", color=C_LINE, zorder=0)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(C_LINE)

    ax.text(0.0, -1.02,
            "补依据的直接收获：查出 1 条自己写错的规则（「单篇图片不超过 100 张」——无任何官方出处），已删除。",
            transform=ax.transData, fontsize=9.0, color=C_RED, fontweight="bold")
    ax.text(0.0, -1.42,
            "官方明文来源：新增草稿接口文档（去除 JS / 外部图片 url 将被过滤）、永久素材接口文档（过滤外部图片链接 / 图片格式与大小）",
            transform=ax.transData, fontsize=8.2, color=C_SUB)

    out = os.path.join(IMG_DIR, "fig3_evidence.png")
    fig.savefig(out, dpi=100, facecolor="white", bbox_inches="tight",
                pil_kwargs={"optimize": True})
    plt.close(fig)
    return out


def main() -> int:
    os.makedirs(IMG_DIR, exist_ok=True)
    font = setup_font()
    print(f"中文字体：{font}")
    total = 0
    for fn in (fig1_pipeline, fig2_pitfalls, fig3_evidence):
        p = fn()
        size = os.path.getsize(p)
        total += size
        print(f"  {os.path.relpath(p, ROOT)}  {size:,} 字节")
    print(f"合计 {total:,} 字节；转 base64 后约 {int(total * 4 / 3):,} 字节"
          f"（官方要求正文 < 1M，留足余量）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
