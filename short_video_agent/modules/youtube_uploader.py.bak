"""YouTube Data API v3 上传器

首次运行会弹出浏览器进行 OAuth 授权，之后 token 缓存在
config/youtube_token.json，无需再次授权。
"""
import os
import pickle
import time

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload


SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# 可重试的 HTTP 状态码
RETRIABLE_STATUS_CODES = {500, 502, 503, 504}
MAX_RETRIES = 5


class YouTubeUploader:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.yt_cfg = cfg["direction"]["youtube"]
        self.credentials_path = cfg["api"]["youtube_credentials"]
        self.token_path = cfg["api"]["youtube_token"]
        self._service = None

    # ------------------------------------------------------------------ #
    # 认证                                                                  #
    # ------------------------------------------------------------------ #

    def authenticate(self):
        """OAuth2 认证（首次运行弹出浏览器，之后自动续期）"""
        creds = None

        if os.path.exists(self.token_path):
            with open(self.token_path, "rb") as f:
                creds = pickle.load(f)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("  [YouTube] 刷新 OAuth Token...")
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"未找到 YouTube OAuth 凭证文件：{self.credentials_path}\n"
                        "请按文档说明在 Google Cloud Console 创建 OAuth 客户端 ID，\n"
                        "下载后重命名为 youtube_credentials.json 放到 config/ 目录。"
                    )
                print("  [YouTube] 首次授权，即将打开浏览器...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=8080, open_browser=True)

            with open(self.token_path, "wb") as f:
                pickle.dump(creds, f)
            print(f"  [YouTube] Token 已保存: {self.token_path}")

        self._service = build("youtube", "v3", credentials=creds)
        print("  [YouTube] 认证成功 ✅")

    # ------------------------------------------------------------------ #
    # 上传                                                                  #
    # ------------------------------------------------------------------ #

    def upload(self, video_path: str, script_data: dict, privacy: str = None) -> str:
        """
        上传视频，返回 YouTube video_id。
        privacy: "private" | "unlisted" | "public"（默认取 config 里的值）
        """
        if not self._service:
            self.authenticate()

        privacy = privacy or self.yt_cfg.get("privacy", "private")
        tags_from_script = script_data.get("tags", [])
        first_tag = tags_from_script[0] if tags_from_script else "佛法"

        title = self.yt_cfg["title_template"].format(
            title=script_data.get("title", ""),
        )
        description = self.yt_cfg["description_template"].format(
            cover_quote=script_data.get("cover_quote", ""),
            theme=first_tag,
        )
        tags = self.yt_cfg["tags"] + tags_from_script

        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": list(dict.fromkeys(tags))[:500],   # 去重
                "categoryId": self.yt_cfg["category_id"],
                "defaultLanguage": self.yt_cfg["default_language"],
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False,
            },
        }

        media = MediaFileUpload(
            video_path,
            mimetype="video/mp4",
            resumable=True,
            chunksize=8 * 1024 * 1024,  # 8MB chunks
        )
        request = self._service.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media,
        )

        print(f"  [YouTube] 开始上传: 「{title}」")
        print(f"  [YouTube] 隐私设置: {privacy}")
        video_id = self._resumable_upload(request)
        url = f"https://youtu.be/{video_id}"
        print(f"  [YouTube] ✅ 上传完成: {url}")
        return video_id

    def _resumable_upload(self, request) -> str:
        """断点续传，自动重试"""
        response = None
        retry = 0

        while response is None:
            try:
                status, response = request.next_chunk()
                if status:
                    pct = int(status.progress() * 100)
                    bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
                    print(f"\r  [YouTube] [{bar}] {pct}%", end="", flush=True)
            except HttpError as e:
                if e.resp.status in RETRIABLE_STATUS_CODES:
                    retry += 1
                    if retry > MAX_RETRIES:
                        raise
                    wait = 2 ** retry
                    print(f"\n  [YouTube] 服务器错误 {e.resp.status}，{wait}秒后重试...")
                    time.sleep(wait)
                else:
                    raise

        print()  # 换行
        return response["id"]
