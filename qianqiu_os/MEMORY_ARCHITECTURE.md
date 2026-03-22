<!-- ================================================================
Copyright (c) 2026 程特峰 (Tefeng Cheng)
All Rights Reserved.

Project: AgentOS / Wolong Agent System
This document and its contents are proprietary and confidential.
Unauthorized copying, modification, distribution or use of this
document, in whole or in part, is strictly prohibited.
================================================================ -->

# AgentOS Memory Architecture

## 当前目标
为千秋基座建立清晰的记忆分层，避免任务、经验、用户、知识混在一起。

## 四层记忆

### 1. task_memory
用途：
- 记录任务过程与状态流转
当前载体：
- qianqiu_os/data/tasks.json

### 2. experience_memory
用途：
- 记录人工复核后的经验
当前载体：
- qianqiu_os/data/experience_log.json

### 3. user_memory
用途：
- 记录用户长期偏好、风格、长期目标
当前载体：
- qianqiu_os/data/user_memory.json

### 4. knowledge_memory
用途：
- 记录规则、政策、知识源
当前载体：
- knowledge/

## 当前原则
- 先用本地文件做第一代记忆层
- 后续再逐步升级数据库与向量检索
- 先把分层做清楚，再做复杂化

## 当前映射
- tasks.json = task_memory
- experience_log.json = experience_memory
- user_memory.json = user_memory
- knowledge/ = knowledge_memory
## P2 第三刀：记忆分层（进行中）
当前已明确四层记忆：
- task_memory → qianqiu_os/data/tasks.json
- experience_memory → qianqiu_os/data/experience_log.json
- user_memory → qianqiu_os/data/user_memory.json
- knowledge_memory → knowledge/