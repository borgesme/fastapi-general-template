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

## Docker 部署（生产环境）

### 前置准备

```bash
# 复制环境变量模板并填入真实密钥
cp .env.production.example .env.production
# 编辑 .env.production，填入 SECRET_KEY 和 POSTGRES_PASSWORD
# 生成密钥: python -c "import secrets; print(secrets.token_hex(32))"
```

### 启动所有服务

```bash
# 构建镜像并启动（app + postgres:16 + redis:7）
docker compose up --build -d

# 查看日志
docker compose logs -f app

# 验证健康检查
curl http://localhost:8000/health
```

### 各服务说明

| 容器 | 端口 | 说明 |
|------|------|------|
| app | 8000 | FastAPI 应用（4 workers） |
| postgres | 5432 | PostgreSQL 16 |
| redis | 6379 | Redis 7 |

### 常用操作

```bash
# 重新构建（代码变更后）
docker compose up --build -d

# 停止所有服务
docker compose down

# 停止并清除数据卷（慎用）
docker compose down -v

# 进入 app 容器
docker compose exec app bash

# 手动执行数据库迁移
docker compose exec app python -m alembic upgrade head
```

## 项目结构

```
app/
├── main.py              # 应用入口
├── config.py            # 配置管理
├── dependencies.py      # 依赖注入
├── api/                 # 路由层
│   ├── root.py          # 健康检查
│   └── v1/              # API v1
│       ├── auth.py      # 认证接口
│       └── users.py     # 用户管理
├── core/                # 核心模块
│   ├── logger.py        # 日志配置（structlog + loguru）
│   ├── security.py      # JWT 安全
│   └── exceptions.py    # 统一异常
├── middleware/          # 中间件
│   ├── request_id.py    # 请求 ID 追踪
│   └── request_logging.py  # 请求日志
├── models/              # 数据库模型
├── schemas/             # Pydantic Schema
├── services/            # 业务逻辑层
├── db/                  # 数据库层
├── cache/               # Redis 缓存
└── utils/               # 工具函数

Docker 相关
├── Dockerfile           # 多阶段构建镜像
├── docker-compose.yml   # 服务编排
└── entrypoint.sh        # 启动脚本（迁移 + 启动）
```
