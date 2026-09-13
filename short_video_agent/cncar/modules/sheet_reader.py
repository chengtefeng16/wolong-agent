"""CNcar Google Sheets 素材库读取器（工作表2）

列结构（A-H）：
  A car_model        车型
  B destination      目的国
  C landed_cost_usd  落地成本 USD
  D report_url       CNcar 报告链接
  E copy_en          英文文案（预填则直接用，空则 AI 生成）
  F copy_ar          阿语文案（预填则直接用，空则 AI 生成）
  G cover_prompt     封面图提示词
  H used             已用日期 YYYY-MM-DD（空=未用）
"""
import csv
import io
import os
import random
from datetime import datetime

import requests

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

COLUMNS = ["car_model", "destination", "landed_cost_usd", "report_url",
           "copy_en", "copy_ar", "cover_prompt", "used"]


class CNcarSheetReader:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.direction = cfg["direction"]
        self._client = None
        self._sheet = None
        self._cached_rows = None

    # ------------------------------------------------------------------ #

    def _connect_service_account(self):
        import gspread
        from google.oauth2.service_account import Credentials

        creds_path = self.cfg["api"].get("gsheets_credentials", "")
        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        self._client = gspread.authorize(creds)
        sheet_cfg = self.direction["google_sheet"]
        wb = self._client.open_by_key(sheet_cfg["spreadsheet_id"])
        self._sheet = wb.worksheet(sheet_cfg["worksheet_name"])

    def _read_public_csv(self) -> list[dict]:
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
            except Exception:
                if attempt == 2:
                    raise
                import time; time.sleep(5)
        if resp.status_code != 200:
            raise RuntimeError(
                f"无法读取 Google Sheet (HTTP {resp.status_code})。\n"
                "请确认表格已设置为【任何人可查看】。"
            )
        reader = csv.DictReader(io.StringIO(resp.text))
        return list(reader)

    # ------------------------------------------------------------------ #

    def _get_rows(self) -> list[dict]:
        if self._cached_rows is not None:
            return self._cached_rows

        if not self._sheet:
            self._connect_service_account()

        all_values = self._sheet.get_all_values()
        rows = []
        for i, raw in enumerate(all_values[1:], start=2):
            padded = list(raw) + [""] * max(0, 8 - len(raw))
            row = {col: padded[j] for j, col in enumerate(COLUMNS)}
            row["_row_number"] = i
            rows.append(row)

        self._cached_rows = rows
        return rows

    def _remap_csv_rows(self, raw_rows: list[dict]) -> list[dict]:
        result = []
        for row in raw_rows:
            values = list(row.values())
            padded = values + [""] * max(0, 8 - len(values))
            r = {col: padded[j] for j, col in enumerate(COLUMNS)}
            result.append(r)
        return result

    # ------------------------------------------------------------------ #

    def get_unused_material(self, count: int = 1) -> list[dict]:
        creds_path = self.cfg["api"].get("gsheets_credentials", "")

        if os.path.exists(creds_path):
            if not self._sheet:
                self._connect_service_account()
            rows = self._get_rows()
        else:
            print("  [CNcar Sheet] 未找到 Service Account，尝试公开 CSV 读取...")
            raw = self._read_public_csv()
            rows = self._remap_csv_rows(raw)

        unused = [r for r in rows if not r["used"].strip()]

        if not unused:
            # 库存用尽：复用最久未用
            used_rows = [r for r in rows if r["used"].strip()]
            if not used_rows:
                raise ValueError("CNcar 素材库为空，请先在工作表2添加数据")
            print("  [CNcar Sheet] ⚠️  库存已空，复用最久未用行")
            used_rows.sort(key=lambda r: self._parse_date(r["used"]))
            unused = [used_rows[0]]

        # 主题轮换：避免连续相同目的国
        N = self.direction["google_sheet"].get("recent_themes_count", 3)
        used_rows = [r for r in rows if r["used"].strip()]
        used_sorted = sorted(used_rows, key=lambda r: self._parse_date(r["used"]), reverse=True)
        recent_destinations = {r["destination"].strip() for r in used_sorted[:N] if r["destination"].strip()}

        candidates = [r for r in unused if r["destination"].strip() not in recent_destinations]
        if not candidates:
            candidates = unused

        selected = random.sample(candidates, min(count, len(candidates)))
        print(
            f"  [CNcar Sheet] 共{len(rows)}条，未用{len(unused)}条，"
            f"本次取{len(selected)}条"
        )
        for r in selected:
            print(f"    → {r['car_model']} → {r['destination']} (${r['landed_cost_usd']})")
        return selected

    def mark_as_used(self, row_number: int, date_str: str = None):
        creds_path = self.cfg["api"].get("gsheets_credentials", "")
        if not os.path.exists(creds_path):
            print("  [CNcar Sheet] ⚠️  跳过标记（只读模式）")
            return
        if not self._sheet:
            self._connect_service_account()

        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        # H 列 = 列号 8
        self._sheet.update_cell(row_number, 8, date_str)
        print(f"  [CNcar Sheet] ✅ 已标记行{row_number} H列 = {date_str}")
        self._cached_rows = None

    def append_material_row(self, car_model: str, destination: str,
                            landed_cost_usd: str, report_url: str) -> int:
        """在工作表2末尾追加一行（E-H留空），返回新行号"""
        if not self._sheet:
            self._connect_service_account()
        row = [car_model, destination, landed_cost_usd, report_url, "", "", "", ""]
        self._sheet.append_row(row, value_input_option="USER_ENTERED")
        new_row_num = len(self._sheet.get_all_values())
        print(f"  [CNcar Sheet] ✅ 已写入第{new_row_num}行：{car_model} → {destination} ${landed_cost_usd}")
        self._cached_rows = None
        return new_row_num

    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        try:
            return datetime.strptime(date_str.strip(), "%Y-%m-%d")
        except Exception:
            return datetime.min
