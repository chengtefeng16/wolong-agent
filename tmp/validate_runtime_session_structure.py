import json
from pathlib import Path

project_root = Path.cwd()

paths = {
    "conversation_index": project_root / "qianqiu_os/runtime_sessions/whatsapp/conversation_index.json",
    "conversation_1": project_root / "qianqiu_os/runtime_sessions/whatsapp/conversations/+77011234567.json",
    "conversation_2": project_root / "qianqiu_os/runtime_sessions/whatsapp/conversations/+992900000001.json",
    "conversation_3": project_root / "qianqiu_os/runtime_sessions/whatsapp/conversations/+79161230000.json",
    "tag_index": project_root / "qianqiu_os/runtime_sessions/whatsapp/tags/tag_index.json",
    "crm_queue": project_root / "qianqiu_os/runtime_sessions/whatsapp/exports/crm_export_queue.json",
    "h5_view": project_root / "qianqiu_os/runtime_views/h5_dashboard_whatsapp.json",
}

result = {k: v.exists() for k, v in paths.items()}

if paths["conversation_index"].exists():
    with open(paths["conversation_index"], "r", encoding="utf-8") as f:
        data = json.load(f)
    result["conversation_index_count"] = len(data.get("items", []))

if paths["tag_index"].exists():
    with open(paths["tag_index"], "r", encoding="utf-8") as f:
        data = json.load(f)
    result["tag_stats"] = data.get("stats", {})

print(json.dumps(result, ensure_ascii=False, indent=2))
