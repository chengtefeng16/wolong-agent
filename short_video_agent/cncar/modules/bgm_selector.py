"""CNcar BGM 选择器

本地音乐库 + 情绪匹配 + 轮换。不从网络抓音乐。

目录结构：
  cncar/assets/bgm/
    tense/    *.mp3  (警示/骗局/损失)
    neutral/  *.mp3  (纪实/流程/政策)
    uplift/   *.mp3  (正向/解法/CNcar 推介)

使用记录：cncar/bgm_usage.json (运行时自动生成，已加入 .gitignore)

情绪判断优先级：
  1. 故事文件第一行 'mood: tense/neutral/uplift'
  2. 关键词兜底
  3. 默认 neutral
"""

import json
import os
import random
import re
import subprocess
from pathlib import Path

_HERE = Path(__file__).parent.parent          # cncar/
BGM_DIR    = _HERE / "assets" / "bgm"
USAGE_FILE = _HERE / "bgm_usage.json"

BGM_VOLUME = 0.10           # 人声的 10%（可在调用方覆盖）
MOODS      = ("tense", "neutral", "uplift")
_AUDIO_EXT = {".mp3", ".m4a", ".wav", ".flac"}

# ── 关键词（仅在无 mood: 标注时使用）─────────────────────────────────────── #

_TENSE_WORDS = {
    "scam", "fraud", "held", "seized", "lost", "fake", "detained",
    "deposit", "stolen", "risk", "danger", "warning", "beware",
    "blocked", "refused", "penalty", "fine", "reject", "stranded",
    "disappear", "disappeared", "missing", "confiscated", "dispute",
}
_UPLIFT_WORDS = {
    "cncar", "verified", "guarantee", "certainty", "safe", "solution",
    "trusted", "transparent", "protect", "secure", "success", "approved",
    "certified", "peace", "reliable", "accurate", "breakdown", "insight",
}


# ═══════════════════════════════════════════════════════════════════════════ #
#  BgmSelector                                                                #
# ═══════════════════════════════════════════════════════════════════════════ #

class BgmSelector:
    def __init__(self):
        self._usage = self._load_usage()

    # ── 情绪检测 ─────────────────────────────────────────────────────────── #

    @staticmethod
    def parse_mood_tag(story_path: str) -> "str | None":
        """读取故事文件第一行的 'mood: xxx' 标注；无则返回 None"""
        try:
            with open(story_path, encoding="utf-8") as f:
                first = f.readline().strip().lower()
            if first.startswith("mood:"):
                mood = first.split(":", 1)[1].strip()
                if mood in MOODS:
                    return mood
                print(f"  [BGM] ⚠️  未知情绪标注 '{mood}'，忽略（合法值: {MOODS}）")
        except Exception:
            pass
        return None

    @staticmethod
    def detect_mood(text: str) -> str:
        """关键词兜底情绪检测"""
        words = set(re.findall(r"\b\w+\b", text.lower()))
        ts = len(words & _TENSE_WORDS)
        us = len(words & _UPLIFT_WORDS)
        if ts > us and ts > 0:
            return "tense"
        if us > ts and us > 0:
            return "uplift"
        return "neutral"

    def get_mood(self, story_path: str, narration: str) -> str:
        """返回情绪字符串：优先文件 mood: 标注，其次关键词，最终 neutral"""
        mood = self.parse_mood_tag(story_path)
        if mood:
            print(f"  [BGM] 情绪: {mood}  (文件标注)")
            return mood
        mood = self.detect_mood(narration)
        print(f"  [BGM] 情绪: {mood}  (关键词兜底)")
        return mood

    # ── 文件选取 ─────────────────────────────────────────────────────────── #

    def select(self, mood: str) -> "str | None":
        """
        从 bgm/<mood>/ 目录选一首最近最少使用的文件。
        - mood 目录为空 → 降级到 neutral
        - neutral 也为空 → 返回 None（调用方跳过 BGM，不报错）
        """
        path = self._pick(mood)
        if path is None and mood != "neutral":
            print(f"  [BGM] {mood}/ 无文件，降级到 neutral/")
            path = self._pick("neutral")
        if path is None:
            print("  [BGM] 无可用 BGM，跳过背景音乐")
        return path

    def _pick(self, mood: str) -> "str | None":
        mood_dir = BGM_DIR / mood
        if not mood_dir.exists():
            return None
        files = sorted(
            f.name for f in mood_dir.iterdir() if f.suffix.lower() in _AUDIO_EXT
        )
        if not files:
            return None

        # 轮换窗口：同一情绪最多记住 min(总数-1, 3) 首
        recent  = self._usage.get(mood, [])
        window  = min(len(files) - 1, 3)
        exclude = set(recent[-window:]) if window > 0 else set()

        candidates = [f for f in files if f not in exclude]
        if not candidates:
            # 全部都在近期 → 重置并从全集选
            self._usage[mood] = []
            candidates = files

        chosen = random.choice(candidates)
        self._record(mood, chosen)
        print(f"  [BGM] 选中: bgm/{mood}/{chosen}")
        return str(mood_dir / chosen)

    # ── 使用记录 ─────────────────────────────────────────────────────────── #

    def _load_usage(self) -> dict:
        if USAGE_FILE.exists():
            try:
                with open(USAGE_FILE, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {m: [] for m in MOODS}

    def _record(self, mood: str, filename: str):
        lst = self._usage.setdefault(mood, [])
        lst.append(filename)
        self._usage[mood] = lst[-10:]       # 只保留最近 10 条
        try:
            with open(USAGE_FILE, "w", encoding="utf-8") as f:
                json.dump(self._usage, f, indent=2)
        except Exception as e:
            print(f"  [BGM] ⚠️  写 bgm_usage.json 失败: {e}")


# ═══════════════════════════════════════════════════════════════════════════ #
#  BGM 混音（ffmpeg，视频轨 -c:v copy 不重编，只重编音频）                      #
# ═══════════════════════════════════════════════════════════════════════════ #

def mix_bgm_into_video(
    video_path: str,
    bgm_path: str,
    vol: float = BGM_VOLUME,
) -> str:
    """
    把 bgm_path 混入 video_path。

    - BGM 用 -stream_loop -1 无限循环，amix duration=first 截断到视频时长
    - -c:v copy：视频轨不重编，速度快
    - 成功后覆盖原文件，返回 video_path
    - 失败时打印警告，返回原文件（不抛出）

    参数：
      vol  人声比例中 BGM 的响度，0.10 = 10%（人声100% + BGM 10%，未做归一化）
    """
    tmp = video_path + "._bgm_tmp.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-stream_loop", "-1",
        "-i", bgm_path,
        "-filter_complex",
        f"[1:a]volume={vol}[b];[0:a][b]amix=inputs=2:duration=first[out]",
        "-map", "0:v",
        "-map", "[out]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        tmp,
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if r.returncode != 0:
            raise RuntimeError(r.stderr[-600:])
        os.replace(tmp, video_path)
        print(f"  [BGM] ✅ 混音完成 (vol={vol})")
        return video_path
    except Exception as e:
        if os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except Exception:
                pass
        print(f"  [BGM] ⚠️  混音失败，跳过（视频仍正常）: {str(e)[:200]}")
        return video_path
