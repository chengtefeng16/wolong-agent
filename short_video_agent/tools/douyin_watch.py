#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定心 · 抖音新视频监控 → 提炼 → 素材库  (short_video_agent/tools/douyin_watch.py)

全自动（GitHub Actions 每周跑一次，见 .github/workflows/douyin_watch.yml）：
  1) Playwright 无头浏览器带 cookie 打开王利杰抖音主页，拦截作品接口拿视频列表
     （yt-dlp 不支持抖音用户主页列表，只用它下载单条视频）
  2) 按 aweme_id 去重（状态记在 douyin_watch/state.json，由 workflow 提交回仓库）
  3) 取文本：① 字幕（yt-dlp --write-subs/--write-auto-subs，或接口自带字幕）
            ② 下载音视频 → faster-whisper 转写
            ③ 都没有 → 记为 no_text 跳过
  4) 复用 distill_source.py 的 Gemini 提示词 + 校验，提炼成「现代视角·xx」一章 3 条
  5) 复用 import_inbox.py 的行校验，直接追加进「素材库」（定心出片读的同一张表）

失败处理：
  - cookie 缺失 / 过期 / 列表接口拿不到 → 退出码 2，并输出明确的"请更新 DOUYIN_COOKIES Secret"
  - 单条视频失败 → 记 attempts，下次重试；连续 3 次失败标记 failed 不再重试
  - 本次尝试的视频全部失败 → 退出码 1
  - cookie 剩余 < 7 天 → 写 GITHUB_OUTPUT cookie_expiring=true（workflow 开 Issue 提醒）

用法：
  python3 tools/douyin_watch.py              # 正式运行
  python3 tools/douyin_watch.py --dry-run    # 取文本+提炼，但不写表、不改状态
  python3 tools/douyin_watch.py --list-only  # 只列出新视频

环境变量：
  DOUYIN_COOKIES_FILE  Netscape cookies.txt 路径（必需）
  GEMINI_KEY           Gemini key（必需，非 --list-only）
  GSHEETS_SA           服务账号 JSON 路径（写表用）
  WLJ_DOUYIN_URL       监控的主页（默认王利杰）
  WATCH_MAX_PER_RUN    每次最多处理几条新视频（默认 7）
  WATCH_MAX_AGE_DAYS   只处理多少天内发布的视频（默认 30，更早的记 too_old）
  WHISPER_MODEL        faster-whisper 模型（默认 small）
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# ── 配置 ─────────────────────────────────────────────────────────
USER_URL = os.environ.get(
    "WLJ_DOUYIN_URL",
    "https://www.douyin.com/user/"
    "MS4wLjABAAAAgVu-792u4Pc58RDSC4myZlddQ17n7Tiqi8LnJ9F2dsc")
STATE_PATH = Path(os.environ.get(
    "WATCH_STATE", str(HERE.parent / "douyin_watch" / "state.json")))
MAX_PER_RUN = int(os.environ.get("WATCH_MAX_PER_RUN", "7"))
MAX_AGE_DAYS = int(os.environ.get("WATCH_MAX_AGE_DAYS", "30"))
MAX_ATTEMPTS = 3
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "small")
MIN_TEXT_LEN = 30           # 转写/字幕少于这么多字视为无效
MAX_TEXT_LEN = 4500         # 提炼只用前 4000 字，够了就停止转写省时间
COOKIE_WARN_DAYS = 7
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
LOGIN_COOKIES = ("sessionid", "sessionid_ss", "sid_tt")
# ──────────────────────────────────────────────────────────────────


class CookieError(RuntimeError):
    """cookie 缺失/过期/失效，或列表接口整体拿不到（需人工处理）。"""


def log(m):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {m}", flush=True)


def gh_output(key, val):
    p = os.environ.get("GITHUB_OUTPUT")
    if p:
        with open(p, "a", encoding="utf-8") as f:
            f.write(f"{key}={val}\n")


def gh_summary(md):
    p = os.environ.get("GITHUB_STEP_SUMMARY")
    if p:
        with open(p, "a", encoding="utf-8") as f:
            f.write(md + "\n")


