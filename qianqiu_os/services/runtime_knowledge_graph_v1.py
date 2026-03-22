# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

import json
import sys
from datetime import datetime
from pathlib import Path

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

BASE_DIR = Path(__file__).resolve().parents[1]
WHATSAPP_VIEW_PATH = BASE_DIR / "runtime_views" / "h5_dashboard_whatsapp.json"
GRAPH_OUTPUT_PATH = BASE_DIR / "runtime_views" / "knowledge_graph" / "customer_graph_v1.json"


class RuntimeKnowledgeGraphV1:
    def _now_str(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _read_json(self, path: Path):
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def _write_json(self, path: Path, data: dict):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def build_graph(self):
        source = self._read_json(WHATSAPP_VIEW_PATH) or {}

        raw_items = []
        if isinstance(source.get("recent_focus"), list):
            raw_items = source.get("recent_focus") or []
        elif isinstance(source.get("customers"), list):
            raw_items = source.get("customers") or []
        elif isinstance(source.get("items"), list):
            raw_items = source.get("items") or []
        elif isinstance(source.get("records"), list):
            raw_items = source.get("records") or []

        nodes = []
        edges = []
        seen_nodes = set()

        def add_node(node_id, node_type, label, extra=None):
            if not node_id or node_id in seen_nodes:
                return
            seen_nodes.add(node_id)
            node = {
                "id": node_id,
                "type": node_type,
                "label": label,
            }
            if extra:
                node.update(extra)
            nodes.append(node)

        def add_edge(source_id, target_id, relation):
            if not source_id or not target_id:
                return
            edges.append({
                "source": source_id,
                "target": target_id,
                "relation": relation,
            })

        for idx, item in enumerate(raw_items):
            if not isinstance(item, dict):
                continue

            phone = str(item.get("phone") or f"phone_{idx+1}")
            customer_name = item.get("customer_name") or item.get("name") or phone
            bucket = item.get("bucket") or item.get("category") or "待判断"
            latest_message = item.get("latest_message") or item.get("message") or ""

            customer_node = f"customer::{phone}"
            bucket_node = f"bucket::{bucket}"

            add_node(customer_node, "customer", customer_name, {
                "phone": phone,
                "latest_message": latest_message,
            })
            add_node(bucket_node, "bucket", bucket)

            add_edge(customer_node, bucket_node, "belongs_to_bucket")

            if latest_message:
                message_node = f"message::{phone}"
                add_node(message_node, "message", latest_message)
                add_edge(customer_node, message_node, "has_latest_message")

                lowered = latest_message.lower()
                keyword_candidates = [
                    "prado", "camry", "suv", "units", "regularly", "prices",
                    "export", "dealer", "showroom", "resale"
                ]
                for kw in keyword_candidates:
                    if kw in lowered:
                        kw_node = f"keyword::{kw}"
                        add_node(kw_node, "keyword", kw)
                        add_edge(customer_node, kw_node, "mentions_keyword")

        top_stats = source.get("top_stats", {}) or {}
        for label, value in top_stats.items():
            stat_node = f"stat::{label}"
            add_node(stat_node, "stat", label, {"count": value})

        result = {
            "graph_name": "customer_graph_v1",
            "built_at": self._now_str(),
            "source_path": str(WHATSAPP_VIEW_PATH),
            "source_top_keys": list(source.keys()) if isinstance(source, dict) else [],
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": nodes,
            "edges": edges,
        }

        self._write_json(GRAPH_OUTPUT_PATH, result)
        return result


if __name__ == "__main__":
    builder = RuntimeKnowledgeGraphV1()
    print(json.dumps(builder.build_graph(), ensure_ascii=False, indent=2))
