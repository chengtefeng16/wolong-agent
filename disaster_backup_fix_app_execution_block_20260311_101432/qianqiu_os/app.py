# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

import uuid
import logging

from qianqiu_os.services.input_adapter import InputAdapter
from qianqiu_os.services.output_adapter import OutputAdapter
from qianqiu_os.services.agent_loader import AgentLoader
from qianqiu_os.services.scheduler import Scheduler
from qianqiu_os.services.state_manager import StateManager
from qianqiu_os.services.memory_manager import MemoryManager
from qianqiu_os.services.planner import Planner
from qianqiu_os.services.critic import Critic
from qianqiu_os.services.execution_manager import ExecutionManager
from qianqiu_os.services.promotion_manager import PromotionManager
from qianqiu_os.services.reflection_manager import ReflectionManager
from qianqiu_os.services.knowledge_graph_manager import KnowledgeGraphManager
from qianqiu_os.services.human_machine_loop_manager import HumanMachineLoopManager
from qianqiu_os.services.early_warning_manager import EarlyWarningManager
from qianqiu_os.services.metrics_manager import MetricsManager
from qianqiu_os.services.self_healing_manager import SelfHealingManager
from qianqiu_os.services.test_manager import TestManager
from qianqiu_os.registry.agent_registry import AgentRegistry
from qianqiu_os.registry.tool_registry import ToolRegistry
from qianqiu_os.managers.wolong_manager import WolongManager
from qianqiu_os.tools.policy_check_tool import policy_check_tool


def get_audit_logger():
    logger = logging.getLogger("qianqiu_os_audit")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def find_similar_experience(input_payload, tool_result):
    return {
        "matched_count": 0,
        "latest_decision": None,
        "latest_note": None,
    }


def build_platform_governance(result):
    tool_result = result.get("tool_result", {}) or {}
    wolong_result = result.get("wolong_result", {}) or {}

    manual_review_required = False
    governance_notes = []

    if tool_result.get("manual_review_required"):
        manual_review_required = True
        governance_notes.append("Tool result requires manual review.")

    if wolong_result.get("manual_review_result", {}).get("manual_review_required"):
        manual_review_required = True
        governance_notes.append("Wolong preliminary review requires human confirmation.")

    return {
        "manual_review_required": manual_review_required,
        "governance_notes": governance_notes,
    }


ENABLE_REAL_FAILED_STEP_INJECTION = True
ENABLE_TEST_CUT4_CONCURRENCY_BOUNDARY = True
ENABLE_TEST_CUT5_STEP1_REPLAY_METRICS = True
ENABLE_TEST_CUT5_STEP2_REPLAY_ENHANCED = True
ENABLE_TEST_CUT5_STEP3_H5_PANEL_LINKAGE = True


