# 04 · 数据面约定：对象存储、ACL 与混合检索

> **执行状态**：⬜ 未开始 | 🟦 进行中 | ✅ 已完成 | ⏸️ 暂停 | ❌ 阻塞  
> **当前状态**：⬜  
> **适用范围**：平台共用；RAG / 文档智能优先落地  
> **负责人**：_（选填）_  
> **更新日期**：_（选填）_  
> **阻塞项**：无

### 本章验收
- [ ] 文件「真相源」策略已定（本地盘仅开发 / OSS 为生产默认）
- [ ] 文档 ACL 模型（可后期实现）已书面约定，检索过滤预留字段
- [ ] 混合检索作为 RAG 可选增强，开关与降级路径已说明
- [ ] rag-agent / doc-intelligence 已知晓并引用本文

---

## 1. 对象存储（OSS）约定

### 1.1 原则

| 环境 | 建议 |
| :--- | :--- |
| 本地开发 | 本地目录即可 |
| 预发/生产 | **对象存储为文件真相源**（MinIO / 阿里云 OSS / S3 等） |

关系库存：`bucket`、`object_key`、`content_type`、`size`、`checksum`；  
**不要**把大文件永久只放在应用机本地磁盘。

### 1.2 最小对象元数据

| 字段 | 说明 |
| :--- | :--- |
| storage_provider | local / minio / oss / s3 |
| bucket | |
| object_key | 建议含 tenant/app/kb/doc 路径前缀 |
| checksum | sha256，对齐 `content_hash` |
| url_expire_sec | 签名 URL 有效期策略 |

入库 Worker 从 OSS 拉原文再解析；删除文档时同步删对象（或标记 GC）。

---

## 2. 文档 ACL（访问控制）

### 2.1 目标模型（可分期实现）

仅有 `kb_id` 不足以支撑企业「同库不同密级/部门」。目标过滤维度：

```text
检索可见 ⊆ 文档 ACL ∩ 用户身份属性
```

| 维度 | 示例 | MVP | 完整 |
| :--- | :--- | :---: | :---: |
| kb_id | 知识库隔离 | ✅ 强制 | ✅ |
| owner / dept_ids | 部门可见 | 预留字段 | ✅ |
| sensitivity | public / internal / secret | 预留 | ✅ |
| role_allow_list | 角色白名单 | 可选 | ✅ |

### 2.2 数据字段预留（建议写入 document / chunk.meta）

```json
{
  "acl": {
    "visibility": "internal",
    "dept_ids": ["D01", "D02"],
    "role_allow": ["hr", "manager"],
    "user_allow": []
  }
}
```

### 2.3 检索强制规则

1. **MVP**：`filter.kb_id == request.kb_id`（已有）  
2. **完整版**：在向量检索 / 混合检索的 filter 中叠加 ACL；**禁止**先召回再在应用层“碰巧过滤漏了”却已送进 Prompt（至少在送入 LLM 前二次校验）  
3. App 挂载多个 kb 时，取用户有权子集的并集  

实现可后置，但 **表结构与检索接口从一开始预留 `acl` / `filters`**，避免推倒重来。

---

## 3. 混合检索（Hybrid）约定

### 3.1 定位

| 模式 | 说明 | 阶段 |
| :--- | :--- | :---: |
| 纯向量 | MVP 默认 | P1 |
| **混合检索** | 向量 + 关键词/全文（BM25 等）→ 融合 →（可选）Rerank | 完整版可选 |
| 仅关键词 | 降级或运维排障 | 可选 |

### 3.2 融合与降级

- 融合：RRF（ Reciprocal Rank Fusion）或加权分；参数进 App bindings / 配置  
- 任一通路失败：降级为单路，并打点告警，**不导致整次问答 500**  
- Query 改写 / HyDE：标为进阶可选，不阻塞混合检索本身  

### 3.3 与 RAG 域分工

- **平台本文**：开关语义、ACL 同滤、降级与配置键名  
- **rag-agent**：具体索引（PG 全文 / ES / Milvus 标量）与召回实现步骤  

RAG 完整版评测时，对比「纯向量 vs 混合」应写入实验记录（见 06）。

---

## 4. 配置键建议

```bash
STORAGE_PROVIDER=local|minio|oss
STORAGE_BUCKET=cacch-ai
STORAGE_ENDPOINT=...

RAG_HYBRID_ENABLED=false
RAG_HYBRID_ALPHA=0.5          # 或改用 RRF，不必强行 alpha
RAG_ACL_ENFORCE=false         # MVP false；上线企业多部门前改 true
```

---

## 5. 能力域落地勾选

**rag-agent**
- [ ] document 表含存储指针字段  
- [ ] chunk/document 预留 acl  
- [ ] retriever 支持 filters；完整版接 hybrid  

**doc-intelligence**
- [ ] 解析输入统一从 OSS 读取  
- [ ] 输出落库同样受 ACL 约束（谁可看抽取结果）  

---

## 下一步

- Agent 安全硬约束：[05-Agent工具安全与HITL基线.md](./05-Agent工具安全与HITL基线.md)  
- RAG 执行细节：[../rag-agent/README.md](../rag-agent/README.md)  
