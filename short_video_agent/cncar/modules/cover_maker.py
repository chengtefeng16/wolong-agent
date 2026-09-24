"""CNcar 封面生成器 — 高点击率钩子布局

布局（9:16，从上到下）：
  ┌────────────────────────────────┐
  │  [亮调 Pexels 背景 + 深色叠层]   │
  │                                │
  │  "Real landed cost 👇"         │  ← 钩子问句（54px 白色，顶部 12%）
  │                                │
  │  BYD Han EV 2024 → UAE         │  ← 副标题（52px 白色）
  │  ████████████████████████████  │  ← 半透明深色底板
  │       $19,340                  │  ← 主角数字（120px 金色）
  │                                │
  │  ──────── 金色分隔线 ────────   │
  │            CNcar.io            │  ← 品牌签名（42px 金色）
  └────────────────────────────────┘

亮调筛选：
  - 关键词加 sunny/bright/modern 修饰
  - 像素平均亮度 < brightness_min 时丢弃重抓（最多 brightness_retries 次）

钩子文案：
  - 从 cncar.yaml cover.hook_lines / hook_lines_ar 读取
  - 按 title_seed md5 轮换，保证同一视频固定不跳
"""
import hashlib
import io
import os
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont, ImageStat

GOLD = (255, 200, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

_HERE = Path(__file__).parent
_FONTS_DIR = _HERE.parent.parent.parent / "assets" / "fonts"
_BASE_COVER = _HERE.parent / "assets" / "cover_me.jpg"

# 变量数据区：69%~84%（跳过"Safe Deal"62%止，停在"CNcar.io"84%前）
# 像素测量值：Chery Tiggo 71-74%, CHINA→UAE 74-76%, 价格 81-82%
_ZONE_TOP_PCT = 0.69
_ZONE_BOT_PCT = 0.84

FONT_CANDIDATES = [
    _FONTS_DIR / "NotoSansSC-Bold.ttf",
    Path("/Library/Fonts/Arial Unicode.ttf"),
    Path("/System/Library/Fonts/STHeiti Medium.ttc"),
    Path("/System/Library/Fonts/STHeiti Light.ttc"),
]

# 封面专用关键词：亮调、有活力
COVER_QUERIES = [
    "sunny bright modern car dealership showroom",
    "modern bright Dubai car showroom luxury",
    "sunny car auction energy crowd daylight",
    "bright professional car lot lineup daytime",
    "modern auto expo showroom bright lights",
]

PEXELS_KEY = "P0a88apfxfsKw2wzW5BK8fIpIq5mui64iDGbqUGHZpxoH3M9igl2HoNK"


def overlay_title(
    base_path: str,
    line1: str,
    output_path: str,
    line2: str = "",
    W: int = 1080,
    H: int = 1920,
) -> str:
    """
    数据线 + 故事线共用的封面叠字函数。

    以 base_path（cover_me.jpg）为底图，在变量数据区
    （y = 63%~81%，刚好覆盖旧车型/价格区域）叠一个半透明
    黑色遮罩，然后居中写标题：
      - line1  白色粗体（车型信息 或 故事标题）
      - line2  金色副标（落地价，故事线留空）
    支持自动折行，最多两行。
    """
    img = Image.open(base_path).convert("RGB").resize((W, H), Image.LANCZOS)

    zone_top = int(H * _ZONE_TOP_PCT)
    zone_bot = int(H * _ZONE_BOT_PCT)

    # 半透明遮罩覆盖变量数据区
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle([(0, zone_top), (W, zone_bot)], fill=(0, 0, 0, 215))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    def _get_font(size: int) -> ImageFont.FreeTypeFont:
        for path in FONT_CANDIDATES:
            if Path(path).exists():
                try:
                    return ImageFont.truetype(str(path), size)
                except Exception:
                    continue
        return ImageFont.load_default(size=size)

    def _wrap(text: str, fnt: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
        words = text.split()
        lines, cur = [], []
        for word in words:
            test = " ".join(cur + [word])
            if draw.textbbox((0, 0), test, font=fnt)[2] > max_w and cur:
                lines.append(" ".join(cur))
                cur = [word]
            else:
                cur.append(word)
        if cur:
            lines.append(" ".join(cur))
        return lines

    def _draw_lines(lines: list[str], fnt: ImageFont.FreeTypeFont,
                    color: tuple, start_y: int, line_gap: int):
        for ln in lines:
            bb = draw.textbbox((0, 0), ln, font=fnt)
            x = (W - (bb[2] - bb[0])) // 2
            draw.text((x + 2, start_y + 2), ln, font=fnt, fill=BLACK)  # shadow
            draw.text((x, start_y), ln, font=fnt, fill=color)
            start_y += line_gap
        return start_y

    zone_h = zone_bot - zone_top
    pad_x = 80

    if line2:
        f1, f2 = _get_font(68), _get_font(54)
        lns1 = _wrap(line1, f1, W - pad_x * 2)
        lns2 = _wrap(line2, f2, W - pad_x * 2)
        gap = 20
        total_h = len(lns1) * (68 + 10) + gap + len(lns2) * (54 + 10)
        y = zone_top + max((zone_h - total_h) // 2, 20)
        y = _draw_lines(lns1, f1, WHITE, y, 68 + 10)
        y += gap
        _draw_lines(lns2, f2, GOLD, y, 54 + 10)
    else:
        # 单行标题：逐级缩小字号直到能在两行内显示
        f = _get_font(72)
        lns = _wrap(line1, f, W - pad_x * 2)
        if len(lns) > 2:
            f = _get_font(60)
            lns = _wrap(line1, f, W - pad_x * 2)
        if len(lns) > 2:
            f = _get_font(50)
            lns = _wrap(line1, f, W - pad_x * 2)
        size = 72 if len(_wrap(line1, _get_font(72), W - pad_x * 2)) <= 2 else 60
        line_gap = size + 12
        total_h = len(lns) * line_gap
        y = zone_top + max((zone_h - total_h) // 2, 20)
        for ln in lns:
            bb = draw.textbbox((0, 0), ln, font=f)
            x = (W - (bb[2] - bb[0])) // 2
            for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
                draw.text((x + dx, y + dy), ln, font=f, fill=BLACK)
            draw.text((x, y), ln, font=f, fill=WHITE)
            y += line_gap

    img.save(output_path, "JPEG", quality=92)
    print(f"  [Cover] ✅ 封面已生成: {output_path}")
    return output_path


class CNcarCoverMaker:
    W = 1080
    H = 1920

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.output_dir = cfg["output"]["dir"]
        self._cover_cfg = cfg.get("cover", {})
        self._font_cache: dict = {}

    # ------------------------------------------------------------------ #

    def make(self, script_data: dict, filename: str,
             bg_image_path: str = "") -> str:
        """bg_image_path: 优先用视频首帧图；留空则 make_brand_cover 自行从 Pexels 抓图。"""
        out_path = os.path.join(self.output_dir, filename)
        os.makedirs(self.output_dir, exist_ok=True)

        import hashlib as _hs
        from cncar.modules.brand_cover import make_brand_cover

        car_model   = script_data.get("car_model", "")
        destination = script_data.get("destination", "")
        landed_cost = str(script_data.get("landed_cost_usd", "")).strip()
        title       = script_data.get("title", "")

        # 封面顶部大标题：优先用 AI 生成的带数字钩子标题，
        # 退回到 "车型 → 目的国" 作为上下文兜底。
        hook = title if title else (
            f"{car_model} → {destination}" if (car_model or destination) else "CNcar"
        )

        # 底部钩子句：用脚本的 cover_quote（已是最抓眼的一句话）
        caption = (
            script_data.get("cover_quote", "")
            or (f"Landed ≈ ${landed_cost}" if landed_cost else hook)
        )

        big_number = ""
        if landed_cost:
            try:
                big_number = f"${int(float(landed_cost)):,}"
            except Exception:
                pass

        seed = int(_hs.md5(title.encode()).hexdigest(), 16)

        make_brand_cover(
            title=hook,
            caption=caption,
            mood="data",
            output_path=out_path,
            big_number=big_number,
            impact_word="LANDED",
            bg_image_path=bg_image_path,   # 调用方传视频首帧图；留空→Pexels
            seed=seed,
        )
        return out_path

    # ── 背景（亮调筛选）──────────────────────────────────────────────── #

    def _avg_brightness(self, img: Image.Image) -> float:
        thumb = img.resize((100, 100)).convert("L")
        return ImageStat.Stat(thumb).mean[0]

    def _get_background(self, script_data: dict) -> Image.Image:
        title = script_data.get("title", "")
        seed = int(hashlib.md5(title.encode()).hexdigest(), 16)
        query = COVER_QUERIES[seed % len(COVER_QUERIES)]
        print(f"  [CNcar Cover] Pexels背景: {query}")

        bmin = self._cover_cfg.get("brightness_min", 90)
        retries = self._cover_cfg.get("brightness_retries", 5)

        best_img: Image.Image | None = None
        best_brightness = -1.0

        try:
            resp = requests.get(
                "https://api.pexels.com/v1/search",
                headers={"Authorization": PEXELS_KEY},
                params={"query": query, "orientation": "portrait", "per_page": 15},
                timeout=15,
            )
            if resp.status_code == 200:
                photos = resp.json().get("photos", [])
                for attempt in range(min(retries, len(photos))):
                    photo = photos[(seed + attempt) % len(photos)]
                    r = requests.get(photo["src"]["large2x"], timeout=20)
                    if r.status_code != 200:
                        continue
                    candidate = Image.open(io.BytesIO(r.content)).convert("RGB")
                    brightness = self._avg_brightness(candidate)
                    print(f"  [CNcar Cover] 亮度={brightness:.1f} (阈值{bmin}) photo#{photo['id']}")
                    if brightness >= bmin:
                        print("  [CNcar Cover] Pexels ✅")
                        return self._crop_to_ratio(candidate)
                    if brightness > best_brightness:
                        best_brightness = brightness
                        best_img = candidate
                if best_img is not None:
                    print(f"  [CNcar Cover] ⚠️  全部偏暗，取最亮(亮度={best_brightness:.1f})")
                    return self._crop_to_ratio(best_img)
        except Exception as e:
            print(f"  [CNcar Cover] Pexels失败，用渐变: {e}")

        return self._gradient_bg()

    def _crop_to_ratio(self, img: Image.Image) -> Image.Image:
        w, h = img.size
        target = self.W / self.H
        if (w / h) > target:
            new_w = int(h * target)
            img = img.crop(((w - new_w) // 2, 0, (w - new_w) // 2 + new_w, h))
        else:
            new_h = int(w / target)
            img = img.crop((0, (h - new_h) // 2, w, (h - new_h) // 2 + new_h))
        return img.resize((self.W, self.H), Image.LANCZOS)

    def _gradient_bg(self) -> Image.Image:
        img = Image.new("RGB", (self.W, self.H))
        draw = ImageDraw.Draw(img)
        for y in range(self.H):
            t = y / self.H
            draw.line([(0, y), (self.W, y)], fill=(
                int(8 * (1-t) + 18 * t),
                int(12 * (1-t) + 22 * t),
                int(38 * (1-t) + 55 * t),
            ))
        return img

    # ── 合成 ─────────────────────────────────────────────────────────── #

    def _compose(self, bg: Image.Image, script_data: dict) -> Image.Image:
        overlay = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 150))
        img = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(img)

        car_model = script_data.get("car_model", "")
        destination = script_data.get("destination", "")
        landed_cost = str(script_data.get("landed_cost_usd", "")).strip()
        title = script_data.get("title", car_model)

        # ── 1. 钩子问句（顶部 12%）──────────────────────────────────────
        hook = self._pick_hook(title, script_data.get("language", "en"))
        hook_y = int(self.H * 0.10)
        self._draw_text_centered(draw, hook, self._font(54), WHITE, hook_y,
                                 shadow=True)

        # ── 2. 副标题：车型 + 目的国（钩子下方）────────────────────────
        subtitle = f"{car_model}  →  {destination}"
        sub_y = hook_y + self._text_h(draw, hook, self._font(54)) + 32
        self._draw_text_centered(draw, subtitle, self._font(52), WHITE, sub_y,
                                 shadow=True)

        # ── 3. 主角数字：半透明底板 + 金色大字（视觉中心 42–58%）───────
        price_text = f"${landed_cost}"
        price_font = self._font(120)
        price_h = self._text_h(draw, price_text, price_font)

        pad_v, pad_h = 28, 40
        plate_top = int(self.H * 0.42)
        plate_bot = plate_top + price_h + pad_v * 2

        # 半透明深色底板
        plate = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))
        pd = ImageDraw.Draw(plate)
        pd.rectangle([(pad_h, plate_top), (self.W - pad_h, plate_bot)],
                     fill=(0, 0, 0, 170))
        img = Image.alpha_composite(img.convert("RGBA"), plate).convert("RGB")
        draw = ImageDraw.Draw(img)

        # 金色数字
        self._draw_text_centered(draw, price_text, price_font, GOLD,
                                 plate_top + pad_v, shadow=True)

        # ── 4. 品牌签名（底部，长 slogan 已移除）────────────────────────
        sep_y = int(self.H * 0.88)
        draw.line([(80, sep_y), (self.W - 80, sep_y)], fill=(*GOLD, 200), width=2)

        sig_font = self._font(42)
        sig_y = sep_y + 20
        self._draw_text_centered(draw, "CNcar.io", sig_font, GOLD, sig_y, shadow=True)

        return img

    # ── 钩子选取 ─────────────────────────────────────────────────────── #

    def _pick_hook(self, title_seed: str, language: str = "en") -> str:
        key = f"hook_lines_ar" if language.startswith("ar") else "hook_lines"
        lines = self._cover_cfg.get(key) or self._cover_cfg.get("hook_lines", [])
        if not lines:
            return "Real landed cost 👇"
        seed = int(hashlib.md5(title_seed.encode()).hexdigest(), 16)
        return lines[seed % len(lines)]

    # ── 绘图工具 ─────────────────────────────────────────────────────── #

    def _draw_text_centered(self, draw: ImageDraw.ImageDraw, text: str,
                             font: ImageFont.FreeTypeFont, color: tuple,
                             y: int, shadow: bool = False):
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        x = (self.W - w) // 2
        if shadow:
            draw.text((x + 3, y + 3), text, font=font, fill=(*BLACK, 200))
        draw.text((x, y), text, font=font, fill=color)

    def _text_h(self, draw: ImageDraw.ImageDraw, text: str,
                font: ImageFont.FreeTypeFont) -> int:
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[3] - bbox[1]

    def _font(self, size: int) -> ImageFont.FreeTypeFont:
        if size in self._font_cache:
            return self._font_cache[size]
        for path in FONT_CANDIDATES:
            if Path(path).exists():
                try:
                    f = ImageFont.truetype(str(path), size)
                    self._font_cache[size] = f
                    return f
                except Exception:
                    continue
        f = ImageFont.load_default(size=size)
        self._font_cache[size] = f
        return f
