"""
短视频自动化Agent — 主流程编排

用法:
  python main.py --produce          # 完整生产（Sheet→Gemini→TTS→视频，跳过YouTube上传）
  python main.py                    # 完整流程含YouTube上传（需配置OAuth）
  python main.py --demo             # 仅测试各模块连通性（不调用Gemini）
  python main.py --step video       # 仅合成视频（需提供 --audio 和 --script）
  python main.py --step upload      # 仅上传YouTube（需提供 --video 和 --script）
"""
import argparse
import json
import os
import sys
import uuid
from datetime import datetime

from modules.config_loader import load_config
from modules.video_composer import VideoComposer


# ──────────────────────────────────────────────────────────────────────────────
# 完整生产流程（步骤1-4，跳过YouTube）
# ──────────────────────────────────────────────────────────────────────────────

def run_produce(cfg: dict):
    """Sheet → Gemini脚本 → ElevenLabs音频 → MoviePy视频合成"""
    from modules.sheet_reader import SheetReader
    from modules.script_generator import ScriptGenerator
    from modules.audio_generator import AudioGenerator

    ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
    uid = str(uuid.uuid4())[:6]
    os.makedirs(cfg["output"]["dir"], exist_ok=True)

    print("\n=== 短视频Agent 生产模式（步骤1-4）===\n")

    # ── Step 1: 读取素材 ───────────────────────────────────────────────
    print("[1/4] 从 Google Sheet 读取讲义素材...")
    reader    = SheetReader(cfg)
    materials = reader.get_unused_material(count=3)
    cols      = cfg["direction"]["google_sheet"]["columns"]
    for i, m in enumerate(materials, 1):
        preview = str(m.get(cols["source_text"], ""))[:50]
        print(f"      素材{i}: {preview}...")
    print()

    # ── Step 2: Gemini 生成脚本 ────────────────────────────────────────
    print("[2/4] Gemini 生成60秒口播脚本...")
    generator   = ScriptGenerator(cfg)
    script_data = generator.generate(materials)

    print(f"      标题  : {script_data['title']}")
    print(f"      金句  : {script_data['cover_quote']}")
    print(f"      字数  : {len(script_data['full_script'])}字")
    print(f"      脚本预览: {script_data['full_script'][:60]}...")
    print()

    # 保存脚本 JSON（方便后续单步重跑）
    script_path = os.path.join(cfg["output"]["dir"], f"script_{ts}_{uid}.json")
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(script_data, f, ensure_ascii=False, indent=2)
    print(f"      脚本已保存: {script_path}\n")

    # ── Step 3: ElevenLabs TTS ────────────────────────────────────────
    print(f"[3/4] ElevenLabs Sarah 生成音频（voice: {cfg['api']['elevenlabs_voice_id']}）...")
    audio_gen  = AudioGenerator(cfg)
    audio_path = audio_gen.generate(
        script_data["full_script"],
        f"audio_{ts}_{uid}.mp3",
    )
    print()

    # ── Step 4: MoviePy 视频合成 ──────────────────────────────────────
    print("[4/4] MoviePy 合成9:16竖屏视频...")
    composer   = VideoComposer(cfg)
    is_bilingual = cfg["direction"].get("language", "zh") == "zh-en"
    if is_bilingual and script_data.get("en_subtitles"):
        print("  [Video] 双语字幕模式")
        video_path = composer.compose_bilingual(
            audio_path=audio_path,
            script_data=script_data,
            output_filename=f"video_{ts}_{uid}.mp4",
        )
    else:
        video_path = composer.compose(
            audio_path=audio_path,
            script_text=script_data["full_script"],
            output_filename=f"video_{ts}_{uid}.mp4",
            title=script_data["title"],
            cover_quote=script_data["cover_quote"],
        )
    cover_path = composer.make_cover_image(
        script_data["title"],
        script_data["cover_quote"],
        f"cover_{ts}_{uid}.jpg",
    )
    print()

    print("=" * 55)
    print(f"✅ 生产完成！")
    print(f"   标题  : {script_data['title']}")
    print(f"   金句  : {script_data['cover_quote']}")
    print(f"   脚本  : {script_path}")
    print(f"   音频  : {audio_path}")
    print(f"   视频  : {video_path}")
    print(f"   封面  : {cover_path}")
    print(f"\n   下一步: python main.py --step upload --video {video_path} --script {script_path}")
    return video_path, script_data


# ──────────────────────────────────────────────────────────────────────────────
# 完整流程含YouTube上传（步骤1-5）
# ──────────────────────────────────────────────────────────────────────────────

def run_full_pipeline(cfg: dict):
    """完整5步流程，包含YouTube上传"""
    from modules.youtube_uploader import YouTubeUploader

    video_path, script_data = run_produce(cfg)

    print("\n[5/5] 上传到 YouTube...")
    uploader = YouTubeUploader(cfg)
    video_id = uploader.upload(video_path, script_data)
    print(f"\n🎉 YouTube 发布成功: https://youtu.be/{video_id}")


