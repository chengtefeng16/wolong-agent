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

    def _build_prompt(self, script_data: dict) -> str:
        tags = script_data.get("tags", [])
        tag_str = " ".join(tags)
        if any(w in tag_str for w in ["焦虑", "压力", "迷茫", "比较"]):
            base = "still water with soft ripples, calming blue-green tones, misty morning lake"
        elif any(w in tag_str for w in ["放下", "执着", "当下"]):
            base = "fallen autumn leaves on ancient stone path, maple forest, warm amber light"
        elif any(w in tag_str for w in ["付出", "布施", "功德", "慈悲"]):
            base = "golden sunrise over misty mountain peaks, expansive sky, rays of light"
        else:
            base = "zen garden with raked sand patterns, single stone, morning mist"
        return (
            f"modern zen aesthetic, {base}, "
            "9:16 vertical portrait, cinematic photography, "
            "soft natural diffused lighting, muted earth tones with subtle warmth, "
            "no people, no text, no watermark, high quality"
        )

    def _try_imagen(self, prompt: str, out_path: str):
        if not self.gemini_key:
            return None
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=self.gemini_key)
            response = client.models.generate_images(
                model="imagen-3.0-generate-002",
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="9:16",
                    output_mime_type="image/jpeg",
                ),
            )
            if response.generated_images:
                img_bytes = response.generated_images[0].image.image_bytes
                img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                img = self._resize_and_darken(img)
                img.save(out_path, "JPEG", quality=92)
                return out_path
        except Exception as e:
            print(f"  [BG] Imagen错误: {e}")
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
