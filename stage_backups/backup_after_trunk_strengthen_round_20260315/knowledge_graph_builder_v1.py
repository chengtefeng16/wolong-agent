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
from typing import Any, Dict, List, Tuple

BASE_DIR = Path(__file__).resolve().parents[1]
MEMORY_DIR = BASE_DIR / "memory" / "customer_profiles"
GRAPH_DIR = BASE_DIR / "runtime_knowledge"


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _read_json(path: Path, default: Any):
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _write_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class KnowledgeGraphBuilderV1:
    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: Dict[Tuple[str, str, str], Dict[str, Any]] = {}

    def _add_node(self, node_id: str, node_type: str, label: str, extra: Dict[str, Any] | None = None):
        if not node_id:
            return
        if node_id not in self.nodes:
            self.nodes[node_id] = {
                "id": node_id,
                "type": node_type,
                "label": label,
            }
            if extra:
                self.nodes[node_id].update(extra)

    def _add_edge(self, source: str, target: str, relation: str, extra: Dict[str, Any] | None = None):
        if not source or not target or not relation:
            return
        key = (source, target, relation)
        if key not in self.edges:
            self.edges[key] = {
                "source": source,
                "target": target,
                "relation": relation,
            }
            if extra:
                self.edges[key].update(extra)

    def _load_profiles(self) -> List[Dict[str, Any]]:
        profiles = []
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        for path in MEMORY_DIR.glob("*.json"):
            data = _read_json(path, {})
            if isinstance(data, dict) and data:
                profiles.append(data)
        return profiles

    def build(self) -> Dict[str, Any]:
        profiles = self._load_profiles()

        for profile in profiles:
            customer_id = str(profile.get("customer_id") or "").strip()
            latest = profile.get("latest_profile", {}) or {}

            customer_name = profile.get("customer_name") or customer_id
            country = profile.get("country") or latest.get("destination_country") or ""
            bucket = latest.get("bucket") or ""
            stage = latest.get("business_stage") or ""
            models = latest.get("models") or []

            customer_node_id = f"customer::{customer_id}"
            self._add_node(
                customer_node_id,
                "customer",
                customer_name,
                {
                    "customer_id": customer_id,
                    "priority": latest.get("priority"),
                    "needs_human_review": latest.get("needs_human_review"),
                },
            )

            if country:
                country_node_id = f"country::{country}"
                self._add_node(country_node_id, "country", country)
                self._add_edge(customer_node_id, country_node_id, "destination_country")

            if bucket:
                bucket_node_id = f"bucket::{bucket}"
                self._add_node(bucket_node_id, "bucket", bucket)
                self._add_edge(customer_node_id, bucket_node_id, "classified_as")

            if stage:
                stage_node_id = f"stage::{stage}"
                self._add_node(stage_node_id, "business_stage", stage)
                self._add_edge(customer_node_id, stage_node_id, "current_stage")

            for model in models:
                model_node_id = f"model::{model}"
                self._add_node(model_node_id, "car_model", model)
                self._add_edge(customer_node_id, model_node_id, "interested_in")

        payload = {
            "generated_at": _now_str(),
            "graph_name": "knowledge_graph_latest",
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "nodes": list(self.nodes.values()),
            "edges": list(self.edges.values()),
        }

        latest_path = GRAPH_DIR / "knowledge_graph_latest.json"
        dated_path = GRAPH_DIR / f"knowledge_graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        _write_json(latest_path, payload)
        _write_json(dated_path, payload)

        return {
            "success": True,
            "knowledge_graph_latest_path": str(latest_path),
            "dated_knowledge_graph_path": str(dated_path),
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
        }


if __name__ == "__main__":
    print(json.dumps(KnowledgeGraphBuilderV1().build(), ensure_ascii=False, indent=2))
