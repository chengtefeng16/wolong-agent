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
class DecisionTrace:
    trace_id: str
    task_id: str
    agent_id: str
    decision_summary: str
    decision_basis: List[str] = field(default_factory=list)
    input_context: Dict[str, Any] = field(default_factory=dict)
    plan_context: Dict[str, Any] = field(default_factory=dict)
    risk_judgement: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ExecutionTrace:
    trace_id: str
    task_id: str
    agent_id: str
    execution_status: str
    execution_steps: List[Dict[str, Any]] = field(default_factory=list)
    execution_result: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ErrorReflection:
    reflection_id: str
    task_id: str
    agent_id: str
    error_type: str
    error_summary: str
    possible_causes: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)
    reflection_level: str = "light"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class SuccessReflection:
    reflection_id: str
    task_id: str
    agent_id: str
    success_summary: str
    success_factors: List[str] = field(default_factory=list)
    reusable_patterns: List[str] = field(default_factory=list)
    reinforcement_suggestions: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ReflectionLog:
    log_id: str
    task_id: str
    agent_id: str
    decision_trace: Dict[str, Any]
    execution_trace: Dict[str, Any]
    error_reflection: Optional[Dict[str, Any]] = None
    success_reflection: Optional[Dict[str, Any]] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class ReflectionManager:
    def __init__(self) -> None:
        self.module_name = "reflection_manager_v1"

    def build_decision_trace(
        self,
        task_id: str,
        agent_id: str,
        decision_summary: str,
        decision_basis: Optional[List[str]] = None,
        input_context: Optional[Dict[str, Any]] = None,
        plan_context: Optional[Dict[str, Any]] = None,
        risk_judgement: Optional[str] = None,
    ) -> Dict[str, Any]:
        trace = DecisionTrace(
            trace_id=f"decision_{task_id}",
            task_id=task_id,
            agent_id=agent_id,
            decision_summary=decision_summary,
            decision_basis=decision_basis or [],
            input_context=input_context or {},
            plan_context=plan_context or {},
            risk_judgement=risk_judgement,
        )
        return asdict(trace)

    def build_execution_trace(
        self,
        task_id: str,
        agent_id: str,
        execution_status: str,
        execution_steps: Optional[List[Dict[str, Any]]] = None,
        execution_result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        trace = ExecutionTrace(
            trace_id=f"execution_{task_id}",
            task_id=task_id,
            agent_id=agent_id,
            execution_status=execution_status,
            execution_steps=execution_steps or [],
            execution_result=execution_result or {},
        )
        return asdict(trace)

    def build_error_reflection(
        self,
        task_id: str,
        agent_id: str,
        error_type: str,
        error_summary: str,
        possible_causes: Optional[List[str]] = None,
        improvement_suggestions: Optional[List[str]] = None,
        reflection_level: str = "light",
    ) -> Dict[str, Any]:
        reflection = ErrorReflection(
            reflection_id=f"error_reflection_{task_id}",
            task_id=task_id,
            agent_id=agent_id,
            error_type=error_type,
            error_summary=error_summary,
            possible_causes=possible_causes or [],
            improvement_suggestions=improvement_suggestions or [],
            reflection_level=reflection_level,
        )
        return asdict(reflection)

    def build_success_reflection(
        self,
        task_id: str,
        agent_id: str,
        success_summary: str,
        success_factors: Optional[List[str]] = None,
        reusable_patterns: Optional[List[str]] = None,
        reinforcement_suggestions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        reflection = SuccessReflection(
            reflection_id=f"success_reflection_{task_id}",
            task_id=task_id,
            agent_id=agent_id,
            success_summary=success_summary,
            success_factors=success_factors or [],
            reusable_patterns=reusable_patterns or [],
            reinforcement_suggestions=reinforcement_suggestions or [],
        )
        return asdict(reflection)

    def build_reflection_log(
        self,
        task_id: str,
        agent_id: str,
        decision_trace: Dict[str, Any],
        execution_trace: Dict[str, Any],
        error_reflection: Optional[Dict[str, Any]] = None,
        success_reflection: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        log = ReflectionLog(
            log_id=f"reflection_log_{task_id}",
            task_id=task_id,
            agent_id=agent_id,
            decision_trace=decision_trace,
            execution_trace=execution_trace,
            error_reflection=error_reflection,
            success_reflection=success_reflection,
        )
        return asdict(log)

    def reflect_from_runtime(
        self,
        task_id: str,
        agent_id: str,
        input_context: Optional[Dict[str, Any]] = None,
        plan_context: Optional[Dict[str, Any]] = None,
        execution_task: Optional[Dict[str, Any]] = None,
        execution_result: Optional[Dict[str, Any]] = None,
        platform_governance: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        input_context = input_context or {}
        plan_context = plan_context or {}
        execution_task = execution_task or {}
        execution_result = execution_result or {}
        platform_governance = platform_governance or {}

        decision_basis = []
        planner_notes = plan_context.get("planner_notes", [])
        if planner_notes:
            decision_basis.extend(planner_notes)

        governance_notes = platform_governance.get("governance_notes", [])
        if governance_notes:
            decision_basis.extend(governance_notes)

        decision_trace = self.build_decision_trace(
            task_id=task_id,
            agent_id=agent_id,
            decision_summary="根据输入上下文、规划结果与治理结果生成本次任务执行决策。",
            decision_basis=decision_basis,
            input_context=input_context,
            plan_context=plan_context,
            risk_judgement=(
                "manual_review_required"
                if platform_governance.get("manual_review_required")
                else "normal"
            ),
        )

        execution_trace = self.build_execution_trace(
            task_id=task_id,
            agent_id=agent_id,
            execution_status=execution_result.get(
                "execution_status",
                execution_task.get("execution_status", "unknown"),
            ),
            execution_steps=execution_task.get("execution_steps", []),
            execution_result=execution_result,
        )

        failed_step_count = execution_result.get("failed_step_count", 0)
        execution_status = execution_result.get("execution_status", "unknown")

        error_reflection = None
        success_reflection = None

        if failed_step_count > 0 or execution_status in {"failed", "partial_failed"}:
            failed_steps = execution_result.get("failed_steps", [])
            possible_causes: List[str] = []
            improvement_suggestions: List[str] = []

            for step in failed_steps:
                executor = step.get("executor", "unknown")
                action = step.get("action", "unknown")
                error_code = step.get("error_code", "UNKNOWN_ERROR")
                possible_causes.append(
                    f"执行器 {executor} 在动作 {action} 上触发错误：{error_code}"
                )

                if executor == "browser":
                    improvement_suggestions.append(
                        "为 browser 执行链补充刷新、重试、重新定位页面元素能力。"
                    )
                elif executor == "desktop":
                    improvement_suggestions.append(
                        "为 desktop 执行链补充输入校验、按键重试与窗口状态检查能力。"
                    )
                elif executor == "api":
                    improvement_suggestions.append(
                        "为 api 执行链补充请求重发、接口回退与结果校验能力。"
                    )
                else:
                    improvement_suggestions.append(
                        "补充通用执行失败归因与二次重试策略。"
                    )

            error_reflection = self.build_error_reflection(
                task_id=task_id,
                agent_id=agent_id,
                error_type="execution_failure",
                error_summary="本次任务执行中出现失败步骤，需要进入错误反思与后续修正。",
                possible_causes=possible_causes,
                improvement_suggestions=improvement_suggestions,
                reflection_level="light",
            )
        else:
            success_reflection = self.build_success_reflection(
                task_id=task_id,
                agent_id=agent_id,
                success_summary="本次任务执行完成，可将成功路径沉淀为后续参考经验。",
                success_factors=[
                    "规划链路顺利进入执行阶段。",
                    "执行层当前骨架能够稳定跑通。",
                    "治理结果与执行结果保持一致。",
                ],
                reusable_patterns=[
                    "可复用当前多步计划到同类型任务。",
                    "可复用当前 execution + governance + output 的主链闭环。",
                ],
                reinforcement_suggestions=[
                    "把当前成功路径继续沉淀为标准任务模板。",
                    "后续可将成功特征写入经验记忆或知识图谱层。",
                ],
            )

        return self.build_reflection_log(
            task_id=task_id,
            agent_id=agent_id,
            decision_trace=decision_trace,
            execution_trace=execution_trace,
            error_reflection=error_reflection,
            success_reflection=success_reflection,
        )
