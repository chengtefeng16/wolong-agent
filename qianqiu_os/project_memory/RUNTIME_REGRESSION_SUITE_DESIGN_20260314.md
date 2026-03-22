<!-- ================================================================
Copyright (c) 2026 程特峰 (Tefeng Cheng)
All Rights Reserved.

Project: AgentOS / Wolong Agent System
This document and its contents are proprietary and confidential.
Unauthorized copying, modification, distribution or use of this
document, in whole or in part, is strictly prohibited.
================================================================ -->

# RUNTIME REGRESSION SUITE DESIGN · 2026-03-14

## 一、目的
把自动化回归测试层从“口头检查”补到“最小可重复回归集”。

## 二、当前最小覆盖
1. active_config 是否存在
2. whatsapp_control 是否存在
3. readonly 安全基线是否保持
4. preview 模块是否存在
5. alert guard 是否健康
6. self heal 是否可运行
7. reflection check 是否可运行
8. human loop 是否保留人工最终确认权
9. knowledge graph 是否非空

## 三、产物
- runtime_governance/regression/runtime_regression_result_v1.json

## 四、当前定位
这一版不是完整 CI/CD 测试体系，而是最小回归测试骨架。
目标是先让关键主干具备“改完能回归验证”的基础。
