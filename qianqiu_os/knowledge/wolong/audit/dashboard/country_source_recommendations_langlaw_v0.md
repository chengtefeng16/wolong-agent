<!-- ================================================================
Copyright (c) 2026 程特峰 (Tefeng Cheng)
All Rights Reserved.

Project: AgentOS / Wolong Agent System
This document and its contents are proprietary and confidential.
Unauthorized copying, modification, distribution or use of this
document, in whole or in part, is strictly prohibited.
================================================================ -->

# 卧龙 Agent 按国家语言/法系差异调整补源建议（V0）

- 国家总数：11

## 单国补源建议概览

| Country | 中文名 | Region | Language | Legal Style | audit_status | Top Priority Sources |
|---|---|---|---|---|---|---|
| Algeria | 阿尔及利亚 | africa | fr_ar | francophone_gazette_heavy | audit_restricted | customs, tax_or_revenue, transport_or_industry_or_trade |
| Armenia | 亚美尼亚 | central_asia | hy_ru | post_soviet_legal_portal | audit_restricted | official_gazette_or_law_db, customs, tax_or_revenue |
| Kazakhstan | 哈萨克斯坦 | central_asia | kk_ru | post_soviet_legal_portal | audit_restricted | official_gazette_or_law_db, customs, tax_or_revenue |
| Kyrgyzstan | 吉尔吉斯斯坦 | central_asia | ky_ru | post_soviet_legal_portal | audit_restricted | official_gazette_or_law_db, customs, tax_or_revenue |
| Saudi Arabia | 沙特阿拉伯 | middle_east | ar_en | agency_guidance_plus_regulatory_pages | audit_restricted | tax_or_revenue, transport_or_industry_or_trade, official_gazette_or_law_db |
| Tajikistan | 塔吉克斯坦 | central_asia | tg_ru | legal_portal_plus_agency_pages | audit_restricted | official_gazette_or_law_db, customs, tax_or_revenue |
| Turkmenistan | 土库曼斯坦 | central_asia | tk_ru | official_portal_limited_visibility | audit_restricted | official_gazette_or_law_db, customs, tax_or_revenue |
| Uzbekistan | 乌兹别克斯坦 | central_asia | uz_ru | legal_portal_plus_agency_pages | audit_restricted | official_gazette_or_law_db, customs, tax_or_revenue |
| Ghana | 加纳 | africa | en | agency_guidance_plus_market_info | audit_restricted | tax_or_revenue, transport_or_industry_or_trade, official_gazette_or_law_db |
| Mexico | 墨西哥 | latin_america | es | spanish_tax_customs_legal_bulletin | audit_restricted | official_gazette_or_law_db, tax_or_revenue, transport_or_industry_or_trade |
| United Arab Emirates | 阿联酋 | middle_east | ar_en | agency_guidance_plus_customs_pages | audit_restricted | official_gazette_or_law_db, tax_or_revenue, high_trust_industry_or_embassy |

## 分国家建议

### Algeria / 阿尔及利亚

- 语言体系：fr_ar
- 法系/发布习惯：francophone_gazette_heavy
- 找源提示：优先找法语官方公报、法语法令页、法语海关/财政/工业部门页面；阿语可做交叉验证。

1. 海关来源：优先补海关官网、海关公告、清关规则页；优先找法语官方公报、法语法令页、法语海关/财政/工业部门页面；阿语可做交叉验证。
2. 税务/财政来源：优先补税务、财政、收入主管部门资料；优先找法语官方公报、法语法令页、法语海关/财政/工业部门页面；阿语可做交叉验证。
3. 交通/工业/商务来源：优先补交通、工业、商务主管部门资料；优先找法语官方公报、法语法令页、法语海关/财政/工业部门页面；阿语可做交叉验证。

### Armenia / 亚美尼亚

- 语言体系：hy_ru
- 法系/发布习惯：post_soviet_legal_portal
- 找源提示：优先找亚美尼亚政府法律门户、海关、税务、俄语/本国语法规页，必要时看欧亚经济联盟规则。

