"""Google Sheets 素材库读取器
支持两种接入方式：
  1. Service Account（需要 gsheets_credentials.json）— 完整读写权限
  2. 公开表格 CSV fallback（表格设置为"任何人可查看"）— 只读，无需凭证
"""
import csv
import io
import os
import random

import requests

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]


class SheetReader:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.direction = cfg["direction"]
        self._client = None
        self._sheet = None

    # ------------------------------------------------------------------ #
    # 连接（优先 Service Account，fallback 公开 CSV）                       #
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
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            raise RuntimeError(
                f"无法读取 Google Sheet (HTTP {resp.status_code})。\n"
                "请确认表格已设置为【任何人可查看】，或提供 Service Account 凭证。"
            )
        reader = csv.DictReader(io.StringIO(resp.text))
        return list(reader)

    # ------------------------------------------------------------------ #
    # 公开接口                                                              #
    # ------------------------------------------------------------------ #

    def get_unused_material(self, count: int = 3) -> list[dict]:
        """随机取 count 条未使用的素材（自动选择接入方式）"""
        creds_path = self.cfg["api"].get("gsheets_credentials", "")
        cols = self.direction["google_sheet"]["columns"]

        if os.path.exists(creds_path):
            # Service Account 模式（完整权限）
            if not self._sheet:
                self._connect_service_account()
            rows = self._sheet.get_all_records()
        else:
            # 公开 CSV 模式（只读）
            print("  [Sheet] 未找到 Service Account 凭证，尝试公开 CSV 读取...")
            rows = self._read_public_csv()
            # CSV 列名是第一行的表头文字，需要映射到列字母
            rows = self._remap_csv_columns(rows, cols)

        unused = [
            r for r in rows
            if str(r.get(cols["used"], "")).strip().lower() not in ("yes", "1", "true", "已用")
        ]
        if not unused:
            raise ValueError("素材库已全部使用完，请补充新素材")

        selected = random.sample(unused, min(count, len(unused)))
        print(f"  [Sheet] 读取成功，共 {len(rows)} 条素材，未用 {len(unused)} 条，本次取 {len(selected)} 条")
        return selected

    def mark_as_used(self, row_index: int):
        """标记某行已使用（需要 Service Account）"""
        creds_path = self.cfg["api"].get("gsheets_credentials", "")
        if not os.path.exists(creds_path):
            print("  [Sheet] 跳过标记（只读模式，无 Service Account 凭证）")
            return
        if not self._sheet:
            self._connect_service_account()
        cols = self.direction["google_sheet"]["columns"]
        self._sheet.update_cell(row_index + 1, self._col_letter_to_num(cols["used"]), "已用")

    # ------------------------------------------------------------------ #
    # 工具                                                                  #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _remap_csv_columns(rows: list[dict], cols: dict) -> list[dict]:
        """
        CSV 读出来的列名是表头文字（如 "素材原文"），而我们的 cols 是列字母（"A","B"...）。
        做一个字母→位置的映射，用位置来取值。
        """
        if not rows:
            return []
        headers = list(rows[0].keys())
        col_map = {
            cols["source_text"]: headers[ord(cols["source_text"].upper()) - ord("A")]
            if len(headers) > ord(cols["source_text"].upper()) - ord("A") else None,
        }
        # 重新构建每行，使用列字母作为 key
        result = []
        for row in rows:
            header_list = list(row.values())
            new_row = {}
            for letter, val in zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", header_list):
                new_row[letter] = val
            result.append(new_row)
        return result

    @staticmethod
    def _col_letter_to_num(letter: str) -> int:
        return ord(letter.upper()) - ord("A") + 1
