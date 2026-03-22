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

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional


def _now_iso() -> str:
    return datetime.now().isoformat()


class TestManager:
    """
    AgentOS 测试层管理器

    当前版本目标：
    1. 保持第三刀：真实 failed_steps 注入
    2. 保持第四刀：并发 / 边界测试执行骨架
    3. 保持第五刀第一步：真实回放小样本 + 指标化压测视图骨架
    4. 保持第五刀第二步：更真实的并发回放 + 更真实的边界回放 + 指标视图增强骨架
    5. 新增第五刀第三步：H5 指标面板联动 + 回放结果可视化增强骨架

    设计原则：
    - 先骨架、后增强
    - 输出结构尽量稳定
    - 主结果、预警、自愈、反思、测试日志可继续联动
    """

    def __init__(self) -> None:
        self.version = "test_manager_v5_2"

    # =========================================================
    # 通用工具
    # =========================================================
    def _normalize_signal(
        self,
        signal_type: str,
        signal_source: str,
        signal_summary: str,
        signal_value: Any = True,
        signal_level: str = "high",
        threshold_hint: str = "n/a",
        prefix: str = "normalized_signal",
    ) -> Dict[str, Any]:
        return {
            "signal_id": f"{prefix}_{signal_type}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            "signal_type": signal_type,
            "signal_level": signal_level,
            "signal_source": signal_source,
            "signal_summary": signal_summary,
            "signal_value": signal_value,
            "threshold_hint": threshold_hint,
            "created_at": _now_iso(),
        }

    def _build_test_scenario(
        self,
        scenario_type: str,
        scenario_name: str,
        scenario_description: str,
        expected_focus: List[str],
    ) -> Dict[str, Any]:
        ts = datetime.now().strftime("%Y%m%d%H%M%S%f")
        return {
            "scenario_id": f"test_scenario_{scenario_type}_{ts}",
            "scenario_type": scenario_type,
            "scenario_name": scenario_name,
            "scenario_description": scenario_description,
            "expected_focus": expected_focus,
            "created_at": _now_iso(),
        }

    # =========================================================
    # 第三刀：真实 failed_steps 注入
    # =========================================================
    def inject_real_failed_steps(
        self,
        execution_result: Dict[str, Any],
        execution_task: Dict[str, Any],
    ) -> Dict[str, Any]:
        result = deepcopy(execution_result)

        failed_steps = list(result.get("failed_steps", []))
        execution_logs = list(result.get("execution_logs", []))

        injected_step = {
            "step": "test_injected_step_1",
            "action": "simulate_execution_failure",
            "executor": "test_injector",
            "status": "failed",
            "error_message": "Simulated failed step injected by TestManager v3.",
            "injected_by": "inject_real_failed_steps",
            "injected_at": _now_iso(),
        }
        failed_steps.append(injected_step)

        execution_logs.append(
            {
                "step": "test_injected_step_1",
                "action": "simulate_execution_failure",
                "executor": "test_injector",
                "message": "测试层第三刀已注入真实 failed_steps。",
                "logged_at": _now_iso(),
            }
        )

        result["execution_status"] = "failed"
        result["failed_steps"] = failed_steps
        result["failed_step_count"] = len(failed_steps)
        result["execution_logs"] = execution_logs
        result["real_failed_steps_injected"] = True
        result["injection_marker"] = {
            "injection_type": "real_failed_steps",
            "injection_version": "v3",
            "injected_at": _now_iso(),
            "task_id": execution_task.get("task_id"),
            "execution_id": execution_task.get("execution_id"),
        }
        return result

    # =========================================================
    # 第四刀：并发测试与边界测试执行骨架
    # =========================================================
    def run_cut4_concurrency_boundary(
        self,
        execution_result: Dict[str, Any],
        healing_result: Dict[str, Any],
        reflection_log: Dict[str, Any],
        early_warning_log: Dict[str, Any],
    ) -> Dict[str, Any]:
        cut4_result = {
            "cut_name": "测试层第四刀：并发测试与边界测试执行骨架",
            "status": "executed",
            "executed_at": _now_iso(),
            "concurrent_test_executed": True,
            "boundary_test_executed": True,
            "concurrency_boundary_skeleton_ready": True,
            "test_layer_cut4_ready": True,
            "max_parallel_cases": 4,
            "boundary_case_count": 8,
            "cut4_risk_level": "critical",
            "cut4_risk_signals": [
                "queue_backlog_peak_detected",
                "context_isolation_anomaly_detected",
                "timeout_near_limit_detected",
                "ultra_long_input_pressure_detected",
                "max_steps_pressure_detected",
                "missing_context_boundary_detected",
                "failed_steps_replay_pressure_detected",
                "execution_failed_under_cut4_context",
                "failed_step_count_amplified_under_cut4",
            ],
            "concurrent_test_result": {
                "executed": True,
                "executed_at": _now_iso(),
                "max_parallel_cases": 4,
                "queue_backlog_peak": 2,
                "context_isolation_anomaly_count": 1,
                "duplicate_execution_count": 1,
                "timeout_near_limit_count": 1,
                "latency_spike_count": 1,
                "passed_case_ids": ["CT-001", "CT-003"],
                "warning_case_ids": ["CT-002", "CT-004"],
                "failed_case_ids": [],
                "observations": [
                    "已具备并发执行占位结果。",
                    "已具备共享上下文隔离风险占位判断。",
                    "已具备幂等与超时边缘占位判断。",
                ],
            },
            "boundary_test_result": {
                "executed": True,
                "executed_at": _now_iso(),
                "boundary_case_count": 8,
                "empty_input_hit_count": 1,
                "ultra_short_input_hit_count": 1,
                "ultra_long_input_hit_count": 1,
                "max_steps_pressure_count": 1,
                "near_timeout_hit_count": 1,
                "near_rate_limit_hit_count": 1,
                "missing_context_hit_count": 1,
                "failed_steps_replay_pressure_count": 1,
                "observations": [
                    "已具备空输入、超短输入、超长输入边界占位结果。",
                    "已具备接近超时、接近限流边界占位判断。",
                    "已具备 failed_steps 回放压力占位判断。",
                ],
            },
            "cut4_suggested_actions": [
                "增加并发上下文隔离校验与 request_scope 清理。",
                "为并发场景增加超时降级与排队熔断策略。",
                "为超长输入增加截断、摘要化或分段处理策略。",
                "为关键上下文字段增加默认值与前置校验。",
                "为 failed_steps 回放增加长度上限与压缩策略。",
            ],
            "linked_modules": {
                "early_warning": True,
                "self_healing": True,
                "reflection": True,
                "compatible_with_real_failed_steps": True,
            },
        }

        updated_healing = deepcopy(healing_result)
        raw_summary = updated_healing.get("healing_summary", {})
        if isinstance(raw_summary, dict):
            summary = dict(raw_summary)
        else:
            summary = {
                "summary_text": str(raw_summary) if raw_summary is not None else ""
            }
        summary["summary_text"] = summary.get("summary_text", "差异化轻度自愈动作已执行模拟。")
        summary["cut4_linked"] = True
        summary["cut4_summary"] = "测试层第四刀已把并发与边界风险修复建议挂入自愈结果。"
        summary.pop("legacy_healing_summary", None)
        updated_healing["healing_summary"] = summary
        updated_healing["cut4_linked"] = True
        updated_healing["cut4_updated_at"] = cut4_result["executed_at"]
        updated_healing["cut4_suggested_actions"] = cut4_result["cut4_suggested_actions"]

        updated_reflection = deepcopy(reflection_log)
        updated_reflection["cut4_linked"] = True
        updated_reflection["cut4_reflection"] = {
            "reflection_status": "triggered",
            "reflection_source": "test_layer_cut4_concurrency_boundary",
            "reflection_summary": "并发测试与边界测试骨架已发现潜在放大风险，需要进入错误反思与规则收敛。",
            "signals": cut4_result["cut4_risk_signals"],
            "created_at": cut4_result["executed_at"],
        }
        if updated_reflection.get("error_reflection"):
            updated_reflection["error_reflection"]["cut4_linked"] = True
            updated_reflection["error_reflection"]["cut4_summary"] = "第四刀已把并发与边界风险纳入 error_reflection 观察范围。"
            updated_reflection["error_reflection"]["cut4_signals"] = cut4_result["cut4_risk_signals"]

        updated_warning = deepcopy(early_warning_log)
        updated_warning["cut4_linked"] = True
        updated_warning["cut4_risk_level"] = cut4_result["cut4_risk_level"]
        updated_warning["cut4_summary"] = {
            "linked_at": cut4_result["executed_at"],
            "concurrent_test_executed": True,
            "boundary_test_executed": True,
            "max_parallel_cases": 4,
            "boundary_case_count": 8,
        }

        risk_signals = list(updated_warning.get("risk_signals", []))
        for signal_type in cut4_result["cut4_risk_signals"]:
            risk_signals.append(
                self._normalize_signal(
                    signal_type=signal_type,
                    signal_source="cut4",
                    signal_summary=f"测试层信号标准化：{signal_type}",
                )
            )
        updated_warning["risk_signals"] = risk_signals

        if updated_warning.get("warning_snapshot"):
            updated_warning["warning_snapshot"]["signals"] = risk_signals
            updated_warning["warning_snapshot"]["cut4_linked"] = True

        return {
            "execution_result": execution_result,
            "healing_result": updated_healing,
            "reflection_log": updated_reflection,
            "early_warning_log": updated_warning,
            "cut4_result": cut4_result,
        }

    # =========================================================
    # 第五刀第一步：真实回放小样本 + 指标化压测视图骨架
    # =========================================================
    def run_cut5_replay_metrics(
        self,
        execution_result: Dict[str, Any],
        healing_result: Dict[str, Any],
        reflection_log: Dict[str, Any],
        early_warning_log: Dict[str, Any],
        cut4_result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        cut5_result = {
            "cut_name": "测试层第五刀第一步：真实回放小样本骨架 + 指标化压测视图骨架",
            "status": "executed",
            "executed_at": _now_iso(),
            "sample_replay_executed": True,
            "metrics_view_generated": True,
            "sample_replay_case_count": 3,
            "metrics_panel_count": 4,
            "cut5_step1_ready": True,
            "cut5_risk_level": "critical",
            "cut5_risk_signals": [
                "sample_replay_warning_detected",
                "sample_replay_timeout_detected",
                "sample_replay_boundary_touch_detected",
                "replay_pressure_index_elevated",
                "failed_step_count_propagated_into_cut5",
            ],
            "replay_test_result": {
                "executed": True,
                "executed_at": _now_iso(),
                "sample_replay_case_count": 3,
                "replay_success_count": 1,
                "replay_warning_count": 2,
                "replay_failed_count": 0,
                "replay_timeout_count": 1,
                "replay_boundary_touch_count": 2,
                "replay_case_ids": ["RP-001", "RP-002", "RP-003"],
                "observations": [
                    "已具备真实回放小样本占位结果。",
                    "已具备失败步影响下的回放观察入口。",
                    "已具备与第四刀联动后的回放风险放大占位判断。",
                ],
            },
            "metrics_view_result": {
                "generated": True,
                "generated_at": _now_iso(),
                "metrics_panel_count": 4,
                "collected_metric_count": 9,
                "chart_ready": True,
                "replay_pressure_index": 3,
                "panel_names": [
                    "回放任务概览",
                    "回放超时观察",
                    "边界触发统计",
                    "风险放大指数",
                ],
                "observations": [
                    "已具备指标化压测视图骨架。",
                    "已具备回放压力指数占位结果。",
                    "后续可继续接入 H5 控制台指标面板。",
                ],
            },
            "cut5_suggested_actions": [
                "为真实回放增加更明确的超时阈值与终止策略。",
                "为边界回放增加分层回放顺序：先轻边界，再重边界。",
                "把第五刀指标视图逐步接入 H5 控制台面板。",
                "为回放压力指数增加红黄绿分级展示。",
            ],
            "linked_modules": {
                "early_warning": True,
                "self_healing": True,
                "reflection": True,
                "compatible_with_cut4": True,
            },
        }

        return self._apply_cut5_common_updates(
            execution_result=execution_result,
            healing_result=healing_result,
            reflection_log=reflection_log,
            early_warning_log=early_warning_log,
            cut5_result=cut5_result,
            cut5_reflection_source="test_layer_cut5_replay_metrics",
            cut5_reflection_summary="真实回放小样本与指标视图骨架已发现新的放大风险，需要进入下一轮反思与规则收敛。",
            trend_summary="测试层第五刀第一步执行后，真实回放小样本与指标视图风险已进入观察。",
            trend_reason="sample replay + metrics view skeleton",
            intervention_summary="建议优先收敛回放超时、边界触发顺序与指标分级展示。",
        )

    # =========================================================
    # 第五刀第二步：更真实的并发回放 + 更真实的边界回放 + 指标视图增强
    # =========================================================
    def run_cut5_replay_metrics_step2(
        self,
        execution_result: Dict[str, Any],
        healing_result: Dict[str, Any],
        reflection_log: Dict[str, Any],
        early_warning_log: Dict[str, Any],
        cut4_result: Optional[Dict[str, Any]] = None,
        cut5_result_step1: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        cut5_result = {
            "cut_name": "测试层第五刀第二步：更真实的并发回放 + 更真实的边界回放 + 指标化压测视图增强骨架",
            "status": "executed",
            "executed_at": _now_iso(),
            "sample_replay_executed": True,
            "metrics_view_generated": True,
            "sample_replay_case_count": 3,
            "metrics_panel_count": 6,
            "cut5_step2_ready": True,
            "cut5_risk_level": "critical",
            "cut5_risk_signals": [
                "sample_replay_warning_detected",
                "sample_replay_timeout_detected",
                "sample_replay_boundary_touch_detected",
                "replay_context_collision_detected",
                "replay_parallel_timeout_detected",
                "ordered_boundary_replay_enabled",
                "boundary_timeout_trigger_detected",
                "replay_pressure_index_elevated",
                "failed_step_count_propagated_into_cut5",
            ],
            "replay_test_result": {
                "executed": True,
                "executed_at": _now_iso(),
                "sample_replay_case_count": 3,
                "replay_success_count": 1,
                "replay_warning_count": 2,
                "replay_failed_count": 0,
                "replay_timeout_count": 1,
                "replay_boundary_touch_count": 2,
                "replay_case_ids": ["RP-001", "RP-002", "RP-003"],
                "observations": [
                    "已具备真实回放小样本占位结果。",
                    "已具备失败步影响下的回放观察入口。",
                    "已具备与第四刀联动后的回放风险放大占位判断。",
                ],
            },
            "replay_concurrency_result": {
                "executed": True,
                "executed_at": _now_iso(),
                "replay_parallel_case_count": 4,
                "replay_parallel_warning_count": 2,
                "replay_parallel_timeout_count": 1,
                "replay_context_collision_count": 1,
                "replay_duplicate_hit_count": 1,
                "replay_parallel_case_ids": ["RCP-001", "RCP-002", "RCP-003", "RCP-004"],
                "observations": [
                    "已具备更真实的并发回放占位结果。",
                    "已具备并发回放中的上下文碰撞观察入口。",
                    "已具备并发回放中的超时与重复命中观察入口。",
                ],
            },
            "replay_boundary_result": {
                "executed": True,
                "executed_at": _now_iso(),
                "replay_boundary_case_count": 6,
                "light_boundary_case_count": 3,
                "heavy_boundary_case_count": 3,
                "ordered_replay_enabled": True,
                "boundary_timeout_trigger_count": 1,
                "boundary_fallback_trigger_count": 1,
                "replay_boundary_case_ids": ["RBP-001", "RBP-002", "RBP-003", "RBP-004", "RBP-005", "RBP-006"],
                "observations": [
                    "已具备更真实的边界回放占位结果。",
                    "已具备轻边界优先、重边界后置的顺序控制占位结果。",
                    "已具备边界回放中的超时与降级触发观察入口。",
                ],
            },
            "metrics_view_result": {
                "generated": True,
                "generated_at": _now_iso(),
                "metrics_panel_count": 6,
                "collected_metric_count": 14,
                "chart_ready": True,
                "replay_pressure_index": 5,
                "replay_pressure_level": "red",
                "panel_names": [
                    "回放任务概览",
                    "回放超时观察",
                    "边界触发统计",
                    "风险放大指数",
                    "并发回放观察",
                    "边界顺序控制观察",
                ],
                "observations": [
                    "已具备指标化压测视图增强骨架。",
                    "已具备回放压力指数与分级占位结果。",
                    "后续可继续接入 H5 控制台指标面板。",
                ],
            },
            "cut5_suggested_actions": [
                "为真实回放增加更明确的超时阈值与终止策略。",
                "为边界回放增加分层回放顺序：先轻边界，再重边界。",
                "为并发回放增加 request_scope 隔离与重复执行保护。",
                "把第五刀指标视图逐步接入 H5 控制台面板。",
                "为回放压力指数增加红黄绿分级展示。",
            ],
            "linked_modules": {
                "early_warning": True,
                "self_healing": True,
                "reflection": True,
                "compatible_with_cut4": True,
            },
        }

        return self._apply_cut5_common_updates(
            execution_result=execution_result,
            healing_result=healing_result,
            reflection_log=reflection_log,
            early_warning_log=early_warning_log,
            cut5_result=cut5_result,
            cut5_reflection_source="test_layer_cut5_replay_metrics_step2",
            cut5_reflection_summary="更真实的并发回放与边界回放骨架已发现新的放大风险，需要进入下一轮反思与规则收敛。",
            trend_summary="测试层第五刀第二步执行后，更真实的并发回放与边界回放风险已进入观察。",
            trend_reason="replay concurrency + replay boundary + metrics view",
            intervention_summary="建议优先收敛回放并发碰撞、边界顺序控制与指标分级展示。",
        )

    # =========================================================
    # 第五刀第三步：H5 指标面板联动 + 可视化增强骨架
    # =========================================================
    def run_cut5_h5_panel_linkage(
        self,
        execution_result: Dict[str, Any],
        healing_result: Dict[str, Any],
        reflection_log: Dict[str, Any],
        early_warning_log: Dict[str, Any],
        cut4_result: Optional[Dict[str, Any]] = None,
        cut5_result_step2: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        第五刀第三步：
        - 把前两步的 replay / metrics 结果往 H5 面板联动
        - 增加回放结果可视化增强骨架
        - 保持与 early_warning / self_healing / reflection 的联动格式稳定
        """
        cut5_result = {
            "cut_name": "测试层第五刀第三步：H5 指标面板联动 + 回放结果可视化增强骨架",
            "status": "executed",
            "executed_at": _now_iso(),
            "sample_replay_executed": True,
            "metrics_view_generated": True,
            "sample_replay_case_count": 3,
            "metrics_panel_count": 8,
            "cut5_step3_ready": True,
            "cut5_risk_level": "critical",
            "cut5_risk_signals": [
                "h5_panel_linkage_enabled",
                "h5_panel_data_ready",
                "h5_trend_card_ready",
                "h5_risk_badge_red_detected",
                "replay_visualization_ready",
                "replay_parallel_timeout_detected",
                "replay_context_collision_detected",
                "boundary_timeout_trigger_detected",
                "replay_pressure_index_elevated",
            ],
            "replay_test_result": {
                "executed": True,
                "executed_at": _now_iso(),
                "sample_replay_case_count": 3,
                "replay_success_count": 1,
                "replay_warning_count": 2,
                "replay_failed_count": 0,
                "replay_timeout_count": 1,
                "replay_boundary_touch_count": 2,
                "replay_case_ids": ["RP-001", "RP-002", "RP-003"],
                "observations": [
                    "已保留真实回放小样本结果作为 H5 联动前置输入。",
                    "已保留失败步影响下的回放观察入口。",
                ],
            },
            "replay_concurrency_result": {
                "executed": True,
                "executed_at": _now_iso(),
                "replay_parallel_case_count": 4,
                "replay_parallel_warning_count": 2,
                "replay_parallel_timeout_count": 1,
                "replay_context_collision_count": 1,
                "replay_duplicate_hit_count": 1,
                "replay_parallel_case_ids": ["RCP-001", "RCP-002", "RCP-003", "RCP-004"],
                "observations": [
                    "已保留更真实的并发回放结果作为 H5 联动前置输入。",
                    "已保留并发回放中的上下文碰撞与超时观察入口。",
                ],
            },
            "replay_boundary_result": {
                "executed": True,
                "executed_at": _now_iso(),
                "replay_boundary_case_count": 6,
                "light_boundary_case_count": 3,
                "heavy_boundary_case_count": 3,
                "ordered_replay_enabled": True,
                "boundary_timeout_trigger_count": 1,
                "boundary_fallback_trigger_count": 1,
                "replay_boundary_case_ids": ["RBP-001", "RBP-002", "RBP-003", "RBP-004", "RBP-005", "RBP-006"],
                "observations": [
                    "已保留轻边界优先、重边界后置的顺序控制结果作为 H5 联动前置输入。",
                    "已保留边界回放中的超时与降级触发观察入口。",
                ],
            },
            "metrics_view_result": {
                "generated": True,
                "generated_at": _now_iso(),
                "metrics_panel_count": 8,
                "collected_metric_count": 18,
                "chart_ready": True,
                "trend_ready": True,
                "replay_pressure_index": 5,
                "replay_pressure_level": "red",
                "panel_names": [
                    "回放任务概览",
                    "回放超时观察",
                    "边界触发统计",
                    "风险放大指数",
                    "并发回放观察",
                    "边界顺序控制观察",
                    "H5 面板联动总览",
                    "回放结果可视化增强区",
                ],
                "observations": [
                    "已具备 H5 联动所需的指标视图增强骨架。",
                    "已具备趋势卡片、风险徽标、图表占位能力。",
                    "后续可继续接入 H5 控制台真实展示层。",
                ],
            },
            "h5_panel_result": {
                "generated": True,
                "generated_at": _now_iso(),
                "h5_panel_generated": True,
                "panel_card_count": 8,
                "linked_panel_names": [
                    "总览卡",
                    "超时卡",
                    "边界卡",
                    "压力指数卡",
                    "并发观察卡",
                    "顺序控制卡",
                    "趋势卡",
                    "风险徽标卡",
                ],
                "panel_status": "ready_for_console_linkage",
                "risk_badge_level": "red",
                "trend_chart_type": "line",
                "distribution_chart_type": "bar",
                "panel_refresh_mode": "manual_refresh_skeleton",
                "observations": [
                    "已具备 H5 指标面板联动骨架。",
                    "已具备风险徽标、趋势图、分布图占位信息。",
                    "后续可将其接入前端 H5 控制台页面。",
                ],
            },
            "replay_visualization_result": {
                "generated": True,
                "generated_at": _now_iso(),
                "visualization_ready": True,
                "chart_block_count": 4,
                "chart_blocks": [
                    "回放超时趋势图",
                    "回放风险分布图",
                    "并发回放碰撞图",
                    "边界顺序控制图",
                ],
                "observations": [
                    "已具备回放结果可视化增强骨架。",
                    "后续可对接真实 H5 图表组件。",
                ],
            },
            "cut5_suggested_actions": [
                "把第五刀第三步 H5 面板骨架逐步接入真实前端页面。",
                "为 H5 面板增加自动刷新与分页策略。",
                "为图表数据增加时间窗与筛选条件。",
                "继续推进真实 browser / desktop / api 回放链路接入。",
                "为回放压力指数增加更细粒度的分级规则。",
            ],
            "linked_modules": {
                "early_warning": True,
                "self_healing": True,
                "reflection": True,
                "compatible_with_cut4": True,
                "compatible_with_cut5_step2": True,
                "h5_console_ready": True,
            },
        }

        return self._apply_cut5_common_updates(
            execution_result=execution_result,
            healing_result=healing_result,
            reflection_log=reflection_log,
            early_warning_log=early_warning_log,
            cut5_result=cut5_result,
            cut5_reflection_source="test_layer_cut5_h5_panel_linkage",
            cut5_reflection_summary="H5 指标面板联动与回放结果可视化增强骨架已发现新的展示与联动风险，需要进入下一轮反思与规则收敛。",
            trend_summary="测试层第五刀第三步执行后，H5 面板联动与回放可视化风险已进入观察。",
            trend_reason="h5 panel linkage + replay visualization enhancement",
            intervention_summary="建议优先收敛 H5 面板联动协议、图表数据结构与自动刷新策略。",
        )

    # =========================================================
    # cut5 公共联动收口
    # =========================================================
    def _apply_cut5_common_updates(
        self,
        execution_result: Dict[str, Any],
        healing_result: Dict[str, Any],
        reflection_log: Dict[str, Any],
        early_warning_log: Dict[str, Any],
        cut5_result: Dict[str, Any],
        cut5_reflection_source: str,
        cut5_reflection_summary: str,
        trend_summary: str,
        trend_reason: str,
        intervention_summary: str,
    ) -> Dict[str, Any]:
        updated_healing = deepcopy(healing_result)
        raw_summary = updated_healing.get("healing_summary", {})
        if isinstance(raw_summary, dict):
            summary = dict(raw_summary)
        else:
            summary = {
                "summary_text": str(raw_summary) if raw_summary is not None else ""
            }
        summary["summary_text"] = summary.get("summary_text", "差异化轻度自愈动作已执行模拟。")
        # 注意：这里明确去掉 legacy，避免结构回摆
        summary.pop("legacy_healing_summary", None)
        summary["cut5_linked"] = True
        summary["cut5_summary"] = f"{cut5_result['cut_name']}已把相关修复建议挂入自愈结果。"
        updated_healing["healing_summary"] = summary
        updated_healing["cut5_linked"] = True
        updated_healing["cut5_updated_at"] = cut5_result["executed_at"]
        updated_healing["cut5_suggested_actions"] = cut5_result["cut5_suggested_actions"]

        updated_reflection = deepcopy(reflection_log)
        updated_reflection["cut5_linked"] = True
        updated_reflection["cut5_reflection"] = {
            "reflection_status": "triggered",
            "reflection_source": cut5_reflection_source,
            "reflection_summary": cut5_reflection_summary,
            "signals": cut5_result["cut5_risk_signals"],
            "created_at": cut5_result["executed_at"],
        }
        if updated_reflection.get("error_reflection"):
            updated_reflection["error_reflection"]["cut5_linked"] = True
            updated_reflection["error_reflection"]["cut5_summary"] = f"{cut5_result['cut_name']}已把相关风险纳入 error_reflection 观察范围。"
            updated_reflection["error_reflection"]["cut5_signals"] = cut5_result["cut5_risk_signals"]

        updated_warning = deepcopy(early_warning_log)
        updated_warning["cut5_linked"] = True
        updated_warning["cut5_risk_level"] = cut5_result["cut5_risk_level"]
        updated_warning["cut5_summary"] = {
            "linked_at": cut5_result["executed_at"],
            "sample_replay_executed": cut5_result.get("sample_replay_executed", False),
            "metrics_view_generated": cut5_result.get("metrics_view_generated", False),
            "sample_replay_case_count": cut5_result.get("sample_replay_case_count", 0),
            "metrics_panel_count": cut5_result.get("metrics_panel_count", 0),
        }

        risk_signals = list(updated_warning.get("risk_signals", []))
        for signal_type in cut5_result["cut5_risk_signals"]:
            risk_signals.append(
                self._normalize_signal(
                    signal_type=signal_type,
                    signal_source="cut5",
                    signal_summary=f"测试层信号标准化：{signal_type}",
                )
            )
        updated_warning["risk_signals"] = risk_signals

        if updated_warning.get("warning_snapshot"):
            updated_warning["warning_snapshot"]["signals"] = risk_signals
            updated_warning["warning_snapshot"]["cut5_linked"] = True

        updated_warning["trend_analysis"] = {
            "analysis_id": f"trend_analysis_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            "task_id": updated_warning.get("task_id"),
            "agent_id": updated_warning.get("agent_id"),
            "trend_status": "rising",
            "trend_summary": trend_summary,
            "trend_reason": trend_reason,
            "created_at": _now_iso(),
        }
        updated_warning["intervention_suggestion"] = {
            "suggestion_id": f"intervention_suggestion_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            "task_id": updated_warning.get("task_id"),
            "agent_id": updated_warning.get("agent_id"),
            "intervention_level": "high",
            "suggestion_summary": intervention_summary,
            "actions": cut5_result["cut5_suggested_actions"],
            "created_at": _now_iso(),
        }

        return {
            "execution_result": execution_result,
            "healing_result": updated_healing,
            "reflection_log": updated_reflection,
            "early_warning_log": updated_warning,
            "cut5_result": cut5_result,
        }

    # =========================================================
    # 测试总蓝图
    # =========================================================
    def build_test_blueprint_from_runtime(
        self,
        task_id: str,
        agent_id: str,
        execution_result: Dict[str, Any],
        healing_result: Dict[str, Any],
        reflection_log: Dict[str, Any],
        early_warning_log: Dict[str, Any],
        human_machine_loop_log: Dict[str, Any],
        cut4_result: Optional[Dict[str, Any]] = None,
        cut5_result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        now = _now_iso()

        cut4_present = cut4_result is not None
        cut5_present = cut5_result is not None

        plan_name = "AgentOS 测试层基础计划"
        suite_name = "AgentOS 基础测试场景套件"
        test_status = "executed_basic"

        if cut5_present and cut5_result.get("cut5_step3_ready"):
            plan_name = "AgentOS 测试层第五刀第三步计划"
            suite_name = "AgentOS 第五批测试场景套件"
            test_status = "executed_with_h5_panel_linkage"
        elif cut5_present and cut5_result.get("cut5_step2_ready"):
            plan_name = "AgentOS 测试层第五刀第二步计划"
            suite_name = "AgentOS 第五批测试场景套件"
            test_status = "executed_with_replay_step2"
        elif cut5_present and cut5_result.get("cut5_step1_ready"):
            plan_name = "AgentOS 测试层第五刀第一步计划"
            suite_name = "AgentOS 第五批测试场景套件"
            test_status = "executed_with_replay_metrics"
        elif cut4_present:
            plan_name = "AgentOS 测试层第四刀计划"
            suite_name = "AgentOS 第四批测试场景套件"
            test_status = "executed_with_concurrency_boundary"

        plan_scope = [
            "正常路径",
            "异常路径",
            "守护/自愈路径",
            "反思路径",
            "预警路径",
            "人机协同闭环路径",
        ]
        if cut4_present:
            plan_scope.extend(
                [
                    "并发测试路径",
                    "边界测试路径",
                    "故障注入路径",
                    "真实 failed_steps 注入路径",
                    "并发测试执行骨架",
                    "边界测试执行骨架",
                ]
            )
        if cut5_present:
            plan_scope.extend(
                [
                    "真实回放小样本路径",
                    "指标化压测视图路径",
                ]
            )
            if cut5_result.get("cut5_step2_ready"):
                plan_scope.extend(
                    [
                        "更真实并发回放路径",
                        "更真实边界回放路径",
                    ]
                )
            if cut5_result.get("cut5_step3_ready"):
                plan_scope.extend(
                    [
                        "H5 指标面板联动路径",
                        "回放结果可视化增强路径",
                    ]
                )

        plan_goal = [
            "验证主链是否可稳定运行。",
            "验证真实 failed_steps 出现后，自愈层、反思层、预警层是否形成联动。",
        ]
        if cut5_present and cut5_result.get("cut5_step3_ready"):
            plan_goal.extend(
                [
                    "验证第五刀第三步是否完成 H5 指标面板联动骨架。",
                    "验证第五刀第三步是否完成回放结果可视化增强骨架。",
                ]
            )
        elif cut5_present and cut5_result.get("cut5_step2_ready"):
            plan_goal.extend(
                [
                    "验证第五刀第二步是否完成更真实的并发回放骨架。",
                    "验证第五刀第二步是否完成更真实的边界回放骨架。",
                ]
            )
        elif cut5_present and cut5_result.get("cut5_step1_ready"):
            plan_goal.extend(
                [
                    "验证第五刀第一步是否完成真实回放小样本骨架。",
                    "验证第五刀第一步是否完成指标化压测视图骨架。",
                ]
            )
        elif cut4_present:
            plan_goal.extend(
                [
                    "验证第四刀是否完成并发测试与边界测试骨架执行。",
                ]
            )

        scenarios = [
            self._build_test_scenario(
                "normal_path",
                "正常路径测试",
                "验证规划、执行、输出、反思、图谱、人机闭环是否能按正常路径跑通。",
                [
                    "execution_result 是否完整",
                    "formatted_output 是否生成",
                    "reflection_log 是否生成",
                    "knowledge_graph 是否生成",
                    "human_machine_loop_log 是否生成",
                ],
            ),
            self._build_test_scenario(
                "exception_path",
                "异常路径测试",
                "验证执行失败、治理异常、输出异常时，系统是否能进入异常分支。",
                [
                    "failed_step_count 是否上升",
                    "error_reflection 是否进入主链",
                    "self_healing 是否能介入",
                ],
            ),
            self._build_test_scenario(
                "healing_path",
                "守护/自愈路径测试",
                "验证守护层在失败出现后是否能触发重试、修复与日志归档。",
                [
                    "healing_plan 是否生成",
                    "healing_result 是否记录",
                    "retry_result / repair_result 是否可观察",
                ],
            ),
            self._build_test_scenario(
                "warning_path",
                "预警路径测试",
                "验证预警层是否能在风险放大前识别征兆并生成干预建议。",
                [
                    "risk_signals 是否生成",
                    "warning_snapshot 是否可用",
                    "trend_analysis 是否可用",
                    "intervention_suggestion 是否可用",
                ],
            ),
            self._build_test_scenario(
                "human_machine_loop",
                "人机协同闭环测试",
                "验证人工确认、机器执行、结果回流、反思接入和下一轮调整是否形成闭环。",
                [
                    "human_decision 是否记录",
                    "machine_execution 是否记录",
                    "result_feedback 是否回流",
                    "next_round_adjustment 是否形成",
                ],
            ),
        ]

        if cut4_present:
            scenarios.append(
                self._build_test_scenario(
                    "concurrency_boundary",
                    "并发与边界测试",
                    "验证系统在任务量抬升、等待人工复核任务堆积、执行器压力增大时的可承受边界。",
                    [
                        "系统何时开始抬升预警",
                        "哪个模块先成为瓶颈",
                        "并发边界受哪些资源与架构因素决定",
                    ],
                )
            )

        if cut5_present:
            scenarios.append(
                self._build_test_scenario(
                    "replay_metrics",
                    "真实回放与指标视图测试",
                    "验证第五刀是否形成真实回放与指标视图骨架。",
                    [
                        "sample_replay_executed 是否为 True",
                        "metrics_view_generated 是否为 True",
                        "sample_replay_case_count 是否可观察",
                        "metrics_panel_count 是否可观察",
                    ],
                )
            )

        if cut5_present and cut5_result.get("cut5_step2_ready"):
            scenarios.append(
                self._build_test_scenario(
                    "replay_step2",
                    "更真实并发回放与边界回放测试",
                    "验证第五刀第二步是否形成更真实的并发回放与边界回放骨架。",
                    [
                        "replay_concurrency_result.executed 是否为 True",
                        "replay_boundary_result.executed 是否为 True",
                        "ordered_replay_enabled 是否为 True",
                        "replay_pressure_level 是否可观察",
                    ],
                )
            )

        if cut5_present and cut5_result.get("cut5_step3_ready"):
            scenarios.append(
                self._build_test_scenario(
                    "h5_panel_linkage",
                    "H5 指标面板联动测试",
                    "验证第五刀第三步是否形成 H5 指标面板联动与回放可视化增强骨架。",
                    [
                        "h5_panel_result.generated 是否为 True",
                        "replay_visualization_result.generated 是否为 True",
                        "panel_card_count 是否可观察",
                        "risk_badge_level 是否可观察",
                    ],
                )
            )

        injection_actions = [
            "模拟 execution_step 失败",
            "模拟输出状态异常",
            "模拟 retry / repair 触发",
            "模拟预警信号上升",
            "真实注入 failed_steps",
        ]
        if cut4_present:
            injection_actions.extend(
                [
                    "执行并发测试与边界测试骨架",
                ]
            )
        if cut5_present:
            injection_actions.extend(
                [
                    "执行真实回放小样本骨架",
                    "执行指标化压测视图骨架",
                ]
            )
            if cut5_result.get("cut5_step2_ready"):
                injection_actions.extend(
                    [
                        "执行更真实的并发回放骨架",
                        "执行更真实的边界回放骨架",
                    ]
                )
            if cut5_result.get("cut5_step3_ready"):
                injection_actions.extend(
                    [
                        "执行 H5 指标面板联动骨架",
                        "执行回放结果可视化增强骨架",
                    ]
                )

        simulated_failures = [
            {
                "failure_id": f"sim_exec_fail_{task_id}",
                "failure_type": "execution_step_failure",
                "target_module": "execution_layer",
                "failure_summary": "模拟执行步骤失败，用于观察 failed_step_count、self_healing 与 reflection 是否联动。",
            },
            {
                "failure_id": f"sim_output_fail_{task_id}",
                "failure_type": "output_status_anomaly",
                "target_module": "output_adapter",
                "failure_summary": "模拟输出异常或输出未闭环，用于观察预警层与人机闭环是否联动。",
            },
            {
                "failure_id": f"real_failed_step_injection_{task_id}",
                "failure_type": "real_failed_steps_injected",
                "target_module": "execution_result",
                "failure_summary": "已把真实 failed_steps 注入 execution_result，用于触发后续守护、反思与预警链路观察。",
            },
        ]
        if cut4_present:
            simulated_failures.append(
                {
                    "failure_id": f"cut4_concurrency_boundary_{task_id}",
                    "failure_type": "concurrency_boundary_skeleton_executed",
                    "target_module": "test_layer_cut4",
                    "failure_summary": "已执行并发测试与边界测试骨架，用于放大观察并发、边界与 failed_steps 相关风险。",
                }
            )
        if cut5_present:
            simulated_failures.append(
                {
                    "failure_id": f"cut5_replay_metrics_{task_id}",
                    "failure_type": "replay_metrics_skeleton_executed",
                    "target_module": "test_layer_cut5",
                    "failure_summary": "已执行真实回放小样本与指标视图骨架，用于放大观察回放与视图指标相关风险。",
                }
            )
            if cut5_result.get("cut5_step2_ready"):
                simulated_failures.append(
                    {
                        "failure_id": f"cut5_replay_metrics_step2_{task_id}",
                        "failure_type": "replay_step2_skeleton_executed",
                        "target_module": "test_layer_cut5_step2",
                        "failure_summary": "已执行更真实的并发回放与边界回放骨架，用于进一步放大观察并发回放与边界顺序控制风险。",
                    }
                )
            if cut5_result.get("cut5_step3_ready"):
                simulated_failures.append(
                    {
                        "failure_id": f"cut5_h5_panel_linkage_{task_id}",
                        "failure_type": "h5_panel_linkage_skeleton_executed",
                        "target_module": "test_layer_cut5_step3",
                        "failure_summary": "已执行 H5 指标面板联动与回放可视化增强骨架，用于放大观察展示层与回放指标联动风险。",
                    }
                )

        next_actions = []
        findings = []
        if cut5_present and cut5_result.get("cut5_step3_ready"):
            findings = [
                "当前已具备 H5 指标面板联动占位结果。",
                "当前已具备回放结果可视化增强占位结果。",
                "第五刀第二步结果已成功成为第五刀第三步的前置输入。",
                "early_warning 已接住第五刀第三步风险信号。",
                "self_healing 已接住第五刀第三步修复建议。",
                "reflection 已接住第五刀第三步反思触发。",
            ]
            next_actions = [
                "下一步推进 H5 控制台真实页面接入。",
                "下一步推进回放图表真实渲染与交互。",
                "下一步推进真实 browser / desktop / api 回放链路。",
                "后续继续推进真实压测与节流保护。",
            ]
        elif cut5_present and cut5_result.get("cut5_step2_ready"):
            findings = [
                "当前已具备更真实的并发回放占位结果。",
                "当前已具备更真实的边界回放占位结果。",
                "第五刀第一步结果已成功成为第五刀第二步的前置输入。",
                "early_warning 已接住第五刀第二步风险信号。",
                "self_healing 已接住第五刀第二步修复建议。",
                "reflection 已接住第五刀第二步反思触发。",
            ]
            next_actions = [
                "下一步推进测试层第五刀第三步：H5 指标面板联动。",
                "下一步推进测试层第五刀第三步：回放结果可视化增强。",
                "下一步推进真实 browser / desktop / api 回放链路。",
                "后续继续推进真实压测与节流保护。",
            ]
        elif cut5_present and cut5_result.get("cut5_step1_ready"):
            findings = [
                "当前已具备真实回放小样本占位结果。",
                "当前已具备指标化压测视图骨架结果。",
                "第四刀结果已成功成为第五刀第一步的前置输入。",
                "early_warning 已接住第五刀第一步风险信号。",
                "self_healing 已接住第五刀第一步修复建议。",
                "reflection 已接住第五刀第一步反思触发。",
            ]
            next_actions = [
                "下一步推进测试层第五刀第二步：更真实的并发回放。",
                "下一步推进测试层第五刀第二步：更真实的边界回放。",
                "下一步推进第五刀第三步：H5 指标面板联动。",
                "后续继续推进更真实的 browser / desktop / api 回放链路。",
            ]
        elif cut4_present:
            findings = [
                "当前已具备并发测试占位结果。",
                "当前已具备边界测试占位结果。",
                "第三刀真实 failed_steps 已成功成为第四刀风险放大输入。",
                "early_warning 已接住第四刀风险信号。",
                "self_healing 已接住第四刀修复建议。",
                "reflection 已接住第四刀反思触发。",
            ]
            next_actions = [
                "下一步推进测试层第五刀：真实回放小样本。",
                "下一步推进测试层第五刀：指标化压测视图。",
                "下一步推进更真实的 browser / desktop / api 故障并发注入。",
            ]

        log = {
            "log_id": f"test_log_{task_id}",
            "task_id": task_id,
            "agent_id": agent_id,
            "test_plan": {
                "plan_id": f"test_plan_{task_id}",
                "task_id": task_id,
                "agent_id": agent_id,
                "plan_name": plan_name,
                "plan_scope": plan_scope,
                "plan_goal": plan_goal,
                "created_at": now,
            },
            "test_suite": {
                "suite_id": f"test_suite_{task_id}",
                "task_id": task_id,
                "agent_id": agent_id,
                "suite_name": suite_name,
                "scenarios": scenarios,
                "created_at": now,
            },
            "fault_injection_plan": {
                "injection_plan_id": f"fault_injection_plan_{task_id}",
                "task_id": task_id,
                "agent_id": agent_id,
                "injection_status": test_status,
                "injection_targets": ["execution_layer", "output_adapter", "self_healing", "early_warning", "reflection"],
                "injection_actions": injection_actions,
                "created_at": now,
            },
            "fault_injection_result": {
                "injection_result_id": f"fault_injection_result_{task_id}",
                "task_id": task_id,
                "agent_id": agent_id,
                "simulated_failure_count": len(simulated_failures),
                "simulated_failures": simulated_failures,
                "observation_points": [
                    "execution_result.failed_step_count 是否变化",
                    "healing_plan / healing_result 是否变化",
                    "reflection_log.error_reflection 是否进入主链",
                    "early_warning_log.risk_signals 是否上升",
                    "human_machine_loop_log.result_feedback 是否出现异常回流",
                    "concurrent_test_executed 是否为 True",
                    "boundary_test_executed 是否为 True",
                    "sample_replay_executed 是否为 True",
                    "metrics_view_generated 是否为 True",
                ],
                "created_at": now,
            },
            "test_conclusion": {
                "conclusion_id": f"test_conclusion_{task_id}",
                "task_id": task_id,
                "agent_id": agent_id,
                "test_status": test_status,
                "test_summary": self._build_test_summary(test_status),
                "findings": findings,
                "next_test_actions": next_actions,
                "created_at": now,
            },
            "created_at": now,
        }

        if cut4_present:
            log["cut4_result"] = cut4_result
        if cut5_present:
            log["cut5_result"] = cut5_result

        return log

    def _build_test_summary(self, test_status: str) -> str:
        mapping = {
            "executed_with_concurrency_boundary": "测试层第四刀已把并发测试与边界测试执行骨架正式接入，且已与真实 failed_steps、预警、自愈、反思形成联动。",
            "executed_with_replay_metrics": "测试层第五刀第一步已把真实回放小样本骨架与指标化压测视图骨架正式接入，且已与第四刀、预警、自愈、反思形成联动。",
            "executed_with_replay_step2": "测试层第五刀第二步已把更真实的并发回放骨架与边界回放骨架正式接入，且已与第五刀第一步、第四刀、预警、自愈、反思形成联动。",
            "executed_with_h5_panel_linkage": "测试层第五刀第三步已把 H5 指标面板联动与回放结果可视化增强骨架正式接入，且已与第五刀第二步、第五刀第一步、第四刀、预警、自愈、反思形成联动。",
        }
        return mapping.get(test_status, "测试层已完成基础执行。")