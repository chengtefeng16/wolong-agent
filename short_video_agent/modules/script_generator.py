"""Gemini API 脚本生成器 — 单次调用直出完整60秒口播稿"""
import json
import re

from google import genai


class ScriptGenerator:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.direction = cfg["direction"]
        self._client = genai.Client(api_key=cfg["api"]["gemini_key"])
        self._model = "gemini-2.5-flash"

    def generate(self, materials: list[dict]) -> dict:
        """
        从素材生成完整脚本，一次 Gemini 调用返回：
          title        : 标题
          cover_quote  : 封面金句
          full_script  : 完整口播稿（直接送 TTS）
          tags         : 标签列表
        """
        cols = self.direction["google_sheet"]["columns"]

        # 拼接素材（带情绪标签）
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

        print(f"  [Gemini] 调用 {self._model}，生成口播脚本...")
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
        )
        raw = response.text.strip()

        # 提取 JSON（兼容 Gemini 包裹 ```json ... ``` 的情况）
        json_match = re.search(r"\{[\s\S]+\}", raw)
        if not json_match:
            raise ValueError(f"Gemini 未返回有效 JSON，原始输出：\n{raw[:500]}")

        script_data = json.loads(json_match.group())

        # 校验必要字段
        for field in ["title", "cover_quote", "full_script"]:
            if field not in script_data:
                raise ValueError(f"Gemini 输出缺少字段 '{field}'，请检查 prompt")

        char_count = len(script_data["full_script"])
        print(f"  [Gemini] 脚本生成完成：{char_count}字")

        return script_data
