"""Gemini API 选题 & 脚本生成器"""
import json
import re
from google import genai
from google.genai import types


class ScriptGenerator:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.direction = cfg["direction"]
        self._client = genai.Client(api_key=cfg["api"]["gemini_key"])
        self._model = "gemini-2.0-flash"

    def generate_topic_and_script(self, materials: list[dict]) -> dict:
        """从素材生成选题 + 分段脚本，返回结构化 dict"""
        cols = self.direction["google_sheet"]["columns"]
        source_text = "\n\n".join(
            f"【{m.get(cols['theme'], '通用')}】{m.get(cols['source_text'], '')}"
            for m in materials
        )

        prompt = self.direction["topic_prompt"].format(
            target_audience=self.direction["target_audience"],
            source_material=source_text,
        )

        response = self._client.models.generate_content(
            model=self._model, contents=prompt
        )
        raw = response.text.strip()

        # 提取 JSON（Gemini 有时会包裹在 markdown 代码块里）
        json_match = re.search(r"\{[\s\S]+\}", raw)
        if not json_match:
            raise ValueError(f"Gemini 未返回有效 JSON:\n{raw}")
        script_data = json.loads(json_match.group())

        # 口语化润色
        full_script = " ".join(s["text"] for s in script_data["segments"])
        script_data["polished_script"] = self._polish(full_script)
        script_data["segments_polished"] = self._polish_segments(script_data["segments"])

        return script_data

    def _polish(self, script: str) -> str:
        prompt = self.direction["script_polish_prompt"].format(script=script)
        response = self._client.models.generate_content(
            model=self._model, contents=prompt
        )
        return response.text.strip()

    def _polish_segments(self, segments: list[dict]) -> list[dict]:
        result = []
        for seg in segments:
            polished = self._polish(seg["text"])
            result.append({**seg, "text_polished": polished})
        return result
