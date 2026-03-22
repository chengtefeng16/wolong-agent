# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

class BusinessContextManager:
    def build_context(
        self,
        input_context=None,
        tool_result=None,
        wolong_result=None,
        user_memory_context=None,
    ):
        input_context = input_context or {}
        tool_result = tool_result or {}
        wolong_result = wolong_result or {}
        user_memory_context = user_memory_context or {}

        metadata = input_context.get("metadata", {}) or {}
        user_profile = input_context.get("user_profile", {}) or {}
        business_action_result = wolong_result.get("business_action_result", {}) or {}
        customer_reply_result = wolong_result.get("customer_reply_result", {}) or {}
        manual_review_result = wolong_result.get("manual_review_result", {}) or {}

        business_stage = self._first_non_empty(
            business_action_result.get("business_stage"),
            user_profile.get("business_stage"),
            metadata.get("business_stage"),
            user_memory_context.get("business_stage"),
        )

        risk_level = self._first_non_empty(
            business_action_result.get("risk_level"),
            tool_result.get("risk_level"),
            user_profile.get("risk_level"),
            metadata.get("risk_level"),
            user_memory_context.get("risk_level"),
        )

        destination_country = self._first_non_empty(
            business_action_result.get("destination_country"),
            metadata.get("destination_country"),
            user_profile.get("destination_country"),
            user_memory_context.get("destination_country"),
        )

        customer_type = self._first_non_empty(
            business_action_result.get("customer_type"),
            user_profile.get("customer_type"),
            metadata.get("customer_type"),
            user_memory_context.get("customer_type"),
        )

        intent_type = self._first_non_empty(
            business_action_result.get("intent_type"),
            tool_result.get("intent_type"),
            metadata.get("intent_type"),
            user_memory_context.get("intent_type"),
        )

        emotion_state = self._infer_emotion_state(
            business_action_result=business_action_result,
            customer_reply_result=customer_reply_result,
            manual_review_result=manual_review_result,
            metadata=metadata,
            user_profile=user_profile,
            user_memory_context=user_memory_context,
        )

        return {
            "business_stage": business_stage,
            "risk_level": risk_level,
            "destination_country": destination_country,
            "customer_type": customer_type,
            "intent_type": intent_type,
            "emotion_state": emotion_state,
        }

    def _infer_emotion_state(
        self,
        business_action_result,
        customer_reply_result,
        manual_review_result,
        metadata,
        user_profile,
        user_memory_context,
    ):
        return self._first_non_empty(
            business_action_result.get("emotion_state"),
            customer_reply_result.get("emotion_state"),
            manual_review_result.get("emotion_state"),
            metadata.get("emotion_state"),
            user_profile.get("emotion_state"),
            user_memory_context.get("emotion_state"),
        )

    def _first_non_empty(self, *values):
        for value in values:
            if value is None:
                continue
            if isinstance(value, str) and not value.strip():
                continue
            return value
        return None
