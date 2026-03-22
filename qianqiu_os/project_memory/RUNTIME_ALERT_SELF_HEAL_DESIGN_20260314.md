<!-- ================================================================
Copyright (c) 2026 程特峰 (Tefeng Cheng)
All Rights Reserved.

Project: AgentOS / Wolong Agent System
This document and its contents are proprietary and confidential.
Unauthorized copying, modification, distribution or use of this
document, in whole or in part, is strictly prohibited.
================================================================ -->

# RUNTIME ALERT / SELF HEAL DESIGN · 2026-03-14

## 一、目的
为 AgentOS / 卧龙 Agent 增加最小预警层与最小自愈层骨架，先把“没有”补到“半稳起步”。

## 二、当前最小预警能力
1. 检查 active_config 是否存在
2. 检查 whatsapp_control 是否存在
3. 检查 auto_reply 是否被误打开
4. 检查 runtime view 是否存在
5. 检查 conversation index 是否存在
6. 检查 runtime view 与 conversation index 数量是否不一致

## 三、当前最小自愈能力
1. active_config 缺失时自动补一个最小骨架
2. whatsapp_control 缺失时自动注入默认值
3. auto_reply 被误开时强制改回 false
4. auto_dispatch 被误开时强制改回 false

## 四、默认安全基线
- ingress_mode = readonly
- auto_classify = true
- auto_tagging = true
- h5_visible = true
- auto_reply = false
- auto_dispatch = false

## 五、当前定位
这一版不是完整自愈系统，而是“预警层 + 自愈层最小骨架”。
目标是先减少明显错误、减少返工、减少误开风险，为后续补到半稳 / 稳打基础。
