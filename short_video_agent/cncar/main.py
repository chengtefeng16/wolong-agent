"""
CNcar 短视频 Agent — 主入口

用法:
  python cncar/main.py --produce          # 读表 → 生成脚本/音频/视频 → 写入 pending.json（停在此，等人工审核）
  python cncar/main.py --list             # 列出所有待审核视频
  python cncar/main.py --approve <id>     # 人工审核通过后上传 YouTube
  python cncar/main.py --reject <id>      # 拒绝并标记（不上传）
  python cncar/main.py --demo             # 测试模块连通性（不调用 Gemini）
  python cncar/main.py --story cncar/stories/story_01.txt   # 故事线：直接传旁白文案

注意：--produce / --story 生成完视频后写入 pending.json 并退出，不自动上传。
"""
import argparse
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

# 使父级 modules（audio/video/background）可 import
_HERE = Path(__file__).parent
_ROOT = _HERE.parent
sys.path.insert(0, str(_ROOT))

from modules.config_loader import load_config as _load_base
from cncar.modules.sheet_reader import CNcarSheetReader
from cncar.modules.script_generator import CNcarScriptGenerator

PENDING_FILE = _HERE / "pending.json"
OUTPUT_DIR   = _HERE / "output"


# ------------------------------------------------------------------ #
# 配置加载                                                              #
# ------------------------------------------------------------------ #

def load_cncar_config() -> dict:
    """加载 base_config + cncar.yaml，注入 CNcar 专属凭证路径"""
    import yaml
    cfg = _load_base()  # 加载 base_config（含 API keys）

    cncar_yaml = _HERE / "config" / "cncar.yaml"
    with open(cncar_yaml) as f:
        direction_cfg = yaml.safe_load(f)
    cfg["direction"] = direction_cfg

    # CNcar 独立 YouTube 凭证（路径相对于仓库根）
    cfg["api"]["youtube_credentials"] = str(_ROOT / direction_cfg.get(
        "youtube_credentials", "cncar/config/cncar_youtube_credentials.json"
    ))
    cfg["api"]["youtube_token"] = str(_ROOT / direction_cfg.get(
        "youtube_token", "cncar/config/cncar_youtube_token.json"
    ))

    # 覆盖输出目录
    cfg["output"] = {"dir": str(OUTPUT_DIR), "keep_temp": False}
    # CNcar 视频背景色：商务深蓝
    cfg["video"]["background_color"] = [10, 20, 40]
    # CNcar 品牌签名（覆盖 video_composer 里的定心默认值）
    cfg["channel_name"] = "CNcar.io"
    # CNcar 配音音色注入 api（cncar.yaml 的 elevenlabs_voice_id → cfg["api"]）
    cfg["api"]["elevenlabs_voice_id"] = direction_cfg.get(
        "elevenlabs_voice_id", cfg["api"].get("elevenlabs_voice_id", "")
    )

    # CNcar Google Sheets 写入凭证（本地，不进仓库）
    sa_path = os.path.expanduser("~/.config/cncar/gsheets_sa.json")
    cfg["api"]["gsheets_credentials"] = sa_path

    return cfg


# ------------------------------------------------------------------ #
# Pending 队列                                                          #
# ------------------------------------------------------------------ #

def _read_pending() -> list:
    if not PENDING_FILE.exists():
        return []
    with open(PENDING_FILE, encoding="utf-8") as f:
        return json.load(f)


def _write_pending(items: list):
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def _add_pending(entry: dict):
    items = _read_pending()
    items.append(entry)
    _write_pending(items)


# ------------------------------------------------------------------ #
# 生产：Sheet → 脚本 → 音频 → 视频 → pending.json（停止，等审核）        #
# ------------------------------------------------------------------ #

