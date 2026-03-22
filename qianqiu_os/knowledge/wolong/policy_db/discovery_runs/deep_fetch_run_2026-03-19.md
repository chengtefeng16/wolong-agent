<!-- ================================================================
Copyright (c) 2026 程特峰 (Tefeng Cheng)
All Rights Reserved.

Project: AgentOS / Wolong Agent System
This document and its contents are proprietary and confidential.
Unauthorized copying, modification, distribution or use of this
document, in whole or in part, is strictly prohibited.
================================================================ -->

# 卧龙 Agent 深链真实抓取结果（V0）

- run_id: deep_fetch_run_2026-03-19
- source_site_search_run_id: site_search_run_2026-03-19
- site_count: 15
- total_selected_links: 31
- ok_links: 29
- failed_links: 2
- pdf_links: 1

## 站点汇总

| Country Slug | Domain | selected | fetched | ok | failed |
|---|---|---:|---:|---:|---:|
| algeria | commerce.gov.dz | 3 | 3 | 2 | 1 |
| algeria | joradp.dz | 0 | 0 | 0 | 0 |
| armenia | arlis.am | 3 | 3 | 3 | 0 |
| armenia | src.am | 2 | 2 | 2 | 0 |
| kazakhstan | adilet.zan.kz | 1 | 1 | 1 | 0 |
| kazakhstan | egov.kz | 3 | 3 | 2 | 1 |
| kyrgyzstan | customs.gov.kg | 3 | 3 | 3 | 0 |
| mexico | sat.gob.mx | 0 | 0 | 0 | 0 |
| saudi_arabia | zatca.gov.sa | 0 | 0 | 0 | 0 |
| tajikistan | andoz.tj | 3 | 3 | 3 | 0 |
| tajikistan | customs.tj | 3 | 3 | 3 | 0 |
| turkmenistan | customs.gov.tm | 3 | 3 | 3 | 0 |
| turkmenistan | infotrade.gov.tm | 1 | 1 | 1 | 0 |
| united_arab_emirates | moiat.gov.ae | 3 | 3 | 3 | 0 |
| uzbekistan | customs.uz | 3 | 3 | 3 | 0 |

## 深链明细

### algeria / commerce.gov.dz

- score=1 ok=False status=503 fetch_mode=fallback_unverified_ssl url=http://www.commerce.gov.dz/avis/collection/avis-douverture-de-licence-dimportation body_file= keyword_hits=import
- score=1 ok=True status=200 fetch_mode=fallback_unverified_ssl url=https://commerce.gov.dz/avis/profil/importateur body_file=commerce.gov.dz_avis_profil_importateur.html keyword_hits=import
- score=1 ok=True status=200 fetch_mode=fallback_unverified_ssl url=https://commerce.gov.dz/listing-des-autorites-de-regulation body_file=commerce.gov.dz_listing-des-autorites-de-regulation.html keyword_hits=regulation

### algeria / joradp.dz

- none

### armenia / arlis.am

- score=1 ok=True status=200 fetch_mode=fallback_unverified_ssl url=http://www.datalex.am/ body_file=www.datalex.am_.html keyword_hits=lex
- score=1 ok=True status=200 fetch_mode=fallback_unverified_ssl url=https://wiselaw.am/ body_file=wiselaw.am_.html keyword_hits=law
- score=1 ok=True status=200 fetch_mode=fallback_unverified_ssl url=https://www.finlex.am/ body_file=www.finlex.am_.bin keyword_hits=lex

### armenia / src.am

- score=1 ok=True status=200 fetch_mode=fallback_unverified_ssl url=https://src.am/am/legal body_file=src.am_am_legal.html keyword_hits=legal
- score=1 ok=True status=200 fetch_mode=fallback_unverified_ssl url=https://src.am/am/showDeclarationsPage/207 body_file=src.am_am_showdeclarationspage_207.html keyword_hits=declaration

### kazakhstan / adilet.zan.kz

- score=1 ok=True status=200 fetch_mode=fallback_unverified_ssl url=https://adilet.zan.kz/kaz/histlawkz body_file=adilet.zan.kz_kaz_histlawkz.html keyword_hits=law

### kazakhstan / egov.kz

- score=1 ok=True status=200 fetch_mode=fallback_unverified_ssl url=https://egov.kz/cms/kk/categories/bus_tax body_file=egov.kz_cms_kk_categories_bus_tax.html keyword_hits=tax
- score=1 ok=True status=200 fetch_mode=fallback_unverified_ssl url=https://egov.kz/cms/kk/information/help/tax_code body_file=egov.kz_cms_kk_information_help_tax_code.html keyword_hits=tax
- score=1 ok=False status=504 fetch_mode=fallback_unverified_ssl url=https://egov.kz/cms/kk/law body_file= keyword_hits=law

### kyrgyzstan / customs.gov.kg

