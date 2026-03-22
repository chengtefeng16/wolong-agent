<!-- ================================================================
Copyright (c) 2026 程特峰 (Tefeng Cheng)
All Rights Reserved.

Project: AgentOS / Wolong Agent System
This document and its contents are proprietary and confidential.
Unauthorized copying, modification, distribution or use of this
document, in whole or in part, is strictly prohibited.
================================================================ -->

# 卧龙 Agent 首批 WhatsApp 灰度开启条件清单（V1）

## 1. 目标
本清单用于定义：卧龙 Agent 在首批 WhatsApp 灰度接入时，什么条件满足后才允许开启。

原则：
- 小范围
- 白名单优先
- 低风险优先
- 强审计
- 强人工兜底
- 随时可回退

---

## 2. 当前阶段定位
当前不是“大规模正式上线”阶段，而是：

- 第一批小范围灰度验证阶段
- 第一批真实渠道低风险验证阶段
- 第一批运行链路观察阶段

---

## 3. 必须全部满足的开启条件

### 3.1 治理条件
以下必须全部满足：

1. delegation 治理链已稳定
2. 人工复核闸门正常
3. runtime active config 正常可读
4. save / preview / rollback / snapshot 正常
5. 白名单机制已生效
6. delivery result loop 正常
7. manual takeover flow 正常

### 3.2 渠道条件
以下必须全部满足：

1. real_channel_adapter 总开关可控
2. whatsapp 渠道单独开关可控
3. 未开启时必须默认 pending_manual
4. 开启后仍能随时切回人工

### 3.3 人工值守条件
以下必须全部满足：

1. 首批灰度期间必须有人值守
2. 出现 failed / blocked / rate_limited / pending_manual 时有人可接手
3. 接管 ticket 能够生成
4. 人工接手后能看到原始上下文

### 3.4 客户条件
首批仅允许：

1. 明确在 customer_whitelist 中
2. 明确在 session_whitelist 中
3. 非争议客户
4. 非投诉客户
5. 非高情绪波动客户

### 3.5 风险条件
首批仅允许：

1. risk_level = low
2. emotion_state in [calm, neutral]
3. business_stage in [lead, contacted, negotiating]
4. 非敏感承诺类消息
5. 非高风险合规边界消息

---

## 4. 首批建议开启范围

### 4.1 渠道范围
首批仅开：
- whatsapp

### 4.2 客户范围
首批只开：
- 2 到 5 个白名单客户
- 2 到 5 个白名单会话

### 4.3 消息范围
首批只开：
- 低风险咨询回复
- 非承诺性说明
- 非情绪冲突场景
- 非价格强承诺场景
- 非法规边界模糊场景

### 4.4 时间范围
首批建议只在人工可值守时间内开启。

---

## 5. 开启前检查项（逐项打钩）
- [ ] runtime active config 正常
- [ ] whitelist 配置正确
- [ ] whatsapp channel config 可控
- [ ] provider 配置已就绪
- [ ] audit 记录可写
- [ ] delivery result log 可写
- [ ] manual takeover ticket 可写
- [ ] fallback_action = human_review 正常
- [ ] rollback 可用
- [ ] 值守人员在线

---

## 6. 开启后观察项
灰度开启后要重点观察：

1. 是否正确命中白名单
2. 是否只放行低风险消息
3. 是否有异常返回
4. 是否能写入 delivery result log
5. 是否能生成 manual takeover ticket
6. 是否需要频繁人工接手
7. 是否出现话术不稳 / 关系紧张 / 合规边界不清

---

## 7. 立即关停条件
出现以下任一情况，应立即关停 WhatsApp 灰度：

1. 发送异常连续出现
2. 出现未预期外发
3. 出现高风险承诺性回复
4. 审计日志写入失败
5. manual takeover ticket 生成失败
6. provider 返回异常无法解释
7. 人工值守不在线
8. 客户情绪明显升级
9. 合规边界不清

---

## 8. 当前结论
首批 WhatsApp 灰度开启，不是“能发就开”，而是必须在：
- 治理稳定
- 白名单稳定
- 人工兜底稳定
- 审计稳定
- 可回退
的前提下，谨慎开启。

