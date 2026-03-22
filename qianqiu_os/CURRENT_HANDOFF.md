<!-- ================================================================
Copyright (c) 2026 程特峰 (Tefeng Cheng)
All Rights Reserved.

Project: AgentOS / Wolong Agent System
This document and its contents are proprietary and confidential.
Unauthorized copying, modification, distribution or use of this
document, in whole or in part, is strictly prohibited.
================================================================ -->

# CURRENT_HANDOFF.md

## 当前阶段
卧龙 Agent 最小闭环第一版，已经成功接回 AgentOS 主链，并且人工复核链已挂齐。

---

## 当前已完成
1. 已新增并接线以下文件：
   - `qianqiu_os/agents/wolong_agent.py`
   - `qianqiu_os/data/wolong_policy_rules.py`
   - `qianqiu_os/tools/wolong_policy_tool.py`
   - `qianqiu_os/managers/wolong_manager.py`

2. 已改好以下注册文件：
   - `qianqiu_os/registry/agent_registry.py`
   - `qianqiu_os/registry/tool_registry.py`

3. 已整页替换并改好：
   - `qianqiu_os/app.py`

4. 当前主程序已成功跑通：
   - `python -m py_compile qianqiu_os/app.py` 通过
   - `python -m qianqiu_os.app` 跑通

---

## 当前跑通后的关键结果
当前已经确认：

- `wolong_result.wolong_linked = True`
- `wolong_result.policy_check_executed = True`
- `wolong_result.customer_reply_result.reply_ready = True`
- `wolong_result.manual_review_result.manual_review_required = True`
- `platform_governance.manual_review_required = True`
- `formatted_output.needs_human_handoff = True`

这说明：
卧龙 Agent 第一版最小闭环已经从“能跑”升级到“人工复核链已挂齐”。

---

## 当前仍然存在但不阻断主链的问题
1. `formatted_output.response_text` 现在仍然偏底层调试口吻。
2. 还没有优先采用卧龙自己的客户回复草稿作为主输出文本。
3. 历史指标里还残留旧错误：
   - `name 'policy_health' is not defined`
   这是历史残留，不代表本轮主链没跑通。

---

## 下一步唯一优先动作
下一步不要扩大战线，不碰 H5，不碰真实 WhatsApp，不碰 CRM。

下一步只做这一件事：

**把输出层收口，让 `formatted_output.response_text` 优先使用卧龙生成的 `reply_text`。**

目标是让系统输出更像真实客户沟通，而不是底层调试口吻。

---

## 当前推荐验证命令
后续默认用这两条短验证：

