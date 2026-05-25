"""Gemini API 脚本生成器 — 单次调用直出完整60秒口播稿（支持双语）"""
import json
import re

from google import genai


class ScriptGenerator:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.direction = cfg["direction"]
        self._client = genai.Client(api_key=cfg["api"]["gemini_key"])
        self._model = "gemini-2.5-flash"
        self._bilingual = self.direction.get("language", "zh") == "zh-en"

    def generate(self, materials: list[dict]) -> dict:
        cols = self.direction["google_sheet"]["columns"]

        material_lines = []
        for m in materials:
            theme = str(m.get(cols["theme"], "")).strip()
            text  = str(m.get(cols["source_text"], "")).strip()
            if text:
                prefix = f"[{theme}] " if theme else ""
                material_lines.append(f"{prefix}{text}")
        source_material = "\n\n".join(material_lines)

        prompt = self.direction["script_prompt"].format(
            target_audience=self.direction["target_audience"],
            source_material=source_material,
        )

        if self._bilingual:
            prompt += """

另外，请在JSON中额外添加一个字段：
  "en_subtitles": 将full_script按句子分割，每句提供对应的英文翻译，格式为字符串数组。
  例如：["Don't wait for conditions to be perfect.", "Start with what you have right now."]
  要求：英文自然流畅，适合年轻海外华人阅读，每句15词以内。
"""

        print(f"  [Gemini] 调用 {self._model}，生成{'双语' if self._bilingual else ''}口播脚本...")
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
        )
        raw = response.text.strip()

        json_match = re.search(r"\{[\s\S]+\}", raw)
        if not json_match:
            raise ValueError(f"Gemini 未返回有效 JSON，原始输出：\n{raw[:500]}")

        script_data = json.loads(json_match.group())

        for field in ["title", "cover_quote", "full_script"]:
            if field not in script_data:
                raise ValueError(f"Gemini 输出缺少字段 '{field}'，请检查 prompt")

        char_count = len(script_data["full_script"])
        print(f"  [Gemini] 脚本生成完成：{char_count}字")

        if self._bilingual:
            en_count = len(script_data.get("en_subtitles", []))
            print(f"  [Gemini] 英文字幕：{en_count}句")

        return script_data
