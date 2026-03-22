import json
from pathlib import Path

project_root = Path.cwd()
checklist_path = project_root / "qianqiu_os" / "WOLONG_REAL_SOCIAL_MEDIA_READINESS_CHECKLIST.md"

result = {
    "checklist_exists": checklist_path.exists(),
    "path": str(checklist_path),
    "size_bytes": checklist_path.stat().st_size if checklist_path.exists() else 0
}

print(json.dumps(result, ensure_ascii=False, indent=2))
