<!-- ================================================================
Copyright (c) 2026 程特峰 (Tefeng Cheng)
All Rights Reserved.

Project: AgentOS / Wolong Agent System
This document and its contents are proprietary and confidential.
Unauthorized copying, modification, distribution or use of this
document, in whole or in part, is strictly prohibited.
================================================================ -->

# SCHEDULING OVERVIEW SUMMARY · 2026-03-14

- 生成时间：2026-03-14 18:09:02

## WhatsApp Control
- ingress_mode: readonly
- auto_reply: False
- auto_dispatch: False

## Delegation Policy Keys
- action_control
- allowed_actions
- allowed_channels
- allowed_time_windows
- audit_control
- audit_required
- business_stage
- business_stage_control
- business_stages_allowed
- channel_control
- configurable_fields
- delegation_enabled
- delegation_master_switch
- delegation_stage
- destination_country
- exception_control
- fallback_to_human_on_risk
- human_supervision_mode
- l1_whitelist_candidate
- manual_review_required
- next_action
- permission_control
- permission_level
- quota_control
- risk_control
- risk_level
- risk_levels_allowed
- rollback_enabled
- supervision_control
- time_control

## Time Logic Summary
- nightly_status: scheduled
- weekly_report_status: scheduled
- window_handoff_status: always_required

## 结论
调度层已具备配置调度 + 时间调度总览能力。
