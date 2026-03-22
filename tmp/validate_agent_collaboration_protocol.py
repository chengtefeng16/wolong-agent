import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

protocol_path = PROJECT_ROOT / "qianqiu_os" / "AGENT_COLLABORATION_PROTOCOL.md"
matrix_path = PROJECT_ROOT / "qianqiu_os" / "config" / "agent_collaboration_matrix_v1.json"

result = {
    "protocol_exists": protocol_path.exists(),
    "matrix_exists": matrix_path.exists(),
}

if matrix_path.exists():
    with open(matrix_path, "r", encoding="utf-8") as f:
        matrix = json.load(f)
    result["agent_count"] = len(matrix.get("agents", []))
    result["trigger_rule_count"] = len(matrix.get("trigger_rules", []))
    result["has_wolong"] = any(item.get("agent_id") == "wolong" for item in matrix.get("agents", []))
    result["has_fuxue"] = any(item.get("agent_id") == "fuxue" for item in matrix.get("agents", []))
    result["has_legal_guardian"] = any(item.get("agent_id") == "legal_guardian" for item in matrix.get("agents", []))

print(json.dumps(result, ensure_ascii=False, indent=2))
