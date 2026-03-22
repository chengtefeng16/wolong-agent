<!-- ================================================================
Copyright (c) 2026 程特峰 (Tefeng Cheng)
All Rights Reserved.

Project: AgentOS / Wolong Agent System
This document and its contents are proprietary and confidential.
Unauthorized copying, modification, distribution or use of this
document, in whole or in part, is strictly prohibited.
================================================================ -->

# RUNTIME REFLECTION / CHECK DESIGN · 2026-03-14

## 一、目的
把“检查—反思—学习—下一步动作”从纯口头规则，补成最小可运行骨架。

## 二、当前最小能力
1. 调用 RuntimeAlertGuardV1 做运行态预警检查
2. 调用 RuntimeSelfHealGuardV1 做自愈建议检查（默认不自动应用）
3. 生成 reflection_notes
4. 生成 next_actions
5. 生成 tomorrow_plan_seed
6. 把结果落盘到 project_memory/CHECK_RUNTIME_STATUS_20260314.json

## 三、当前定位
这一版不是完整 nightly check 系统，而是“运行态检查 + 反思 + 下一步动作”的最小联动骨架。
目标是先把 check 层从概念推进到半稳起步。

## 四、后续可继续增强
1. 接入更多运行态指标
2. 接入 H5 真源一致性检查
3. 接入 nightly 23:00 自动收口逻辑
4. 接入更完整的次日计划生成逻辑
