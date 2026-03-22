<!-- ================================================================
Copyright (c) 2026 程特峰 (Tefeng Cheng)
All Rights Reserved.

Project: AgentOS / Wolong Agent System
This document and its contents are proprietary and confidential.
Unauthorized copying, modification, distribution or use of this
document, in whole or in part, is strictly prohibited.
================================================================ -->

# 卧龙 Agent 白名单灰度策略（最小版）

## 1. 目标
本策略用于定义卧龙 Agent 在接入真实社交媒体前后的最小灰度放行规则。

原则：
- 小范围
- 低风险
- 白名单优先
- 默认保守
- 可回滚
- 可人工接管

---

## 2. 当前灰度策略定位
当前阶段不追求“大规模真实自动外发”，只允许：

- 少量客户
- 少量渠道
- 少量低风险场景
- 强审计
- 强人工兜底

---

## 3. 白名单灰度范围

### 3.1 客户白名单
只允许：
- 明确加入白名单的客户 ID
- 明确加入白名单的测试会话

### 3.2 渠道白名单
首批仅建议：
- whatsapp
- web_chat

不建议首批直接同时放开多渠道。

### 3.3 场景白名单
首批仅建议：
- 低风险咨询类回复
- 非承诺性说明
- 非高情绪冲突场景
- 非敏感合规边界场景

### 3.4 动作白名单
首批仅建议：
- customer_send
- 且仅限低风险外发文本

---

## 4. 允许条件
以下条件需同时满足：

1. customer_id 在白名单中
2. channel 在渠道白名单中
3. action 在动作白名单中
4. risk_level 为 low
5. business_stage 在允许阶段中
6. 无人工复核要求
7. 无高风险合规边界
8. 审计日志开启
9. 可随时回滚
10. 可人工接管

---

## 5. 强制降级条件
出现以下任一情况，必须降级为人工：

1. risk_level != low
2. customer emotion unstable
3. compliance boundary unclear
4. channel send returns abnormal
5. customer not in whitelist
6. business stage not allowed
7. manual review required
8. delegation not passed

---

## 6. 当前建议首批允许阶段
建议仅允许：
- lead
- contacted
- negotiating

暂不建议首批自动放开：
- closing
- after_sales
- disputed / complaint-like scenarios

---

## 7. 当前建议首批允许情绪状态
建议仅允许：
- calm
- neutral

若出现：
- angry
- frustrated
- anxious
- unstable

建议强制降级为人工或协同辅助。

---

## 8. 人工兜底动作
若降级，默认进入：
- draft only
- human review
- manual takeover

---

## 9. 当前结论
本灰度策略为最小版 v1，作用是让卧龙 Agent 从“具备真实社媒准入可能”进一步走向“具备受控灰度执行框架”。

