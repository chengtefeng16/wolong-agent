#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把本机 Chrome（已登录抖音的小号 profile）里的 douyin.com cookie
用 yt-dlp 的 --cookies-from-browser 同一套代码导出成 Netscape 格式，
只保留 douyin.com 域，base64 后直接通过 `gh secret set` 写进
GitHub Actions Secret「DOUYIN_COOKIES」。

全程只在内存里，不落盘、不打印 cookie 值。约 30 天过期后重跑一次即可。

用法（在本机终端跑，需已 `pip install yt-dlp` 且 `gh auth login`）：
  python3 short_video_agent/tools/douyin_cookie_export.py --list-profiles
  python3 short_video_agent/tools/douyin_cookie_export.py --profile "Profile 2"
  python3 short_video_agent/tools/douyin_cookie_export.py --profile "Profile 2" --check  # 只检查不上传
"""
import argparse
import base64
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

REPO = "chengtefeng16/wolong-agent"
SECRET = "DOUYIN_COOKIES"
LOGIN_COOKIES = ("sessionid", "sessionid_ss", "sid_tt")
CHROME_DIR = Path.home() / "Library/Application Support/Google/Chrome"


def list_profiles():
    import json
    try:
        info = json.loads((CHROME_DIR / "Local State").read_text())
        for k, v in info.get("profile", {}).get("info_cache", {}).items():
            print(f'  --profile "{k}"   ← {v.get("name", "")}')
    except Exception as e:
        print(f"读取 Chrome profile 列表失败：{e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default=None,
                    help='Chrome profile 目录名，如 "Default" / "Profile 2"（用小号那个）')
    ap.add_argument("--list-profiles", action="store_true")
    ap.add_argument("--check", action="store_true", help="只检查，不上传")
    a = ap.parse_args()
    if a.list_profiles:
        list_profiles()
        return 0

    from yt_dlp.cookies import extract_cookies_from_browser
    jar = extract_cookies_from_browser("chrome", a.profile)
    lines = ["# Netscape HTTP Cookie File"]
    login_exp = []
    n = 0
    for c in jar:
        if not c.domain.endswith("douyin.com"):
            continue
        http_only = c.has_nonstandard_attr("HttpOnly") or c.has_nonstandard_attr("httponly")
        dom = ("#HttpOnly_" if http_only else "") + c.domain
        lines.append("\t".join([
            dom, "TRUE" if c.domain.startswith(".") else "FALSE",
            c.path or "/", "TRUE" if c.secure else "FALSE",
            str(int(c.expires or 0)), c.name, c.value or ""]))
        n += 1
        if c.name in LOGIN_COOKIES and c.value:
            login_exp.append(int(c.expires or 0))
    if not n:
        print("❌ 这个 profile 里没有 douyin.com cookie，请先在该 Chrome profile 打开 douyin.com 登录小号")
        return 1
    if not login_exp:
        print("❌ 有 douyin.com cookie 但没有登录态（sessionid），请先在该 profile 登录抖音小号")
        return 1
    exp = min(e for e in login_exp if e > 0) if any(login_exp) else 0
    if exp:
        days = (exp - time.time()) / 86400
        print(f"✅ 导出 {n} 个 douyin.com cookie，登录态到期 "
              f"{datetime.fromtimestamp(exp):%Y-%m-%d}（约 {days:.0f} 天）")
        if days <= 0:
            print("❌ 登录态已过期，请先在 Chrome 里重新登录抖音")
            return 1
    else:
        print(f"✅ 导出 {n} 个 douyin.com cookie（登录态为会话 cookie，无到期日）")

    payload = base64.b64encode(("\n".join(lines) + "\n").encode()).decode()
    if len(payload) > 48 * 1024:
        print("❌ 超过 GitHub Secret 48KB 上限")
        return 1
    if a.check:
        print("（--check：未上传）")
        return 0
    r = subprocess.run(["gh", "secret", "set", SECRET, "--repo", REPO],
                       input=payload, text=True)
    if r.returncode == 0:
        print(f"✅ 已更新 {REPO} 的 Secret {SECRET}。可在 Actions 里手动 Run「Douyin Watch」验证。")
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
