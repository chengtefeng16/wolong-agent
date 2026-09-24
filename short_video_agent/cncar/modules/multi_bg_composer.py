"""CNcar 多背景图视频合成器

直接复用 VideoComposer 的字幕渲染方法，不修改定心共享代码。

分段逻辑:
  ≤ 20s  → 1 张
  20–40s → 3 张
  > 40s  → min(5, floor(duration/10)) 张

淡变: CrossFadeIn(0.8s)，并配合 3–4% 的缓慢推近 / 拉远：
  - 每段只做轻微镜头推进，不做跳切或夸张特效
  - 分段按故事中的「场景 → 文件/风险 → 港口/费用 → 核验/CTA」推进
  - 保持同一汽车贸易语境，避免变成无关的素材拼贴

背景叠加补偿公式:
  每张 clip_dur = (audio_dur + (n-1)*FADE_DUR) / n
  保证叠加后总时长 = audio_dur

主题优先级（高 → 低）:
  1 报关/税   customs/duty/VAT/tax/tariff/import
  2 港口/运输 shipping/freight/transport/cargo/ship/port/RoRo
  3 CTA/品牌  report/visit/link/CNcar/cncar/get the/click
  4 车型展厅  car/vehicle/BYD/Seal/model/electric/EV
  5 兜底
"""

import hashlib
import math
import os
import re
from pathlib import Path

import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont

_CAPTION_FONT_CANDIDATES = [
    Path(__file__).parent.parent.parent.parent / "assets" / "fonts" / "NotoSansSC-Bold.ttf",
    Path("/Library/Fonts/Arial Unicode.ttf"),
    Path("/System/Library/Fonts/STHeiti Medium.ttc"),
    Path("/System/Library/Fonts/STHeiti Light.ttc"),
    Path("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJKsc-Bold.otf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
]


def _caption_font(size: int) -> ImageFont.FreeTypeFont:
    for p in _CAPTION_FONT_CANDIDATES:
        if Path(p).exists():
            try:
                return ImageFont.truetype(str(p), size)
            except Exception:
                continue
    return ImageFont.load_default(size=size)


def _make_static_caption_clip(caption: str, duration: float, W: int, H: int):
    """
    Renders a full-frame RGBA overlay: semi-transparent bar at the bottom
    with the caption text in white, static for the entire clip duration.
    Font is one step larger than normal subtitles for readability.
    """
    from moviepy import ImageClip

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Bar: 22% of height, 4% margin from bottom
    bar_h = int(H * 0.22)
    bar_top = H - bar_h - int(H * 0.04)
    draw.rectangle([(0, bar_top), (W, bar_top + bar_h)], fill=(0, 0, 0, 185))

    font_size = 80
    font = _caption_font(font_size)
    max_w = W - 80

    # Word-wrap
    words = caption.split()
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

    line_h = font_size + 14
    total_h = len(lines) * line_h
    y = bar_top + (bar_h - total_h) // 2

    for line in lines:
        bb = draw.textbbox((0, 0), line, font=font)
        x = (W - (bb[2] - bb[0])) // 2
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0, 255))
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        y += line_h

    arr = np.array(img)  # (H, W, 4) RGBA
    return ImageClip(arr, duration=duration)

PEXELS_KEY = "P0a88apfxfsKw2wzW5BK8fIpIq5mui64iDGbqUGHZpxoH3M9igl2HoNK"
FADE_DUR = 0.8  # 淡变秒数
HOOK_DUR = 2.4  # 开头高反差视觉钩子；旁白不中断
_HOOK_DIR = Path(__file__).parent.parent / "assets" / "hook"

