# 日志模块实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 FastAPI 项目中建立统一日志体系：开发环境彩色控制台，生产环境 JSON 文件每日轮转保留 14 天。

**Architecture:** structlog 负责结构化 processor 链 + 请求上下文绑定，loguru 负责生产文件 sink + 时间轮转，中间件负责请求级追踪字段注入。

**Tech Stack:** structlog, loguru, FastAPI Middleware, contextvars

---

## 文件结构

| 操作 | 路径 |
|------|------|
| 修改 | `app/config.py` |
| 创建 | `app/core/logger.py` |
| 创建 | `app/middleware/__init__.py` |
| 创建 | `app/middleware/request_id.py` |
| 创建 | `app/middleware/request_logging.py` |
| 修改 | `app/main.py` |

---

## Task 1: 扩展配置项

**文件:** `app/config.py`

- [ ] **Step 1: 添加日志配置字段**

在 `Settings` 类中添加以下字段：

```python
# Logging
log_level: str = "INFO"
log_dir: str = "logs"
log_retention_days: int = 14
```

---

## Task 2: 创建核心 logger

**文件:** `app/core/logger.py`（新建）

- [ ] **Step 1: 编写 `get_logger` 工厂函数**

```python
import sys
import logging
from pathlib import Path

import structlog
from loguru import logger as loguru_logger

from app.config import settings


def setup_logging():
    """配置 structlog + loguru 双引擎。"""
    # 确保日志目录存在
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # 移除 loguru 默认 handler（避免重复输出）
    loguru_logger.remove()

    if settings.debug:
        # ===== 开发：structlog ConsoleRenderer =====
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
                structlog.dev.ConsoleRenderer(),
            ],
        )
        # loguru 仅用于带颜色的控制台（保留 structlog ConsoleRenderer 样式）
        loguru_logger.add(
            sys.stderr,
            level=settings.log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> <level>[{level}]</level> <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> {message}",
            colorize=True,
        )
    else:
        # ===== 生产：loguru JSON 文件 sink =====
        # structlog 输出到 loguru，再由 loguru 序列化写入文件
        class LoguruSink:
            """将 structlog 事件转发给 loguru。"""

            def __init__(self):
                self._logger = loguru_logger.bind()

            def __call__(self, event_dict):
                level = event_dict.pop("level", "info")
                event = event_dict.pop("event", "")
                msg = event
                extra = " ".join(f"{k}={v}" for k, v in event_dict.items())
                self._logger.opt(depth=1).log(level.lower(), f"{msg} {extra}" if extra else msg)

        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, settings.log_level.upper(), logging.INFO)
            ),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(file=LoguruSink()),
            cache_logger_on_first_use=False,
        )
        # loguru 接管文件输出：每日轮转，保留 14 天，gzip 压缩
        loguru_logger.add(
            f"{settings.log_dir}/{settings.app_name}.log",
            rotation="00:00",
            retention=f"{settings.log_retention_days} days",
            compression="gz",
            level=settings.log_level,
            serialize=True,  # JSON 格式
            enqueue=True,    # 多进程安全
        )
        # 结构化 JSON 日志同时写标准错误（供容器 stdout 采集）
        loguru_logger.add(
            sys.stderr,
            level=settings.log_level,
            serialize=True,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} [{level}] {message}",
        )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """获取带有指定名称的结构化 logger。"""
    return structlog.get_logger(name)
```

> **注意**：上述 `LoguruSink` 和 structlog 工厂的写法偏复杂。考虑简化：structlog 和 loguru 各自独立配置，structlog 通过 `add_log_level → TimeStamper → JSONRenderer/ConsoleRenderer` 直接输出，不走 loguru sink。loguru 只负责文件 sink。两种方式二选一。

**简化方案（推荐）**：

```python
# app/core/logger.py
import sys
from pathlib import Path

import structlog
from loguru import logger as loguru_logger

from app.config import settings


def setup_logging():
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    loguru_logger.remove()

    if settings.debug:
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
                structlog.dev.ConsoleRenderer(),
            ],
        )
        loguru_logger.add(
            sys.stderr,
            level=settings.log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> <level>[{level}]</level> {name}:{function}:{line} {message}",
            colorize=True,
        )
    else:
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer(),
            ],
        )
        loguru_logger.add(
            f"{settings.log_dir}/{settings.app_name}.log",
            rotation="00:00",
            retention=f"{settings.log_retention_days} days",
            compression="gz",
            level=settings.log_level,
            serialize=True,
            enqueue=True,
        )


def get_logger(name: str):
    return structlog.get_logger(name)
```

- [ ] **Step 2: 提交**

```bash
git add app/core/logger.py
git commit -m "feat: 添加 structlog + loguru 核心 logger 配置"
```

---

## Task 3: 创建 request_id 中间件

**文件:** `app/middleware/request_id.py`（新建）

- [ ] **Step 1: 编写 request_id 中间件**

```python
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import structlog.contextvars

from app.core.logger import get_logger

log = get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """生成 request_id 并绑定到结构化日志上下文。"""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
```

- [ ] **Step 2: 提交**

```bash
git add app/middleware/request_id.py
git commit -m "feat: 添加 request_id 中间件"
```