def main():
    audit_logger = get_audit_logger()

    input_adapter = InputAdapter()
    planner = Planner()
    output_adapter = OutputAdapter()
    state_manager = StateManager()
    memory_manager = MemoryManager()
    metrics_manager = MetricsManager()
    execution_manager = ExecutionManager()
    self_healing_manager = SelfHealingManager()
    critic = Critic()
    promotion_manager = PromotionManager()
    reflection_manager = ReflectionManager()
    knowledge_graph_manager = KnowledgeGraphManager()
    human_machine_loop_manager = HumanMachineLoopManager()
    early_warning_manager = EarlyWarningManager()
    test_manager = TestManager()
    agent_registry = AgentRegistry()
    tool_registry = ToolRegistry()
    wolong_manager = WolongManager(tool_registry=tool_registry)

    tool_registry.register("policy_check", policy_check_tool)

    agent_loader = AgentLoader()
    loaded_agents = agent_loader.load_agents(tool_registry, audit_logger)

    agent_profiles = {}
    for agent_id, agent_data in loaded_agents.items():
        agent_registry.register(agent_id, agent_data["instance"])
        agent_profiles[agent_id] = agent_data["profile"]

    scheduler = Scheduler(state_manager, audit_logger, agent_registry)

    incoming_input = input_adapter.normalize_input(
        source="whatsapp_mock",
        user_profile={
            "user_id": "wa_user_001",
            "customer_id": "cust_001",
            "source": "whatsapp",
            "display_name": "test_customer",
            "language": "en",
            "preference": "import feasibility",
        },
        message_text="Can I import a 2018 petrol SUV into Kenya?",
        metadata={
            "channel": "whatsapp",
            "session_id": "wa_session_001",
        },
    )

    user_profile = incoming_input["user_profile"]
    user_memory_context = memory_manager.upsert_user_memory(user_profile)

    task = scheduler.create_task(
        agent_id="wolong",
        task_type="policy_check",
        input_payload={
            "source": incoming_input["source"],
            "message_text": incoming_input["message_text"],
            "metadata": incoming_input["metadata"],
            "user_profile": user_profile,
            "country_code_or_name": "ke",
            "vehicle": {
                "age": 7,
                "fuel": "petrol",
                "emission": "unknown",
                "steering": "unknown",
                "certification": True,
                "ev_grid_risk": "low",
            },
        },
    )

    scheduler.enqueue_task(task)

    try:
        task, result = scheduler.dispatch_next_task()

        plan_context = planner.build_plan(task)

        experience_reference = find_similar_experience(
            task.input_payload,
            result.get("tool_result", {}),
        )
        result["experience_reference"] = experience_reference

        memory_context = memory_manager.get_memory_summary()
        result["memory_context"] = memory_context

        result["user_memory_context"] = user_memory_context
        result["input_context"] = incoming_input
        result["plan_context"] = plan_context
        result["agent_profile"] = agent_profiles.get(task.agent_id)

        wolong_result = wolong_manager.handle_inquiry(
            incoming_input=incoming_input,
            user_memory_context=user_memory_context,
        )
        result["wolong_result"] = wolong_result

        wolong_policy_result = (
            result.get("wolong_result", {}).get("policy_result")
            if isinstance(result.get("wolong_result", {}), dict)
            else None
        )
        if isinstance(wolong_policy_result, dict) and wolong_policy_result:
            result["tool_result"] = wolong_policy_result

        platform_governance = build_platform_governance(result)

        wolong_manual_review_required = (
            result.get("wolong_result", {})
            .get("manual_review_result", {})
            .get("manual_review_required", False)
        )

        if wolong_manual_review_required:
            platform_governance["manual_review_required"] = True
            platform_governance.setdefault("governance_notes", [])
            platform_governance["governance_notes"].append(
                "Wolong preliminary review requires human confirmation."
            )

        governance_notes = platform_governance.get("governance_notes", [])
        if isinstance(governance_notes, list):
            deduped_notes = []
            for note in governance_notes:
                if note not in deduped_notes:
                    deduped_notes.append(note)
            platform_governance["governance_notes"] = deduped_notes

        result["platform_governance"] = platform_governance

        execution_task = execution_manager.build_execution_task(
            task=task,
            plan_context=plan_context,
            agent_profile=result.get("agent_profile"),
        )
        result["execution_task"] = execution_task

        execution_result = {
            "execution_status": "pending",
            "executed_step_count": 0,
            "failed_step_count": 0,
            "failed_steps": [],
            "execution_logs": [],
            "control_flags": execution_task.get("control_flags", {}),
        }
        result["execution_result"] = execution_result

        heartbeat_context = {
            "module_name": "execution_layer",
            "heartbeat_status": "pending",
            "details": {
                "execution_id": execution_task.get("execution_id"),
                "task_id": execution_task.get("task_id"),
                "execution_status": "pending",
            },
        }
        result["heartbeat_context"] = heartbeat_context

        health_snapshot = {
            "module_name": "self_healing_manager_v5",
            "system_health": "pending",
            "execution_id": execution_task.get("execution_id"),
            "task_id": execution_task.get("task_id"),
            "execution_status": "pending",
            "failed_step_count": 0,
        }
        result["health_snapshot"] = health_snapshot

        healing_plan = {
            "healing_status": "pending",
            "healing_level": "none",
            "healing_actions": [],
            "healing_reason": "not_built_yet",
        }
        result["healing_plan"] = healing_plan

        healing_result = {
            "healing_execution_status": "pending",
            "executed_action_count": 0,
            "retry_result": {
                "retry_attempted": False,
                "retry_success_count": 0,
                "retry_failed_count": 0,
            },
            "repair_result": {
                "repair_attempted": False,
                "repair_success_count": 0,
                "repair_failed_count": 0,
            },
            "healing_execution_logs": [],
            "healing_summary": {
                "summary_text": "healing not executed yet",
            },
        }
        result["healing_result"] = healing_result

            result["reflection_log"] = reflection_log
            result["early_warning_log"] = early_warning_log
            result["cut4_result"] = cut4_result

        cut5_result = None
        if ENABLE_TEST_CUT5_STEP1_REPLAY_METRICS:
            cut5_bundle = test_manager.run_cut5_replay_metrics(
                execution_result=execution_result,
                healing_result=healing_result,
                reflection_log=reflection_log,
                early_warning_log=early_warning_log,
                cut4_result=cut4_result,
            )

            execution_result = cut5_bundle.get("execution_result", execution_result)
            healing_result = cut5_bundle.get("healing_result", healing_result)
            reflection_log = cut5_bundle.get("reflection_log", reflection_log)
            early_warning_log = cut5_bundle.get("early_warning_log", early_warning_log)
            cut5_result = cut5_bundle.get("cut5_result", cut5_result)

            result["execution_result"] = execution_result
            result["healing_result"] = healing_result
            result["reflection_log"] = reflection_log
            result["early_warning_log"] = early_warning_log
            result["cut5_result"] = cut5_result

        if ENABLE_TEST_CUT5_STEP2_REPLAY_ENHANCED:
            cut5_step2_bundle = test_manager.run_cut5_replay_metrics_step2(
                execution_result=execution_result,
                healing_result=healing_result,
                reflection_log=reflection_log,
                early_warning_log=early_warning_log,
                cut4_result=cut4_result,
                cut5_result_step1=cut5_result,
            )

            execution_result = cut5_step2_bundle.get("execution_result", execution_result)
            healing_result = cut5_step2_bundle.get("healing_result", healing_result)
            reflection_log = cut5_step2_bundle.get("reflection_log", reflection_log)
            early_warning_log = cut5_step2_bundle.get("early_warning_log", early_warning_log)
            cut5_result = cut5_step2_bundle.get("cut5_result", cut5_result)

            result["execution_result"] = execution_result
            result["healing_result"] = healing_result
            result["reflection_log"] = reflection_log
            result["early_warning_log"] = early_warning_log
            result["cut5_result"] = cut5_result

        if ENABLE_TEST_CUT5_STEP3_H5_PANEL_LINKAGE:
            cut5_step3_bundle = test_manager.run_cut5_h5_panel_linkage(
                execution_result=execution_result,
                healing_result=healing_result,
                reflection_log=reflection_log,
                early_warning_log=early_warning_log,
                cut4_result=cut4_result,
                cut5_result_step2=cut5_result,
            )

            execution_result = cut5_step3_bundle.get("execution_result", execution_result)
            healing_result = cut5_step3_bundle.get("healing_result", healing_result)
            reflection_log = cut5_step3_bundle.get("reflection_log", reflection_log)
            early_warning_log = cut5_step3_bundle.get("early_warning_log", early_warning_log)
            cut5_result = cut5_step3_bundle.get("cut5_result", cut5_result)

            result["execution_result"] = execution_result
            result["healing_result"] = healing_result
            result["reflection_log"] = reflection_log
            result["early_warning_log"] = early_warning_log
            result["cut5_result"] = cut5_result

        healing_log = self_healing_manager.build_healing_log(
            health_snapshot=health_snapshot,
            healing_plan=healing_plan,
            healing_result=healing_result,
        )
        result["healing_log"] = healing_log

        test_log = test_manager.build_test_blueprint_from_runtime(
            task_id=task.task_id,
            agent_id=task.agent_id,
            execution_result=execution_result,
            healing_result=healing_result,
            reflection_log=reflection_log,
            early_warning_log=early_warning_log,
            human_machine_loop_log=human_machine_loop_log,
            cut4_result=cut4_result,
            cut5_result=cut5_result,
        )
        result["test_log"] = test_log

        critic_context = critic.review(
            plan_context=plan_context,
            formatted_output=formatted_output,
            tool_result=result.get("tool_result", {}),
            experience_reference=experience_reference,
        )
        result["critic_context"] = critic_context

        if platform_governance["manual_review_required"]:
            state_manager.update_task_status(
                task.task_id,
                "waiting_human_review",
                result=result,
            )
            audit_logger.info(f"Task waiting_human_review: {task.task_id}")
        else:
            state_manager.update_task_status(
                task.task_id,
                "done",
                result=result,
            )
            audit_logger.info(f"Task done: {task.task_id}")

        print("=== TASK RESULT ===")
        print(result)

    except Exception as exc:
        failed_task_id = str(uuid.uuid4())
        audit_logger.exception(f"Task failed: {failed_task_id} | {exc}")
        raise


if __name__ == "__main__":
    main()
