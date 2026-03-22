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
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from qianqiu_os.services.pdf_export_utils_v1 import render_markdown_to_pdf

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASE_DIR = Path(__file__).resolve().parents[1]
TZ = ZoneInfo("Asia/Shanghai")

EXPORT_DIR = BASE_DIR / "runtime_exports" / "weekly"
INDEX_PATH = BASE_DIR / "runtime_exports" / "export_index_latest.json"

CONSTITUTION_PATH = PROJECT_ROOT / "PROJECT_CONSTITUTION.md"
MEMO_PATH = PROJECT_ROOT / "PROJECT_MEMO.md"
CHECKLIST_PATH = PROJECT_ROOT / "PROJECT_CHECKLIST.md"


def _now():
    return datetime.now(TZ)


def _read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _mtime(path: Path) -> str:
    if not path.exists():
        return "missing"
    return datetime.fromtimestamp(path.stat().st_mtime, TZ).strftime("%Y-%m-%d %H:%M:%S")


def _recent_agentos_files(days: int = 7) -> list[str]:
    cutoff = _now() - timedelta(days=days)
    targets = []
    for rel in ["qianqiu_os", "PROJECT_CONSTITUTION.md", "PROJECT_MEMO.md", "PROJECT_CHECKLIST.md"]:
        p = PROJECT_ROOT / rel
        if p.is_file():
            if datetime.fromtimestamp(p.stat().st_mtime, TZ) >= cutoff:
                targets.append(p)
        elif p.exists():
            for f in p.rglob("*"):
                if f.is_file() and datetime.fromtimestamp(f.stat().st_mtime, TZ) >= cutoff:
                    targets.append(f)
    targets.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return [str(x.relative_to(PROJECT_ROOT)) for x in targets[:30]]


def _update_index(md_path: Path, pdf_path: Path):
    data = _read_json(INDEX_PATH, {})
    if not isinstance(data, dict):
        data = {}
    data["latest_agentos_weekly_report"] = {
        "md_path": str(md_path),
        "pdf_path": str(pdf_path),
        "generated_at": _now().strftime("%Y-%m-%d %H:%M:%S")
    }
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def generate() -> dict:
    now = _now()
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    recent = _recent_agentos_files()

    content = f"""# AgentOS 当前主干总表（周更）

生成时间：{now.strftime("%Y-%m-%d %H:%M:%S")}
时区：Asia/Shanghai

## 一、本周新增 / 改进（按最近7天文件变动归集）
""" + "\n".join([f"- {x}" for x in recent]) + f"""

## 二、主干层当前重点
- 接入层
- 状态层
- 运行真源层
- 记忆层
- 推理 / 判断层
- 工具执行层
- 治理层
- 输出层
- 反思学习层
- 自愈层
- 预警层
- 时间层 / 交付层

## 三、本周固定文件状态
- PROJECT_CONSTITUTION.md 最新修改：{_mtime(CONSTITUTION_PATH)}
- PROJECT_MEMO.md 最新修改：{_mtime(MEMO_PATH)}
- PROJECT_CHECKLIST.md 最新修改：{_mtime(CHECKLIST_PATH)}

## 四、未完成项（人工继续补充）
- 把本周新增真正归并到主干稳定结构
- 回看半稳 / 偏弱模块是否已推进
- 校验固定交付节奏是否真正执行
- 校验海外多语言能力是否进入主干层设计

## 五、下周计划（人工继续补充）
- 按最新阶段补齐仍偏弱的层
- 校验真实渠道与 H5 联动
- 校验周五总表与夜间检查点的自动交付是否真正稳定
"""

    md_out = EXPORT_DIR / f"agentos_weekly_report_{now.strftime('%Y%m%d_%H%M%S')}.md"
    md_out.write_text(content, encoding="utf-8")

    latest_md = EXPORT_DIR / "agentos_weekly_report_latest.md"
    latest_md.write_text(content, encoding="utf-8")

    pdf_out = EXPORT_DIR / f"agentos_weekly_report_{now.strftime('%Y%m%d_%H%M%S')}.pdf"
    render_markdown_to_pdf(content, pdf_out, title="AgentOS 当前主干总表（周更）")

    latest_pdf = EXPORT_DIR / "agentos_weekly_report_latest.pdf"
    render_markdown_to_pdf(content, latest_pdf, title="AgentOS 当前主干总表（周更）")

    _update_index(md_out, pdf_out)

    return {
        "success": True,
        "task": "weekly_agentos_report",
        "export_path": str(md_out),
        "latest_path": str(latest_md),
        "pdf_path": str(pdf_out),
        "latest_pdf_path": str(latest_pdf),
        "generated_at": now.strftime("%Y-%m-%d %H:%M:%S")
    }


if __name__ == "__main__":
    print(json.dumps(generate(), ensure_ascii=False, indent=2))
