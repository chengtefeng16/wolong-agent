#!/bin/bash
# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This script is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

set -euo pipefail

ROOT="$(pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="$ROOT/REAL_DISASTER_BACKUPS_$STAMP"

mkdir -p "$OUT/common" "$OUT/agentos_staging" "$OUT/wolong_staging"

echo "[INFO] 项目根目录: $ROOT"
echo "[INFO] 输出目录: $OUT"

copy_rel_file() {
  local rel="$1"
  local dst="$2"
  if [ -f "$ROOT/$rel" ]; then
    mkdir -p "$(dirname "$dst")"
    cp "$ROOT/$rel" "$dst"
    echo "[OK] $rel"
  else
    echo "[WARN] 缺少文件: $rel"
  fi
}

copy_abs_file() {
  local src="$1"
  local dst="$2"
  if [ -f "$src" ]; then
    mkdir -p "$(dirname "$dst")"
    cp "$src" "$dst"
    echo "[OK] $src"
  else
    echo "[WARN] 缺少文件: $src"
  fi
}

copy_rel_dir() {
  local rel="$1"
  local dst="$2"
  if [ -d "$ROOT/$rel" ]; then
    mkdir -p "$(dirname "$dst")"
    cp -R "$ROOT/$rel" "$dst"
    echo "[OK] $rel/"
  else
    echo "[WARN] 缺少目录: $rel/"
  fi
}

# 0. Git 历史 bundle
if [ -d "$ROOT/.git" ]; then
  git -C "$ROOT" bundle create "$OUT/common/project_history_$STAMP.bundle" --all
  echo "[OK] 已生成 Git 历史 bundle"
else
  echo "[WARN] 当前目录不是 Git 仓库，无法生成 project_history.bundle"
fi

# 1. 当前工作树快照
(
  cd "$ROOT"
  zip -qr "$OUT/common/current_worktree_snapshot_$STAMP.zip" . \
    -x ".git/*" \
    -x ".venv/*" \
    -x ".venv_delivery/*" \
    -x "node_modules/*" \
    -x "__pycache__/*" \
    -x ".mypy_cache/*" \
    -x ".pytest_cache/*" \
    -x "dist/*" \
    -x "build/*" \
    -x "tmp/*" \
    -x "tmp_debug/*" \
    -x "REAL_DISASTER_BACKUPS_*/*"
)
echo "[OK] 已生成当前工作树代码快照"

WORKTREE_ZIP="$OUT/common/current_worktree_snapshot_$STAMP.zip"
HISTORY_BUNDLE="$OUT/common/project_history_$STAMP.bundle"

# ================================================================
# AgentOS 六要素
# ================================================================

mkdir -p "$OUT/agentos_staging/01_完整代码包"
copy_rel_file "PROJECT_CONSTITUTION.md" "$OUT/agentos_staging/01_完整代码包/PROJECT_CONSTITUTION.md"
copy_rel_file "PROJECT_MEMO.md" "$OUT/agentos_staging/01_完整代码包/PROJECT_MEMO.md"
copy_rel_file "PROJECT_CHECKLIST.md" "$OUT/agentos_staging/01_完整代码包/PROJECT_CHECKLIST.md"
copy_rel_dir "qianqiu_os" "$OUT/agentos_staging/01_完整代码包/qianqiu_os"
copy_rel_file "main.py" "$OUT/agentos_staging/01_完整代码包/main.py"
copy_rel_file "agents.py" "$OUT/agentos_staging/01_完整代码包/agents.py"
copy_abs_file "$WORKTREE_ZIP" "$OUT/agentos_staging/01_完整代码包/current_worktree_snapshot_$STAMP.zip"
copy_abs_file "$HISTORY_BUNDLE" "$OUT/agentos_staging/01_完整代码包/project_history_$STAMP.bundle"

