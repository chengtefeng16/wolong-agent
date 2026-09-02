"""Gemini API 脚本生成器

两阶段生成：
  1. 专门生成钩子（去掉佛学框架，按随机抽取的形式写钩子）
  2. 生成正文（把钩子+素材拼进去，让正文自然接钩子往下走）

钩子形式从 direction config 的 hook_styles 随机抽取，
确保每条视频钩子的形状/切入角度不同，避免同质化。
"""
import json
import random
import re

from google import genai


# ── 钩子生成 prompt 模板 ──────────────────────────────────────────────
HOOK_PROMPT = """你是一个短视频钩子专家，专门为面向海外华人的生活类账号写前3秒开场白。

这个视频的核心主题是：{theme_hint}

本条开场钩子请使用「{style_name}」这种形式来写（其它所有规则不变）：
{style_desc}
参考示例（形式参考，内容根据当前主题重新写）：{style_example}

写3个钩子候选，每个独立成句，20字以内，风格各有侧重。

硬性禁止（出现即为不合格）：
✗ "是不是…" "有没有…" "你是否…"（情感共鸣型，太软）
✗ "大多数人搞错了" "这件事很重要" "你必须知道"（空洞标题党）
✗ "今天聊聊…" "其实啊…" "你有没有想过…"（温吞铺垫）
✗ 直接说道理、心灵鸡汤、励志金句

输出JSON格式：
{{
  "hook_1": "第1个钩子（最贴合指定形式）",
  "hook_2": "第2个钩子（同一形式的变体）",
  "hook_3": "第3个钩子（可以略微变形，但不要变成另一种形式）",
  "style_used": "{style_name}"
}}"""

# ── 正文生成 prompt ────────────────────────────────────────────────────
BODY_PROMPT = """你是一位面向海外华人的短视频创作者，风格像隔壁大姐聊天，说话直接，不绕弯。

视频开场已经定好了，第一句是：
「{hook}」

基于以下讲义素材，接着这个开头写完剩余正文：

【素材】
{source_material}

【正文结构】
1. 接钩子（约40字）：自然揭示钩子背后的发现/故事，不要卖关子太久
2. 核心道理（约60字）：把素材的智慧翻译成一个日常生活场景，让人一听就懂
3. 今日练习（约50字）：一个今天就能做的动作，步骤不超过2步，说清楚做什么
4. 收尾（约15字）：温柔收尾，引导关注

【最重要的写作原则：大白话 + 日常场景】
专业词会在说话者和听众之间竖起一堵玻璃墙——听的人先翻译，翻译时距离就来了。
日常场景是直接递到对方手里的东西，不需要翻译，直接进身体记忆。

把素材智慧翻译成日常场景，不是解释概念，是描述一个任何人都经历过的瞬间：
  ✗ "执着会带来痛苦"
  ✓ "那杯茶凉了，你还舍不得倒掉，盯着它，心里那股堵"

  ✗ "当下即圆满"
  ✓ "边吃饭边刷手机，饭吃完了，不知道吃了什么味道"

  ✗ "放下分别心"
  ✓ "同事买了新包，你就心烦了一下，但你自己包里装着什么，你都忘了"

  ✗ "布施自然有功德"
  ✓ "帮人提了次重东西，对方说了句谢谢，你心里那一下轻快"

语言检验标准：写完每句问自己——"我奶奶听得懂吗？" 听不懂就换掉。
禁止出现的词：执着/无常/因缘/正念/觉知/修行/境界/法门/圆满/功德/业力

【格式要求】
- 全程口语化逗号停顿，像说话不像写文章
- 不要重复开场句，直接从第2句开始写
- 正文字数严格控制在130-160字（加上开场句总共150-180字）
- 不分段标注，输出连贯口播稿

输出JSON：
{{
  "body": "（正文，不含开场句，130-160字，全是大白话）",
  "title": "（12字以内，必须符合爆款结构。铁律：①优先用疑问句或反问句，如'你是不是活得太用力了？'②或用对比反差，如'别再比了，你的心会更自由'③禁止陈述句和正能量口号，如'自己点亮自己的路'这种必死④多用'别再比''放下''太用力''羡慕''睡不着'等已验证高效词⑤戳具体痛点，不说抽象道理）",
  "cover_quote": "（直接用开场句，或一句更适合截图的金句，大白话）",
  "tags": ["标签1", "标签2", "标签3"]
}}"""


