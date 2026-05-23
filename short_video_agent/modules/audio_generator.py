"""ElevenLabs TTS 音频生成器"""
import os
import requests


class AudioGenerator:
    BASE_URL = "https://api.elevenlabs.io/v1"

    def __init__(self, cfg: dict):
        self.api_key = cfg["api"]["elevenlabs_key"]
        self.voice_id = cfg["api"]["elevenlabs_voice_id"]
        self.output_dir = cfg["output"]["dir"]

    def generate(self, text: str, filename: str) -> str:
        """生成音频文件，返回文件路径"""
        url = f"{self.BASE_URL}/text-to-speech/{self.voice_id}"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.55,
                "similarity_boost": 0.80,
                "style": 0.20,
                "use_speaker_boost": True,
            },
        }

        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        if resp.status_code != 200:
            raise RuntimeError(
                f"ElevenLabs API 错误 {resp.status_code}: {resp.text[:300]}"
            )

        os.makedirs(self.output_dir, exist_ok=True)
        out_path = os.path.join(self.output_dir, filename)
        with open(out_path, "wb") as f:
            f.write(resp.content)

        print(f"  [Audio] 已生成: {out_path}")
        return out_path

    def get_voice_list(self) -> list:
        """调试用：列出账号下所有音色"""
        resp = requests.get(
            f"{self.BASE_URL}/voices",
            headers={"xi-api-key": self.api_key},
            timeout=15,
        )
        return resp.json().get("voices", [])