1. 官方公报/法律数据库来源：优先补官方公报、法令库、官方法规数据库；优先找亚美尼亚政府法律门户、海关、税务、俄语/本国语法规页，必要时看欧亚经济联盟规则。
2. 海关来源：优先补海关官网、海关公告、清关规则页；优先找亚美尼亚政府法律门户、海关、税务、俄语/本国语法规页，必要时看欧亚经济联盟规则。
3. 税务/财政来源：优先补税务、财政、收入主管部门资料；优先找亚美尼亚政府法律门户、海关、税务、俄语/本国语法规页，必要时看欧亚经济联盟规则。

### Kazakhstan / 哈萨克斯坦

- 语言体系：kk_ru
- 法系/发布习惯：post_soviet_legal_portal
- 找源提示：优先找 eGov、Adilet、海关、税务、俄语/哈语法规与政府说明页。

1. 官方公报/法律数据库来源：优先补官方公报、法令库、官方法规数据库；优先找 eGov、Adilet、海关、税务、俄语/哈语法规与政府说明页。
2. 海关来源：优先补海关官网、海关公告、清关规则页；优先找 eGov、Adilet、海关、税务、俄语/哈语法规与政府说明页。
3. 税务/财政来源：优先补税务、财政、收入主管部门资料；优先找 eGov、Adilet、海关、税务、俄语/哈语法规与政府说明页。

### Kyrgyzstan / 吉尔吉斯斯坦

- 语言体系：ky_ru
- 法系/发布习惯：post_soviet_legal_portal
- 找源提示：优先找政府法律库、海关、税务、俄语/本国语法规与政府说明页。

1. 官方公报/法律数据库来源：优先补官方公报、法令库、官方法规数据库；优先找政府法律库、海关、税务、俄语/本国语法规与政府说明页。
2. 海关来源：优先补海关官网、海关公告、清关规则页；优先找政府法律库、海关、税务、俄语/本国语法规与政府说明页。
3. 税务/财政来源：优先补税务、财政、收入主管部门资料；优先找政府法律库、海关、税务、俄语/本国语法规与政府说明页。

### Saudi Arabia / 沙特阿拉伯

- 语言体系：ar_en
- 法系/发布习惯：agency_guidance_plus_regulatory_pages
- 找源提示：优先找阿语/英语官方页、ZATCA、标准/交通/商务主管部门页面；法规与行政说明双轨并看。

1. 税务/财政来源：优先补税务、财政、收入主管部门资料；优先找阿语/英语官方页、ZATCA、标准/交通/商务主管部门页面；法规与行政说明双轨并看。
2. 交通/工业/商务来源：优先补交通、工业、商务主管部门资料；优先找阿语/英语官方页、ZATCA、标准/交通/商务主管部门页面；法规与行政说明双轨并看。
3. 官方公报/法律数据库来源：优先补官方公报、法令库、官方法规数据库；优先找阿语/英语官方页、ZATCA、标准/交通/商务主管部门页面；法规与行政说明双轨并看。

### Tajikistan / 塔吉克斯坦

- 语言体系：tg_ru
- 法系/发布习惯：legal_portal_plus_agency_pages
- 找源提示：优先找法律门户、海关、税务及俄语/塔吉克语政府页面。

1. 官方公报/法律数据库来源：优先补官方公报、法令库、官方法规数据库；优先找法律门户、海关、税务及俄语/塔吉克语政府页面。
2. 海关来源：优先补海关官网、海关公告、清关规则页；优先找法律门户、海关、税务及俄语/塔吉克语政府页面。
3. 税务/财政来源：优先补税务、财政、收入主管部门资料；优先找法律门户、海关、税务及俄语/塔吉克语政府页面。

### Turkmenistan / 土库曼斯坦

- 语言体系：tk_ru
- 法系/发布习惯：official_portal_limited_visibility
- 找源提示：优先找官方政府页、法律公报/法令页、海关说明；公开度不足时再用高可信行业源辅助。