mkdir -p "$OUT/agentos_staging/02_关键文档说明"
copy_rel_file "PROJECT_CONSTITUTION.md" "$OUT/agentos_staging/02_关键文档说明/PROJECT_CONSTITUTION.md"
copy_rel_file "PROJECT_MEMO.md" "$OUT/agentos_staging/02_关键文档说明/PROJECT_MEMO.md"
copy_rel_file "PROJECT_CHECKLIST.md" "$OUT/agentos_staging/02_关键文档说明/PROJECT_CHECKLIST.md"
copy_rel_file "Agent Os 新主干结构图正式执行版260320.docx" "$OUT/agentos_staging/02_关键文档说明/AgentOS_新主干结构图正式执行版_260320.docx"
copy_rel_file "统一 Agent 协议 V1边界优先版260320.docx" "$OUT/agentos_staging/02_关键文档说明/统一_Agent_协议_V1_边界优先版_260320.docx"
copy_rel_file "Agent Os 卧龙agent 边界表与五张关键映射表260320（v1）.pdf" "$OUT/agentos_staging/02_关键文档说明/AgentOS_卧龙Agent_边界表与五张关键映射表_260320_v1.pdf"
copy_rel_file "Agent Os 卧龙agent 旧模块映射与兼容迁移清单260320.pdf" "$OUT/agentos_staging/02_关键文档说明/AgentOS_卧龙Agent_旧模块映射与兼容迁移清单_260320.pdf"

mkdir -p "$OUT/agentos_staging/03_运行态与治理数据"
copy_rel_dir "qianqiu_os/runtime_views" "$OUT/agentos_staging/03_运行态与治理数据/runtime_views"
copy_rel_dir "qianqiu_os/runtime_exports" "$OUT/agentos_staging/03_运行态与治理数据/runtime_exports"
copy_rel_file "qianqiu_os/runtime_exports/fixed_delivery_state_v1.json" "$OUT/agentos_staging/03_运行态与治理数据/fixed_delivery_state_v1.json"
copy_rel_file "qianqiu_os/runtime_exports/export_index_latest.json" "$OUT/agentos_staging/03_运行态与治理数据/export_index_latest.json"

mkdir -p "$OUT/agentos_staging/04_阶段总结与主干总表"
copy_rel_file "qianqiu_os/runtime_exports/weekly/agentos_weekly_report_latest.pdf" "$OUT/agentos_staging/04_阶段总结与主干总表/agentos_weekly_report_latest.pdf"
copy_rel_file "qianqiu_os/runtime_exports/weekly/agentos_weekly_report_latest.md" "$OUT/agentos_staging/04_阶段总结与主干总表/agentos_weekly_report_latest.md"
copy_rel_file "qianqiu_os/runtime_exports/nightly/nightly_checkpoint_latest.pdf" "$OUT/agentos_staging/04_阶段总结与主干总表/nightly_checkpoint_latest.pdf"
copy_rel_file "qianqiu_os/runtime_exports/nightly/nightly_checkpoint_latest.md" "$OUT/agentos_staging/04_阶段总结与主干总表/nightly_checkpoint_latest.md"

mkdir -p "$OUT/agentos_staging/05_恢复说明与续接说明"
cat > "$OUT/agentos_staging/05_恢复说明与续接说明/README_恢复说明.txt" <<EOF
AgentOS 恢复顺序（$STAMP）
1. 先读 02_关键文档说明 下的宪法 / 备忘 / checklist / 主干结构 / 统一协议 / 映射文档
2. 再读 03_运行态与治理数据 下的 runtime_exports / runtime_views / fixed_delivery_state
3. 再读 04_阶段总结与主干总表 下的 weekly / nightly 最新文件
4. 代码恢复时先用 01_完整代码包/current_worktree_snapshot_$STAMP.zip
5. 若存在 Git 历史包，再用 01_完整代码包/project_history_$STAMP.bundle
EOF

