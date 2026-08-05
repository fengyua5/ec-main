# Langfuse 监控接入实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在项目接入 Langfuse 监控，自动追踪聊天链路中的 LLM 调用并记录 RAG 检索元数据，用于人工评估 RAG 质量。

**Architecture:** `infra/langfuse/docker-compose.yml` 自托管 Langfuse（端口 5000）；后端新增追踪模块（未配置返回 None 优雅降级）；`ChatEngine.process_message` 通过 `trace_context` 把 LLM 调用关联到每次请求的 trace，并在 graph 结束后用 `start_observation(as_type="retriever")` 记录检索观测。

**Tech Stack:** langfuse>=3.0,<4（实际安装 3.15，OTel 架构）、langchain-ollama、langgraph>=0.2、fastapi、pytest。

---

### Task 1: infra/langfuse 部署文件

**Files:**
- Create: `infra/langfuse/docker-compose.yml`
- Create: `infra/langfuse/README.md`

- [x] **Step 1: 创建 docker-compose.yml**

```yaml
services:
  langfuse-db:
    image: postgres:16
    restart: always
    environment:
      POSTGRES_USER: langfuse
      POSTGRES_PASSWORD: langfuse
      POSTGRES_DB: langfuse
    volumes:
      - langfuse-db-data:/var/lib/postgresql/data

  langfuse:
    image: langfuse/langfuse:2
    restart: always
    depends_on:
      - langfuse-db
    ports:
      - "5000:3000"
    environment:
      DATABASE_URL: postgresql://langfuse:langfuse@langfuse-db:5432/langfuse
      NEXTAUTH_URL: http://localhost:5000
      NEXTAUTH_SECRET: dev-nextauth-secret-change-me
      SALT: dev-salt-change-me
      ENCRYPTION_KEY: <openssl-rand-hex-32-bytes>
      LANGFUSE_INIT_ORG_ID: ec-main
      LANGFUSE_INIT_ORG_NAME: ec-main
      LANGFUSE_INIT_PROJECT_ID: ec-main-project
      LANGFUSE_INIT_PROJECT_NAME: ec-main
      LANGFUSE_INIT_PROJECT_PUBLIC_KEY: pk-dev-langfuse
      LANGFUSE_INIT_PROJECT_SECRET_KEY: sk-dev-langfuse
      LANGFUSE_INIT_USER_EMAIL: admin@localhost
      LANGFUSE_INIT_USER_PASSWORD: admin123
      LANGFUSE_INIT_ACTION: create_org_project_api_key

volumes:
  langfuse-db-data:
```

- [x] **Step 2: 创建 README.md**（含启动、初始化账号、后端接入说明）

- [x] **Step 3: 提交** `feat: 新增 Langfuse 自托管部署文件（端口 5000）`

---

### Task 2: 后端配置项

**Files:**
- Modify: `backend/app/core/config.py`
- Modify: `backend/.env.example`
- Test: `backend/tests/test_langfuse_tracing.py`

- [x] **Step 1: 写失败测试**（断言默认值）
- [x] **Step 2: 运行验证失败**（`AttributeError`）
- [x] **Step 3: config.py 追加配置项**

```python
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "http://localhost:5000"
```

- [x] **Step 4: .env.example 追加**（`LANGFUSE_PUBLIC_KEY/SECRET_KEY/HOST`）
- [x] **Step 5: 测试通过**
- [x] **Step 6: 提交** `feat: 新增 Langfuse 配置项（公钥/私钥/HOST）`

---

### Task 3: 追踪模块 tracing.py

**Files:**
- Create: `backend/app/domain/ai/llm/tracing.py`
- Test: `backend/tests/test_langfuse_tracing.py`

> **实施偏差**：langfuse 3.15（及 v4）为 OTel 重构版，`CallbackHandler` 位于 `langfuse.langchain`，无 `get_trace/get_span`，也不支持 `CallbackHandler(langfuse=client)`。改用官方推荐的 `trace_context` 关联机制：显式 `Langfuse` 客户端注册后，`CallbackHandler(public_key=..., trace_context={"trace_id": ...})` 把 LLM run 挂到指定 trace，检索通过 `client.start_observation(as_type="retriever", trace_context=...)` 记录为观测节点。

- [x] **Step 1: 写失败测试**（未配置禁用 / 缺密钥禁用 / 配置后创建 / record_retrieval 关联 trace_id）
- [x] **Step 2: 安装依赖** `.venv/bin/python -m uv pip install 'langfuse>=3.0,<4'`（实际 `uv pip install 'langfuse>=3.0,<4'` → 3.15.0）
- [x] **Step 3: 创建 tracing.py**

