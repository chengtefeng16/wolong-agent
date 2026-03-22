<!-- ================================================================
Copyright (c) 2026 程特峰 (Tefeng Cheng)
All Rights Reserved.

Project: AgentOS / Wolong Agent System
This document and its contents are proprietary and confidential.
Unauthorized copying, modification, distribution or use of this
document, in whole or in part, is strictly prohibited.
================================================================ -->

# RUNTIME PROMOTION GUARD DESIGN · 2026-03-14

## 一、目的
把推广 / 自推广层从“原则”补到“最小安全骨架”。

## 二、当前最小能力
1. 推广总开关
2. 灰度开关
3. 人工最终确认
4. 每日限额
5. 白名单开关
6. 回滚开关
7. 审计开关
8. 给出：
   - blocked
   - allow_gray_only
   - human_decide

## 三、当前最小原则
1. 推广不得绕过人工最终确认权
2. 默认不允许直接大规模推广
3. 允许的最高状态是 allow_gray_only
4. 必须保留白名单、回滚、审计、限额

## 四、当前定位
这一版不是完整自推广系统，而是“安全推广骨架”。
目标是先把推广层从偏弱推进到半稳起步，确保未来推广动作不会失控。
