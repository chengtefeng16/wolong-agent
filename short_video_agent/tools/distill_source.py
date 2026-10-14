#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定心 素材提炼器 (short_video_agent/tools/distill_source.py)

把"灵感来源"文本（如王利杰抖音视频的口播/文案，你或豆包导出后放进来）
用 Gemini 改写成「定心」风格的原创素材，输出成 待导入-*.csv 丢进收件箱，
随后由 import_inbox.py 自动追加进素材库，形成闭环。

规则：
  - 只处理"没提炼过的"源文件（靠 源文件夹/.processed.json 记账去重）
  - 每次最多 4 个新主题，每主题 3 条 = 最多 12 条
  - 每条正文 50-200 字；tags 为白名单中的 1-2 个（与导入器完全一致）
  - Gemini 输出先过同样的校验，不合格自动重试；3 次仍不行则跳过该源（不记为已处理，下次再试）
  - chapter_id 从 .processed.json 的计数器续号（默认从 28 起，接在现有 27 之后，单调递增不复用）
  - 完全原创改写，禁止照抄原文、禁止出现作者名/平台名
  - --dry-run：只列出"这次会提炼哪些源"，不调 Gemini、不写文件、不记账

输入：源文件夹放 *.txt / *.md，一个文件 = 一个视频/一条灵感来源
用法：
  python3 distill_source.py            # 正式提炼
  python3 distill_source.py --dry-run  # 预览将提炼的源
环境变量：GEMINI_KEY（由 .env 提供，必需）；可选 WLJ_SOURCE_DIR / IMPORT_INBOX_DIR /
          WLJ_MAX_THEMES / WLJ_START_CHAPTER / GEMINI_MODEL 覆盖
"""
import argparse
import csv
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ── 配置（可被环境变量覆盖）─────────────────────────────────────────
SOURCE_DIR = Path(os.path.expanduser(os.environ.get(
    "WLJ_SOURCE_DIR", "~/Documents/Obsidian Vault/AI/王利杰原始素材")))
INBOX_DIR = Path(os.path.expanduser(os.environ.get(
    "IMPORT_INBOX_DIR", "~/Documents/Obsidian Vault/AI/定心素材收件箱")))
LEDGER = SOURCE_DIR / ".processed.json"
SRC_EXTS = (".txt", ".md")

MAX_THEMES = int(os.environ.get("WLJ_MAX_THEMES", "4"))
SEGS_PER_THEME = 3
START_CHAPTER = int(os.environ.get("WLJ_START_CHAPTER", "28"))

ALLOWED_TAGS = {"焦虑", "失眠", "比较", "放下", "当下", "付出", "孤独", "执着"}
TEXT_MIN, TEXT_MAX = 50, 200
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
# ──────────────────────────────────────────────────────────────────

PROMPT = """你是「定心」短视频的文案作者。定心面向在海外打拼的华人，用现代生活的困境切入，\
融合佛法视角，把焦虑、失眠、比较、孤独等情绪轻轻化解。语气温暖、口语化、适合睡前听。

下面是一条"灵感来源"的原始文字（可能是某条短视频的口播或文案）。\
请你**提炼其中的核心观点，用定心自己的话完全原创地重写**，产出一个主题、正好 3 条短文案：
- 第1条：从现代人的一个具体场景/情绪切入，让人共鸣
- 第2条：转念，给出佛法/智慧的视角，把情绪松开
- 第3条：以"今日练习："开头，给一个今晚就能做的小动作

硬性要求：
- 完全原创重写，禁止照抄原文句子；禁止出现任何作者名、平台名、"视频/抖音/博主"等字样。
- 每条正文 50-200 个汉字（务必落在这个区间内）。
- 每条配 1-2 个标签，只能从这个集合里选：焦虑, 失眠, 比较, 放下, 当下, 付出, 孤独, 执着。
- 主题名格式为「现代视角·<不超过12字的概括>」。

只输出严格 JSON，不要任何解释、不要代码块标记：
{"theme":"现代视角·xxx","segments":[{"text":"...","tags":["焦虑"]},{"text":"...","tags":["放下","当下"]},{"text":"...","tags":["当下"]}]}

