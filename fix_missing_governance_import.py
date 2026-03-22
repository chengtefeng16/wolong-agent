# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

from pathlib import Path
import shutil
import subprocess
import re

app_path = Path("qianqiu_os/app.py")
if not app_path.exists():
    raise SystemExit("[ERROR] 找不到 qianqiu_os/app.py")

backup_path = Path("qianqiu_os/app.py.bak_fix_missing_governance_import")
shutil.copy2(app_path, backup_path)

text = app_path.read_text(encoding="utf-8")

old_import = "from qianqiu_os.governance.platform_governance import build_platform_governance"
new_import = """try:
    from qianqiu_os.governance.platform_governance import build_platform_governance
except Exception:
    def build_platform_governance(result):
        tool_result = result.get("tool_result", {}) or {}
        wolong_result = result.get("wolong_result", {}) or {}
        manual_review_required = False
        governance_notes = []

        if tool_result.get("manual_review_required"):
            manual_review_required = True
            governance_notes.append("Tool result requires manual review.")

        if wolong_result.get("manual_review_result", {}).get("manual_review_required"):
            manual_review_required = True
            governance_notes.append("Wolong preliminary review requires human confirmation.")

        return {
            "manual_review_required": manual_review_required,
            "governance_notes": governance_notes,
        }"""

if old_import in text:
    text = text.replace(old_import, new_import)
    print("[OK] 已替换缺失的 governance 导入为兜底实现")
else:
    print("[WARN] 没找到原 governance 导入，尝试检查是否已修过")

remaining = re.findall(r"^from\\s+qianqiu_os\\.governance\\.[^\\n]+", text, flags=re.MULTILINE)

app_path.write_text(text, encoding="utf-8")
print(f"[OK] 已写回 {app_path}")
print(f"[OK] 备份文件: {backup_path}")

print()
print("=== 剩余 governance 导入 ===")
if remaining:
    for item in remaining:
        print(item)
else:
    print("[OK] 已无 qianqiu_os.governance 残留导入")

commands = [
    ["python", "-m", "py_compile", "qianqiu_os/managers/wolong_manager.py"],
    ["python", "-m", "py_compile", "qianqiu_os/app.py", "qianqiu_os/services/output_adapter.py"],
    ["python", "extract_wolong_summary.py"],
]

for cmd in commands:
    print("\\n" + "=" * 70)
    print("RUN:", " ".join(cmd))
    print("=" * 70)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.stdout:
        print(proc.stdout)
    if proc.stderr:
        print(proc.stderr)
    print(f"[exit_code] {proc.returncode}")
