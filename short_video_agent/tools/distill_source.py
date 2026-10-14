#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定心 素材提炼器 (short_video_agent/tools/distill_source.py)

把"灵感来源"文本（如王利杰抖音视频的口播/文案，你或豆包导出后放进来）
用 Gemini 提炼核心洞察、**融进定心既有的思维世界**改写成原创素材（绝不跑题），
输出成 待导入-*.csv 丢进收件箱，随后由 import_inbox.py 自动追加进素材库，形成闭环。

规则：
  - 只处理"没提炼过的"源文件（靠 源文件夹/.processed.json 记账去重）
  - 每次最多 4 个新主题，每主题 3 条 = 最多 12 条
  - 每条正文 50-200 字；tags 为白名单中的 1-2 个（与导入器完全一致）
  - 结合定心既有调性、绝不跑题（不许写成创业/商业/AI/投资/职场内容）
  - Gemini 输出先过同样的校验，不合格自动重试；3 次仍不行则跳过该源（不记为已处理）
  - chapter_id 优先读素材库当前最大章号 +1（读不到时退回 .processed.json 计数器）
  - --dry-run：只列出"这次会提炼哪些源"，不调 Gemini、不写文件、不记账

输入：源文件夹放 *.txt / *.md，一个文件 = 一个视频/一条灵感来源
用法：
  python3 distill_source.py            # 正式提炼
  python3 distill_source.py --dry-run  # 预览将提炼的源
环境变量：GEMINI_KEY（由 .env 提供，必需）；可选 WLJ_SOURCE_DIR / IMPORT_INBOX_DIR /
          WLJ_MAX_THEMES / WLJ_START_CHAPTER / GEMINI_MODEL / GSHEETS_SA 覆盖
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

# 读素材库最大章号用（与导入器同一张表/服务账号）
SA_KEY_PATH = Path(os.path.expanduser(
    os.environ.get("GSHEETS_SA", "~/.config/cncar/gsheets_sa.json")))
SPREADSHEET_ID = os.environ.get(
    "DINGXIN_SHEET_ID", "1rC0T5Jmo5Th2KYqiNCa7Z3c510dOVkt3NQNLc_76hVk")
WORKSHEET_NAME = os.environ.get("DINGXIN_WS", "素材库")

ALLOWED_TAGS = {"焦虑", "失眠", "比较", "放下", "当下", "付出", "孤独", "执着"}
TEXT_MIN, TEXT_MAX = 50, 200
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
# ──────────────────────────────────────────────────────────────────

PROMPT = """你是「定心」短视频的文案作者。定心面向在海外打拼的华人，用现代生活的困境切入，\
融合佛法视角，把焦虑、失眠、比较、孤独、执着这些情绪轻轻化解。语气温暖、口语，像睡前跟朋友说话。

【定心已有素材的调性——照这个来，不要跑题】
· 现象开场：你有没有被一句话冒犯，气了一整天？佛法说"无我"，不是说你不存在，是说那个一碰就痛的"我"，\
更像大脑每天在讲的一个故事……
· 转念落地：不是等到成功才安心，而是每一个当下的动作都认真去做。海外打工人最容易犯的毛病：\
总觉得现在做的事不够高级，焦虑于"我该去做更重要的事"，结果连当下都活不好……
· 今日练习：今天试着用一句不带头衔、身份、收入的话介绍自己，比如"我是一个每天认真生活的人"，\
说给自己听一遍，感受一下不靠标签的自己是什么感觉。

【这次任务】
下面是一条"灵感来源"原文。请**提炼其中的核心洞察，把它融进定心上面这种思维世界**，\
产出一个与定心一脉相承、但带来新角度的主题，正好 3 条：
- 第1条：从现代人的一个具体场景/情绪切入，让人共鸣
- 第2条：转念，用佛法/智慧的视角把情绪松开
- 第3条：以"今日练习："开头，给一个今晚就能做的小动作

【硬性要求——务必遵守】
- 绝不跑题：最终内容必须是定心（安心/放下/觉察/面向海外华人情绪）的调子，\
绝不能写成创业、商业、AI、投资、职场成功学。若来源偏离定心，就只取其中能跟\
"焦虑/执着/放下/当下/比较/孤独"呼应的那个情绪内核，用定心的话完全重讲。
- 完全原创：禁止照抄原文句子；禁止出现任何人名、平台名、"视频/抖音/博主/手册"等字样。
- 每条正文 50-200 个汉字（务必落在区间内）。
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


def next_chapter_from_sheet():
    """读素材库 A 列最大章号 +1；读不到返回 None（退回计数器）。"""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        if not SA_KEY_PATH.exists():
            return None
        creds = Credentials.from_service_account_file(
            str(SA_KEY_PATH), scopes=SCOPES)
        ws = gspread.authorize(creds).open_by_key(
            SPREADSHEET_ID).worksheet(WORKSHEET_NAME)
        nums = [int(v) for v in ws.col_values(1)[1:] if v.strip().isdigit()]
        return (max(nums) + 1) if nums else None
    except Exception as e:
        log(f"  读取素材库最大章号失败，改用计数器：{e}")
        return None


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
    next_ch = next_chapter_from_sheet() or int(
        ledger.get("next_chapter", START_CHAPTER))
    log(f"起始章号 = {next_ch}")
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
