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


class MemoryManager:
    def __init__(
        self,
        task_memory_path="qianqiu_os/data/tasks.json",
        experience_memory_path="qianqiu_os/data/experience_log.json",
        user_memory_path="qianqiu_os/data/user_memory.json",
        knowledge_memory_root="knowledge/"
    ):
        self.task_memory_path = task_memory_path
        self.experience_memory_path = experience_memory_path
        self.user_memory_path = user_memory_path
        self.knowledge_memory_root = knowledge_memory_root

    def _load_json_file(self, path):
        if not os.path.exists(path):
            return []

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_json_file(self, path, data):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_task_memory(self):
        return self._load_json_file(self.task_memory_path)

    def load_experience_memory(self):
        return self._load_json_file(self.experience_memory_path)

    def load_user_memory(self):
        return self._load_json_file(self.user_memory_path)

    def get_knowledge_memory_root(self):
        return self.knowledge_memory_root

    def get_memory_summary(self):
        task_memory = self.load_task_memory()
        experience_memory = self.load_experience_memory()
        user_memory = self.load_user_memory()

        return {
            "task_memory_count": len(task_memory),
            "experience_memory_count": len(experience_memory),
            "user_memory_count": len(user_memory),
            "knowledge_memory_root": self.knowledge_memory_root
        }

    def upsert_user_memory(self, user_profile: dict):
        if not user_profile:
            return None

        user_id = user_profile.get("user_id")
        if not user_id:
            return None

        user_memory = self.load_user_memory()

        existing = None
        for item in user_memory:
            if item.get("user_id") == user_id:
                existing = item
                break

        now = datetime.utcnow().isoformat()

        if existing:
            existing["source"] = user_profile.get("source")
            existing["display_name"] = user_profile.get("display_name")
            existing["language"] = user_profile.get("language")
            existing["preference"] = user_profile.get("preference")
            existing["last_seen_at"] = now
        else:
            existing = {
                "user_id": user_id,
                "source": user_profile.get("source"),
                "display_name": user_profile.get("display_name"),
                "language": user_profile.get("language"),
                "preference": user_profile.get("preference"),
                "created_at": now,
                "last_seen_at": now
            }
            user_memory.append(existing)

        self._save_json_file(self.user_memory_path, user_memory)
        return existing

    def get_user_memory(self, user_id: str):
        user_memory = self.load_user_memory()
        for item in user_memory:
            if item.get("user_id") == user_id:
                return item
        return None