def run_produce(cfg: dict, cover_override: str = None):
    ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
    uid = str(uuid.uuid4())[:6]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    from modules.video_composer import VideoComposer
    from modules.background_generator import BackgroundGenerator
    from modules.audio_generator import AudioGenerator
    from cncar.modules.cover_maker import CNcarCoverMaker
    from cncar.modules.multi_bg_composer import (
        n_images_for_duration, fetch_segment_images, segment_script,
        compose_multi_bg,
    )

    print("\n=== CNcar Agent 生产模式 ===\n")

    # Step 1: 读素材
    print("[1/4] 从工作表2读取素材...")
    reader    = CNcarSheetReader(cfg)
    materials = reader.get_unused_material(count=1)
    material  = materials[0]
    source_row = material.get("_row_number")

    # Step 2: 生成脚本
    print("\n[2/4] 生成脚本...")
    generator   = CNcarScriptGenerator(cfg)
    script_data = generator.generate(material)
    script_data["_source_row"] = source_row
    script_data["landed_cost_usd"] = material.get("landed_cost_usd", "")

    script_path = OUTPUT_DIR / f"script_{ts}_{uid}.json"
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(script_data, f, ensure_ascii=False, indent=2)
    print(f"  脚本: {script_path}")

    # Step 3: TTS 音频
    print(f"\n[3/4] ElevenLabs 生成音频...")
    audio_gen  = AudioGenerator(cfg)
    audio_path = audio_gen.generate(
        script_data["full_script"],
        f"audio_{ts}_{uid}.mp3",
    )

    # Step 4: 视频合成（多背景图）
    print("\n[4/4] 合成视频...")
    composer = VideoComposer(cfg)

    # 4a: 先用音频文件确定时长，决定图片数量
    from moviepy import AudioFileClip as _AFC
    _audio_dur = _AFC(audio_path).duration
    n_bg = n_images_for_duration(_audio_dur)
    print(f"  [MultiBG] 音频时长={_audio_dur:.1f}s → 需要 {n_bg} 张背景图")

    # 4b: 按脚本分段抓对应主题的 Pexels 图
    tmp_bg_dir = str(OUTPUT_DIR / f"multibg_{ts}_{uid}")
    segments = segment_script(script_data["full_script"], n_bg)
    bg_paths = fetch_segment_images(segments, tmp_bg_dir, script_data["title"])

    # 4c: 多图合成（含淡入淡出）
    video_path = compose_multi_bg(
        composer=composer,
        audio_path=audio_path,
        script_text=script_data["full_script"],
        bg_paths=bg_paths,
        output_path=str(OUTPUT_DIR / f"video_{ts}_{uid}.mp4"),
    )
    # 封面：有手动指定则直接用，否则走自动生成
    if cover_override and Path(cover_override).exists():
        import shutil
        cover_path = str(OUTPUT_DIR / f"cover_{ts}_{uid}.jpg")
        shutil.copy2(cover_override, cover_path)
        print(f"  [CNcar Cover] 使用手动封面: {cover_override}")
    else:
        cover_maker = CNcarCoverMaker(cfg)
        cover_path = cover_maker.make(
            script_data, f"cover_{ts}_{uid}.jpg",
            bg_image_path=bg_paths[0] if bg_paths else "",  # 复用视频首帧图
        )

    # 写入 pending.json — 视频文件确实存在才算成功
    if not video_path or not Path(video_path).exists():
        print("❌ 视频文件未生成，跳过写入 pending.json 和 used 标记")
        sys.exit(1)

    pending_id = f"{ts}_{uid}"
    entry = {
        "id":              pending_id,
        "status":          "pending",
        "created_at":      datetime.now().isoformat(),
        "car_model":       script_data.get("car_model", ""),
        "destination":     script_data.get("destination", ""),
        "landed_cost_usd": material.get("landed_cost_usd", ""),
        "report_url":      script_data.get("report_url", ""),
        "title":           script_data["title"],
        "cover_quote":     script_data["cover_quote"],
        "video_path":      str(video_path),
        "cover_path":      str(cover_path),
        "script_path":     str(script_path),
        "_source_row":     source_row,
    }
    _add_pending(entry)

    # 生成成功后自动回填 used — 失败不阻断流程（仅警告）
    if source_row:
        try:
            reader.mark_as_used(source_row)
        except Exception as e:
            print(f"  ⚠️  used 回填失败（不影响视频）: {e}")
    else:
        print("  ⚠️  无 _row_number，跳过 used 回填（公开CSV模式）")

    print("\n" + "=" * 55)
    print(f"✅ 生成完成，已写入 pending.json，等待人工审核")
    print(f"   ID     : {pending_id}")
    print(f"   车型   : {entry['car_model']} → {entry['destination']}")
    print(f"   标题   : {entry['title']}")
    print(f"   视频   : {entry['video_path']}")
    print(f"   封面   : {entry['cover_path']}")
    print(f"\n   审核命令: python cncar/main.py --list")
    print(f"   通过命令: python cncar/main.py --approve {pending_id}")
    print(f"   拒绝命令: python cncar/main.py --reject {pending_id}")


