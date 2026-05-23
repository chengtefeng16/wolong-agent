"""
短视频自动化Agent — 主流程编排
用法:
  python main.py                    # 完整流程（读Sheet→生成脚本→合成视频→上传）
  python main.py --step video       # 仅合成视频（需提供 --audio 和 --script）
  python main.py --step upload      # 仅上传（需提供 --video）
  python main.py --demo             # 用示例数据跑完整视频合成（不需要Sheet/YouTube）
"""
import argparse
import json
import os
import sys
import uuid
from datetime import datetime

from modules.config_loader import load_config
from modules.video_composer import VideoComposer


def run_demo(cfg: dict):
    """
    完整 Demo：依次测试 Sheet读取 → ElevenLabs音频 → 视频合成
    每步独立报告，失败不中断后续步骤。
    """
    print("\n=== DEMO 模式：逐步测试各模块 ===\n")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(cfg["output"]["dir"], exist_ok=True)

    sample_script = (
        "你有没有想过，为什么我们越忙，内心越空，"
        "佛法说，苦的根源不是外境，而是我们抓住不放的执念，"
        "试着今天放下一件事，只是一件，看看会发生什么，"
    )
    sample_title = "越忙越空"
    sample_quote = "苦，来自执着"

    # ── Step 1: Google Sheet ──────────────────────────────────────────
    print("【1/3】测试 Google Sheet 读取...")
    sheet_ok = False
    materials = []
    try:
        from modules.sheet_reader import SheetReader
        reader = SheetReader(cfg)
        materials = reader.get_unused_material(count=2)
        # 展示第一条素材内容
        cols = cfg["direction"]["google_sheet"]["columns"]
        for i, m in enumerate(materials, 1):
            preview = str(m.get(cols["source_text"], m.get("A", "")))[:60]
            print(f"  素材{i}: {preview}...")
        sheet_ok = True
        print(f"  ✅ Google Sheet 读取成功\n")
        # 如果从 Sheet 读到内容，用真实素材拼接脚本
        sample_script = "，".join(
            str(m.get(cols["source_text"], m.get("A", "")))[:80]
            for m in materials
        ) + "，"
    except Exception as e:
        print(f"  ⚠️  Google Sheet 读取失败: {e}\n  → 继续使用示例脚本\n")

    # ── Step 2: ElevenLabs 音频 ───────────────────────────────────────
    print(f"【2/3】测试 ElevenLabs 音频生成（voice_id: {cfg['api']['elevenlabs_voice_id']}）...")
    audio_path = os.path.join(cfg["output"]["dir"], f"demo_audio_{ts}.mp3")
    audio_ok = False
    try:
        from modules.audio_generator import AudioGenerator
        gen = AudioGenerator(cfg)
        audio_path = gen.generate(sample_script, f"demo_audio_{ts}.mp3")
        audio_ok = True
        print(f"  ✅ 音频生成成功\n")
    except Exception as e:
        print(f"  ⚠️  音频生成失败: {e}")
        # fallback：复用上次的 demo_audio.mp3
        fallback = os.path.join(cfg["output"]["dir"], "demo_audio.mp3")
        if os.path.exists(fallback):
            audio_path = fallback
            print(f"  → 使用已有音频文件继续: {fallback}\n")
        else:
            print(f"  → 无可用音频，仅生成静态封面帧\n")

    # ── Step 3: 视频合成 ───────────────────────────────────────────────
    print("【3/3】合成视频...")
    composer = VideoComposer(cfg)
    if audio_ok or os.path.exists(audio_path):
        out = composer.compose(
            audio_path=audio_path,
            script_text=sample_script,
            output_filename=f"demo_video_{ts}.mp4",
            title=sample_title,
            cover_quote=sample_quote,
        )
        print(f"  ✅ 视频合成成功\n")
    else:
        _run_silent_demo(cfg, sample_script, sample_title, sample_quote)
        return

    composer.make_cover_image(sample_title, sample_quote, f"demo_cover_{ts}.jpg")

    print("=" * 50)
    print(f"✅ Demo 完成！")
    print(f"   Sheet  : {'✅ 读取成功' if sheet_ok else '⚠️  跳过（见上方错误）'}")
    print(f"   Audio  : {'✅ 新音频' if audio_ok else '⚠️  使用旧音频/跳过'}")
    print(f"   Video  : output/demo_video_{ts}.mp4")


