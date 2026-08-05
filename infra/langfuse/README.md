# Langfuse 监控

自托管 Langfuse 用于追踪 AI 客服 RAG 链路，评估检索与回答质量。

## 启动

```bash
# 首次：生成 ENCRYPTION_KEY 后填入 docker-compose.yml
openssl rand -hex 32
docker compose -f infra/langfuse/docker-compose.yml up -d
```

面板地址：http://localhost:5000

## 初始化账号

首次启动通过环境变量自动创建组织/项目/API Key：

- 邮箱：admin@localhost
- 密码：admin123
- 公钥：pk-dev-langfuse
- 私钥：sk-dev-langfuse

## 后端接入

在 `backend/.env` 中配置：

```
LANGFUSE_PUBLIC_KEY=pk-dev-langfuse
LANGFUSE_SECRET_KEY=sk-dev-langfuse
LANGFUSE_HOST=http://localhost:5000
```

重启后端后，AI 客服页提问即可在面板 Traces 看到每条对话的 LLM 调用与检索元数据。
