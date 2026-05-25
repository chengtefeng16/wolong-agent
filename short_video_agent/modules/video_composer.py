"""
竖屏9:16 短视频合成器
输入：音频文件 + 脚本文本
输出：mp4 视频（背景 + 字幕 + 音频）
"""
import os
import textwrap
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from moviepy import AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips


_ASSETS = Path(__file__).parent.parent / "assets"
_FONTS_DIR = _ASSETS / "fonts"


class VideoComposer:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.vcfg = cfg["video"]
        self.scfg = cfg["subtitle"]
        self.output_dir = cfg["output"]["dir"]
        self.W = self.vcfg["width"]
        self.H = self.vcfg["height"]
        self.fps = self.vcfg["fps"]
        self._font_cache: dict = {}

    # ------------------------------------------------------------------ #
    # 公开接口                                                              #
    # ------------------------------------------------------------------ #

    def compose(
        self,
        audio_path: str,
        script_text: str,
        output_filename: str,
        background_path: str = None,
        title: str = "",
        cover_quote: str = "",
    ) -> str:
        """
        合成视频主入口。
        audio_path       : 音频文件路径 (.mp3/.wav)
        script_text      : 全文脚本（用于字幕分段）
        output_filename  : 输出文件名 (不含路径)
        background_path  : 背景图片路径，None 则用渐变色背景
        title            : 视频标题（显示在顶部）
        cover_quote      : 封面金句（封面帧使用）
        """
        os.makedirs(self.output_dir, exist_ok=True)
        out_path = os.path.join(self.output_dir, output_filename)

        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration

        # 1. 生成背景帧（PIL → numpy array → ImageClip）
        bg_img = self._make_background(background_path)

        # 2. 字幕分段（按时间均匀分配）
        subtitle_clips = self._make_subtitle_clips(script_text, duration, bg_img)

        # 3. 合成：背景 + 字幕层叠
        bg_clip = ImageClip(self._pil_to_array(bg_img), duration=duration)
        all_clips = [bg_clip] + subtitle_clips

        video = CompositeVideoClip(all_clips, size=(self.W, self.H))
        video = video.with_audio(audio_clip)
        video = video.with_duration(duration)

        # 4. 写出 MP4
        video.write_videofile(
            out_path,
            fps=self.fps,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=os.path.join(self.output_dir, "_tmp_audio.m4a"),
            remove_temp=True,
            logger=None,
        )

        print(f"  [Video] 已合成: {out_path}  ({duration:.1f}s)")
        return out_path

    def make_cover_image(self, title: str, cover_quote: str, output_filename: str, background_path: str = None) -> str:
        """生成封面图（1080x1920 JPG）"""
        os.makedirs(self.output_dir, exist_ok=True)
        out_path = os.path.join(self.output_dir, output_filename)

        img = self._make_background(background_path).copy()
        draw = ImageDraw.Draw(img)

        # 金句（居中大字）
        self._draw_centered_text(
            draw, cover_quote,
            y_center=self.H * 0.42,
            font_size=self.scfg["font_size"] + 10,
            max_chars=12,
            bold=True,
        )

        # 标题（小字，金句下方）
        self._draw_centered_text(
            draw, title,
            y_center=self.H * 0.58,
            font_size=self.scfg["font_size"] - 14,
            max_chars=16,
        )

        img.save(out_path, "JPEG", quality=92)
        print(f"  [Cover] 已生成: {out_path}")
        return out_path

    # ------------------------------------------------------------------ #
    # 背景生成                                                              #
    # ------------------------------------------------------------------ #

    def _make_background(self, background_path: str = None) -> Image.Image:
        if background_path and os.path.exists(background_path):
            img = Image.open(background_path).convert("RGB")
            # 裁剪/缩放到 9:16
            img = self._crop_to_ratio(img, self.W, self.H)
            return img
        return self._gradient_background()

    def _gradient_background(self) -> Image.Image:
        """默认渐变背景：深蓝紫渐变"""
        img = Image.new("RGB", (self.W, self.H))
        draw = ImageDraw.Draw(img)

        top_color = (12, 10, 35)       # 深夜紫
        bottom_color = (35, 20, 60)    # 深紫

        for y in range(self.H):
            t = y / self.H
            r = int(top_color[0] * (1 - t) + bottom_color[0] * t)
            g = int(top_color[1] * (1 - t) + bottom_color[1] * t)
            b = int(top_color[2] * (1 - t) + bottom_color[2] * t)
            draw.line([(0, y), (self.W, y)], fill=(r, g, b))

        # 中央光晕
        self._draw_glow(draw, self.W // 2, int(self.H * 0.38), 380, (80, 60, 140, 40))

        return img

    def _draw_glow(self, draw: ImageDraw.Draw, cx: int, cy: int, radius: int, color: tuple):
        """半透明光晕（用椭圆叠加模拟）"""
        for i in range(8, 0, -1):
            r = int(radius * i / 8)
            alpha = int(color[3] * (1 - i / 10))
            # PIL 不支持 RGBA 在 RGB 图上直接画，用覆盖色模拟
            intensity = int(30 * (1 - i / 9))
            c = (
                min(255, color[0] + intensity),
                min(255, color[1] + intensity),
                min(255, color[2] + intensity),
            )
            draw.ellipse(
                [cx - r, cy - r, cx + r, cy + r],
                fill=None,
                outline=c,
                width=2,
            )

    @staticmethod
    def _crop_to_ratio(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
        src_w, src_h = img.size
        target_ratio = target_w / target_h
        src_ratio = src_w / src_h

        if src_ratio > target_ratio:
            # 图片太宽，按高度缩放后裁宽
            new_h = target_h
            new_w = int(src_w * target_h / src_h)
        else:
            new_w = target_w
            new_h = int(src_h * target_w / src_w)

        img = img.resize((new_w, new_h), Image.LANCZOS)
        left = (new_w - target_w) // 2
        top = (new_h - target_h) // 2
        return img.crop((left, top, left + target_w, top + target_h))

    # ------------------------------------------------------------------ #
    # 字幕生成                                                              #
    # ------------------------------------------------------------------ #

    def _make_subtitle_clips(self, script_text: str, duration: float, bg_img: Image.Image) -> list:
        """将脚本按句子拆分，均匀分配时间，生成字幕 ImageClip 列表"""
        sentences = self._split_sentences(script_text)
        if not sentences:
            return []

        time_per_char = duration / max(sum(len(s) for s in sentences), 1)
        clips = []
        current_time = 0.0

        for sentence in sentences:
            seg_duration = max(len(sentence) * time_per_char, 1.0)
            seg_duration = min(seg_duration, duration - current_time)
            if seg_duration <= 0:
                break

            # 把字幕画到背景副本上
            frame_img = self._draw_subtitle_frame(bg_img, sentence)
            frame_arr = self._pil_to_array(frame_img)

            clip = (
                ImageClip(frame_arr)
                .with_start(current_time)
                .with_duration(seg_duration)
            )
            clips.append(clip)
            current_time += seg_duration

        return clips

    def _draw_subtitle_frame(self, bg_img: Image.Image, text: str) -> Image.Image:
        """在背景副本上绘制字幕，返回新图"""
        img = bg_img.copy()
        draw = ImageDraw.Draw(img)

        max_chars = self.scfg["max_chars_per_line"]
        lines = textwrap.wrap(text, width=max_chars)

        font_size = self.scfg["font_size"]
        font = self._get_font(font_size)
        line_height = int(font_size * self.scfg["line_height"])

        total_height = line_height * len(lines)
        y_start = self.H - self.scfg["padding_bottom"] - total_height

        for i, line in enumerate(lines):
            y = y_start + i * line_height
            # 测量文字宽度以居中
            bbox = draw.textbbox((0, 0), line, font=font)
            text_w = bbox[2] - bbox[0]
            x = (self.W - text_w) // 2

            # 阴影
            shadow_off = self.scfg["shadow_offset"]
            shadow_color = tuple(self.scfg["shadow_color"])
            draw.text((x + shadow_off, y + shadow_off), line, font=font, fill=shadow_color)

            # 主文字
            text_color = tuple(self.scfg["color"])
            draw.text((x, y), line, font=font, fill=text_color)

        return img

    def _draw_centered_text(
        self, draw: ImageDraw.Draw, text: str,
        y_center: float, font_size: int,
        max_chars: int = 14, bold: bool = False,
    ):
        font = self._get_font(font_size)
        lines = textwrap.wrap(text, width=max_chars)
        line_height = int(font_size * 1.5)
        total_h = line_height * len(lines)
        y_start = int(y_center - total_h / 2)

        for i, line in enumerate(lines):
            y = y_start + i * line_height
            bbox = draw.textbbox((0, 0), line, font=font)
            x = (self.W - (bbox[2] - bbox[0])) // 2

            # 阴影
            draw.text((x + 3, y + 3), line, font=font, fill=(0, 0, 0))
            draw.text((x, y), line, font=font, fill=(255, 255, 255))

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """按中文标点拆分句子"""
        import re
        sentences = re.split(r"(?<=[。！？，…])", text)
        return [s.strip() for s in sentences if s.strip()]

    # ------------------------------------------------------------------ #
    # 字体加载                                                              #
    # ------------------------------------------------------------------ #

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        if size in self._font_cache:
            return self._font_cache[size]

        font_path = self._find_chinese_font()
        if font_path:
            font = ImageFont.truetype(str(font_path), size)
        else:
            # 系统默认字体（不支持中文但至少能运行）
            font = ImageFont.load_default(size=size)

        self._font_cache[size] = font
        return font

    @staticmethod
    def _find_chinese_font() -> Path | None:
        """自动查找可用中文字体"""
        candidates = [
            # 项目内置（优先）
            _FONTS_DIR / "NotoSansSC-Regular.ttf",
            _FONTS_DIR / "NotoSansSC-Bold.ttf",
            # macOS 系统字体
            Path("/Library/Fonts/Arial Unicode.ttf"),
            Path("/Library/Fonts/Arial Unicode MS.ttf"),
            Path("/System/Library/Fonts/STHeiti Medium.ttc"),
            Path("/System/Library/Fonts/STHeiti Light.ttc"),
            Path("/System/Library/Fonts/PingFang.ttc"),
            # Linux
            Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
            Path("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"),
        ]
        for p in candidates:
            if p.exists():
                return p
        return None

    # ------------------------------------------------------------------ #
    # 工具                                                                  #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _pil_to_array(img: Image.Image):
        import numpy as np
        return np.array(img)


    def compose_bilingual(
        self,
        audio_path: str,
        script_data: dict,
        output_filename: str,
        background_path: str = None,
    ) -> str:
        """双语字幕版本：中文主字幕 + 英文副字幕"""
        os.makedirs(self.output_dir, exist_ok=True)
        out_path = os.path.join(self.output_dir, output_filename)

        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration

        bg_img = self._make_background(background_path)
        script_text = script_data.get("full_script", "")
        en_subtitles = script_data.get("en_subtitles", [])

        subtitle_clips = self._make_bilingual_subtitle_clips(
            script_text, en_subtitles, duration, bg_img
        )

        bg_clip = ImageClip(self._pil_to_array(bg_img), duration=duration)
        all_clips = [bg_clip] + subtitle_clips

        video = CompositeVideoClip(all_clips, size=(self.W, self.H))
        video = video.with_audio(audio_clip)
        video = video.with_duration(duration)

        video.write_videofile(
            out_path,
            fps=self.fps,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=os.path.join(self.output_dir, "_tmp_audio.m4a"),
            remove_temp=True,
            logger=None,
        )

        print(f"  [Video] 双语视频已合成: {out_path}  ({duration:.1f}s)")
        return out_path

    def _make_bilingual_subtitle_clips(
        self, zh_text: str, en_subtitles: list, duration: float, bg_img
    ) -> list:
        zh_sentences = self._split_sentences(zh_text)
        if not zh_sentences:
            return []

        # 对齐中英句子数量
        while len(en_subtitles) < len(zh_sentences):
            en_subtitles.append("")
        en_subtitles = en_subtitles[:len(zh_sentences)]

        time_per_char = duration / max(sum(len(s) for s in zh_sentences), 1)
        clips = []
        current_time = 0.0

        for zh, en in zip(zh_sentences, en_subtitles):
            seg_duration = max(len(zh) * time_per_char, 1.0)
            seg_duration = min(seg_duration, duration - current_time)
            if seg_duration <= 0:
                break

            frame_img = self._draw_bilingual_frame(bg_img, zh, en)
            frame_arr = self._pil_to_array(frame_img)

            clip = (
                ImageClip(frame_arr)
                .with_start(current_time)
                .with_duration(seg_duration)
            )
            clips.append(clip)
            current_time += seg_duration

        return clips

    def _draw_bilingual_frame(self, bg_img, zh_text: str, en_text: str):
        img = bg_img.copy()
        draw = ImageDraw.Draw(img)

        font_size_zh = self.scfg["font_size"]
        font_size_en = max(font_size_zh - 16, 24)

        font_zh = self._get_font(font_size_zh)
        font_en = self._get_font(font_size_en)

        line_height_zh = int(font_size_zh * self.scfg["line_height"])
        line_height_en = int(font_size_en * 1.4)
        gap = 16

        # 中文行
        zh_lines = textwrap.wrap(zh_text, width=self.scfg["max_chars_per_line"])
        zh_total_h = line_height_zh * len(zh_lines)

        # 英文行
        en_lines = textwrap.wrap(en_text, width=26) if en_text else []
        en_total_h = line_height_en * len(en_lines)

        total_h = zh_total_h + (gap + en_total_h if en_lines else 0)
        y_start = self.H - self.scfg["padding_bottom"] - total_h

        # 画中文
        for i, line in enumerate(zh_lines):
            y = y_start + i * line_height_zh
            bbox = draw.textbbox((0, 0), line, font=font_zh)
            x = (self.W - (bbox[2] - bbox[0])) // 2
            shadow_off = self.scfg["shadow_offset"]
            draw.text((x + shadow_off, y + shadow_off), line, font=font_zh,
                      fill=tuple(self.scfg["shadow_color"]))
            draw.text((x, y), line, font=font_zh, fill=tuple(self.scfg["color"]))

        # 画英文（灰白色，比中文小）
        if en_lines:
            en_y_start = y_start + zh_total_h + gap
            for i, line in enumerate(en_lines):
                y = en_y_start + i * line_height_en
                bbox = draw.textbbox((0, 0), line, font=font_en)
                x = (self.W - (bbox[2] - bbox[0])) // 2
                draw.text((x + 2, y + 2), line, font=font_en, fill=(0, 0, 0))
                draw.text((x, y), line, font=font_en, fill=(200, 200, 200))

        return img
