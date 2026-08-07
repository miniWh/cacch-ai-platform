# 附录 C · Prompt 与代码示例

> **执行状态**：⬜ 未开始 | 🟦 进行中 | ✅ 已完成 | ⏸️ 暂停 | ❌ 阻塞  
> **当前状态**：⬜  
> **适用范围**：共用（配合 05 / 06）  
> **负责人**：_（选填）_  
> **更新日期**：_（选填）_  
> **阻塞项**：无

### 本章验收
- [ ] Prompt 已落入 `app/core/prompt`
- [ ] 入库 / 对话示意逻辑已对照实现（含答案累积与 citations）
- [ ] 关键兜底表已在 Manager / API 层落地

> 以下为示意代码，非可直接运行的完整工程。

---

## 1. Prompt 模板

```text
系统角色：
你是企业知识库助手。只能依据「检索上下文」回答用户问题。
规则：
1. 若上下文不足以回答，明确说明「根据现有知识库无法确定」，禁止编造。
2. 回答简洁、分点，使用与用户相同的语言。
3. 不要伪造链接、制度文号或数据。
4. 若上下文有多处相关，综合归纳，并在表述上保持审慎。

检索上下文：
{context}

（上下文中每段格式：
[doc_id={doc_id} chunk_id={chunk_id} title={title}]
{content}
）
```

组装：将 hits 格式化为 `context`；历史以 chat messages 追加；最后追加当前 user 问题。无 hits 时可不调用模型，直接返回兜底。

---

## 2. 向量入库流水线（示意）

```python
# app/rag/pipeline/ingest_pipeline.py
from app.rag.loader import FileLoader, WebLoader, DatabaseLoader
from app.rag.splitter import WindowSplitter
from app.core.embedding import EmbeddingClient
from app.dao.vector_db import VectorDB
from app.dao.repositories import DocumentRepository, ChunkRepository


class IngestPipeline:
    def __init__(self):
        self.splitter = WindowSplitter(chunk_size=500, chunk_overlap=50)
        self.embedding = EmbeddingClient()
        self.vector_db = VectorDB()
        self.doc_repo = DocumentRepository()
        self.chunk_repo = ChunkRepository()

    def run(self, kb_id: int, source_type: str, source_data: dict) -> int:
        loader = {
            "file": FileLoader,
            "web": WebLoader,
            "database": DatabaseLoader,
        }.get(source_type)
        if not loader:
            raise ValueError(f"不支持的数据源类型: {source_type}")

        documents = loader().load(source_data)
        doc = self.doc_repo.upsert_pending(kb_id, source_type, documents[0])
        if self.doc_repo.is_unchanged(doc):
            self.doc_repo.mark_ready(doc.id)
            return doc.id

        chunks = self.splitter.split(documents)
        vectors = self.embedding.embed_batch([c.content for c in chunks])

        self.vector_db.delete_by_doc_id(kb_id, doc.id)
        self.chunk_repo.delete_by_doc_id(doc.id)

        new_version = doc.version + 1
        self.vector_db.insert_chunks(kb_id, doc.id, new_version, chunks, vectors)
        self.chunk_repo.batch_save(kb_id, doc.id, new_version, chunks)
        self.doc_repo.mark_ready(doc.id, version=new_version)
        return doc.id
```

---

## 3. 对话编排（示意，含答案累积与引用）

```python
# app/manager/chat_manager.py
from app.rag.retriever import VectorRetriever
from app.core.llm import LLMClient
from app.core.prompt import build_rag_messages
from app.service.chat_service import ChatService


class ChatManager:
    def __init__(self):
        self.retriever = VectorRetriever(top_k=4)
        self.llm = LLMClient()
        self.chat_service = ChatService()

    def chat_stream(self, session_id: str, kb_id: int, query: str):
        session = self.chat_service.ensure_session(session_id, kb_id)
        hits = self.retriever.search(kb_id=kb_id, query=query)
        history = self.chat_service.get_recent_history(session.id, max_turns=6)
        messages = build_rag_messages(hits=hits, history=history, question=query)

        yield {"event": "meta", "data": {"session_id": session.id}}

        answer_parts: list[str] = []
        try:
            if not hits:
                fallback = "知识库中未检索到相关内容，请换个问法或补充文档后再试。"
                answer_parts.append(fallback)
                yield {"event": "token", "data": {"text": fallback}}
            else:
                for token in self.llm.chat_stream(messages):
                    answer_parts.append(token)
                    yield {"event": "token", "data": {"text": token}}
        except Exception:
            err = "模型调用失败，请稍后重试。"
            yield {"event": "error", "data": {"message": err}}
            return

        answer_full = "".join(answer_parts)
        citations = self.chat_service.to_citations(hits)
        self.chat_service.save_turn(session.id, query, answer_full, citations)

        yield {"event": "citations", "data": {"citations": citations}}
        yield {"event": "done", "data": {"finish_reason": "stop"}}
```

---

## 4. 关键场景与兜底

| 场景 | 处理 |
| :--- | :--- |
| 检索无结果 | 固定文案；`citations=[]` |
| 模型超时/5xx | SSE `error`；可重试 1～2 次 |
| 知识库停用/不存在 | HTTP 4xx，明确 message |
| session 与 kb_id 不一致 | 拒绝请求，防串库 |
| 入库文件过大/类型不符 | 创建任务前校验失败 |
| Embedding 限流 | Worker 退避重试 |
| 向量维度不匹配 | 启动时校验，失败则拒绝写入 |

---

## 返回

- [05-分步搭建-数据入库.md](../05-分步搭建-数据入库.md)  
- [06-分步搭建-RAG对话核心.md](../06-分步搭建-RAG对话核心.md)  
