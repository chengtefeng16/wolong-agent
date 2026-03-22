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
class HumanDecision:
    decision_id: str
    task_id: str
    agent_id: str
    decision_owner: str
    decision_type: str
    decision_summary: str
    decision_reason: List[str] = field(default_factory=list)
    confirmation_required: bool = True
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class MachineExecution:
    execution_id: str
    task_id: str
    agent_id: str
    execution_status: str
    execution_summary: str
    execution_steps: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ResultFeedback:
    feedback_id: str
    task_id: str
    agent_id: str
    feedback_status: str
    feedback_summary: str
    business_result: Dict[str, Any] = field(default_factory=dict)
    execution_result: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ReflectionEntry:
    entry_id: str
    task_id: str
    agent_id: str
    reflection_status: str
    reflection_summary: str
    reflection_source: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class NextRoundAdjustment:
    adjustment_id: str
    task_id: str
    agent_id: str
    adjustment_status: str
    adjustment_summary: str
    next_actions: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class HumanMachineLoopLog:
    loop_id: str
    task_id: str
    agent_id: str
    human_decision: Dict[str, Any]
    machine_execution: Dict[str, Any]
    result_feedback: Dict[str, Any]
    reflection_entry: Dict[str, Any]
    next_round_adjustment: Dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class HumanMachineLoopManager:
    """
    人机协同闭环层第一刀：
    - human_decision
    - machine_execution
    - result_feedback
    - reflection_entry
    - next_round_adjustment
    - human_machine_loop_log

    当前定位：
    1. 把“人拍板 -> 系统执行 -> 结果反馈 -> 反思 -> 下一轮调整”串成最小闭环。
    2. 先把闭环记录结构立起来。
    3. 后续再继续增强真实干预策略、任务回灌、策略调整。
    """

    def __init__(self) -> None:
        self.module_name = "human_machine_loop_manager_v1"

    def build_human_decision(
        self,
        task_id: str,
        agent_id: str,
        decision_owner: str,
        decision_type: str,
        decision_summary: str,
        decision_reason: Optional[List[str]] = None,
        confirmation_required: bool = True,
    ) -> Dict[str, Any]:
        obj = HumanDecision(
            decision_id=f"human_decision_{task_id}",
            task_id=task_id,
            agent_id=agent_id,
            decision_owner=decision_owner,
            decision_type=decision_type,
            decision_summary=decision_summary,
            decision_reason=decision_reason or [],
            confirmation_required=confirmation_required,
        )
        return asdict(obj)

    def build_machine_execution(
        self,
        task_id: str,
        agent_id: str,
        execution_status: str,
        execution_summary: str,
        execution_steps: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        obj = MachineExecution(
            execution_id=f"machine_execution_{task_id}",
            task_id=task_id,
            agent_id=agent_id,
            execution_status=execution_status,
            execution_summary=execution_summary,
            execution_steps=execution_steps or [],
        )
        return asdict(obj)

    def build_result_feedback(
        self,
        task_id: str,
        agent_id: str,
        feedback_status: str,
        feedback_summary: str,
        business_result: Optional[Dict[str, Any]] = None,
        execution_result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        obj = ResultFeedback(
            feedback_id=f"result_feedback_{task_id}",
            task_id=task_id,
            agent_id=agent_id,
            feedback_status=feedback_status,
            feedback_summary=feedback_summary,
            business_result=business_result or {},
            execution_result=execution_result or {},
        )
        return asdict(obj)

    def build_reflection_entry(
        self,
        task_id: str,
        agent_id: str,
        reflection_status: str,
        reflection_summary: str,
        reflection_source: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        obj = ReflectionEntry(
            entry_id=f"reflection_entry_{task_id}",
            task_id=task_id,
            agent_id=agent_id,
            reflection_status=reflection_status,
            reflection_summary=reflection_summary,
            reflection_source=reflection_source or {},
        )
        return asdict(obj)

    def build_next_round_adjustment(
        self,
        task_id: str,
        agent_id: str,
        adjustment_status: str,
        adjustment_summary: str,
        next_actions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        obj = NextRoundAdjustment(
            adjustment_id=f"next_round_adjustment_{task_id}",
            task_id=task_id,
            agent_id=agent_id,
            adjustment_status=adjustment_status,
            adjustment_summary=adjustment_summary,
            next_actions=next_actions or [],
        )
        return asdict(obj)

    def build_loop_log(
        self,
        task_id: str,
        agent_id: str,
        human_decision: Dict[str, Any],
        machine_execution: Dict[str, Any],
        result_feedback: Dict[str, Any],
        reflection_entry: Dict[str, Any],
        next_round_adjustment: Dict[str, Any],
    ) -> Dict[str, Any]:
        obj = HumanMachineLoopLog(
            loop_id=f"human_machine_loop_{task_id}",
            task_id=task_id,
            agent_id=agent_id,
            human_decision=human_decision,
            machine_execution=machine_execution,
            result_feedback=result_feedback,
            reflection_entry=reflection_entry,
            next_round_adjustment=next_round_adjustment,
        )
        return asdict(obj)

    def build_loop_from_runtime(
        self,
        task_id: str,
        agent_id: str,
        platform_governance: Optional[Dict[str, Any]] = None,
        execution_task: Optional[Dict[str, Any]] = None,
        execution_result: Optional[Dict[str, Any]] = None,
        formatted_output: Optional[Dict[str, Any]] = None,
        reflection_log: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        platform_governance = platform_governance or {}
        execution_task = execution_task or {}
        execution_result = execution_result or {}
        formatted_output = formatted_output or {}
        reflection_log = reflection_log or {}

        manual_review_required = platform_governance.get("manual_review_required", False)
        governance_notes = platform_governance.get("governance_notes", [])

        if manual_review_required:
            decision_type = "human_review_gate"
            decision_summary = "当前任务需要保留人类最终确认权，进入人工复核闭环。"
            confirmation_required = True
        else:
            decision_type = "normal_execution_gate"
            decision_summary = "当前任务可按既定流程继续进入自动执行闭环。"
            confirmation_required = False

        human_decision = self.build_human_decision(
            task_id=task_id,
            agent_id=agent_id,
            decision_owner="human_operator",
            decision_type=decision_type,
            decision_summary=decision_summary,
            decision_reason=governance_notes,
            confirmation_required=confirmation_required,
        )

        machine_execution = self.build_machine_execution(
            task_id=task_id,
            agent_id=agent_id,
            execution_status=execution_result.get("execution_status", "unknown"),
            execution_summary="系统根据规划与治理结果完成当前任务执行链。",
            execution_steps=execution_task.get("execution_steps", []),
        )

        feedback_status = formatted_output.get("reply_status", execution_result.get("execution_status", "unknown"))
        result_feedback = self.build_result_feedback(
            task_id=task_id,
            agent_id=agent_id,
            feedback_status=feedback_status,
            feedback_summary="将业务结果、执行结果与对外输出状态汇总回流。",
            business_result={
                "reply_type": formatted_output.get("reply_type"),
                "needs_human_handoff": formatted_output.get("needs_human_handoff"),
            },
            execution_result=execution_result,
        )

        reflection_status = "ready" if reflection_log else "missing"
        reflection_entry = self.build_reflection_entry(
            task_id=task_id,
            agent_id=agent_id,
            reflection_status=reflection_status,
            reflection_summary="本次执行结果已进入反思层，供后续复盘与经验沉淀使用。",
            reflection_source=reflection_log,
        )

        next_actions: List[str] = []
        if manual_review_required:
            next_actions.append("等待人类复核并给出最终处理意见。")
            next_actions.append("复核结果回流后可继续沉淀为经验样本。")
        else:
            next_actions.append("继续按自动执行链路推进后续任务。")

        if execution_result.get("failed_step_count", 0) > 0:
            next_actions.append("将失败步骤交由守护层与反思层继续分析。")
        else:
            next_actions.append("将当前成功路径沉淀为可复用流程模板。")

        next_round_adjustment = self.build_next_round_adjustment(
            task_id=task_id,
            agent_id=agent_id,
            adjustment_status="planned",
            adjustment_summary="根据本轮结果，为下一轮任务、人类介入和经验沉淀预留调整动作。",
            next_actions=next_actions,
        )

        return self.build_loop_log(
            task_id=task_id,
            agent_id=agent_id,
            human_decision=human_decision,
            machine_execution=machine_execution,
            result_feedback=result_feedback,
            reflection_entry=reflection_entry,
            next_round_adjustment=next_round_adjustment,
        )
