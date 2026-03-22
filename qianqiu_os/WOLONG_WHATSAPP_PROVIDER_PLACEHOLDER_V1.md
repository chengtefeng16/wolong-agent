<!-- ================================================================
Copyright (c) 2026 程特峰 (Tefeng Cheng)
All Rights Reserved.

Project: AgentOS / Wolong Agent System
This document and its contents are proprietary and confidential.
Unauthorized copying, modification, distribution or use of this
document, in whole or in part, is strictly prohibited.
================================================================ -->

# 卧龙 Agent WhatsApp Provider 最小接入占位设计（V1）

## 1. 目标
本设计用于为卧龙 Agent 的 WhatsApp 渠道补齐 provider 层占位结构。

当前阶段不接真实密钥、不接真实账号、不接真实 API，只先定义：
- provider 配置字段
- provider client 骨架
- provider 原始返回值到统一结果结构的映射方法
- 与现有 whatsapp adapter 的衔接方式

---

## 2. 当前定位
当前 provider 占位层位于：
- whatsapp_channel_adapter_v1 之下
- 真正 provider SDK / HTTP 调用 之上

它的作用是：
- 给未来真实接入留稳定接口
- 不让将来一接真实 provider 就重写整个 adapter

---

## 3. 最小配置字段建议
最小字段建议包括：

- provider_name
- enabled
- api_base_url
- api_version
- phone_number_id
- business_account_id
- access_token_placeholder
- timeout_seconds

当前阶段：
- access_token_placeholder 仅允许占位
- 不写真实密钥
- 不提交真实生产参数

---

## 4. provider client 最小职责
provider client 当前阶段只负责：
1. 校验最小配置是否存在
2. 返回 provider_not_configured / provider_disabled 等占位结果
3. 统一把 provider 层结果映射成：
   - success
   - delivery_status
   - error_code
   - error_message
   - retryable
   - fallback_action

---

## 5. 映射原则
### 若 provider 未启用
返回：
- success = false
- delivery_status = pending_manual
- error_code = provider_disabled
- fallback_action = human_review

### 若 provider 未配置完成
返回：
- success = false
- delivery_status = pending_manual
- error_code = provider_not_configured
- fallback_action = human_review

### 若未来 provider 真接入成功
才允许映射为：
- sent
- failed
- rate_limited
- auth_invalid
- provider_unavailable
- account_blocked

---

## 6. 当前阶段建议
当前阶段只做：
- provider config 占位
- provider client 占位
- adapter 内部预留调用接口

暂不做：
- 真实 access token
- 真实 API 请求
- 真实生产发消息

---

## 7. 当前结论
本设计是卧龙 Agent 从“WhatsApp adapter 骨架”走向“可真接 provider 的前置占位层”的关键一步。

