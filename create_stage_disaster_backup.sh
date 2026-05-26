# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

#!/bin/bash

set -e

PROJECT_ROOT="$(pwd)"
PROJECT_NAME="AgentOS_关键节点灾难恢复备份"
STAGE_TAG="stage_reflection_kg_humanloop_h5_v4"
TIMESTAMP="$(date +"%Y%m%d_%H%M%S")"
BACKUP_ROOT="${PROJECT_ROOT}/disaster_recovery_backups"
BACKUP_DIR="${BACKUP_ROOT}/${PROJECT_NAME}_${STAGE_TAG}_${TIMESTAMP}"
EXPORT_DIR="${BACKUP_DIR}/01_完整代码包"
DOC_DIR="${BACKUP_DIR}/02_中文详细说明书"
ENV_DIR="${BACKUP_DIR}/03_配置与运行环境说明"
SNAPSHOT_DIR="${BACKUP_DIR}/04_数据与结构快照"
RESTORE_DIR="${BACKUP_DIR}/05_恢复操作说明"
VERIFY_DIR="${BACKUP_DIR}/06_阶段版本标识与验证结论"

mkdir -p "${EXPORT_DIR}" "${DOC_DIR}" "${ENV_DIR}" "${SNAPSHOT_DIR}" "${RESTORE_DIR}" "${VERIFY_DIR}"

echo "[1/8] 复制完整代码 ..."
rsync -av \
  --exclude "__pycache__" \
  --exclude ".git" \
  --exclude ".DS_Store" \
  --exclude "venv" \
  --exclude "node_modules" \
  --exclude "disaster_recovery_backups" \
  "${PROJECT_ROOT}/" "${EXPORT_DIR}/project_full_copy/" >/dev/null

echo "[2/8] 生成代码清单 ..."
find "${PROJECT_ROOT}" -type f \
  \( -name "*.py" -o -name "*.json" -o -name "*.md" -o -name "*.txt" -o -name "*.sh" -o -name "*.tsx" -o -name "*.ts" -o -name "*.jsx" -o -name "*.js" \) \
  -not -path "*/__pycache__/*" \
  -not -path "*/venv/*" \
  -not -path "*/node_modules/*" \
  -not -path "*/.git/*" \
  | sed "s#${PROJECT_ROOT}/##" \
  | sort > "${SNAPSHOT_DIR}/代码文件清单.txt"

find "${PROJECT_ROOT}" -type f \
  \( -name "*.py" -o -name "*.json" -o -name "*.md" -o -name "*.txt" -o -name "*.sh" -o -name "*.tsx" -o -name "*.ts" -o -name "*.jsx" -o -name "*.js" \) \
  -not -path "*/__pycache__/*" \
  -not -path "*/venv/*" \
  -not -path "*/node_modules/*" \
  -not -path "*/.git/*" \
  -print0 | xargs -0 wc -l > "${SNAPSHOT_DIR}/代码行数统计.txt" || true

echo "[3/8] 生成中文详细说明书 ..."
cat > "${DOC_DIR}/AgentOS_本阶段中文详细说明书.md" <<DOC
# AgentOS / 千秋基座 本阶段中文详细说明书

## 一、当前备份定位
本次备份属于关键节点灾难恢复备份。

本轮备份重点覆盖以下阶段成果：
1. 反思层第一刀正式接入主链
2. 知识图谱第一刀正式接入主链
3. 人机协同闭环层第一刀正式接入主链
4. H5 控制台第四刀当前满意版固化

本轮备份目标：
- 防止主干阶段成果丢失
- 保证后续继续开发前可快速恢复
- 让系统在出现误改、误删、分支偏航时可以回退到当前稳定节点

## 二、本阶段主干新增能力概览

### 1. 反思层第一刀
当前已正式接入主链：
- ReflectionManager
- decision_trace
- execution_trace
- error_reflection
- success_reflection
- reflection_log

当前意义：
- 决策开始可追溯
- 执行开始可回看
- 成功开始可沉淀
- 失败开始具备反思入口

