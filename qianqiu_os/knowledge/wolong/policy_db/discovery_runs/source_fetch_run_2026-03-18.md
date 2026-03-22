<!-- ================================================================
Copyright (c) 2026 程特峰 (Tefeng Cheng)
All Rights Reserved.

Project: AgentOS / Wolong Agent System
This document and its contents are proprietary and confidential.
Unauthorized copying, modification, distribution or use of this
document, in whole or in part, is strictly prohibited.
================================================================ -->

# 卧龙 Agent 真实网页抓取执行结果（V0.1）

- run_id: source_fetch_run_2026-03-18
- source_discovery_run_id: source_discovery_run_2026-03-18
- country_count: 11
- total_verified_sites: 22
- ok_sites: 18
- failed_sites: 4
- fallback_sites: 18

## 国家抓取结果

| Country | 中文名 | verified_sites | fetched_sites | ok_sites | failed_sites | fallback_sites |
|---|---|---:|---:|---:|---:|---:|
| Algeria | 阿尔及利亚 | 2 | 2 | 2 | 0 | 2 |
| Saudi Arabia | 沙特阿拉伯 | 2 | 2 | 2 | 0 | 2 |
| United Arab Emirates | 阿联酋 | 1 | 1 | 1 | 0 | 1 |
| Ghana | 加纳 | 2 | 2 | 0 | 2 | 0 |
| Mexico | 墨西哥 | 2 | 2 | 2 | 0 | 2 |
| Kazakhstan | 哈萨克斯坦 | 2 | 2 | 2 | 0 | 2 |
| Uzbekistan | 乌兹别克斯坦 | 1 | 1 | 1 | 0 | 1 |
| Armenia | 亚美尼亚 | 4 | 4 | 3 | 1 | 3 |
| Kyrgyzstan | 吉尔吉斯斯坦 | 1 | 1 | 1 | 0 | 1 |
| Tajikistan | 塔吉克斯坦 | 3 | 3 | 2 | 1 | 2 |
| Turkmenistan | 土库曼斯坦 | 2 | 2 | 2 | 0 | 2 |

## 站点明细

### Algeria / 阿尔及利亚

- commerce.gov.dz [transport_or_industry_or_trade] status=200 ok=True fetch_mode=fallback_unverified_ssl content_type=text/html; charset=UTF-8 body_file=commerce.gov.dz__root.html error= fallback_reason=URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1096)>
- joradp.dz [official_gazette_or_law_db] status=200 ok=True fetch_mode=fallback_unverified_ssl content_type=text/html body_file=joradp.dz__root.html error= fallback_reason=URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1096)>

### Saudi Arabia / 沙特阿拉伯

- zatca.gov.sa [customs] status=200 ok=True fetch_mode=fallback_unverified_ssl content_type=text/html; charset=utf-8 body_file=zatca.gov.sa__root.html error= fallback_reason=URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain (_ssl.c:1096)>
- zatca.gov.sa [tax_or_revenue] status=200 ok=True fetch_mode=fallback_unverified_ssl content_type=text/html; charset=utf-8 body_file=zatca.gov.sa__root.html error= fallback_reason=URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain (_ssl.c:1096)>

### United Arab Emirates / 阿联酋

- moiat.gov.ae [transport_or_industry_or_trade] status=200 ok=True fetch_mode=fallback_unverified_ssl content_type=text/html; charset=utf-8 body_file=moiat.gov.ae__root.html error= fallback_reason=URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1096)>

### Ghana / 加纳

- gragh.gov.gh [customs] status=0 ok=False fetch_mode=fallback_unverified_ssl content_type= body_file= error=URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1096)> fallback_reason=URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1096)>
- gragh.gov.gh [tax_or_revenue] status=0 ok=False fetch_mode=fallback_unverified_ssl content_type= body_file= error=URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1096)> fallback_reason=URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1096)>

### Mexico / 墨西哥

- sat.gob.mx [tax_or_revenue] status=200 ok=True fetch_mode=fallback_unverified_ssl content_type=text/html body_file=sat.gob.mx__root.html error= fallback_reason=URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain (_ssl.c:1096)>
- sat.gob.mx [customs] status=200 ok=True fetch_mode=fallback_unverified_ssl content_type=text/html body_file=sat.gob.mx__root.html error= fallback_reason=URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain (_ssl.c:1096)>

### Kazakhstan / 哈萨克斯坦

- egov.kz [customs] status=200 ok=True fetch_mode=fallback_unverified_ssl content_type=text/html; charset=utf-8 body_file=egov.kz__root.html error= fallback_reason=URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1096)>
- adilet.zan.kz [official_gazette_or_law_db] status=200 ok=True fetch_mode=fallback_unverified_ssl content_type=text/html;charset=UTF-8 body_file=adilet.zan.kz__root.html error= fallback_reason=URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1096)>

### Uzbekistan / 乌兹别克斯坦

- customs.uz [customs] status=200 ok=True fetch_mode=fallback_unverified_ssl content_type=text/html; charset=UTF-8 body_file=customs.uz__root.html error= fallback_reason=URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain (_ssl.c:1096)>

### Armenia / 亚美尼亚

- src.am [customs] status=200 ok=True fetch_mode=fallback_unverified_ssl content_type=text/html; charset=UTF-8 body_file=src.am__root.html error= fallback_reason=URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1096)>
- src.am [tax_or_revenue] status=200 ok=True fetch_mode=fallback_unverified_ssl content_type=text/html; charset=UTF-8 body_file=src.am__root.html error= fallback_reason=URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1096)>
- arlis.am [official_gazette_or_law_db] status=200 ok=True fetch_mode=fallback_unverified_ssl content_type=text/html; charset=UTF-8 body_file=arlis.am__root.html error= fallback_reason=URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1096)>
- new.arlis.am [official_gazette_or_law_db] status=0 ok=False fetch_mode=fallback_unverified_ssl content_type= body_file= error=URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1096)> fallback_reason=URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1096)>

### Kyrgyzstan / 吉尔吉斯斯坦

- customs.gov.kg [customs] status=200 ok=True fetch_mode=fallback_unverified_ssl content_type=text/html;charset=utf-8 body_file=customs.gov.kg__root.html error= fallback_reason=URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1096)>

### Tajikistan / 塔吉克斯坦

- andoz.tj [tax_or_revenue] status=200 ok=True fetch_mode=fallback_unverified_ssl content_type=text/html; charset=utf-8 body_file=andoz.tj__root.html error= fallback_reason=URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1096)>
- customs.tj [customs] status=200 ok=True fetch_mode=fallback_unverified_ssl content_type=text/html; charset=utf-8 body_file=customs.tj__root.html error= fallback_reason=URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1096)>
- adliya.tj [official_gazette_or_law_db] status=0 ok=False fetch_mode=fallback_unverified_ssl content_type= body_file= error=URLError: <urlopen error _ssl.c:1078: The handshake operation timed out> fallback_reason=URLError: <urlopen error _ssl.c:1078: The handshake operation timed out>

### Turkmenistan / 土库曼斯坦

- customs.gov.tm [customs] status=200 ok=True fetch_mode=fallback_unverified_ssl content_type=text/html; charset=UTF-8 body_file=customs.gov.tm__root.html error= fallback_reason=URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain (_ssl.c:1096)>
- infotrade.gov.tm [transport_or_industry_or_trade] status=200 ok=True fetch_mode=fallback_unverified_ssl content_type=text/html; charset=utf-8 body_file=infotrade.gov.tm__root.html error= fallback_reason=URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1096)>

