# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
# Project: AgentOS / Wolong Agent System
# ================================================================
"""
闭环管理器 V1 — 连通所有环节，形成自学习闭环

整体闭环架构：
┌────────────────────────────────────────────────────────────────┐
│                     千秋OS 自学习闭环                           │
│                                                                │
│  客户消息                                                       │
│     ↓                                                          │
│  [接入层] InputAdapter → 标准化输入                             │
│     ↓                                                          │
│  [分类层] LLM Gateway → classify_customer()                    │
│     ↓                  ↑ 注入历史经验                          │
│  [检索层] ExperienceStore.retrieve_similar()                   │
│     ↓                                                          │
│  [回复生成] LLM Gateway → generate_reply()                     │
│     ↓  (AI建议 → H5展示给人类)                                 │
│  [人类审核] H5面板 → 采纳/修改/忽略                            │
│     ↓                                                          │
│  [经验存储] ExperienceStore.save_experience()                  │
│     ↓                                                          │
│  [反思层] ReflectionManager → 分析本轮质量                     │
│     ↓                                                          │
│  [知识更新] 将反思结论写入经验库                                │
│     ↓                                                          │
│  [下次检索] → 更好的经验注入 → 更好的回复 → 闭环！             │
└────────────────────────────────────────────────────────────────┘

职责：
  1. process_incoming_message()  — 处理新消息，生成AI建议，存初始记录
  2. record_human_decision()     — 记录人类审核结果，完成经验存储
  3. run_reflection_cycle()      — 定期反思，提炼经验，更新知识
  4. get_loop_status()           — 返回当前闭环健康状态
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _safe_import(module_name: str):
    try:
        import importlib
        return importlib.import_module(module_name), None
    except ImportError as e:
        return None, str(e)


class ClosedLoopManager:
    """
    千秋OS 自学习闭环总控制器。
    连通：输入 → 分类 → 经验检索 → AI回复 → 人类审核 → 经验存储 → 反思 → 回流
    """

    def __init__(self):
        # 懒加载各子系统（允许部分不可用）
        self._llm = None
        self._exp = None
        self._reflection = None
        self._pending_decisions: Dict[str, Dict] = {}  # task_id → 待审核记录

    def _get_llm(self):
        if self._llm is None:
            mod, err = _safe_import("qianqiu_os.services.llm_gateway_v1")
            if mod:
                self._llm = mod
        return self._llm

    def _get_exp(self):
        if self._exp is None:
            mod, err = _safe_import("qianqiu_os.services.experience_store_v1")
            if mod:
                self._exp = mod
        return self._exp

    # ── 1. 处理新消息 ──

    def process_incoming_message(
        self,
        phone: str,
        customer_name: str,
        country: str,
        message_text: str,
        conversation_history: List[Dict] = None,
        existing_category: str = "",
    ) -> Dict[str, Any]:
        """
        核心入口：处理一条新进来的客户消息。

        流程：
          1. 用 LLM 分类客户（如有历史则参考历史）
          2. 从经验库检索相关成功案例
          3. 用 LLM 生成回复建议（注入经验）
          4. 生成一个 task_id 用于后续人类审核追踪

        返回：{task_id, category, suggested_reply, experience_count, llm_source}
        """
        task_id = str(uuid.uuid4())[:8]
        ts = time.strftime("%Y-%m-%d %H:%M:%S")

        llm = self._get_llm()
        exp = self._get_exp()

        # Step 1: 分类
        if existing_category and existing_category not in ("待判断", "unknown", ""):
            category = existing_category
            classify_source = "existing"
        elif llm:
            classify_result = llm.classify_customer(message_text, conversation_history)
            category = classify_result.get("bucket", "疑似车商")
            classify_source = classify_result.get("source", "rule")
        else:
            category = existing_category or "疑似车商"
            classify_source = "fallback"

        # Step 2: 检索相关经验
        experience_examples = []
        experience_count = 0
        if exp:
            experience_examples = exp.retrieve_similar(
                customer_msg=message_text,
                category=category,
                country=country,
                top_k=3,
                only_approved=True,
            )
            experience_count = len(experience_examples)

        # Step 3: 生成 AI 回复建议
        if llm:
            reply_result = llm.generate_reply(
                customer_name=customer_name,
                country=country,
                category=category,
                last_message=message_text,
                conversation_history=conversation_history,
                experience_examples=experience_examples,
            )
            suggested_reply = reply_result.get("suggested_reply", "")
            llm_source = reply_result.get("source", "unknown")
        else:
            suggested_reply = ""
            llm_source = "no_llm"

        # Step 4: 暂存待审核记录
        pending = {
            "task_id": task_id,
            "timestamp": ts,
            "phone": phone,
            "customer_name": customer_name,
            "country": country,
            "category": category,
            "customer_msg": message_text,
            "ai_suggested": suggested_reply,
            "experience_count": experience_count,
            "llm_source": llm_source,
            "classify_source": classify_source,
        }
        self._pending_decisions[task_id] = pending

        return {
            "task_id": task_id,
            "category": category,
            "suggested_reply": suggested_reply,
            "experience_count": experience_count,
            "llm_source": llm_source,
            "classify_source": classify_source,
        }

    # ── 2. 记录人类决策（关键闭环节点）──

    def record_human_decision(
        self,
        task_id: str,
        final_reply: str,
        human_approved: bool,
        outcome: str = "unknown",
        quality_score: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        记录人类对 AI 建议的审核决策，并将结果写入经验库。
        这是闭环的关键节点：人类的判断成为 AI 下次学习的素材。
        """
        pending = self._pending_decisions.get(task_id)
        if not pending:
            # 没有匹配的 pending，仍然存一条（可能是手动创建的）
            pending = {
                "task_id": task_id,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "customer_msg": "",
                "ai_suggested": "",
                "country": "",
                "category": "",
            }

        exp = self._get_exp()
        entry_id = None
        if exp:
            entry_id = exp.save_experience(
                customer_msg=pending.get("customer_msg", ""),
                ai_suggested=pending.get("ai_suggested", ""),
                final_reply=final_reply,
                human_approved=human_approved,
                category=pending.get("category", ""),
                country=pending.get("country", ""),
                outcome=outcome,
                quality_score=quality_score,
                extra={"task_id": task_id, "llm_source": pending.get("llm_source", "unknown")},
            )

        # 清理 pending
        self._pending_decisions.pop(task_id, None)

        return {
            "task_id": task_id,
            "entry_id": entry_id,
            "human_approved": human_approved,
            "stored": entry_id is not None,
            "message": "经验已存储，AI 下次回复将参考此决策" if entry_id else "经验存储失败",
        }

    # ── 3. 反思周期（可定期触发）──

    def run_reflection_cycle(self, recent_n: int = 20) -> Dict[str, Any]:
        """
        反思最近 N 条经验，提炼规律，更新系统认知。

        输出：
          - 采纳率趋势
          - 最常被修改的回复类型
          - 建议：哪类场景需要优化
          - 如果 LLM 可用：用 AI 分析规律并生成改进建议
        """
        exp = self._get_exp()
        if not exp:
            return {"status": "no_experience_store", "insights": []}

        recent = exp.get_recent_entries(limit=recent_n)
        summary = exp.get_summary()

        if not recent:
            return {"status": "no_data", "total_entries": 0, "insights": []}

        # 基础统计分析
        total = len(recent)
        approved = sum(1 for e in recent if e.get("human_approved", False))
        modified = sum(1 for e in recent if e.get("human_modified", False))
        approval_rate = round(approved / total, 2) if total > 0 else 0

        # 按分类统计
        by_cat: Dict[str, Dict] = {}
        for e in recent:
            cat = e.get("category", "unknown")
            if cat not in by_cat:
                by_cat[cat] = {"total": 0, "approved": 0}
            by_cat[cat]["total"] += 1
            if e.get("human_approved"):
                by_cat[cat]["approved"] += 1

        # 生成洞察
        insights = []
        if approval_rate < 0.5:
            insights.append(f"近期采纳率偏低（{approval_rate:.0%}），AI建议质量需要提升")
        elif approval_rate > 0.8:
            insights.append(f"近期采纳率良好（{approval_rate:.0%}），AI建议得到认可")

        for cat, stats in by_cat.items():
            cat_rate = stats["approved"] / stats["total"] if stats["total"] > 0 else 0
            if cat_rate < 0.4 and stats["total"] >= 3:
                insights.append(f"「{cat}」类客户的回复采纳率较低（{cat_rate:.0%}），建议重点优化此类场景")

        if modified > total * 0.6:
            insights.append("超过 60% 的回复被人类修改，说明 AI 建议与真实业务还有差距，需要更多经验积累")

        # 用 LLM 做深度反思（如可用）
        llm_insights = []
        llm = self._get_llm()
        if llm and recent and summary.get("total_entries", 0) >= 5:
            recent_samples = recent[:5]
            samples_text = "\n".join([
                f"- 客户说：「{e.get('customer_msg','')[:60]}」 → AI建议：「{e.get('ai_suggested','')[:60]}」 → 人类{'采纳' if e.get('human_approved') else '拒绝/修改'}"
                for e in recent_samples
            ])
            reflect_prompt = f"""以下是最近 {len(recent_samples)} 条客户回复记录：
{samples_text}

整体采纳率：{approval_rate:.0%}

请分析：
1. AI 回复有哪些模式或问题导致被人类修改？
2. 什么类型的回复最受认可？
3. 给出 2-3 条具体改进建议。

请简洁回答，每条不超过 50 字。"""

            from qianqiu_os.services.llm_gateway_v1 import WOLONG_SYSTEM_PROMPT, call_llm
            reflect_result = call_llm(reflect_prompt, system=WOLONG_SYSTEM_PROMPT, max_tokens=300, temperature=0.4)
            if reflect_result.get("text"):
                llm_insights = [reflect_result["text"].strip()]

        return {
            "status": "ok",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "recent_analyzed": total,
            "approval_rate": approval_rate,
            "modified_rate": round(modified / total, 2) if total > 0 else 0,
            "by_category": by_cat,
            "insights": insights,
            "llm_insights": llm_insights,
            "global_summary": {
                "total_entries": summary.get("total_entries", 0),
                "global_approval_rate": summary.get("approval_rate", 0),
                "top_keywords": summary.get("top_keywords", [])[:5],
            },
        }

    # ── 4. 闭环状态 ──

    def get_loop_status(self) -> Dict[str, Any]:
        """返回整个闭环的当前健康状态"""
        llm = self._get_llm()
        exp = self._get_exp()

        import os
        has_api_key = bool(os.getenv("GEMINI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))

        exp_summary = {}
        if exp:
            exp_summary = exp.get_summary()

        return {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "loop_components": {
                "llm_gateway": "online" if llm else "unavailable",
                "experience_store": "online" if exp else "unavailable",
                "api_key_configured": has_api_key,
                "llm_mode": "gemini_ai" if os.getenv("GEMINI_API_KEY") else ("claude_ai" if os.getenv("ANTHROPIC_API_KEY") else "rule_fallback"),
            },
            "experience_stats": {
                "total_entries": exp_summary.get("total_entries", 0),
                "approval_rate": exp_summary.get("approval_rate", 0),
                "top_keywords": exp_summary.get("top_keywords", [])[:3],
            },
            "pending_decisions": len(self._pending_decisions),
            "status": "healthy" if llm and exp else "degraded",
            "degraded_reason": None if (llm and exp) else "部分组件未就绪",
        }


# 单例（供 api_server 等模块共用）
_instance: Optional[ClosedLoopManager] = None


def get_closed_loop_manager() -> ClosedLoopManager:
    global _instance
    if _instance is None:
        _instance = ClosedLoopManager()
    return _instance
