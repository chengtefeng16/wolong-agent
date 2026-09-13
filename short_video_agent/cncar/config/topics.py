"""CNcar 选题候选池

每条记录：(car_model, destination, country_iso2, fob_usd_reference)
- fob_usd_reference 是填进 cncar.io/cost-calculator 的参考 FOB 价，用于指导人工填表
- 实际 landed_cost_usd 由网站真实引擎算出，不在此处计算
- UAE 出现两次 → 权重加倍（优先选 UAE）
- 按需在此文件直接增删行，不影响其他代码
"""

TOPIC_POOL = [
    # ── UAE (double weight) ──────────────────────────────────────────
    ("BYD Atto 3 2024",      "UAE",          "AE", 18500),
    ("BYD Seal 2024",        "UAE",          "AE", 21000),
    ("Chery Tiggo 8 Pro 2024","UAE",         "AE", 16000),
    ("GAC Aion S 2024",      "UAE",          "AE", 14500),
    ("BYD Han EV 2024",      "UAE",          "AE", 22000),  # UAE second entry
    ("BAIC BJ40 2024",       "UAE",          "AE", 17000),

    # ── Saudi Arabia ─────────────────────────────────────────────────
    ("BYD Atto 3 2024",      "Saudi Arabia", "SA", 18500),
    ("BYD Seal 2024",        "Saudi Arabia", "SA", 21000),
    ("Chery Tiggo 7 Pro 2024","Saudi Arabia","SA", 14000),

    # ── Oman ─────────────────────────────────────────────────────────
    ("GAC Aion S 2024",      "Oman",         "OM", 14500),
    ("BYD Atto 3 2024",      "Oman",         "OM", 18500),

    # ── Qatar ────────────────────────────────────────────────────────
    ("BYD Han EV 2024",      "Qatar",        "QA", 22000),
    ("Chery Tiggo 8 Pro 2024","Qatar",       "QA", 16000),

    # ── Kuwait ───────────────────────────────────────────────────────
    ("BYD Seal 2024",        "Kuwait",       "KW", 21000),
]
