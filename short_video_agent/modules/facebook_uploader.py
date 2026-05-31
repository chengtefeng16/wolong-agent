"""
facebook_uploader.py
=====================
把竖版短视频以 Reels 形式发布到 Facebook 主页。

使用的是 Facebook 官方的 *Reels Publishing API*（三阶段流程），
与普通的 /{page-id}/videos 端点不同：

    1. start   : POST graph.facebook.com/{ver}/{page_id}/video_reels?upload_phase=start
                 -> 返回 video_id 和 upload_url
    2. upload  : POST rupload.facebook.com/video-upload/{ver}/{video_id}
                 header 带 Authorization / offset / file_size，body 为视频二进制
    3. finish  : POST graph.facebook.com/{ver}/{page_id}/video_reels?upload_phase=finish
                 带 video_id / description / video_state=PUBLISHED

Reels 视频要求：竖版 9:16，时长约 3–90 秒，>=540x960（建议 720p），MP4。

环境变量
--------
    FB_PAGE_ACCESS_TOKEN   长期（最好永久）的 Page Access Token，必填
    FB_PAGE_ID             主页 ID，必填
    FB_GRAPH_API_VERSION   Graph API 版本，可选，默认 v23.0

注意：requests 会自动读取 HTTP_PROXY / HTTPS_PROXY 环境变量，
所以本地走代理、GitHub Actions 不走代理都不用改代码。
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger("facebook_uploader")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

GRAPH_API_VERSION = os.getenv("FB_GRAPH_API_VERSION", "v23.0")
GRAPH_HOST = f"https://graph.facebook.com/{GRAPH_API_VERSION}"
RUPLOAD_HOST = f"https://rupload.facebook.com/video-upload/{GRAPH_API_VERSION}"

# 单次请求的网络超时（秒）。上传大文件时连接超时给宽一点。
CONNECT_TIMEOUT = 30
READ_TIMEOUT = 600


class FacebookUploadError(RuntimeError):
    """Facebook API 返回错误，或上传/发布流程失败时抛出。"""


class FacebookReelsUploader:
    def __init__(
        self,
        page_id: Optional[str] = None,
        access_token: Optional[str] = None,
    ) -> None:
        self.page_id = page_id or os.getenv("FB_PAGE_ID")
        self.access_token = access_token or os.getenv("FB_PAGE_ACCESS_TOKEN")
        if not self.page_id:
            raise FacebookUploadError("缺少 Page ID（设置环境变量 FB_PAGE_ID）")
        if not self.access_token:
            raise FacebookUploadError("缺少 Page Access Token（设置环境变量 FB_PAGE_ACCESS_TOKEN）")

    # ---- 工具方法 -------------------------------------------------------

    @staticmethod
    def _raise_on_error(resp: requests.Response, stage: str) -> dict:
        """把响应解析成 dict，若含 error 字段或状态码异常则抛错。"""
        try:
            data = resp.json()
        except ValueError:
            data = {}
        if resp.status_code >= 400 or (isinstance(data, dict) and "error" in data):
            err = data.get("error", {}) if isinstance(data, dict) else {}
            msg = err.get("message", resp.text[:500])
            code = err.get("code", resp.status_code)
            raise FacebookUploadError(f"[{stage}] Facebook 返回错误 (code={code}): {msg}")
        return data if isinstance(data, dict) else {}

    # ---- 三个阶段 -------------------------------------------------------

    def _start(self) -> tuple[str, str]:
        """阶段 1：初始化上传会话，返回 (video_id, upload_url)。"""
        url = f"{GRAPH_HOST}/{self.page_id}/video_reels"
        resp = requests.post(
            url,
            params={"access_token": self.access_token, "upload_phase": "start"},
            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
        )
        data = self._raise_on_error(resp, "start")
        video_id = data.get("video_id")
        if not video_id:
            raise FacebookUploadError(f"[start] 未返回 video_id，响应：{data}")
        upload_url = data.get("upload_url") or f"{RUPLOAD_HOST}/{video_id}"
        logger.info("已创建上传会话 video_id=%s", video_id)
        return video_id, upload_url

    def _upload_local_file(self, upload_url: str, video_path: Path) -> None:
        """阶段 2（本地文件）：把二进制流式上传到 rupload 主机。"""
        file_size = video_path.stat().st_size
        headers = {
            "Authorization": f"OAuth {self.access_token}",
            "offset": "0",
            "file_size": str(file_size),
        }
        logger.info("开始上传文件 %s（%.1f MB）", video_path.name, file_size / 1024 / 1024)
        with video_path.open("rb") as f:
            resp = requests.post(
                upload_url,
                headers=headers,
                data=f,  # 流式上传，避免一次性读入内存
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            )
        data = self._raise_on_error(resp, "upload")
        if not data.get("success", True):
            raise FacebookUploadError(f"[upload] 上传未成功，响应：{data}")
        logger.info("二进制上传完成")

    def _upload_hosted_file(self, upload_url: str, video_url: str) -> None:
        """阶段 2（远程 CDN）：让 Facebook 自己去拉取 video_url。"""
        headers = {
            "Authorization": f"OAuth {self.access_token}",
            "file_url": video_url,
        }
        logger.info("让 Facebook 从 URL 拉取视频：%s", video_url)
        resp = requests.post(upload_url, headers=headers, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))
        self._raise_on_error(resp, "upload")
        logger.info("远程视频已提交")

    def _finish(self, video_id: str, description: str, video_state: str = "PUBLISHED") -> None:
        """阶段 3：发布 Reel。video_state 可为 PUBLISHED / DRAFT / SCHEDULED。"""
        url = f"{GRAPH_HOST}/{self.page_id}/video_reels"
        params = {
            "access_token": self.access_token,
            "upload_phase": "finish",
            "video_id": video_id,
            "video_state": video_state,
            "description": description,
        }
        resp = requests.post(url, params=params, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))
        self._raise_on_error(resp, "finish")
        logger.info("已提交发布请求（video_state=%s）", video_state)

    def _poll_status(self, video_id: str, timeout: int = 180, interval: int = 10) -> dict:
        """轮询 Reel 的处理/发布状态，直到完成或超时。返回最后一次 status。"""
        url = f"{GRAPH_HOST}/{video_id}"
        deadline = time.time() + timeout
        last: dict = {}
        while time.time() < deadline:
            resp = requests.get(
                url,
                params={"access_token": self.access_token, "fields": "status"},
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            )
            data = self._raise_on_error(resp, "status")
            last = data.get("status", {}) or {}
            video_status = last.get("video_status") or last.get("publishing_phase", {}).get("status")
            logger.info("当前状态：%s", last)
            if video_status in {"ready", "published", "complete"}:
                return last
            if video_status in {"error", "failed", "expired"}:
                raise FacebookUploadError(f"[status] Reel 处理失败：{last}")
            time.sleep(interval)
        logger.warning("轮询超时，Reel 可能仍在处理中。最后状态：%s", last)
        return last

    # ---- 对外主入口 -----------------------------------------------------

    def upload_reel(
        self,
        video_path: Optional[str] = None,
        video_url: Optional[str] = None,
        description: str = "",
        wait_for_status: bool = True,
    ) -> str:
        """
        上传并发布一个 Reel。提供 video_path（本地文件）或 video_url（公网可访问 URL）之一。
        返回 video_id。
        """
        if not video_path and not video_url:
            raise FacebookUploadError("必须提供 video_path 或 video_url")

        video_id, upload_url = self._start()

        if video_path:
            path = Path(video_path)
            if not path.exists():
                raise FacebookUploadError(f"视频文件不存在：{path}")
            self._upload_local_file(upload_url, path)
        else:
            self._upload_hosted_file(upload_url, video_url)  # type: ignore[arg-type]

        self._finish(video_id, description)

        if wait_for_status:
            self._poll_status(video_id)

        logger.info("Reel 发布流程完成，video_id=%s", video_id)
        return video_id


# ---- 从 script JSON 中提取文案 -----------------------------------------

def build_description_from_script(script_path: str) -> str:
    """
    从 script_*.json 里拼出 Reel 的文案。
    兼容多种可能的字段名（title / description / caption / text / content / hashtags），
    取到什么用什么，取不到就返回空串。如果你的 JSON 结构固定，可以把这里改简单。
    """
    try:
        data = json.loads(Path(script_path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        logger.warning("无法读取 script JSON（%s），将使用空文案：%s", script_path, e)
        return ""

    if isinstance(data, str):
        return data.strip()
    if not isinstance(data, dict):
        return ""

    parts: list[str] = []
    title = data.get("title") or data.get("titleZh") or data.get("title_zh")
    body = (
        data.get("description")
        or data.get("caption")
        or data.get("text")
        or data.get("content")
    )
    if title:
        parts.append(str(title).strip())
    if body and str(body).strip() != str(title or "").strip():
        parts.append(str(body).strip())

    hashtags = data.get("hashtags") or data.get("tags")
    if isinstance(hashtags, (list, tuple)):
        tags = " ".join(f"#{str(t).lstrip('#')}" for t in hashtags if str(t).strip())
        if tags:
            parts.append(tags)
    elif isinstance(hashtags, str) and hashtags.strip():
        parts.append(hashtags.strip())

    return "\n\n".join(parts).strip()


# ---- 给 main.py 调用的便捷函数 ------------------------------------------

def run(video: str, script: Optional[str] = None, description: Optional[str] = None) -> str:
    """
    main.py 的 upload_facebook 步骤调用入口。
    优先用显式传入的 description，否则从 script JSON 提取。
    """
    desc = description if description is not None else (build_description_from_script(script) if script else "")
    uploader = FacebookReelsUploader()
    return uploader.upload_reel(video_path=video, description=desc)


# ---- 命令行入口（匹配 main.py --step upload_facebook 的参数风格）--------

def _main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="发布 Facebook Reel")
    parser.add_argument("--video", help="本地视频文件路径")
    parser.add_argument("--video-url", help="公网可访问的视频 URL（与 --video 二选一）")
    parser.add_argument("--script", help="script_*.json 路径，用于自动生成文案")
    parser.add_argument("--description", help="直接指定文案（优先于 --script）")
    parser.add_argument("--no-wait", action="store_true", help="提交后不轮询发布状态")
    args = parser.parse_args(argv)

    if not args.video and not args.video_url:
        parser.error("必须提供 --video 或 --video-url")

    desc = args.description
    if desc is None and args.script:
        desc = build_description_from_script(args.script)
    desc = desc or ""

    try:
        uploader = FacebookReelsUploader()
        video_id = uploader.upload_reel(
            video_path=args.video,
            video_url=args.video_url,
            description=desc,
            wait_for_status=not args.no_wait,
        )
    except FacebookUploadError as e:
        logger.error("发布失败：%s", e)
        return 1

    print(video_id)
    return 0


if __name__ == "__main__":
    sys.exit(_main())
