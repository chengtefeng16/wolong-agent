<!-- ================================================================
Copyright (c) 2026 程特峰 (Tefeng Cheng)
All Rights Reserved.

Project: AgentOS / Wolong Agent System
This document and its contents are proprietary and confidential.
Unauthorized copying, modification, distribution or use of this
document, in whole or in part, is strictly prohibited.
================================================================ -->

# 卧龙 Agent 真实发送结果闭环设计（V1）

## 1. 目标
本设计用于把卧龙 Agent 的真实发送执行面补齐为闭环。

所谓“发送结果闭环”，包括：
- 发前有记录
- 发后有结果
- 异常有分类
- 是否可重试有判断
- 是否需人工接管有建议
- 审计有落盘
- 后续可回看、可追踪、可统计

---

## 2. 闭环的必要性
如果只有“发出去了”或“没发出去”，是不够的。

真实执行面必须能回答：
1. 这条消息为什么会被允许发？
2. 发给了谁？
3. 通过哪个渠道发？
4. 渠道返回了什么？
5. 成功还是失败？
6. 是普通失败、限流、认证异常还是账号异常？
7. 能不能重试？
8. 是否必须人工接管？
9. 审计记录在哪里？

---

## 3. 闭环结构（最小版）

### 3.1 发前记录（pre_send_record）
至少包括：
- trace_id
- channel
- customer_id
- session_id
- send_text
- business_context
- delegation_decision
- config_version
- applied_preset
- created_at

### 3.2 发后结果（post_send_result）
至少包括：
- success
- channel
- delivery_status
- provider_message_id
- error_code
- error_message
- retryable
- fallback_action
- finished_at

### 3.3 审计记录（audit_record）
审计层应同时保存：
- 发前记录
- 发后结果
- 最终状态
- 是否进入人工接管

---

## 4. 最小状态分类建议

### 成功类
- sent

### 待人工类
- pending_manual

### 失败类
- failed
- blocked
- rate_limited
- provider_unavailable
- auth_invalid
- account_blocked
- invalid_payload

---

## 5. retryable 判断建议

### 可重试
- send_failed
- rate_limited
- provider_unavailable

### 不可重试
- auth_invalid
- account_blocked
- invalid_payload
- channel_not_supported
- channel_disabled
- adapter_disabled

---

## 6. fallback_action 建议

### 可选值
- human_review
- manual_takeover
- draft_only
- retry_later
- none

### 默认建议
- 任何高风险或结构性异常，优先：
  - human_review
  - manual_takeover

---

## 7. 与治理层的关系
发送结果闭环不替代治理层。

关系应为：
1. 治理层决定能否调用真实发送
2. adapter 尝试真实发送
3. 发送结果闭环记录执行结果
4. 若失败/异常，再决定：
   - 人工复核
   - 接管
   - 延后重试
   - 草稿保留

---

## 8. 与人工接管机制的关系
发送结果闭环必须给人工接管机制提供明确输入：

- customer_id
- session_id
- send_text
- channel
- error_code
- error_message
- fallback_action

这样人工才能快速续接，不丢上下文。

---

## 9. 当前阶段建议
当前阶段先做：
1. 结果结构标准化
2. 审计文件落盘骨架
3. 最小记录器骨架
4. 先支持 mock real adapter 的闭环记录

暂不建议当前阶段做：
- 自动重试策略复杂化
- 多渠道并行复杂调度
- 大规模发送状态统计平台

---

## 10. 当前结论
本设计为卧龙 Agent 从“有真实渠道 adapter 骨架”走向“真实执行面闭环”的关键一步。