### 2. 知识图谱第一刀
当前已正式接入主链：
- KnowledgeGraphManager
- GraphNode
- GraphEdge
- KnowledgeGraphSnapshot
- knowledge_graph

当前最小实体：
- customer
- country
- product
- order
- risk
- event

当前最小关系：
- customer -> interested_in -> product
- product -> related_to -> country
- order -> belongs_to -> customer
- order -> has_risk -> risk
- event -> affects -> country
- event -> affects -> product

当前意义：
- 平台开始把业务对象组织成点
- 平台开始把业务关系组织成线
- 为后续规律提炼、经验回灌、关系理解打下基础

### 3. 人机协同闭环层第一刀
当前已正式接入主链：
- HumanMachineLoopManager
- human_decision
- machine_execution
- result_feedback
- reflection_entry
- next_round_adjustment
- human_machine_loop_log

当前意义：
- 人类拍板权开始进入系统结构
- 机器执行不再孤立
- 执行结果开始统一回流
- 反思层开始进入闭环
- 平台开始具备“下一轮调整意识”

### 4. H5 控制台第四刀当前满意版
当前已形成四层结构：
- 总览
- 控制
- 反馈
- 总控 / 详情

当前已明确：
- 各 Agent 工作状态优先展示
- 总算力分配示意保留，但压缩为更小更集中的模块
- 保留业务警示弹窗
- 保留代码 / 运行警示弹窗
- 当前版本先作为阶段性可用管理台基线版

## 三、当前平台主干结构判断
当前 AgentOS 已形成更完整主干趋势：

规划
-> 执行
-> 守护
-> 反思
-> 图谱沉淀
-> 人机闭环调整
-> 再优化

也就是说，当前平台已经不再只是会执行，
而是开始成长为：
- 会记录
- 会反思
- 会沉淀
- 会组织关系
- 会形成闭环
- 会为下一轮调整预留动作

## 四、当前版本适合做什么
当前版本适合：
1. 继续沿主干稳步推进
2. 继续增强执行层、自愈层、预警层
3. 继续迭代 H5 控制台
4. 为后续垂直 Agent 接入打基础
5. 作为后续分支试验前的稳定回退点

## 五、当前版本还不是什么
当前版本还不是最终完成版。

当前仍然属于：
- 主干逐步增强阶段
- 结构不断固化阶段
- 能力持续接入阶段
- H5 持续迭代阶段

因此本备份的意义不是“封板”，
而是“把当前最关键的一轮阶段成果安全固化”。

## 六、后续主线建议
当前备份完成后，后续建议优先顺序：
1. 继续沿主干推进，不急于频繁大改 H5
2. 新能力进入主干后，再反向补 H5 映射
3. 关键节点继续做灾难性备份六要素
4. 持续坚持“经常回看、关键节点备份、主干优先”的协作纪律

DOC

echo "[4/8] 生成配置与运行环境说明 ..."
{
  echo "# 配置与运行环境说明"
  echo
  echo "## 1. 备份时间"
  date
  echo
  echo "## 2. 当前项目路径"
  echo "${PROJECT_ROOT}"
  echo
  echo "## 3. Python 版本"
  python --version 2>&1 || true
  echo
  echo "## 4. Pip 版本"
  pip --version 2>&1 || true
  echo
  echo "## 5. 当前目录文件"
  ls -la
  echo
  echo "## 6. requirements.txt"
  if [ -f "${PROJECT_ROOT}/requirements.txt" ]; then
    cat "${PROJECT_ROOT}/requirements.txt"
  else
    echo "未发现 requirements.txt"
  fi
  echo
  echo "## 7. pip freeze"
  pip freeze 2>/dev/null || true
} > "${ENV_DIR}/配置与运行环境说明.md"

