<!-- ================================================================
Copyright (c) 2026 程特峰 (Tefeng Cheng)
All Rights Reserved.

Project: AgentOS / Wolong Agent System
This document and its contents are proprietary and confidential.
Unauthorized copying, modification, distribution or use of this
document, in whole or in part, is strictly prohibited.
================================================================ -->

# 卧龙 Agent source discovery 渠道清单（V1）

## 一、目标
本清单用于国家政策法规活数据库的自动找源环节。
目标不是“随便搜索网页”，而是优先锁定：
- 官方法规源
- 官方海关/税务/交通/工业/商务主管部门
- 官方公报 / 法律数据库
- 高可信行业辅助源
- 待验证实操反馈源

---

## 二、来源分级
### A 级来源（优先）
- 官方公报
- 海关官网
- 税务主管部门
- 交通/工业/商务主管部门
- 官方法规数据库
- 官方 FAQ / 官方服务说明页

### B 级来源
- 高可信行业机构
- 正规清关/物流服务商
- 商务情报 / 市场准入说明
- 使领馆或官方授权说明材料

### C 级来源
- 实操反馈
- 市场传闻
- 非正式经验总结
- 社区讨论

规则：
- A 级可直接作为正式规则依据候选
- B 级可作为补充与交叉验证
- C 级只进入 pending_verification，不得直接覆盖正式规则

---

## 三、重点国家第一轮渠道方向

### 1. Algeria
A 级优先：
- 官方公报 / Journal Officiel
- 海关 / 财政相关部门
- 工业 / 矿业 / 交通主管部门

B 级补充：
- 正规清关/物流合规机构
- 专业法规解读材料

### 2. Saudi Arabia
A 级优先：
- ZATCA
- Saudi Standards / related official import controls
- 交通/商业主管部门

B 级补充：
- 官方授权 FAQ
- 正规物流合规机构

### 3. United Arab Emirates
A 级优先：
- 联邦工业/先进技术主管部门
- Customs 官方渠道
- 道路/车辆监管官方渠道

B 级补充：
- Dubai Customs / Abu Dhabi Customs 官方说明页
- 合规服务说明页

### 4. Ghana
A 级优先：
- Customs / Revenue Authority
- 贸易/交通相关官方渠道
- 官方进口程序说明页

B 级补充：
- U.S. Commercial Service / 市场准入情报
- 高可信行业资料

### 5. Mexico
A 级优先：
- SAT / Aduanas
- Economía / 交通主管部门
- 官方进口法规与程序页

B 级补充：
- 高可信市场准入说明
- 商务情报页

### 6. Armenia
A 级优先：
- Customs / Revenue Committee
- Economy / Transport official pages
- EAEU 相关官方规则页

B 级补充：
- 高可信行业合规资料

### 7. Kazakhstan
A 级优先：
- eGov
- Adilet
- Customs / Revenue / Transport official pages

B 级补充：
- 高可信新闻或合规机构说明

### 8. Kyrgyzstan
A 级优先：
- Customs / Government legal portal
- Revenue / Transport official pages

B 级补充：
- 高可信合规资讯

### 9. Uzbekistan
A 级优先：
- Customs / Lex / government legal portal
- Transport / trade official pages

B 级补充：
- 高可信市场准入资料

### 10. Tajikistan
A 级优先：
- Customs / legal portal / official ministry pages

B 级补充：
- 高可信行业资料

### 11. Turkmenistan
A 级优先：
- Customs / official government pages / legal portal

B 级补充：
- 高可信行业与市场资料

---

## 四、渠道清单字段建议
每条渠道建议记录：
- country
- source_name
- source_level
- source_type
- preferred_for
- base_url
- notes
- last_checked_at
- next_small_update_due
- next_major_update_due

---

## 五、后续执行原则
1. 每个国家先从 A 级渠道开始
2. A 级不充分时，再引入 B 级补充
3. C 级只进入待验证层
4. 每次找源必须记录来源状态
5. 每次找源后都要刷新 next_small_update_due / next_major_update_due

