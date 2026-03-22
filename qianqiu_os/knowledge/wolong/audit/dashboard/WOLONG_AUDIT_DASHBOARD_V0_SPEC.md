<!-- ================================================================
Copyright (c) 2026 程特峰 (Tefeng Cheng)
All Rights Reserved.

Project: AgentOS / Wolong Agent System
This document and its contents are proprietary and confidential.
Unauthorized copying, modification, distribution or use of this
document, in whole or in part, is strictly prohibited.
================================================================ -->

# 卧龙 Agent 批量国家审计结果汇总面板 V0 说明

## 一、目标
将国家卡与审计输出聚合为统一面板，便于快速查看：
- 当前审计状态
- 来源覆盖强弱
- 更新节点
- 风险优先级
- 人工复核需求

## 二、面板字段
- country_name_en
- country_name_zh
- audit_status
- human_review_needed
- cross_validation_status
- cross_validation_score
- issues_count
- warnings_count
- source_count
- last_checked_at
- next_small_update_due
- next_major_update_due
- priority_bucket

## 三、priority_bucket 建议规则
### P0
- audit_fail

### P1
- audit_restricted
- 且 cross_validation_status = weak

### P2
- audit_restricted
- 但 cross_validation_status != weak

### P3
- audit_pass_with_warning

### P4
- audit_pass

## 四、用途
- 决定下一轮优先补源国家
- 决定下一轮优先人工复核国家
- 决定哪些国家不能直接对外输出
- 为后续 H5 / 管理台接入提供数据源

