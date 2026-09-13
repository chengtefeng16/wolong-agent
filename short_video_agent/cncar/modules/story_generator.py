"""CNcar 故事线脚本生成器

流程：
  1. 从 story_topics.py 按轮换选一个未用过的选题
  2. 调 Gemini 生成完整故事脚本（mood/title/caption + 旁白）
  3. 保存为 cncar/stories/auto_YYYYMMDD_HHMMSS.txt
  4. 返回文件路径供 run_story() 使用
"""

import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

_HERE = Path(__file__).parent
_STORIES_DIR = _HERE.parent / "stories"
_TOPICS_FILE = _HERE.parent / "config" / "story_topics.py"
_USAGE_FILE = _HERE.parent / "story_topic_usage.json"

SYSTEM_PROMPT = """You are a short-video scriptwriter for CNcar, a platform that helps
overseas Chinese buyers import cars from China to the Gulf region (UAE, Saudi Arabia, Oman, Qatar, Kuwait).

Your audience: overseas Chinese who are considering importing a car,
or who want to avoid scams and hidden costs. They speak English in this video.

Write in a direct, journalistic style — real story, real stakes, clear advice.
The script will be read aloud as voiceover (40–50 seconds when spoken at a natural pace).
"""

SCRIPT_PROMPT = """Write a short video script for CNcar based on this story angle:

ANGLE: {angle}

Output ONLY this exact format (no extra text, no markdown):

mood: {mood}
title: {title_hint}
caption: [ONE punchy hook sentence, max 12 words, present tense]

[blank line]
[Narration: 3–4 short paragraphs. Natural spoken English.
No bullet points. No headers. Each paragraph 2 sentences max.
End with a clear call to action mentioning CNcar.]
"""


def _load_topics():
    import importlib.util
    spec = importlib.util.spec_from_file_location("story_topics", str(_TOPICS_FILE))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.STORY_TOPICS


def _load_usage() -> dict:
    if _USAGE_FILE.exists():
        return json.loads(_USAGE_FILE.read_text())
    return {}


def _save_usage(usage: dict):
    _USAGE_FILE.write_text(json.dumps(usage, indent=2, ensure_ascii=False))


def _pick_topic(topics: list, usage: dict) -> tuple:
    """轮换选题：优先选从未用过的，全部用完后从使用次数最少的开始。"""
    used_counts = {t[0]: usage.get(t[0], 0) for t in topics}
    min_count = min(used_counts.values())
    candidates = [t for t in topics if used_counts[t[0]] == min_count]
    # 用 topic_id 的 hash 做稳定排序，避免每次随机
    seed = int(datetime.utcnow().strftime("%Y%m%d"))
    candidates.sort(key=lambda t: int(hashlib.md5((t[0] + str(seed)).encode()).hexdigest(), 16))
    return candidates[0]


def _title_hint(angle: str) -> str:
    """从 angle 提取前几个词作为标题提示。"""
    words = angle.split()[:8]
    return " ".join(words) + "..."


def generate_story(cfg: dict) -> str:
    """生成一个故事脚本文件，返回文件路径。"""
    gemini_key = (
        cfg.get("api", {}).get("gemini_key")
        or os.environ.get("GEMINI_KEY", "")
    )
    if not gemini_key:
        raise ValueError("GEMINI_KEY 未配置")

    from google import genai

    client = genai.Client(api_key=gemini_key)

    topics = _load_topics()
    usage = _load_usage()
    topic_id, mood, angle, _keywords = _pick_topic(topics, usage)

    print(f"  [StoryGen] 选题: {topic_id} (mood={mood})")

    prompt = SCRIPT_PROMPT.format(
        angle=angle,
        mood=mood,
        title_hint=_title_hint(angle),
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={"system_instruction": SYSTEM_PROMPT},
    )
    raw = response.text.strip()
    print(f"  [StoryGen] Gemini 返回 {len(raw)} 字符")

    # 校验基本格式
    if "mood:" not in raw or "caption:" not in raw:
        raise ValueError(f"Gemini 输出格式不符合预期:\n{raw[:200]}")

    # 保存文件
    _STORIES_DIR.mkdir(exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = _STORIES_DIR / f"auto_{ts}_{topic_id}.txt"
    out_path.write_text(raw, encoding="utf-8")
    print(f"  [StoryGen] ✅ 故事文件: {out_path}")

    # 更新使用记录
    usage[topic_id] = usage.get(topic_id, 0) + 1
    _save_usage(usage)

    return str(out_path)
