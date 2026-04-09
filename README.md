# FastAPI 微服务模板

基于 FastAPI + SQLAlchemy + PostgreSQL + Redis 的单体应用模板。

## 快速开始

### 1. 安装依赖

```bash
python -m venv venv
source venv/bin/activate
# Windows PowerShell:
# venv\Scripts\Activate.ps1
# Windows bash:
# source venv/Scripts/activate
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填写数据库和 Redis 连接信息
# 生成 SECRET_KEY: python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. 数据库迁移

```bash
alembic upgrade head
```

### 4. 启动服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问: http://localhost:8000/docs （Swagger UI）

## API 文档

| 路径 | 说明 |
|------|------|
| GET /health | 健康检查 |
| POST /api/v1/auth/register | 用户注册 |
| POST /api/v1/auth/login | 用户登录 |
| POST /api/v1/auth/refresh | 刷新 Token |
| POST /api/v1/auth/logout | 登出 |
| GET /api/v1/users/me | 获取当前用户 |
| PUT /api/v1/users/me | 更新个人资料 |
| PUT /api/v1/users/me/password | 修改密码 |

## 运行测试

```bash
pip install aiosqlite
pytest -v
```

## 项目结构

```
app/
├── main.py              # 应用入口
├── config.py            # 配置管理
├── dependencies.py       # 依赖注入
├── api/                  # 路由层
│   ├── root.py           # 健康检查
│   └── v1/               # API v1
│       ├── auth.py        # 认证接口
│       └── users.py      # 用户管理
├── core/                 # 核心模块
│   ├── security.py       # JWT 安全
│   └── exceptions.py     # 统一异常
├── models/               # 数据库模型
├── schemas/              # Pydantic Schema
├── services/             # 业务逻辑层
├── db/                   # 数据库层
├── cache/                # Redis 缓存
└── utils/                # 工具函数
```
