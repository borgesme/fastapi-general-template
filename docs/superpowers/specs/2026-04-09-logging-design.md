# 日志模块设计方案

## 目标

为 FastAPI 项目建立统一、可观测的日志体系：
- **开发环境**：彩色控制台输出，便于调试
- **生产环境**：JSON 格式文件 + 每日轮转 + 14 天保留

## 技术选型

| 职责 | 工具 | 理由 |
|------|------|------|
| 结构化上下文 + 请求绑定 | `structlog` | `contextvars` 注入、processor 链灵活 |
| 文件输出 + 时间轮转 | `loguru` | `rotation="00:00"` 简洁，压缩、保留策略开箱即用 |
| 控制台（开发） | `structlog.dev.ConsoleRenderer` | 彩色高亮，人读友好 |

两者均已安装，无新增依赖。

---

## 模块结构

```
app/
├── core/
│   └── logger.py          # 核心 logger 配置
└── middleware/
    ├── __init__.py
    ├── request_id.py      # request_id 生成 & 上下文绑定
    └── request_logging.py # 请求日志中间件
```

---

## 核心 logger（`app/core/logger.py`）

### 配置逻辑

```python
# 环境判断
if settings.debug:
    # 开发：structlog ConsoleRenderer
else:
    # 生产：loguru 文件输出（JSON + 时间轮转）
```

### structlog processor 链

```python
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,  # 注入上下文变量
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),           # 或 JSONRenderer
    ],
)
```

### loguru 文件 sink（生产）

```python
loguru_logger.add(
    sys.stderr,                        # 开发时同时写控制台
    level=settings.log_level,
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} [{level}] {name}:{function}:{line} {message}",
    colorize=True,
)

# 每日零点轮转，保留 14 天，gzip 压缩
loguru_logger.add(
    f"{settings.log_dir}/{settings.app_name}.log",
    rotation="00:00",
    retention=f"{settings.log_retention_days} days",
    compression="gz",
    level=settings.log_level,
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} [{level}] {message}",
    serialize=True,  # JSON 格式输出
    enqueue=True,    # 多进程安全
)
```

### 统一入口

```python
def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
```

---

## 请求追踪（`app/middleware/request_logging.py`）

### 追踪字段

| 字段 | 说明 |
|------|------|
| `request_id` | UUID v4，随请求生成，写入响应头 `X-Request-ID` |
| `method` | HTTP 方法（GET、POST 等） |
| `path` | 请求路径 |
| `client_ip` | 客户端 IP（支持 `X-Forwarded-For`） |
| `status_code` | 响应状态码 |
| `duration_ms` | 响应耗时（毫秒） |
| `user_id` | 已认证用户的 ID（未认证则为 null） |

### 中间件逻辑

1. 生成 `request_id`（UUID v4），绑定到 `structlog.contextvars`
2. 写入响应头 `X-Request-ID`
3. 请求入口记录 `method path`
4. 请求结束时记录 `status_code duration_ms`
5. 若请求中有已认证用户，注入 `user_id`

### 日志输出示例

**开发控制台：**
```
2026-04-09 14:30:12 [INFO] app.middleware.request_logging: POST /api/v1/auth/login 200 45ms request_id=f1a2b3c4
```

**生产 JSON 文件：**
```json
{"event": "POST /api/v1/auth/login", "request_id": "f1a2b3c4-d4e5-f6a7-b8c9-d0e1f2a3b4c5", "method": "POST", "path": "/api/v1/auth/login", "client_ip": "127.0.0.1", "status_code": 200, "duration_ms": 45, "user_id": null, "level": "info", "timestamp": "2026-04-09T14:30:12.345678+08:00"}
```

---

## 配置项（`app/config.py` 扩展）

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `log_level` | `"INFO"` | 日志级别 |
| `log_dir` | `"logs"` | 日志文件目录 |
| `log_retention_days` | `14` | 保留天数 |

---

## 全局使用方式

```python
from app.core.logger import get_logger

log = get_logger(__name__)
log.info("user_login", user_id=123)
log.warning("rate_limit_exceeded", user_id=456)
log.error("payment_failed", error="timeout", order_id=789)
```

请求上下文内的字段（`request_id`、`user_id` 等）由中间件自动注入，业务代码无需手动传递。

---

## 接入步骤

1. 扩展 `app/config.py` 增加日志配置项
2. 新建 `app/core/logger.py`，实现 `get_logger()` 工厂函数
3. 新建 `app/middleware/request_id.py`，生成并绑定 `request_id`
4. 新建 `app/middleware/request_logging.py`，实现请求日志中间件
5. 修改 `app/main.py`，注册中间件，替换现有 `structlog.configure`
6. 清理现有 `main.py` 中的临时 `structlog.configure` 代码
