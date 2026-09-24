"""CNcar 故事线脚本生成器

流程：
  1. 从 story_topics.py 按轮换选一个未用过的选题
  2. 调 Gemini 生成完整故事脚本（mood/title/caption + 旁白）
  3. 保存为 cncar/stories/auto_YYYYMMDD_HHMMSS.txt
  4. 返回文件路径供 run_story() 使用
"""

import json
import os
import re
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

# Gemini/代理偶发 TLS 断流时，不应该让当天的定时任务直接断更。
# 总等待约 135 秒；每一次会新建 client，避免复用已损坏的连接池。
_RETRY_DELAYS = [5, 10, 20, 40, 60]  # seconds between attempts (6 total tries)


def _is_network_error(exc: Exception) -> bool:
    name = type(exc).__qualname__.lower()
    msg  = str(exc).lower()
    return any(k in name or k in msg for k in (
        "remoteprotocol", "connecterror", "timeout",
        "disconnected", "network", "connection", "remotedisconnected",
    ))

_HERE = Path(__file__).parent
_STORIES_DIR = _HERE.parent / "stories"
_TOPICS_FILE = _HERE.parent / "config" / "story_topics.py"
_USAGE_FILE = _HERE.parent / "story_topic_usage.json"

SYSTEM_PROMPT = """You are a short-video scriptwriter for CNcar, a platform that helps
overseas buyers import cars from China to the Gulf region (UAE, Saudi Arabia, Oman, Qatar, Kuwait).

Your audience: people considering importing a car, or wanting to avoid scams and hidden costs.
Write in a direct, journalistic style — real stakes, real numbers, clear advice.

TARGET LENGTH: 85–100 words of narration (spoken in 40–50 seconds). Hard cap.
FIRST SENTENCE RULE: The opening line must be a hook — a specific number, a sharp conflict,
or a counterintuitive fact. No background. No scene-setting. No "A buyer once...".
Start mid-action so viewers are hooked before they can swipe away.
LANGUAGE LEVEL: Grade 5 English only. One idea per sentence. Use the simplest word that works.
No jargon, no complex words, no long clauses. If a 10-year-old can't read it, rewrite it.
"""

SCRIPT_PROMPT = """Write a short video script for CNcar based on this story angle:

ANGLE: {angle}

FIRST SENTENCE — non-negotiable rules:
• Must contain a specific number (dollar amount, days, %, quantity) AND a conflict or surprise.
• Start mid-action. Drop viewers into the moment. No warm-up. No scene-setting intro.
✅ "$12,000 sent. No car. No response. Here's what every buyer must verify first."
✅ "One missing document held his car at port for 60 days — and cost $4,800 extra."
❌ "A buyer sent $12,000 to a car dealer in Guangzhou." (scene-setting — BANNED)
❌ "Importing a car from China sounds simple." (soft opener — BANNED)

ENDING HOOK — non-negotiable rules:
• Do NOT give the final answer or recommendation. Leave a question open — make viewers want to know more.
• Frame CNcar as the tool to "see the real picture / know before you commit" — NOT "we recommend X".
✅ "See what your real numbers look like at CNcar.io."
✅ "Know the full cost and risk at CNcar.io — before you commit."
❌ "CNcar recommends container shipping." (gives the answer away AND sounds like a sales pitch — BANNED)
❌ "Protect your investment with CNcar." (emotional sales language — BANNED)

Output ONLY this exact format (no extra text, no markdown):

mood: {mood}
title: {title_hint}
caption: [ONE punchy hook sentence, max 12 words, present tense, must contain a number or conflict]
cover_hook: [2–4 ALL-CAPS punch words for the thumbnail, e.g. HIDDEN FEES, PORT TRAP, BYD BOOM. Never repeat the full title.]
cover_number: [the single strongest number from the story, e.g. $6,000 or 140%]
cover_impact: [1–2 ALL-CAPS words explaining that number, e.g. EXTRA COST, HIDDEN FEES, SURGE]
visuals: [EXACTLY 5 English visual beats separated by |. Each beat is 5–12 words and starts with wide shot / medium shot / close-up. Tell the same story in order: 1) vehicle/import setting, 2) problem or warning sign, 3) consequence at port/dealer, 4) cost or proof detail, 5) buyer verifying/checking solution. EVERY beat must visibly include at least one auto-trade element: a car/vehicle, car key, dealership, vehicle document, car carrier, or port with cars. Do not use generic phone, generic laptop, generic money, generic person, or abstract words alone.]

[blank line]
[Narration: 2–3 very short paragraphs. 85–100 words TOTAL — count every word, hard cap.
Short sentences, max 12 words each. Each sentence must add NEW information.
If two sentences say the same thing in different words, delete one.
No bullet points. No headers. No filler words. Facts and numbers only.
Grade 5 English only. One idea per sentence. Simplest word always wins.
Do NOT name specific dealers or individuals. Do NOT give a final recommendation.
End with one curiosity-hook CTA sentence pointing to CNcar.io.]
"""