THEME_RULES = [
    {
        "name": "documents",
        "triggers": {"certificate", "document", "paperwork", "license", "coc", "registration"},
        "queries": [
            "car import documents close up desk",
            "customs certificate paperwork close up",
            "vehicle export documents inspection",
        ],
    },
    {
        "name": "money",
        "triggers": {"deposit", "fee", "fees", "cost", "paid", "payment", "money", "refund", "loss"},
        "queries": [
            "car buyer reviewing invoice dealership",
            "import cost documents calculator desk",
            "car purchase contract close up hands",
        ],
    },
    {
        "name": "customs",
        "triggers": {"customs", "duty", "vat", "tax", "tariff", "import"},
        "queries": [
            "customs officer port inspection",
            "import export border checkpoint",
            "port customs clearance authority",
        ],
    },
    {
        "name": "shipping",
        "triggers": {"shipping", "freight", "transport", "cargo", "ship", "port", "roro"},
        "queries": [
            "RoRo ship loading cars port",
            "cargo ship automobiles ocean",
            "container port cranes busy",
        ],
    },
    {
        "name": "cta",
        "triggers": {"report", "visit", "link", "cncar", "click", "get the",
                     "breakdown", "detailed", "full report", "see the"},
        "queries": [
            "businessman reviewing contract document",
            "professional car deal handshake",
            "modern Dubai car showroom luxury",
        ],
    },
    {
        "name": "vehicle",
        "triggers": {"car", "vehicle", "byd", "seal", "model", "electric", "ev"},
        "queries": [
            "luxury car dealership showroom interior",
            "car salesman customer dealership",
            "used car lot lineup",
        ],
    },
    {
        "name": "default",
        "triggers": set(),
        "queries": [
            "car auction dealer business",
            "auto export logistics team",
            "SUV desert highway sunrise",
        ],
    },
]


# ── 数量决策 ─────────────────────────────────────────────────────────────── #

def n_images_for_duration(duration: float) -> int:
    if duration <= 20:
        return 1
    if duration <= 40:
        return 3
    # 40–50 秒故事固定使用 5 个镜头：足够讲出起因、问题、后果、成本、核验，
    # 又不会因为过多切换破坏专业感。
    return min(5, max(5, math.ceil(duration / 10)))


def pick_hook_image(seed_text: str) -> str:
    """从本地高反差开场素材中稳定轮换一张；目录为空则优雅跳过。"""
    choices = sorted(
        p for p in _HOOK_DIR.glob("*")
        if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
    )
    if not choices:
        return ""
    seed = int(hashlib.md5(seed_text.encode()).hexdigest(), 16)
    chosen = choices[seed % len(choices)]
    print(f"  [MultiBG] 开场反差钩子: {chosen.name} ({HOOK_DUR:.1f}s)")
    return str(chosen)


# ── 主题检测 ─────────────────────────────────────────────────────────────── #

def theme_for_segment(text: str) -> dict:
    lower = text.lower()
    for theme in THEME_RULES[:-1]:
        if any(re.search(r"\b" + re.escape(t) + r"\b", lower) for t in theme["triggers"]):
            return theme
    return THEME_RULES[-1]


def motion_for_segment(index: int, visual_beat: str = "") -> str:
    """5-mode Ken Burns rotation with beat overrides."""
    beat = visual_beat.lower()
    if "close" in beat:
        return "pull_out"
    if "wide" in beat:
        return "push_in_left" if index % 2 == 0 else "push_in_right"
    _modes = ("push_in_left", "pull_out", "push_in_right", "pull_out_left", "push_in")
    return _modes[index % len(_modes)]


def visual_theme_for_segment(text: str, index: int, total: int) -> dict:
    """让画面随故事推进，而不是仅按单词机械命中。

    开头优先给车/场景建立上下文，结尾稳定落到核验/解决方案；
    中间才根据费用、文件、清关、运输等实际情节选画面。
    """
    if index == 0:
        return next(rule for rule in THEME_RULES if rule["name"] == "vehicle")
    if index == total - 1:
        return next(rule for rule in THEME_RULES if rule["name"] == "cta")
    return theme_for_segment(text)


def _with_car_context(visual_beat: str) -> str:
    """把 Gemini 的分镜转成更适合素材库搜索的汽车贸易画面描述。

    即使模型偶尔写出“phone”或“laptop”，也必须把它放回买车、证件、港口的
    真实语境，避免视频突然变成无关的手机或泛商务素材。
    """
    beat = visual_beat.lower()
    if any(word in beat for word in ("certificate", "license", "document", "paperwork")):
        return "vehicle export certificate document with car key close up"
    if any(word in beat for word in ("phone", "message", "unresponsive", "call")):
        return "car dealer phone message with car key close up"
    if any(word in beat for word in ("laptop", "computer", "verify", "checking")):
        return "car buyer checking vehicle import documents on laptop"
    if any(word in beat for word in ("port", "ship", "cargo", "carrier", "customs")):
        return "cars at import port cargo ship customs inspection"
    if any(word in beat for word in ("invoice", "fee", "cost", "payment", "money")):
        return "car import invoice with vehicle key close up"
    if any(word in beat for word in ("car", "vehicle", "dealership", "key")):
        return visual_beat
    return f"car import {visual_beat}"


