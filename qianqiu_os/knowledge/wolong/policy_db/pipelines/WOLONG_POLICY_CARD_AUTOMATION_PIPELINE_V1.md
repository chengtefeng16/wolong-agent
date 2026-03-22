<!-- ================================================================
Copyright (c) 2026 程特峰 (Tefeng Cheng)
All Rights Reserved.

Project: AgentOS / Wolong Agent System
This document and its contents are proprietary and confidential.
Unauthorized copying, modification, distribution or use of this
document, in whole or in part, is strictly prohibited.
================================================================ -->

# 卧龙 Agent 国家卡自动化生成与更新流水线设计稿（V1）

## 一、定位
本流水线不是单次脚本，而是面向国家政策法规活数据库的长期自动化能力。

其目标是让系统逐步具备以下能力：
- 自动发现法规政策来源
- 自动抓取法规原文或页面快照
- 自动提炼结构化国家卡字段
- 自动写入国家卡数据库
- 自动挂三天小更新 / 七天大更新节点
- 自动保留来源记录、来源状态、待验证项
- 自动为合规规则引擎与其他 Agent 提供输入

---

## 二、总流程
建议总流程定义为：

### Step 1：自动找源（Source Discovery）
目标：
- 持续发现与目标国家二手车进口、清关、关税、税费、文件、限制相关的法规来源

优先来源方向：
- 官方公报
- 海关官网
- 税务主管部门
- 交通 / 工业 / 商务主管部门
- 官方法规数据库
- 高可信行业机构
- 物流 / 清关合规服务商
- 已有人工上传的 PDF / 文档 / 链接

输出：
- source_candidate_list

---

### Step 2：自动抓取（Source Capture）
目标：
- 把发现的来源保存为可追溯快照

支持形式：
- PDF
- HTML 页面
- 公告文本
- 法规页面截图
- 已上传文档归档

输出落点建议：
- source_snapshots/
- pending_verification/
- source_records

每条来源应记录：
- source_id
- source_url_or_file
- source_type
- source_level
- capture_time
- language
- snapshot_hash
- status

---

### Step 3：自动抽取（Field Extraction）
目标：
- 从法规原文中提炼国家卡需要的结构化字段

优先提炼字段：
- applicable_person_type
- usage_scope
- frequency_limit
- used_vehicle_import_allowed
- allowed_vehicle_types
- max_vehicle_age_years
- steering_requirement
- fuel_type_rules
- emission_rules
- certification_rules
- tariff_rule
- vat_rule
- additional_tax_rule
- required_documents
- customs_clearance_requirements
- foreign_exchange_requirements
- risk_flags
- manual_review_required_cases

抽取原则：
- 能明确提炼的直接入结构化字段
- 模糊项写入 enforcement_uncertainty_notes
- 不确定项打入 pending_verification
- 不允许把模糊推断当正式规则

---

### Step 4：自动入库（Card Writeback）
目标：
- 把抽取结果写回国家卡 JSON

写入对象：
- country_cards/<country>.json

写入规则：
- 若国家卡不存在，则生成 skeleton + structured_v1
- 若国家卡已存在，则执行增量更新
- 必须保留历史 source_records
- 必须保留 pending_tasks
- 必须保留上一次版本号和更新时间

---

### Step 5：自动挂更新节奏（Update Scheduling）
目标：
- 每次更新国家卡时，自动刷新后续小更新和大更新节点

规则：
- last_checked_at = 本次更新时间
- next_small_update_due = +3 days
- next_major_update_due = +7 days

解释：
- 三天小更新负责补充来源与小变动
- 七天大更新负责整卡复核与规则口径一致性检查

---

### Step 6：自动输出给调用层（Serving Layer）
目标：
- 国家卡生成后，不只静态存档，还要给系统其他模块用

建议输出对象：
- 合规规则引擎
- 客服 Agent
- 报价 Agent
- 风控 Agent
- 物流 Agent
- 场景话术模板库联动层

建议输出结果：
- country_policy_card
- policy_check_input
- internal_workbench_warning
- customer_safe_explanation_seed
- risk_summary

---

## 三、来源分级在流水线中的使用
### A 级来源
- 直接进入正式结构化规则层

### B 级来源
- 可进入补充层
- 与 A 级冲突时需标注并等待人工确认

### C 级来源
- 进入 pending_verification
- 可形成风险提示，但不得直接覆盖正式规则

---

## 四、待验证机制
自动化流水线必须允许“半自动正确”，不允许“自动瞎定”。

因此应建立：
- pending_verification/
- enforcement_uncertainty_notes
- manual_review_required_cases

适用场景：
- 条文模糊
- 税费拆分不清
- 方向盘要求未明确
- 商业进口与个人进口边界不清
- 不同来源冲突

---

## 五、Algeria 样板意义
Algeria 第一张国家卡应视为：
- 第一张结构化国家卡
- 第一张带正式 source_records 的样板卡
- 第一张带 last_checked_at / next_small_update_due / next_major_update_due 的样板卡
- 第一张用于反推自动化流水线字段映射的样板卡

后续自动化设计应优先围绕这张样板卡抽象字段映射与流程模板。

---

## 六、建议的自动化产物目录
policy_db/
  country_cards/
  source_snapshots/
  pending_verification/
  update_logs/
  generated_outputs/
  pipelines/

其中：
- country_cards/：正式国家卡
- source_snapshots/：来源快照
- pending_verification/：待验证条目
- update_logs/：更新日志
- generated_outputs/：给 Agent 的衍生输出
- pipelines/：自动化设计与脚本入口

---

## 七、建议的更新日志结构
每次自动运行应写入 update_logs，建议字段：

- run_id
- run_time
- target_country
- source_count
- new_sources_found
- fields_extracted
- fields_updated
- pending_verification_count
- next_small_update_due
- next_major_update_due
- human_review_needed

---

## 八、建议的最小自动化能力阶段
### Phase 1
- 手工上传来源 + 自动抽取 + 自动写卡 + 自动挂更新日期

### Phase 2
- 半自动找源 + 自动抓取 + 自动抽取 + 自动写卡

### Phase 3
- 自动找源 + 自动抓取 + 自动比对变更 + 自动更新国家卡 + 自动输出给 Agent

---

## 九、与主干关系
本流水线属于卧龙 Agent 主干中的法规事实层自动化基础设施。

关系如下：
- 国家政策法规库：规则事实层
- 自动化流水线：更新与生成层
- 合规规则引擎：判断执行层
- 场景话术模板库：表达层

四者应形成连续链路，而不是孤立存在。

---

## 十、当前结论
从本阶段开始，国家卡不应被理解为“手工整理的静态文件”，而应被理解为：

**可持续发现来源、可持续结构化、可持续更新、可持续供 Agent 调用的活数据对象。**