```python
import logging

from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: Langfuse | None = None


def is_langfuse_enabled() -> bool:
    return bool(
        settings.langfuse_public_key
        and settings.langfuse_secret_key
        and settings.langfuse_host
    )


def get_langfuse_client() -> Langfuse | None:
    global _client
    if _client is not None:
        return _client
    if not is_langfuse_enabled():
        logger.info("Langfuse 未配置（LANGFUSE_PUBLIC_KEY/SECRET_KEY/HOST），追踪已禁用")
        return None
    _client = Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )
    logger.info("Langfuse 追踪已启用，上报地址: %s", settings.langfuse_host)
    return _client


def create_chat_trace() -> tuple[CallbackHandler | None, str | None]:
    client = get_langfuse_client()
    if client is None:
        return None, None
    trace_id = client.create_trace_id()
    handler = CallbackHandler(
        public_key=settings.langfuse_public_key,
        trace_context={"trace_id": trace_id},
    )
    return handler, trace_id


def record_retrieval(
    trace_id: str,
    *,
    query: str,
    intent: str | None,
    hits: list[dict],
) -> None:
    client = get_langfuse_client()
    if client is None:
        return
    span = client.start_observation(
        name="retrieve_faq",
        as_type="retriever",
        trace_context={"trace_id": trace_id},
        input={"query": query},
        output={"hits": hits, "intent": intent},
        metadata={"hit_count": len(hits)},
    )
    span.end()


def _reset_langfuse() -> None:
    """测试辅助：重置客户端单例缓存。"""
    global _client
    _client = None
```

- [x] **Step 4: 测试通过**（5 个）
- [x] **Step 5: pyproject.toml 追加依赖** `"langfuse>=3.0,<4",`
- [x] **Step 6: 提交** `feat: 新增 Langfuse 追踪模块，未配置时优雅降级`

---

### Task 4: ChatEngine 接线

**Files:**
- Modify: `backend/app/domain/ai/workflow/engine.py`
- Test: `backend/tests/test_langfuse_tracing.py`

- [x] **Step 1: 写失败测试**（handler 传入 graph config、record_retrieval 被调用、未配置时跳过）
- [x] **Step 2: 运行验证失败**
- [x] **Step 3: engine.py 接线**

导入：

```python
from app.domain.ai.llm.tracing import create_chat_trace, record_retrieval
```

`process_message` 中 `result = await self.graph.ainvoke(state)` 替换为：

```python
        handler, trace_id = create_chat_trace()
        kwargs = {"config": {"callbacks": [handler]}} if handler is not None else {}
        result = await self.graph.ainvoke(state, **kwargs)
```

落库逻辑之后追加：

```python
        if trace_id is not None:
            self._record_retrieval(trace_id, result, user_message)
```

新增方法：

```python
    def _record_retrieval(self, trace_id: str, result: dict, query: str) -> None:
        try:
            context = result.get("skills", {}).get("faq", {}).get("context", [])
            hits = [
                {
                    "content": c.get("content", ""),
                    "score": c.get("score", 0.0),
                    "source": c.get("source", ""),
                }
                for c in context
            ]
            record_retrieval(
                trace_id,
                query=query,
                intent=result.get("flow", {}).get("intent"),
                hits=hits,
            )
        except Exception as e:
            logger.warning("Langfuse 记录检索元数据失败: %s", e)
```

- [x] **Step 4: 测试通过**（7 个）
- [x] **Step 5: 提交** `feat: ChatEngine 接入 Langfuse 追踪，记录 RAG 检索观测`

---

### Task 5: 全量回归与收尾

**Files:**
- Test: `backend/tests/`（全量）

- [x] **Step 1: 全量测试**

Run: `.venv/bin/pytest -q`
Expected: **111 passed**（原 104 + 新增 7）且无新增失败

- [x] **Step 2: 提交**（本计划文档同步为最终实现）

---

## 验证（人工）

1. `docker compose -f infra/langfuse/docker-compose.yml up -d`，访问 `http://localhost:5000` 用 admin@localhost/admin123 登录。
2. `backend/.env` 填入公钥 `pk-dev-langfuse` / 私钥 `sk-dev-langfuse`，重启后端。
3. AI 客服页提问，面板 Traces 出现 trace：LLM 观测 + retrieve_faq（retriever 类型）观测（query/intent/hits/hit_count）。
4. 逐条检查召回 chunk 相关性、回答是否基于召回、意图判定是否合理。