---

## Task 4: 创建请求日志中间件

**文件:** `app/middleware/request_logging.py`（新建）

- [ ] **Step 1: 编写请求日志中间件**

```python
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import structlog.contextvars

from app.core.logger import get_logger

log = get_logger(__name__)


def get_client_ip(request: Request) -> str:
    """优先从 X-Forwarded-For 获取真实 IP。"""
    return request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (
        request.client.host if request.client else "unknown"
    )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """记录请求方法、路径、状态码、响应耗时。"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        structlog.contextvars.bind_contextvars(
            method=request.method,
            path=request.url.path,
            client_ip=get_client_ip(request),
        )
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        structlog.contextvars.bind_contextvars(
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        log.info(
            f"{request.method} {request.url.path}",
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        return response
```

> **注意**：`user_id` 注入在 `request_id.py` 的 `dispatch` 中通过读取 `request.state.user`（需依赖 `get_current_user` 的 `User` 对象注入到 `request.state`）实现。简化起见，`user_id` 绑定在 `dependencies.py` 的 `get_current_user` 中完成，不在中间件层处理。

- [ ] **Step 2: 提交**

```bash
git add app/middleware/request_logging.py
git commit -m "feat: 添加请求日志中间件"
```

---

## Task 5: 创建 middleware 统一导出

**文件:** `app/middleware/__init__.py`（新建）

- [ ] **Step 1: 导出中间件**

```python
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware

__all__ = ["RequestIDMiddleware", "RequestLoggingMiddleware"]
```

- [ ] **Step 2: 提交**

```bash
git add app/middleware/__init__.py
git commit -m "feat: 添加 middleware 模块"
```

---

## Task 6: 集成到 main.py

**文件:** `app/main.py`

- [ ] **Step 1: 替换 structlog 配置，添加中间件注册**

```python
# 替换现有的 structlog.configure(...) 块
from app.core.logger import setup_logging, get_logger, logger as root_logger
from app.middleware import RequestIDMiddleware, RequestLoggingMiddleware

setup_logging()
logger = get_logger(__name__)


# 替换 lifespan 中的 logger 引用
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app_starting", app=settings.app_name)
    ...
```

```python
# 在 app = FastAPI(...) 之后添加
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RequestLoggingMiddleware)
```

> 注意：中间件添加顺序是反向生效的。`RequestLoggingMiddleware` 应先添加（外层），`RequestIDMiddleware` 后添加（内层），这样 `request_id` 可在日志中间件中可用。FastAPI 的 `add_middleware` 是栈结构，后添加的在外层。

即：
```python
app.add_middleware(RequestLoggingMiddleware)  # 外层：记录完整请求（含 request_id）
app.add_middleware(RequestIDMiddleware)     # 内层：生成 request_id
```

- [ ] **Step 2: 提交**

```bash
git add app/main.py
git commit -m "feat: 集成日志中间件到 main.py"
```

---

## Task 7: user_id 注入（可选，完善请求追踪）

**文件:** `app/dependencies.py`

- [ ] **Step 1: 在 `get_current_user` 中绑定 user_id 到日志上下文**

```python
import structlog.contextvars

async def get_current_user(...) -> User:
    ...
    structlog.contextvars.bind_contextvars(user_id=user.id)
    return user
```

- [ ] **Step 2: 提交**

```bash
git add app/dependencies.py
git commit -m "feat: 在认证依赖中注入 user_id 到日志上下文"
```

---

## Task 8: .gitignore 更新

**文件:** `.gitignore`

- [ ] **Step 1: 添加日志目录忽略**

```gitignore
# Logs
logs/
*.log
```

- [ ] **Step 2: 提交**

```bash
git add .gitignore
git commit -m "chore: 忽略日志文件目录"
```

---

## Task 9: 验证

- [ ] **Step 1: 启动服务验证控制台日志**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问 `http://localhost:8000/docs`，执行任意 API，检查控制台是否输出格式化的请求日志（含 `request_id`、`method`、`path`、`status_code`、`duration_ms`）。

- [ ] **Step 2: 验证 request_id 响应头**

```bash
curl -I http://localhost:8000/
```

确认响应头包含 `X-Request-ID: <uuid>`。

- [ ] **Step 3: 生产模式验证（可选）**

将 `.env` 中 `DEBUG=false`，检查 `logs/` 目录是否生成 JSON 格式日志文件。

---

## 任务依赖图

```
Task 1 (config)
Task 2 (logger)     → Task 1
Task 3 (request_id) → Task 2
Task 4 (logging)    → Task 2
Task 5 (__init__)   → Task 3, Task 4
Task 6 (main)       → Task 2, Task 5
Task 7 (user_id)    → Task 2
Task 8 (.gitignore)
Task 9 (验证)
```

---

## 验收标准

1. `DEBUG=true` 时控制台输出彩色格式日志
2. `DEBUG=false` 时 `logs/` 目录生成 JSON 格式日志，每日零点轮转，保留 14 天
3. 每条日志包含 `request_id`、`method`、`path`、`status_code`、`duration_ms`
4. 响应头包含 `X-Request-ID`
5. 业务代码中 `get_logger(__name__)` 可直接使用，无需额外配置