# ── cookie ───────────────────────────────────────────────────────
def parse_netscape(text):
    """解析 Netscape cookies.txt → list[dict]（只保留 douyin.com 相关）。"""
    out = []
    for line in text.splitlines():
        http_only = False
        if line.startswith("#HttpOnly_"):
            http_only = True
            line = line[len("#HttpOnly_"):]
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 7:
            continue
        domain, _sub, path, secure, expires, name, value = parts[:7]
        if "douyin.com" not in domain:
            continue
        try:
            exp = int(float(expires))
        except ValueError:
            exp = 0
        out.append({"domain": domain, "path": path or "/",
                    "secure": secure.upper() == "TRUE",
                    "expires": exp, "name": name, "value": value,
                    "httpOnly": http_only})
    return out


def check_cookies(cookies):
    """返回登录 cookie 剩余天数；缺失/已过期抛 CookieError。"""
    if not cookies:
        raise CookieError("cookies.txt 里没有任何 douyin.com 的 cookie")
    login = [c for c in cookies if c["name"] in LOGIN_COOKIES and c["value"]]
    if not login:
        raise CookieError(
            "cookie 里没有登录态（sessionid/sid_tt），导出时 Chrome 可能没登录抖音")
    now = time.time()
    exps = [c["expires"] for c in login if c["expires"] > 0]
    if not exps:
        return None      # 会话 cookie，无过期时间
    days = (min(exps) - now) / 86400
    if days <= 0:
        raise CookieError(
            f"抖音登录 cookie 已于 "
            f"{datetime.fromtimestamp(min(exps)):%Y-%m-%d} 过期")
    return days


def load_cookies():
    path = os.environ.get("DOUYIN_COOKIES_FILE", "")
    if not path or not Path(path).exists():
        raise CookieError("未提供 cookies.txt（DOUYIN_COOKIES Secret 为空？）")
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    cookies = parse_netscape(text)
    days = check_cookies(cookies)
    return path, cookies, days


# ── 列表：Playwright 拦截作品接口 ───────────────────────────────────
def list_videos(cookies):
    from playwright.sync_api import sync_playwright

    pw_cookies = []
    for c in cookies:
        d = {"name": c["name"], "value": c["value"],
             "domain": c["domain"], "path": c["path"],
             "secure": c["secure"], "httpOnly": c["httpOnly"],
             "sameSite": "Lax"}
        if c["expires"] > 0:
            d["expires"] = c["expires"]
        pw_cookies.append(d)

    payloads, statuses = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"])
        ctx = browser.new_context(user_agent=UA, locale="zh-CN",
                                  viewport={"width": 1366, "height": 900})
        ctx.add_cookies(pw_cookies)
        ctx.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        page = ctx.new_page()

        def on_resp(r):
            if "/aweme/v1/web/aweme/post/" in r.url:
                statuses.append(r.status)
                try:
                    payloads.append(r.json())
                except Exception:
                    payloads.append(None)

        page.on("response", on_resp)
        page.goto(USER_URL, wait_until="domcontentloaded", timeout=90000)
        for _ in range(20):                       # 最多等 20 秒
            if any(payloads):
                break
            page.wait_for_timeout(1000)
        title = page.title()
        still_logged_in = any(c["name"] in LOGIN_COOKIES
                              for c in ctx.cookies("https://www.douyin.com"))
        browser.close()

    items = []
    for d in payloads:
        if d and d.get("aweme_list"):
            items.extend(d["aweme_list"])
    if not items:
        raise CookieError(
            f"作品列表接口没有返回数据（拦截到 {len(statuses)} 次请求，"
            f"HTTP {statuses or '无'}；页面标题「{title}」；"
            f"登录态{'仍在' if still_logged_in else '已丢失'}）。"
            "最可能是 cookie 失效被要求重新登录，其次是抖音对海外 IP 风控/验证码")
    seen, out = set(), []
    for a in items:
        aid = str(a.get("aweme_id", ""))
        if not aid or aid in seen:
            continue
        seen.add(aid)
        out.append(a)
    out.sort(key=lambda a: a.get("create_time", 0), reverse=True)
    return out


