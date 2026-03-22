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
import os
from datetime import datetime


class StateManager:
    def __init__(self, file_path="qianqiu_os/data/tasks.json"):
        self.file_path = file_path
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)

    def _load(self):
        with open(self.file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def create_task(self, task):
        data = self._load()
        data.append(task.to_dict())
        self._save(data)

    def update_task_status(self, task_id, status, result=None, error_message=None):
        data = self._load()
        for item in data:
            if item["task_id"] == task_id:
                item["status"] = status
                item["updated_at"] = datetime.utcnow().isoformat()
                if result is not None:
                    item["result"] = result
                if error_message is not None:
                    item["error_message"] = error_message
                break
        self._save(data)

    def update_task_fields(self, task_id, fields: dict):
        data = self._load()
        for item in data:
            if item["task_id"] == task_id:
                for key, value in fields.items():
                    item[key] = value
                item["updated_at"] = datetime.utcnow().isoformat()
                break
        self._save(data)

    def get_task(self, task_id):
        data = self._load()
        for item in data:
            if item["task_id"] == task_id:
                return item
        return None