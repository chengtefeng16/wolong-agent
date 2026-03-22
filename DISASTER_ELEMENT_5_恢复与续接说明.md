# 灾难备份第五要素：恢复说明与续接说明
> 版本：V1 | 日期：2026-03-22 | 项目：AgentOS / 卧龙Agent

---

## 一、本文档用途

本文档专为**灾难恢复场景**编写。
当发生以下情况时，以本文档为第一恢复入口：

- 本地代码全部丢失
- 开发环境损坏无法启动
- 换新电脑需要重建环境
- 需要将项目交接给他人继续开发

---

## 二、代码仓库位置

| 仓库 | 地址 |
|------|------|
| 主仓库（卧龙Agent + 千秋OS） | https://github.com/chengtefeng16/wolong-agent |
| 备用仓库（AgentOS） | https://github.com/chengtefeng16/Agent-OS |

---

## 三、本地环境恢复步骤

### 第一步：克隆代码

```bash
git clone https://github.com/chengtefeng16/wolong-agent.git
cd wolong-agent
```

### 第二步：重建 Python 虚拟环境

```bash
# 创建新的虚拟环境（命名为 venv_delivery，与历史一致）
python3 -m venv venv_delivery

# 激活虚拟环境
source venv_delivery/bin/activate

# 安装依赖（如有 requirements.txt）
pip install -r requirements.txt
```

> ⚠️ 注意：仓库中已排除 venv/ 目录，需要重新安装依赖。

### 第三步：恢复配置文件

以下配置文件**不在 Git 仓库中**，需要手动恢复（从备份或重新配置）：

| 配置文件 | 说明 | 恢复方式 |
|----------|------|----------|
| `.env` 或环境变量 | API Key、数据库连接等 | 联系原开发者获取 |
| `launchd` 配置 | macOS 定时任务 | 见下方 launchd 恢复说明 |
| 数据库连接配置 | CRM、法规数据库等 | 联系原开发者获取 |

### 第四步：恢复 launchd 定时任务（macOS）

```bash
# 查看现有 launchd 任务
ls ~/Library/LaunchAgents/

# 如有备份的 plist 文件，复制回去
cp backup/*.plist ~/Library/LaunchAgents/

# 加载任务
launchctl load ~/Library/LaunchAgents/你的任务.plist
```

---

## 四、系统启动说明

### 卧龙Agent 启动方式

> ⚠️ 当前阶段卧龙Agent **通过 AgentOS 统一入口被调用**，不支持单独直接启动。
> 正式口径已在《统一 Agent 协议 V1（边界优先版）》中确认。

```bash
# 激活虚拟环境
source venv_delivery/bin/activate

# 进入千秋OS目录
cd qianqiu_os

# 启动主服务（根据实际入口文件调整）
python main.py
```

### 前端 H5 控制台启动方式

```bash
cd wolong_h5_console

# 安装前端依赖
npm install

# 开发模式启动
npm run dev

# 生产构建
npm run build
```

---

## 五、项目核心目录结构说明

```
wolong-agent/
├── qianqiu_os/              # 千秋OS核心（AgentOS主干）
│   ├── services/            # 核心服务层
│   ├── MEMORY_ARCHITECTURE.md  # 记忆架构说明
│   └── ...
├── wolong_h5_console/       # 卧龙H5前端控制台
│   ├── src/
│   │   ├── App.jsx          # 主界面
│   │   └── ...
│   └── vite.config.js
├── 合规核心/                 # 合规相关核心模块
├── 核/                      # 核心业务逻辑
├── backup_20260315_*/       # 各阶段备份快照（重要历史节点）
├── FULL_RESCUE_WOLONG_2026* # 完整救援备份
├── .gitignore               # 排除虚拟环境和大型备份
└── README.md
```

---

## 六、续接开发说明

### 当前阶段定位

截至 2026-03-22，项目处于：

- **AgentOS 主干已建立**，统一协议 V1 已完成文档化
- **卧龙Agent 双轨制运行**（同步主轨 + 异步旁轨）
- **迁移兼容阶段**：旧模块按"先包裹后收口"原则逐步迁移
- **五张关键表已固化**（见第六要素文档）

### 续接时必读的三份文档

1. `DISASTER_ELEMENT_6_规则与宪法.md`（本仓库）
2. 《AgentOS / 卧龙Agent 旧模块映射与兼容迁移清单 V1》
3. 《AgentOS / 卧龙Agent 边界表与五张关键映射表 V1》

### 续接开发禁止事项

- ❌ 禁止新增"野入口"绕过统一接入壳层
- ❌ 禁止直接删除旧模块（兼容包裹优先）
- ❌ 禁止把深法规逻辑堵回同步主轨
- ❌ 禁止 H5 直接读取业务私有字段（必须走适配壳）
- ❌ 禁止新工具调用不经过工具网关

### 续接开发应做事项

- ✅ 新增功能优先走 AgentOS 主干正式入口
- ✅ 新增异步任务优先用 followup_task 标准描述
- ✅ 新增输出优先走标准结果包与统一交付链
- ✅ 每次重大改动前先做备份快照

---

## 七、关键联系与资源

| 资源 | 地址/说明 |
|------|-----------|
| GitHub 主仓库 | https://github.com/chengtefeng16/wolong-agent |
| 原始开发者 | chengtefeng16（GitHub） |
| 备份节点说明 | 见仓库内各 `backup_*` 目录的命名，包含阶段信息 |

---

*本文档为灾难备份六要素第五要素，应与第六要素（规则与宪法）配套使用。*
