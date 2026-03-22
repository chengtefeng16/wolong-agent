<!-- ================================================================
Copyright (c) 2026 程特峰 (Tefeng Cheng)
All Rights Reserved.

Project: AgentOS / Wolong Agent System
This document and its contents are proprietary and confidential.
Unauthorized copying, modification, distribution or use of this
document, in whole or in part, is strictly prohibited.
================================================================ -->

# 卧龙 Agent 真实渠道 Adapter 设计骨架（V1）

## 1. 目标
本设计用于为卧龙 Agent 的真实社交媒体接入提供统一 adapter 骨架。

当前阶段目标不是立即接通真实平台，而是先定义：
- 统一请求格式
- 统一返回格式
- 统一异常分类
- 与治理层的衔接点
- 与白名单灰度机制的衔接点
- 与人工接管机制的衔接点

---

## 2. 当前定位
本设计属于“真实渠道执行面”的骨架层。

在系统中的位置应为：
- 位于 execution 层的真实外发末端
- 接在 delegation / governance 放行之后
- 接在白名单灰度判断之后
- 接在 runtime active config / business context / audit 逻辑之后

---

## 3. 统一输入结构（建议）
真实渠道 adapter 接收的统一输入建议包括：

1. channel
   - 目标渠道
   - 例如：whatsapp / web_chat / facebook / instagram

2. customer_id
   - 目标客户唯一标识

3. session_id
   - 当前会话唯一标识

4. send_text
   - 准备发送的正文

5. business_context
   - 业务上下文对象
   - 例如：
     - business_stage
     - risk_level
     - destination_country
     - customer_type
     - intent_type
     - emotion_state

6. delegation_decision
   - 发前治理决策摘要
   - 例如：
     - allow_real_send
     - reason
     - priority_level

7. audit_context
   - 审计上下文
   - 例如：
     - operator
     - config_version
     - applied_preset
     - trace_id

---

## 4. 统一返回结构（建议）
真实渠道 adapter 返回统一结构：

1. success
   - 是否发送成功

2. channel
   - 实际发送渠道

3. delivery_status
   - 例如：
     - sent
     - failed
     - rate_limited
     - blocked
     - pending_manual

4. provider_message_id
   - 渠道侧消息 id（若有）

5. error_code
   - 渠道异常码（若有）

6. error_message
   - 异常说明（若有）

7. retryable
   - 是否允许自动或人工重试

8. fallback_action
   - 建议兜底动作
   - 例如：
     - human_review
     - manual_takeover
     - draft_only
     - retry_later

---

## 5. 统一异常分类（最小版）
建议最小分类如下：

1. send_failed
   - 普通发送失败

2. rate_limited
   - 渠道限流

3. auth_invalid
   - token / 认证异常

4. account_blocked
   - 账号异常 / 封禁

5. provider_unavailable
   - 渠道服务不可用

6. invalid_payload
   - 发送参数不合法

---

## 6. 与治理层的衔接
只有在以下条件满足时，真实渠道 adapter 才应被调用：

1. send_blocked_by_gate = false
2. send_blocked_by_delegation = false
3. allow_real_send = true
4. channel 在灰度白名单中
5. customer_id / session_id 在灰度白名单中
6. risk_level 在允许范围中
7. emotion_state 在允许范围中
8. manual_review_required = false

否则：
- 不进入真实渠道 adapter
- 改走人工复核 / 草稿 / 接管路径

---

## 7. 与白名单灰度机制的衔接
真实渠道 adapter 不负责决定“是否允许发”，它只负责在已经允许的前提下执行真实发送。

也就是说：
- 灰度策略决定“能不能调 adapter”
- adapter 负责“真正发出去”和“把结果带回来”

---

## 8. 与人工接管机制的衔接
当 adapter 返回以下情况时，应触发人工兜底：

1. success = false
2. delivery_status = failed / blocked / rate_limited
3. retryable = false
4. fallback_action = human_review / manual_takeover / draft_only

---

## 9. 当前阶段建议
当前阶段先做：
1. 统一 adapter 抽象层
2. mock real adapter 骨架
3. 返回结构标准化
4. 与灰度机制 / 审计机制接口预留

暂不建议当前阶段做：
- 多平台同时真实接入
- 无白名单大规模外发
- 无人工兜底真实自动化

---

## 10. 当前结论
本设计为卧龙 Agent 从“灰度接入准备阶段”走向“真实渠道执行面”的第一块骨架。

