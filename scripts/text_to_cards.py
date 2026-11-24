#!/usr/bin/env python3
"""text_to_cards.py —— 一段 JSON 文字，画成一套 3:4 的图文卡。

用法：
    python text_to_cards.py cards.json --out cards/

cards.json 长这样：

{
  "brand": "蓝雨 · 一个住在机器里的 AI",
  "size": [1080, 1440],
  "cards": [
    {"label": "01 / 封面", "big": "核引文", "sub": "一个开源的小工具"},
    {"label": "02", "big": "43 万字", "sub": "删到 6.5 万\\n还不报错"}
  ]
}

big 是一个词组（一行，放不下会自动缩字号）；sub 最多三行，用 \\n 分。
底色和字色可以整份覆盖：{"bg": [13,20,32], "fg": [255,255,255], "accent": [120,200,255]}
"""
import argparse
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

# Windows 自带的中文字体，雅黑粗最稳
FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
]


def load_font(size):
    for p in FONT_CANDIDATES:
        if os.path.isfile(p):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    sys.exit("找不到中文字体（试过 msyhbd.ttc / msyh.ttc / simhei.ttf）")


def fit_font(text, max_width, start, draw, floor=48):
    """从 start 往下降，直到这行放得下。"""
    size = start
    while size > floor:
        f = load_font(size)
        if draw.textlength(text, font=f) <= max_width:
            return f
        size -= 8
    return load_font(floor)


def draw_card(spec, cfg, idx, total, size):
    w, h = size
    bg = tuple(cfg.get("bg", [13, 20, 32]))
    fg = tuple(cfg.get("fg", [245, 248, 255]))
    accent = tuple(cfg.get("accent", [122, 200, 255]))
    dim = tuple(cfg.get("dim", [120, 140, 165]))

    img = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(img)

    pad = int(w * 0.09)

    # 左上角品牌标
    brand = cfg.get("brand")
    if brand:
        fb = load_font(int(w * 0.026))
        d.rounded_rectangle(
            [pad, pad, pad + d.textlength(brand, font=fb) + 36, pad + 62],
            radius=31, outline=dim, width=2,
        )
        d.text((pad + 18, pad + 16), brand, font=fb, fill=dim)

    # 顶部小标签
    label = spec.get("label")
    if label:
        fl = load_font(int(w * 0.028))
        d.text((pad, int(h * 0.20)), label, font=fl, fill=dim)

    # 大字
    big = str(spec.get("big", "")).strip()
    if big:
        fb = fit_font(big, w - pad * 2, int(w * 0.14), d)
        d.text((pad, int(h * 0.30)), big, font=fb, fill=fg)

    # 副文字（最多三行）
    sub = str(spec.get("sub", "")).strip()
    if sub:
        fs = load_font(int(w * 0.045))
        y = int(h * 0.56)
        for line in sub.split("\n")[:3]:
            d.text((pad, y), line, font=fs, fill=accent)
            y += int(w * 0.075)

    # 底部页码
    fp = load_font(int(w * 0.024))
    d.text((pad, h - pad - 30), f"{idx}/{total}", font=fp, fill=dim)

    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec", help="卡片内容的 JSON")
    ap.add_argument("--out", default="cards", help="输出目录")
    a = ap.parse_args()

    with open(a.spec, encoding="utf-8") as fh:
        cfg = json.load(fh)

    cards = cfg.get("cards") or []
    if not cards:
        sys.exit("JSON 里没有 cards")

    size = tuple(cfg.get("size") or [1080, 1440])
    os.makedirs(a.out, exist_ok=True)

    made = []
    for i, spec in enumerate(cards, 1):
        img = draw_card(spec, cfg, i, len(cards), size)
        p = os.path.join(a.out, f"{i:02d}.png")
        img.save(p)
        made.append(p)
        print(f"  {p}  {os.path.getsize(p)//1024} KB")

    print(f"好了：{len(made)} 张，{size[0]}x{size[1]}")


if __name__ == "__main__":
    main()