```bash
python -m py_compile qianqiu_os/app.py
python -m qianqiu_os.app

---

## 2026-03-14 最新强制规则提醒
1. 执行力优先，禁止找理由和借口。
2. 用户要求“马上执行”的事项，必须立刻转成终端命令、文件落地、文档交付。
3. 已证伪路径禁止重复建议。
4. 每周五 17:00（Asia/Shanghai）两份总表属于固定主线交付，不得漏交。
5. 先整理 markdown / checkpoint / handoff / memory，再继续 WhatsApp 主线。

## 十一、时间逻辑层（2026-03-14 追加）
1. 当前长期协作规则不再只有三层，而是正式升级为四层：
   - 对话宪法层
   - 项目 markdown / 备忘层
   - check / 检查层
   - 时间逻辑层
2. 时间逻辑层的目标是：在规定时间做规定的事，把静态规则真正变成可执行工作系统。

### A. 每日 23:00（Asia/Shanghai）固定动作
1. 回读当天新增的 constitution / checkpoint / handoff / markdown 更新
2. 总结当天新增的原子规则、经验、踩坑结论、已证伪路径
3. 反思当天哪里做得好、哪里做得不好
4. 把新增的高价值框架性要求写入：
   - 对话宪法层
   - 项目 markdown / 备忘层
   - check / 续接机制层
5. 生成次日工作计划
6. 形成夜间收口摘要，确保第二天一早可快速进入状态

### B. 每日开工时固定动作
1. 优先查看前一晚生成的夜间收口摘要与次日工作计划
2. 再查看：
   - PROJECT_CHECKPOINT.md
   - CURRENT_HANDOFF.md
   - PROJECT_CONSTITUTION_MASTER_20260314.md
3. 先校准主线与优先级，再开始当天工作，不允许直接扎进局部问题

### C. 每周五 17:00（Asia/Shanghai）固定动作
1. 正式交付两份文档：
   - AgentOS 当前主干总表
   - 卧龙Agent 当前主干总表
2. 必须输出 Word + PDF
3. 内容必须完整覆盖全主干模块，并包含：
   - 本周完成
   - 较上周新增
   - 当前欠缺
   - 下周计划
   - 上周计划完成情况回看

### D. 对话卡顿 / 换新窗口时固定动作
1. 必须主动生成承上启下续接备忘
2. 续接备忘至少包含：
   - 当前进展到哪里
   - 当前项目写到什么程度
   - 下一步要干什么
   - 当前最高优先级
   - 必须继续遵守的规则
   - 已证伪路径 / 已踩过的坑
3. 目标是让新窗口一打开就能马上进入状态，不让用户重新解释

### E. 时间逻辑层的执行原则
1. 没有时间逻辑的规则，只是静态规则；只有把规则与时间节点绑定，才是可执行系统
2. 到点不做，视为执行缺失
3. 时间节点、规则层、项目层、check 层必须联动，不允许彼此脱节

## 十二、2026-03-14 当日主干补强结果（H5 / 预警 / 自愈 / Check）
1. 已完成 H5 配置保存链补强：
   - h5_delegation_config_service_v2.py 已正式把 whatsapp_control 纳入保存主链
2. 已完成 H5 配置预览链补强：
   - h5_delegation_active_config_preview_v1.py 已可稳定读取并预览 whatsapp_control
3. 已完成真实写入 / 读回验证：
   - 已实测把 ingress_mode 改为 manual 后再读回
   - 已实测恢复为 readonly 安全基线
4. 已完成 H5 前端真源读取补强：
   - App.jsx 已读取 /runtime/views/h5_dashboard_whatsapp.json
   - App.jsx 已读取 /runtime/views/whatsapp_control_snapshot.json
   - H5 页面已显示运行时真源状态
5. 已完成预警层最小骨架：
   - runtime_alert_guard_v1.py 已可检查 active_config / whatsapp_control / runtime view / conversation index
6. 已完成自愈层最小骨架：
   - runtime_self_heal_guard_v1.py 已可自动注入默认 whatsapp_control，并强制关闭 auto_reply / auto_dispatch
7. 已完成反思 / check 层最小骨架：
   - runtime_reflection_check_v1.py 已可生成 reflection_notes / next_actions / tomorrow_plan_seed
   - CHECK_RUNTIME_STATUS_20260314.json 已成功落盘
8. 当前阶段判断：
   - H5 真源展示链：已由偏弱推进到半稳接近稳
   - 预警层：已由空白推进到半稳起步
   - 自愈层：已由空白推进到半稳起步
   - 反思 / check 层：已由概念推进到半稳起步
9. 当前安全基线仍保持：
   - ingress_mode = readonly
   - auto_reply = false
   - auto_dispatch = false

## 十三、方向检查与战略提醒（2026-03-14 追加）
1. 我们做的不是单纯“会聊天的工具”，而是面向跨境汽车贸易的规则、成本、风控、执行一体化系统。
2. 卧龙Agent 是第一个垂直样板，AgentOS 是基础底座；战略纪律必须是：
   - 卧龙先打穿
   - 底座后放大
3. 以后要经常性检查方向，反复确认：
   - 是否仍然服务真实跨境汽车贸易场景
   - 是否仍然围绕法规、成本、风控、执行推进
   - 是否开始只长底座、不长业务价值
4. 不仅用户提醒助手要学习，助手也要反过来提醒用户一起检查方向、反思方向、确认没有跑偏。
5. 每次阶段性 check 必须增加“方向检查”这一项，不能只检查代码和功能。

## 宪法增补｜关于“未完成功能不得误报完成”的执行铁律（2026-03-14）

1. 用户明确指定的“第X刀”目标，必须逐项对照验收；未全部满足前，严禁表述为“已完成”“已达成”“已经做出来了”。

2. 以后汇报进度时，必须明确区分三种状态：
   - 已完成
   - 部分完成
   - 尚未完成
   不得将“部分完成”混同为“已完成”。

3. 当用户要求的是组合目标时（例如：居中弹窗提醒 + 一键跳转跟进），必须两项都真正落地后，才可宣称该刀完成；只做出提醒条、提醒统计、局部提醒逻辑，不得擅自等同为“弹窗提醒已完成”。

4. 每一刀结束前，必须按“用户原始要求”做逐项验收，不允许助手自行降级理解、替换目标或提前宣布收口。

5. 一旦发现口径失真、误报完成、推进快于验收，必须立刻回滚口径，明确说明：
   - 已完成什么
   - 还差什么
   - 为什么当前不能宣称完成

6. 该类错误视为执行纪律错误，不是普通措辞问题。后续协作中必须优先保证验收真实性，高于表面推进速度。

7. 学习基因固化：
   - 不准把“提醒中心/提醒条/统计卡”误报成“居中弹窗提醒”
   - 不准把“可跳转逻辑未落地”误报成“一键跳转跟进已实现”
   - 不准在未逐项验收前，自行宣布某刀完成

8. 后续所有“第X刀”交付，默认采用以下收口格式：
   - 本刀目标
   - 已完成项
   - 未完成项
   - 当前是否可宣称完成：是 / 否

9. 若再次出现同类错误，必须立刻停止继续扩功能，先纠正验收与口径，再继续开发。
## 当前新增硬要求｜23:00 三层文件固定交付（2026-03-14）

从本节点起，每天 23:00（Asia/Shanghai）必须固定整理并交付以下三份文件：

1. 对话宪法层  
   `qianqiu_os/project_memory/PROJECT_CONSTITUTION_MASTER_20260314.md`

2. 项目备忘 / 交接层  
   `qianqiu_os/CURRENT_HANDOFF.md`

3. check 层记录文件  
   `qianqiu_os/project_memory/CHECK_LAYER_NIGHTLY_DELIVERY_RULE_20260314.md`

本要求的原因：
- 之前已经明确约定夜间收口要落到文件
- 但执行中仍出现“口头记得，实际没发”的问题
- 说明时间逻辑没有和执行层真正绑死

从现在开始，23:00 固定交付视为日终收口的一部分，优先于普通 H5 样式微调。未完成三层文件交付，不得视为当日收口完成。

今晚以及后续每晚执行时，必须至少覆盖：
- 当天新增规则 / 宪法结论
- 当天主线推进状态
- 当天 check / 反思 / 错误与纠正
- 次日最优先动作

当前与本要求直接相关的反思结论：
- 之前错误地把“已约定每日执行”当成“会自然执行”
- 实际上，没有固定文件、固定顺序、固定验证，就会失真
- 后续必须把时间逻辑变成显式动作，而不是口头记忆

## 当前执行切换｜先做稳可推进主干，再回打 WhatsApp 参数链（2026-03-14）

当前判断：
- WhatsApp 真实接入入口仍未顺利打开
- 继续死盯入口会造成空耗
- 因此本阶段执行切换为：先做稳当前可推进主干，再回头继续采集 WhatsApp 真实接入参数链

当前优先补稳项：
1. 输入层
2. 工具执行层
3. 执行层
4. 输出层
5. 提醒后的动作链
6. 卧龙 Agent 未稳部分

执行原则：
- 总体目标不变：仍然是卧龙先打穿，真实 WhatsApp 接入闭环最终必须完成
- 当前路径调整：先把可做稳的系统主干全部补稳，避免外部入口卡点拖住整体进度
- H5 当前页面保持稳态，不做大幅折腾，只做必要小补丁

后续衔接：
- 等用户继续尝试采集 WhatsApp 真实参数链
- 一旦入口恢复，再立刻回到真实接入闭环主线
