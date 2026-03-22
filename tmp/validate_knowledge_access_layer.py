import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from qianqiu_os.services.knowledge_access_layer import KnowledgeAccessLayer

layer = KnowledgeAccessLayer()

result = {
    "runtime_delegation_config": layer.load_runtime_delegation_config()["success"],
    "h5_schema": layer.load_h5_schema()["success"],
    "h5_default_config": layer.load_h5_default_config()["success"],
    "h5_presets": layer.load_h5_presets()["success"],
    "integration_checklist": layer.load_integration_checklist()["success"],
}

print(json.dumps(result, ensure_ascii=False, indent=2))
