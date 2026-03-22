import json
from pathlib import Path

project_root = Path.cwd()
policy_path = project_root / "qianqiu_os" / "WOLONG_GRAY_RELEASE_POLICY_V1.md"
whitelist_path = project_root / "qianqiu_os" / "config" / "wolong_gray_release_whitelist_v1.json"

result = {
    "policy_exists": policy_path.exists(),
    "whitelist_exists": whitelist_path.exists(),
    "policy_size_bytes": policy_path.stat().st_size if policy_path.exists() else 0,
    "whitelist_size_bytes": whitelist_path.stat().st_size if whitelist_path.exists() else 0
}

if whitelist_path.exists():
    with open(whitelist_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    result["enabled"] = data.get("enabled")
    result["customer_whitelist_count"] = len(data.get("customer_whitelist", []))
    result["channel_whitelist_count"] = len(data.get("channel_whitelist", []))
    result["allowed_business_stage_count"] = len(data.get("allowed_business_stages", []))
    result["allowed_risk_level_count"] = len(data.get("allowed_risk_levels", []))
    result["fallback_mode"] = data.get("fallback_mode")

print(json.dumps(result, ensure_ascii=False, indent=2))
