"""CNcar 品牌封面生成器 v2

布局（9:16, 1080×1920）：
  ┌──┬─────────────────────────────────┐
  │  │ [顶部 navy 渐变压色]             │
  │  │ BIG TITLE LINE ONE              │  ← Bebas Neue 白+黑描边
  │  │ LINE TWO                        │
  │  │                                 │
  │  │ [背景图，62% 暗化]              │
  │  │                                 │
  │  │       $19,340                   │  ← 巨型数字（金/红），自适应宽度
  │  │       LANDED                    │  ← 冲击词，白色
  │  │                                 │
  │  ├─────────────────────────────────┤
  │  │▐ hook caption sentence here     │  ← 底部钩子条（左彩边+半透明黑底）
  │  │       CNcar.io                  │  ← 金色签名
  └──┴─────────────────────────────────┘
  ↑
  左侧竖色条 16px（red=tense / gold=其他）
  右上角 金盾✓
"""

import io
import os
import re
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
PAD_X   = 80          # 文字左边距（色条16 + 间距64）
MAX_TW  = W - PAD_X - 40   # 标题最大宽度

# ── 品牌色 ───────────────────────────────────────────────────────────────── #
NAVY      = (9,   16,  31)
GOLD      = (201, 168,  76)
WHITE     = (255, 255, 255)
BLACK     = (0,   0,    0)
RED_ALERT = (200,  55,  45)

MOOD_COLORS = {
    "tense":   RED_ALERT,
    "neutral": GOLD,
    "uplift":  GOLD,
    "data":    GOLD,
}

_IMPACT_DEFAULT = {
    "tense":   "GONE",
    "neutral": "REAL COST",
    "uplift":  "SAVED",
    "data":    "LANDED",
}
_IMPACT_FALLBACK = {   # 提不到金额时使用
    "tense":   "RED FLAG",
    "neutral": "REAL COST",
    "uplift":  "WATCH OUT",
    "data":    "LANDED",
}

# ── 字体：优先项目字体，缺失时使用各运行环境的系统字体 ───────────────────── #
_FONTS = Path(__file__).parent.parent / "assets" / "fonts"
_BODY_CANDIDATES = [
    _FONTS / "NotoSansSC-Bold.ttf",
    Path("/Library/Fonts/Arial Unicode.ttf"),
    Path("/System/Library/Fonts/STHeiti Medium.ttc"),
    Path("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"),   # GitHub Actions
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
]

