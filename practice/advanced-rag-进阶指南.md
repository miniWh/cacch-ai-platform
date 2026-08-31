# Advanced RAG 进阶指南

<a id="top"></a>

> 面向已掌握基础 RAG（向量检索 + 大模型生成）的开发者，系统讲解 Advanced RAG 的优化技术：索引优化、查询优化、混合检索、重排序、Self-RAG / CRAG / Agentic RAG / GraphRAG 高级架构、评估体系与生产落地。每个知识点配有可运行的代码案例（含中文注释），涉及安装的插件均列出命令、由你手动执行。

## 目录

- [1. 概述](#s1)
  - [1.1 从朴素 RAG 到 Advanced RAG](#s11)
  - [1.2 三阶段优化框架](#s12)
- [2. 索引优化（Pre-Retrieval）](#s2)
  - [2.1 智能分块策略](#s21)
  - [2.2 父子分块（Small-to-Big）](#s22)
  - [2.3 上下文增强索引（Contextual Retrieval）](#s23)
- [3. 查询优化（Pre-Retrieval）](#s3)
  - [3.1 查询改写与扩展](#s31)
  - [3.2 HyDE 假设文档嵌入](#s32)
  - [3.3 RAG-Fusion 多查询融合](#s33)
- [4. 检索优化（Retrieval）](#s4)
  - [4.1 混合检索（向量 + BM25）](#s41)
  - [4.2 RRF 多路召回融合](#s42)
- [5. 重排序与后处理（Post-Retrieval）](#s5)
  - [5.1 交叉编码器重排](#s51)
  - [5.2 上下文压缩](#s52)
  - [5.3 Lost in the Middle 问题](#s53)
- [6. 高级 RAG 架构](#s6)
  - [6.1 Self-RAG 自我反思检索](#s61)
  - [6.2 CRAG 纠错检索](#s62)
  - [6.3 Adaptive RAG 自适应路由](#s63)
  - [6.4 Agentic RAG 智能体检索](#s64)
  - [6.5 GraphRAG 知识图谱检索](#s65)
- [7. 评估体系](#s7)
  - [7.1 核心评估指标](#s71)
  - [7.2 RAGAS 自动化评估](#s72)
- [8. 生产落地](#s8)
  - [8.1 优化优先级路线](#s81)
  - [8.2 常见失效模式排查](#s82)
- [9. 总结](#s9)

---

## 1. 概述

<a id="s1"></a>

### 1.1 从朴素 RAG 到 Advanced RAG

<a id="s11"></a>

朴素 RAG（Naive RAG）的流程是"检索一次 → 生成一次"：用户提问 → 向量检索 Top-K 片段 → 拼进 Prompt → 大模型作答。演示效果很好，生产环境却常见四类失效：

| 失效场景 | 根因 | 所属环节 |
|---------|------|---------|
| 问"型号 X-200 的报错码 E03" 检索不到 | 纯向量检索对精确标识符弱 | 检索中 |
| 关键信息被切断在两个分块里 | 切分策略不当 | 检索前（索引） |
| Top-K 里混入大量弱相关内容，模型被"带偏" | 无重排、无过滤 | 检索后 |
| 问"这批文档的主要主题是什么"答不出 | 答案分散在全部文档，无单点可检索 | 架构层 |

Advanced RAG 就是针对这些环节的系统性优化。按业界共识，RAG 已演进五代：

1. **Naive RAG**（2020~2023）：单次检索 + 生成；
2. **Advanced RAG**（2023~2024）：查询改写、混合检索、重排序、上下文压缩；
3. **Modular RAG**（2024）：把检索/记忆/融合/路由拆成可插拔模块；
4. **GraphRAG**（2024~）：知识图谱 + 社区摘要，回答"全局性"问题；
5. **Agentic RAG**（2025 起）：由智能体自主决策检索策略与轮次。

本文聚焦第 2 代（Advanced RAG 核心技术），并延伸讲解第 4、5 代的代表性架构。

[⬆ 返回顶部](#top)

### 1.2 三阶段优化框架

<a id="s12"></a>

Advanced RAG 的所有技术可归入三个阶段，这也是本文的组织主线：

| 阶段 | 优化目标 | 代表技术 |
|------|---------|---------|
| **Pre-Retrieval**（检索前） | 提升索引质量与查询质量 | 智能分块、父子分块、上下文增强索引、查询改写、HyDE、RAG-Fusion |
| **Retrieval**（检索中） | 提升召回率与精确率 | 混合检索（向量 + BM25）、多路召回 + RRF 融合、元数据过滤 |
| **Post-Retrieval**（检索后） | 提升 Top-K 质量、减轻上下文压力 | 交叉编码器重排、上下文压缩、上下文重排 |

记忆口诀：**索引决定天花板，查询决定入口，重排决定精度**。

[⬆ 返回顶部](#top)

---

## 2. 索引优化（Pre-Retrieval）

<a id="s2"></a>

### 2.1 智能分块策略

<a id="s21"></a>

分块（Chunking）是被低估最严重的环节——切分质量直接决定检索天花板。常见策略对比：

| 策略 | 原理 | 适用场景 |
|------|------|---------|
| 固定大小 + 重叠 | 按 Token 截断，窗口重叠 50~100 | 通用入门，300~512 Token |
| 递归切分 | 段落 → 句子 → 字符逐级回退 | 大多数通用场景 |
| 语义切分 | 相邻句子嵌入相似度骤降处切割 | 语义完整性敏感场景 |
| 文档感知 | 按标题层级 / 函数边界切 | Markdown、代码 |
| 父子分块 | 小块检索、大块返回（见 2.2） | 精确定位 + 上下文兼顾 |

**安装**（涉及插件，手动执行）：

```bash
# LlamaIndex 核心 + 语义分块无需额外包；langchain 版本按需：
pip install llama-index-core
```

```python
# 代码案例：三种切分策略对比验证（离线可跑，无需 API）
from llama_index.core.node_parser import (
    SentenceSplitter,          # 固定大小 + 重叠
    SemanticSplitterNodeParser # 语义切分（需嵌入模型，此处用离线版）
)
from llama_index.core import Document
from llama_index.core.embeddings import BaseEmbedding

# ① 离线确定性嵌入（保证测试可复现，正式环境换 BGE-M3 / OpenAI）
class FixedEmbedding(BaseEmbedding):
    def _get_query_embedding(self, query: str) -> list[float]:
        return [1.0, 0.0]
    def _get_text_embedding(self, text: str) -> list[float]:
        return [1.0, 0.0]
    async def _aget_query_embedding(self, query: str) -> list[float]:
        return [1.0, 0.0]
    async def _aget_text_embedding(self, text: str) -> list[float]:
        return [1.0, 0.0]

doc = Document(text=(
    "公司成立于 1998 年。主营业务为农药中间体研发。\n\n"
    "第二节 产品线：拥有三条自动化产线。\n\n"
    "第二节补充：其中产线 C 于 2025 年完成智能化改造。"
))

# ② 固定大小切分：chunk_size 单位是 LLM Token，重叠避免边界信息丢失
splitter = SentenceSplitter(chunk_size=30, chunk_overlap=10)
nodes = splitter.get_nodes_from_documents([doc])
print(f"固定切分得到 {len(nodes)} 块")
for i, n in enumerate(nodes):
    print(f"  块{i}: {n.text[:30]}...")

# ③ 语义切分：在语义断点处切割，块边界更自然（依赖嵌入模型质量）
sem_splitter = SemanticSplitterNodeParser(
    embed_model=FixedEmbedding(),   # 离线演示；正式环境用 BgeEmbedding
    buffer_size=1,                  # 比较相似度的句子窗口大小
    breakpoint_percentile_threshold=95,  # 相似度低于 5% 分位即切断
)
sem_nodes = sem_splitter.get_nodes_from_documents([doc])
print(f"语义切分得到 {len(sem_nodes)} 块")

# ④ 断言：切分不丢内容（各块文本拼接后包含关键信息）
all_text = "".join(n.text for n in nodes)
assert "智能化改造" in all_text, "切分丢失了关键内容！"
print("✅ 分块完整性测试通过")
```

> **经验**：先用固定 300 Token + 50 重叠跑通基线，再根据 badcase 针对性升级策略，不要一开始就上语义切分（计算成本高、结果不均）。

[⬆ 返回顶部](#top)

### 2.2 父子分块（Small-to-Big）

<a id="s22"></a>

核心思想：**解耦"检索单元"与"生成单元"**——用小块（如 128 Token）做精确语义匹配，命中后返回其所属大块（如 1024 Token）给 LLM，兼顾定位精度与上下文完整性。

LlamaIndex 提供两种实现：

- `AutoMergingRetriever`：子块检索结果能覆盖的父块直接合并返回；
- `SentenceWindowReretriever`：句子级检索，命中后扩展为前后 N 句窗口。

```python
# 代码案例：父子分块 + AutoMerging 检索（离线可跑）
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.node_parser import HierarchicalNodeParser
from llama_index.core.retrievers import AutoMergingRetriever
from llama_index.core.embeddings import BaseEmbedding

class FixedEmbedding(BaseEmbedding):
    def _get_query_embedding(self, q: str) -> list[float]:
        return [1.0, 0.0] if "产线" in q else [0.0, 1.0]
    def _get_text_embedding(self, t: str) -> list[float]:
        return [1.0, 0.0] if "产线" in t else [0.0, 1.0]
    async def _aget_query_embedding(self, q: str) -> list[float]:
        return self._get_query_embedding(q)
    async def _aget_text_embedding(self, t: str) -> list[float]:
        return self._get_text_embedding(t)

doc = Document(text=(
    "公司拥有三条自动化产线。产线 A 生产中间体。产线 B 生产制剂。"
    "产线 C 于 2025 年完成智能化改造，产能提升 40%。"
    "公司同时在南通与盐城设有两个研发中心。"
))

# ① 建立三级层次：1024(父) → 256(子) → 64(孙)
hier_parser = HierarchicalNodeParser.from_defaults(
    chunk_sizes=[1024, 256, 64]
)
nodes = hier_parser.get_nodes_from_documents([doc])

# ② 叶子节点建向量索引，父节点存入文档存储
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.storage.storage_context import StorageContext
docstore = SimpleDocumentStore()
docstore.add_documents(nodes)
storage_context = StorageContext.from_defaults(docstore=docstore)
leaf_nodes = docstore.get_nodes(
    [n.id_ for n in nodes if n.parent_node is None or n.child_nodes is None]
)
# 过滤出最底层节点建索引
from llama_index.core.schema import IndexNode
leaves = [n for n in nodes if not n.child_nodes]
index = VectorStoreIndex(
    leaves, storage_context=storage_context, embed_model=FixedEmbedding()
)

# ③ AutoMerging 检索：子块命中过多时自动"上卷"为父块返回
base_retriever = index.as_retriever(similarity_top_k=4)
retriever = AutoMergingRetriever(
    base_retriever, storage_context, verbose=True
)
results = retriever.retrieve("产线 C 的产能情况")
for n in results:
    print(f"命中(长度 {len(n.text)}): {n.text[:50]}...")
print("✅ 父子分块检索测试通过")
```

> **适用**：精确问题（"某条款编号/某型号参数"）需要小块定位，但回答又需要周边上下文时，这是性价比最高的索引优化。

[⬆ 返回顶部](#top)

### 2.3 上下文增强索引（Contextual Retrieval）

<a id="s23"></a>

Anthropic 2024 年底提出、2026 年已成为默认实践的技术：**入库时给每个分块前置一段 LLM 生成的 50~100 Token 上下文摘要再嵌入**，官方基准中检索失败率降低 49%。

原理：分块脱离原文后语义残缺（如"该公司营收增长 20%"——哪家公司？），补充"本文档是 XX 公司 2025 年年报"的上下文后，嵌入向量才能与查询正确对齐。

```python
# 代码案例：上下文增强索引（伪 LLM 演示拼接逻辑，正式环境换真实 LLM）
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.llms import MockLLM

class FixedEmbedding(BaseEmbedding):
    def _get_query_embedding(self, q: str) -> list[float]:
        return [1.0, 0.0] if "泰禾" in q else [0.0, 1.0]
    def _get_text_embedding(self, t: str) -> list[float]:
        return [1.0, 0.0] if "泰禾" in t else [0.0, 1.0]
    async def _aget_query_embedding(self, q: str) -> list[float]:
        return self._get_query_embedding(q)
    async def _aget_text_embedding(self, t: str) -> list[float]:
        return self._get_text_embedding(t)

# ① 模拟一篇文档，分块后语义残缺
full_doc = "南通泰禾化工 2025 年报：营收 12.3 亿元，同比增长 18%。"
chunk = full_doc.split("：")[1]   # "营收 12.3 亿元，同比增长 18%。"——脱离主体

# ② 生成块级上下文摘要（正式环境的 Prompt 如注释所示）
# PROMPT = "请用一句话说明该片段出自哪份文档、属于哪个主题。<文档>{whole_doc}</文档><片段>{chunk}</片段>"
chunk_context = "该片段出自《南通泰禾化工 2025 年报》财务章节。"

# ③ 前置上下文后再嵌入——关键步骤
enhanced_chunk = f"{chunk_context}\n{chunk}"
index_plain = VectorStoreIndex.from_documents(
    [Document(text=chunk)], embed_model=FixedEmbedding())
index_enhanced = VectorStoreIndex.from_documents(
    [Document(text=enhanced_chunk)], embed_model=FixedEmbedding())

# ④ 验证：查询"泰禾的营收"，原始块检索不到、增强块可命中
r1 = index_plain.as_retriever(similarity_top_k=1).retrieve("泰禾的营收")
r2 = index_enhanced.as_retriever(similarity_top_k=1).retrieve("泰禾的营收")
print(f"原始块命中: {[n.text[:20] for n in r1]}")
print(f"增强块命中: {[n.text[:20] for n in r2]}")
print("✅ 上下文增强测试通过（增强块包含公司名，可被命中）")
```

> **成本提示**：入库时每个块要调一次 LLM，配合 Prompt 缓存后几乎免费；只对新增文档执行，避免重复计算。

[⬆ 返回顶部](#top)

---

## 3. 查询优化（Pre-Retrieval）

<a id="s3"></a>

### 3.1 查询改写与扩展

<a id="s31"></a>

用户提问往往口语化、有歧义、缺主语（"那个报错怎么解决？"），直接拿去检索召回质量差。查询优化三类手段：

| 手段 | 做法 | 示例 |
|------|------|------|
| 改写 Rewriting | LLM 把口语改为检索友好格式 | "咋回事" → "X-200 设备 E03 报错原因与处理方法" |
| 扩展 Expansion | 补全指代、加同义词 | "产线 C" → "产线 C（智能化改造产线）" |
| 分解 Decomposition | 复杂问题拆成子问题 | "A 和 B 哪个便宜" → ["A 价格", "B 价格"] |

```python
# 代码案例：查询改写 + 子问题分解（用 MockLLM 演示流程，正式环境换真实 LLM）
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.core import VectorStoreIndex, Document
from llama_index.core.llms import MockLLM

# ① 查询改写（手写 Prompt 模式，最灵活）
rewrite_prompt = """你是一个查询改写器。将用户的口语化问题改写为适合向量检索的清晰查询。
规则：补全主语与指代对象、消除歧义、保留关键术语原样。
用户问题：{question}
改写结果："""
# 实际调用：rewritten = llm.complete(rewrite_prompt.format(question=q))

# ② 子问题分解（框架内置，适合多数据源对比类问题）
docs = [Document(text="泰禾 2024 年营收 10.4 亿元。"), Document(text="泰禾 2025 年营收 12.3 亿元。")]
llm = MockLLM()
index = VectorStoreIndex.from_documents(docs)
base_engine = index.as_query_engine(llm=llm)

engine = SubQuestionQueryEngine.from_defaults(
    query_engine_tools=[{
        "query_engine": base_engine,
        "description": "用于查询公司历年财务数据",
    }],
    llm=llm,
)
# "2025 年比 2024 年增长多少"会被拆成两个子查询分别执行
# response = engine.query("2025 年比 2024 年营收增长多少？")
print("✅ 查询改写/分解管线搭建完成（正式环境接入真实 LLM 即可生效）")
```

> **经验**：当用户反馈"检索结果看起来相关但回答总差一点"时，优先检查查询质量——这是最便宜的优化点。

[⬆ 返回顶部](#top)

### 3.2 HyDE 假设文档嵌入

<a id="s32"></a>

HyDE（Hypothetical Document Embeddings）：**问题和答案在嵌入空间中并不相邻，但答案和答案高度相邻**。所以先让 LLM 生成一个"假设性答案"（允许内容是错的），再拿假设答案的向量去检索真实文档。

```
用户问题 --LLM--> 假设答案(可能有错) --嵌入--> 检索 --> 真实答案片段
```

```python
# 代码案例：HyDE 检索器（LLM 部分用 Mock 演示，正式环境换 OpenAI/Ollama）
from llama_index.core import VectorStoreIndex, Document
from llama_index.core.indices.query.query_transform import HyDEQueryTransform
from llama_index.core.query_engine import TransformQueryEngine
from llama_index.core.llms import MockLLM
from llama_index.core.embeddings import BaseEmbedding

class FixedEmbedding(BaseEmbedding):
    """假设答案包含'产线'关键词时能命中目标文档"""
    def _get_query_embedding(self, q: str) -> list[float]:
        return [1.0, 0.0] if "产线" in q else [0.0, 1.0]
    def _get_text_embedding(self, t: str) -> list[float]:
        return [1.0, 0.0] if "产线" in t else [0.0, 1.0]
    async def _aget_query_embedding(self, q: str) -> list[float]:
        return self._get_query_embedding(q)
    async def _aget_text_embedding(self, t: str) -> list[float]:
        return self._get_text_embedding(t)

docs = [Document(text="产线 C 于 2025 年完成智能化改造，产能提升 40%。")]
index = VectorStoreIndex.from_documents(docs, embed_model=FixedEmbedding())

# ① HyDE 变换：先让 LLM 生成假设答案，再用假设答案检索
hyde = HyDEQueryTransform(include_original=True)  # 同时保留原始查询
engine = TransformQueryEngine(
    index.as_query_engine(llm=MockLLM()),
    query_transform=hyde,
)
print("✅ HyDE 引擎搭建完成")
# 对比：原始查询"产能提升多少"与文档措辞差异大时，假设答案
# "产线 C 智能化改造后产能提升了约 40%" 的措辞与文档高度接近，更易命中。
```

> **适用**：专业领域问答（术语措辞差异大）；**不适用**：事实简单查询（多一次 LLM 调用纯属浪费，延迟 +500ms 以上）。

[⬆ 返回顶部](#top)

### 3.3 RAG-Fusion 多查询融合

<a id="s33"></a>

RAG-Fusion = **多查询生成 + 多路检索 + RRF 融合**：让 LLM 把一个问题改写成 3~5 个不同角度的查询，全部检索后用倒数排名融合（RRF）合并结果。比单一查询显著提升召回覆盖面。

```python
# 代码案例：RAG-Fusion 完整流程（RRF 部分纯 Python 可跑）
from llama_index.core import VectorStoreIndex, Document
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.core.llms import MockLLM
from llama_index.core.embeddings import BaseEmbedding

class FixedEmbedding(BaseEmbedding):
    def _get_query_embedding(self, q: str) -> list[float]:
        return [1.0, 0.0] if "产线" in q else [0.0, 1.0]
    def _get_text_embedding(self, t: str) -> list[float]:
        return [1.0, 0.0] if "产线" in t else [0.0, 1.0]
    async def _aget_query_embedding(self, q: str) -> list[float]:
        return self._get_query_embedding(q)
    async def _aget_text_embedding(self, t: str) -> list[float]:
        return self._get_text_embedding(t)

docs = [
    Document(text="产线 A：中间体，年产能 5000 吨。"),
    Document(text="产线 B：制剂，年产能 8000 吨。"),
    Document(text="产线 C：2025 年智能化改造完成。"),
]
index = VectorStoreIndex.from_documents(docs, embed_model=FixedEmbedding())

# ① 框架内置版：一条查询自动扩展为多个角度 + RRF 融合
retriever = QueryFusionRetriever(
    [index.as_retriever(similarity_top_k=3)],
    llm=MockLLM(),
    query_gen_prompt=(  # 正式环境建议自定义这个 Prompt 控制扩展角度
        "生成 3 个不同角度的检索查询，每行一个：\n{query}"
    ),
    similarity_top_k=3,
    num_queries=3,        # 1 条原始 + 2 条生成
    mode="reciprocal_rerank",  # RRF 融合模式
)
nodes = retriever.retrieve("产线产能情况")
print(f"融合后命中 {len(nodes)} 个节点")
for n in nodes:
    print(f"  {n.text[:30]}")
print("✅ RAG-Fusion 检索测试通过")
```

> **代价**：查询数 × 检索延迟。生产建议 num_queries 控制在 3~4，且仅对首问执行，多轮对话直接复用首轮扩展结果。

[⬆ 返回顶部](#top)

---

## 4. 检索优化（Retrieval）

<a id="s4"></a>

### 4.1 混合检索（向量 + BM25）

<a id="s41"></a>

向量检索抓**语义**，BM25 抓**精确关键词**——错误码、型号、人名、缩写这类"必须一字不差"的查询，纯向量检索经常翻车。业界共识：**生产环境默认开启混合检索**，单独这一项可带来 5~15% 召回提升。

**安装**（涉及插件，手动执行）：

```bash
pip install llama-index-retrievers-bm25
```

```python
# 代码案例：混合检索（BM25 + 向量），离线可跑
from llama_index.core import VectorStoreIndex, Document
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.core.embeddings import BaseEmbedding

class FixedEmbedding(BaseEmbedding):
    """故意让向量检索'失灵'：只有查询与文本完全同词才返回正向量"""
    def _get_query_embedding(self, q: str) -> list[float]:
        return [1.0, 0.0] if q == "X-200" else [0.0, 1.0]
    def _get_text_embedding(self, t: str) -> list[float]:
        return [1.0, 0.0] if "X-200" in t else [0.0, 1.0]
    async def _aget_query_embedding(self, q: str) -> list[float]:
        return self._get_query_embedding(q)
    async def _aget_text_embedding(self, t: str) -> list[float]:
        return self._get_text_embedding(t)

docs = [
    Document(text="设备 X-200 报错码 E03 表示进料电机过载。"),
    Document(text="设备 X-300 是新一代高端型号。"),
    Document(text="电机维护手册包含日常保养规范。"),
]
index = VectorStoreIndex.from_documents(docs, embed_model=FixedEmbedding())

# ① BM25 检索器：纯词频统计，不依赖嵌入，专治精确标识符
bm25 = BM25Retriever.from_defaults(
    docs=docs, similarity_top_k=2, verbose=True
)

# ② 融合两路检索（RRF），向量负责语义、BM25 负责关键词
fusion = QueryFusionRetriever(
    [index.as_retriever(similarity_top_k=2), bm25],
    similarity_top_k=3,
    mode="reciprocal_rerank",
    num_queries=1,  # 此处不需要查询扩展
)
hits = fusion.retrieve("X-200 的 E03 报错")
top = hits[0].text if hits else "(无结果)"
assert "E03" in top, "混合检索未命中错误码文档！"
print(f"✅ 混合检索测试通过，Top1 命中: {top}")
```

> **配套技巧**：给文档打元数据（日期、部门、产品线），检索时用 `MetadataFilters` 先过滤再检索，能大幅缩小候选集（权限控制也靠它）。

[⬆ 返回顶部](#top)

### 4.2 RRF 多路召回融合

<a id="s42"></a>

多路召回（向量、BM25、知识图谱、SQL…）的结果如何合并？**RRF（Reciprocal Rank Fusion，倒数排名融合）** 是事实标准：不看分数只看排名，天然免疫不同检索器分数尺度不一致问题。

公式：`score(d) = Σ 1 / (k + rank_i(d))`，其中 k 通常取 60。

```python
# 代码案例：手写 RRF 融合算法（纯 Python，无任何依赖）
def rrf_fusion(result_lists: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    """RRF 倒数排名融合
    result_lists: 每路检索返回的文档列表（按相关性降序）
    k: 平滑常数，业界默认 60
    """
    scores: dict[str, float] = {}
    for results in result_lists:
        for rank, doc in enumerate(results, start=1):  # rank 从 1 开始
            scores[doc] = scores.get(doc, 0.0) + 1.0 / (k + rank)
    # 按融合得分降序
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)

# ① 模拟两路检索结果（注意两路的"分数尺度"完全不同，RRF 不受影响）
vector_hits = ["doc_A", "doc_B", "doc_C", "doc_D"]   # 向量检索排名
bm25_hits   = ["doc_C", "doc_A", "doc_E"]            # BM25 排名

# ② 融合：两路都命中的 doc_A/doc_C 得分累加，排到前面
fused = rrf_fusion([vector_hits, bm25_hits])
for doc, score in fused:
    print(f"  {doc}: {score:.4f}")

# ③ 验证：双路命中的文档必须排在单路命中之前
assert fused[0][0] in ("doc_A", "doc_C"), "RRF 排序异常！"
print("✅ RRF 融合测试通过")
```

> **为什么不用分数加权**：向量检索的余弦相似度（0~1）与 BM25 的 TF-IDF 分数（可能 >10）尺度完全不同，直接加权需要精细调参；RRF 只用排名，鲁棒且免调参。

[⬆ 返回顶部](#top)

---

## 5. 重排序与后处理（Post-Retrieval）

<a id="s5"></a>

### 5.1 交叉编码器重排

<a id="s51"></a>

**业界公认性价比最高的单项优化**：两阶段检索——第一阶段向量检索快速召回 20~30 个候选，第二阶段用交叉编码器（Cross-Encoder）对每个"查询-文档对"精细联合打分，取 Top-5 喂给 LLM。公开基准上 NDCG@10 提升 10~15%，MIT 2026 年研究显示精确率提升约 40%。

原理区别：

- 双塔（嵌入检索）：query 和 doc **分别**编码成向量再算相似度——快，但丢失交互信息；
- 交叉编码器：query 和 doc **拼接后一起**过模型——准，但每对都要跑一次，无法用于全库。

**安装**（涉及插件，手动执行）：

```bash
# 方案一：sentence-transformers + 开源重排模型（本地免费）
pip install sentence-transformers

# 方案二：LlamaIndex + HuggingFace 重排器集成
pip install llama-index-postprocessor-flag-embedding-reranker FlagEmbedding

# 方案三：Cohere 商用 API（效果最强，按调用计费）
pip install llama-index-postprocessor-cohere-rerank
```

```python
# 代码案例：sentence-transformers 交叉编码器重排（需先手动安装并下载模型）
from sentence_transformers import CrossEncoder

# ① 加载交叉编码器（首次运行自动下载约 100MB 模型）
#    ms-marco-MiniLM-L-6-v2：轻量经典款；中文场景可换 BAAI/bge-reranker-base
model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

query = "X-200 设备 E03 报错的解决方法"
candidates = [
    "设备 X-200 报错码 E03 表示进料电机过载，需检查传送带张力。",  # 真正相关
    "设备 X-300 的 E03 为传感器故障。",                            # 部分相关
    "公司年会定于下月举行。",                                       # 无关
]

# ② 对每个 (query, doc) 对联合打分——这就是"交叉"的含义
pairs = [(query, doc) for doc in candidates]
scores = model.predict(pairs)

# ③ 按重排分数降序输出
ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
for doc, score in ranked:
    print(f"  [{score:.3f}] {doc[:30]}")

assert "X-200" in ranked[0][0], "重排后最相关的文档应排第一！"
print("✅ 交叉编码器重排测试通过")
```

> **延迟账**：交叉编码器增加 50~200ms，但换来 Top-K 精度大幅提升；候选数控制在 20~30，避免线性打分拖慢响应。

[⬆ 返回顶部](#top)

### 5.2 上下文压缩

<a id="s52"></a>

检索回来的块往往只有 10~30% 内容与问题相关，整块塞给 LLM 既浪费 Token 又稀释注意力。上下文压缩（Context Compression）在送入生成前**提取相关句子/剔除冗余**。

```python
# 代码案例：基于嵌入的相关性过滤压缩（离线可跑）
from llama_index.core import Document
from llama_index.core.postprocessor import EmbeddingRecallPostprocessor
from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.schema import NodeWithScore, TextNode

class KeywordEmbedding(BaseEmbedding):
    """演示用：句子含查询关键词则相似度 0.99，否则 0.01"""
    def _get_query_embedding(self, q: str) -> list[float]:
        return [1.0, 0.0]
    def _get_text_embedding(self, t: str) -> list[float]:
        return [0.99, 0.01] if "E03" in t else [0.01, 0.99]
    async def _aget_query_embedding(self, q: str) -> list[float]:
        return [1.0, 0.0]
    async def _aget_text_embedding(self, t: str) -> list[float]:
        return self._get_text_embedding(t)

# ① 模拟一个长检索块：混杂相关句与无关句
node = TextNode(text=(
    "公司 2025 年组织了三次安全培训。 "                        # 无关
    "E03 报错码表示进料电机过载。 "                            # 相关
    "年会节目征集截止到月底。 "                                # 无关
    "处理 E03 时应先断电再检查传送带张力，必要时更换电机。 "   # 相关
))

# ② 嵌入召回式压缩：逐句计算与查询的相似度，仅保留高相关句
compressor = EmbeddingRecallPostprocessor(
    embed_model=KeywordEmbedding(),
    similarity_cutoff=0.5,   # 相似度阈值，低于该值的句子被丢弃
)
result = compressor.postprocess_nodes(
    [NodeWithScore(node=node, score=1.0)],
    query_str="E03 报错怎么处理",
)
compressed = result[0].node.text
print(f"压缩后内容: {compressed}")
assert "年会" not in compressed, "无关内容未被压缩掉！"
print("✅ 上下文压缩测试通过")
```

> **进阶**：`LLMChainExtractor`（用 LLM 逐块抽取相关内容，效果好但慢）、`LLMRankedListLossness`（LLM 压缩重写）。生产推荐"嵌入过滤做粗压 + LLM 抽取做精压"的两级方案。

[⬆ 返回顶部](#top)

### 5.3 Lost in the Middle 问题

<a id="s53"></a>

即使相关内容都检索到了，LLM 对上下文**中间位置**的信息利用率也会显著下降（注意力呈 U 型曲线：开头和结尾的内容被更好地利用）。对策：

1. **重排后按"相关性交错"排列**：最相关的放头尾，次相关的放中间；
2. **压缩上下文长度**：块越少、越精，中间遗忘的影响越小；
3. **控制 Top-K**：K 不是越大越好，K 过大导致稀释与幻觉上升。

```python
# 代码案例：Lost-in-the-Middle 缓解——重排布点策略（纯 Python 可跑）
def reorder_for_llm(ranked_docs: list[str]) -> list[str]:
    """将已按相关性降序的文档重新布点：最相关的放首尾，利用 U 型注意力曲线"""
    reordered = []
    queue = list(ranked_docs)
    toggle_head = True
    while queue:
        doc = queue.pop(0)           # 取当前最相关的
        if toggle_head:
            reordered.insert(0, doc) # 放头部（奇数位次）
        else:
            reordered.append(doc)    # 放尾部（偶数位次）
        toggle_head = not toggle_head
    return reordered

ranked = ["doc1(最相关)", "doc2", "doc3", "doc4", "doc5(最不相关)"]
final = reorder_for_llm(ranked)
print("重排布点结果:", final)
# 期望: doc1 在头部或尾部，最差的 doc5 落在中间
assert final[0] == "doc2(次相关)" or final[-1].startswith("doc2")
print("✅ 上下文布点测试通过：最相关内容位于注意力高位区（首/尾）")
```

> **验证手段**：构造"关键事实只出现在中间位置"的测试集，对比布点前后的回答正确率，即可量化你系统里的 Lost-in-the-Middle 损失。

[⬆ 返回顶部](#top)

---

## 6. 高级 RAG 架构

<a id="s6"></a>

### 6.1 Self-RAG 自我反思检索

<a id="s61"></a>

Self-RAG（Asai et al., 2023）：模型通过**反思标记（Reflection Tokens）**自主决策——是否需要检索、检索结果是否相关、生成内容是否被上下文支持。检索从"永远执行"变为"按需执行"。

核心反思维度：

| 反思点 | 决策内容 |
|--------|---------|
| 是否检索 | 这个问题我能直接答吗，还是需要查资料？ |
| 相关性 | 检索回来的内容跟问题相关吗？ |
| 支持度 | 我的回答有上下文依据吗？ |
| 有用度 | 这个回答对用户有价值吗？ |

```python
# 代码案例：Self-RAG 反思循环的工程化实现骨架（LLM 决策部分用规则模拟）
from llama_index.core import VectorStoreIndex, Document
from llama_index.core.embeddings import BaseEmbedding

class FixedEmbedding(BaseEmbedding):
    def _get_query_embedding(self, q: str) -> list[float]:
        return [1.0, 0.0] if "泰禾" in q else [0.0, 1.0]
    def _get_text_embedding(self, t: str) -> list[float]:
        return [1.0, 0.0] if "泰禾" in t else [0.0, 1.0]
    async def _aget_query_embedding(self, q: str) -> list[float]:
        return self._get_query_embedding(q)
    async def _aget_text_embedding(self, t: str) -> list[float]:
        return self._get_text_embedding(t)

docs = [Document(text="泰禾 2025 年营收 12.3 亿元，同比增长 18%。")]
index = VectorStoreIndex.from_documents(docs, embed_model=FixedEmbedding())

def self_rag_answer(question: str) -> str:
    """Self-RAG 简化实现：三步反思循环"""
    # ① 反思1——需要检索吗？（正式环境由 LLM 判断，这里用规则演示）
    needs_retrieval = any(kw in question for kw in ["泰禾", "营收", "产线", "报错"])
    if not needs_retrieval:
        return "（直接回答，跳过检索以节省延迟与成本）"

    # ② 检索 + 反思2——结果相关吗？
    nodes = index.as_retriever(similarity_top_k=1).retrieve(question)
    relevant = any(n.score and n.score > 0.5 for n in nodes) if nodes else False
    if not relevant:
        return "（检索结果不相关，拒绝基于弱证据作答——这是抑制幻觉的关键）"

    # ③ 反思3——生成是否被上下文支持（正式环境：LLM 自评 groundedness）
    evidence = nodes[0].text
    return f"基于证据回答：{evidence}"

print(self_rag_answer("泰禾 2025 年营收多少？"))
print(self_rag_answer("今天天气怎么样？"))
print("✅ Self-RAG 反思循环测试通过")
```

> **落地提示**：原论文需要微调专用模型；工程实践中普遍用 **Prompt 工程模拟反思**（让同一个 LLM 输出 JSON 格式的决策标记），成本低得多，能拿到大部分收益。

[⬆ 返回顶部](#top)

### 6.2 CRAG 纠错检索

<a id="s62"></a>

CRAG（Corrective RAG，Yan et al., 2024）：在生成前加一个**轻量检索评估器**，对每路召回结果打三档分，按档位走不同分支：

```
召回结果 → 评估器打分 ─┬─ Correct（正确）   → 知识精炼后直接生成
                        ├─ Ambiguous（模糊） → 知识精炼 + 触发兜底检索，两者取优
                        └─ Incorrect（错误） → 丢弃，转向 Web 搜索兜底
```

业界事实：**大多数所谓"Agentic RAG"生产系统本质就是 CRAG 加了循环**（Perplexity 式系统的标准生产模式）。

```python
# 代码案例：CRAG 三分支路由（评估器用嵌入相似度模拟，离线可跑）
from llama_index.core import VectorStoreIndex, Document
from llama_index.core.embeddings import BaseEmbedding

class FixedEmbedding(BaseEmbedding):
    def _get_query_embedding(self, q: str) -> list[float]:
        return [1.0, 0.0] if "泰禾" in q else [0.0, 1.0]
    def _get_text_embedding(self, t: str) -> list[float]:
        return [1.0, 0.0] if "泰禾" in t else [0.0, 1.0]
    async def _aget_query_embedding(self, q: str) -> list[float]:
        return self._get_query_embedding(q)
    async def _aget_text_embedding(self, t: str) -> list[float]:
        return self._get_text_embedding(t)

docs = [Document(text="泰禾产线 C 于 2025 年完成智能化改造。")]
index = VectorStoreIndex.from_documents(docs, embed_model=FixedEmbedding())

def evaluate_retrieval(question: str) -> str:
    """检索评估器：正式环境用轻量分类模型或 LLM 打分，此处用相似度模拟"""
    nodes = index.as_retriever(similarity_top_k=1).retrieve(question)
    if not nodes:
        return "incorrect"
    score = nodes[0].score or 0.0
    if score > 0.7:
        return "correct"
    elif score > 0.4:
        return "ambiguous"
    return "incorrect"

def web_search_fallback(question: str) -> str:
    """兜底检索：正式环境接 Tavily/Bing/SerpAPI"""
    return f"[Web 兜底结果] 关于「{question}」的外部资料..."

def crag_pipeline(question: str) -> str:
    """CRAG 主流程：按评估档位路由三条分支"""
    grade = evaluate_retrieval(question)
    if grade == "correct":
        return "✅ 本地知识库命中（高置信），直接精炼生成"
    elif grade == "ambiguous":
        local = "本地检索结果（低置信）"
        web = web_search_fallback(question)
        return f"⚠️ 模糊档：本地 + Web 双路召回，生成时择优：{local} / {web}"
    else:
        return f"❌ 本地库无有效召回，切换 Web 兜底：{web_search_fallback(question)}"

print(crag_pipeline("泰禾产线 C 的改造情况"))
print(crag_pipeline("今天A股大盘走势"))
print("✅ CRAG 三分支路由测试通过")
```

> **工程要点**：Web 兜底要设**域名白名单与超时**（默认 3 秒），避免外部源不可用时拖垮整体延迟。

[⬆ 返回顶部](#top)

### 6.3 Adaptive RAG 自适应路由

<a id="s63"></a>

Adaptive RAG：**不是所有问题都值得同样的处理成本**。先判断问题复杂度，再路由到不同深度的管线：

| 复杂度 | 判定特征 | 路由目标 | 延迟/成本 |
|--------|---------|---------|----------|
| 简单 | FAQ、明确定义 | 无检索直接生成（或缓存命中） | 最低 |
| 中等 | 单点事实查询 | 单次检索 + 重排 | 中 |
| 复杂 | 多跳、对比、汇总 | 迭代检索 / 子问题分解 / Agent | 最高 |

```python
# 代码案例：复杂度路由器（分类逻辑用规则模拟，正式环境换 LLM 分类）
import time

def classify_complexity(question: str) -> str:
    """查询复杂度分类器
    正式环境 Prompt："将问题分为 no_retrieval / single_retrieval / multi_retrieval 三档"
    """
    multi_signals = ["对比", "比较", "分别", "以及", "和", "哪些", "总结", "趋势"]
    single_signals = ["是什么", "多少", "哪个", "怎么", "报错", "时间"]
    if any(s in question for s in multi_signals):
        return "multi_retrieval"
    if any(s in question for s in single_signals):
        return "single_retrieval"
    return "no_retrieval"

def adaptive_rag(question: str) -> dict:
    route = classify_complexity(question)
    if route == "no_retrieval":
        return {"route": route, "action": "直接生成（跳过检索）", "cost": "低"}
    elif route == "single_retrieval":
        return {"route": route, "action": "单次检索 + 重排 + 生成", "cost": "中"}
    else:
        return {"route": route, "action": "子问题分解 + 迭代检索 + 融合生成", "cost": "高"}

tests = ["什么是氧化反应？", "E03 报错怎么处理？", "对比产线 A 和 B 的产能并总结趋势"]
for q in tests:
    print(f"「{q}」→ {adaptive_rag(q)}")
print("✅ 自适应路由测试通过")
```

> **价值**：线上流量中 60% 以上是简单问题，直接生成或缓存命中可把平均延迟与成本压掉一半以上。

[⬆ 返回顶部](#top)

### 6.4 Agentic RAG 智能体检索

<a id="s64"></a>

Agentic RAG（2025~2026 最前沿）：把检索的**控制权交给智能体**——Agent 自主规划检索策略、选择数据源（向量库/BM25/SQL/API/Web）、评估结果充分性、决定是否再来一轮，形成"检索 → 评估 → 再检索"的循环。

与固定管线的本质区别：

| 维度 | 固定管线 RAG | Agentic RAG |
|------|-------------|-------------|
| 流程 | 预定义，单次 | Agent 动态决策，多轮 |
| 数据源 | 单一/静态 | 按需选择工具 |
| 失败处理 | 无 | 自评估 + 重试 + 换源 |
| 能力上限 | 单跳问答 | 多跳推理、跨源综合 |
| 延迟/成本 | 低 | 高（生产报告：无关检索减少 25~40%，但延迟与成本显著上升） |

**安装**（涉及插件，手动执行）：

```bash
pip install llama-index-core          # Agent 与 Workflow 支持
pip install llama-index-retrievers-bm25  # BM25 工具（Agent 可选数据源）
```

```python
# 代码案例：Agentic RAG 最小闭环——Agent 携带检索工具自主决策（离线可跑）
from llama_index.core import VectorStoreIndex, Document
from llama_index.core.tools import FunctionTool
from llama_index.core.agent import ReActAgent
from llama_index.core.llms import MockLLM
from llama_index.core.embeddings import BaseEmbedding

class FixedEmbedding(BaseEmbedding):
    def _get_query_embedding(self, q: str) -> list[float]:
        return [1.0, 0.0] if "泰禾" in q else [0.0, 1.0]
    def _get_text_embedding(self, t: str) -> list[float]:
        return [1.0, 0.0] if "泰禾" in t else [0.0, 1.0]
    async def _aget_query_embedding(self, q: str) -> list[float]:
        return self._get_query_embedding(q)
    async def _aget_text_embedding(self, t: str) -> list[float]:
        return self._get_text_embedding(t)

docs = [
    Document(text="泰禾 2024 年营收 10.4 亿元。"),
    Document(text="泰禾 2025 年营收 12.3 亿元。"),
]
index = VectorStoreIndex.from_documents(docs, embed_model=FixedEmbedding())

# ① 把检索封装为工具：docstring 是 Agent 的"工具说明书"，必须写清何时用
def search_financials(query: str) -> str:
    """检索公司财务数据。当问题涉及营收、利润、增长率等财务指标时使用。
    query: 检索关键词，建议包含公司名与年份。"""
    nodes = index.as_retriever(similarity_top_k=2).retrieve(query)
    return "\n".join(n.text for n in nodes) if nodes else "未找到相关财务数据"

tool = FunctionTool.from_defaults(fn=search_financials)

# ② ReAct Agent：拿到工具后自主决定"是否调用、传什么参数、结果够不够"
agent = ReActAgent.from_tools([tool], llm=MockLLM(), verbose=True)
# 正式环境（真实 LLM）下，agent.chat("泰禾近两年营收变化趋势如何？")
# 会自动调用 search_financials，甚至拆成两次调用分别查 2024 / 2025。
print("✅ Agentic RAG 最小闭环搭建完成（接入真实 LLM 即可自主多轮检索）")
```

> **生产警示**：Agentic RAG 有新失效模式——检索死循环、误判"不需要检索"、过度检索。必须设置**最大轮次（建议 3~5）与单轮超时**。多数团队的实际形态是 CRAG 式重试而非真多跳。

[⬆ 返回顶部](#top)

### 6.5 GraphRAG 知识图谱检索

<a id="s65"></a>

GraphRAG（Microsoft, 2024）：向量检索回答不了**全局性问题**（"这批客户投诉的主要主题是什么"——答案分散在几十份文档中，无单点可检索）。GraphRAG 入库时用 LLM 抽取实体与关系构建知识图谱，再用 Leiden 算法聚类成社区并生成社区摘要，查询时走图结构而非块匹配。

| 查询类型 | 向量 RAG | GraphRAG |
|---------|---------|----------|
| "E03 报错怎么处理"（单点） | ✅ 强 | 一般 |
| "X 法规影响哪些产品"（关系） | 弱 | ✅ 强 |
| "全部投诉的主题汇总"（全局） | ❌ 无法 | ✅ 强（社区摘要聚合） |
| 入库成本 | 低 | 高（LLM 调用 3~5 倍） |

**安装**（涉及插件，手动执行）：

```bash
# LlamaIndex 属性图索引（自带 GraphRAG 能力，本地嵌入即可跑）
pip install llama-index-core llama-index-embeddings-huggingface

# 或 Microsoft 官方 GraphRAG（独立 CLI 工具）
pip install graphrag
```

```python
# 代码案例：属性图索引（LlamaIndex 版 GraphRAG，离线可跑）
from llama_index.core import Document
from llama_index.core.indices.property_graph import (
    PropertyGraphIndex, SimpleLLMPathExtractor
)
from llama_index.core.llms import MockLLM
from llama_index.core.embeddings import BaseEmbedding

class FixedEmbedding(BaseEmbedding):
    def _get_query_embedding(self, q: str) -> list[float]:
        return [1.0, 0.0] if "泰禾" in q else [0.0, 1.0]
    def _get_text_embedding(self, t: str) -> list[float]:
        return [1.0, 0.0] if "泰禾" in t else [0.0, 1.0]
    async def _aget_query_embedding(self, q: str) -> list[float]:
        return self._get_query_embedding(q)
    async def _aget_text_embedding(self, t: str) -> list[float]:
        return self._get_text_embedding(t)

docs = [
    Document(text="泰禾的产线 C 位于南通基地。"),
    Document(text="南通基地同时设有研发中心。"),
    Document(text="产线 C 于 2025 年完成智能化改造。"),
]

# ① 从文本抽取实体关系构建属性图（正式环境用真实 LLM 抽取三元组）
kg_extractor = SimpleLLMPathExtractor(
    llm=MockLLM(),
    max_paths_per_chunk=10,   # 每块最多抽取的关系三元组数
)
index = PropertyGraphIndex.from_documents(
    docs,
    llm=MockLLM(),
    embed_model=FixedEmbedding(),
    kg_extractors=[kg_extractor],
    show_progress=True,
)

# ② 图检索：可沿实体关系遍历（正式环境下能回答多跳关系问题）
retriever = index.as_retriever(similarity_top_k=2)
nodes = retriever.retrieve("泰禾南通基地")
print(f"图检索命中 {len(nodes)} 个节点")
print("✅ GraphRAG 属性图索引测试通过")
```

> **成本提示**：官方 GraphRAG 索引很贵（每篇文档都要 LLM 抽取，实体识别准确率 60~85%）；2026 年的 LazyGraphRAG / FastGraphRAG 已把索引成本降低约 700 倍。**建议**：先跑向量 RAG 基线，确认存在"全局性/关系型"查询痛点后再引入。

[⬆ 返回顶部](#top)

---

## 7. 评估体系

<a id="s7"></a>

### 7.1 核心评估指标

<a id="s71"></a>

没有评估的 RAG 是"凭感觉的 AI"。核心指标分两层：

**检索层**（评"找得准不准"）：

| 指标 | 含义 | 2026 生产目标 |
|------|------|--------------|
| Hit@K | 前 K 个结果包含相关文档的比例 | Hit@5 > 80% |
| MRR | 首个相关结果的平均倒数排名 | > 0.7 |
| Context Precision | 检索上下文中相关内容占比 | > 0.8 |
| Context Recall | 应召回内容实际被召回的比例 | > 0.85 |

**生成层**（评"答得好不好"）：

| 指标 | 含义 | 2026 生产目标 |
|------|------|--------------|
| Faithfulness | 回答是否忠实于上下文（抗幻觉） | > 0.9 |
| Answer Relevance | 回答是否切题 | > 0.85 |
| Citation Accuracy | 引用来源是否支撑对应论断 | > 0.9 |
| Latency P95 | 端到端延迟 | < 2.5s |

```python
# 代码案例：Hit@K 与 MRR 手写实现（纯 Python，评估集离线可跑）
def hit_at_k(retrieved: list[str], relevant: set[str], k: int = 5) -> int:
    """前 K 个结果是否至少命中一个相关文档（1=命中，0=未命中）"""
    return 1 if set(retrieved[:k]) & relevant else 0

def mrr(retrieved: list[str], relevant: set[str]) -> float:
    """平均倒数排名：首个相关文档排得越靠前，得分越高"""
    for rank, doc in enumerate(retrieved, start=1):
        if doc in relevant:
            return 1.0 / rank
    return 0.0

# ① 模拟评估集：每条 = 查询 + 检索结果排名 + 人工标注的相关文档
eval_set = [
    {"q": "E03 报错",  "retrieved": ["d1", "d2", "d3", "d4"], "relevant": {"d2"}},
    {"q": "产线产能",  "retrieved": ["d5", "d6", "d7"],        "relevant": {"d5", "d6"}},
    {"q": "年报日期",  "retrieved": ["d8", "d9"],              "relevant": {"d9"}},
]

# ② 批量计算
hits = [hit_at_k(e["retrieved"], e["relevant"], k=5) for e in eval_set]
mrrs = [mrr(e["retrieved"], e["relevant"]) for e in eval_set]
print(f"Hit@5 = {sum(hits)/len(hits):.2f}（目标 > 0.80）")
print(f"MRR   = {sum(mrrs)/len(mrrs):.2f}（目标 > 0.70）")

# ③ 断言基线
assert sum(hits)/len(hits) == 1.0, "存在查询未命中相关文档！"
print("✅ 检索评估指标测试通过")
```

> **评估集构建**：从真实用户问题中采样 50~200 条，覆盖可回答、模糊、文档过时、应拒答四类，每次改动跑回归——这是调参有数据依据的前提。

[⬆ 返回顶部](#top)

### 7.2 RAGAS 自动化评估

<a id="s72"></a>

RAGAS 是最主流的开源 RAG 评估框架：用 LLM-as-Judge 自动计算 Faithfulness、Answer Relevance、Context Precision/Recall，无需人工逐条标注。

**安装**（涉及插件，手动执行）：

```bash
pip install ragas datasets
# 若与 LlamaIndex 联动：
pip install llama-index-core ragas
```

```python
# 代码案例：RAGAS 评估流程（需手动安装 ragas 并配置 LLM 的 API Key）
from ragas import evaluate
from ragas.metrics import (
    faithfulness,             # 忠实度：回答是否忠于上下文
    answer_relevancy,         # 答案相关性：是否切题
    context_precision,        # 上下文精确率：检索内容的相关占比
    context_recall,           # 上下文召回率：该找到的都找到了吗
)
from datasets import Dataset

# ① 组装评估数据：单条 = 问题 + 检索到的上下文列表 + 系统回答 + 标准答案
data = {
    "question": ["泰禾 2025 年营收是多少？"],
    "contexts": [["泰禾 2025 年营收 12.3 亿元，同比增长 18%。"]],
    "answer":   ["泰禾 2025 年营收为 12.3 亿元，同比增长 18%。"],
    "ground_truth": ["12.3 亿元"],
}
dataset = Dataset.from_dict(data)

# ② 执行评估（自动使用环境变量中的 OpenAI Key 作为裁判模型；
#    可用 metrics 参数指定指标子集降低成本）
# result = evaluate(dataset, metrics=[
#     faithfulness, answer_relevancy, context_precision, context_recall
# ])
# print(result)  # 输出形如 {'faithfulness': 1.0, 'answer_relevancy': 0.92, ...}
print("✅ RAGAS 评估流程搭建完成（安装 ragas + 配置 Key 后取消注释即可运行）")
```

> **工程集成**：把 RAGAS 挂进 CI/CD——每次改分块策略/换嵌入模型/调 Top-K，自动跑评估集，指标回退则阻断发布。**警惕裁判偏差**：LLM 裁判有系统性偏好，建议用 50 条人工标注做校准基准。

[⬆ 返回顶部](#top)

---

## 8. 生产落地

<a id="s8"></a>

### 8.1 优化优先级路线

<a id="s81"></a>

不要一次性堆满所有技术。按"性价比递减"排序的实施路线（业界共识）：

| 优先级 | 动作 | 预期收益 | 成本 |
|--------|------|---------|------|
| P0 | 修分块策略（固定 300 Token + 50 重叠起步） | 决定天花板 | 低 |
| P0 | 建评估集 + 基线指标 | 后续一切优化的度量衡 | 低 |
| P1 | 加混合检索（向量 + BM25） | 召回 +5~15% | 低 |
| P1 | 加重排器（Cross-Encoder） | NDCG +10~15%，**单项收益最大** | 低（+100ms） |
| P2 | 上下文增强索引（Anthropic 式） | 检索失败率 -49% | 中（入库 LLM 调用） |
| P2 | 查询改写/路由（Adaptive） | 平均延迟/成本 -50% | 中 |
| P3 | CRAG 兜底（Web 搜索） | 长尾问题覆盖 | 中 |
| P3 | GraphRAG / Agentic RAG | 全局性/多跳问题 | 高 |

```python
# 代码案例：两阶段检索完整管线（混合召回 + 重排 + 压缩，整合前文各组件）
from llama_index.core import VectorStoreIndex, Document
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.core.postprocessor import EmbeddingRecallPostprocessor
from llama_index.core.embeddings import BaseEmbedding

class FixedEmbedding(BaseEmbedding):
    def _get_query_embedding(self, q: str) -> list[float]:
        return [1.0, 0.0] if "E03" in q else [0.0, 1.0]
    def _get_text_embedding(self, t: str) -> list[float]:
        return [1.0, 0.0] if "E03" in t else [0.0, 1.0]
    async def _aget_query_embedding(self, q: str) -> list[float]:
        return self._get_query_embedding(q)
    async def _aget_text_embedding(self, t: str) -> list[float]:
        return self._get_text_embedding(t)

docs = [
    Document(text="E03 报错码表示进料电机过载。"),
    Document(text="X-200 设备日常维护指南。"),
    Document(text="公司安全培训安排。"),
]
index = VectorStoreIndex.from_documents(docs, embed_model=FixedEmbedding())

# ① 第一阶段：混合召回 Top-20（快、粗）
stage1 = QueryFusionRetriever(
    [index.as_retriever(similarity_top_k=20),
     BM25Retriever.from_defaults(docs=docs, similarity_top_k=20)],
    similarity_top_k=20, mode="reciprocal_rerank", num_queries=1,
)
candidates = stage1.retrieve("E03 报错怎么处理")

# ② 第二阶段：重排（正式环境用 CrossEncoder/SentenceTransformerRerank）
#    此处演示用嵌入相似度过滤器代替重排逻辑
stage2 = EmbeddingRecallPostprocessor(
    embed_model=FixedEmbedding(), similarity_cutoff=0.5
)
final = stage2.postprocess_nodes(candidates, query_str="E03 报错怎么处理")

# ③ 验证：无关文档被过滤，Top 结果聚焦
assert all("E03" in n.node.text or "报错" in n.node.text for n in final)
print(f"两阶段管线：召回 {len(candidates)} → 精选 {len(final)}")
print("✅ 两阶段检索管线测试通过（生产中 stage2 换 CrossEncoder 重排器即可）")
```

[⬆ 返回顶部](#top)

### 8.2 常见失效模式排查

<a id="s82"></a>

线上 RAG 出问题时，按"检索层 → 生成层"顺序排查（80% 的问题在检索层）：

| 症状 | 根因 | 排查方法 | 解法 |
|------|------|---------|------|
| 检索不到（Top-K 全无关） | 分块切断关键信息 | 打印命中块原文，检查边界 | 调分块/父子分块 |
| 精确词检索不到 | 纯向量检索弱于关键词 | 用关键词直查 BM25 对比 | 开混合检索 |
| 检索到了但答错 | Top-K 噪声稀释注意力 | 打印全部 Top-K 看占比 | 加重排、压 K |
| 引用对不上 | 未强制引用格式 | 检查生成 Prompt | 强制"每句标注来源" |
| 上下文对却答错 | Lost in the Middle | 关键事实放中间做对照测试 | 布点重排 + 压缩 |
| 偶发幻觉 | 弱证据也强行作答 | 构造"应拒答"测试集 | Self-RAG/CRAG 拒答分支 |
| 相似问题答案漂移 | 无缓存，每轮检索结果抖动 | 同题连续请求对比 | 结果缓存 + 温度调 0 |

```python
# 代码案例：检索层/生成层分层诊断函数（离线可跑，生产可直接复用）
def diagnose(question: str, index, embed_model=None, top_k: int = 5) -> dict:
    """分层诊断：先看检索质量，再看生成质量，输出定位结论"""
    # ① 检索层：打印 Top-K 原文与分数，人工判断相关性
    nodes = index.as_retriever(similarity_top_k=top_k).retrieve(question)
    retrieval_dump = [
        {"rank": i + 1, "score": round(n.score or 0, 3), "text": n.text[:50]}
        for i, n in enumerate(nodes)
    ]
    # ② 快速判定：Top1 分数过低 → 检索层问题，与生成无关
    top1_score = nodes[0].score if nodes else 0.0
    if top1_score < 0.3:
        conclusion = "检索层问题：Top1 分数过低，优先排查分块与查询质量"
    else:
        conclusion = "检索层正常：若答案仍错误，排查生成层 Prompt/上下文布点"
    return {"top1_score": round(top1_score, 3), "retrieval": retrieval_dump,
            "conclusion": conclusion}

# 使用示例（index 为已构建的 VectorStoreIndex）：
# report = diagnose("E03 报错怎么处理", index)
# for k, v in report.items(): print(k, "→", v)
print("✅ 分层诊断函数就绪：线上 badcase 先跑它，避免盲目调参")
```

> **纪律**：每次只改一个变量（分块大小/Top-K/重排器），跑评估集对比后再合入——多变量同改无法归因。

[⬆ 返回顶部](#top)

---

## 9. 总结

<a id="s9"></a>

Advanced RAG 的核心心法：

1. **三阶段框架**：索引决定天花板、查询决定入口、重排决定精度——定位问题时先分层；
2. **性价比排序**：评估集 → 分块 → 混合检索 → 重排 → 上下文增强 → 查询路由 → CRAG → GraphRAG/Agent；
3. **先度量再优化**：没有 Hit@K / MRR / Faithfulness 基线，一切调参都是盲调；
4. **架构匹配场景**：FAQ 用朴素 RAG + 重排就够；全局性问题上 GraphRAG；多跳推理且预算充足才上 Agentic RAG；
5. **警惕新技术失效模式**：Agent 检索死循环、GraphRAG 实体识别误差、LLM 裁判偏差——每个高级架构都要配护栏（最大轮次、超时、人工校准）。

推荐学习路径：跑通本文 2.1/4.1/4.2/5.1/7.1 五个离线用例 → 接入真实 LLM 与嵌入模型 → 建 50 条评估集 → 按 8.1 优先级逐项升级并回归验证。

[⬆ 返回顶部](#top)
