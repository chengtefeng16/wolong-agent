<!-- ================================================================
Copyright (c) 2026 程特峰 (Tefeng Cheng)
All Rights Reserved.

Project: AgentOS / Wolong Agent System
This document and its contents are proprietary and confidential.
Unauthorized copying, modification, distribution or use of this
document, in whole or in part, is strictly prohibited.
================================================================ -->

# 卧龙 Agent audit_status 字段规范（V1）

## 一、目标
为国家政策法规相关对象建立统一审计状态字段，支持：
- 国家卡
- update_logs
- extractor_logs
- 后续合规规则引擎输出前置检查

---

## 二、标准状态值
### 1. audit_pass
含义：
- 来源、时效、适用范围、输出安全性均满足基本要求
- 可用于内部判断
- 可用于受控对外表达

### 2. audit_pass_with_warning
含义：
- 总体可用
- 但存在注意项或需提示警示
- 可用于内部判断
- 对外表达时应带风险说明

### 3. audit_restricted
含义：
- 仅限内部参考
- 不得直接作为客户或交易最终结论
- 通常存在待验证项、更新时效问题、适用范围不够清晰等情况

### 4. audit_fail
含义：
- 当前不可作为业务结论使用
- 应阻断直接对外与直接决策使用

---

## 三、建议写入位置
### 国家卡
建议字段：
- audit_status
- audit_summary
- audit_last_checked_at

### update_logs / extractor_logs
建议字段：
- audit_status
- audit_summary
- human_review_needed

---

## 四、判定原则
### 可判为 audit_pass
- 有来源记录
- 来源等级合理
- 更新时间有效
- 小更新/大更新未过期
- 无关键待验证项阻断
- 有安全输出模板

### 可判为 audit_pass_with_warning
- 可用，但存在少量不确定项
- 不确定项不影响主判断
- 对外使用必须带警示

### 应判为 audit_restricted
- 存在关键 pending_verification
- 存在 enforcement_uncertainty_notes
- 适用对象/适用范围边界不够清晰
- 适合内部参考，不适合直接外发

### 应判为 audit_fail
- 无来源
- 来源严重不足
- 关键时间字段缺失
- 已明显过期
- 关键规则抽取明显不可靠

