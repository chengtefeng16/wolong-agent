#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定心 素材收件箱导入工具  (short_video_agent/tools/import_inbox.py)

把收件箱里的 待导入-*.csv 校验后追加到 Google 表格「素材库」工作表末尾。

规则:
  - 只追加，绝不修改 / 删除已有行
  - segment_id 与表里已有的（或本次已处理的）重复 → 跳过该行
  - 行校验：恰好 5 列 / segment_text 长度 50-200 / tags 为白名单中的 1-2 个
  - 某个 CSV 处理成功后移入同目录 已导入/ 子文件夹；处理出错则原文件保留不动
  - --dry-run：只打印将要追加的行，不写表、不移动文件
  - 结束用 osascript 弹系统通知（best-effort，非 mac / 无 osascript 时静默跳过）

用法:
  python3 import_inbox.py            # 正式导入
  python3 import_inbox.py --dry-run  # 预演，不写表

可用环境变量覆盖（主要供测试）:
  IMPORT_INBOX_DIR   收件箱目录
  GSHEETS_SA         服务账号 JSON 路径
  DINGXIN_SHEET_ID   表格 ID
  DINGXIN_WS         工作表名
"""

import argparse
import csv
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ── 配置（可被环境变量覆盖）─────────────────────────────────────────
INBOX_DIR = Path(os.environ.get(
    "IMPORT_INBOX_DIR",
    os.path.expanduser("~/Documents/Obsidian Vault/AI/定心素材收件箱"),
))
DONE_SUBDIR = "已导入"
FILE_GLOB = "待导入-*.csv"

SA_KEY_PATH = Path(os.path.expanduser(
    os.environ.get("GSHEETS_SA", "~/.config/cncar/gsheets_sa.json")
))
SPREADSHEET_ID = os.environ.get(
    "DINGXIN_SHEET_ID", "1rC0T5Jmo5Th2KYqiNCa7Z3c510dOVkt3NQNLc_76hVk"
)
WORKSHEET_NAME = os.environ.get("DINGXIN_WS", "素材库")

ALLOWED_TAGS = {"焦虑", "失眠", "比较", "放下", "当下", "付出", "孤独", "执着"}
TEXT_MIN, TEXT_MAX = 50, 200
N_COLS = 5
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
# ──────────────────────────────────────────────────────────────────


def log(msg):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}", flush=True)


def notify(text):
    """best-effort macOS 通知；无 osascript 时静默跳过。"""
    try:
        subprocess.run(
            ["osascript", "-e",
             f'display notification "{text}" with title "定心素材收件箱"'],
            check=False,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10,
        )
    except Exception:
        pass


def parse_tags(raw):
    """拆分 tags（兼容中英文逗号），去空白后返回列表。"""
    return [p.strip() for p in raw.replace("，", ",").split(",") if p.strip()]


def validate_row(fields):
    """校验一行。返回 (ok, reason, normalized_5_fields_or_None)。"""
    if len(fields) != N_COLS:
        return False, f"列数={len(fields)}（应为5）", None
    chapter_id, chapter_name, segment_id, segment_text, tags_raw = \
        [f.strip() for f in fields]

    if not chapter_id:
        return False, "chapter_id 为空", None
    if not chapter_name:
        return False, "chapter_name 为空", None
    if not segment_id:
        return False, "segment_id 为空", None

    n = len(segment_text)
    if n < TEXT_MIN or n > TEXT_MAX:
        return False, f"segment_text 长度 {n}（应 {TEXT_MIN}-{TEXT_MAX}）", None

    tags = parse_tags(tags_raw)
    if not (1 <= len(tags) <= 2):
        return False, f"tags 数量 {len(tags)}（应 1-2 个）", None
    bad = [t for t in tags if t not in ALLOWED_TAGS]
    if bad:
        return False, f"tags 含非白名单词 {bad}", None

    # tags 统一用英文逗号回写，与表内既有格式一致
    return True, "", [chapter_id, chapter_name, segment_id,
                      segment_text, ",".join(tags)]


def read_csv_rows(path):
    """读取 CSV（UTF-8 带BOM），跳过表头与空行，返回数据行（list[list[str]]）。"""
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for i, row in enumerate(csv.reader(f)):
            first = row[0].strip().lstrip("﻿") if row else ""
            if i == 0 and first == "chapter_id":
                continue  # 表头
            if not any(c.strip() for c in row):
                continue  # 空行
            rows.append(row)
    return rows


def connect_worksheet():
    import gspread
    from google.oauth2.service_account import Credentials
    if not SA_KEY_PATH.exists():
        raise FileNotFoundError(f"服务账号密钥不存在: {SA_KEY_PATH}")
    creds = Credentials.from_service_account_file(str(SA_KEY_PATH), scopes=SCOPES)
    gc = gspread.authorize(creds)
    return gc.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)


def existing_segment_ids(ws):
    """读 C 列（segment_id），返回去表头、去空后的集合。"""
    return {v.strip() for v in ws.col_values(3)[1:] if v.strip()}


def move_to_done(path):
    done = path.parent / DONE_SUBDIR
    done.mkdir(exist_ok=True)
    dest = done / path.name
    if dest.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = done / f"{path.stem}.{stamp}{path.suffix}"
    shutil.move(str(path), str(dest))
    return dest


def main():
    ap = argparse.ArgumentParser(description="定心 素材收件箱导入")
    ap.add_argument("--dry-run", action="store_true",
                    help="只打印将追加的行，不写表、不移动文件")
    dry = ap.parse_args().dry_run
    tag = "[DRY-RUN] " if dry else ""

    # 1) 扫描收件箱 —— 没有文件就直接结束（不碰凭证/网络）
    if not INBOX_DIR.exists():
        log(f"{tag}收件箱目录不存在: {INBOX_DIR}")
        log(f"{tag}没有待导入文件")
        notify("没有待导入文件")
        return 0
    files = sorted(INBOX_DIR.glob(FILE_GLOB))
    if not files:
        log(f"{tag}没有待导入文件")
        notify("没有待导入文件")
        return 0
    log(f"{tag}发现 {len(files)} 个待导入文件: {[f.name for f in files]}")

    # 2) 连接表格并读取已有 segment_id
    try:
        ws = connect_worksheet()
        seen = existing_segment_ids(ws)
        log(f"{tag}表「{WORKSHEET_NAME}」现有 {len(seen)} 个 segment_id")
    except Exception as e:
        log(f"{tag}连接表格失败，终止（未改动任何文件）: {e}")
        notify(f"连接表格失败：{e}")
        return 1

    total_add = total_dup = total_bad = 0

    # 3) 逐文件处理
    for path in files:
        log(f"{tag}── {path.name} ──")
        try:
            rows = read_csv_rows(path)
        except Exception as e:
            log(f"{tag}  读取失败，保留原文件: {e}")
            continue

        to_append = []
        for ln, row in enumerate(rows, start=1):
            ok, reason, norm = validate_row(row)
            if not ok:
                total_bad += 1
                log(f"{tag}  跳过(第{ln}行·不合格): {reason}")
                continue
            sid = norm[2]
            if sid in seen:
                total_dup += 1
                log(f"{tag}  跳过(第{ln}行·重复): {sid}")
                continue
            seen.add(sid)
            to_append.append(norm)

        if dry:
            log(f"{tag}  将追加 {len(to_append)} 条:")
            for r in to_append:
                preview = r[3][:20].replace("\n", " ")
                log(f"{tag}    {r[2]} | {r[1]} | [{r[4]}] | {preview}…")
            total_add += len(to_append)
            continue

        # 正式写入
        if to_append:
            try:
                ws.append_rows(to_append, value_input_option="RAW",
                               insert_data_option="INSERT_ROWS",
                               table_range="A1")
                log(f"{tag}  已追加 {len(to_append)} 条")
            except Exception as e:
                for r in to_append:        # 写失败 → 撤回占用的 id
                    seen.discard(r[2])
                log(f"{tag}  写入失败，保留原文件: {e}")
                continue
        else:
            log(f"{tag}  无新行可追加（全部重复/不合格）")

        total_add += len(to_append)
        try:
            dest = move_to_done(path)
            log(f"{tag}  已移入 {dest.parent.name}/{dest.name}")
        except Exception as e:
            log(f"{tag}  移动文件失败（数据已写入表格）: {e}")

    # 4) 汇总 + 通知
    summary = (f"导入 {total_add} 条，跳过 {total_dup + total_bad} 条"
               f"（重复 {total_dup}，不合格 {total_bad}）")
    log(f"{tag}{summary}")
    notify((tag + summary).strip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
