"""CNcar 脚本生成器

逻辑：
  1. 如果素材行的 copy_en 已填写 → 直接使用，跳过 Gemini
  2. 如果 copy_en 为空 → 调用 Gemini 按 script_prompt 生成英文脚本
  3. copy_ar 本期不生成（留 Step 4 Arabic 支持）
"""
import json
import re

from google import genai


class CNcarScriptGenerator:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.direction = cfg["direction"]
        self._client = genai.Client(api_key=cfg["api"]["gemini_key"])
        self._model = "gemini-2.5-flash"

    def generate(self, material: dict) -> dict:
        car_model       = material.get("car_model", "").strip()
        destination     = material.get("destination", "").strip()
        landed_cost_usd = material.get("landed_cost_usd", "").strip()
        report_url      = material.get("report_url", "").strip()
        copy_en         = material.get("copy_en", "").strip()

        if copy_en:
            print(f"  [CNcar Script] copy_en 已预填，直接使用（跳过 Gemini）")
            return {
                "title":       f"{car_model} in {destination} — Landed Cost",
                "cover_quote": copy_en[:80],
                "full_script": copy_en,
                "tags":        [car_model, destination, "CNcar", "EV import"],
                "report_url":  report_url,
                "car_model":   car_model,
                "destination": destination,
                "_source":     "prefilled",
            }

        print(f"  [CNcar Script] copy_en 为空，调用 Gemini 生成...")
        prompt = self.direction["script_prompt"].format(
            car_model=car_model,
            destination=destination,
            landed_cost_usd=landed_cost_usd,
            report_url=report_url,
        )

        raw = self._call(prompt)
        data = self._parse_json(raw)

        print(f"  [CNcar Script] 生成完成：{len(data.get('full_script',''))}字")
        return {
            "title":       data.get("title", f"{car_model} — {destination} Cost"),
            "cover_quote": data.get("cover_quote", ""),
            "full_script": data.get("full_script", ""),
            "tags":        data.get("tags", []),
            "report_url":  report_url,
            "car_model":   car_model,
            "destination": destination,
            "_source":     "gemini",
        }

    def _call(self, prompt: str, retries: int = 3) -> str:
        import time
        for attempt in range(retries):
            try:
                response = self._client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                )
                return response.text.strip()
            except Exception as e:
                err = str(e)
                if attempt < retries - 1 and any(
                    x in err for x in ["503", "502", "disconnected", "UNAVAILABLE"]
                ):
                    wait = 8 * (attempt + 1)
                    print(f"  [CNcar Script] 重试 {attempt+1}/{retries}，等待{wait}秒...")
                    time.sleep(wait)
                else:
                    raise

    @staticmethod
    def _parse_json(raw: str) -> dict:
        match = re.search(r"\{[\s\S]+\}", raw)
        if not match:
            raise ValueError(f"Gemini 未返回有效 JSON：\n{raw[:400]}")
        return json.loads(match.group())
