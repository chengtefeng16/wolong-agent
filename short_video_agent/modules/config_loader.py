"""配置加载器 — 合并 base_config + content_config

密钥优先级（从高到低）：
  1. 环境变量  GEMINI_KEY / ELEVENLABS_KEY
  2. 项目根目录 .env 文件（本地开发用，已加入 .gitignore）
  3. base_config.yaml 里的值（留空，不存密钥）
"""
import os
import yaml
from pathlib import Path

_ROOT = Path(__file__).parent.parent


def _load_dotenv():
    """读取项目根目录的 .env 文件，不覆盖已有环境变量"""
    env_path = _ROOT / ".env"
    if not env_path.exists():
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:   # 不覆盖已有 env var
                os.environ[key] = val


def load_config(base_path: str = None) -> dict:
    """加载并合并配置，返回完整 config dict"""
    _load_dotenv()   # 先读 .env，再读 yaml，环境变量优先
    base_path = base_path or _ROOT / "config" / "base_config.yaml"
    with open(base_path) as f:
        cfg = yaml.safe_load(f)

    # 加载内容方向配置并合并
    direction = cfg.get("content_config", "buddhism_zh")

    # 简繁轮换：偶数日简体，奇数日繁体（同频道扩大覆盖）
    import datetime, os
    force_direction = os.environ.get("FORCE_DIRECTION", "")
    if force_direction:
        direction = force_direction
    elif direction == "buddhism_zh":
        day = datetime.date.today().day
        if day % 2 == 1:  # 奇数日用繁体
            tw_path = _ROOT / "config" / "buddhism_zh_tw.yaml"
            if tw_path.exists():
                direction = "buddhism_zh_tw"
        print(f"  [Config] 今日方向: {direction}")

    direction_path = _ROOT / "config" / f"{direction}.yaml"
    if direction_path.exists():
        with open(direction_path) as f:
            direction_cfg = yaml.safe_load(f)
        cfg["direction"] = direction_cfg

    # ── 环境变量覆盖密钥（yaml 为空时生效）────────────────────────────
    env_overrides = {
        "gemini_key":     "GEMINI_KEY",
        "elevenlabs_key": "ELEVENLABS_KEY",
    }
    for cfg_key, env_var in env_overrides.items():
        env_val = os.environ.get(env_var, "").strip()
        if env_val:
            cfg["api"][cfg_key] = env_val
        elif not cfg["api"].get(cfg_key):
            # yaml 也没有值：给出明确错误提示（不静默失败）
            cfg["api"][cfg_key] = ""  # 保留空，调用时自然报错

    # direction 级别的 voice_id 覆盖 base_config（每个方向可用不同音色）
    direction_voice = cfg.get("direction", {}).get("elevenlabs_voice_id")
    if direction_voice:
        cfg["api"]["elevenlabs_voice_id"] = direction_voice

    # 解析相对路径 → 绝对路径
    for key in ["youtube_credentials", "youtube_token", "gsheets_credentials"]:
        p = cfg["api"].get(key, "")
        if p and not os.path.isabs(p):
            cfg["api"][key] = str(_ROOT / p)

    return cfg
