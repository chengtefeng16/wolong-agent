<!-- ================================================================
Copyright (c) 2026 程特峰 (Tefeng Cheng)
All Rights Reserved.

Project: AgentOS / Wolong Agent System
This document and its contents are proprietary and confidential.
Unauthorized copying, modification, distribution or use of this
document, in whole or in part, is strictly prohibited.
================================================================ -->

# 卧龙 Agent 字段抽取映射模板（V0）

## 一、目标
本模板用于把原始法规来源中的文本内容，映射到国家卡的结构化字段中。

来源类型包括：
- PDF 法规原文
- 官方网页
- 官方 FAQ
- 官方服务说明页
- 高可信行业资料
- 待验证实操信息

本模板用于指导：
- 自动抽取
- 半自动抽取
- 人工复核
- 后续脚本化映射

---

## 二、总原则
1. 能明确提炼的字段，直接写入国家卡。
2. 不能明确提炼的字段，不允许硬猜，必须进入：
   - pending_verification
   - enforcement_uncertainty_notes
   - manual_review_required_cases
3. 不允许把模糊推断当正式规则。
4. 若来源之间冲突，优先级遵循来源分级：
   - A > B > C

---

## 三、字段映射总表

### 1. 适用对象与范围
#### 原始表达常见形式
- resident individuals only
- for personal use
- importer must be a resident
- non-commercial use
- dealer import not covered

#### 映射字段
- eligibility_scope.applicable_person_type
- eligibility_scope.usage_scope
- access_rules.special_restrictions
- risk_and_review.operational_warnings

#### 处理规则
- 明确写“居民个人”的，写入 resident_individual_only
- 明确写“个人使用”的，写入 personal_use_only
- 明确排除商业进口的，写入 dealer_not_covered 或 operational_warnings

---

### 2. 频次限制
#### 原始表达常见形式
- once every 3 years
- only one import in a given period
- cannot repeat within X years

#### 映射字段
- eligibility_scope.frequency_limit
- risk_and_review.risk_flags

#### 处理规则
- 有明确周期时直接写入 frequency_limit
- 同时加入风险提醒，避免业务误读

---

### 3. 是否允许进口二手车
#### 原始表达常见形式
- used vehicle import allowed
- importation prohibited
- restricted import allowed under conditions

#### 映射字段
- access_rules.used_vehicle_import_allowed
- status

#### 处理规则
- 明确允许：true
- 明确禁止：false
- 有条件允许：true + status = restricted

---

### 4. 允许车辆类型
#### 原始表达常见形式
- passenger vehicles
- light commercial vehicles
- vans
- pickup under X tons
- only hybrid/electric/petrol categories

#### 映射字段
- access_rules.allowed_vehicle_types
- access_rules.fuel_type_rules

#### 处理规则
- 车辆类型分开写入
- 燃料限制单独写 fuel_type_rules
- 吨位限制可写入 allowed_vehicle_types 的说明值或 special_restrictions

---

### 5. 车龄限制
#### 原始表达常见形式
- vehicle age shall not exceed 3 years
- must be less than X years old

#### 映射字段
- access_rules.max_vehicle_age_years
- risk_and_review.risk_flags

#### 处理规则
- 有明确数字时直接写整数
- 并加入风险提醒，如 age_limit_3_years

---

### 6. 方向盘要求
#### 原始表达常见形式
- left-hand drive only
- right-hand drive prohibited
- steering side requirement

#### 映射字段
- access_rules.steering_requirement
- risk_and_review.enforcement_uncertainty_notes

#### 处理规则
- 明确时直接写入
- 未明确时不得猜测，写 pending_verification

---

### 7. 排放 / 环保 / 安全要求
#### 原始表达常见形式
- must meet environmental requirements
- compliance with safety standards required
- emissions compliance required

#### 映射字段
- access_rules.emission_rules
- access_rules.certification_rules
- customs_and_documents.compliance_report_requirements
- risk_and_review.manual_review_required_cases

#### 处理规则
- 环保和安全要求可分别写入 emission_rules / certification_rules
- 若要求第三方合规报告，写入 compliance_report_requirements

---

### 8. 税费规则
#### 原始表达常见形式
- duties and taxes payable
- customs duty
- VAT applies
- additional levy

#### 映射字段
- tax_rules.tariff_rule
- tax_rules.vat_rule
- tax_rules.additional_tax_rule
- tax_rules.fee_notes

#### 处理规则
- 若法规只写“应缴税费”但未拆项，先写 tariff_rule 或 fee_notes
- 未拆清 VAT / additional tax 时，写 pending_verification_in_source

---

### 9. 外汇要求
#### 原始表达常见形式
- own foreign currency
- payment from personal foreign exchange
- foreign currency transfer required

#### 映射字段
- tax_rules.currency_notes
- customs_and_documents.foreign_exchange_requirements
- risk_and_review.risk_flags

#### 处理规则
- 明确外汇要求时，写入 foreign_exchange_requirements
- 同时加入 currency_notes 方便对内对外解释

---

### 10. 单证要求
#### 原始表达常见形式
- identity document
- residence certificate
- registration certificate
- invoice / sale contract
- inspection report
- conformity report

#### 映射字段
- customs_and_documents.required_documents
- customs_and_documents.inspection_requirements
- customs_and_documents.compliance_report_requirements

#### 处理规则
- 身份、居住、登记、发票、合同等写入 required_documents
- 车况检查写 inspection_requirements
- 合规鉴定写 compliance_report_requirements

---

### 11. 清关要求
#### 原始表达常见形式
- customs clearance at entry office
- declaration required
- temporary admission title valid for one month
- release into consumption

#### 映射字段
- customs_and_documents.customs_clearance_requirements
- logistics_and_delivery.logistics_constraints
- risk_and_review.operational_warnings

#### 处理规则
- 清关程序写 customs_clearance_requirements
- 时效或临时入境限制写 logistics_constraints

---

### 12. 风险与人工复核
#### 原始表达常见形式
- subject to verification
- unless otherwise approved
- not clearly defined
- exceptions may apply
- special case handling required

#### 映射字段
- risk_and_review.risk_flags
- risk_and_review.manual_review_required_cases
- risk_and_review.enforcement_uncertainty_notes

#### 处理规则
- 法规含糊、适用边界不清、税费未拆清、商业/个人边界模糊的，一律进入人工复核提示

---

## 四、抽取结果状态建议
每次抽取后，字段状态建议分为：

- extracted_confirmed
- extracted_with_uncertainty
- pending_verification
- not_found_in_source

其中：
- extracted_confirmed：可直接入正式国家卡
- extracted_with_uncertainty：可入国家卡，但必须附带 notes
- pending_verification：进入待验证层
- not_found_in_source：当前来源未发现

---

## 五、Algeria 样板映射说明
Algeria 当前已验证适合作为第一张映射样板卡。
建议重点作为以下字段的样板来源：
- applicable_person_type
- usage_scope
- frequency_limit
- used_vehicle_import_allowed
- allowed_vehicle_types
- max_vehicle_age_years
- foreign_exchange_requirements
- required_documents
- customs_clearance_requirements
- compliance_report_requirements
- risk_flags

---

## 六、后续脚本化方向
后续自动化脚本应围绕本模板发展为：
1. 原文句段识别
2. 句段 -> 字段映射
3. 字段置信度打分
4. uncertain 字段自动进入 pending_verification
5. 正式字段自动写回 country card

