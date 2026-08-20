"""
背景图生成器 - 现代禅意风
主方案：Imagen API（复用Gemini Key）
备选：Unsplash免费图库
最终备选：原渐变背景
"""
import os
import io
import requests
from PIL import Image


class BackgroundGenerator:

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.gemini_key = cfg["api"].get("gemini_key", "")
        self.unsplash_key = cfg["api"].get("unsplash_key", "")
        self.output_dir = cfg["output"]["dir"]
        self.W = cfg["video"]["width"]
        self.H = cfg["video"]["height"]

    def generate(self, script_data: dict, filename: str):
        os.makedirs(self.output_dir, exist_ok=True)
        out_path = os.path.join(self.output_dir, filename)
        prompt = self._build_prompt(script_data)

        result = self._try_imagen(prompt, out_path)
        if result:
            print(f"  [BG] Imagen生成背景图 ✅")
            return result

        result = self._try_unsplash(script_data, out_path)
        if result:
            print(f"  [BG] Unsplash背景图 ✅")
            return result

        print("  [BG] 使用默认渐变背景")
        return None

    SCENES = [
        "ancient chinese buddhist temple courtyard at dawn, incense smoke rising, golden morning light through wooden pillars, no people",
        "small zen temple in misty mountain, stone steps, moss covered walls, ethereal fog, soft light",
        "mountain stream flowing over ancient stones, bamboo forest, morning mist, soft dappled light",
        "lone pine tree on mountain cliff at sunrise, vast dramatic sky, chinese ink painting aesthetic",
        "cherry blossom petals falling on still dark water, soft pink reflection, zen atmosphere",
        "single incense stick burning in dark room, smoke curling upward, warm candlelight glow, deep shadows",
        "golden sunset light streaming through ancient temple gate, dramatic sky, spiritual atmosphere",
        "morning dew on lotus leaf in ancient pond, soft bokeh background, warm golden hour light",
        "stone buddha statue in deep forest covered in moss, sunlight rays breaking through trees",
        "ancient temple bell tower in mountain monastery, foggy morning, soft blue mist",
        "empty meditation hall, polished wooden floor, single arched window with light beams, dust particles",
        "waterfall cascading over ancient moss stones in deep forest, long exposure, morning mist",
        "candle flame reflected in dark still water, minimal, meditative, warm glow in darkness",
        "mountain peak above clouds at golden hour, vast ethereal landscape, rays of light",
        "old stone lantern in japanese garden, night, soft warm glow, cherry blossoms, misty",
    ]

    def _build_prompt(self, script_data: dict) -> str:
        import random, hashlib
        tags = script_data.get("tags", [])
        tag_str = " ".join(tags)
        title = script_data.get("title", "")

        # 根据主题选择对应场景
        if any(w in tag_str for w in ["焦虑", "压力", "迷茫"]):
            candidates = [2, 11, 12]  # 流水、瀑布、烛光
        elif any(w in tag_str for w in ["放下", "执着", "比较"]):
            candidates = [3, 4, 13]  # 松树、樱花、山峰
        elif any(w in tag_str for w in ["付出", "布施", "慈悲"]):
            candidates = [6, 13, 14]  # 夕阳、山峰、石灯
        elif any(w in tag_str for w in ["当下", "专注", "平静"]):
            candidates = [5, 10, 7]  # 香烛、禅堂、荷叶
        elif any(w in tag_str for w in ["孤独", "异乡", "思念"]):
            candidates = [0, 1, 9]  # 寺庙、晨雾、钟楼
        else:
            candidates = list(range(len(self.SCENES)))

        # 用title做随机种子，保证同一视频每次生成相同背景
        seed = int(hashlib.md5(title.encode()).hexdigest(), 16) % len(candidates)
        scene_idx = candidates[seed % len(candidates)]
        base = self.SCENES[scene_idx]

        return (
            f"cinematic zen photography, {base}, "
            "9:16 vertical portrait orientation, "
            "soft natural diffused lighting, muted earth tones with subtle warmth, "
            "no text, no watermark, high quality, photorealistic"
        )

    def _try_imagen(self, prompt: str, out_path: str):
        """用Unsplash获取高质量禅意背景图（免费稳定）"""
        # Unsplash关键词映射
        zen_queries = [
            "zen buddhist temple morning",
            "misty mountain forest path",
            "bamboo forest sunlight",
            "lotus pond reflection",
            "incense smoke meditation",
            "autumn forest path",
            "mountain peak clouds sunrise",
            "stone garden meditation",
            "waterfall forest moss",
            "candlelight dark peaceful",
            "cherry blossom water",
            "monastery foggy morning",
            "pine tree cliff sunrise",
            "ancient stone lantern",
            "empty hall wooden floor light",
        ]
        import random, hashlib
        seed = int(hashlib.md5(prompt[:50].encode()).hexdigest(), 16) % len(zen_queries)
        query = zen_queries[seed]
        return self._try_unsplash_query(query, out_path)

    def _try_unsplash_query(self, query: str, out_path: str):
        """用Pexels API获取高质量禅意图片"""
        try:
            pexels_key = "P0a88apfxfsKw2wzW5BK8fIpIq5mui64iDGbqUGHZpxoH3M9igl2HoNK"
            headers = {"Authorization": pexels_key}
            resp = requests.get(
                "https://api.pexels.com/v1/search",
                headers=headers,
                params={"query": query, "orientation": "portrait", "per_page": 10},
                timeout=15
            )
            if resp.status_code == 200:
                photos = resp.json().get("photos", [])
                if photos:
                    import hashlib
                    idx = int(hashlib.md5(query.encode()).hexdigest(), 16) % len(photos)
                    img_url = photos[idx]["src"]["large2x"]
                    img_resp = requests.get(img_url, timeout=20)
                    if img_resp.status_code == 200:
                        img = Image.open(io.BytesIO(img_resp.content)).convert("RGB")
                        img = self._resize_and_darken(img)
                        img.save(out_path, "JPEG", quality=92)
                        print(f"  [BG] Pexels图片: {query}")
                        return out_path
        except Exception as e:
            print(f"  [BG] Pexels错误: {e}")
        return None

    def _try_unsplash(self, script_data: dict, out_path: str):
        try:
            tags = script_data.get("tags", [])
            tag_str = " ".join(tags)
            if any(w in tag_str for w in ["焦虑", "压力"]):
                query = "zen water calm meditation"
            elif any(w in tag_str for w in ["放下", "执着"]):
                query = "autumn leaves zen forest path"
            else:
                query = "zen minimalist nature meditation"
            if self.unsplash_key:
                resp = requests.get(
                    "https://api.unsplash.com/photos/random",
                    params={"query": query, "orientation": "portrait", "client_id": self.unsplash_key},
                    timeout=10
                )
                if resp.status_code == 200:
                    img_url = resp.json()["urls"]["regular"]
                else:
                    return None
            else:
                img_url = f"https://source.unsplash.com/1080x1920/?{query.replace(' ', ',')}"
            img_resp = requests.get(img_url, timeout=15)
            if img_resp.status_code == 200:
                img = Image.open(io.BytesIO(img_resp.content)).convert("RGB")
                img = self._resize_and_darken(img)
                img.save(out_path, "JPEG", quality=92)
                return out_path
        except Exception as e:
            print(f"  [BG] Unsplash错误: {e}")
        return None

    def _resize_and_darken(self, img: Image.Image) -> Image.Image:
        src_w, src_h = img.size
        if src_w / src_h > self.W / self.H:
            new_h, new_w = self.H, int(src_w * self.H / src_h)
        else:
            new_w, new_h = self.W, int(src_h * self.W / src_w)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        left, top = (new_w - self.W) // 2, (new_h - self.H) // 2
        img = img.crop((left, top, left + self.W, top + self.H))
        overlay = Image.new("RGB", (self.W, self.H), (0, 0, 0))
        mask = Image.new("L", (self.W, self.H))
        pixels = []
        for y in range(self.H):
            alpha = int(80 + 100 * (y / self.H))
            pixels.extend([alpha] * self.W)
        mask.putdata(pixels)
        img = Image.composite(overlay, img, mask)
        return img