def _load_topics():
    import importlib.util
    spec = importlib.util.spec_from_file_location("story_topics", str(_TOPICS_FILE))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.STORY_TOPICS


_COOLDOWN_DAYS = 14  # 同一选题至少间隔 N 天才能再次被选


def _load_usage() -> dict:
    """返回 {topic_id: "YYYY-MM-DD"}，兼容旧格式（count 整数）。"""
    if not _USAGE_FILE.exists():
        return {}
    raw = json.loads(_USAGE_FILE.read_text())
    # 旧格式是整数 count，统一转为遥远过去的占位日期（确保不影响冷却逻辑）
    migrated = {}
    for k, v in raw.items():
        if isinstance(v, int):
            migrated[k] = "2000-01-01"
        else:
            migrated[k] = v
    return migrated


def _save_usage(usage: dict):
    _USAGE_FILE.write_text(json.dumps(usage, indent=2, ensure_ascii=False))


def _pick_topic(topics: list, usage: dict, today: date | None = None) -> tuple:
    """14天冷却轮换：排除最近 COOLDOWN_DAYS 天内用过的选题，优先选最久未用的。
    若全部选题均在冷却期（极端情况），降级为选最久未用的（不阻断生成）。
    """
    if today is None:
        today = date.today()
    cutoff = today - timedelta(days=_COOLDOWN_DAYS)

    def last_used(topic_id: str) -> date:
        d = usage.get(topic_id)
        if not d:
            return date.min          # 从未用过，最优先
        try:
            return date.fromisoformat(d)
        except ValueError:
            return date.min

    available = [t for t in topics if last_used(t[0]) <= cutoff]
    pool = available if available else topics  # 全冷却时降级使用全部

    if not available:
        print("  [StoryGen] ⚠️  所有选题均在冷却期，降级选最久未用选题")

    pool.sort(key=lambda t: last_used(t[0]))   # 最久未用的排最前
    return pool[0]


def _title_hint(angle: str) -> str:
    """Returns a format constraint so Gemini generates a punchy, number-first title."""
    return (
        "[under 10 words, MUST contain a specific number AND a conflict or consequence. "
        "e.g. 'He Lost $4,000 Over One Missing Chip.' or '$12,000 Sent. No Car. Here's Why.' "
        "NEVER start with 'A buyer' or scene-setting. Lead with the cost or the shock.]"
    )


def generate_story(cfg: dict) -> str:
    """生成一个故事脚本文件，返回文件路径。"""
    gemini_key = (
        cfg.get("api", {}).get("gemini_key")
        or os.environ.get("GEMINI_KEY", "")
    )
    if not gemini_key:
        raise ValueError("GEMINI_KEY 未配置")

    from google import genai

    topics = _load_topics()
    usage = _load_usage()
    topic_id, mood, angle, _keywords = _pick_topic(topics, usage)

    print(f"  [StoryGen] 选题: {topic_id} (mood={mood})")

    prompt = SCRIPT_PROMPT.format(
        angle=angle,
        mood=mood,
        title_hint=_title_hint(angle),
    )

    last_exc: Exception | None = None
    for attempt in range(1, len(_RETRY_DELAYS) + 2):  # 6 attempts total
        try:
            # 每次都创建新的 HTTP client：代理偶发中断后，不复用旧连接。
            client = genai.Client(api_key=gemini_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={"system_instruction": SYSTEM_PROMPT},
            )
            break
        except Exception as exc:
            last_exc = exc
            if attempt <= len(_RETRY_DELAYS) and _is_network_error(exc):
                delay = _RETRY_DELAYS[attempt - 1]
                print(
                    f"  [StoryGen] ⚠️  网络错误(第{attempt}次)，"
                    f"{delay}s 后以新连接重试: {exc}"
                )
                time.sleep(delay)
            else:
                raise
    else:
        raise RuntimeError(f"Gemini 调用失败，已重试 {len(_RETRY_DELAYS)} 次: {last_exc}") from last_exc

    raw = response.text.strip()
    print(f"  [StoryGen] Gemini 返回 {len(raw)} 字符")

    # 校验基本格式
    if "mood:" not in raw or "caption:" not in raw or "visuals:" not in raw:
        raise ValueError(f"Gemini 输出格式不符合预期:\n{raw[:200]}")

    # 保存文件
    _STORIES_DIR.mkdir(exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = _STORIES_DIR / f"auto_{ts}_{topic_id}.txt"
    out_path.write_text(raw, encoding="utf-8")
    print(f"  [StoryGen] ✅ 故事文件: {out_path}")

    # 更新使用记录（记最后使用日期，用于 14 天冷却窗口）
    usage[topic_id] = date.today().isoformat()
    _save_usage(usage)

    return str(out_path)
