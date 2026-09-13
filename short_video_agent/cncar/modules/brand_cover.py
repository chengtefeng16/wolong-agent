"""CNcar 品牌封面生成器

布局（9:16, 1080×1920）：
  ┌──┬──────────────────────────────┐
  │  │  CNcar           cncar.io   │  ← 顶栏 (深蓝底, 110px)
  │  │                              │
  │  │   [Pexels 背景图, 暗化]       │
  │  │                              │
  │  │                              │
  │  │  ████ 底部渐变黑 ████         │
  │  │                              │
  │  │  HOOK LINE 1                 │  ← Bebas Neue 白色大字
  │  │  HOOK LINE 2                 │
  │  │  ─────                       │  ← 情绪色分割线
  │  │  subtitle text here          │  ← Inter 小字
  └──┴──────────────────────────────┘
  ↑
  情绪色条 (14px, 全高)
  tense=红  neutral=金  uplift=青
"""

import io
import os
import random
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920

# ── 品牌色 ──────────────────────────────────────────────────────────────── #
NAVY        = (9,   16,  31)
GOLD        = (201, 168, 76)
WHITE       = (255, 255, 255)
MOOD_COLORS = {
    "tense":   (200,  55,  45),   # 砖红
    "neutral": (201, 168,  76),   # 烫金
    "uplift":  ( 42, 157, 143),   # 青绿
}

# ── 字体路径 ──────────────────────────────────────────────────────────────── #
_FONTS = Path(__file__).parent.parent.parent / "assets" / "fonts"
_BEBAS    = _FONTS / "BebasNeue-Regular.ttf"
_BODY_CANDIDATES = [
    _FONTS / "NotoSansSC-Bold.ttf",
    Path("/Library/Fonts/Arial Unicode.ttf"),
    Path("/System/Library/Fonts/STHeiti Medium.ttc"),
]

PEXELS_KEY = "P0a88apfxfsKw2wzW5BK8fIpIq5mui64iDGbqUGHZpxoH3M9igl2HoNK"

# Pexels 查询按情绪分组
_PEXELS_POOL = {
    "tense": [
        "empty car dealership dark moody",
        "suspicious businessman dark office",
        "contract signing negotiation tense",
        "port shipping containers night",
        "money loss financial crisis dark",
    ],
    "neutral": [
        "modern car showroom bright interior",
        "professional car import export",
        "luxury car dealership UAE",
        "businessman reviewing documents",
        "automotive industry professional",
    ],
    "uplift": [
        "happy car buyer dealership success",
        "BYD electric car UAE sunny",
        "modern city skyline Dubai bright",
        "successful business handshake",
        "luxury car delivery excited",
    ],
}


# ── 字体加载 ──────────────────────────────────────────────────────────────── #

def _bebas(size: int) -> ImageFont.FreeTypeFont:
    if _BEBAS.exists():
        return ImageFont.truetype(str(_BEBAS), size)
    return ImageFont.load_default(size=size)


def _body(size: int) -> ImageFont.FreeTypeFont:
    for p in _BODY_CANDIDATES:
        if Path(p).exists():
            try:
                return ImageFont.truetype(str(p), size)
            except Exception:
                continue
    return ImageFont.load_default(size=size)


# ── Pexels 抓图 ───────────────────────────────────────────────────────────── #

