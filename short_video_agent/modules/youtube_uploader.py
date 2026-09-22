"""YouTube Data API v3 上传器

云端运行使用 JSON 格式 token（兼容 GitHub Actions）
本地首次运行会弹出浏览器进行 OAuth 授权。
"""
import os
import json
import time

import requests as _requests
from google.auth.transport.requests import Request, AuthorizedSession
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import google_auth_httplib2
import httplib2
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload


SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",  # required for thumbnails().set()
]
RETRIABLE_STATUS_CODES = {500, 502, 503, 504}
MAX_RETRIES = 5


class YouTubeUploader:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.yt_cfg = cfg["direction"]["youtube"]
        self.credentials_path = cfg["api"]["youtube_credentials"]
        self.token_path = cfg["api"]["youtube_token"]
        self._service = None

    def _load_creds_from_json(self, path: str):
        with open(path, "r") as f:
            data = json.load(f)
        return Credentials(
            token=data.get("token"),
            refresh_token=data.get("refresh_token"),
            token_uri=data.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=data.get("client_id"),
            client_secret=data.get("client_secret"),
            scopes=data.get("scopes", SCOPES),
        )

    def _save_creds_to_json(self, creds, path: str):
        data = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": list(creds.scopes) if creds.scopes else SCOPES,
        }
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def authenticate(self):
        creds = None
        if os.path.exists(self.token_path):
            try:
                creds = self._load_creds_from_json(self.token_path)
            except (json.JSONDecodeError, KeyError):
                import pickle
                with open(self.token_path, "rb") as f:
                    old_creds = pickle.load(f)
                self._save_creds_to_json(old_creds, self.token_path)
                creds = self._load_creds_from_json(self.token_path)
                print("  [YouTube] 已将token从pickle格式迁移到JSON格式")

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("  [YouTube] 刷新 OAuth Token...")
                creds.refresh(Request())
                self._save_creds_to_json(creds, self.token_path)
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(f"未找到凭证文件：{self.credentials_path}")
                print("  [YouTube] 首次授权，即将打开浏览器...")
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=8080, open_browser=True)
                self._save_creds_to_json(creds, self.token_path)
                print(f"  [YouTube] Token 已保存: {self.token_path}")

        # 注入代理：httplib2 不读环境变量，需显式配置
        # 优先级：环境变量 → macOS 系统代理（urllib.request.getproxies()）
        import httplib2
        import urllib.request
        proxy_info = None
        proxy_url = (os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY")
                     or os.environ.get("http_proxy") or os.environ.get("HTTP_PROXY"))
        if not proxy_url:
            sys_proxies = urllib.request.getproxies()
            proxy_url = sys_proxies.get("https") or sys_proxies.get("http")
        if proxy_url:
            from urllib.parse import urlparse
            p = urlparse(proxy_url)
            proxy_type = 2 if (p.scheme or "").startswith("socks5") else 3  # SOCKS5 or HTTP
            proxy_info = httplib2.ProxyInfo(
                proxy_type=proxy_type,
                proxy_host=p.hostname,
                proxy_port=p.port or 8080,
            )
            print(f"  [YouTube] 代理: {p.scheme}://{p.hostname}:{p.port}")
        http = google_auth_httplib2.AuthorizedHttp(
            creds, http=httplib2.Http(proxy_info=proxy_info)
        )
        self._service = build("youtube", "v3", http=http)
        # AuthorizedSession：proxies 控制上传流量，auth_request 控制 token 刷新流量
        # 两者都需要走代理，否则 token refresh 会直连超时
        if proxy_url:
            proxy_sess = _requests.Session()
            proxy_sess.proxies = {"https": proxy_url, "http": proxy_url}
            auth_req = Request(session=proxy_sess)
        else:
            auth_req = None
        self._session = AuthorizedSession(creds, auth_request=auth_req)
        if proxy_url:
            self._session.proxies = {"https": proxy_url, "http": proxy_url}
        print("  [YouTube] 认证成功 ✅")

    def upload(self, video_path: str, script_data: dict, privacy: str = None) -> str:
        if not self._service:
            self.authenticate()

        privacy = privacy or self.yt_cfg.get("privacy", "private")
        tags_from_script = script_data.get("tags", [])
        first_tag = tags_from_script[0] if tags_from_script else "佛法"

        title = self.yt_cfg["title_template"].format(title=script_data.get("title", ""))
        description = self.yt_cfg["description_template"].format(
            cover_quote=script_data.get("cover_quote", ""),
            theme=first_tag,
            report_url=script_data.get("report_url", self.yt_cfg.get("report_url", "")),
            title=script_data.get("title", ""),
        )
        tags = self.yt_cfg["tags"] + tags_from_script

        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": list(dict.fromkeys(tags))[:500],
                "categoryId": self.yt_cfg["category_id"],
                "defaultLanguage": self.yt_cfg["default_language"],
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False,
            },
        }

        print(f"  [YouTube] 开始上传: 「{title}」")
        print(f"  [YouTube] 隐私设置: {privacy}")
        video_id = self._requests_resumable_upload(video_path, body)
        print(f"  [YouTube] ✅ 上传完成: https://youtu.be/{video_id}")
        return video_id

    def set_thumbnail(self, video_id: str, image_path: str):
        if not self._service:
            self.authenticate()
        media = MediaFileUpload(image_path, mimetype="image/jpeg", resumable=False)
        self._service.thumbnails().set(videoId=video_id, media_body=media).execute()

    def _requests_resumable_upload(self, video_path: str, body: dict) -> str:
        """5MB分块断点续传，用 AuthorizedSession 规避 httplib2+代理重定向问题。"""
        _NETWORK_ERRS = (
            ConnectionError,
            TimeoutError,
            _requests.exceptions.ConnectionError,
            _requests.exceptions.ChunkedEncodingError,
            _requests.exceptions.ReadTimeout,
        )
        sess = self._session
        file_size = os.path.getsize(video_path)
        chunk_size = 5 * 1024 * 1024  # 5 MB

        # ── Step 1: 初始化 resumable upload，拿到 upload URI ──────────────
        init_url = (
            "https://www.googleapis.com/upload/youtube/v3/videos"
            "?uploadType=resumable&part=snippet,status"
        )
        for attempt in range(MAX_RETRIES + 1):
            try:
                resp = sess.post(
                    init_url,
                    headers={
                        "Content-Type": "application/json; charset=UTF-8",
                        "X-Upload-Content-Type": "video/mp4",
                        "X-Upload-Content-Length": str(file_size),
                    },
                    json=body,
                    timeout=30,
                )
                resp.raise_for_status()
                upload_uri = resp.headers["Location"]
                break
            except _NETWORK_ERRS as e:
                if attempt >= MAX_RETRIES:
                    raise
                wait = 2 ** (attempt + 1)
                print(f"\n  [YouTube] 初始化失败({type(e).__name__})，{wait}s后重试...")
                time.sleep(wait)

        # ── Step 2: 分块上传，网络断开后从服务器确认的偏移量继续 ──────────
        with open(video_path, "rb") as f:
            offset = 0
            while offset < file_size:
                f.seek(offset)
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                chunk_end = offset + len(chunk) - 1

                for attempt in range(MAX_RETRIES + 1):
                    try:
                        resp = sess.put(
                            upload_uri,
                            headers={
                                "Content-Type": "video/mp4",
                                "Content-Range": f"bytes {offset}-{chunk_end}/{file_size}",
                            },
                            data=chunk,
                            timeout=120,
                        )
                        if resp.status_code in (200, 201):
                            print()
                            return resp.json()["id"]
                        elif resp.status_code == 308:
                            offset += len(chunk)
                            pct = int(offset / file_size * 100)
                            bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
                            print(f"\r  [YouTube] [{bar}] {pct}%", end="", flush=True)
                            break
                        elif resp.status_code in RETRIABLE_STATUS_CODES:
                            wait = 2 ** (attempt + 1)
                            print(f"\n  [YouTube] 服务器错误 {resp.status_code}，{wait}s后重试...")
                            time.sleep(wait)
                        else:
                            raise RuntimeError(f"上传错误: {resp.status_code} {resp.text[:200]}")
                    except _NETWORK_ERRS as e:
                        if attempt >= MAX_RETRIES:
                            raise
                        wait = 2 ** (attempt + 1)
                        print(f"\n  [YouTube] 网络中断({type(e).__name__})，{wait}s后查询断点({attempt+1}/{MAX_RETRIES})...")
                        time.sleep(wait)
                        try:
                            qr = sess.put(
                                upload_uri,
                                headers={"Content-Range": f"bytes */{file_size}"},
                                timeout=30,
                            )
                            if qr.status_code == 308 and "Range" in qr.headers:
                                offset = int(qr.headers["Range"].split("-")[1]) + 1
                                f.seek(offset)
                                chunk = f.read(chunk_size)
                                chunk_end = offset + len(chunk) - 1
                                print(f"  [YouTube] 服务器已确认 {offset} 字节，从此续传")
                        except Exception:
                            pass

        raise RuntimeError("上传结束但未收到完成响应")
