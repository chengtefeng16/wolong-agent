<!-- ================================================================
Copyright (c) 2026 程特峰 (Tefeng Cheng)
All Rights Reserved.

Project: AgentOS / Wolong Agent System
This document and its contents are proprietary and confidential.
Unauthorized copying, modification, distribution or use of this
document, in whole or in part, is strictly prohibited.
================================================================ -->

# CHECK 层执行灵活性规则（2026-03-14）

## 本次检查结论
当前错误风险不在于“方向变了”，而在于：
- 容易被外部入口卡点拖住
- 容易围绕单一问题持续纠缠
- 没有及时把阶段性可推进主干先做稳

## 本次纠正原则
当 WhatsApp 参数链暂时无法顺利采集时，检查层应明确给出：
1. 当前哪些主干已稳
2. 当前哪些主干未稳
3. 哪些未稳项可以立即推进
4. 是否已经切换到“先做稳可推进部分”的执行模式

## 本次固定结论
当前应优先补稳：
- 输入层
- 工具执行层
- 执行层
- 输出层
- 提醒后的动作链
- 卧龙 Agent 未稳部分

## 学习与反思
1. 总目标不变，不代表执行路径不能灵活调整
2. 外部入口卡住时，先做稳内部主干，是正确执行，不是跑偏
3. 以后必须避免“卡点空耗”，并把“先稳主干，再回打入口”的思路固定到检查层