def _run_silent_demo(cfg: dict, script: str, title: str, quote: str):
    """无音频版 demo：生成静态封面图，验证画面渲染逻辑"""
    from PIL import Image
    import numpy as np

    composer = VideoComposer(cfg)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    cover_path = composer.make_cover_image(title, quote, f"demo_cover_{ts}.jpg")

    # 生成一张字幕测试帧
    os.makedirs(cfg["output"]["dir"], exist_ok=True)
    bg = composer._make_background(None)
    frame = composer._draw_subtitle_frame(bg, script[:25])
    frame_path = os.path.join(cfg["output"]["dir"], f"demo_frame_{ts}.jpg")
    frame.save(frame_path, "JPEG", quality=90)

    print(f"\n✅ 静态帧测试完成！")
    print(f"   封面图: {cover_path}")
    print(f"   字幕帧: {frame_path}")


def run_full_pipeline(cfg: dict):
    """完整流程"""
    from modules.sheet_reader import SheetReader
    from modules.script_generator import ScriptGenerator
    from modules.audio_generator import AudioGenerator
    from modules.youtube_uploader import YouTubeUploader

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    uid = str(uuid.uuid4())[:8]

    print("\n=== 短视频Agent 启动 ===\n")

    # Step 1: 读取素材
    print("[1/5] 从 Google Sheet 读取素材...")
    reader = SheetReader(cfg)
    materials = reader.get_unused_material(count=3)
    print(f"      已取 {len(materials)} 条素材")

    # Step 2: 生成脚本
    print("[2/5] Gemini 生成选题与脚本...")
    generator = ScriptGenerator(cfg)
    script_data = generator.generate_topic_and_script(materials)
    print(f"      标题: {script_data['title']}")
    print(f"      金句: {script_data['cover_quote']}")

    # 保存脚本 JSON
    script_path = os.path.join(cfg["output"]["dir"], f"script_{ts}_{uid}.json")
    os.makedirs(cfg["output"]["dir"], exist_ok=True)
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(script_data, f, ensure_ascii=False, indent=2)
    print(f"      脚本已保存: {script_path}")

    # Step 3: 生成音频
    print("[3/5] ElevenLabs TTS 生成音频...")
    audio_gen = AudioGenerator(cfg)
    full_text = script_data.get("polished_script", " ".join(
        s["text"] for s in script_data["segments"]
    ))
    audio_path = audio_gen.generate(full_text, f"audio_{ts}_{uid}.mp3")

    # Step 4: 合成视频
    print("[4/5] MoviePy 合成视频...")
    composer = VideoComposer(cfg)
    video_path = composer.compose(
        audio_path=audio_path,
        script_text=full_text,
        output_filename=f"video_{ts}_{uid}.mp4",
        title=script_data["title"],
        cover_quote=script_data["cover_quote"],
    )
    composer.make_cover_image(
        script_data["title"],
        script_data["cover_quote"],
        f"cover_{ts}_{uid}.jpg",
    )

    # Step 5: 上传 YouTube
    print("[5/5] 上传到 YouTube...")
    uploader = YouTubeUploader(cfg)
    video_id = uploader.upload(video_path, script_data)

    print(f"\n✅ 全流程完成!")
    print(f"   YouTube: https://youtu.be/{video_id}")
    print(f"   本地视频: {video_path}")


def main():
    parser = argparse.ArgumentParser(description="短视频自动化Agent")
    parser.add_argument("--step", choices=["all", "video", "upload", "demo"], default="all")
    parser.add_argument("--demo", action="store_true", help="运行 Demo 模式（不需要外部配置）")
    parser.add_argument("--audio", help="音频文件路径（--step video 时使用）")
    parser.add_argument("--script", help="脚本JSON文件路径（--step video 时使用）")
    parser.add_argument("--video", help="视频文件路径（--step upload 时使用）")
    parser.add_argument("--config", default=None, help="自定义配置文件路径")
    args = parser.parse_args()

    cfg = load_config(args.config)

    if args.demo or args.step == "demo":
        run_demo(cfg)
    elif args.step == "all":
        run_full_pipeline(cfg)
    elif args.step == "video":
        if not args.audio or not args.script:
            print("Error: --step video 需要 --audio 和 --script 参数")
            sys.exit(1)
        cfg_out = cfg["output"]["dir"]
        with open(args.script, encoding="utf-8") as f:
            script_data = json.load(f)
        from modules.video_composer import VideoComposer
        composer = VideoComposer(cfg)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        composer.compose(
            audio_path=args.audio,
            script_text=script_data.get("polished_script", ""),
            output_filename=f"video_{ts}.mp4",
        )
    elif args.step == "upload":
        if not args.video or not args.script:
            print("Error: --step upload 需要 --video 和 --script 参数")
            sys.exit(1)
        with open(args.script, encoding="utf-8") as f:
            script_data = json.load(f)
        from modules.youtube_uploader import YouTubeUploader
        uploader = YouTubeUploader(cfg)
        uploader.upload(args.video, script_data)


if __name__ == "__main__":
    main()
