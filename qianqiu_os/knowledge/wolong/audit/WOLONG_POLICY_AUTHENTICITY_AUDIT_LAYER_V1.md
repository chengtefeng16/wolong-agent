<!-- ================================================================
Copyright (c) 2026 程特峰 (Tefeng Cheng)
All Rights Reserved.

Project: AgentOS / Wolong Agent System
This document and its contents are proprietary and confidential.
Unauthorized copying, modification, distribution or use of this
document, in whole or in part, is strictly prohibited.
================================================================ -->

# 卧龙 Agent 国家政策法规真实性审计层设计稿（V1）

## 一、定位
国家政策法规真实性审计层，是卧龙 Agent 审计与治理体系中的专门子层。

它不只审：
- 代码是否运行
- 输出是否生成
- 字段是否存在

它更要审：
- 国家政策法规来源是否真实
- 结构化抽取是否正确
- 规则是否适用于当前场景
- 政策是否已经过期
- 当前输出是否可以直接用于客户沟通或交易判断

---

## 二、为什么必须独立成层
国家政策法规属于高损失级规则信息。

若出现以下错误，将直接造成真实业务风险：
- 把旧政策当成现行政策
- 把个人进口规则误用于商业进口
- 把适用国家/车型/用途理解错误
- 把未明确条款误写成确定规则
- 把高风险待验证信息当成正式结论发给客户

因此，国家政策法规真实性审计不能只作为普通日志检查的一部分，必须独立成审计子层。

---

## 三、审计目标
本层的目标是确保：

1. 法规来源真实可追溯  
2. 结构化字段与原始来源一致  
3. 规则适用范围未被误判  
4. 更新时间和更新节点有效  
5. 未通过审计的内容不得直接作为最终业务结论对外使用  

---

## 四、审计对象
本审计层覆盖以下对象：

### 1. 国家政策法规库
审计内容：
- source_records
- source_level
- last_source_snapshot
- confidence_level
- last_checked_at
- next_small_update_due
- next_major_update_due

### 2. 自动化流水线
审计内容：
- 找源是否来自合规渠道
- 抓取是否保留快照
- 抽取是否存在越权推断
- 入库是否覆盖了旧数据且缺乏版本痕迹
- pending_verification 是否被正确保留

### 3. 合规规则引擎
审计内容：
- 判断是否基于最新国家卡
- 是否存在把 pending_verification 字段当 confirmed 规则使用
- 是否存在不适用场景误判

### 4. 场景话术模板库 / 对外输出层
审计内容：
- 是否把待验证规则直接发给客户
- 是否把内部判断标签直接外露
- 是否在高风险场景缺失人工复核提示

---

## 五、核心审计维度

### A. 来源真实性审计
检查项：
- 是否有 source_records
- 是否有 source_id
- 是否标明 source_level
- 是否保留来源标题/类型/语言/状态
- 是否能回溯到原始文件或页面快照

风险信号：
- 无来源
- 来源等级不明
- 来源冲突未标注
- 只有 C 级来源却被当正式规则使用

---

### B. 抽取正确性审计
检查项：
- 原文句段与结构化字段是否一一对应
- 是否把模糊语句误写为确定规则
- 是否把未出现的字段擅自补全
- 是否把解释性资料误当法规正文

风险信号：
- 字段值与来源原文不一致
- 抽取结果中出现强推断
- 未明确条款被写成 confirmed

---

### C. 适用范围审计
检查项：
- 适用于个人还是经销商
- 适用于进口还是出口
- 适用于哪类车辆
- 是否有车龄/排量/功率/排放/方向盘限制
- 是否存在例外条款

风险信号：
- 适用对象混淆
- 用途范围混淆
- 车辆类型混淆
- 把例外条款当普遍规则

---

### D. 时效性审计
检查项：
- last_checked_at 是否存在
- next_small_update_due 是否存在
- next_major_update_due 是否存在
- 当前日期是否超过更新节点
- source_records 是否存在过期风险

风险信号：
- 国家卡已超期未复核
- 来源时间过旧
- 小更新/大更新已过期仍继续输出

---

### E. 输出安全性审计
检查项：
- 当前规则是否允许直接对外表达
- 是否存在 human_review_needed
- 是否存在 manual_review_required_cases
- customer_safe_explanation_template 是否安全
- high_risk_warning_template 是否齐备

风险信号：
- 待验证规则直接对外发送
- 高风险规则未标人工复核
- 内部判断直接暴露给客户

---

## 六、建议的审计结果等级
建议将审计结果分为：

- audit_pass
- audit_pass_with_warning
- audit_restricted
- audit_fail

### 含义
- audit_pass：可用于内部与受控对外输出
- audit_pass_with_warning：可用，但必须带警示信息
- audit_restricted：仅限内部参考，不可直接外发
- audit_fail：禁止作为业务结论使用

---

## 七、建议的强制审计字段
凡国家卡进入业务判断或对外表达前，至少检查以下字段：

- source_records
- confidence_level
- last_checked_at
- next_small_update_due
- next_major_update_due
- risk_and_review.manual_review_required_cases
- risk_and_review.enforcement_uncertainty_notes
- output_support.customer_safe_explanation_template

若关键字段缺失，则不得通过真实性审计。

---

## 八、与现有主干模块的关系
### 1. 国家政策法规库
提供法规事实层

### 2. 自动化流水线
提供来源发现、抓取、抽取、入库、更新时间

### 3. 合规规则引擎
提供规则判断层

### 4. 场景话术模板库
提供表达层

### 5. 政策法规真实性审计层
对以上四层形成反向审计与风险制衡

关系总结：
- 法规库负责“是什么”
- 流水线负责“怎么更新”
- 引擎负责“怎么判断”
- 话术层负责“怎么表达”
- 审计层负责“能不能信、能不能直接用”

---

## 九、建议的阻断机制
以下情况应默认阻断“直接对客户输出”：

1. 仅有 C 级来源  
2. last_checked_at 缺失  
3. next_small_update_due / next_major_update_due 已过期  
4. 存在 enforcement_uncertainty_notes 且未人工复核  
5. 适用范围疑似混淆（个人/商业、进口/出口、车型/用途等）  
6. 关键税费、方向盘、排量/年份限制未明确  

---

## 十、建议的后续落地方向
1. 为国家卡增加 audit_status 字段  
2. 为 update_logs 增加 audit_summary 字段  
3. 建立第一版真实性审计脚本入口  
4. 对高风险国家默认开启人工复核闸门  
5. 将“真实性审计通过”作为法规输出层的前置条件  

---

## 十一、当前结论
国家政策法规相关能力，必须在原有审计/治理框架下，独立增加：

**国家政策法规真实性审计层**

它属于卧龙 Agent 的高风险规则保障层，必须与法规库、自动化流水线、合规规则引擎、场景话术模板库形成相互支持、相互监督、相互制衡的闭环。