# ── 取文本 ──────────────────────────────────────────────────────────
def subs_to_text(raw):
    """VTT/SRT/JSON 字幕 → 纯文本（去时间轴、序号、标签、相邻重复）。"""
    raw = raw.strip()
    if raw.startswith("{") or raw.startswith("["):
        try:
            d = json.loads(raw)
            texts = []

            def walk(x):
                if isinstance(x, dict):
                    for k in ("text", "Text", "content"):
                        if isinstance(x.get(k), str):
                            texts.append(x[k])
                    for v in x.values():
                        if isinstance(v, (dict, list)):
                            walk(v)
                elif isinstance(x, list):
                    for v in x:
                        walk(v)
            walk(d)
            raw = "\n".join(texts)
        except Exception:
            pass
    lines, prev = [], None
    for ln in raw.splitlines():
        s = ln.strip()
        if (not s or s == "WEBVTT" or s.isdigit() or "-->" in s
                or s.startswith(("NOTE", "Kind:", "Language:", "STYLE"))):
            continue
        s = re.sub(r"<[^>]+>", "", s).strip()
        if s and s != prev:
            lines.append(s)
            prev = s
    return "\n".join(lines)


def video_url(aid):
    return f"https://www.douyin.com/video/{aid}"


def run_ytdlp(args, cookie_path, workdir):
    cmd = [sys.executable, "-m", "yt_dlp", "--cookies", cookie_path,
           "--no-progress", "--no-playlist", "--retries", "3",
           "--user-agent", UA, "-P", str(workdir)] + args
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        log(f"    yt-dlp rc={r.returncode}: {r.stderr.strip()[-300:]}")
    return r.returncode == 0


def try_subtitles(aweme, cookie_path, workdir):
    # a) 接口自带字幕
    infos = (aweme.get("video") or {}).get("subtitle_infos") or []
    import requests
    for info in infos:
        url = info.get("Url") or info.get("url")
        if not url:
            continue
        try:
            r = requests.get(url, timeout=30,
                             headers={"User-Agent": UA,
                                      "Referer": "https://www.douyin.com/"})
            txt = subs_to_text(r.text)
            if len(txt) >= MIN_TEXT_LEN:
                return txt, "接口字幕"
        except Exception as e:
            log(f"    接口字幕下载失败：{e}")
    # b) yt-dlp 字幕
    run_ytdlp(["--skip-download", "--write-subs", "--write-auto-subs",
               "--sub-langs", "all", "-o", "sub.%(ext)s",
               video_url(aweme["aweme_id"])], cookie_path, workdir)
    for f in sorted(workdir.glob("sub*")):
        if f.suffix in (".vtt", ".srt", ".json", ".ass"):
            txt = subs_to_text(f.read_text(encoding="utf-8", errors="replace"))
            if len(txt) >= MIN_TEXT_LEN:
                return txt, "yt-dlp字幕"
    return None, None


def download_media(aweme, cookie_path, workdir):
    ok = run_ytdlp(["-f", "bestaudio/worst/best", "-o", "media.%(ext)s",
                    video_url(aweme["aweme_id"])], cookie_path, workdir)
    files = [f for f in workdir.glob("media.*") if f.stat().st_size > 10_000]
    if ok and files:
        return files[0]
    # 兜底：用列表接口里的播放地址直接下载
    import requests
    urls = ((aweme.get("video") or {}).get("play_addr") or {}).get("url_list") or []
    jar = {c["name"]: c["value"] for c in parse_netscape(
        Path(cookie_path).read_text(encoding="utf-8", errors="replace"))}
    for u in urls:
        try:
            r = requests.get(u, timeout=120, cookies=jar, stream=True,
                             headers={"User-Agent": UA,
                                      "Referer": "https://www.douyin.com/"})
            if r.status_code != 200:
                continue
            dst = workdir / "media_direct.mp4"
            with open(dst, "wb") as f:
                for chunk in r.iter_content(1 << 16):
                    f.write(chunk)
            if dst.stat().st_size > 10_000:
                log("    yt-dlp 失败，已用接口播放地址直接下载")
                return dst
        except Exception as e:
            log(f"    直接下载失败：{e}")
    return None


_whisper = None


