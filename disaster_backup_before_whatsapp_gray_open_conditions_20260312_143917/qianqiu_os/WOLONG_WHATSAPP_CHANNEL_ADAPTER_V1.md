<!-- ================================================================
Copyright (c) 2026 程特峰 (Tefeng Cheng)
All Rights Reserved.

Project: AgentOS / Wolong Agent System
This document and its contents are proprietary and confidential.
Unauthorized copying, modification, distribution or use of this
document, in whole or in part, is strictly prohibited.
================================================================ -->

# 卧龙 Agent WhatsApp 最小真实渠道 Adapter 设计（V1）

## 1. 目标
本设计用于为卧龙 Agent 提供首个真实业务目标渠道的最小 adapter 骨架。

当前阶段不直接接真实账号，不直接接真实 API，只先定义：
- WhatsApp 输入结构
- WhatsApp 输出结构
- 与统一 real_channel_adapter 的衔接方式
- 与灰度白名单 / 审计 / 人工接管的关系

---

## 2. 当前定位
WhatsApp adapter 属于：
- 真实渠道执行面的第一个目标实现骨架
- 位于统一 real_channel_adapter 下层
- 只在 governance / delegation / whitelist 通过后才允许被调用

---

## 3. 最小输入结构
建议至少包括：
- customer_id
- session_id
- send_text
- trace_id
- business_context
- delegation_decision
- audit_context

---

## 4. 最小输出结构
统一返回：
- success
- channel = whatsapp
- delivery_status
- provider_message_id
- error_code
- error_message
- retryable
- fallback_action

---

## 5. 当前阶段行为原则
### 若未接真实 provider
默认行为应为：
- 不假装真实成功
- 返回 pending_manual 或 adapter_disabled / provider_not_configured
- fallback_action = human_review

### 若未来接真实 provider
才允许返回：
- sent
- failed
- rate_limited
- auth_invalid
- provider_unavailable
- account_blocked

---

## 6. 与灰度机制的关系
WhatsApp adapter 不能决定“能不能发”，只能在以下前提下执行：
- whatsapp 在渠道白名单内
- customer / session 在白名单内
- 风险等级允许
- 情绪状态允许
- delegation 已通过
- manual review 未触发

---

## 7. 与结果闭环的关系
WhatsApp adapter 返回结果后，应进入：
- delivery_result_loop
- audit record
- manual takeover decision

---

## 8. 当前阶段建议
当前阶段只做：
1. WhatsApp adapter 骨架
2. 配置读取
3. provider_not_configured / disabled 等保守返回
4. 接入统一 real_channel_adapter

暂不建议：
- 真接 provider token
- 真发生产消息
- 绕过白名单灰度机制

---

## 9. 当前结论
WhatsApp adapter v1 是卧龙 Agent 迈向真实业务渠道的第一块真实渠道实现骨架。