# ──────────────────────────────────────────────────────────────────────────────
# Demo 模式（测试各模块连通性，不调用 Gemini）
# ──────────────────────────────────────────────────────────────────────────────

def run_demo(cfg: dict):
    """依次测试 Sheet读取 → ElevenLabs音频 → 视频合成（跳过Gemini，用示例脚本）"""
    print("\n=== DEMO 模式：测试模块连通性（跳过Gemini）===\n")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(cfg["output"]["dir"], exist_ok=True)

    sample_script = (
        "你有没有想过，为什么我们越忙，内心越空，"
        "佛法说，苦的根源不是外境，而是我们抓住不放的执念，"
        "试着今天放下一件事，只是一件，看看会发生什么，"
    )
    sample_title = "越忙越空"
    sample_quote = "苦，来自执着"

    # Step 1: Google Sheet
    print("【1/3】测试 Google Sheet 读取...")
    sheet_ok = False
    try:
        from modules.sheet_reader import SheetReader
        reader    = SheetReader(cfg)
        materials = reader.get_unused_material(count=2)
        cols      = cfg["direction"]["google_sheet"]["columns"]
        for i, m in enumerate(materials, 1):
            preview = str(m.get(cols["source_text"], ""))[:60]
            print(f"  素材{i}: {preview}...")
        sheet_ok = True
        print(f"  ✅ Google Sheet 读取成功\n")
    except Exception as e:
        print(f"  ⚠️  Google Sheet 读取失败: {e}\n  → 继续使用示例脚本\n")

    # Step 2: ElevenLabs
    print(f"【2/3】测试 ElevenLabs 音频（voice: {cfg['api']['elevenlabs_voice_id']}）...")
    audio_path = os.path.join(cfg["output"]["dir"], f"demo_audio_{ts}.mp3")
    audio_ok   = False
    try:
        from modules.audio_generator import AudioGenerator
        gen        = AudioGenerator(cfg)
        audio_path = gen.generate(sample_script, f"demo_audio_{ts}.mp3")
        audio_ok   = True
        print(f"  ✅ 音频生成成功\n")
    except Exception as e:
        print(f"  ⚠️  音频生成失败: {e}")
        fallback = os.path.join(cfg["output"]["dir"], "demo_audio.mp3")
        if os.path.exists(fallback):
            audio_path = fallback
            print(f"  → 使用已有音频: {fallback}\n")
        else:
            print(f"  → 无可用音频，退出\n")
            return

    # Step 3: 视频合成
    print("【3/3】合成视频...")
    composer   = VideoComposer(cfg)
    video_path = composer.compose(
        audio_path=audio_path,
        script_text=sample_script,
        output_filename=f"demo_video_{ts}.mp4",
        title=sample_title,
        cover_quote=sample_quote,
    )
    composer.make_cover_image(sample_title, sample_quote, f"demo_cover_{ts}.jpg")

    print("=" * 50)
    print(f"✅ Demo 完成！")
    print(f"   Sheet  : {'✅ 读取成功' if sheet_ok else '⚠️  跳过'}")
    print(f"   Audio  : {'✅ 新音频' if audio_ok else '⚠️  使用旧音频'}")
    print(f"   Video  : {video_path}")


# ──────────────────────────────────────────────────────────────────────────────
# CLI 入口
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="短视频自动化Agent")
    parser.add_argument("--produce", action="store_true",
                        help="完整生产模式（步骤1-4，跳过YouTube上传）")
    parser.add_argument("--demo", action="store_true",
                        help="Demo模式（测试连通性，跳过Gemini）")
    parser.add_argument("--step", choices=["video", "upload"],
                        help="单步模式")
    parser.add_argument("--audio",  help="音频文件路径（--step video 时使用）")
    parser.add_argument("--script", help="脚本JSON路径（--step video/upload 时使用）")
    parser.add_argument("--video",  help="视频文件路径（--step upload 时使用）")
    parser.add_argument("--config", default=None, help="自定义配置文件路径")
    args = parser.parse_args()

    cfg = load_config(args.config)

    if args.demo:
        run_demo(cfg)

    elif args.produce:
        run_produce(cfg)

    elif args.step == "video":
        if not args.audio or not args.script:
            print("Error: --step video 需要 --audio 和 --script 参数")
            sys.exit(1)
        with open(args.script, encoding="utf-8") as f:
            script_data = json.load(f)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        VideoComposer(cfg).compose(
            audio_path=args.audio,
            script_text=script_data.get("full_script", ""),
            output_filename=f"video_{ts}.mp4",
            title=script_data.get("title", ""),
            cover_quote=script_data.get("cover_quote", ""),
        )

    elif args.step == "upload":
        if not args.video or not args.script:
            print("Error: --step upload 需要 --video 和 --script 参数")
            sys.exit(1)
        with open(args.script, encoding="utf-8") as f:
            script_data = json.load(f)
        from modules.youtube_uploader import YouTubeUploader
        YouTubeUploader(cfg).upload(args.video, script_data)

    else:
        # 默认：完整5步流程含YouTube
        run_full_pipeline(cfg)


if __name__ == "__main__":
    main()
