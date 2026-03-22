# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

from datetime import datetime


class PromotionManager:
    def __init__(self):
        self.module_name = "promotion_manager_v2"
        self.allowed_promotion_modes = {"silent", "test", "scale"}
        self.allowed_promotion_intensity = {"low", "medium", "high"}

    def build_promotion_task(self, agent_profile=None, promotion_goal=None):
        if agent_profile is None:
            agent_profile = {}
        if promotion_goal is None:
            promotion_goal = {}

        agent_name = agent_profile.get("name", "Unknown Agent")
        agent_domain = agent_profile.get("domain", "unknown")

        promotion_mode = promotion_goal.get("promotion_mode", "silent")
        if promotion_mode not in self.allowed_promotion_modes:
            promotion_mode = "silent"

        promotion_intensity = promotion_goal.get("promotion_intensity", "low")
        if promotion_intensity not in self.allowed_promotion_intensity:
            promotion_intensity = "low"

        return {
            "promotion_id": f"promo_{agent_profile.get('agent_id', 'unknown')}",
            "agent_id": agent_profile.get("agent_id"),
            "agent_name": agent_name,
            "agent_domain": agent_domain,
            "promotion_status": "planned",
            "approval_status": "pending",
            "requires_human_approval": True,
            "promotion_goal": promotion_goal,
            "promotion_mode": promotion_mode,
            "promotion_intensity": promotion_intensity,
            "control_flags": {
                "can_execute": False,
                "can_pause": True,
                "can_stop": True
            },
            "created_at": datetime.utcnow().isoformat()
        }

    def generate_promotion_content(self, agent_profile=None, promotion_goal=None):
        if agent_profile is None:
            agent_profile = {}
        if promotion_goal is None:
            promotion_goal = {}

        agent_name = agent_profile.get("name", "Unknown Agent")
        description = agent_profile.get("description", "")
        target_channel = promotion_goal.get("target_channel", "web_content")
        target_audience = promotion_goal.get("target_audience", "general_users")
        promotion_mode = promotion_goal.get("promotion_mode", "silent")

        content_title = f"{agent_name} 能为你做什么？"
        content_body = (
            f"{agent_name} 是一个面向 {agent_profile.get('domain', 'unknown')} 领域的垂直智能体。"
            f"它当前的核心定位是：{description}。"
            f"本次推广面向对象为：{target_audience}，目标渠道为：{target_channel}，"
            f"当前推广模式为：{promotion_mode}。"
        )

        return {
            "content_title": content_title,
            "content_body": content_body,
            "content_status": "drafted",
            "generated_at": datetime.utcnow().isoformat()
        }

    def build_distribution_plan(self, promotion_task, promotion_content):
        target_channel = promotion_task.get("promotion_goal", {}).get("target_channel", "web_content")
        promotion_mode = promotion_task.get("promotion_mode", "silent")
        promotion_intensity = promotion_task.get("promotion_intensity", "low")

        distribution_actions = [
            {
                "step": 1,
                "executor": "promotion",
                "action": "prepare_content",
                "status": "pending",
                "description": "整理并确认推广内容草稿。"
            },
            {
                "step": 2,
                "executor": "human_gate",
                "action": "await_human_approval",
                "status": "pending",
                "description": "等待人类确认后才允许进入真实推广执行。"
            },
            {
                "step": 3,
                "executor": "execution_layer",
                "action": "open_publish_page",
                "status": "pending",
                "description": "预留给执行层打开目标发布页面。",
                "payload": {
                    "target_channel": target_channel
                }
            },
            {
                "step": 4,
                "executor": "execution_layer",
                "action": "submit_content",
                "status": "pending",
                "description": "预留给执行层提交推广内容。",
                "payload": {
                    "content_title": promotion_content.get("content_title"),
                    "content_body": promotion_content.get("content_body")
                }
            }
        ]

        return {
            "distribution_status": "planned",
            "approval_status": promotion_task.get("approval_status", "pending"),
            "requires_human_approval": promotion_task.get("requires_human_approval", True),
            "promotion_mode": promotion_mode,
            "promotion_intensity": promotion_intensity,
            "target_channel": target_channel,
            "distribution_actions": distribution_actions,
            "planned_at": datetime.utcnow().isoformat()
        }

    def build_promotion_log(self, promotion_task, promotion_content, distribution_plan):
        return {
            "module_name": self.module_name,
            "promotion_task": promotion_task,
            "promotion_content": promotion_content,
            "distribution_plan": distribution_plan,
            "logged_at": datetime.utcnow().isoformat()
        }