def transcribe(media):
    global _whisper
    from faster_whisper import WhisperModel
    if _whisper is None:
        log(f"    加载 faster-whisper {WHISPER_MODEL}（CPU int8）…")
        _whisper = WhisperModel(WHISPER_MODEL, device="cpu",
                                compute_type="int8")
    segs, _info = _whisper.transcribe(
        str(media), language="zh", vad_filter=True, beam_size=5,
        initial_prompt="以下是普通话的句子，使用简体中文。")
    parts, n = [], 0
    for s in segs:
        t = s.text.strip()
        if t:
            parts.append(t)
            n += len(t)
        if n >= MAX_TEXT_LEN:
            break
    return "，".join(parts)


def get_text(aweme, cookie_path):
    with tempfile.TemporaryDirectory(prefix="dy_") as td:
        wd = Path(td)
        txt, src = try_subtitles(aweme, cookie_path, wd)
        if txt:
            return txt, src
        media = download_media(aweme, cookie_path, wd)
        if not media:
            raise RuntimeError("音视频下载失败（yt-dlp 与直链都失败）")
        txt = transcribe(media)
        if len(txt) >= MIN_TEXT_LEN:
            return txt, f"whisper-{WHISPER_MODEL}"
        return None, None


# ── 状态 ─────────────────────────────────────────────────────────
def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"videos": {}}


def save_state(st):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(st, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")


def mark(st, aid, aweme, status, **extra):
    v = st["videos"].setdefault(aid, {})
    v.update({"status": status,
              "desc": (aweme.get("desc") or "")[:60],
              "create_time": datetime.fromtimestamp(
                  aweme.get("create_time", 0), timezone.utc
              ).strftime("%Y-%m-%d"),
              "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")})
    v.update(extra)


