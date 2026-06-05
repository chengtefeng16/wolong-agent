"""配置加载器 — 合并 base_config + content_config

密钥优先级（从高到低）：
  1. 环境变量  GEMINI_KEY / ELEVENLABS_KEY
  2. base_config.yaml 里的值（仅本地调试用，生产环境保持空字符串）
"""
import os
import yaml
from pathlib import Path

_ROOT = Path(__file__).parent.parent


def load_config(base_path: str = None) -> dict:
    """加载并合并配置，返回完整 config dict"""
    base_path = base_path or _ROOT / "config" / "base_config.yaml"
    with open(base_path) as f:
        cfg = yaml.safe_load(f)

    # 加载内容方向配置并合并
    direction = cfg.get("content_config", "buddhism_zh")
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
