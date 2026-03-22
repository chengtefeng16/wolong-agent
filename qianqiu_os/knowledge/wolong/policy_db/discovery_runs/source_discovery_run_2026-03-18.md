<!-- ================================================================
Copyright (c) 2026 程特峰 (Tefeng Cheng)
All Rights Reserved.

Project: AgentOS / Wolong Agent System
This document and its contents are proprietary and confidential.
Unauthorized copying, modification, distribution or use of this
document, in whole or in part, is strictly prohibited.
================================================================ -->

# 卧龙 Agent source discovery 执行清单（V0）

- run_id: source_discovery_run_2026-03-18
- run_time: 2026-03-18
- 国家总数: 11
- 可直接执行国家数: 11
- 仍待补白名单国家数: 0
- next_small_update_due: 2026-03-21
- next_major_update_due: 2026-03-25

## 国家执行清单

| Country | 中文名 | whitelist_status | verified_sites | pending_sites | discovery_ready | priority_dimensions |
|---|---|---|---:|---:|---|---|
| Algeria | 阿尔及利亚 | partial_verified | 2 | 2 | Y | official_gazette_or_law_db, transport_or_industry_or_trade |
| Saudi Arabia | 沙特阿拉伯 | verified_core | 2 | 0 | Y | customs, tax_or_revenue |
| United Arab Emirates | 阿联酋 | verified_core | 1 | 2 | Y | transport_or_industry_or_trade |
| Ghana | 加纳 | verified_core | 2 | 0 | Y | customs, tax_or_revenue |
| Mexico | 墨西哥 | verified_core | 2 | 2 | Y | customs, tax_or_revenue |
| Kazakhstan | 哈萨克斯坦 | verified_core | 2 | 1 | Y | customs, official_gazette_or_law_db |
| Uzbekistan | 乌兹别克斯坦 | verified_core | 1 | 2 | Y | customs |
| Armenia | 亚美尼亚 | verified_core | 4 | 0 | Y | customs, tax_or_revenue, official_gazette_or_law_db |
| Kyrgyzstan | 吉尔吉斯斯坦 | partial_verified | 1 | 0 | Y | customs |
| Tajikistan | 塔吉克斯坦 | verified_core | 3 | 0 | Y | customs, tax_or_revenue, official_gazette_or_law_db |
| Turkmenistan | 土库曼斯坦 | verified_core | 2 | 0 | Y | customs, transport_or_industry_or_trade |

## 分国家站点清单

### Algeria / 阿尔及利亚

- language_family: fr_ar
- whitelist_status: partial_verified
- discovery_ready: Y

#### verified_sites
- commerce.gov.dz [transport_or_industry_or_trade]
- joradp.dz [official_gazette_or_law_db]

#### pending_sites
- douane.gov.dz [customs]
- impots.gov.dz [tax_or_revenue]

### Saudi Arabia / 沙特阿拉伯

- language_family: ar_en
- whitelist_status: verified_core
- discovery_ready: Y

#### verified_sites
- zatca.gov.sa [customs]
- zatca.gov.sa [tax_or_revenue]

#### pending_sites
- none

### United Arab Emirates / 阿联酋

- language_family: ar_en
- whitelist_status: verified_core
- discovery_ready: Y

#### verified_sites
- moiat.gov.ae [transport_or_industry_or_trade]

#### pending_sites
- dubaicustoms.gov.ae [customs]
- abudhabicustoms.gov.ae [customs]

### Ghana / 加纳

- language_family: en
- whitelist_status: verified_core
- discovery_ready: Y

#### verified_sites
- gragh.gov.gh [customs]
- gragh.gov.gh [tax_or_revenue]

#### pending_sites
- none

### Mexico / 墨西哥

- language_family: es
- whitelist_status: verified_core
- discovery_ready: Y

#### verified_sites
- sat.gob.mx [tax_or_revenue]
- sat.gob.mx [customs]

#### pending_sites
- anam.gob.mx [customs]
- dof.gob.mx [official_gazette_or_law_db]

### Kazakhstan / 哈萨克斯坦

- language_family: kk_ru
- whitelist_status: verified_core
- discovery_ready: Y

#### verified_sites
- egov.kz [customs]
- adilet.zan.kz [official_gazette_or_law_db]

#### pending_sites
- kgd.gov.kz [tax_or_revenue]

### Uzbekistan / 乌兹别克斯坦

- language_family: uz_ru
- whitelist_status: verified_core
- discovery_ready: Y

#### verified_sites
- customs.uz [customs]

#### pending_sites
- lex.uz [official_gazette_or_law_db]
- soliq.uz [tax_or_revenue]

### Armenia / 亚美尼亚

- language_family: hy_ru
- whitelist_status: verified_core
- discovery_ready: Y

#### verified_sites
- src.am [customs]
- src.am [tax_or_revenue]
- arlis.am [official_gazette_or_law_db]
- new.arlis.am [official_gazette_or_law_db]

#### pending_sites
- none

### Kyrgyzstan / 吉尔吉斯斯坦

- language_family: ky_ru
- whitelist_status: partial_verified
- discovery_ready: Y

#### verified_sites
- customs.gov.kg [customs]

#### pending_sites
- none

### Tajikistan / 塔吉克斯坦

- language_family: tg_ru
- whitelist_status: verified_core
- discovery_ready: Y

#### verified_sites
- andoz.tj [tax_or_revenue]
- customs.tj [customs]
- adliya.tj [official_gazette_or_law_db]

#### pending_sites
- none

### Turkmenistan / 土库曼斯坦

- language_family: tk_ru
- whitelist_status: verified_core
- discovery_ready: Y

#### verified_sites
- customs.gov.tm [customs]
- infotrade.gov.tm [transport_or_industry_or_trade]

#### pending_sites
- none