class ScriptGenerator:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.direction = cfg["direction"]
        self._client = genai.Client(api_key=cfg["api"]["gemini_key"])
        from modules.hotword_engine import HotwordEngine
        self._hotword = HotwordEngine(api_key=cfg["api"].get("youtube_api_key", ""))
        self._model = "gemini-2.5-flash"
        self._bilingual = self.direction.get("language", "zh") == "zh-en"

    def generate(self, materials: list[dict]) -> dict:
        """两阶段生成：先出钩子，再接正文"""
        cols = self.direction["google_sheet"]["columns"]

        # 拼接素材
        material_lines = []
        for m in materials:
            theme = str(m.get(cols["theme"], "")).strip()
            text  = str(m.get(cols["source_text"], "")).strip()
            if text:
                prefix = f"[{theme}] " if theme else ""
                material_lines.append(f"{prefix}{text}")
        source_material = "\n\n".join(material_lines)

        # 从素材里提炼主题提示（给钩子生成用，不提佛法）
        theme_hint = self._extract_theme_hint(source_material)

        # ── 随机抽取钩子形式 ──────────────────────────────────────────
        style = self._pick_hook_style()
        print(f"  [Gemini] 阶段1/2 — 钩子形式: 【{style['name']}】")

        # ── 阶段1：生成3个同一形式的钩子候选 ────────────────────────────
        hook_trad = ""
        if self.direction.get("output_traditional"):
            hook_trad = "\n【重要】钩子必须用繁体中文（台湾用语）。\n"
        hook_prompt = hook_trad + HOOK_PROMPT.format(
            theme_hint=theme_hint,
            style_name=style["name"],
            style_desc=style["desc"],
            style_example=style["example"],
        )
        hook_resp = self._call(hook_prompt)
        hook_data = self._parse_json(hook_resp)

        # 取第1个候选（与指定形式最贴合的那个）
        chosen_hook = hook_data.get("hook_1") or hook_data.get("hook_2") or hook_data.get("hook_3", "")
        print(f"  [Gemini] 选用钩子: 「{chosen_hook}」")
        print(f"           候选2: {hook_data.get('hook_2','')}")
        print(f"           候选3: {hook_data.get('hook_3','')}")

        # ── 易经式随机维度：每天不同受众+基调+结构 ──────────────────────
        import datetime
        day_seed = int(datetime.date.today().strftime("%Y%m%d")) + len(source_material) % 100
        rng = __import__('random').Random(day_seed)

        audiences = self.direction.get("audiences", [])
        tones = self.direction.get("tones", [])
        body_structures = self.direction.get("body_structures", [])

        combo_injection = ""
        if audiences and tones and body_structures:
            audience = rng.choice(audiences)
            tone = rng.choice(tones)
            structure = rng.choice(body_structures)
            # 融入当下热词（三源：自己高效词+YouTube实时+海外情绪）
            hotwords = self._hotword.pick_hotwords(rng, count=2)
            hotword_line = ""
            if hotwords:
                hotword_line = f"- 当下热词（自然融入正文，不生硬堆砌）：{' / '.join(hotwords)}\n"

            combo_injection = f"""
今日创作维度（严格按照这个方向写正文）：
- 核心受众：{audience}
- 情绪基调：{tone}
- 叙事结构：{structure}
{hotword_line}
"""
            print(f"  [Gemini] 今日维度：{tone[:8]}｜{structure[:5]}")
            if hotwords:
                print(f"  [Gemini] 今日热词：{' / '.join(hotwords)}")

        # ── 阶段2：接正文 ──────────────────────────────────────────────
        print(f"  [Gemini] 阶段2/2 — 生成正文...")
        # 繁体中文输出（台港受众）
        traditional_req = ""
        if self.direction.get("output_traditional"):
            traditional_req = "\n\n【重要】全部输出必须使用繁体中文（台湾用语习惯），包括标题、金句、正文、标签，一个简体字都不要出现。\n"

        body_prompt = traditional_req + combo_injection + BODY_PROMPT.format(
            hook=chosen_hook,
            source_material=source_material,
        )
        if self._bilingual:
            body_prompt += """

另外在JSON中加一个字段：
"en_subtitles": 把完整口播稿（开场句+正文合并）按句子分割，每句给英文翻译，字符串数组，每句15词以内。"""

        body_resp = self._call(body_prompt)
        body_data = self._parse_json(body_resp)

        # 拼合最终结果
        full_script = chosen_hook + "，" + body_data.get("body", "")
        char_count  = len(full_script)
        print(f"  [Gemini] 脚本生成完成：{char_count}字")

        result = {
            "title":        body_data.get("title", ""),
            "cover_quote":  body_data.get("cover_quote", chosen_hook),
            "full_script":  full_script,
            "tags":         body_data.get("tags", []),
            "_hook_style":  style["name"],   # 保留供调试
            "_hooks":       hook_data,
        }

        if self._bilingual:
            result["en_subtitles"] = body_data.get("en_subtitles", [])
            print(f"  [Gemini] 英文字幕：{len(result['en_subtitles'])}句")

        return result

    # ── 工具方法 ─────────────────────────────────────────────────────────

    def _pick_hook_style(self) -> dict:
        """从 direction config 的 hook_styles 随机抽取一种钩子形式"""
        styles = self.direction.get("hook_styles", [])
        if not styles:
            # 降级：无配置时用默认窥探型
            return {
                "name": "场景白描",
                "desc": "描述一个具体的画面或动作，留下悬念，不交代原因和结果",
                "example": "昨晚有个人盯着手机屏幕坐了两个小时，什么都没做",
            }
        return random.choice(styles)

    def _extract_theme_hint(self, source_material: str) -> str:
        """从素材文本里提炼情绪/处境主题，给钩子生成用（不提佛法）"""
        text = source_material[:200]
        # 关键词映射到生活化主题描述
        mapping = [
            (["失眠", "难眠", "睡不着"],   "长期睡不好觉、夜里反复想事情的人"),
            (["焦虑", "烦恼", "内耗"],      "在异国容易焦虑、对未来感到不确定的人"),
            (["比较", "嫉妒", "朋友圈"],    "总觉得别人过得比自己好、刷朋友圈难受的人"),
            (["放下", "执着", "执念"],      "某件事放不下、越想越难受的人"),
            (["孤独", "独自", "没人"],      "在国外独自撑着、很久没有真正被理解的人"),
            (["压力", "硬撑", "努力"],      "一直在努力但感觉越来越累的人"),
            (["回家", "故乡", "思念"],      "在国外想家、身份认同有些模糊的人"),
        ]
        for keywords, desc in mapping:
            if any(k in text for k in keywords):
                return desc
        return "在海外打拼、偶尔感到疲惫迷茫的人"

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
                    print(f"  [Gemini] 连接中断，{wait}秒后重试（{attempt+1}/{retries}）...")
                    time.sleep(wait)
                else:
                    raise

    @staticmethod
    def _parse_json(raw: str) -> dict:
        match = re.search(r"\{[\s\S]+\}", raw)
        if not match:
            raise ValueError(f"Gemini 未返回有效 JSON：\n{raw[:400]}")
        return json.loads(match.group())
