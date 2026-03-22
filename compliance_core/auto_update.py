# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

import yaml
import requests
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup

# ===================================
# 自动更新监测器 V1 – Draft 版本
# ===================================

BASE_PATH = Path(__file__).parent

def load_data_sources(country_code: str):
    """ 加载国家数据源配置 """
    config_path = BASE_PATH / "data_sources" / f"{country_code}_sources.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"No config for {country_code}")
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config

def fetch_url_text(url):
    import requests

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=20,
        verify=False  # 忽略SSL证书
    )

    response.raise_for_status()
    return response.text

def simple_extract_text(html_content: str):
    """ 先用最简单的方式提取所有文本 """
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(separator="\n")

def create_draft_policy(country_code: str):
    """
    生成待确认 draft 版政策法规内容
    """

    config = load_data_sources(country_code)
    draft = {
        "country": config["country"],
        "version": None,
        "source_urls": [],
        "last_checked": datetime.utcnow().strftime("%Y-%m-%d"),
        "max_vehicle_age_years": None,
        "min_vehicle_age_years": None,
        "allowed_fuel_types": [],
        "engine_displacement_max_l": None,
        "power_max_kw": None,
        "steering_requirement": None,
        "accident_vehicle_allowed": None,
        "used_as_taxi_allowed": None,
        "tax_rate_percent": None,
        "consumption_tax_percent": None,
        "emission_standard_required": None,
        "additional_notes": ""
    }

    for src in config["sources"]:
        url = src["url"]
        draft["source_urls"].append(url)

        try:
            html = fetch_url_text(url)
            text = simple_extract_text(html)
            draft["additional_notes"] += f"\n--- SOURCE {url} ---\n{text}\n"
        except Exception as e:
            draft["additional_notes"] += f"\n--- SOURCE {url} FAILED: {str(e)} ---\n"

    return draft