# ------------------------------------------------------------------ #
# 列出待审核                                                             #
# ------------------------------------------------------------------ #

def run_list():
    items = _read_pending()
    if not items:
        print("pending.json 为空，无待审核视频。")
        return
    print(f"\n共 {len(items)} 条待处理记录：\n")
    for item in items:
        status = item.get("status", "?")
        icon   = {"pending": "⏳", "approved": "✅", "rejected": "❌"}.get(status, "?")
        source = item.get("source", "cncar")
        src_label = f"[{source}]" if source != "cncar" else ""
        print(f"  {icon} [{status}] {src_label} {item['id']}")
        if source == "story":
            print(f"       故事线: {item.get('story_file','')} | 情绪: {item.get('mood','')} | {item.get('title','')}")
        else:
            print(f"       {item.get('car_model','')} → {item.get('destination','')} | {item.get('title','')}")
        print(f"       视频: {item.get('video_path','')}")
        print()


# ------------------------------------------------------------------ #
# 审核通过 → 上传 YouTube                                                #
# ------------------------------------------------------------------ #

def run_approve(cfg: dict, pending_id: str, privacy: str | None = None):
    items = _read_pending()
    entry = next((x for x in items if x["id"] == pending_id), None)
    if not entry:
        print(f"❌ 未找到 ID={pending_id}")
        sys.exit(1)
    if entry["status"] != "pending":
        print(f"⚠️  该记录状态为 {entry['status']}，非 pending，跳过。")
        return

    video_path  = entry["video_path"]
    script_path = entry["script_path"]
    source_row  = entry.get("_source_row")

    # 故事线 entry 没有独立脚本文件，直接从 pending 里重建 script_data
    if script_path and Path(script_path).exists():
        with open(script_path, encoding="utf-8") as f:
            script_data = json.load(f)
    else:
        script_data = {
            "title":       entry.get("title", ""),
            "cover_quote": entry.get("cover_quote", ""),
            "full_script": "",
            "tags":        [],
            "report_url":  entry.get("report_url", ""),
            "car_model":   entry.get("car_model", ""),
            "destination": entry.get("destination", ""),
        }

    print(f"\n[上传] {entry['title']}")

    from modules.youtube_uploader import YouTubeUploader
    uploader = YouTubeUploader(cfg)
    video_id = uploader.upload(video_path, script_data, privacy=privacy)
    yt_url   = f"https://youtu.be/{video_id}"

    # 上传自定义缩略图
    cover_path = entry.get("cover_path", "")
    if cover_path and Path(cover_path).exists():
        try:
            uploader.set_thumbnail(video_id, cover_path)
            print(f"  [YouTube] 🖼  缩略图已上传")
        except Exception as e:
            print(f"  [YouTube] ⚠️  缩略图上传失败（不影响视频）: {e}")

    print(f"\n🎉 YouTube 发布成功: {yt_url}")

    # 标记素材已用
    if source_row:
        reader = CNcarSheetReader(cfg)
        reader.mark_as_used(source_row)

    # 写入 history.json（与定心共用，source 字段区分数据线/故事线）
    history_path = _ROOT / "history.json"
    history = []
    if history_path.exists():
        with open(history_path, encoding="utf-8") as f:
            history = json.load(f)
    history.append({
        "id":           pending_id,
        "source":       entry.get("source", "cncar"),
        "published_at": datetime.now().isoformat(),
        "youtube_url":  yt_url,
        "title":        entry["title"],
        "car_model":    entry.get("car_model", ""),
        "destination":  entry.get("destination", ""),
        "story_file":   entry.get("story_file", ""),
        "mood":         entry.get("mood", ""),
    })
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    # 更新 pending 状态
    entry["status"]       = "approved"
    entry["youtube_url"]  = yt_url
    entry["approved_at"]  = datetime.now().isoformat()
    _write_pending(items)
    print(f"✅ pending.json 已更新为 approved")