# 之前下载的 BebasNeue 文件不含可用英文 glyph，会渲染为方框。这里不再使用它；
# 标题与正文统一走经过验证的粗体字体，确保本机和 GitHub Actions 都不会出现方框。
_HEADLINE_CANDIDATES = [
    _FONTS / "NotoSansSC-Bold.ttf",
    Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
    Path("/Library/Fonts/Arial Unicode.ttf"),
    Path("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
]

PEXELS_KEY = "P0a88apfxfsKw2wzW5BK8fIpIq5mui64iDGbqUGHZpxoH3M9igl2HoNK"

_PEXELS_POOL = {
    "tense": [
        "empty car dealership dark moody",
        "contract signing negotiation tense dark",
        "port shipping containers night",
        "suspicious businessman dark office",
        "money loss financial crisis dark",
    ],
    "neutral": [
        "modern car showroom bright interior",
        "professional car import export",
        "luxury car dealership UAE",
        "businessman reviewing documents office",
        "automotive industry professional",
    ],
    "uplift": [
        "happy car buyer dealership success",
        "BYD electric car UAE sunny",
        "modern city skyline Dubai bright",
        "successful business handshake",
        "luxury car delivery excited customer",
    ],
    "data": [
        "modern car showroom bright interior",
        "luxury car dealership UAE",
        "car port shipping professional",
        "automotive industry professional",
        "professional car import export",
    ],
}


# ── 字体加载 ──────────────────────────────────────────────────────────────── #

def _bebas(size: int) -> ImageFont.FreeTypeFont:
    """品牌标题字体；保留函数名以免影响现有排版调用。"""
    for p in _HEADLINE_CANDIDATES:
        if Path(p).exists():
            try:
                return ImageFont.truetype(str(p), size)
            except Exception:
                continue
    print("  [BrandCover] ⚠ 标题字体不可用，退回默认字体")
    return ImageFont.load_default(size=size)


def _body(size: int) -> ImageFont.FreeTypeFont:
    for p in _BODY_CANDIDATES:
        if Path(p).exists():
            try:
                return ImageFont.truetype(str(p), size)
            except Exception:
                continue
    return ImageFont.load_default(size=size)


# ── 背景图 ────────────────────────────────────────────────────────────────── #

def _fetch_bg(mood: str, seed: int, bg_image_path: str = "") -> Image.Image:
    if bg_image_path and Path(bg_image_path).exists():
        try:
            return _crop_916(Image.open(bg_image_path).convert("RGB"))
        except Exception as e:
            print(f"  [BrandCover] 本地背景图加载失败: {e}")

    pool  = _PEXELS_POOL.get(mood, _PEXELS_POOL["neutral"])
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
                    print(f"  [BrandCover] Pexels: {query} (photo#{photo['id']})")
                    return _crop_916(img)
    except Exception as e:
        print(f"  [BrandCover] Pexels 失败，用渐变: {e}")

    return _gradient_bg(mood)


def _crop_916(img: Image.Image) -> Image.Image:
    w, h = img.size
    if (w / h) > (W / H):
        nw = int(h * W / H)
        img = img.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = int(w * H / W)
        img = img.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    return img.resize((W, H), Image.LANCZOS)


def _gradient_bg(mood: str) -> Image.Image:
    mc = MOOD_COLORS.get(mood, GOLD)
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        r = int(NAVY[0] * (1 - t * 0.3) + mc[0] * t * 0.12)
        g = int(NAVY[1] * (1 - t * 0.3) + mc[1] * t * 0.08)
        b = int(NAVY[2] * (1 - t * 0.3) + mc[2] * t * 0.08)
        draw.line([(0, y), (W, y)], fill=(r, g, b))
    return img


# ── 排版工具 ──────────────────────────────────────────────────────────────── #

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


def _fit_bebas(text: str, max_w: int, start: int = 250, minimum: int = 80) -> ImageFont.FreeTypeFont:
    """从 start 逐步缩小字号直到文字宽度 ≤ max_w。"""
    tmp_draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    size = start
    while size >= minimum:
        f = _bebas(size)
        bb = tmp_draw.textbbox((0, 0), text, font=f)
        if bb[2] - bb[0] <= max_w:
            return f
        size -= 10
    return _bebas(minimum)


def _stroke_text(draw: ImageDraw.ImageDraw, xy, text, font,
                 fill, stroke_fill, stroke_width: int = 4, bold_sim: int = 2):
    """
    绘文字：先黑色描边，再用 fill 色偏移 bold_sim px 模拟加粗，最后画主体。
    bold_sim=0 关闭假粗体；建议标题 2、数字 3。
    """
    x, y = xy
    # 1. 外描边（黑色）
    sw = stroke_width
    for dx in range(-sw, sw + 1):
        for dy in range(-sw, sw + 1):
            if dx == 0 and dy == 0:
                continue
            draw.text((x + dx, y + dy), text, font=font, fill=stroke_fill)
    # 2. 假粗体：用 fill 色在 ±bold_sim 偏移处再画一遍
    if bold_sim:
        for dx, dy in [(-bold_sim, 0), (bold_sim, 0), (0, -bold_sim), (0, bold_sim)]:
            draw.text((x + dx, y + dy), text, font=font, fill=fill)
    # 3. 主体
    draw.text((x, y), text, font=font, fill=fill)


def _draw_shield(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int, color):
    draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=color)
    sw = max(3, r // 7)
    x0, y0 = cx - r // 2 + 4, cy + 4
    xm, ym = cx - r // 10, cy + r // 3
    x1, y1 = cx + r // 2 - 2, cy - r // 3
    draw.line([(x0, y0), (xm, ym)], fill=WHITE, width=sw)
    draw.line([(xm, ym), (x1, y1)], fill=WHITE, width=sw)


# ── 主函数 ────────────────────────────────────────────────────────────────── #

def make_brand_cover(
    title: str,
    caption: str,
    mood: str,
    output_path: str,
    big_number: str = "",
    impact_word: str = "",
    accent_color: tuple[int, int, int] | None = None,
    bg_image_path: str = "",
    seed: int = 0,
) -> str:
    """
    生成 1080×1920 CNcar 品牌封面。

    title       : 顶部大标题（Bebas Neue 白色+黑描边，自适应行数）
    caption     : 底部钩子句（底部条内白色）
    mood        : tense / neutral / uplift / data
    big_number  : "$19,340" 等；留空则从 title/caption 自动提取
    impact_word : 数字下方冲击词；留空则按 mood 自动选
    bg_image_path: 本地图路径；留空则走 Pexels
    seed        : 控制 Pexels 查询轮换
    """
    mood = mood if mood in MOOD_COLORS else "data"
    mc   = MOOD_COLORS[mood]
    accent = accent_color or mc

    # 自动提取巨型数字
    if not big_number:
        found = re.findall(r'(?:\$[\d,]+|\+?\d+%)', f"{title} {caption}")
        big_number = found[0] if found else ""

    # 自动选冲击词
    if not impact_word:
        impact_word = (
            _IMPACT_DEFAULT.get(mood, "LANDED") if big_number
            else _IMPACT_FALLBACK.get(mood, "RED FLAG")
        )

    # ── 1. 背景 ───────────────────────────────────────────────────────── #
    bg = _fetch_bg(mood, seed, bg_image_path)

    # ── 2. 暗化遮罩（62%）─────────────────────────────────────────────── #
    canvas = Image.alpha_composite(
        bg.convert("RGBA"),
        Image.new("RGBA", (W, H), (0, 0, 0, 158)),
    )

    # ── 3. 顶部 navy 渐变（y=0→440）───────────────────────────────────── #
    top_grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    tgd = ImageDraw.Draw(top_grad)
    for y in range(440):
        t = 1 - y / 440
        tgd.line([(0, y), (W, y)], fill=(*NAVY, int(215 * t ** 0.6)))
    canvas = Image.alpha_composite(canvas, top_grad)

    # ── 4. 底部渐变（y=1520→底部）──────────────────────────────────────── #
    bot_grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bgd = ImageDraw.Draw(bot_grad)
    for y in range(1520, H):
        t = (y - 1520) / (H - 1520)
        bgd.line([(0, y), (W, y)], fill=(0, 0, 0, int(175 * t)))
    canvas = Image.alpha_composite(canvas, bot_grad)

    # ── 5. 左侧竖色条（16px 全高）──────────────────────────────────────── #
    stripe = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(stripe).rectangle([(0, 0), (16, H)], fill=(*mc, 255))
    canvas = Image.alpha_composite(canvas, stripe)

    img  = canvas.convert("RGB")
    draw = ImageDraw.Draw(img)

    # ── 6. 大标题（自适应字号：1行112 / 2行88 / 3行70）─────────────────── #
    title_up = title.upper()
    chosen_font, chosen_lines = None, None
    for sz in (112, 88, 70):
        f = _bebas(sz)
        lns = _wrap(title_up, f, MAX_TW, draw)
        if len(lns) <= 3:
            chosen_font, chosen_lines = f, lns[:3]
            break
    if chosen_font is None:
        chosen_font = _bebas(70)
        chosen_lines = _wrap(title_up, chosen_font, MAX_TW, draw)[:3]

    line_h = chosen_font.size + 10
    y_cur  = 80
    for ln in chosen_lines:
        _stroke_text(draw, (PAD_X, y_cur), ln, chosen_font,
                     fill=WHITE, stroke_fill=(*BLACK, 210), stroke_width=4, bold_sim=2)
        y_cur += line_h

    # ── 7. 巨型数字 + 冲击词（垂直居中于 y=520-1580 区间）─────────────── #
    NUM_MAX_W = W - 120

    if big_number:
        f_num = _fit_bebas(big_number, NUM_MAX_W, start=250)
        bb_num = draw.textbbox((0, 0), big_number, font=f_num)
        num_h = bb_num[3] - bb_num[1]
    else:
        f_num, num_h = None, 0

    f_imp  = _bebas(82)
    bb_imp = draw.textbbox((0, 0), impact_word, font=f_imp)
    imp_h  = bb_imp[3] - bb_imp[1]

    gap     = 20
    total_h = num_h + (gap + imp_h if big_number else imp_h)
    zone_c  = (520 + 1580) // 2
    y_num   = zone_c - total_h // 2
    y_imp   = y_num + num_h + (gap if big_number else 0)

    if big_number and f_num:
        bb = draw.textbbox((0, 0), big_number, font=f_num)
        x  = (W - (bb[2] - bb[0])) // 2
        _stroke_text(draw, (x, y_num), big_number, f_num,
                     fill=accent, stroke_fill=(*BLACK, 220), stroke_width=6, bold_sim=3)

    bb  = draw.textbbox((0, 0), impact_word, font=f_imp)
    x   = (W - (bb[2] - bb[0])) // 2
    _stroke_text(draw, (x, y_imp), impact_word, f_imp,
                 fill=accent if accent_color else WHITE,
                 stroke_fill=(*BLACK, 180), stroke_width=3, bold_sim=2)

    # ── 8. 底部钩子条（y=1640, h=190, 左彩边14px, 半透明黑底）──────────── #
    BAR_Y, BAR_H, BORDER = 1640, 190, 14
    bar_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bar_layer)
    bd.rectangle([(0, BAR_Y), (W, BAR_Y + BAR_H)], fill=(0, 0, 0, 184))
    bd.rectangle([(0, BAR_Y), (BORDER, BAR_Y + BAR_H)], fill=(*mc, 255))
    img  = Image.alpha_composite(img.convert("RGBA"), bar_layer).convert("RGB")
    draw = ImageDraw.Draw(img)

    f_cap   = _body(42)
    cap_lns = _wrap(caption, f_cap, W - PAD_X - 30, draw)[:2]
    y_cap   = BAR_Y + 26
    for ln in cap_lns:
        draw.text((PAD_X, y_cap), ln, font=f_cap, fill=WHITE)
        y_cap += 54

    # ── 9. CNcar.io 签名（底部居中）────────────────────────────────────── #
    f_sig = _bebas(38)
    sig   = "CNcar.io"
    bb    = draw.textbbox((0, 0), sig, font=f_sig)
    draw.text(((W - (bb[2] - bb[0])) // 2, 1862), sig, font=f_sig, fill=GOLD)

    # ── 10. 金盾✓（右上角）──────────────────────────────────────────────── #
    _draw_shield(draw, cx=1030, cy=68, r=42, color=GOLD)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    img.save(output_path, "JPEG", quality=93)
    print(f"  [BrandCover] ✅ {output_path}")
    return output_path
