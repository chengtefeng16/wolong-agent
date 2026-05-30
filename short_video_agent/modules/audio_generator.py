"""TTS 音频生成器 - ElevenLabs（声音克隆）优先，edge-tts备用"""
import os
import asyncio
import requests
import edge_tts


class AudioGenerator:
    DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"
    ELEVENLABS_URL = "https://api.elevenlabs.io/v1/text-to-speech"

    def __init__(self, cfg: dict):
        self.api_key = cfg["api"].get("elevenlabs_key", "")
        self.voice_id = cfg["api"].get("elevenlabs_voice_id", self.DEFAULT_VOICE)
        self.output_dir = cfg["output"]["dir"]
        self._use_elevenlabs = (
            self.api_key and
            not self.voice_id.startswith("zh-") and
            not self.voice_id.startswith("en-")
        )

    def generate(self, text: str, filename: str) -> str:
        os.makedirs(self.output_dir, exist_ok=True)
        out_path = os.path.join(self.output_dir, filename)

        if self._use_elevenlabs:
            result = self._try_elevenlabs(text, out_path)
            if result:
                print(f"  [Audio] ElevenLabs已生成: {out_path}")
                return result
            print("  [Audio] ElevenLabs失败，切换edge-tts备用")

        asyncio.run(self._edge_tts(text, out_path))
        print(f"  [Audio] edge-tts已生成: {out_path}")
        return out_path

    def _try_elevenlabs(self, text: str, out_path: str):
        try:
            url = f"{self.ELEVENLABS_URL}/{self.voice_id}"
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
            if resp.status_code == 200:
                with open(out_path, "wb") as f:
                    f.write(resp.content)
                return out_path
            else:
                print(f"  [Audio] ElevenLabs错误 {resp.status_code}: {resp.text[:200]}")
                return None
        except Exception as e:
            print(f"  [Audio] ElevenLabs异常: {e}")
            return None

    async def _edge_tts(self, text: str, out_path: str):
        voice = self.voice_id if (self.voice_id.startswith("zh-") or self.voice_id.startswith("en-")) else self.DEFAULT_VOICE
        communicate = edge_tts.Communicate(text, voice, rate="-15%")
        await communicate.save(out_path)