echo "[5/8] 生成数据与结构快照说明 ..."
{
  echo "# 数据与结构快照"
  echo
  echo "## 1. 当前 PROJECT_CHECKPOINT 末尾快照"
  echo
  if [ -f "${PROJECT_ROOT}/qianqiu_os/PROJECT_CHECKPOINT.md" ]; then
    tail -n 220 "${PROJECT_ROOT}/qianqiu_os/PROJECT_CHECKPOINT.md"
  else
    echo "未发现 qianqiu_os/PROJECT_CHECKPOINT.md"
  fi
  echo
  echo "## 2. memory 宪法文件快照"
  echo
  if [ -f "${PROJECT_ROOT}/memory/constitution_v1_3.txt" ]; then
    tail -n 220 "${PROJECT_ROOT}/memory/constitution_v1_3.txt"
  else
    echo "未发现 memory/constitution_v1_3.txt"
  fi
} > "${SNAPSHOT_DIR}/数据与结构快照说明.md"

echo "[6/8] 生成恢复操作说明 ..."
cat > "${RESTORE_DIR}/恢复操作说明.md" <<DOC
# 恢复操作说明

## 一、适用场景
本备份用于以下场景恢复：
1. 主干文件误删
2. 代码误改导致系统跑不通
3. H5 原型被错误覆盖
4. 分支试验失败后回退到当前稳定节点
5. 关键文档或检查点丢失

## 二、恢复原则
恢复时优先恢复：
1. 完整代码
2. PROJECT_CHECKPOINT.md
3. memory 宪法与备忘
4. H5 当前基线版
5. 本阶段说明书与环境说明

## 三、推荐恢复步骤
### 方法 A：整目录恢复
1. 找到本备份目录中的：
   - 01_完整代码包/project_full_copy/
2. 用其覆盖当前项目目录
3. 再重新创建虚拟环境并安装依赖
4. 执行主程序验证是否恢复成功

### 方法 B：按文件恢复
若只坏了部分文件，可从：
- 01_完整代码包/project_full_copy/
中单独取回目标文件覆盖

## 四、建议恢复后执行的验证命令
\`\`\`bash
python -m qianqiu_os.app
\`\`\`

## 五、恢复成功的判断标准
1. 主程序可正常运行
2. 输出中仍能看到：
   - reflection_log
   - knowledge_graph
   - human_machine_loop_log
3. PROJECT_CHECKPOINT.md 中仍保留本阶段固化内容
4. H5 当前满意版仍可继续作为后续迭代基线

DOC

echo "[7/8] 生成阶段版本标识与验证结论 ..."
cat > "${VERIFY_DIR}/阶段版本标识与验证结论.md" <<DOC
# 阶段版本标识与验证结论

## 一、阶段版本标识
- 备份名称：${PROJECT_NAME}
- 阶段标签：${STAGE_TAG}
- 生成时间：${TIMESTAMP}

## 二、本阶段关键成果标识
当前已固化成果：
1. 反思层第一刀正式接入主链
2. 知识图谱第一刀正式接入主链
3. 人机协同闭环层第一刀正式接入主链
4. H5 控制台第四刀当前满意版固化

## 三、当前验证结论
本阶段判断为：
- 主干结构已明显增强
- 当前节点适合做关键阶段备份
- 当前节点适合继续作为后续开发回退点
- 当前节点不宜丢失

## 四、当前是否建议继续作为主干
建议：是

原因：
1. 当前成果均已进入主链
2. 已完成实际运行验证
3. 已完成 PROJECT_CHECKPOINT.md 固化
4. H5 已形成当前阶段满意版
5. 当前节点具备较高恢复价值

DOC

echo "[8/8] 打包压缩 ..."
(
  cd "${BACKUP_ROOT}"
  zip -rq "${PROJECT_NAME}_${STAGE_TAG}_${TIMESTAMP}.zip" "$(basename "${BACKUP_DIR}")"
)

echo
echo "已生成关键节点灾难恢复备份："
echo "${BACKUP_DIR}"
echo "${BACKUP_ROOT}/${PROJECT_NAME}_${STAGE_TAG}_${TIMESTAMP}.zip"