- score=1 ok=True status=200 fetch_mode=fallback_unverified_ssl url=https://customs.gov.kg/# body_file=customs.gov.kg_#.html keyword_hits=customs
- score=1 ok=True status=200 fetch_mode=fallback_unverified_ssl url=https://customs.gov.kg/site/ky/master/_/service/customskg/react4xp/shared.css body_file=customs.gov.kg_site_ky_master___service_customskg_react4xp_shared.css.txt keyword_hits=customs
- score=1 ok=True status=200 fetch_mode=fallback_unverified_ssl url=https://customs.gov.kg/site/ky/master/_/service/customskg/react4xp/site/layouts/section/section.css body_file=customs.gov.kg_site_ky_master___service_customskg_react4xp_site_layouts_section_section.css.txt keyword_hits=customs

### mexico / sat.gob.mx

- none

### saudi_arabia / zatca.gov.sa

- none

### tajikistan / andoz.tj

- score=2 ok=True status=200 fetch_mode=fallback_unverified_ssl url=https://andoz.tj/ForTaxpayer/DeclarationsNew body_file=andoz.tj_fortaxpayer_declarationsnew.html keyword_hits=tax,declaration
- score=2 ok=True status=200 fetch_mode=fallback_unverified_ssl url=https://andoz.tj/ForTaxpayer/DeclarationsOld body_file=andoz.tj_fortaxpayer_declarationsold.html keyword_hits=tax,declaration
- score=1 ok=True status=200 fetch_mode=fallback_unverified_ssl url=https://andoz.tj/ForTaxpayer body_file=andoz.tj_fortaxpayer.html keyword_hits=tax

### tajikistan / customs.tj

- score=2 ok=True status=200 fetch_mode=fallback_unverified_ssl url=https://customs.tj/images/stories/img_text/Dar_borai_KHGHJT/Kodeks/Kodek.pdf body_file=customs.tj_images_stories_img_text_dar_borai_khghjt_kodeks_kodek.pdf.pdf keyword_hits=customs,kodeks
- score=1 ok=True status=200 fetch_mode=fallback_unverified_ssl url=http://customs.tj/ body_file=customs.tj_.html keyword_hits=customs
- score=1 ok=True status=200 fetch_mode=standard_ssl url=http://infoportal.customs.tj body_file=infoportal.customs.tj.html keyword_hits=customs

### turkmenistan / customs.gov.tm

- score=2 ok=True status=200 fetch_mode=fallback_unverified_ssl url=https://customs.gov.tm/#for_legal_entities body_file=customs.gov.tm_#for_legal_entities.html keyword_hits=customs,legal
- score=2 ok=True status=200 fetch_mode=fallback_unverified_ssl url=https://customs.gov.tm/customs-info/for-legal-entities body_file=customs.gov.tm_customs-info_for-legal-entities.html keyword_hits=customs,legal
- score=2 ok=True status=200 fetch_mode=fallback_unverified_ssl url=https://customs.gov.tm/export-import/brokers body_file=customs.gov.tm_export-import_brokers.html keyword_hits=import,customs

### turkmenistan / infotrade.gov.tm

- score=1 ok=True status=200 fetch_mode=fallback_unverified_ssl url=https://infotrade.gov.tm/Laws?l=tk body_file=infotrade.gov.tm_laws_l_tk.html keyword_hits=law

### united_arab_emirates / moiat.gov.ae

- score=1 ok=True status=200 fetch_mode=fallback_unverified_ssl url=https://moiat.gov.ae/ar/about-us/laws-and-legislation body_file=moiat.gov.ae_ar_about-us_laws-and-legislation.html keyword_hits=law
- score=1 ok=True status=200 fetch_mode=fallback_unverified_ssl url=https://moiat.gov.ae/ar/digital-participation/consultations/advisory-national-metrology-capabilitiestechnical-regulations-for-air-quality-measurement body_file=moiat.gov.ae_ar_digital-participation_consultations_advisory-national-metrology-capabilitiestechnical-regulations-for-air-quality-measurement.html keyword_hits=regulation
- score=1 ok=True status=200 fetch_mode=fallback_unverified_ssl url=https://moiat.gov.ae/ar/digital-participation/consultations/advisory-note-registering-items-for-customs-exemption body_file=moiat.gov.ae_ar_digital-participation_consultations_advisory-note-registering-items-for-customs-exemption.html keyword_hits=customs

### uzbekistan / customs.uz

- score=1 ok=True status=200 fetch_mode=fallback_unverified_ssl url=http://customs.uz body_file=customs.uz.html keyword_hits=customs
- score=1 ok=True status=200 fetch_mode=fallback_unverified_ssl url=http://customs.uz/css/bootstrap-theme.min.css body_file=customs.uz_css_bootstrap-theme.min.css.txt keyword_hits=customs
- score=1 ok=True status=200 fetch_mode=fallback_unverified_ssl url=http://customs.uz/css/bootstrap.min.css body_file=customs.uz_css_bootstrap.min.css.txt keyword_hits=customs

