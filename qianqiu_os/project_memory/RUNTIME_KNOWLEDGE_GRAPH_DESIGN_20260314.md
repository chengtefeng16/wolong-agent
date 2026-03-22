<!-- ================================================================
Copyright (c) 2026 程特峰 (Tefeng Cheng)
All Rights Reserved.

Project: AgentOS / Wolong Agent System
This document and its contents are proprietary and confidential.
Unauthorized copying, modification, distribution or use of this
document, in whole or in part, is strictly prohibited.
================================================================ -->

# RUNTIME KNOWLEDGE GRAPH DESIGN · 2026-03-14

## 一、目的
把知识图谱层从“概念”补到“可运行骨架”。

## 二、当前最小能力
1. 从 h5_dashboard_whatsapp.json 读取客户视图真源
2. 抽取 customer / country / channel / category / risk / intent / keyword / tag 节点
3. 建立客户与国家、渠道、标签、关键词、意图、风险之间的关系边
4. 输出到 runtime_views/knowledge_graph/customer_graph_v1.json

## 三、当前定位
这一版不是完整知识图谱系统，而是“客户关系图谱最小骨架”。
目标是先让结构化关系落盘，为后续客户画像、国家偏好、车型偏好、风控与协同提供基础。

## 四、后续增强方向
1. 接入车型节点
2. 接入口岸节点
3. 接入业务阶段节点
4. 接入经销商 / 个人身份判定依据节点
5. 接入跨客户的共现关系分析
