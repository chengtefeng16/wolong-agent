<!-- ================================================================
Copyright (c) 2026 程特峰 (Tefeng Cheng)
All Rights Reserved.

Project: AgentOS / Wolong Agent System
This document and its contents are proprietary and confidential.
Unauthorized copying, modification, distribution or use of this
document, in whole or in part, is strictly prohibited.
================================================================ -->

# DIRECTION CHECK EXECUTION DESIGN · 2026-03-14

## 一、目的
把“方向检查”从口头提醒和项目备忘，补成可落盘、可续接、可检查的最小执行骨架。

## 二、当前最小能力
1. 固定输出方向检查问题
2. 固定输出当前方向判断
3. 固定输出阶段提醒语
4. 落盘 JSON 状态文件
5. 生成 Markdown 摘要文件

## 三、当前定位
这一版不是完整战略评审系统，而是“方向检查执行骨架”。
目标是先把方向检查变成每个关键节点都可以重复调用的稳定动作。

## 四、后续增强方向
1. 接入时间逻辑层，在 23:00 自动触发方向检查
2. 接入周五 17:00 总表前检查
3. 接入对话续接备忘自动摘要
4. 接入更多业务真实性判断指标
