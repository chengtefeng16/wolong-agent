import json
from pathlib import Path

project_root = Path.cwd()
doc_path = project_root / "qianqiu_os" / "WOLONG_WHATSAPP_GRAY_OPEN_CONDITIONS_V1.md"
cfg_path = project_root / "qianqiu_os" / "config" / "wolong_whatsapp_gray_open_checklist_v1.json"

result = {
    "doc_exists": doc_path.exists(),
    "config_exists": cfg_path.exists(),
    "doc_size_bytes": doc_path.stat().st_size if doc_path.exists() else 0,
    "config_size_bytes": cfg_path.stat().st_size if cfg_path.exists() else 0
}

if cfg_path.exists():
    with open(cfg_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    result["gray_open_enabled"] = data.get("gray_open_enabled")
    result["allowed_channel_count"] = len(data.get("allowed_channels", []))
    result["allowed_stage_count"] = len(data.get("allowed_business_stages", []))
    result["allowed_risk_count"] = len(data.get("allowed_risk_levels", []))
    result["shutdown_trigger_count"] = len(data.get("shutdown_triggers", []))

print(json.dumps(result, ensure_ascii=False, indent=2))
