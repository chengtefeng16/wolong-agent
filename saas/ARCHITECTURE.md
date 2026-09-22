# 卧龙 SaaS — 架构决策记录

## 数据库迁移策略

### 当前：SQLAlchemy `create_all`（MVP 阶段）

```python
# saas/backend/database.py — lifespan 启动时执行
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

- 首次部署自动建全部表
- 零运维，适合 MVP 快速迭代
- **限制：** 不能自动处理 ALTER TABLE（加列、改类型、加索引等）

### 后续：迁移到 Alembic（改表结构时必做）

触发时机：任何 `models.py` 里的字段变更（加列、删列、改约束）

步骤：
```bash
cd saas/
pip install alembic
alembic init backend/migrations

# alembic.ini 里配置：
# sqlalchemy.url = %(DATABASE_URL)s

alembic revision --autogenerate -m "describe_change"
alembic upgrade head
```

Railway 部署时在 CMD 前加：
```dockerfile
CMD alembic upgrade head && uvicorn saas.backend.main:app ...
```

---

## 多租户隔离设计

所有业务表（conversations / messages / ai_drafts / waba_accounts / usage_events）
都带 `tenant_id` 字段，**查询必须过滤**。

核心原则：
- JWT payload 里含 `tenant_id`，由 `get_current_user` dep 注入
- 每个 API handler 显式用 `WHERE tenant_id = user.tenant_id`
- PostgreSQL 行级安全（RLS）是 v2 加固项

---

## BSUID vs 电话号码

- `customer_bsuid`（Meta wa_id）是多租户下的唯一客户标识符
- Meta 2026+ 会隐藏真实手机号，phone 仅供展示
- Conversation 的唯一约束：`(waba_id, customer_bsuid)`

---

## Embedded Signup 版本

- **使用 v4**（FB.login with sessionInfoVersion=3）
- v2 已于 2026-10-08 废弃，不要回退
- 需要 Meta App 开启 Embedded Signup 权限 + config_id

---

## 环境变量清单

| 变量 | 说明 | Railway 设置方式 |
|------|------|-----------------|
| `DATABASE_URL` | PostgreSQL 连接串 | `${{Postgres.DATABASE_URL}}` |
| `JWT_SECRET` | JWT 签名密钥（32 字节 hex） | 已用 openssl rand -hex 32 生成 |
| `TOKEN_ENCRYPTION_KEY` | Fernet 加密 WhatsApp token | 已用 openssl rand -hex 32 生成 |
| `META_APP_ID` | Meta App ID | 待填 |
| `META_APP_SECRET` | Meta App Secret | 待填 |
| `META_WEBHOOK_VERIFY_TOKEN` | Webhook 验证令牌 | `wolong_webhook_2026` |
| `GEMINI_API_KEY` | Gemini API 密钥 | 待填 |
