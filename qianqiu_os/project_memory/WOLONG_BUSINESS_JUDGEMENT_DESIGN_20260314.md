<!-- ================================================================
Copyright (c) 2026 程特峰 (Tefeng Cheng)
All Rights Reserved.

Project: AgentOS / Wolong Agent System
This document and its contents are proprietary and confidential.
Unauthorized copying, modification, distribution or use of this
document, in whole or in part, is strictly prohibited.
================================================================ -->

# WOLONG BUSINESS JUDGEMENT DESIGN · 2026-03-14

## 一、目的
把卧龙 Agent 从“只展示客户列表和基础标签”，推进到“能输出更像真实业务助手的判断结果”。

## 二、当前最小能力
1. 基于 recent_focus 对客户做 customer_type 判断
2. 做 business_stage 判断
3. 做 risk_level 判断
4. 做 intent_type 判断
5. 给出 next_best_action
6. 给出 follow_up_questions
7. 给出 handoff_recommended
8. 给出 reason_keywords
9. 落盘 JSON 与 Markdown 摘要

## 三、当前定位
这一版不是完整业务大脑，而是“卧龙业务判断力增强第一刀”。
目标是先让系统能输出更贴近真实跨境汽车贸易业务推进的判断结果。

## 四、后续增强方向
1. 接入国家/口岸/物流规则
2. 接入报价结构建议
3. 接入客户历史行为记忆
4. 接入车型偏好与采购数量偏好
5. 接入更精细的人工接管建议