# ------------------------------------------------------------------ #
# 拒绝                                                                  #
# ------------------------------------------------------------------ #

def run_reject(pending_id: str):
    items = _read_pending()
    entry = next((x for x in items if x["id"] == pending_id), None)
    if not entry:
        print(f"❌ 未找到 ID={pending_id}")
        sys.exit(1)
    entry["status"]      = "rejected"
    entry["rejected_at"] = datetime.now().isoformat()
    _write_pending(items)
    print(f"✅ ID={pending_id} 已标记为 rejected")


# ------------------------------------------------------------------ #
# Demo                                                                  #
# ------------------------------------------------------------------ #

def run_demo(cfg: dict):
    print("\n=== CNcar Demo 模式：测试连通性 ===\n")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("【1/2】测试工作表2读取...")
    try:
        reader    = CNcarSheetReader(cfg)
        materials = reader.get_unused_material(count=1)
        print(f"  ✅ 读取成功，返回 {len(materials)} 条")
        for m in materials:
            print(f"     {m.get('car_model','?')} → {m.get('destination','?')}")
    except Exception as e:
        print(f"  ⚠️  读取失败: {e}")

    print("\n【2/2】脚本生成器检查（不实际调用 Gemini）...")
    try:
        gen = CNcarScriptGenerator(cfg)
        # 用预填 copy_en 走快速路径
        result = gen.generate({
            "car_model": "BYD Han 2024", "destination": "UAE",
            "landed_cost_usd": "28500", "report_url": "https://cncar.io/report/demo",
            "copy_en": "Did you know a BYD Han costs less than a Camry in Dubai? Here is the full breakdown.",
            "copy_ar": "", "cover_prompt": "", "used": "",
        })
        print(f"  ✅ 脚本生成器正常，标题: {result['title']}")
    except Exception as e:
        print(f"  ⚠️  脚本生成器失败: {e}")

    print("\n✅ Demo 完成")


# ------------------------------------------------------------------ #
# 故事线：旁白文案 → TTS → 多图视频 → BGM混音 → pending.json           #
# ------------------------------------------------------------------ #

