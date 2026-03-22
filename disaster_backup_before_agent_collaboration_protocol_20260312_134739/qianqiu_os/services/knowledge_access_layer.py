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
from pathlib import Path


class KnowledgeAccessLayer:
    def __init__(self, base_dir=None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[1]
        self.base_dir = Path(base_dir)

    def load_json(self, relative_path):
        path = self.base_dir / relative_path
        if not path.exists():
            return {
                "success": False,
                "source_type": "json",
                "path": str(path),
                "message": "file not found",
                "data": None,
            }

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "success": True,
                "source_type": "json",
                "path": str(path),
                "message": "loaded",
                "data": data,
            }
        except Exception as e:
            return {
                "success": False,
                "source_type": "json",
                "path": str(path),
                "message": str(e),
                "data": None,
            }

    def load_text(self, relative_path):
        path = self.base_dir / relative_path
        if not path.exists():
            return {
                "success": False,
                "source_type": "text",
                "path": str(path),
                "message": "file not found",
                "data": None,
            }

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = f.read()
            return {
                "success": True,
                "source_type": "text",
                "path": str(path),
                "message": "loaded",
                "data": data,
            }
        except Exception as e:
            return {
                "success": False,
                "source_type": "text",
                "path": str(path),
                "message": str(e),
                "data": None,
            }

    def load_runtime_delegation_config(self):
        return self.load_json("runtime_governance/delegation_active_config.json")

    def load_h5_schema(self):
        return self.load_json("config/h5_delegation_form_schema_v1.json")

    def load_h5_default_config(self):
        return self.load_json("config/h5_delegation_default_config_v1.json")

    def load_h5_presets(self):
        return self.load_json("config/h5_delegation_presets_v1.json")

    def load_integration_checklist(self):
        return self.load_text("H5_DELEGATION_INTEGRATION_CHECKLIST.md")
