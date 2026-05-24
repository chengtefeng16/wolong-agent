"""
短视频Agent管理后台
功能：发布历史、YouTube数据、手动触发、评论管理
"""
import os
import json
import requests
from flask import Flask, render_template, jsonify, request
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import pickle

app = Flask(__name__)

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "chengtefeng16/wolong-agent")
GITHUB_WORKFLOW = os.environ.get("GITHUB_WORKFLOW", "daily_upload.yml")
YOUTUBE_TOKEN_PATH = os.environ.get("YOUTUBE_TOKEN_PATH", "config/youtube_token.json")

def get_youtube_service():
    """获取YouTube API服务"""
    try:
        token_b64 = os.environ.get("YOUTUBE_TOKEN_B64")
        if token_b64:
            import base64, tempfile
            token_data = base64.b64decode(token_b64)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as f:
                f.write(token_data)
                token_path = f.name
        else:
            token_path = YOUTUBE_TOKEN_PATH

        with open(token_path, "rb") as f:
            creds = pickle.load(f)
        return build("youtube", "v3", credentials=creds)
    except Exception as e:
        print(f"YouTube API error: {e}")
        return None


def get_history():
    """从GitHub获取发布历史"""
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/short_video_agent/history.json"
        headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            import base64
            content = base64.b64decode(resp.json()["content"]).decode("utf-8")
            return json.loads(content)
    except Exception as e:
        print(f"History fetch error: {e}")
    return []


def get_youtube_stats(video_ids):
    """批量获取YouTube视频数据"""
    if not video_ids:
        return {}
    try:
        yt = get_youtube_service()
        if not yt:
            return {}
        resp = yt.videos().list(
            part="statistics,snippet",
            id=",".join(video_ids)
        ).execute()
        stats = {}
        for item in resp.get("items", []):
            vid = item["id"]
            s = item.get("statistics", {})
            stats[vid] = {
                "views": int(s.get("viewCount", 0)),
                "likes": int(s.get("likeCount", 0)),
                "comments": int(s.get("commentCount", 0)),
                "shares": int(s.get("favoriteCount", 0)),
                "thumbnail": item["snippet"]["thumbnails"].get("medium", {}).get("url", ""),
            }
        return stats
    except Exception as e:
        print(f"YouTube stats error: {e}")
        return {}


def trigger_github_action():
    """手动触发GitHub Actions"""
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/{GITHUB_WORKFLOW}/dispatches"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        resp = requests.post(url, headers=headers, json={"ref": "main"}, timeout=10)
        return resp.status_code == 204
    except Exception as e:
        print(f"Trigger error: {e}")
        return False


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/videos")
def api_videos():
    history = get_history()
    video_ids = [v["video_id"] for v in history if v.get("video_id")]
    stats = get_youtube_stats(video_ids)
    for v in history:
        vid = v.get("video_id")
        if vid and vid in stats:
            v.update(stats[vid])
        else:
            v.setdefault("views", 0)
            v.setdefault("likes", 0)
            v.setdefault("comments", 0)
            v.setdefault("shares", 0)
    history.sort(key=lambda x: x.get("views", 0), reverse=True)
    return jsonify(history)


@app.route("/api/trigger", methods=["POST"])
def api_trigger():
    success = trigger_github_action()
    return jsonify({"success": success})


@app.route("/api/stats")
def api_stats():
    history = get_history()
    video_ids = [v["video_id"] for v in history if v.get("video_id")]
    stats = get_youtube_stats(video_ids)
    total_views = sum(s.get("views", 0) for s in stats.values())
    total_likes = sum(s.get("likes", 0) for s in stats.values())
    total_comments = sum(s.get("comments", 0) for s in stats.values())
    success_count = sum(1 for v in history if v.get("status") == "success")
    return jsonify({
        "total_videos": len(history),
        "success_count": success_count,
        "total_views": total_views,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "this_week": sum(1 for v in history if v.get("published_at", "")[:10] >= datetime.now().strftime("%Y-%m-%d")[:8] + "01"),
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
