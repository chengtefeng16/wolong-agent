# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from qianqiu_os.services.pdf_export_utils_v1 import render_markdown_to_pdf

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASE_DIR = Path(__file__).resolve().parents[1]
TZ = ZoneInfo("Asia/Shanghai")

EXPORT_DIR = BASE_DIR / "runtime_exports" / "nightly"
INDEX_PATH = BASE_DIR / "runtime_exports" / "export_index_latest.json"

CONSTITUTION_PATH = PROJECT_ROOT / "PROJECT_CONSTITUTION.md"
MEMO_PATH = PROJECT_ROOT / "PROJECT_MEMO.md"
CHECKLIST_PATH = PROJECT_ROOT / "PROJECT_CHECKLIST.md"

WHATSAPP_VIEW = BASE_DIR / "runtime_views" / "h5_dashboard_whatsapp.json"
FACEBOOK_VIEW = BASE_DIR / "runtime_views" / "h5_dashboard_facebook.json"
FACEBOOK_FEED_VIEW = BASE_DIR / "runtime_views" / "h5_dashboard_facebook_feed.json"


def _now():
    return datetime.now(TZ)


def _read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _line_count(path: Path) -> int:
    text = _read_text(path)
    return len(text.splitlines()) if text else 0


def _mtime(path: Path) -> str:
    if not path.exists():
        return "missing"
    return datetime.fromtimestamp(path.stat().st_mtime, TZ).strftime("%Y-%m-%d %H:%M:%S")


def _latest_changed_files() -> list[str]:
    targets = []
    for rel in ["qianqiu_os", "wolong_h5_console/src"]:
        p = PROJECT_ROOT / rel
        if p.exists():
            for f in p.rglob("*"):
                if f.is_file():
                    targets.append(f)
    targets.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return [str(x.relative_to(PROJECT_ROOT)) for x in targets[:15]]


def _runtime_summary() -> dict:
    wa = _read_json(WHATSAPP_VIEW, {})
    fb = _read_json(FACEBOOK_VIEW, {})
    fb_feed = _read_json(FACEBOOK_FEED_VIEW, {})
    return {
        "whatsapp_customer_count": wa.get("customer_count", 0),
        "whatsapp_stats": wa.get("stats", {}),
        "facebook_customer_count": fb.get("customer_count", 0),
        "facebook_stats": fb.get("stats", {}),
        "facebook_feed_customer_count": fb_feed.get("customer_count", 0),
        "facebook_feed_stats": fb_feed.get("stats", {})
    }


def _update_index(md_path: Path, pdf_path: Path):
    data = _read_json(INDEX_PATH, {})
    if not isinstance(data, dict):
        data = {}
    data["latest_nightly_checkpoint"] = {
        "md_path": str(md_path),
        "pdf_path": str(pdf_path),
        "generated_at": _now().strftime("%Y-%m-%d %H:%M:%S")
    }
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def generate() -> dict:
    now = _now()
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    runtime = _runtime_summary()
    changed = _latest_changed_files()

    content = f"""# 夜间检查点

生成时间：{now.strftime("%Y-%m-%d %H:%M:%S")}
时区：Asia/Shanghai

## 一、对话宪法层
- 文件：PROJECT_CONSTITUTION.md
- 是否存在：{'是' if CONSTITUTION_PATH.exists() else '否'}
- 最新修改：{_mtime(CONSTITUTION_PATH)}
- 行数：{_line_count(CONSTITUTION_PATH)}

## 二、项目备忘层
- 文件：PROJECT_MEMO.md
- 是否存在：{'是' if MEMO_PATH.exists() else '否'}
- 最新修改：{_mtime(MEMO_PATH)}
- 行数：{_line_count(MEMO_PATH)}

## 三、check层 / 时间层
- 文件：PROJECT_CHECKLIST.md
- 是否存在：{'是' if CHECKLIST_PATH.exists() else '否'}
- 最新修改：{_mtime(CHECKLIST_PATH)}
- 行数：{_line_count(CHECKLIST_PATH)}

## 四、运行态摘要
- WhatsApp 客户数：{runtime['whatsapp_customer_count']}
- WhatsApp 统计：{json.dumps(runtime['whatsapp_stats'], ensure_ascii=False)}
- Facebook 私信客户数：{runtime['facebook_customer_count']}
- Facebook 私信统计：{json.dumps(runtime['facebook_stats'], ensure_ascii=False)}
- Facebook Feed 观察数：{runtime['facebook_feed_customer_count']}
- Facebook Feed 统计：{json.dumps(runtime['facebook_feed_stats'], ensure_ascii=False)}

## 五、最近变动文件（前15）
""" + "\n".join([f"- {x}" for x in changed]) + """

## 六、人工复核提示
- 检查今天是否已把关键协作规则固化到宪法 / 备忘 / check 层
- 检查今天是否有新的主干性结论未落盘
- 检查时间层任务是否按节奏执行
"""

    md_out = EXPORT_DIR / f"nightly_checkpoint_{now.strftime('%Y%m%d_%H%M%S')}.md"
    md_out.write_text(content, encoding="utf-8")

    latest_md = EXPORT_DIR / "nightly_checkpoint_latest.md"
    latest_md.write_text(content, encoding="utf-8")

    pdf_out = EXPORT_DIR / f"nightly_checkpoint_{now.strftime('%Y%m%d_%H%M%S')}.pdf"
    render_markdown_to_pdf(content, pdf_out, title="夜间检查点")

    latest_pdf = EXPORT_DIR / "nightly_checkpoint_latest.pdf"
    render_markdown_to_pdf(content, latest_pdf, title="夜间检查点")

    _update_index(md_out, pdf_out)

    return {
        "success": True,
        "task": "nightly_checkpoint",
        "export_path": str(md_out),
        "latest_path": str(latest_md),
        "pdf_path": str(pdf_out),
        "latest_pdf_path": str(latest_pdf),
        "generated_at": now.strftime("%Y-%m-%d %H:%M:%S")
    }


if __name__ == "__main__":
    print(json.dumps(generate(), ensure_ascii=False, indent=2))