灵感来源原文：
<<<
%s
>>>"""


def log(m):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {m}", flush=True)


def notify(text):
    try:
        subprocess.run(
            ["osascript", "-e",
             f'display notification "{text}" with title "定心素材提炼"'],
            check=False, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, timeout=10)
    except Exception:
        pass


def load_ledger():
    if LEDGER.exists():
        try:
            return json.loads(LEDGER.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"processed": [], "next_chapter": START_CHAPTER}


def save_ledger(d):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(d, ensure_ascii=False, indent=2),
                      encoding="utf-8")


def clean_tags(tags):
    out = []
    for t in tags or []:
        t = str(t).strip()
        if t in ALLOWED_TAGS and t not in out:
            out.append(t)
    return out[:2]


def validate_theme(obj):
    """校验并就地规整。返回 (ok, reason)。"""
    theme = str(obj.get("theme", "")).strip()
    if not theme:
        return False, "theme 为空"
    if not theme.startswith("现代视角"):
        theme = "现代视角·" + theme
    segs = obj.get("segments") or []
    if len(segs) != SEGS_PER_THEME:
        return False, f"segments 数={len(segs)}（应 {SEGS_PER_THEME}）"
    for i, s in enumerate(segs, 1):
        txt = str(s.get("text", "")).strip()
        n = len(txt)
        if n < TEXT_MIN or n > TEXT_MAX:
            return False, f"第{i}条长度 {n}（应 {TEXT_MIN}-{TEXT_MAX}）"
        tg = clean_tags(s.get("tags"))
        if not (1 <= len(tg) <= 2):
            return False, f"第{i}条标签数不对（应 1-2 个白名单词）"
        s["_text"] = txt
        s["_tags"] = tg
    obj["_theme"] = theme
    return True, ""


def make_client():
    from google import genai
    key = os.environ.get("GEMINI_KEY", "").strip()
    if not key:
        raise RuntimeError("未设置 GEMINI_KEY（请确认已 source .env）")
    return genai.Client(api_key=key)


def rewrite_one(raw_text, client):
    """调 Gemini，返回解析后的 dict（未校验）。"""
    resp = client.models.generate_content(
        model=GEMINI_MODEL, contents=PROMPT % raw_text[:4000])
    raw = (getattr(resp, "text", "") or "").strip()
    raw = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", raw).strip()
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        raise ValueError(f"无有效 JSON：{raw[:200]}")
    return json.loads(m.group(0))


def main():
    ap = argparse.ArgumentParser(description="定心 素材提炼器")
    ap.add_argument("--dry-run", action="store_true",
                    help="只列出将提炼的源，不调 Gemini、不写文件、不记账")
    dry = ap.parse_args().dry_run
    tag = "[DRY-RUN] " if dry else ""

    if not SOURCE_DIR.exists():
        log(f"{tag}源文件夹不存在：{SOURCE_DIR}")
        log(f"{tag}没有新的待提炼素材")
        notify("没有新的待提炼素材")
        return 0

    ledger = load_ledger()
    done = list(ledger.get("processed", []))
    done_set = set(done)
    srcs = sorted(
        [p for p in SOURCE_DIR.iterdir()
         if p.suffix.lower() in SRC_EXTS and p.name not in done_set],
        key=lambda p: p.stat().st_mtime)
    if not srcs:
        log(f"{tag}没有新的待提炼素材（已有的都提炼过了）")
        notify("没有新的待提炼素材")
        return 0

    picked = srcs[:MAX_THEMES]
    log(f"{tag}发现 {len(srcs)} 个未提炼源，本次取 {len(picked)} 个："
        f"{[p.name for p in picked]}")

    if dry:
        log(f"{tag}（dry-run：不调 Gemini、不写文件、不记账）")
        return 0

    client = make_client()
    next_ch = int(ledger.get("next_chapter", START_CHAPTER))
    rows = []
    processed_now = []
    themes = 0

    for p in picked:
        raw = p.read_text(encoding="utf-8", errors="replace").strip()
        if len(raw) < 10:
            log(f"  跳过（源内容太短）：{p.name}")
            continue
        obj = None
        for attempt in range(3):
            try:
                cand = rewrite_one(raw, client)
                ok, reason = validate_theme(cand)
                if ok:
                    obj = cand
                    break
                log(f"  {p.name} 第{attempt+1}次输出不合格：{reason}，重试")
            except Exception as e:
                log(f"  {p.name} 第{attempt+1}次调用失败：{e}")
        if not obj:
            log(f"  放弃（3次仍不合格，不记为已处理，下次再试）：{p.name}")
            continue
        ch = next_ch
        next_ch += 1
        themes += 1
        for i, s in enumerate(obj["segments"], 1):
            rows.append([str(ch), obj["_theme"], f"seg_{ch}_{i:02d}",
                         s["_text"], ",".join(s["_tags"])])
        processed_now.append(p.name)
        log(f"  ✅ {p.name} → 章{ch}《{obj['_theme']}》3 条")

    if not rows:
        log(f"{tag}没有成功改写的内容（源都未通过校验）")
        notify("提炼完成，但没有可用输出")
        return 0

    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    out = INBOX_DIR / f"待导入-王利杰-{datetime.now():%Y%m%d}.csv"
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["chapter_id", "chapter_name", "segment_id",
                    "segment_text", "tags"])
        w.writerows(rows)
    log(f"{tag}已写出 {len(rows)} 条 / {themes} 主题 → 收件箱 {out.name}")

    ledger["processed"] = done + processed_now
    ledger["next_chapter"] = next_ch
    save_ledger(ledger)
    log(f"{tag}记账更新：已处理 +{len(processed_now)}，下一章号 = {next_ch}")

    notify(f"改写 {themes} 主题 / {len(rows)} 条，已放入收件箱")
    return 0


if __name__ == "__main__":
    sys.exit(main())
