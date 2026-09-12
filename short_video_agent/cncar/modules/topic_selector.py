"""CNcar 选题器

逻辑：
  1. 读工作表2（公开 CSV），提取已用的 car_model×destination 组合
  2. 从候选池里排除最近 14 天内已写过的组合
  3. 剩余里随机选一条（UAE 已在候选池里双权重）
  4. 如全部最近都用过，复用候选池里最久没选的一条（避免卡死）
"""
import csv
import io
import random
from datetime import datetime, timedelta
from pathlib import Path

import requests

_HERE = Path(__file__).parent.parent


def _read_sheet_rows(cfg: dict) -> list[dict]:
    """读工作表2公开 CSV，返回已有行列表"""
    direction = cfg["direction"]
    sheet_cfg = direction["google_sheet"]
    sid = sheet_cfg["spreadsheet_id"]
    sheet_name = sheet_cfg["worksheet_name"]
    url = (
        f"https://docs.google.com/spreadsheets/d/{sid}"
        f"/gviz/tq?tqx=out:csv&sheet={requests.utils.quote(sheet_name)}"
    )
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code != 200:
            return []
        reader = csv.DictReader(io.StringIO(resp.text))
        return list(reader)
    except Exception:
        return []


def _parse_date(s: str) -> datetime | None:
    s = s.strip() if s else ""
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def select_topic(cfg: dict) -> tuple[str, str, str, int]:
    """
    返回 (car_model, destination, country_iso2, fob_usd_reference)
    优先选近 14 天内未写过的组合；全部都写过则选最久未用的。
    """
    from cncar.config.topics import TOPIC_POOL

    rows = _read_sheet_rows(cfg)
    cutoff = datetime.now() - timedelta(days=14)

    # 收集近 14 天内已写过的 (car_model, destination) 组合
    # 工作表列：A=car_model, B=destination, H=used(日期)
    # CSV DictReader 的 key 是表头第一行，这里用位置读取
    recent_combos: set[tuple[str, str]] = set()
    for row in rows:
        values = list(row.values())
        if len(values) < 2:
            continue
        car = (values[0] or "").strip()
        dest = (values[1] or "").strip()
        used_str = values[7] if len(values) > 7 else ""
        used_date = _parse_date(used_str)
        if used_date and used_date >= cutoff:
            recent_combos.add((car, dest))

    # 候选池里过滤掉近期已用
    available = [t for t in TOPIC_POOL if (t[0], t[1]) not in recent_combos]

    if available:
        chosen = random.choice(available)
    else:
        # 全部都近期用过 → 选最久未用（从sheet里找最早日期的那条）
        print("  [选题] 所有候选近 14 天内都已用过，复用最久未选的一条")
        used_dates: dict[tuple[str, str], datetime] = {}
        for row in rows:
            values = list(row.values())
            if len(values) < 2:
                continue
            car = (values[0] or "").strip()
            dest = (values[1] or "").strip()
            used_date = _parse_date(values[7] if len(values) > 7 else "")
            if used_date:
                key = (car, dest)
                if key not in used_dates or used_date < used_dates[key]:
                    used_dates[key] = used_date
        pool_in_sheet = [(t, used_dates.get((t[0], t[1]), datetime.min)) for t in TOPIC_POOL]
        chosen = min(pool_in_sheet, key=lambda x: x[1])[0]

    return chosen  # (car_model, destination, country_iso2, fob_usd)
