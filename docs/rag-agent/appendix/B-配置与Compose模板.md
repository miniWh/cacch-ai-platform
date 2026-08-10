# 附录 B · 配置与 Compose 模板

> **执行状态**：⬜ 未开始 | 🟦 进行中 | ✅ 已完成 | ⏸️ 暂停 | ❌ 阻塞  
> **当前状态**：⬜  
> **适用范围**：共用（配合 01 / 04 / 09）  
> **负责人**：_（选填）_  
> **更新日期**：_（选填）_  
> **阻塞项**：无

### 本章验收
- [ ] 已复制为项目内 `.env.example` / `docker-compose.yml`
- [ ] 本地 Compose 可启动 MySQL、Redis、向量库
- [ ] `.env` 已填真实密钥且未提交 Git

---

## 1. `.env` 示例（勿提交真实密钥）

```bash
APP_ENV=dev
API_AUTH_TOKEN=change-me

# LLM
LLM_PROVIDER=doubao
LLM_API_KEY=sk-xxx
LLM_MODEL=your-chat-model
LLM_BASE_URL=https://ark.cn-beijing.volces.com/api/v3

# Embedding（维度必须与向量库集合一致）
EMBEDDING_API_KEY=sk-xxx
EMBEDDING_MODEL=your-embedding-model
EMBEDDING_DIM=2048

# MySQL（可选备选）
# MYSQL_DSN=mysql+pymysql://user:pass@127.0.0.1:3306/cacch_ai?charset=utf8mb4

# PostgreSQL（当前基础库，对应 JDBC）
# jdbc:postgresql://10.80.86.93:5432/cdb  user=esb  password=esb
DATABASE_URL=postgresql+psycopg://esb:esb@10.80.86.93:5432/cdb

# 向量库（二选一）
VECTOR_BACKEND=milvus   # milvus | pgvector
MILVUS_URI=http://127.0.0.1:19530
# PGVECTOR_DSN=postgresql+psycopg2://user:pass@127.0.0.1:5432/cacch_ai

REDIS_URL=redis://127.0.0.1:6379/0

# RAG 默认参数
CHUNK_SIZE=500
CHUNK_OVERLAP=50
RETRIEVE_TOP_K=4
HISTORY_MAX_TURNS=6
MAX_CONTEXT_TOKENS=6000
```

---

## 2. `docker-compose.yml` 最小骨架

```yaml
services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: cacch_ai
    ports: ["3306:3306"]
    volumes: ["mysql_data:/var/lib/mysql"]

  redis:
    image: redis:7
    ports: ["6379:6379"]

  # 示例：Milvus Standalone（实际以官方 compose 为准，可含 etcd/minio）
  milvus:
    image: milvusdb/milvus:v2.4.0
    command: ["milvus", "run", "standalone"]
    ports: ["19530:19530"]
    volumes: ["milvus_data:/var/lib/milvus"]

volumes:
  mysql_data:
  milvus_data:
```

> 生产环境请改用官方完整 Compose，并配置持久化、网络与资源限制。

---

## 3. 使用勾选

- [ ] `.env.example` 已进仓库
- [ ] `.env` 已进 `.gitignore`
- [ ] `EMBEDDING_DIM` 与建集合参数一致
- [ ] 预发/生产使用独立密钥与库实例
