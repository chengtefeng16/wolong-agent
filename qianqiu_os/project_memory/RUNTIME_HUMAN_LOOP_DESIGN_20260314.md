<!-- ================================================================
Copyright (c) 2026 程特峰 (Tefeng Cheng)
All Rights Reserved.

Project: AgentOS / Wolong Agent System
This document and its contents are proprietary and confidential.
Unauthorized copying, modification, distribution or use of this
document, in whole or in part, is strictly prohibited.
================================================================ -->

# RUNTIME HUMAN LOOP DESIGN · 2026-03-14

## 一、目的
把人机协同层从“原则”补到“可运行骨架”。

## 二、当前最小能力
1. 读取 active_config 中的 whatsapp_control / delegation_policy
2. 判断 requested_action / risk_level / business_stage / source
3. 给出：
   - blocked
   - allow_readonly
   - human_decide
4. 明确保留 human_final_authority = true
5. 把判断结果落盘到 runtime_governance/human_loop/human_loop_decision_v1.json

## 三、当前最小原则
1. channel off 时直接 blocked
2. readonly 时只允许只读观察
3. manual 时进入人工决策
4. medium / high / unknown 风险等级默认进入人工确认
5. negotiating / quoted / deal_closing 阶段默认进入人工确认
6. 自动回复 / 自动外发不得绕过人工最终确认权

## 四、当前定位
这一版不是完整的人机协同闭环系统，而是“人类最终确认权”最小执行骨架。
目标是先把原则落成可运行判断。