mkdir -p "$OUT/agentos_staging/06_规则与宪法固化"
copy_rel_file "PROJECT_CONSTITUTION.md" "$OUT/agentos_staging/06_规则与宪法固化/PROJECT_CONSTITUTION.md"
copy_rel_file "PROJECT_MEMO.md" "$OUT/agentos_staging/06_规则与宪法固化/PROJECT_MEMO.md"
copy_rel_file "PROJECT_CHECKLIST.md" "$OUT/agentos_staging/06_规则与宪法固化/PROJECT_CHECKLIST.md"

# ================================================================
# 卧龙 六要素
# ================================================================

mkdir -p "$OUT/wolong_staging/01_完整代码包"
copy_rel_file "PROJECT_CONSTITUTION.md" "$OUT/wolong_staging/01_完整代码包/PROJECT_CONSTITUTION.md"
copy_rel_file "PROJECT_MEMO.md" "$OUT/wolong_staging/01_完整代码包/PROJECT_MEMO.md"
copy_rel_file "PROJECT_CHECKLIST.md" "$OUT/wolong_staging/01_完整代码包/PROJECT_CHECKLIST.md"
copy_rel_dir "qianqiu_os/agents" "$OUT/wolong_staging/01_完整代码包/qianqiu_os/agents"
copy_rel_dir "qianqiu_os/managers" "$OUT/wolong_staging/01_完整代码包/qianqiu_os/managers"
copy_rel_dir "qianqiu_os/tools" "$OUT/wolong_staging/01_完整代码包/qianqiu_os/tools"
copy_rel_dir "qianqiu_os/data" "$OUT/wolong_staging/01_完整代码包/qianqiu_os/data"
copy_rel_dir "qianqiu_os/services" "$OUT/wolong_staging/01_完整代码包/qianqiu_os/services"
copy_abs_file "$WORKTREE_ZIP" "$OUT/wolong_staging/01_完整代码包/current_worktree_snapshot_$STAMP.zip"
copy_abs_file "$HISTORY_BUNDLE" "$OUT/wolong_staging/01_完整代码包/project_history_$STAMP.bundle"

mkdir -p "$OUT/wolong_staging/02_关键文档说明"
copy_rel_file "PROJECT_CONSTITUTION.md" "$OUT/wolong_staging/02_关键文档说明/PROJECT_CONSTITUTION.md"
copy_rel_file "PROJECT_MEMO.md" "$OUT/wolong_staging/02_关键文档说明/PROJECT_MEMO.md"
copy_rel_file "PROJECT_CHECKLIST.md" "$OUT/wolong_staging/02_关键文档说明/PROJECT_CHECKLIST.md"
copy_rel_file "Agent Os 新主干结构图正式执行版260320.docx" "$OUT/wolong_staging/02_关键文档说明/AgentOS_新主干结构图正式执行版_260320.docx"
copy_rel_file "统一 Agent 协议 V1边界优先版260320.docx" "$OUT/wolong_staging/02_关键文档说明/统一_Agent_协议_V1_边界优先版_260320.docx"
copy_rel_file "Agent Os 卧龙agent 边界表与五张关键映射表260320（v1）.pdf" "$OUT/wolong_staging/02_关键文档说明/AgentOS_卧龙Agent_边界表与五张关键映射表_260320_v1.pdf"
copy_rel_file "Agent Os 卧龙agent 旧模块映射与兼容迁移清单260320.pdf" "$OUT/wolong_staging/02_关键文档说明/AgentOS_卧龙Agent_旧模块映射与兼容迁移清单_260320.pdf"

mkdir -p "$OUT/wolong_staging/03_运行态与治理数据"
copy_rel_dir "qianqiu_os/runtime_views" "$OUT/wolong_staging/03_运行态与治理数据/runtime_views"
copy_rel_dir "qianqiu_os/runtime_exports" "$OUT/wolong_staging/03_运行态与治理数据/runtime_exports"
copy_rel_file "qianqiu_os/runtime_exports/fixed_delivery_state_v1.json" "$OUT/wolong_staging/03_运行态与治理数据/fixed_delivery_state_v1.json"
copy_rel_file "qianqiu_os/runtime_exports/export_index_latest.json" "$OUT/wolong_staging/03_运行态与治理数据/export_index_latest.json"

