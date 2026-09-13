"""
CNcar YouTube OAuth 授权脚本
=============================
用途：用 @pierpont-006 的 Google 账号做一次性授权，
      生成专属 token 存到 cncar/config/cncar_youtube_token.json。

使用步骤：
  1. 在 GCP Console 下载 OAuth 客户端 JSON，
     改名放到 cncar/config/cncar_youtube_credentials.json
  2. 在终端跑：
       cd short_video_agent
       python3 cncar/auth_youtube.py
  3. 浏览器会自动打开，用 @pierpont-006 的 Google 账号登录并授权
  4. 授权成功后 token 自动写到 cncar/config/cncar_youtube_token.json
  5. 以后 --approve 上传时自动复用此 token，无需再次授权

注意：凭证和 token 文件都在 .gitignore 范围，不会进仓库。
"""

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).parent
CREDS_PATH = _HERE / "config" / "cncar_youtube_credentials.json"
TOKEN_PATH = _HERE / "config" / "cncar_youtube_token.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",  # 用于授权后查频道名核实
]


def main():
    print("\n=== CNcar YouTube 授权 (@pierpont-006) ===\n")

    # ── 检查凭证文件 ─────────────────────────────────────── #
    if not CREDS_PATH.exists():
        print("❌ 未找到凭证文件：")
        print(f"   {CREDS_PATH}")
        print()
        print("请先完成以下步骤：")
        print("  1. 打开 https://console.cloud.google.com/apis/credentials")
        print("  2. 创建或选择一个项目（建议新建项目命名 cncar-youtube）")
        print("  3. 创建凭证 → OAuth 客户端 ID → 类型选【桌面应用】")
        print("  4. 下载 JSON，改名为 cncar_youtube_credentials.json")
        print(f"  5. 把文件放到：{CREDS_PATH}")
        print("  6. 确保该 GCP 项目已启用 YouTube Data API v3")
        print()
        sys.exit(1)

    print(f"✅ 找到凭证文件：{CREDS_PATH}")

    # ── 读 client_id 让用户核实 ──────────────────────────── #
    with open(CREDS_PATH) as f:
        creds_data = json.load(f)
    key = "installed" if "installed" in creds_data else "web"
    client_id = creds_data[key]["client_id"]
    print(f"   Client ID: {client_id[:40]}...")
    print()

    # ── 如果 token 已存在，询问是否重新授权 ─────────────── #
    if TOKEN_PATH.exists():
        ans = input(f"⚠️  {TOKEN_PATH.name} 已存在，重新授权会覆盖它。继续？(y/n) ").strip().lower()
        if ans != "y":
            print("已取消。")
            return
        print()

    # ── 执行 OAuth 流程 ──────────────────────────────────── #
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        print("❌ 缺少依赖，请先安装：")
        print("   pip3 install google-auth-oauthlib google-api-python-client --break-system-packages")
        sys.exit(1)

    print("正在打开浏览器，请用 @pierpont-006 的 Google 账号登录并授权...")
    print("（如果浏览器没有自动打开，复制终端里打印的 URL 手动访问）\n")

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_PATH), SCOPES)
    credentials = flow.run_local_server(port=0, open_browser=True)

    # ── 保存 token ───────────────────────────────────────── #
    token_data = {
        "token":         credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri":     credentials.token_uri,
        "client_id":     credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes":        list(credentials.scopes),
    }
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(TOKEN_PATH, "w") as f:
        json.dump(token_data, f, indent=2)

    print(f"\n✅ Token 已保存：{TOKEN_PATH}")

    # ── 核实频道名 ───────────────────────────────────────── #
    print("\n正在核实授权的 YouTube 频道...\n")
    try:
        yt = build("youtube", "v3", credentials=credentials)
        resp = yt.channels().list(part="snippet", mine=True).execute()
        channels = resp.get("items", [])
        if channels:
            ch = channels[0]["snippet"]
            print(f"  频道名称：{ch['title']}")
            print(f"  频道 ID ：{channels[0]['id']}")
            custom = ch.get("customUrl", "(未设置自定义URL)")
            print(f"  自定义URL：{custom}")
            print()
            if "pierpont" in custom.lower() or "pierpont" in ch["title"].lower():
                print("✅ 确认是 @pierpont-006，凭证配置正确！")
            else:
                print("⚠️  频道名称与 @pierpont-006 不符，请核实！")
                print("   如果登录了错误的 Google 账号，请删除 token 文件重新授权。")
        else:
            print("⚠️  未找到频道，请确认该账号有 YouTube 频道。")
    except Exception as e:
        print(f"⚠️  频道核实失败（不影响 token 有效性）: {e}")

    print()
    print("完成。现在可以跑：")
    print("  python3 cncar/main.py --approve <ID>")


if __name__ == "__main__":
    main()
