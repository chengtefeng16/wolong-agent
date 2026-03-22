import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from qianqiu_os.services.knowledge_access_layer import KnowledgeAccessLayer

layer = KnowledgeAccessLayer()

faq_result = layer.load_wolong_faq_pack()
rule_result = layer.load_wolong_rule_pack()

result = {
    "wolong_faq_pack_loaded": faq_result["success"],
    "wolong_rule_pack_loaded": rule_result["success"],
    "faq_item_count": len((faq_result.get("data") or {}).get("items", [])) if faq_result["success"] else 0,
    "rule_item_count": len((rule_result.get("data") or {}).get("rules", [])) if rule_result["success"] else 0,
    "faq_pack_name": (faq_result.get("data") or {}).get("pack_name") if faq_result["success"] else None,
    "rule_pack_name": (rule_result.get("data") or {}).get("pack_name") if rule_result["success"] else None
}

print(json.dumps(result, ensure_ascii=False, indent=2))