def _parse_story_file(path: str) -> tuple[dict, str]:
    """
    解析 story 文件。

    文件格式：
      mood: tense | neutral | uplift
      title: 封面标题文字
      caption: 视频画面上的钩子句（全程显示，1-2句）
      cover_hook: 封面短冲击词
      cover_number: 封面巨型数字
      cover_impact: 数字的解释词
      visuals: wide shot ... | close-up ... | medium shot ... | close-up ... | medium shot ...
      （空行）
      [旁白正文，只有这部分传给 TTS；visuals 单独作为 Pexels 分镜指令]

    返回 (headers_dict, narration_text)。
    """
    _KNOWN = {
        "mood", "title", "caption", "visuals",
        "cover_hook", "cover_number", "cover_impact",
    }
    headers: dict[str, str] = {}
    narration_lines: list[str] = []
    in_header = True
    with open(path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if in_header:
                if not stripped:          # 空行 → header 结束
                    in_header = False
                    continue
                if ":" in stripped:
                    key, _, val = stripped.partition(":")
                    if key.strip().lower() in _KNOWN:
                        headers[key.strip().lower()] = val.strip()
                        continue
                # 非 header 行在空行前出现 → 直接进旁白
                in_header = False
                narration_lines.append(line)
            else:
                narration_lines.append(line)
    return headers, "".join(narration_lines).strip()


def _clean_cover_hook(value: str, fallback: str) -> str:
    """封面主钩子必须短；模型若误输出多个备选，只采用第一个。"""
    candidate = (value or fallback).split(",", 1)[0].split("|", 1)[0].strip()
    words = candidate.split()
    return " ".join(words[:4]) or "REAL COST"


def run_story(cfg: dict, story_path: str):
    """
    故事线生产：直接读旁白文案文件，不读工作表2。

    story 文件格式（header 块 + 空行 + 旁白正文）：
      mood: tense
      title: $12,000 Gone — A Gulf Car Scam
      caption: $12,000 sent. No car. No refund. Here's what to check.

      A buyer sent $12,000 to a dealer in Guangzhou...

    流程：
      解析 header → TTS（仅旁白正文） → Pexels多背景图（仅旁白正文分段）
      → 视频合成（caption全程固定显示） → BGM混音
      → 封面（统一品牌版式 + 本条视频首张背景图）
      → pending.json（source=story）
    """
    story_file = Path(story_path)
    if not story_file.exists():
        print(f"❌ 故事文件不存在: {story_path}")
        sys.exit(1)

    # ── 解析 header（mood/title/caption）和旁白正文 ──────────────────
    headers, narration = _parse_story_file(story_path)
    if not narration:
        print("❌ 故事文件旁白正文为空（空行后无内容）")
        sys.exit(1)

    title   = headers.get("title", story_file.stem.replace("_", " ").title())
    caption = headers.get("caption", "")
    cover_hook = _clean_cover_hook(headers.get("cover_hook", ""), title)
    cover_number = headers.get("cover_number", "")
    cover_impact = headers.get("cover_impact", "")
    visual_beats = [
        beat.strip() for beat in headers.get("visuals", "").split("|") if beat.strip()
    ]

    ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
    uid = str(uuid.uuid4())[:6]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n=== CNcar 故事线生产模式 ===")
    print(f"  文件   : {story_path}")
    print(f"  标题   : {title}")
    print(f"  Caption: {caption or '(未指定，不显示画面字)'}")
    print(f"  分镜   : {len(visual_beats)} 条{'（故事推进模式）' if visual_beats else '（兼容旧版自动匹配）'}")
    print(f"  旁白字数: {len(narration)}\n")

    from modules.audio_generator import AudioGenerator
    from modules.video_composer import VideoComposer
    from moviepy import AudioFileClip as _AFC
    from cncar.modules.multi_bg_composer import (
        n_images_for_duration, fetch_segment_images, segment_script, compose_multi_bg,
        pick_hook_image,
    )
    from cncar.modules.bgm_selector import BgmSelector, mix_bgm_into_video

    # ── Step 1: TTS（只传旁白正文，header 绝不传入）──────────────────
    print("[1/4] 生成配音（edge-tts）...")
    audio_gen  = AudioGenerator(cfg)
    audio_path = audio_gen.generate(narration, f"audio_{ts}_{uid}.mp3")

    # ── Step 2: 背景图（Pexels 分段搜索只用旁白正文）────────────────
    _audio_dur = _AFC(audio_path).duration
    n_bg = n_images_for_duration(_audio_dur)
    print(f"\n[2/4] 抓取背景图（时长={_audio_dur:.1f}s → {n_bg} 张）...")
    tmp_bg_dir = str(OUTPUT_DIR / f"multibg_{ts}_{uid}")
    segments   = segment_script(narration, n_bg)          # 只分旁白正文
    bg_paths   = fetch_segment_images(
        segments, tmp_bg_dir, story_file.stem, visual_beats=visual_beats
    )
    hook_path = pick_hook_image(title)

    # ── Step 3: 视频合成（caption 全程固定显示）──────────────────────
    print("\n[3/4] 合成视频...")
    composer   = VideoComposer(cfg)
    video_path = compose_multi_bg(
        composer=composer,
        audio_path=audio_path,
        script_text=narration,            # 只用于 Pexels 主题判断（已通过 segments 传完）
        bg_paths=bg_paths,
        output_path=str(OUTPUT_DIR / f"video_{ts}_{uid}.mp4"),
        caption=caption,                  # 空字符串 = 无画面字；非空 = 全程固定钩子
        visual_beats=visual_beats,
        hook_image_path=hook_path,
    )

    # ── Step 3.5: BGM 混音 ────────────────────────────────────────────
    bgm_sel  = BgmSelector()
    # 优先使用文件里的 mood 标注，避免重读文件
    mood_tag = headers.get("mood", "")
    if mood_tag in ("tense", "neutral", "uplift"):
        mood = mood_tag
        print(f"  [BGM] 情绪: {mood}  (文件标注)")
    else:
        mood = bgm_sel.detect_mood(narration)
        print(f"  [BGM] 情绪: {mood}  (关键词兜底)")
    bgm_path = bgm_sel.select(mood)
    if bgm_path:
        print(f"\n[3.5/4] 混入背景音乐（{mood} / {Path(bgm_path).name}）...")
        mix_bgm_into_video(video_path, bgm_path)
    else:
        print(f"\n[3.5/4] 跳过背景音乐（bgm/{mood}/ 目录为空）")

    # ── Step 4: 品牌封面 ─────────────────────────────────────────────────
    print("\n[4/4] 生成封面...")
    import re as _re, hashlib as _hs
    from cncar.modules.brand_cover import make_brand_cover
    cover_path = str(OUTPUT_DIR / f"cover_{ts}_{uid}.jpg")
    _seed = int(_hs.md5(title.encode()).hexdigest(), 16)
    # 从 title / caption 提取金额作为巨型数字
    _nums = _re.findall(r'(?:\$[\d,]+|\+?\d+%)', f"{title} {caption or ''}")
    _big_num = cover_number or (_nums[0] if _nums else "")
    make_brand_cover(
        title=cover_hook,
        caption=caption or narration[:80],
        mood=mood,
        output_path=cover_path,
        big_number=_big_num,
        impact_word=cover_impact,
        accent_color=(200, 55, 45),
        # 封面沿用本条视频已成功获取的首张背景图，避免额外联网抓图失败时退化成纯色。
        bg_image_path=bg_paths[0] if bg_paths else "",
        seed=_seed,
    )

    # ── 写入 pending.json ─────────────────────────────────────────────
    if not video_path or not Path(video_path).exists():
        print("❌ 视频文件未生成，退出")
        sys.exit(1)

    cover_quote = caption or narration[:80] + ("…" if len(narration) > 80 else "")

    pending_id = f"{ts}_{uid}"
    entry = {
        "id":              pending_id,
        "status":          "pending",
        "source":          "story",
        "story_file":      story_file.name,
        "mood":            mood,
        "created_at":      datetime.now().isoformat(),
        "car_model":       "",
        "destination":     "",
        "landed_cost_usd": "",
        "report_url":      "https://cncar.io/cost-calculator",
        "title":           title,
        "cover_quote":     cover_quote,
        "video_path":      str(video_path),
        "cover_path":      str(cover_path),
        "script_path":     "",
        "_source_row":     None,
    }
    _add_pending(entry)

    print("\n" + "=" * 55)
    print(f"✅ 故事线视频已写入 pending.json，等待人工审核")
    print(f"   ID     : {pending_id}")
    print(f"   情绪   : {mood}")
    print(f"   时长   : {_audio_dur:.1f}s")
    print(f"   视频   : {video_path}")
    print(f"   封面   : {cover_path}")
    print(f"\n   审核命令: python3 cncar/main.py --list")
    print(f"   通过命令: python3 cncar/main.py --approve {pending_id}")
    print(f"   拒绝命令: python3 cncar/main.py --reject {pending_id}")


# ------------------------------------------------------------------ #
# 选题：自动挑选 → 交互输入成本+链接 → 直接写表                          #
# ------------------------------------------------------------------ #

def run_write_sheet(cfg: dict):
    """
    自动挑选本次选题，引导用户去 cncar.io 算真实成本、拿分享链接，
    输入后直接写入工作表2（不再手动粘贴）。
    """
    from cncar.modules.topic_selector import select_topic

    print("\n=== CNcar 选题 → 写表（交互模式）===\n")

    car_model, destination, iso2, fob_ref = select_topic(cfg)

    print(f"  本次选题：{car_model} → {destination}")
    print(f"  参考 FOB：${fob_ref:,} USD\n")
    print("─" * 60)
    print("请打开 https://cncar.io/cost-calculator，填入：")
    print(f"  FOB 价格 ：${fob_ref:,}")
    print(f"  目的国   ：{destination}（{iso2}）")
    print('  点击"计算"，再点击"Share Report"拿分享链接')
    print("─" * 60)

    # 交互输入
    while True:
        cost_str = input("\n输入 Landed Cost Total（USD，纯数字）：").strip().replace(",", "")
        if cost_str.replace(".", "").isdigit():
            break
        print("  格式错误，请只输入数字（如 18500）")

    while True:
        share_url = input("输入 Share Report URL（https://cncar.io/report/share/...）：").strip()
        if share_url.startswith("https://cncar.io/report/share/"):
            break
        print("  格式不对，URL 应以 https://cncar.io/report/share/ 开头")

    print(f"\n  车型   ：{car_model}")
    print(f"  目的国 ：{destination}")
    print(f"  成本   ：${cost_str}")
    print(f"  链接   ：{share_url}")
    confirm = input("\n确认写入工作表2？(y/n) ").strip().lower()
    if confirm != "y":
        print("已取消，未写入。")
        return

    reader = CNcarSheetReader(cfg)
    row_num = reader.append_material_row(car_model, destination, cost_str, share_url)
    print(f"\n✅ 已写入工作表2 第{row_num}行（E-H列留空，Gemini 将自动生成文案）")
    print("\n下一步：")
    print("  python3 cncar/main.py --produce")


# ------------------------------------------------------------------ #
# CLI 入口                                                              #
# ------------------------------------------------------------------ #

def main():
    parser = argparse.ArgumentParser(description="CNcar 短视频 Agent")
    parser.add_argument("--produce",     action="store_true", help="生产模式（生成视频，停在 pending）")
    parser.add_argument("--cover",       metavar="PATH",      help="手动指定封面图片路径（临时覆盖自动生成）")
    parser.add_argument("--list",        action="store_true", help="列出待审核视频")
    parser.add_argument("--approve",     metavar="ID",        help="审核通过并上传 YouTube")
    parser.add_argument("--public",      action="store_true", help="与 --approve 一起使用，直接公开发布")
    parser.add_argument("--reject",      metavar="ID",        help="拒绝该视频")
    parser.add_argument("--demo",        action="store_true", help="测试模块连通性")
    parser.add_argument("--write-sheet", action="store_true", help="自动选题→交互输入成本+链接→直接写表")
    parser.add_argument("--story",       metavar="FILE",      help="故事线：直接指定旁白文案文件（.txt）生成视频")
    parser.add_argument("--auto-story",  action="store_true", help="故事线：Gemini 自动选题生成脚本再生成视频")
    args = parser.parse_args()

    if args.list:
        run_list()
        return

    if args.reject:
        run_reject(args.reject)
        return

    cfg = load_cncar_config()

    if args.demo:
        run_demo(cfg)
    elif args.produce:
        run_produce(cfg, cover_override=getattr(args, "cover", None))
    elif args.approve:
        run_approve(cfg, args.approve, privacy="public" if args.public else None)
    elif args.public:
        parser.error("--public 只能与 --approve <ID> 一起使用")
    elif getattr(args, "write_sheet", False):
        run_write_sheet(cfg)
    elif args.story:
        run_story(cfg, args.story)
    elif args.auto_story:
        from cncar.modules.story_generator import generate_story
        story_file = generate_story(cfg)
        run_story(cfg, story_file)
    else:
        print("请指定模式：--produce / --list / --approve <id> / --reject <id> / --demo / --write-sheet / --story <file> / --auto-story")
        parser.print_help()


if __name__ == "__main__":
    main()
