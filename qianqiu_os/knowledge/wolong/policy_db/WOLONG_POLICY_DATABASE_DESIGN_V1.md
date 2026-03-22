<!-- ================================================================
Copyright (c) 2026 程特峰 (Tefeng Cheng)
All Rights Reserved.

Project: AgentOS / Wolong Agent System
This document and its contents are proprietary and confidential.
Unauthorized copying, modification, distribution or use of this
document, in whole or in part, is strictly prohibited.
================================================================ -->

# 卧龙 Agent 国家政策法规库 / 活数据库设计稿（V1）

## 一、模块定位
国家政策法规库不是普通资料库，也不是单纯的法规文档堆放区。
它应被定义为：

**面向跨境二手车业务的国家政策法规活数据库**

该模块服务于：
- 跨境二手车合规规则引擎
- 卧龙 Agent 客户服务管理系统
- 多 Agent 协同调用
- 对内合规判断
- 对外客户解释
- 风险预警与人工复核

其本质是：
- 法规事实层
- 规则数据层
- 更新调度层
- 输出支持层

---

## 二、设计目标
本模块必须支持以下目标：

1. 把各国与二手车进口、清关、关税、准入、限制、文件要求相关的规则沉淀为可持续维护的结构化数据库。

2. 不只回答“有没有资料”，而要能支持：
- 能否进入
- 需要满足什么条件
- 哪些风险点需要警惕
- 哪些场景必须人工复核
- 对客户应如何解释

3. 支持持续更新，而不是静态归档。

4. 能被多个 Agent 调用，而不是只供单一模块阅读。

---

## 三、区域包结构
建议先按“区域包”组织，而不是从一开始全球平铺。

### A. 中亚 / 俄语区包
建议优先包括：
- Kazakhstan
- Kyrgyzstan
- Uzbekistan
- Tajikistan
- Turkmenistan
- Russia
- Armenia

### B. 中东包
建议优先包括：
- Saudi Arabia
- United Arab Emirates

### C. 非洲包
建议优先包括：
- Ghana
- Algeria

### D. 拉美包
建议优先包括：
- Mexico

后续可继续扩展更多国家。

---

## 四、国家卡结构（Country Policy Card）
每个国家应至少维护一张结构化国家卡。

建议字段如下：

### 1. 基础信息
- country_code
- country_name_en
- country_name_zh
- region_pack
- status
  - open
  - restricted
  - high_risk
  - pending_verification

### 2. 更新信息
- last_checked_at
- next_small_update_due
- next_major_update_due
- policy_version
- confidence_level

### 3. 准入规则
- used_vehicle_import_allowed
- allowed_vehicle_types
- max_vehicle_age_years
- steering_requirement
- fuel_type_rules
- emission_rules
- certification_rules
- special_restrictions

### 4. 税费规则
- tariff_rule
- vat_rule
- additional_tax_rule
- fee_notes
- currency_notes

### 5. 单证与清关
- required_documents
- customs_clearance_requirements
- inspection_requirements
- compliance_report_requirements
- foreign_exchange_requirements

### 6. 物流与交付约束
- common_ports_or_border_points
- logistics_constraints
- transport_risk_notes

### 7. 风险与人工复核
- risk_flags
- manual_review_required_cases
- enforcement_uncertainty_notes
- operational_warnings

### 8. 输出支持层
- internal_summary_template
- customer_safe_explanation_template
- high_risk_warning_template

### 9. 来源层
- source_records
- last_source_snapshot
- source_quality_notes

---

## 五、来源分级机制
法规数据库必须记录来源层级，不能把所有来源混成同一可信度。

### A 级来源：官方来源
包括但不限于：
- 海关
- 商务/工业/交通主管部门
- 税务部门
- 官方公报
- 官方法律法规文本

特点：
- 优先级最高
- 可直接作为正式规则依据入库

### B 级来源：高可信行业来源
包括但不限于：
- 正规清关/物流服务商
- 行业协会
- 官方授权说明材料
- 长期稳定的专业合规顾问资料

特点：
- 可作为规则补充
- 若与 A 级冲突，以 A 级为准

### C 级来源：业务实操反馈
包括但不限于：
- 一线清关反馈
- 客户成交反馈
- 业务实操经验
- 临时市场信息

特点：
- 可进入待验证层
- 不应直接替代 A 级正式规则

---

## 六、更新机制
本模块必须是“活数据库”，因此更新机制必须制度化。

### 1. 三天小更新
更新周期：
- 每 3 天一次

主要处理：
- 新政策苗头
- 单国小变化
- 费用口径小修正
- 风险提示补丁
- 物流与口岸变化
- 待验证反馈补录

特点：
- 快速
- 小范围
- 增量
- 可带“待验证”标记

### 2. 七天大更新
更新周期：
- 每 7 天一次

主要处理：
- 国家卡全面复核
- 规则字段重审
- 旧条目失效检查
- 高风险国家重点复核
- 输出模板同步修正
- Agent 调用口径一致性检查

特点：
- 更稳
- 更全
- 面向正式运行口径

---

## 七、与合规规则引擎的关系
国家政策法规库是：
- 法规事实来源层
- 规则输入层

合规规则引擎是：
- 判断执行层
- 风险分级层
- 结构化输出层

关系应为：
- 法规库提供结构化国家卡
- 合规规则引擎读取国家卡
- 再结合车辆信息执行 check_policy(country, vehicle_dict)

即：
**法规库不等于规则引擎**
但：
**规则引擎必须以法规库为基础**

---

## 八、与场景话术模板库的关系
国家政策法规库提供：
- 规则事实
- 风险提示
- 合规条件
- 文件要求
- 税费口径

场景话术模板库提供：
- 对内如何提示
- 对外如何表达
- 如何本地化解释
- 如何做客户安全沟通

关系应为：
- 法规库提供“是什么”
- 话术模板库提供“怎么说”

---

## 九、多 Agent 调用方式
未来该模块不应只服务卧龙 Agent 单一前端，而应作为共享能力模块。

建议调用对象包括：
- 客服 Agent
- 报价 Agent
- 风控 Agent
- 物流 Agent
- 经营分析 Agent

建议支持的调用结果包括：
- country_policy_card
- policy_check_result
- risk_summary
- customer_safe_explanation
- internal_workbench_warning

---

## 十、建议的数据目录结构
建议未来目录结构参考如下：

policy_db/
  region_packs/
    central_asia/
    middle_east/
    africa/
    latin_america/
  country_cards/
    kazakhstan.json
    kyrgyzstan.json
    uzbekistan.json
    russia.json
    armenia.json
    saudi_arabia.json
    uae.json
    ghana.json
    algeria.json
    mexico.json
  source_snapshots/
  update_logs/
  pending_verification/
  generated_outputs/

---

## 十一、当前第一阶段建设顺序
### 第一步
先建立设计稿与字段标准。

### 第二步
先从重点区域包入手：
- 中亚 / 俄语区
- 中东
- 非洲
- 拉美

### 第三步
先从重点国家卡开始建立。

### 第四步
把三天小更新、七天大更新接入节奏层。

### 第五步
再逐步接入 Agent 调用层与客户解释输出层。

---

## 十二、当前结论
国家政策法规库必须被正式定义为：
**卧龙 Agent 的国家政策法规活数据库**

它不是附属资料夹，而是：
- 合规规则引擎的基础层
- 多 Agent 可共享调用的国家规则底座
- 面向对内判断与对外解释的核心支撑模块

