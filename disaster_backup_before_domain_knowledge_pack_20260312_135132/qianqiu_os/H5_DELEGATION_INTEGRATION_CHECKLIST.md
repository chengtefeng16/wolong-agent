<!-- ================================================================
Copyright (c) 2026 程特峰 (Tefeng Cheng)
All Rights Reserved.

Project: AgentOS / Wolong Agent System
This document and its contents are proprietary and confidential.
Unauthorized copying, modification, distribution or use of this
document, in whole or in part, is strictly prohibited.
================================================================ -->

# H5 Delegation 前后端对接清单

## 1. 目标
把当前卧龙主线中已经落地的 delegation 治理配置、保存、预览、回滚能力，整理成一份前后端可直接对接的清单。

---

## 2. 前端需要读取的文件
### 2.1 表单结构
- 文件：`qianqiu_os/config/h5_delegation_form_schema_v1.json`
- 作用：生成 H5 表单字段、分区、控件类型、默认值、绑定路径

### 2.2 默认保守配置
- 文件：`qianqiu_os/config/h5_delegation_default_config_v1.json`
- 作用：H5 页面首次打开时的默认安全态

### 2.3 预设配置
- 文件：`qianqiu_os/config/h5_delegation_presets_v1.json`
- 作用：供 H5 用户快速切换 L3 / L4 等放权样例

### 2.4 保存请求示例
- 文件：`qianqiu_os/config/h5_delegation_save_request_example_v1.json`
- 作用：前端组装 POST 请求时参考的标准 JSON

---

## 3. 后端当前已落地能力
### 3.1 配置合并
- 脚本：`qianqiu_os/config/h5_delegation_config_loader_v1.py`
- 作用：读取 default config + preset 并生成最终 delegation_policy

### 3.2 preset 校验
- 脚本：`qianqiu_os/config/h5_delegation_preset_validator_v1.py`
- 作用：校验 preset 应用后的关键治理字段

### 3.3 保存服务
- 脚本：`qianqiu_os/services/h5_delegation_config_service_v2.py`
- 作用：按 applied_preset 或完整 delegation_policy 保存运行态配置，并生成审计记录与回滚快照

### 3.4 保存后预览
- 脚本：`qianqiu_os/services/h5_delegation_active_config_preview_v1.py`
- 作用：读取当前 active config 并输出当前生效策略摘要

### 3.5 rollback 恢复
- 脚本：`qianqiu_os/services/h5_delegation_config_rollback_v1.py`
- 作用：从 rollback snapshot 恢复 active config，并生成 rollback audit 记录

---

## 4. 前端建议调用链
### 4.1 页面初始化
1. 读 `h5_delegation_form_schema_v1.json`
2. 读 `h5_delegation_default_config_v1.json`
3. 可选读 `h5_delegation_presets_v1.json`

### 4.2 用户切换 preset
1. 选中 preset
2. 前端刷新表单值
3. 可调用 loader / validator 对应接口做预览

### 4.3 用户点击保存
1. 组装请求 JSON
2. 请求目标接口：
   - `POST /api/governance/delegation/save`
3. 请求体参考：
   - `h5_delegation_save_request_example_v1.json`

### 4.4 保存成功后
1. 后端写入：
   - active config
   - audit log
   - rollback snapshot
2. 前端立即调用预览接口或读取 preview 输出
3. 页面展示“当前生效策略摘要”

### 4.5 用户点击回滚
1. 选择 snapshot
2. 调用 rollback 接口
3. 回滚后立即刷新 preview

---

## 5. 运行态文件约定
### 5.1 当前生效配置
- 文件：`qianqiu_os/runtime_governance/delegation_active_config.json`

### 5.2 保存审计日志
- 目录：`qianqiu_os/runtime_governance/audit_logs/`

### 5.3 回滚快照
- 目录：`qianqiu_os/runtime_governance/rollback_snapshots/`

---

## 6. 前端必须展示给用户的关键信息
- delegation_master_switch
- delegation_enabled
- delegation_stage
- permission_level
- allowed_time_windows
- allowed_channels
- allowed_actions
- risk_levels_allowed
- business_stages_allowed
- manual_review_required
- human_supervision_mode
- audit_required
- rollback_enabled
- applied_preset
- saved_at
- operator_name
- change_reason

---

## 7. 当前治理硬规则
1. 默认保守，不能默认大开权限
2. 白名单优先
3. 高风险字段必须保留审计与回滚
4. 人类最终确认权不能被产品化交互弱化
5. H5 不能先发明 execution_manager 未接入的新治理语义
6. 新字段必须先写 checkpoint / 宪法 / 协作OS 再开发

---

## 8. 下一步建议
1. 增加真正的 Web API 路由文件
2. 增加前端“保存后即时预览”接口联动
3. 增加 snapshot 列表接口
4. 增加 rollback 接口
5. 增加保存前字段校验与高风险变更二次确认
