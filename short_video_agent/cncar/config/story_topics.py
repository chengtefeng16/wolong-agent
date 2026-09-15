"""CNcar 故事线选题池

每条记录：(topic_id, mood, angle, keywords)
- mood: tense / neutral / uplift
- angle: 给 Gemini 的故事角度提示
- keywords: Pexels 图片主题提示词（写进旁白里自然带出）

目标受众：海外华人，正在从中国进口二手车或电动车到海湾/中东地区
"""

STORY_TOPICS = [
    # ── 骗局 / 风险警示（tense）────────────────────────────────────────
    (
        "scam_deposit",
        "tense",
        "A buyer paid a $12,000 deposit to a car dealer who then vanished. "
        "Focus on: what warning signs they missed, which documents to demand before wiring any money, "
        "and what buyers can check independently to avoid this.",
        ["scam", "dealer", "contract", "money", "fraud"],
    ),
    (
        "fake_certificate",
        "tense",
        "A car imported from China was detained at customs because one certificate was missing. "
        "The buyer lost months and thousands in storage fees. "
        "Focus on: which documents are required, why one missing paper can freeze everything, "
        "and how to check before shipping.",
        ["customs", "certificate", "shipping", "port", "document"],
    ),
    (
        "grey_market_risk",
        "tense",
        "A buyer bought a 'China-spec' EV in the Gulf that had no local warranty. "
        "The battery failed 8 months later — repair cost $6,000 out of pocket. "
        "Focus on: the difference between grey-market and official import, "
        "what specific questions to ask and documents to check before buying.",
        ["warranty", "EV", "battery", "grey market", "repair"],
    ),
    (
        "vat_surprise",
        "tense",
        "An importer quoted $18,000 landed. The real cost after VAT, duty and port fees was $24,000. "
        "Focus on: which costs are commonly omitted from quotes, "
        "how buyers can calculate the true landed cost before committing.",
        ["VAT", "duty", "landed cost", "import tax", "hidden fees"],
    ),

    # ── 市场情报 / 教育（neutral）──────────────────────────────────────
    (
        "byd_gulf_surge",
        "neutral",
        "BYD sales in the Gulf jumped 140% last year. "
        "Focus on: why Gulf buyers are choosing Chinese EVs, "
        "which models are most popular, what the real landed costs look like.",
        ["BYD", "EV", "Gulf", "electric car", "China export"],
    ),
    (
        "roro_vs_container",
        "neutral",
        "Most people don't know there are two ways to ship a car from China to the Gulf — "
        "RoRo and container. One is cheaper. One is safer. "
        "Focus on: what each method means, the real cost and risk difference, "
        "and how buyers can decide which fits their situation.",
        ["RoRo", "shipping", "container", "freight", "port"],
    ),
    (
        "dealer_verification",
        "neutral",
        "Not all car dealers in China are licensed to export. "
        "Focus on: how to check if a dealer is registered, "
        "what export license to ask for, three questions every buyer must ask.",
        ["dealer", "license", "verification", "export", "China"],
    ),

    # ── 成功故事 / 励志（uplift）──────────────────────────────────────
    (
        "smart_buyer_win",
        "uplift",
        "A buyer in Dubai saved $4,200 on a BYD Atto 3 by using CNcar's cost report "
        "to negotiate with the dealer. "
        "Focus on: how knowing the real landed cost gives buyers negotiating power, "
        "the exact steps they took, what to do with the report.",
        ["BYD", "Dubai", "negotiation", "savings", "cost report"],
    ),
    (
        "first_time_importer",
        "uplift",
        "A first-time importer successfully brought a Chery Tiggo 8 Pro from China to Oman "
        "in 47 days with zero surprises. "
        "Focus on: the step-by-step process they followed, "
        "how they found a verified dealer, what CNcar's report told them.",
        ["Chery", "Oman", "import", "first time", "success"],
    ),
]
