<!-- ================================================================
Copyright (c) 2026 程特峰 (Tefeng Cheng)
All Rights Reserved.

Project: AgentOS / Wolong Agent System
This document and its contents are proprietary and confidential.
Unauthorized copying, modification, distribution or use of this
document, in whole or in part, is strictly prohibited.
================================================================ -->

# 卧龙 Agent 人工接管动作定义（V1）

## 1. 目标
本设计用于把卧龙 Agent 在真实社交媒体执行面中的“人工接管”动作正式化。

目标不是只返回：
- human_review
- manual_takeover

而是明确：
1. 什么时候进入人工接管
2. 进入后保存什么
3. 人工从哪里接手
4. 接手后状态如何变化
5. 如何回看与审计

---

## 2. 触发人工接管的典型条件
出现以下情况之一时，应进入人工接管：

1. fallback_action = human_review
2. fallback_action = manual_takeover
3. send_blocked_by_gate = true
4. send_blocked_by_delegation = true
5. delivery_status in:
   - failed
   - blocked
   - rate_limited
   - pending_manual
6. emotion_state 不在允许范围
7. risk_level 不在允许范围
8. compliance boundary unclear
9. real adapter returned non-retryable structural error

---

## 3. 人工接管最小动作链

### 3.1 生成 takeover ticket
至少保存：
- trace_id
- customer_id
- session_id
- channel
- send_text
- business_context
- delegation_decision
- delivery_result
- fallback_action
- created_at

### 3.2 保存草稿/接管上下文
必须保存：
- 原始拟发送文本
- 当前业务上下文
- 当前风险等级
- 当前情绪状态
- 本次未发送/发送异常原因
- 建议人工下一步动作

### 3.3 进入待人工状态
状态建议统一为：
- waiting_human_takeover

### 3.4 人工处理结果回写
人工处理后建议记录：
- human_action
- human_operator
- handled_at
- handled_result
- final_resolution

---

## 4. 建议的人工作业动作类型
可选值建议包括：

- approve_and_send
- rewrite_and_send
- hold_and_wait
- reject_send
- contact_manually
- escalate_to_supervisor

---

## 5. 与草稿机制的关系
若进入人工接管，不应直接丢弃原始拟发送内容。

应保存：
- original_send_text
- suggested_next_step
- context_snapshot

这样人工续接时不会丢上下文。

---

## 6. 与审计机制的关系
人工接管必须可审计。

至少应记录：
- 谁接管了
- 为什么接管
- 接管前状态
- 接管后动作
- 最终结果

---

## 7. 当前阶段建议
当前阶段先做：
1. 人工接管 ticket 结构
2. 最小保存器骨架
3. 最小状态字段
4. 最小审计回写结构

暂不建议当前阶段做：
- 复杂工单系统
- 多人协同处理流
- 复杂审批编排

---

## 8. 当前结论
本设计是卧龙 Agent 从“能识别需要人工接管”走向“真正能把问题交给人工接住”的关键一步。

