# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

class InputAdapter:
    def normalize_input(self, source, user_profile, message_text, metadata=None):
        if metadata is None:
            metadata = {}

        return {
            "source": source,
            "user_profile": user_profile,
            "message_text": message_text,
            "metadata": metadata
        }