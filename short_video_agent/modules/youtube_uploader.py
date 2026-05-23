"""YouTube Data API v3 上传器"""
import os
import pickle
from pathlib import Path

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


class YouTubeUploader:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.yt_cfg = cfg["direction"]["youtube"]
        self.credentials_path = cfg["api"]["youtube_credentials"]
        self.token_path = cfg["api"]["youtube_token"]
        self._service = None

    def authenticate(self):
        """OAuth2 认证（首次运行会弹出浏览器）"""
        creds = None
        if os.path.exists(self.token_path):
            with open(self.token_path, "rb") as f:
                creds = pickle.load(f)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)
            with open(self.token_path, "wb") as f:
                pickle.dump(creds, f)

        self._service = build("youtube", "v3", credentials=creds)
        print("  [YouTube] 认证成功")

    def upload(self, video_path: str, script_data: dict) -> str:
        """上传视频，返回 YouTube video_id"""
        if not self._service:
            self.authenticate()

        title = self.yt_cfg["title_template"].format(
            title=script_data.get("title", ""),
        )
        description = self.yt_cfg["description_template"].format(
            cover_quote=script_data.get("cover_quote", ""),
            theme=script_data.get("tags", [""])[0] if script_data.get("tags") else "",
        )
        tags = self.yt_cfg["tags"] + script_data.get("tags", [])

        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags[:500],
                "categoryId": self.yt_cfg["category_id"],
                "defaultLanguage": self.yt_cfg["default_language"],
            },
            "status": {
                "privacyStatus": self.yt_cfg["privacy"],
                "selfDeclaredMadeForKids": False,
            },
        }

        media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True, chunksize=1024 * 1024 * 8)
        request = self._service.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media,
        )

        print(f"  [YouTube] 开始上传: {title}")
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"  [YouTube] 上传进度: {int(status.progress() * 100)}%")

        video_id = response["id"]
        print(f"  [YouTube] 上传完成: https://youtu.be/{video_id}")
        return video_id