def _fetch_bg(mood: str, seed: int) -> Image.Image:
    pool = _PEXELS_POOL.get(mood, _PEXELS_POOL["neutral"])
    query = pool[seed % len(pool)]
    try:
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": PEXELS_KEY},
            params={"query": query, "orientation": "portrait", "per_page": 15},
            timeout=15,
        )
        if resp.status_code == 200:
            photos = resp.json().get("photos", [])
            if photos:
                photo = photos[(seed // len(pool)) % len(photos)]
                r = requests.get(photo["src"]["large2x"], timeout=20)
                if r.status_code == 200:
                    img = Image.open(io.BytesIO(r.content)).convert("RGB")
                    print(f"  [BrandCover] 背景图: {query} (photo#{photo['id']})")
                    return _crop_916(img)
    except Exception as e:
        print(f"  [BrandCover] Pexels 失败，用渐变: {e}")
    return _gradient_bg(mood)


def _crop_916(img: Image.Image) -> Image.Image:
    w, h = img.size
    if (w / h) > (W / H):
        new_w = int(h * W / H)
        img = img.crop(((w - new_w) // 2, 0, (w - new_w) // 2 + new_w, h))
    else:
        new_h = int(w * H / W)
        img = img.crop((0, (h - new_h) // 2, w, (h - new_h) // 2 + new_h))
    return img.resize((W, H), Image.LANCZOS)


def _gradient_bg(mood: str) -> Image.Image:
    mc = MOOD_COLORS.get(mood, MOOD_COLORS["neutral"])
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        r = int(NAVY[0] * (1 - t * 0.3) + mc[0] * t * 0.15)
        g = int(NAVY[1] * (1 - t * 0.3) + mc[1] * t * 0.10)
        b = int(NAVY[2] * (1 - t * 0.3) + mc[2] * t * 0.10)
        draw.line([(0, y), (W, y)], fill=(r, g, b))
    return img


# ── 文字排版工具 ───────────────────────────────────────────────────────────── #

def _wrap(text: str, font: ImageFont.FreeTypeFont,
          max_w: int, draw: ImageDraw.ImageDraw) -> list[str]:
    words = text.split()
    lines, cur = [], []
    for word in words:
        test = " ".join(cur + [word])
        if draw.textbbox((0, 0), test, font=font)[2] > max_w and cur:
            lines.append(" ".join(cur))
            cur = [word]
        else:
            cur.append(word)
    if cur:
        lines.append(" ".join(cur))
    return lines


def _text_h(text: str, font: ImageFont.FreeTypeFont,
            draw: ImageDraw.ImageDraw) -> int:
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[3] - bb[1]


# ── 主函数 ────────────────────────────────────────────────────────────────── #

def make_brand_cover(
    hook: str,
    subtitle: str,
    mood: str,
    output_path: str,
    seed: int = 0,
) -> str:
    """
    生成一张 1080×1920 品牌封面。

    hook      : 大字钩子文案（1-3 行，Bebas Neue）
    subtitle  : 小字副文案（1-2 行，Inter）
    mood      : tense / neutral / uplift
    output_path: 输出 JPEG 路径
    seed      : 用于 Pexels 查询轮换
    """
    mood_color = MOOD_COLORS.get(mood, MOOD_COLORS["neutral"])

    # 1. 背景图
    bg = _fetch_bg(mood, seed)

    # 2. 暗化叠层 (0.55 不透明度)
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 140))
    canvas = Image.alpha_composite(bg.convert("RGBA"), dark)

    # 3. 底部渐变黑（下 55%）
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    grad_start = int(H * 0.42)
    for y in range(grad_start, H):
        t = (y - grad_start) / (H - grad_start)
        alpha = int(min(245, 60 + 190 * t ** 0.7))
        gd.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
    canvas = Image.alpha_composite(canvas, grad)

    # 4. 顶栏（深蓝底, 110px）
    bar = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bar)
    bd.rectangle([(0, 0), (W, 110)], fill=(*NAVY, 230))
    # 底边金线
    bd.line([(0, 110), (W, 110)], fill=(*mood_color, 120), width=2)
    canvas = Image.alpha_composite(canvas, bar)

    # 5. 左侧情绪色条（14px 全高）
    stripe = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stripe)
    sd.rectangle([(0, 0), (14, H)], fill=(*mood_color, 255))
    canvas = Image.alpha_composite(canvas, stripe)

    # 转 RGB 开始绘文字
    img = canvas.convert("RGB")
    draw = ImageDraw.Draw(img)

    # 6. 顶栏文字
    f_logo = _bebas(48)
    f_domain = _body(28)
    draw.text((30, 30), "CNcar", font=f_logo, fill=WHITE)
    bb = draw.textbbox((0, 0), "cncar.io", font=f_domain)
    draw.text((W - bb[2] - bb[0] - 28, 40), "cncar.io", font=f_domain, fill=GOLD)

    # 7. 钩子文字区（底部往上布局）
    pad_x = 50
    max_w = W - pad_x - 30

    f_hook = _bebas(92)
    hook_lines = _wrap(hook.upper(), f_hook, max_w, draw)
    # 最多 3 行，超出缩小
    if len(hook_lines) > 3:
        f_hook = _bebas(74)
        hook_lines = _wrap(hook.upper(), f_hook, max_w, draw)

    f_sub = _body(38)
    sub_lines = _wrap(subtitle, f_sub, max_w, draw)

    line_gap_hook = 8
    hook_size = 92 if len(hook_lines) <= 3 else 74
    total_hook_h = len(hook_lines) * (hook_size + line_gap_hook)
    divider_h = 6
    sub_h = len(sub_lines) * 50
    margin_bot = 72

    # 从底部往上确定 y 起点
    y_sub_start = H - margin_bot - sub_h
    y_divider   = y_sub_start - 28
    y_hook_start = y_divider - 20 - total_hook_h

    # 画钩子大字（带描边增强可读性）
    for ln in hook_lines:
        bb = draw.textbbox((0, 0), ln, font=f_hook)
        x = pad_x
        # 描边
        for dx, dy in [(-2,0),(2,0),(0,-2),(0,2)]:
            draw.text((x+dx, y_hook_start+dy), ln, font=f_hook,
                      fill=(0, 0, 0, 180))
        draw.text((x, y_hook_start), ln, font=f_hook, fill=WHITE)
        y_hook_start += hook_size + line_gap_hook

    # 情绪色分割线
    draw.rectangle(
        [(pad_x, y_divider), (pad_x + 60, y_divider + 3)],
        fill=mood_color
    )

    # 小字副标
    for ln in sub_lines:
        draw.text((pad_x, y_sub_start), ln, font=f_sub,
                  fill=(220, 220, 220))
        y_sub_start += 50

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    img.save(output_path, "JPEG", quality=93)
    print(f"  [BrandCover] ✅ 封面: {output_path}")
    return output_path