mkdir -p "$OUT/wolong_staging/04_阶段总结与主干总表"
copy_rel_file "qianqiu_os/runtime_exports/weekly/wolong_weekly_report_latest.pdf" "$OUT/wolong_staging/04_阶段总结与主干总表/wolong_weekly_report_latest.pdf"
copy_rel_file "qianqiu_os/runtime_exports/weekly/wolong_weekly_report_latest.md" "$OUT/wolong_staging/04_阶段总结与主干总表/wolong_weekly_report_latest.md"
copy_rel_file "qianqiu_os/runtime_exports/nightly/nightly_checkpoint_latest.pdf" "$OUT/wolong_staging/04_阶段总结与主干总表/nightly_checkpoint_latest.pdf"
copy_rel_file "qianqiu_os/runtime_exports/nightly/nightly_checkpoint_latest.md" "$OUT/wolong_staging/04_阶段总结与主干总表/nightly_checkpoint_latest.md"

mkdir -p "$OUT/wolong_staging/05_恢复说明与续接说明"
cat > "$OUT/wolong_staging/05_恢复说明与续接说明/README_恢复说明.txt" <<EOF
卧龙Agent 恢复顺序（$STAMP）
1. 先读 02_关键文档说明 下的宪法 / 备忘 / checklist / 主干结构 / 统一协议 / 映射文档
2. 再读 03_运行态与治理数据 下的 runtime_exports / runtime_views / fixed_delivery_state
3. 再读 04_阶段总结与主干总表 下的 weekly / nightly 最新文件
4. 代码恢复时先用 01_完整代码包/current_worktree_snapshot_$STAMP.zip
5. 若存在 Git 历史包，再用 01_完整代码包/project_history_$STAMP.bundle
EOF

mkdir -p "$OUT/wolong_staging/06_规则与宪法固化"
copy_rel_file "PROJECT_CONSTITUTION.md" "$OUT/wolong_staging/06_规则与宪法固化/PROJECT_CONSTITUTION.md"
copy_rel_file "PROJECT_MEMO.md" "$OUT/wolong_staging/06_规则与宪法固化/PROJECT_MEMO.md"
copy_rel_file "PROJECT_CHECKLIST.md" "$OUT/wolong_staging/06_规则与宪法固化/PROJECT_CHECKLIST.md"

# ================================================================
# 打包
# ================================================================
(
  cd "$OUT/agentos_staging"
  zip -qr "$OUT/AgentOS_灾难备份六要素_$STAMP.zip" .
)
(
  cd "$OUT/wolong_staging"
  zip -qr "$OUT/卧龙Agent_灾难备份六要素_$STAMP.zip" .
)

mkdir -p "$OUT/full_code_package"
copy_abs_file "$WORKTREE_ZIP" "$OUT/full_code_package/current_worktree_snapshot_$STAMP.zip"
copy_abs_file "$HISTORY_BUNDLE" "$OUT/full_code_package/project_history_$STAMP.bundle"
cat > "$OUT/full_code_package/README.txt" <<EOF
完整代码与历史包（$STAMP）
- current_worktree_snapshot_$STAMP.zip : 当前代码快照
- project_history_$STAMP.bundle        : Git 全历史（如果当前目录是 Git 仓库）
EOF
(
  cd "$OUT/full_code_package"
  zip -qr "$OUT/完整代码与历史包_$STAMP.zip" .
)

rm -rf "$OUT/agentos_staging" "$OUT/wolong_staging" "$OUT/full_code_package"

echo
echo "================================================"
echo "[完成] 已生成 3 个真正用于本机项目的备份压缩包"
echo "[1] $OUT/AgentOS_灾难备份六要素_$STAMP.zip"
echo "[2] $OUT/卧龙Agent_灾难备份六要素_$STAMP.zip"
echo "[3] $OUT/完整代码与历史包_$STAMP.zip"
echo "================================================"
