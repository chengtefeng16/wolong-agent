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

from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class RiskSignal:
    signal_id: str
    signal_type: str
    signal_level: str
    signal_source: str
    signal_summary: str
    signal_value: Any = None
    threshold_hint: Any = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class WarningSnapshot:
    snapshot_id: str
    task_id: str
    agent_id: str
    warning_status: str
    business_warning_count: int
    runtime_warning_count: int
    signals: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class TrendAnalysis:
    analysis_id: str
    task_id: str
    agent_id: str
    trend_status: str
    trend_summary: str
    trend_reason: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class InterventionSuggestion:
    suggestion_id: str
    task_id: str
    agent_id: str
    intervention_level: str
    suggestion_summary: str
    actions: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class EarlyWarningLog:
    log_id: str
    task_id: str
    agent_id: str
    risk_signals: List[Dict[str, Any]]
    warning_snapshot: Dict[str, Any]
    trend_analysis: Dict[str, Any]
    intervention_suggestion: Dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class EarlyWarningManager:
    """
    预警层第一刀：
    - risk_signal
    - warning_snapshot
    - trend_analysis
    - intervention_suggestion
    - early_warning_log

    当前定位：
    1. 先把“问题发生前的征兆”结构化。
    2. 先形成风险信号、趋势判断、干预建议的最小骨架。
    3. 后续再逐步接入更真实的时序数据、负载数据、失败率数据和资源监测。
    """

    def __init__(self) -> None:
        self.module_name = "early_warning_manager_v1"

    def build_risk_signal(
        self,
        signal_type: str,
        signal_level: str,
        signal_source: str,
        signal_summary: str,
        signal_value: Any = None,
        threshold_hint: Any = None,
    ) -> Dict[str, Any]:
        signal = RiskSignal(
            signal_id=f"risk_signal_{signal_type}_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            signal_type=signal_type,
            signal_level=signal_level,
            signal_source=signal_source,
            signal_summary=signal_summary,
            signal_value=signal_value,
            threshold_hint=threshold_hint,
        )
        return asdict(signal)

    def build_warning_snapshot(
        self,
        task_id: str,
        agent_id: str,
        warning_status: str,
        business_warning_count: int,
        runtime_warning_count: int,
        signals: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        snapshot = WarningSnapshot(
            snapshot_id=f"warning_snapshot_{task_id}",
            task_id=task_id,
            agent_id=agent_id,
            warning_status=warning_status,
            business_warning_count=business_warning_count,
            runtime_warning_count=runtime_warning_count,
            signals=signals or [],
        )
        return asdict(snapshot)

    def build_trend_analysis(
        self,
        task_id: str,
        agent_id: str,
        trend_status: str,
        trend_summary: str,
        trend_reason: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        analysis = TrendAnalysis(
            analysis_id=f"trend_analysis_{task_id}",
            task_id=task_id,
            agent_id=agent_id,
            trend_status=trend_status,
            trend_summary=trend_summary,
            trend_reason=trend_reason or [],
        )
        return asdict(analysis)

    def build_intervention_suggestion(
        self,
        task_id: str,
        agent_id: str,
        intervention_level: str,
        suggestion_summary: str,
        actions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        suggestion = InterventionSuggestion(
            suggestion_id=f"intervention_suggestion_{task_id}",
            task_id=task_id,
            agent_id=agent_id,
            intervention_level=intervention_level,
            suggestion_summary=suggestion_summary,
            actions=actions or [],
        )
        return asdict(suggestion)

    def build_early_warning_log(
        self,
        task_id: str,
        agent_id: str,
        risk_signals: List[Dict[str, Any]],
        warning_snapshot: Dict[str, Any],
        trend_analysis: Dict[str, Any],
        intervention_suggestion: Dict[str, Any],
    ) -> Dict[str, Any]:
        log = EarlyWarningLog(
            log_id=f"early_warning_log_{task_id}",
            task_id=task_id,
            agent_id=agent_id,
            risk_signals=risk_signals,
            warning_snapshot=warning_snapshot,
            trend_analysis=trend_analysis,
            intervention_suggestion=intervention_suggestion,
        )
        return asdict(log)

    def analyze_runtime_signals(
        self,
        task_id: str,
        agent_id: str,
        platform_governance: Optional[Dict[str, Any]] = None,
        execution_result: Optional[Dict[str, Any]] = None,
        healing_result: Optional[Dict[str, Any]] = None,
        metrics_context: Optional[Dict[str, Any]] = None,
        formatted_output: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        platform_governance = platform_governance or {}
        execution_result = execution_result or {}
        healing_result = healing_result or {}
        metrics_context = metrics_context or {}
        formatted_output = formatted_output or {}

        risk_signals: List[Dict[str, Any]] = []
        business_warning_count = 0
        runtime_warning_count = 0
        trend_reason: List[str] = []
        suggested_actions: List[str] = []

        if platform_governance.get("manual_review_required") is True:
            risk_signals.append(
                self.build_risk_signal(
                    signal_type="manual_review_required",
                    signal_level="high",
                    signal_source="platform_governance",
                    signal_summary="当前任务已触发人工复核要求，说明业务风险较高。",
                    signal_value=True,
                    threshold_hint="manual_review_required = False",
                )
            )
            business_warning_count += 1
            trend_reason.append("平台治理要求人工复核，业务风险当前偏高。")
            suggested_actions.append("提高人工复核优先级，避免直接自动放行。")

        failed_step_count = execution_result.get("failed_step_count", 0)
        if isinstance(failed_step_count, int) and failed_step_count > 0:
            risk_signals.append(
                self.build_risk_signal(
                    signal_type="failed_step_count",
                    signal_level="high",
                    signal_source="execution_layer",
                    signal_summary="执行层出现失败步骤，说明运行稳定性开始受影响。",
                    signal_value=failed_step_count,
                    threshold_hint=0,
                )
            )
            runtime_warning_count += 1
            trend_reason.append("执行层失败步骤增加，运行风险上升。")
            suggested_actions.append("优先分析失败步骤来源，并触发守护层进一步处置。")

        retry_result = healing_result.get("retry_result", {})
        retry_failed_count = retry_result.get("retry_failed_count", 0)
        if isinstance(retry_failed_count, int) and retry_failed_count > 0:
            risk_signals.append(
                self.build_risk_signal(
                    signal_type="retry_failed_count",
                    signal_level="medium",
                    signal_source="self_healing",
                    signal_summary="自愈重试仍有失败，说明问题可能不是偶发。",
                    signal_value=retry_failed_count,
                    threshold_hint=0,
                )
            )
            runtime_warning_count += 1
            trend_reason.append("自愈重试失败，说明异常存在持续化迹象。")
            suggested_actions.append("降低自动执行强度，必要时切人工接管。")

        waiting_human_review_tasks = metrics_context.get("waiting_human_review_tasks", 0)
        if isinstance(waiting_human_review_tasks, int) and waiting_human_review_tasks >= 10:
            risk_signals.append(
                self.build_risk_signal(
                    signal_type="waiting_human_review_tasks",
                    signal_level="medium",
                    signal_source="metrics",
                    signal_summary="等待人工复核任务较多，存在审核堆积风险。",
                    signal_value=waiting_human_review_tasks,
                    threshold_hint="< 10",
                )
            )
            business_warning_count += 1
            trend_reason.append("待人工复核任务堆积，业务流转可能变慢。")
            suggested_actions.append("考虑增加人工复核处理能力或调整任务优先级。")

        reply_status = formatted_output.get("reply_status")
        if reply_status == "waiting_human_review":
            risk_signals.append(
                self.build_risk_signal(
                    signal_type="reply_waiting_human_review",
                    signal_level="medium",
                    signal_source="output_adapter",
                    signal_summary="当前输出状态处于等待人工复核，未形成最终自动闭环。",
                    signal_value=reply_status,
                    threshold_hint="done",
                )
            )
            business_warning_count += 1
            trend_reason.append("业务结果尚未闭环到最终自动完成状态。")
            suggested_actions.append("确保人工结论能及时回流，避免闭环卡住。")

        if business_warning_count == 0 and runtime_warning_count == 0:
            warning_status = "stable"
            trend_status = "stable"
            trend_summary = "当前未发现明显风险趋势，系统处于相对稳定状态。"
            intervention_level = "low"
            suggestion_summary = "当前保持观察即可，无需额外干预。"
            suggested_actions = ["继续常规监控，并在关键节点记录状态。"]
        else:
            total_warning = business_warning_count + runtime_warning_count
            if total_warning >= 3:
                warning_status = "elevated"
                trend_status = "rising"
                trend_summary = "当前已出现多类风险信号，系统风险趋势正在抬升。"
                intervention_level = "high"
                suggestion_summary = "建议优先人工关注，并对关键链路进行干预。"
            else:
                warning_status = "attention_needed"
                trend_status = "watch"
                trend_summary = "当前已出现早期预警信号，需要持续观察并准备干预。"
                intervention_level = "medium"
                suggestion_summary = "建议提高关注级别，必要时提前调整执行策略。"

        warning_snapshot = self.build_warning_snapshot(
            task_id=task_id,
            agent_id=agent_id,
            warning_status=warning_status,
            business_warning_count=business_warning_count,
            runtime_warning_count=runtime_warning_count,
            signals=risk_signals,
        )

        trend_analysis = self.build_trend_analysis(
            task_id=task_id,
            agent_id=agent_id,
            trend_status=trend_status,
            trend_summary=trend_summary,
            trend_reason=trend_reason,
        )

        intervention_suggestion = self.build_intervention_suggestion(
            task_id=task_id,
            agent_id=agent_id,
            intervention_level=intervention_level,
            suggestion_summary=suggestion_summary,
            actions=suggested_actions,
        )

        return self.build_early_warning_log(
            task_id=task_id,
            agent_id=agent_id,
            risk_signals=risk_signals,
            warning_snapshot=warning_snapshot,
            trend_analysis=trend_analysis,
            intervention_suggestion=intervention_suggestion,
        )