# ── 脚本分段 ─────────────────────────────────────────────────────────────── #

def segment_script(text: str, n: int) -> list[str]:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]
    if not sentences:
        return [text] * n
    if len(sentences) <= n:
        result = list(sentences)
        while len(result) < n:
            result.append(sentences[-1])
        return result[:n]
    size = len(sentences) / n
    return [
        " ".join(sentences[round(i * size):round((i + 1) * size)])
        for i in range(n)
    ]


# ── Pexels 抓图 ──────────────────────────────────────────────────────────── #

def _crop_to_916(img: Image.Image, W=1080, H=1920) -> Image.Image:
    w, h = img.size
    if (w / h) > (W / H):
        new_w = int(h * W / H)
        img = img.crop(((w - new_w) // 2, 0, (w - new_w) // 2 + new_w, h))
    else:
        new_h = int(w * H / W)
        img = img.crop((0, (h - new_h) // 2, w, (h - new_h) // 2 + new_h))
    return img.resize((W, H), Image.LANCZOS)



def _has_vehicle_context(photo: dict) -> bool:
    """用 Pexels 自带图片描述做一层低成本语义筛选。"""
    alt = (photo.get("alt") or "").lower()
    vehicle_words = (
        "car", "vehicle", "automobile", "auto", "suv", "ev", "electric vehicle",
        "dealership", "showroom", "car key", "driving", "parking",
    )
    return any(word in alt for word in vehicle_words)


def _fetch_pexels_dedup(query: str, seed: int, out_path: str,
                        used_photo_ids: set, require_vehicle: bool = False) -> "int | None":
    """抓一张 Pexels 图，跳过 used_photo_ids 中已用过的 photo_id。
    成功返回 photo_id，失败返回 None。"""
    try:
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": PEXELS_KEY},
            params={"query": query, "orientation": "portrait", "per_page": 12},
            timeout=15,
        )
        if resp.status_code != 200:
            return None
        photos = resp.json().get("photos", [])
        if not photos:
            return None
        # 从 seed 起依次尝试，跳过已用 photo_id
        for k in range(len(photos)):
            photo = photos[(seed + k) % len(photos)]
            pid = photo["id"]
            if pid in used_photo_ids:
                continue
            # 故事线有明确汽车分镜时，宁可继续找图，也不要混入泛货轮、手机或办公素材。
            if require_vehicle and not _has_vehicle_context(photo):
                continue
            r = requests.get(photo["src"]["large2x"], timeout=20)
            if r.status_code != 200:
                continue
            import io as _io
            img = Image.open(_io.BytesIO(r.content)).convert("RGB")
            _crop_to_916(img).save(out_path, "JPEG", quality=92)
            return pid
        return None
    except Exception:
        return None


def fetch_segment_images(
    segments: list[str], tmp_dir: str, title_seed: str,
    visual_beats: list[str] | None = None,
) -> list[str]:
    """为每段脚本抓 Pexels 图，同一次视频内每段图各不相同。

    去重策略：记录已用 photo_id；同主题需多张时轮询同 query 的不同图，
    取尽后降级到备选 query，最终兜底渐变。
    """
    os.makedirs(tmp_dir, exist_ok=True)
    paths = []
    used_photo_ids: set[int] = set()

    fallback_queries = [
        "car dealership vehicle documents professional",
        "cars import export logistics port",
    ]

    for i, seg in enumerate(segments):
        theme = visual_theme_for_segment(seg, i, len(segments))
        visual_beat = visual_beats[i] if visual_beats and i < len(visual_beats) else ""
        visual_query = _with_car_context(visual_beat) if visual_beat else ""
        base_seed = int(hashlib.md5((title_seed + seg[:20]).encode()).hexdigest(), 16) + i
        out = os.path.join(tmp_dir, f"multibg_seg{i}.jpg")
        success = False

        # Gemini 的分镜先行；无分镜的旧文件继续沿用关键词匹配。
        queries = ([visual_query] if visual_query else []) + theme["queries"] + fallback_queries
        for query in queries:
            if success:
                break
            # 同一 query 最多 12 张轮询（per_page=12），每次偏移 seed
            for offset in range(12):
                seed = base_seed + hash(query) % 100 + offset
                pid = _fetch_pexels_dedup(
                    query, seed, out, used_photo_ids,
                    require_vehicle=bool(visual_beat),
                )
                if pid is not None:
                    used_photo_ids.add(pid)
                    label = visual_beat or theme["name"]
                    print(f"  [MultiBG] 段{i+1}/{len(segments)} [{label}] ← {query} (photo#{pid})")
                    success = True
                    break

        if not success:
            _make_gradient(out)
            print(f"  [MultiBG] 段{i+1} 兜底渐变")

        paths.append(out)
    return paths


def _make_gradient(out_path: str, W=1080, H=1920):
    img = Image.new("RGB", (W, H))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        draw.line([(0, y), (W, y)], fill=(
            int(8 + 12 * t), int(12 + 18 * t), int(38 + 22 * t)
        ))
    img.save(out_path, "JPEG", quality=90)


def _zoom_crop_frame(bg_img: Image.Image, scale: float, dx_frac: float,
                     W: int, H: int) -> np.ndarray:
    """Resize bg_img to scale×(W,H) then crop a W×H tile offset by dx_frac.

    dx_frac: horizontal offset as fraction of W (positive = shift right in source).
    Returns H×W×3 uint8 array — no black edges as long as |dx_frac| ≤ (scale-1)/2.
    """
    new_w = round(W * scale)
    new_h = round(H * scale)
    scaled = bg_img.resize((new_w, new_h), Image.BILINEAR)
    cx = new_w // 2 + round(W * dx_frac)
    cy = new_h // 2
    x0 = max(0, min(cx - W // 2, new_w - W))
    y0 = max(0, min(cy - H // 2, new_h - H))
    return np.array(scaled.crop((x0, y0, x0 + W, y0 + H)))


def _make_motion_background(composer, bg_path: str, duration: float, motion: str):
    """Ken Burns v2: ease-in-out zoom 10% + horizontal pan 3.5%.

    Generates a VideoClip via per-frame PIL resize+crop.
    PIL BILINEAR at 1080×1920 ≈ 3-6 ms/frame — negligible vs encoding.
    """
    from moviepy import VideoClip

    bg_img = composer._make_background(bg_path)
    W, H = composer.W, composer.H
    ZOOM = 0.10   # 1.0 → 1.10 (or 1.10 → 1.0)
    PAN  = 0.035  # max 3.5% lateral drift

    def _ease(t: float) -> float:
        p = min(1.0, t / max(duration, 0.001))
        return (1.0 - math.cos(math.pi * p)) / 2.0

    if motion == "push_in":
        def make_frame(t):
            e = _ease(t)
            return _zoom_crop_frame(bg_img, 1.0 + ZOOM * e, 0.0, W, H)
    elif motion == "push_in_left":
        def make_frame(t):
            e = _ease(t)
            return _zoom_crop_frame(bg_img, 1.0 + ZOOM * e, -PAN * e, W, H)
    elif motion == "push_in_right":
        def make_frame(t):
            e = _ease(t)
            return _zoom_crop_frame(bg_img, 1.0 + ZOOM * e, PAN * e, W, H)
    elif motion == "pull_out_left":
        def make_frame(t):
            e = _ease(t)
            return _zoom_crop_frame(bg_img, 1.0 + ZOOM * (1.0 - e), -PAN * (1.0 - e), W, H)
    else:  # pull_out
        def make_frame(t):
            e = _ease(t)
            return _zoom_crop_frame(bg_img, 1.0 + ZOOM * (1.0 - e), PAN * e * 0.5, W, H)

    clip = VideoClip(make_frame, duration=duration)
    clip.fps = composer.fps
    return clip, bg_img


def _apply_opening_hook(video, composer, hook_image_path: str,
                        caption: str, duration: float):
    """2.4s 开场反差钩子 — 现在也加 Ken Burns push_in，不再是静止帧。"""
    if not hook_image_path or not Path(hook_image_path).exists():
        return video

    from moviepy import CompositeVideoClip
    hook_dur = min(HOOK_DUR, duration)
    hook_bg, _ = _make_motion_background(composer, hook_image_path, hook_dur, "push_in")
    layers = [hook_bg]
    if caption:
        layers.append(_make_static_caption_clip(
            caption, hook_dur, composer.W, composer.H
        ))
    hook = CompositeVideoClip(layers, size=(composer.W, composer.H))
    return CompositeVideoClip([video, hook], size=(composer.W, composer.H))


# ── 大数字砸屏（仅 hook 段，报价→到岸跳变）─────────────────────────────── #

def _render_price_frame(price: str, label: str, W: int, H: int,
                        highlight: bool) -> Image.Image:
    """RGBA overlay: semi-transparent band + label + big price number."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    box_h   = int(H * 0.24)
    box_top = int(H * 0.13)
    draw.rectangle([(0, box_top), (W, box_top + box_h)],
                   fill=(0, 0, 0, 190 if highlight else 155))

    # Label
    lbl_font  = _caption_font(52)
    lbl_color = (255, 210, 0, 255) if highlight else (200, 200, 200, 210)
    lbl_bb    = draw.textbbox((0, 0), label, font=lbl_font)
    lbl_x     = (W - (lbl_bb[2] - lbl_bb[0])) // 2
    lbl_y     = box_top + 18
    draw.text((lbl_x, lbl_y), label, font=lbl_font, fill=lbl_color)

    # Price — auto-shrink to fit
    for psz in (155, 125, 100, 80):
        pfont = _caption_font(psz)
        p_bb  = draw.textbbox((0, 0), price, font=pfont)
        if (p_bb[2] - p_bb[0]) <= W - 60:
            break
    price_color = (255, 75, 55, 255) if highlight else (255, 230, 80, 220)
    px = (W - (p_bb[2] - p_bb[0])) // 2
    py = lbl_y + 58
    draw.text((px + 4, py + 4), price, font=pfont, fill=(0, 0, 0, 160))  # shadow
    draw.text((px, py), price, font=pfont, fill=price_color)

    return img


def _make_number_splash_clips(script_text: str, seg_dur: float, W: int, H: int):
    """Returns two timed ImageClip overlays for the hook segment.

    Smaller price → 'DEALER QUOTE', larger price → 'LANDED COST'.
    Visible window starts after HOOK_DUR (hook image exits).
    Returns [] if <2 prices found or window too short.
    """
    from moviepy import ImageClip

    raw = re.findall(r'\$[\d,]+', script_text)
    if len(raw) < 2:
        return []

    def _num(s: str) -> int:
        return int(re.sub(r'[^\d]', '', s))

    nums = sorted(set(raw[:4]), key=_num)   # deduplicate, sort ascending
    if len(nums) < 2:
        return []
    quote_str, landed_str = nums[0], nums[-1]  # smallest=quote, largest=landed

    after_hook = seg_dur - HOOK_DUR
    if after_hook < 3.0:
        return []

    dur1 = after_hook * 0.38
    dur2 = after_hook * 0.62

    f1 = _render_price_frame(quote_str,  "DEALER QUOTE", W, H, highlight=False)
    f2 = _render_price_frame(landed_str, "LANDED COST",  W, H, highlight=True)

    c1 = ImageClip(np.array(f1), duration=dur1).with_start(HOOK_DUR)
    c2 = ImageClip(np.array(f2), duration=dur2).with_start(HOOK_DUR + dur1)
    return [c1, c2]


# ── 核心：多图合成 ────────────────────────────────────────────────────────── #

def compose_multi_bg(
    composer,            # VideoComposer 实例，复用其字幕渲染方法
    audio_path: str,
    script_text: str,
    bg_paths: list[str],
    output_path: str,
    caption: str = "",   # 故事线专用：若有值则全程静态显示此钩子，忽略逐句字幕
    visual_beats: list[str] | None = None,
    hook_image_path: str = "",
) -> str:
    """
    多背景图视频合成，复用 VideoComposer 的字幕渲染，不修改定心代码。

    caption 模式（故事线）：
      - caption 非空时，画面不显示旁白字幕，改为全程固定一行/两行钩子文字
      - 字体比正常字幕大一级，底部半透明黑条，全程可见

    总时长保证 = audio_dur:
      每段 clip_dur = (audio_dur + (n-1)*FADE_DUR) / n
      concat with padding=-FADE_DUR → sum = audio_dur ✓
    """
    from moviepy import AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips
    from moviepy.video.fx import CrossFadeIn

    audio = AudioFileClip(audio_path)
    audio_dur = audio.duration

    # Trim TTS trailing silence so video ends within 1s of the last spoken word.
    # Edge-TTS typically appends 200-500ms of silence; strip it here.
    try:
        _arr = audio.to_soundarray(fps=800)
        _amp = np.abs(_arr).max(axis=1) if _arr.ndim > 1 else np.abs(_arr)
        _active = np.where(_amp > 0.003)[0]
        if len(_active) > 0:
            _last_s = _active[-1] / 800.0
            _trim_to = min(_last_s + 0.5, audio_dur)  # ≤0.5s tail after last word
            if audio_dur - _trim_to > 0.15:            # only trim if it saves ≥0.15s
                audio = audio.subclipped(0, _trim_to)
                audio_dur = _trim_to
                print(f"  [MultiBG] 结尾静音截除 → 时长={audio_dur:.2f}s")
    except Exception:
        pass  # non-critical: keep original duration on any failure

    n = len(bg_paths)

    print(f"  [MultiBG] 合成 {n} 段，音频时长={audio_dur:.1f}s，淡变={FADE_DUR}s")
    if caption:
        print(f"  [MultiBG] caption模式（全程钩子）: {caption[:60]!r}")

    if n == 1:
        bg_clip, bg_img = _make_motion_background(
            composer, bg_paths[0], audio_dur,
            motion_for_segment(0, visual_beats[0] if visual_beats else "")
        )
        splash = _make_number_splash_clips(script_text, audio_dur, composer.W, composer.H)
        if caption:
            cap_clip = _make_static_caption_clip(caption, audio_dur, composer.W, composer.H)
            video = CompositeVideoClip([bg_clip] + splash + [cap_clip],
                                       size=(composer.W, composer.H))
        else:
            sub_clips = composer._make_subtitle_clips(script_text, audio_dur, bg_img)
            video = CompositeVideoClip([bg_clip] + splash + sub_clips,
                                       size=(composer.W, composer.H))
        video = _apply_opening_hook(video, composer, hook_image_path, caption, audio_dur)
        video = video.with_audio(audio).with_duration(audio_dur)
        video.write_videofile(output_path, fps=composer.fps, codec="libx264",
                              audio_codec="aac", logger=None)
        print(f"  [MultiBG] ✅ 单图，时长={audio_dur:.1f}s")
        return output_path

    # 每段 clip 的时长（补偿叠加缩短）
    clip_dur = (audio_dur + (n - 1) * FADE_DUR) / n
    segments = segment_script(script_text, n)
    # Splash clips for first segment only (hook = first ~8s where prices are stated)
    hook_splash = _make_number_splash_clips(script_text, clip_dur, composer.W, composer.H)

    seg_clips = []
    for i, (bg_path, seg_text) in enumerate(zip(bg_paths, segments)):
        beat = visual_beats[i] if visual_beats and i < len(visual_beats) else ""
        motion = motion_for_segment(i, beat)
        bg_base, bg_img = _make_motion_background(composer, bg_path, clip_dur, motion)
        splash = hook_splash if i == 0 else []
        if caption:
            cap_clip = _make_static_caption_clip(caption, clip_dur, composer.W, composer.H)
            seg = CompositeVideoClip([bg_base] + splash + [cap_clip],
                                     size=(composer.W, composer.H))
        else:
            sub_clips = composer._make_subtitle_clips(seg_text, clip_dur, bg_img)
            seg = CompositeVideoClip([bg_base] + splash + sub_clips,
                                     size=(composer.W, composer.H))

        if i > 0:
            seg = seg.with_effects([CrossFadeIn(FADE_DUR)])

        seg_clips.append(seg)
        print(
            f"  [MultiBG] 段{i+1} clip_dur={clip_dur:.2f}s "
            f"镜头={motion} 分镜={beat or theme_for_segment(seg_text)['name']}"
        )

    final = concatenate_videoclips(seg_clips, method="compose", padding=-FADE_DUR)

    # 校验时长
    expected = audio_dur
    actual = final.duration
    print(f"  [MultiBG] 时长校验: 预期={expected:.2f}s 实际={actual:.2f}s 偏差={actual-expected:+.3f}s")
    if abs(actual - expected) > 0.1:
        print(f"  [MultiBG] ⚠️  强制截断到 {expected:.2f}s")
        final = final.with_duration(expected)

    final = _apply_opening_hook(final, composer, hook_image_path, caption, audio_dur)
    final = final.with_audio(audio)
    final.write_videofile(
        output_path,
        fps=composer.fps,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile=output_path + ".tmp.m4a",
        remove_temp=True,
        logger=None,
    )
    print(f"  [MultiBG] ✅ 多图视频: {output_path}")
    return output_path
