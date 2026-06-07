#!/usr/bin/env python3
"""
Google Sheet 连通性、主题轮换、已用标记 验证工具

用法:
  # Step 0: 查看 Service Account 邮箱（把表格共享给它"编辑"权限）
  python tools/sheet_tool.py --mode email

  # dry-run: 打印 unused 数量、最近主题、本次选哪行
  python tools/sheet_tool.py --mode dry_run

  # 单测 mark_used: 写入测试日期 → 读回确认 → 清空（验证 scope 权限）
  python tools/sheet_tool.py --mode mark_test --row 2
"""
import argparse
import json
import os
import sys

# 确保从项目根目录导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.config_loader import load_config
from modules.sheet_reader import SheetReader


# ─────────────────────────────────────────────────────────────────────────────

def cmd_email(cfg):
    """打印 Service Account 的 client_email，用于把表格共享给它"""
    creds_path = cfg["api"].get("gsheets_credentials", "")
    if not os.path.exists(creds_path):
        print(f"❌ 未找到凭证文件: {creds_path}")
        print()
        print("请先完成以下步骤：")
        print("  1. 访问 https://console.cloud.google.com/")
        print("  2. 创建项目（或选已有项目）→ 启用 Google Sheets API")
        print("  3. IAM → 服务帐号 → 新建服务帐号")
        print("  4. 创建密钥 → JSON → 下载")
        print(f"  5. 把下载的 JSON 文件放到: {creds_path}")
        print("  6. 再次运行 --mode email 查看邮箱，然后把表格共享给该邮箱（编辑权限）")
        sys.exit(1)

    with open(creds_path) as f:
        creds_data = json.load(f)
    email = creds_data.get("client_email", "未找到 client_email 字段")
    print(f"✅ Service Account 邮箱: {email}")
    print()
    print("下一步：")
    print("  打开 Google Sheet → 右上角「共享」→ 把上面邮箱添加为「编辑者」")
    print("  然后运行: python tools/sheet_tool.py --mode dry_run")


# ─────────────────────────────────────────────────────────────────────────────

def cmd_dry_run(cfg):
    """打印当前 unused 条数、最近已用主题、本次选哪一行（不实际写入）"""
    creds_path = cfg["api"].get("gsheets_credentials", "")
    cols = cfg["direction"]["google_sheet"]["columns"]
    N    = cfg["direction"]["google_sheet"].get("recent_themes_count", 3)

    if not os.path.exists(creds_path):
        print("⚠️  未找到 Service Account 凭证，改用公开 CSV（只读，无行号）")
        reader = SheetReader(cfg)
        materials = reader.get_unused_material(count=1)
        m = materials[0]
        print(f"  选中文本: {str(m.get(cols['source_text'], ''))[:60]}")
        return

    # Service Account 模式
    reader = SheetReader(cfg)
    reader._connect_service_account()
    all_rows = reader._get_rows()

    used_key  = cols["used"]
    theme_key = cols["theme"]

    unused    = [r for r in all_rows if not r[used_key].strip()]
    used_rows = [r for r in all_rows if r[used_key].strip()]

    print(f"总素材   : {len(all_rows)} 条")
    print(f"未用     : {len(unused)} 条")
    print(f"已用     : {len(used_rows)} 条")
    print()

    # 最近 N 条已用主题
    from modules.sheet_reader import SheetReader as SR
    used_sorted   = sorted(used_rows, key=lambda r: SR._parse_date(r[used_key]), reverse=True)
    recent_themes = [r[theme_key].strip() for r in used_sorted[:N] if r[theme_key].strip()]
    print(f"近{N}次已用主题: {recent_themes}")
    print()

    if not unused:
        print("⚠️  库存已空，将从已用行中选最久未用的")
        used_sorted2 = sorted(used_rows, key=lambda r: SR._parse_date(r[used_key]))
        sel = used_sorted2[0]
    else:
        # 候选集
        recent_set = set(r[theme_key].strip() for r in used_sorted[:N] if r[theme_key].strip())
        candidates = [r for r in unused if r[theme_key].strip() not in recent_set]
        if not candidates:
            candidates = unused
        import random
        sel = random.choice(candidates)

    src_preview = str(sel.get(cols["source_text"], ""))[:60]
    print(f"本次会选:")
    print(f"  行号  : {sel.get('_row_number', '无')}")
    print(f"  主题  : {sel.get(theme_key, '?')}")
    print(f"  文本  : {src_preview}...")
    print()
    print("（dry-run 不写入 Sheet，运行 --mode mark_test 验证写入权限）")


# ─────────────────────────────────────────────────────────────────────────────

def cmd_mark_test(cfg, row_number: int):
    """
    单测 mark_used：
      1. 向指定行 F 列写入 '2099-12-31'（明显测试日期）
      2. 读回确认
      3. 清空该单元格（还原）
    """
    creds_path = cfg["api"].get("gsheets_credentials", "")
    if not os.path.exists(creds_path):
        print(f"❌ 未找到凭证文件: {creds_path}")
        print("   请先完成 Service Account 创建并共享表格。运行 --mode email 查看步骤。")
        sys.exit(1)

    cols     = cfg["direction"]["google_sheet"]["columns"]
    used_key = cols["used"]
    test_date = "2099-12-31"

    reader = SheetReader(cfg)
    reader._connect_service_account()

    print(f"测试: 向行{row_number} 列{used_key} 写入 '{test_date}'...")
    reader.mark_as_used(row_number, test_date)

    # 读回验证
    reader._cached_rows = None           # 强制重新拉取
    all_rows = reader._get_rows()
    target = next((r for r in all_rows if r["_row_number"] == row_number), None)

    if target is None:
        print(f"❌ 未找到行 {row_number}（表格共有 {len(all_rows)} 条数据行）")
        sys.exit(1)

    actual = target.get(used_key, "")
    if actual.strip() == test_date:
        print(f"✅ 写入成功！读回值: '{actual}'")
    else:
        print(f"❌ 写入可能失败，读回值: '{actual}'（期望 '{test_date}'）")
        sys.exit(1)

    # 清空还原
    col_num = SheetReader._col_letter_to_num(used_key)
    reader._sheet.update_cell(row_number, col_num, "")
    print(f"✅ 已清空行{row_number}列{used_key}（还原完毕）")
    print()
    print("结论：Service Account 读写权限正常，主题轮换和已用标记可正常工作 🎉")


# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Google Sheet 连通性与主题轮换测试")
    parser.add_argument(
        "--mode",
        choices=["email", "dry_run", "mark_test"],
        default="dry_run",
        help="email=查看SA邮箱 | dry_run=打印选行情况 | mark_test=测试写入权限",
    )
    parser.add_argument(
        "--row",
        type=int,
        default=2,
        help="mark_test 时要写入的行号（gspread 1-based，第一数据行=2）",
    )
    args = parser.parse_args()

    cfg = load_config()

    if args.mode == "email":
        cmd_email(cfg)
    elif args.mode == "dry_run":
        cmd_dry_run(cfg)
    elif args.mode == "mark_test":
        cmd_mark_test(cfg, args.row)


if __name__ == "__main__":
    main()
