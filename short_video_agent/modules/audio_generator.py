"""TTS 音频生成器 - 使用 edge-tts（微软免费TTS，云端友好）"""
import os
import asyncio
import edge_tts


class AudioGenerator:
    # 中文女声，质量接近ElevenLabs Sarah
    DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"

    def __init__(self, cfg: dict):
        self.api_key = cfg["api"].get("elevenlabs_key", "")  # 保留兼容，不再使用
        self.voice_id = cfg["api"].get("elevenlabs_voice_id", self.DEFAULT_VOICE)
        self.output_dir = cfg["output"]["dir"]
        # 如果voice_id是ElevenLabs格式（非zh-开头），用默认中文声音
        if not self.voice_id.startswith("zh-") and not self.voice_id.startswith("en-"):
            self.voice = self.DEFAULT_VOICE
        else:
            self.voice = self.voice_id

    def generate(self, text: str, filename: str) -> str:
        """生成音频文件，返回文件路径"""
        os.makedirs(self.output_dir, exist_ok=True)
        out_path = os.path.join(self.output_dir, filename)

        asyncio.run(self._generate_async(text, out_path))

        print(f"  [Audio] 已生成: {out_path}")
        return out_path

    async def _generate_async(self, text: str, out_path: str):
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(out_path)

    def get_voice_list(self) -> list:
        """列出可用声音"""
        voices = asyncio.run(edge_tts.list_voices())
        return [v for v in voices if v["Locale"].startswith("zh-")]