1. 官方公报/法律数据库来源：优先补官方公报、法令库、官方法规数据库；优先找官方政府页、法律公报/法令页、海关说明；公开度不足时再用高可信行业源辅助。
2. 海关来源：优先补海关官网、海关公告、清关规则页；优先找官方政府页、法律公报/法令页、海关说明；公开度不足时再用高可信行业源辅助。
3. 税务/财政来源：优先补税务、财政、收入主管部门资料；优先找官方政府页、法律公报/法令页、海关说明；公开度不足时再用高可信行业源辅助。

### Uzbekistan / 乌兹别克斯坦

- 语言体系：uz_ru
- 法系/发布习惯：legal_portal_plus_agency_pages
- 找源提示：优先找 Lex / 政府法律门户、海关、税务、交通/贸易部门页面，乌兹语和俄语并看。

1. 官方公报/法律数据库来源：优先补官方公报、法令库、官方法规数据库；优先找 Lex / 政府法律门户、海关、税务、交通/贸易部门页面，乌兹语和俄语并看。
2. 海关来源：优先补海关官网、海关公告、清关规则页；优先找 Lex / 政府法律门户、海关、税务、交通/贸易部门页面，乌兹语和俄语并看。
3. 税务/财政来源：优先补税务、财政、收入主管部门资料；优先找 Lex / 政府法律门户、海关、税务、交通/贸易部门页面，乌兹语和俄语并看。

### Ghana / 加纳

- 语言体系：en
- 法系/发布习惯：agency_guidance_plus_market_info
- 找源提示：优先找 Customs/Revenue Authority、交通/贸易主管部门、英文市场准入和高可信商务说明。

1. 税务/财政来源：优先补税务、财政、收入主管部门资料；优先找 Customs/Revenue Authority、交通/贸易主管部门、英文市场准入和高可信商务说明。
2. 交通/工业/商务来源：优先补交通、工业、商务主管部门资料；优先找 Customs/Revenue Authority、交通/贸易主管部门、英文市场准入和高可信商务说明。
3. 官方公报/法律数据库来源：优先补官方公报、法令库、官方法规数据库；优先找 Customs/Revenue Authority、交通/贸易主管部门、英文市场准入和高可信商务说明。

### Mexico / 墨西哥

- 语言体系：es
- 法系/发布习惯：spanish_tax_customs_legal_bulletin
- 找源提示：优先找西语 SAT/Aduanas、Economía、交通主管部门、官方法令公报与法规库。

1. 官方公报/法律数据库来源：优先补官方公报、法令库、官方法规数据库；优先找西语 SAT/Aduanas、Economía、交通主管部门、官方法令公报与法规库。
2. 税务/财政来源：优先补税务、财政、收入主管部门资料；优先找西语 SAT/Aduanas、Economía、交通主管部门、官方法令公报与法规库。
3. 交通/工业/商务来源：优先补交通、工业、商务主管部门资料；优先找西语 SAT/Aduanas、Economía、交通主管部门、官方法令公报与法规库。

### United Arab Emirates / 阿联酋

- 语言体系：ar_en
- 法系/发布习惯：agency_guidance_plus_customs_pages
- 找源提示：优先找阿语/英语官方页、联邦主管部门、Dubai/Abu Dhabi Customs、工业/交通说明页。

1. 官方公报/法律数据库来源：优先补官方公报、法令库、官方法规数据库；优先找阿语/英语官方页、联邦主管部门、Dubai/Abu Dhabi Customs、工业/交通说明页。
2. 税务/财政来源：优先补税务、财政、收入主管部门资料；优先找阿语/英语官方页、联邦主管部门、Dubai/Abu Dhabi Customs、工业/交通说明页。
3. 高可信行业/使领馆/商务服务来源：优先补高可信行业机构、使领馆、商务服务说明；优先找阿语/英语官方页、联邦主管部门、Dubai/Abu Dhabi Customs、工业/交通说明页。

