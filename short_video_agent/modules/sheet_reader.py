"""Google Sheets 素材库读取器

支持两种接入方式：
  1. Service Account（需要 gsheets_credentials.json）— 完整读写权限
  2. 公开表格 CSV fallback（表格设置为"任何人可查看"）— 只读，无需凭证

行号说明（gspread 约定）：
  - get_all_values() 返回所有行，包含表头（index 0 = 表头 = 第 1 行）
  - 数据行 _row_number 从 2 起（第 1 行是表头），直接用于 update_cell()
"""
import csv
import io
import os
import random
from datetime import datetime

import requests

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",       # 可读写
    "https://www.googleapis.com/auth/drive.readonly",
]


class SheetReader:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.direction = cfg["direction"]
        self._client = None
        self._sheet = None
        self._cached_rows = None   # 同次运行缓存，避免重复拉取

    # ------------------------------------------------------------------ #
    # 连接                                                                  #
    # ------------------------------------------------------------------ #

    def _connect_service_account(self):
        import gspread
        from google.oauth2.service_account import Credentials

        creds_path = self.cfg["api"]["gsheets_credentials"]
        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        self._client = gspread.authorize(creds)
        sheet_cfg = self.direction["google_sheet"]
        wb = self._client.open_by_key(sheet_cfg["spreadsheet_id"])
        self._sheet = wb.worksheet(sheet_cfg["worksheet_name"])

    def _read_public_csv(self) -> list[dict]:
        """从公开表格读取 CSV（表格需设置为"任何人可查看"）"""
        sheet_cfg = self.direction["google_sheet"]
        sid = sheet_cfg["spreadsheet_id"]
        sheet_name = sheet_cfg["worksheet_name"]
        url = (
            f"https://docs.google.com/spreadsheets/d/{sid}"
            f"/gviz/tq?tqx=out:csv&sheet={requests.utils.quote(sheet_name)}"
        )
        for attempt in range(3):
                try:
                    resp = requests.get(url, timeout=30)
                    break
                except Exception as e:
                    if attempt == 2:
                        raise
                    import time; time.sleep(5)
        if resp.status_code != 200:
            raise RuntimeError(
                f"无法读取 Google Sheet (HTTP {resp.status_code})。\n"
                "请确认表格已设置为【任何人可查看】，或提供 Service Account 凭证。"
            )
        reader = csv.DictReader(io.StringIO(resp.text))
        return list(reader)

    # ------------------------------------------------------------------ #
    # 核心：带行号的数据获取（缓存）                                            #
    # ------------------------------------------------------------------ #

    def _get_rows(self) -> list[dict]:
        """
        拉取 Sheet 所有数据行并缓存。每行 dict 包含：
          - 列字母 → 单元格值（如 "D" → 文案正文）
          - "_row_number" → gspread 1-based 行号（表头=1，第一数据行=2）
        """
        if self._cached_rows is not None:
            return self._cached_rows

        if not self._sheet:
            self._connect_service_account()

        cols = self.direction["google_sheet"]["columns"]
        src_idx   = self._col_letter_to_num(cols["source_text"]) - 1   # 0-based
        theme_idx = self._col_letter_to_num(cols["theme"])       - 1
        used_idx  = self._col_letter_to_num(cols["used"])        - 1
        n_need    = max(src_idx, theme_idx, used_idx) + 1

        all_values = self._sheet.get_all_values()   # index 0 = 表头 = 第 1 行
        rows = []
        for i, raw in enumerate(all_values[1:], start=2):   # 第一数据行 = 第 2 行
            padded = list(raw) + [""] * max(0, n_need - len(raw))
            rows.append({
                cols["source_text"]: padded[src_idx],
                cols["theme"]:       padded[theme_idx],
                cols["used"]:        padded[used_idx],
                "_row_number":       i,                      # 直接用于 update_cell
            })

        self._cached_rows = rows
        return rows

    # ------------------------------------------------------------------ #
    # 主题轮换选行                                                           #
    # ------------------------------------------------------------------ #

    def pick_row(self) -> dict:
        """
        主题轮换选行：
          1. unused  = F 列为空的行
          2. recent_themes = 按 F 列日期倒序、最近 N 行的主题集合
          3. candidates = unused 中主题不在 recent_themes 的行
          4. 选中 = random.choice(candidates)；若空则 random.choice(unused)
          5. 若 unused 为空：复用 F 列日期最早（最久未用）的行，打印警告

        返回含 _row_number、source_text 列、theme 列的行 dict。
        """
        rows = self._get_rows()
        cols = self.direction["google_sheet"]["columns"]
        used_key  = cols["used"]
        theme_key = cols["theme"]
        N = self.direction["google_sheet"].get("recent_themes_count", 3)

        unused    = [r for r in rows if not r[used_key].strip()]
        used_rows = [r for r in rows if r[used_key].strip()]

        # ── 库存用尽兜底 ──────────────────────────────────────────────────
        if not unused:
            if not used_rows:
                raise ValueError("素材库为空（无数据行），请先在 Google Sheet 中添加素材")
            print("  [Sheet] ⚠️  库存已空，开始复用最久未用（保证频道不断更）")
            used_rows.sort(key=lambda r: self._parse_date(r[used_key]))
            return used_rows[0]

        # ── 近 N 条已用主题 ──────────────────────────────────────────────
        used_sorted   = sorted(used_rows, key=lambda r: self._parse_date(r[used_key]), reverse=True)
        recent_themes = {r[theme_key].strip() for r in used_sorted[:N] if r[theme_key].strip()}

        if recent_themes:
            print(f"  [Sheet] 最近{N}次已用主题: {sorted(recent_themes)}")

        # ── 候选：主题不在最近列表 ─────────────────────────────────────────
        candidates = [r for r in unused if r[theme_key].strip() not in recent_themes]
        if not candidates:
            print("  [Sheet] 所有未用行的主题均在最近列表中，回退到随机 unused")
            candidates = unused

        selected = random.choice(candidates)
        print(
            f"  [Sheet] 选中行{selected['_row_number']} "
            f"| 主题: {selected.get(theme_key, '?')} "
            f"| 文本: {str(selected.get(cols['source_text'], ''))[:30]}..."
        )
        return selected

    # ------------------------------------------------------------------ #
    # 公开接口                                                               #
    # ------------------------------------------------------------------ #

    def get_unused_material(self, count: int = 3) -> list[dict]:
        """
        取 count 条未使用素材。
        - Service Account 模式：第一条用主题轮换 pick_row()，其余随机补足；
          每条含 _row_number。
        - 公开 CSV 模式（只读）：随机取，无 _row_number。
        """
        creds_path = self.cfg["api"].get("gsheets_credentials", "")
        cols       = self.direction["google_sheet"]["columns"]

        if os.path.exists(creds_path):
            # ── Service Account 模式 ────────────────────────────────────
            if not self._sheet:
                self._connect_service_account()

            primary  = self.pick_row()                  # 主题轮换首选
            all_rows = self._get_rows()                 # 已缓存

            unused    = [r for r in all_rows if not r[cols["used"]].strip()]
            remaining = [r for r in unused if r["_row_number"] != primary["_row_number"]]
            extras    = (
                random.sample(remaining, min(count - 1, len(remaining)))
                if count > 1 and remaining
                else []
            )

            selected   = [primary] + extras
            unused_cnt = len(unused)
            total_cnt  = len(all_rows)
        else:
            # ── 公开 CSV 模式（只读）────────────────────────────────────
            print("  [Sheet] 未找到 Service Account 凭证，尝试公开 CSV 读取...")
            rows = self._read_public_csv()
            rows = self._remap_csv_columns(rows, cols)
            unused = [
                r for r in rows
                if str(r.get(cols["used"], "")).strip().lower()
                not in ("yes", "1", "true", "已用")
            ]
            if not unused:
                raise ValueError("素材库已全部使用完，请补充新素材")
            selected   = random.sample(unused, min(count, len(unused)))
            unused_cnt = len(unused)
            total_cnt  = len(rows)

        print(
            f"  [Sheet] 共 {total_cnt} 条素材，未用 {unused_cnt} 条，"
            f"本次取 {len(selected)} 条"
        )
        return selected

    def mark_as_used(self, row_number: int, date_str: str = None):
        """
        把 date_str（YYYY-MM-DD）写入指定行的 F 列（已用标记）。
        row_number：gspread 1-based 行号（表头=1，第一数据行=2）。
        date_str 默认为今天。
        需要 Service Account；只读模式下会打印提示并跳过。
        """
        creds_path = self.cfg["api"].get("gsheets_credentials", "")
        if not os.path.exists(creds_path):
            print("  [Sheet] ⚠️  跳过标记（只读模式，无 Service Account 凭证）")
            return
        if not self._sheet:
            self._connect_service_account()

        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        cols    = self.direction["google_sheet"]["columns"]
        col_num = self._col_letter_to_num(cols["used"])       # "F" → 6
        self._sheet.update_cell(row_number, col_num, date_str)
        print(f"  [Sheet] ✅ 已标记行{row_number} 列{cols['used']} = {date_str}")

        self._cached_rows = None   # 失效缓存，下次重新拉

    # ------------------------------------------------------------------ #
    # 工具                                                                  #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        """YYYY-MM-DD → datetime；解析失败返回 datetime.min（视为最旧）"""
        try:
            return datetime.strptime(date_str.strip(), "%Y-%m-%d")
        except Exception:
            return datetime.min

    @staticmethod
    def _remap_csv_columns(rows: list[dict], cols: dict) -> list[dict]:
        """
        CSV 读出的列名是表头文字；用列字母序号做位置映射，统一 key 为列字母。
        """
        if not rows:
            return []
        result = []
        for row in rows:
            values = list(row.values())
            new_row = {
                letter: val
                for letter, val in zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", values)
            }
            result.append(new_row)
        return result

    @staticmethod
    def _col_letter_to_num(letter: str) -> int:
        """列字母 → gspread 1-based 列号（A→1, F→6）"""
        return ord(letter.upper()) - ord("A") + 1
