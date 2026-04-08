# FastAPI 微服务模板 — 设计文档

**日期**: 2026-04-08
**状态**: 已批准

---

## 一、技术栈

| 层级 | 技术选型 | 版本 |
|------|----------|------|
| Web 框架 | FastAPI | 0.110+ |
| ORM | SQLAlchemy Core | 2.0+ |
| 数据库迁移 | Alembic | 1.13+ |
| 数据库 | PostgreSQL | 15+ |
| 缓存 / Token 黑名单 | Redis | 7+ |
| 认证 | JWT (PyJWT + python-jose) | — |
| 数据验证 | Pydantic v2 | 2.0+ |
| 配置管理 | Pydantic Settings | 2.0+ |
| 日志 | structlog | 24+ |

---

## 二、项目结构

```
app/
├── __init__.py
├── main.py                  # FastAPI 入口，事件钩子，中间件注册
├── config.py                # Pydantic Settings，从 .env 读取
├── dependencies.py           # 依赖注入：get_db、get_current_user、get_current_active_user
├── api/
│   ├── __init__.py
│   ├── root.py              # GET /health 健康检查
│   └── v1/
│       ├── __init__.py
│       ├── router.py        # v1 路由汇总（include_router）
│       ├── auth.py          # POST /register, /login, /refresh, /logout
│       └── users.py         # GET/PUT /me, PUT /me/password
├── core/
│   ├── __init__.py
│   ├── security.py         # JWT 创建/验证/Redis 黑名单检查
│   └── exceptions.py       # 全局异常类（HTTPException 统一封装）
├── models/
│   ├── __init__.py
│   ├── base.py             # Base, TimestampMixin, SoftDeleteMixin
│   ├── user.py             # User ORM 模型
│   └── order.py            # Order ORM 模型（预留）
├── schemas/
│   ├── __init__.py
│   ├── base.py             # 分页响应基类 PageResponse
│   ├── user.py             # UserCreate, UserUpdate, UserResponse
│   └── order.py            # OrderCreate, OrderUpdate, OrderResponse（预留）
├── services/
│   ├── __init__.py
│   ├── auth_service.py     # 注册/登录/JWT 业务逻辑
│   ├── user_service.py     # 用户查询/更新逻辑
│   └── order_service.py    # 订单业务逻辑（预留）
├── db/
│   ├── __init__.py
│   ├── session.py          # engine, get_db 依赖，session 管理
│   └── init_db.py          # 数据库初始化连接测试
├── cache/
│   ├── __init__.py
│   └── redis_client.py     # Redis 单例连接，TTL 工具
└── utils/
    ├── __init__.py
    └── helpers.py          # 密码哈希工具，通用响应构造

alembic/
├── alembic.ini
├── env.py
└── versions/               # 迁移脚本目录

.env.example                # 环境变量模板
requirements.txt            # 依赖列表
```

---

## 三、API 路由设计

### 3.1 认证（/api/v1/auth）

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /register | 注册用户 | 否 |
| POST | /login | 登录，返回 access_token + refresh_token | 否 |
| POST | /refresh | 用 refresh_token 刷新 access_token | 否 |
| POST | /logout | 将 token 加入 Redis 黑名单 | 是 |

### 3.2 用户（/api/v1/users）

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /me | 获取当前用户信息 | 是 |
| PUT | /me | 更新个人资料（用户名/邮箱） | 是 |
| PUT | /me/password | 修改密码 | 是 |

### 3.3 订单（/api/v1/orders，预留）

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | / | 创建订单 | 是 |
| GET | / | 订单列表（分页 + 状态过滤） | 是 |
| GET | /{id} | 订单详情 | 是 |
| PUT | /{id} | 更新订单 | 是 |
| DELETE | /{id} | 删除订单（软删除） | 是 |

### 3.4 系统

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /health | 健康检查（DB + Redis 连通性） | 否 |

---

## 四、认证机制详解

### 4.1 Token 结构

- **access_token**: 有效期 30 分钟，存储 user_id, role, exp
- **refresh_token**: 有效期 7 天，仅存储 user_id, exp

### 4.2 JWT 黑名单（Redis）

Logout 时将 `jti`（JWT ID）写入 Redis，TTL = token 剩余有效期。  
每次请求在 `security.py` 中检查 jti 是否在黑名单中。

### 4.3 依赖注入

```python
# 获取当前用户（需认证）
async def get_current_user(token: str = Depends(JWTBearer())) -> User:
    # 验证签名 → 检查黑名单 → 查数据库 → 返回 User 模型

# 获取当前活跃用户（封禁用户抛出 403）
async def get_current_active_user(user: User = Depends(get_current_user)) -> User:
```

---

## 五、数据模型

### 5.1 User

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| username | String(50) | 唯一用户名 |
| email | String(255) | 唯一邮箱 |
| hashed_password | String(255) | bcrypt 哈希密码 |
| is_active | Boolean | 默认 True |
| is_superuser | Boolean | 默认 False |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### 5.2 Order（预留）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| user_id | UUID | 外键 → User |
| title | String(200) | 订单标题 |
| amount | Numeric(10,2) | 订单金额 |
| status | Enum | pending/paid/cancelled/completed |
| is_deleted | Boolean | 软删除标记 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

---

## 六、分层架构数据流

```
HTTP Request
    ↓
中间件（异常捕获、日志记录）
    ↓
Depends(get_db) → SQLAlchemy Session
Depends(JWTBearer()) → get_current_user() → Redis 黑名单检查 + DB 查询
    ↓
API Route Handler（接收请求，参数校验）
    ↓
Service Layer（业务逻辑，不直接操作 Session）
    ↓
DB / Redis
    ↓
Pydantic Schema（序列化响应）
    ↓
HTTP Response
```

---

## 七、本阶段实施范围

### 第一阶段（本次）：基础骨架 + 认证 + 用户管理

- [x] 项目结构搭建
- [x] 配置与环境变量
- [x] 数据库连接 + Alembic 初始化
- [x] Redis 连接
- [x] 全局异常处理
- [x] JWT 认证（注册/登录/刷新/登出）
- [x] 用户 CRUD
- [x] 健康检查接口

### 第二阶段（后续）：订单模块

- [ ] Order 模型 + 迁移
- [ ] Order Schema
- [ ] Order Service
- [ ] Order API CRUD
- [ ] 分页支持

---

## 八、关键设计原则

1. **三层架构**：API → Service → DB，逻辑清晰便于新人理解
2. **Schema 与 Model 分离**：Schema 管请求校验，Model 管数据库
3. **依赖注入贯穿全链路**：FastAPI 特色，减少全局状态
4. **统一错误处理**：所有异常经 `exceptions.py` 格式化
5. **Alembic 迁移规范**：每次改表结构必须生成迁移脚本，不得手动修改表
6. **Redis 黑名单**：破解无状态 JWT 无法撤销的问题
