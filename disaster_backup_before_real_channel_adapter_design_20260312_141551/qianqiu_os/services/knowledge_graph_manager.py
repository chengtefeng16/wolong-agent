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
class GraphNode:
    node_id: str
    node_type: str
    name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class GraphEdge:
    edge_id: str
    source_id: str
    relation: str
    target_id: str
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class KnowledgeGraphSnapshot:
    graph_id: str
    task_id: str
    agent_id: str
    node_count: int
    edge_count: int
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    edges: List[Dict[str, Any]] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class KnowledgeGraphManager:
    """
    知识图谱第一刀：
    - 最小实体骨架
    - 最小关系骨架
    - 图谱快照输出

    当前定位：
    1. 先把业务对象组织成点和线。
    2. 先服务于“可理解、可回看、可扩展”。
    3. 后续再逐步增强查询、归纳、模式识别与经验联动。
    """

    def __init__(self) -> None:
        self.module_name = "knowledge_graph_manager_v1"
        self.allowed_node_types = {
            "customer",
            "country",
            "product",
            "order",
            "fund",
            "risk",
            "event",
        }

    def build_node(
        self,
        node_id: str,
        node_type: str,
        name: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        normalized_type = node_type if node_type in self.allowed_node_types else "event"
        node = GraphNode(
            node_id=node_id,
            node_type=normalized_type,
            name=name,
            properties=properties or {},
        )
        return asdict(node)

    def build_edge(
        self,
        edge_id: str,
        source_id: str,
        relation: str,
        target_id: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        edge = GraphEdge(
            edge_id=edge_id,
            source_id=source_id,
            relation=relation,
            target_id=target_id,
            properties=properties or {},
        )
        return asdict(edge)

    def build_graph_snapshot(
        self,
        task_id: str,
        agent_id: str,
        nodes: Optional[List[Dict[str, Any]]] = None,
        edges: Optional[List[Dict[str, Any]]] = None,
        summary: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        nodes = nodes or []
        edges = edges or []
        snapshot = KnowledgeGraphSnapshot(
            graph_id=f"kg_{task_id}",
            task_id=task_id,
            agent_id=agent_id,
            node_count=len(nodes),
            edge_count=len(edges),
            nodes=nodes,
            edges=edges,
            summary=summary or {},
        )
        return asdict(snapshot)

    def build_graph_from_runtime(
        self,
        task_id: str,
        agent_id: str,
        input_context: Optional[Dict[str, Any]] = None,
        tool_result: Optional[Dict[str, Any]] = None,
        execution_task: Optional[Dict[str, Any]] = None,
        agent_profile: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        input_context = input_context or {}
        tool_result = tool_result or {}
        execution_task = execution_task or {}
        agent_profile = agent_profile or {}

        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []

        user_profile = input_context.get("user_profile", {})
        source = input_context.get("source", "unknown")
        message_text = input_context.get("message_text", "")

        customer_id = user_profile.get("user_id", "unknown_customer")
        customer_name = user_profile.get("display_name", "Unknown Customer")
        customer_node = self.build_node(
            node_id=f"customer_{customer_id}",
            node_type="customer",
            name=customer_name,
            properties={
                "source": source,
                "language": user_profile.get("language"),
                "preference": user_profile.get("preference"),
            },
        )
        nodes.append(customer_node)

        country_info = tool_result.get("policy_country", {})
        country_name = country_info.get("name", "Unknown Country")
        country_node = self.build_node(
            node_id=f"country_{country_info.get('iso2', 'unknown')}",
            node_type="country",
            name=country_name,
            properties={
                "iso2": country_info.get("iso2"),
                "aliases": country_info.get("aliases", []),
            },
        )
        nodes.append(country_node)

        product_node = self.build_node(
            node_id="product_used_vehicle_export",
            node_type="product",
            name="二手车出口服务",
            properties={
                "category": "used_vehicle_trade",
                "message_text": message_text,
            },
        )
        nodes.append(product_node)

        risk_level = tool_result.get("risk_level", "unknown")
        risk_node = self.build_node(
            node_id=f"risk_{risk_level}",
            node_type="risk",
            name=f"{risk_level} risk",
            properties={
                "compliance_complexity": tool_result.get("compliance_complexity"),
                "cost_risk": tool_result.get("cost_risk"),
                "warnings": tool_result.get("warnings", []),
            },
        )
        nodes.append(risk_node)

        event_node = self.build_node(
            node_id=f"event_{task_id}",
            node_type="event",
            name="policy_check_task_event",
            properties={
                "task_type": execution_task.get("execution_mode"),
                "agent_domain": agent_profile.get("domain"),
            },
        )
        nodes.append(event_node)

        order_node = self.build_node(
            node_id=f"order_like_{task_id}",
            node_type="order",
            name="咨询意向单",
            properties={
                "status": "pre_order_intent",
                "task_id": task_id,
            },
        )
        nodes.append(order_node)

        edges.append(
            self.build_edge(
                edge_id=f"edge_customer_product_{task_id}",
                source_id=customer_node["node_id"],
                relation="interested_in",
                target_id=product_node["node_id"],
                properties={"source": source},
            )
        )

        edges.append(
            self.build_edge(
                edge_id=f"edge_product_country_{task_id}",
                source_id=product_node["node_id"],
                relation="related_to",
                target_id=country_node["node_id"],
                properties={"reason": "current_policy_check_target"},
            )
        )

        edges.append(
            self.build_edge(
                edge_id=f"edge_order_customer_{task_id}",
                source_id=order_node["node_id"],
                relation="belongs_to",
                target_id=customer_node["node_id"],
                properties={"stage": "pre_sales"},
            )
        )

        edges.append(
            self.build_edge(
                edge_id=f"edge_order_risk_{task_id}",
                source_id=order_node["node_id"],
                relation="has_risk",
                target_id=risk_node["node_id"],
                properties={"risk_level": risk_level},
            )
        )

        edges.append(
            self.build_edge(
                edge_id=f"edge_event_country_{task_id}",
                source_id=event_node["node_id"],
                relation="affects",
                target_id=country_node["node_id"],
                properties={"event_type": "policy_check"},
            )
        )

        edges.append(
            self.build_edge(
                edge_id=f"edge_event_product_{task_id}",
                source_id=event_node["node_id"],
                relation="affects",
                target_id=product_node["node_id"],
                properties={"event_type": "trade_service_analysis"},
            )
        )

        summary = {
            "customer_count": 1,
            "country_count": 1,
            "product_count": 1,
            "order_count": 1,
            "risk_count": 1,
            "event_count": 1,
            "graph_meaning": "将当前任务中的客户、国家、商品、订单意向、风险与事件组织为最小关系图谱。",
        }

        return self.build_graph_snapshot(
            task_id=task_id,
            agent_id=agent_id,
            nodes=nodes,
            edges=edges,
            summary=summary,
        )
