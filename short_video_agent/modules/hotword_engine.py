"""热词抓取与融入模块 - 三源热词系统
1. 你自己的高效词（数据验证）
2. YouTube实时同领域热门词
3. 海外华人情绪词库
"""
import re
import requests
from collections import defaultdict


class HotwordEngine:
    # 源1：你自己数据验证的高效词（平均浏览量高）
    PROVEN_WORDS = [
        "别再比", "放下", "太用力", "羡慕", "海外华人",
        "睡不着", "别等别人", "你的能量", "答案在你",
    ]

    # 源3：海外华人特有情绪词库
    OVERSEAS_EMOTIONS = [
        "内耗", "执念", "焦虑", "孤独", "迷茫",
        "身份认同", "文化夹缝", "思乡", "漂泊", "格格不入",
        "假装合群", "深夜emo", "自我怀疑", "情绪稳定",
        "班味", "活人感", "社交省电", "偷感", "破防",
    ]

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self._cache = None

    def fetch_youtube_hotwords(self, max_words: int = 15) -> list:
        """从YouTube抓取同领域实时热词"""
        if not self.api_key:
            return []
        if self._cache is not None:
            return self._cache

        search_terms = ["海外华人 焦虑", "疗愈 内耗", "佛法 放下", "弘一法师"]
        all_titles = []
        try:
            for term in search_terms:
                url = "https://www.googleapis.com/youtube/v3/search"
                params = {
                    "part": "snippet", "q": term, "type": "video",
                    "order": "viewCount", "maxResults": 15,
                    "relevanceLanguage": "zh", "key": self.api_key,
                }
                resp = requests.get(url, params=params, timeout=15)
                if resp.status_code == 200:
                    for item in resp.json().get("items", []):
                        all_titles.append(item["snippet"]["title"])
        except Exception as e:
            print(f"  [Hotword] YouTube抓取失败: {e}")
            return []

        # 提取高频词
        stopwords = {"视频", "一个", "这个", "什么", "怎么", "如何", "为什么",
                     "我们", "你们", "他们", "自己", "这样", "那样", "佛法与生"}
        word_count = defaultdict(int)
        for t in all_titles:
            for w in re.findall(r"[一-龥]{2,4}", t):
                if w not in stopwords:
                    word_count[w] += 1
        hot = [w for w, c in sorted(word_count.items(), key=lambda x: -x[1]) if c >= 2]
        self._cache = hot[:max_words]
        return self._cache

    def pick_hotwords(self, rng, count: int = 2) -> list:
        """综合三源，随机选取热词"""
        pool = list(self.PROVEN_WORDS) + list(self.OVERSEAS_EMOTIONS)
        yt_hot = self.fetch_youtube_hotwords()
        # YouTube实时词权重更高，重复加入
        pool = pool + yt_hot + yt_hot
        if not pool:
            return []
        chosen = rng.sample(pool, min(count, len(pool)))
        return chosen
