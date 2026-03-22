<!-- ================================================================
Copyright (c) 2026 程特峰 (Tefeng Cheng)
All Rights Reserved.

Project: AgentOS / Wolong Agent System
This document and its contents are proprietary and confidential.
Unauthorized copying, modification, distribution or use of this
document, in whole or in part, is strictly prohibited.
================================================================ -->

# 卧龙 Agent 区域级来源缺口分析（V0）

- 区域总数：4

## 区域概览

| Region | Countries | Audit Restricted | Cross Validation Weak | Priority Gaps |
|---|---:|---:|---:|---|
| central_asia | 6 | 6 | 6 | customs, official_gazette_or_law_db, tax_or_revenue |
| africa | 2 | 2 | 1 | tax_or_revenue, transport_or_industry_or_trade, customs |
| middle_east | 2 | 2 | 1 | high_trust_industry_or_embassy, official_gazette_or_law_db, tax_or_revenue |
| latin_america | 1 | 1 | 0 | official_gazette_or_law_db, tax_or_revenue, transport_or_industry_or_trade |

## 区域缺口明细

### central_asia

| Source Dimension | Covered Countries | Gap Countries |
|---|---:|---:|
| customs | 0 | 6 |
| tax_or_revenue | 0 | 6 |
| transport_or_industry_or_trade | 0 | 6 |
| official_gazette_or_law_db | 0 | 6 |
| high_trust_industry_or_embassy | 5 | 1 |

| Country | 中文名 | audit_status | cross_validation | customs | tax | transport/trade | gazette/law_db | high_trust |
|---|---|---|---|---|---|---|---|---|
| Armenia | 亚美尼亚 | audit_restricted | weak | N | N | N | N | Y |
| Kazakhstan | 哈萨克斯坦 | audit_restricted | weak | N | N | N | N | N |
| Kyrgyzstan | 吉尔吉斯斯坦 | audit_restricted | weak | N | N | N | N | Y |
| Tajikistan | 塔吉克斯坦 | audit_restricted | weak | N | N | N | N | Y |
| Turkmenistan | 土库曼斯坦 | audit_restricted | weak | N | N | N | N | Y |
| Uzbekistan | 乌兹别克斯坦 | audit_restricted | weak | N | N | N | N | Y |

### africa

| Source Dimension | Covered Countries | Gap Countries |
|---|---:|---:|
| customs | 1 | 1 |
| tax_or_revenue | 0 | 2 |
| transport_or_industry_or_trade | 0 | 2 |
| official_gazette_or_law_db | 1 | 1 |
| high_trust_industry_or_embassy | 1 | 1 |

| Country | 中文名 | audit_status | cross_validation | customs | tax | transport/trade | gazette/law_db | high_trust |
|---|---|---|---|---|---|---|---|---|
| Algeria | 阿尔及利亚 | audit_restricted | weak | N | N | N | Y | N |
| Ghana | 加纳 | audit_restricted | medium | Y | N | N | N | Y |

### middle_east

| Source Dimension | Covered Countries | Gap Countries |
|---|---:|---:|
| customs | 2 | 0 |
| tax_or_revenue | 0 | 2 |
| transport_or_industry_or_trade | 1 | 1 |
| official_gazette_or_law_db | 0 | 2 |
| high_trust_industry_or_embassy | 0 | 2 |

| Country | 中文名 | audit_status | cross_validation | customs | tax | transport/trade | gazette/law_db | high_trust |
|---|---|---|---|---|---|---|---|---|
| Saudi Arabia | 沙特阿拉伯 | audit_restricted | weak | Y | N | N | N | N |
| United Arab Emirates | 阿联酋 | audit_restricted | medium | Y | N | Y | N | N |

### latin_america

| Source Dimension | Covered Countries | Gap Countries |
|---|---:|---:|
| customs | 1 | 0 |
| tax_or_revenue | 0 | 1 |
| transport_or_industry_or_trade | 0 | 1 |
| official_gazette_or_law_db | 0 | 1 |
| high_trust_industry_or_embassy | 1 | 0 |

| Country | 中文名 | audit_status | cross_validation | customs | tax | transport/trade | gazette/law_db | high_trust |
|---|---|---|---|---|---|---|---|---|
| Mexico | 墨西哥 | audit_restricted | medium | Y | N | N | N | Y |