# ── 主流程 ─────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="定心 抖音新视频监控")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--list-only", action="store_true")
    a = ap.parse_args()
    tag = "[DRY-RUN] " if a.dry_run else ""

    # 1) cookie + 列表
    try:
        cookie_path, cookies, days = load_cookies()
        if days is not None:
            log(f"登录 cookie 剩余约 {days:.1f} 天")
            gh_output("cookie_days_left", f"{days:.0f}")
            if days < COOKIE_WARN_DAYS:
                gh_output("cookie_expiring", "true")
                print(f"::warning::抖音 cookie 约 {days:.0f} 天后过期，"
                      "请尽快重新导出并更新 DOUYIN_COOKIES Secret")
        videos = list_videos(cookies)
    except CookieError as e:
        msg = (f"抖音监控无法继续：{e}。处理：Chrome 小号重新登录抖音后，"
               "在本机运行 python3 short_video_agent/tools/douyin_cookie_export.py "
               "更新 DOUYIN_COOKIES Secret，再手动重跑 workflow。")
        log(msg)
        print(f"::error::{msg}")
        gh_output("failure_kind", "cookie")
        gh_summary(f"## ❌ 抖音监控失败（cookie/列表）\n\n{msg}")
        return 2

    st = load_state()
    now = time.time()
    new, too_old = [], []
    for v in videos:
        aid = str(v["aweme_id"])
        rec = st["videos"].get(aid)
        if rec and (rec["status"] in ("done", "no_text", "too_old", "failed")):
            continue
        if now - v.get("create_time", now) > MAX_AGE_DAYS * 86400:
            too_old.append(v)
            continue
        new.append(v)
    log(f"主页拿到 {len(videos)} 条；新视频 {len(new)} 条；"
        f"超过 {MAX_AGE_DAYS} 天的旧视频 {len(too_old)} 条（不处理）")
    for v in new:
        log(f"  · {v['aweme_id']} {datetime.fromtimestamp(v.get('create_time', 0)):%m-%d} "
            f"{(v.get('desc') or '')[:30]}")
    if a.list_only:
        return 0
    if not a.dry_run:
        for v in too_old:
            mark(st, str(v["aweme_id"]), v, "too_old")
        save_state(st)

    picked = new[:MAX_PER_RUN]
    if not picked:
        log("没有新视频，结束")
        gh_summary("## ✅ 抖音监控：没有新视频")
        return 0

    # 2) 准备 Gemini + 表格
    import distill_source as ds
    import import_inbox as ii
    client = ds.make_client()
    ws = None
    seen_ids = set()
    next_ch = None
    if not a.dry_run:
        ws = ii.connect_worksheet()
        seen_ids = ii.existing_segment_ids(ws)
        nums = [int(x) for x in ws.col_values(1)[1:] if x.strip().isdigit()]
        next_ch = (max(nums) + 1) if nums else ds.START_CHAPTER
        log(f"素材库已有 {len(seen_ids)} 条，下一章号 {next_ch}")
    else:
        next_ch = 9000

    ok_n, fail_n, skip_n = 0, 0, 0
    report = []
    for v in picked:
        aid = str(v["aweme_id"])
        log(f"── {aid} {(v.get('desc') or '')[:30]}")
        attempts = st["videos"].get(aid, {}).get("attempts", 0) + 1
        try:
            text, src = get_text(v, cookie_path)
            if not text:
                log("    无字幕且转写为空 → 跳过")
                skip_n += 1
                report.append(f"| {aid} | ⏭ 无可用文本 | |")
                if not a.dry_run:
                    mark(st, aid, v, "no_text", attempts=attempts)
                    save_state(st)
                continue
            log(f"    文本来源 {src}，{len(text)} 字")
            raw = f"{v.get('desc') or ''}\n\n{text}".strip()

            obj = None
            for i in range(3):
                try:
                    cand = ds.rewrite_one(raw, client)
                    good, why = ds.validate_theme(cand)
                    if good:
                        obj = cand
                        break
                    log(f"    Gemini 第{i+1}次不合格：{why}")
                except Exception as e:
                    log(f"    Gemini 第{i+1}次失败：{e}")
                    time.sleep(5)
            if not obj:
                raise RuntimeError("Gemini 3 次输出都不合格")

            while any(f"seg_{next_ch}_{k:02d}" in seen_ids for k in (1, 2, 3)):
                next_ch += 1
            rows = []
            for k, s in enumerate(obj["segments"], 1):
                good, why, norm = ii.validate_row(
                    [str(next_ch), obj["_theme"], f"seg_{next_ch}_{k:02d}",
                     s["_text"], ",".join(s["_tags"])])
                if not good:
                    raise RuntimeError(f"行校验失败：{why}")
                rows.append(norm)

            if a.dry_run:
                for r in rows:
                    log(f"    {tag}{r[2]} | {r[1]} | [{r[4]}] | {r[3][:40]}…")
            else:
                for i in range(3):
                    try:
                        ws.append_rows(rows, value_input_option="RAW",
                                       insert_data_option="INSERT_ROWS",
                                       table_range="A1")
                        break
                    except Exception as e:
                        if i == 2:
                            raise RuntimeError(f"写入素材库失败：{e}")
                        log(f"    写表失败重试：{e}")
                        time.sleep(10)
                seen_ids.update(r[2] for r in rows)
                mark(st, aid, v, "done", attempts=attempts,
                     chapter=next_ch, theme=obj["_theme"], text_source=src)
                save_state(st)
            log(f"    ✅ 章{next_ch}《{obj['_theme']}》3 条")
            report.append(f"| {aid} | ✅ 章{next_ch} {obj['_theme']} | {src} |")
            next_ch += 1
            ok_n += 1
        except Exception as e:
            fail_n += 1
            final = attempts >= MAX_ATTEMPTS
            log(f"    ❌ 失败（第{attempts}次{'，不再重试' if final else '，下次重试'}）：{e}")
            report.append(f"| {aid} | ❌ {str(e)[:80]} | 第{attempts}次 |")
            if not a.dry_run:
                mark(st, aid, v, "failed" if final else "retry",
                     attempts=attempts, error=str(e)[:200])
                save_state(st)

    summary = f"新增 {ok_n} 章（{ok_n * 3} 条），跳过 {skip_n}，失败 {fail_n}"
    log(tag + summary)
    gh_summary(f"## 抖音监控 {tag}\n\n{summary}\n\n| 视频 | 结果 | 来源 |\n|---|---|---|\n"
               + "\n".join(report))
    if fail_n and not ok_n and not skip_n:
        gh_output("failure_kind", "videos")
        print(f"::error::本次 {fail_n} 条新视频全部处理失败，详见日志")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
