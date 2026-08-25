# LlamaIndex 框架详解

> 面向 RAG 与智能文档代理的数据框架 —— 截至 2026 年 8 月（llama-index 0.14.x / llamaindex 0.12.x）

<a id="top"></a>

## 目录

- [1. 框架概述](#s1)
  - [1.1 什么是 LlamaIndex](#s11)
  - [1.2 发展历程](#s12)
  - [1.3 核心设计理念](#s13)
  - [1.4 与 LangChain 的对比](#s14)
- [2. 核心概念与数据模型](#s2)
  - [2.1 Document（文档）](#s21)
  - [2.2 Node（节点）](#s22)
  - [2.3 Metadata（元数据）与关系](#s23)
  - [2.4 Settings（全局配置）](#s24)
- [3. 核心组件体系](#s3)
  - [3.1 数据连接器（LlamaHub Readers）](#s31)
  - [3.2 文档解析（LlamaParse）](#s32)
  - [3.3 嵌入模型（Embedding）](#s33)
  - [3.4 向量存储（Vector Stores）](#s34)
  - [3.5 检索器（Retrievers）](#s35)
  - [3.6 后处理器（Node Postprocessors）](#s36)
  - [3.7 引擎（Engines）](#s37)
- [4. 索引类型详解](#s4)
  - [4.1 VectorStoreIndex（向量索引）](#s41)
  - [4.2 SummaryIndex（摘要索引）](#s42)
  - [4.3 TreeIndex（树索引）](#s43)
  - [4.4 KeywordTableIndex（关键词表索引）](#s44)
  - [4.5 PropertyGraphIndex（属性图索引）](#s45)
- [5. 查询与检索增强](#s5)
  - [5.1 混合检索（Hybrid Retrieval）](#s51)
  - [5.2 查询变换（Query Transforms）](#s52)
  - [5.3 子问题查询引擎（SubQuestionQueryEngine）](#s53)
  - [5.4 重排序（Reranking）](#s54)
- [6. Agent 与 Workflows](#s6)
  - [6.1 Agent 框架](#s61)
  - [6.2 多智能体协作（LlamaAgents）](#s62)
  - [6.3 事件驱动 Workflows](#s63)
  - [6.4 工具调用与函数集成](#s64)
- [7. 快速上手](#s7)
  - [7.1 环境安装](#s71)
  - [7.2 五步搭建 RAG 问答](#s72)
  - [7.3 本地模型接入（Ollama）](#s73)
  - [7.4 TypeScript 版本](#s74)
- [8. 应用场景](#s8)
  - [8.1 企业知识库问答](#s81)
  - [8.2 文档分析与报告](#s82)
  - [8.3 多模态检索](#s83)
  - [8.4 智能文档代理](#s84)
- [9. 商业产品与部署](#s9)
  - [9.1 LlamaParse](#s91)
  - [9.2 LlamaCloud](#s92)
  - [9.3 llama-deploy 与生产部署](#s93)
- [10. 最佳实践](#s10)
  - [10.1 分块策略](#s101)
  - [10.2 元数据设计](#s102)
  - [10.3 检索质量优化](#s103)
  - [10.4 常见问题与排查](#s104)
- [11. 总结与学习资源](#s11)
  - [11.1 官方资源](#s111)
  - [11.2 学习路径建议](#s112)

---

## 1. 框架概述

<a id="s1"></a>

### 1.1 什么是 LlamaIndex

<a id="s11"></a>

LlamaIndex 是一个 **MIT 开源许可** 的数据框架（Data Framework），用于构建"以私有数据为底座"的大语言模型（LLM）应用，核心场景是 **RAG（检索增强生成）** 与 **智能文档代理**。它同时提供 Python 和 TypeScript 两种语言实现。

一句话概括：**"把你的数据连接到 LLM"** —— 从 PDF、网页、数据库、API 中摄取数据，建立索引，然后让 LLM 基于这些数据回答问题、执行任务。

| 维度 | 说明 |
|------|------|
| 当前版本（Python） | llama-index 0.14.x（2026-08 最新 0.14.24） |
| 当前版本（TypeScript） | llamaindex 0.12.x |
| 开源协议 | MIT（可免费商用） |
| 语言 | Python 3.10+ / TypeScript（Node 18+、Bun、Deno、Cloudflare Workers、Vercel Edge） |
| 核心定位 | 检索优先（Retrieval-first）、文档代理（Document Agents） |
| 社区规模 | GitHub ~4.8 万 Star、1800+ 贡献者、300+ LlamaHub 集成包 |
| 安装方式 | `pip install llama-index`（Python）/ `npm i llamaindex`（TS） |

与其他框架的本质区别：LangChain 是"链/代理优先"，LlamaIndex 是 **"数据优先"** —— 索引与检索是它的骨架，其他能力（Agent、Workflows）围绕数据能力展开。

[⬆ 返回顶部](#top)

### 1.2 发展历程

<a id="s12"></a>

LlamaIndex 的演进路径清晰地反映了 RAG 领域的发展方向：

| 时间 | 里程碑 |
|------|--------|
| 2022-10 | 以 "GPT Index" 名称首次发布 |
| 2022-11 | 更名为 LlamaIndex |
| 2023 Q2 | 推出 LlamaHub（数据连接器市场），Star 破 2 万 |
| 2023 Q3 | 加入多模态支持，Star 破 3 万 |
| 2023 Q4 | 推出 LlamaParse（文档解析服务），Star 破 4 万 |
| 2024 Q1 | 推出 LlamaCloud（托管服务）与 TypeScript 版本（LlamaIndex.TS） |
| 2024 Q2 | 发布 OCR 平台能力，支持 130+ 文档格式 |
| 2025 | 正式转型"文档代理"平台；LlamaParse/LlamaCloud GA；完成 1900 万美元 A 轮融资；事件驱动 Workflows 成为编排主力 |
| 2026 | 版本推进至 0.14.x；定位为"agentic document and OCR platform"（智能文档与 OCR 平台） |

创始人 Jerry Liu 在 2025 年中明确表示："我们已全面转向多智能体框架"，将传统 RAG 描述为"非常固定的流程"，而代理（Agent）能按任务需求动态加载文件、分析函数、检索特定页面。

[⬆ 返回顶部](#top)

### 1.3 核心设计理念

<a id="s13"></a>

LlamaIndex 的三大设计理念：

1. **检索优先（Retrieval-first）**：开箱即用的默认配置即为生产级检索——混合搜索（BM25 关键词 + 稠密向量）、重排序管线、多种分块策略都以"可配置默认值"的形式存在，而非让开发者从零组装。

2. **数据抽象统一（Unified Data Abstraction）**：所有来源（文件、数据库、API、网页）经连接器统一为 `Document` → `Node` 的标准结构，上层组件只面对统一数据模型。

3. **流水线极短（Minimal Pipeline）**：五行业务代码即可完成"摄取 → 索引 → 查询"闭环，降低入门门槛；同时通过 Workflows 支持复杂生产级编排。

核心管线（Pipeline）：

```
数据源（PDF/网页/DB/API）
   │  ① 摄取（Ingestion）：连接器读取 + 解析 + 分块 + 嵌入
   ▼
索引（Index）：向量 / 摘要 / 树 / 关键词表 / 属性图
   │  ② 索引（Indexing）
   ▼
查询引擎（Query Engine）/ 聊天引擎 / Agent
   │  ③ 查询（Querying）：检索 + 后处理 + 合成
   ▼
最终回答
```

[⬆ 返回顶部](#top)

### 1.4 与 LangChain 的对比

<a id="s14"></a>

LlamaIndex 与 LangChain 常被放在一起比较，2026 年两者的定位已经明显分化：

| 对比维度 | LlamaIndex | LangChain / LangGraph |
|----------|------------|----------------------|
| 核心理念 | 数据优先（检索 + 索引为骨架） | 链/代理优先（编排为骨架） |
| 最佳场景 | RAG 项目、文档问答、多模态检索 | 多步代理、工具调用、持久记忆 |
| 上手速度 | 快（5 行代码出 RAG，~6ms 框架开销） | 中等（抽象层较多） |
| 编排方式 | 事件驱动 Workflows（轻量、低预设） | LangGraph 状态机（显式、强控制） |
| 生产化 | llama-deploy 将 Workflows 部署为服务 | LangSmith 可观测性平台 |
| 版本策略 | 未宣布 1.0，API 演进较快（0.14.x） | 2025-10 发布 1.0，稳定性契约 |
| 商业层 | LlamaCloud + LlamaParse（文档层） | LangSmith（可观测与部署） |
| 社区 | ~4.8 万 Star，300+ 集成 | 10 万+ Star，生态最大 |

**选型建议**：
- 新 RAG 项目 → 优先 LlamaIndex，30 分钟内跑通；
- 复杂多智能体/状态机 → LangGraph 更合适；
- 两者也**可以混用**（LlamaIndex 提供检索组件，LangChain 负责编排）；
- 需要流水线可序列化、可审计 → 考虑 Haystack（2.29.x）。

[⬆ 返回顶部](#top)

---

## 2. 核心概念与数据模型

<a id="s2"></a>

### 2.1 Document（文档）

<a id="s21"></a>

`Document` 是 LlamaIndex 的**数据输入单元**，代表一个完整的来源对象（一个文件、一篇文章、一条数据库记录）。它包含：

- `text`：文档的原始文本内容；
- `metadata`：文档级元数据（文件名、来源 URL、作者、日期等）；
- `relationships`：与其他文档/节点的关系（如来源关系）。

读取文档的标准方式是通过 Reader（见 3.1）：

```python
from llama_index.core import SimpleDirectoryReader

documents = SimpleDirectoryReader("data/").load_data()
# data/ 目录下的 PDF、DOCX、TXT、HTML 等会被自动解析为 Document 列表
```

[⬆ 返回顶部](#top)

### 2.2 Node（节点）

<a id="s22"></a>

`Node` 是**索引与检索的最小单元**。一个 Document 会被按分块策略切分成多个 Node，每个 Node 拥有：

- `text`：分块后的文本；
- `metadata`：继承自 Document 并叠加节点级元数据；
- `node_id`：唯一标识；
- `embedding`：嵌入向量（索引时生成）；
- `relationships`：保留与源 Document 的关联。

切分工具是 `NodeParser`（默认 `SentenceSplitter`，按句子边界切分，默认 chunk_size=1024、chunk_overlap=20）：

```python
from llama_index.core.node_parser import SentenceSplitter

parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)
nodes = parser.get_nodes_from_documents(documents)
```

分块质量直接影响检索效果，10.1 节会给出策略建议。

[⬆ 返回顶部](#top)

### 2.3 Metadata（元数据）与关系

<a id="s23"></a>

元数据（Metadata）是 LlamaIndex 提升检索精度的关键杠杆：

**作用**：
1. **过滤**：检索时按元数据条件过滤（如只检索某日期范围、某部门文档）；
2. **上下文增强**：元数据作为 prompt 上下文喂给 LLM，帮助生成更准确的回答；
3. **来源追溯**：回答后可定位到具体文件与页码。

**示例**：

```python
from llama_index.core import Document

doc = Document(
    text="产品 2026 年 Q2 营收数据……",
    metadata={
        "file_name": "q2-report.pdf",
        "department": "finance",
        "year": 2026,
    },
)

# 检索时按元数据过滤
query_engine = index.as_query_engine(
    filters=MetadataFilters(
        filters=[
            MetadataFilter(key="department", value="finance"),
        ]
    )
)
```

**关系（Relationships）**：Node 与 Document 之间通过关系图关联（如 `SOURCE` 关系），支持引用链追踪与图结构索引。

[⬆ 返回顶部](#top)

### 2.4 Settings（全局配置）

<a id="s24"></a>

`Settings` 是 LlamaIndex 0.10+ 引入的**全局配置对象**，统一管理 LLM、嵌入模型、分块器、节点解析器等默认组件，避免在每个组件上重复传参：

```python
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

Settings.llm = OpenAI(model="gpt-4o", temperature=0.1)
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.chunk_size = 512
Settings.chunk_overlap = 50
```

配置后，`VectorStoreIndex.from_documents()` 会自动使用 Settings 中的模型与参数。这是搭建项目时**第一个要配置的东西**。

[⬆ 返回顶部](#top)

---

## 3. 核心组件体系

<a id="s3"></a>

### 3.1 数据连接器（LlamaHub Readers）

<a id="s31"></a>

LlamaHub 是 LlamaIndex 的**集成市场**，提供 300+ 官方/社区连接器（Reader），覆盖：

| 类别 | 示例 |
|------|------|
| 文件格式 | PDF、DOCX、PPTX、XLSX、EPUB、Markdown、JSON、CSV |
| 数据库 | PostgreSQL、MySQL、SQLite、MongoDB、Neo4j |
| 云存储 | S3、GCS、Azure Blob、Dropbox、Google Drive |
| 生产力工具 | Notion、Google Docs、Slack、Confluence、Jira、飞书 |
| API/网页 | 网页抓取、RSS、Twitter、arXiv、Wikipedia |

**安装与使用**（每个连接器是独立包，按需安装）：

```bash
pip install llama-index-readers-notion
```

```python
from llama_index.readers.notion import NotionPageReader

documents = NotionPageReader(integration_token="xxx").load_data(page_ids=["..."])
```

通用本地文件用 `SimpleDirectoryReader`（随 meta 包自带），支持 PDF/DOCX/TXT/HTML/CSV/图片等。

[⬆ 返回顶部](#top)

### 3.2 文档解析（LlamaParse）

<a id="s32"></a>

LlamaParse 是 LlamaIndex 的**商用文档解析服务**（API），专门处理"会击垮朴素流水线"的复杂文档：

- 扫描版 PDF（OCR）；
- 财务表格、复杂版式；
- PPT/幻灯片、内嵌图表、图片说明；
- 手写内容、多栏排版、页眉页脚。

**使用示例**：

```bash
pip install llama-parse
```

```python
from llama_parse import LlamaParse

parser = LlamaParse(result_type="markdown")
documents = parser.load_data("./scanned_report.pdf")
```

免费额度内可直接使用（LlamaCloud 注册获得 API Key）。LlamaParse 也是 LlamaCloud 的核心组件之一（详见第 9 章）。

[⬆ 返回顶部](#top)

### 3.3 嵌入模型（Embedding）

<a id="s33"></a>

嵌入模型（Embedding Model）将文本转换为向量，是向量检索的基础。LlamaIndex 支持通过统一接口接入几乎所有主流嵌入模型：

| 类型 | 代表 | 安装包 |
|------|------|--------|
| OpenAI | text-embedding-3-small / large | `llama-index-embeddings-openai` |
| 开源本地 | BGE、Nomic、bge-m3 | `llama-index-embeddings-huggingface` |
| Ollama 本地 | nomic-embed-text 等 | `llama-index-embeddings-ollama` |
| 国产模型 | 通义、智谱、文心 | 各厂商集成包 |

```python
from llama_index.embeddings.ollama import OllamaEmbedding

Settings.embed_model = OllamaEmbedding(model_name="nomic-embed-text")
```

本地嵌入模型适合数据隐私敏感或离线场景，与 7.3 节 Ollama 方案搭配。

[⬆ 返回顶部](#top)

### 3.4 向量存储（Vector Stores）

<a id="s34"></a>

向量存储负责**持久化嵌入向量并支持相似度检索**。LlamaIndex 支持 20+ 向量数据库，通过统一接口切换：

| 存储 | 特点 | 安装包 |
|------|------|--------|
| 内存（默认） | 零配置，原型演示用 | 内置 |
| Chroma | 轻量、本地文件 | `llama-index-vector-stores-chroma` |
| Qdrant | 高性能、支持过滤+混合检索 | `llama-index-vector-stores-qdrant` |
| Milvus / Zilliz | 大规模生产级 | `llama-index-vector-stores-milvus` |
| Weaviate | 云原生、多租户 | `llama-index-vector-stores-weaviate` |
| PostgreSQL pgvector | 与业务库共存 | `llama-index-vector-stores-postgres` |
| Elasticsearch | 企业已有基础设施 | `llama-index-vector-stores-elasticsearch` |

**接入示例**（Qdrant）：

```python
from llama_index.vector_stores.qdrant import QdrantVectorStore
import qdrant_client

client = qdrant_client.QdrantClient(path="./qdrant_data")
vector_store = QdrantVectorStore(client=client, collection_name="docs")

index = VectorStoreIndex.from_documents(documents, vector_store=vector_store)
```

对已用 PostgreSQL 的团队，`pgvector` 是最省事的生产选择（无需引入新中间件）。

[⬆ 返回顶部](#top)

### 3.5 检索器（Retrievers）

<a id="s35"></a>

检索器（Retriever）负责从索引中**找出与查询最相关的 Node**。不同类型：

| 检索器 | 用途 |
|--------|------|
| `VectorIndexRetriever` | 向量相似度检索（默认） |
| `BM25Retriever` | 关键词稀疏检索（精确术语匹配） |
| `HybridRetriever` | 向量 + BM25 融合（推荐，见 5.1） |
| `SummaryIndexRetriever` | 摘要索引顺序检索 |
| `KeywordTableRetriever` | 关键词表检索 |
| `AutoMergingRetriever` | 自动合并相邻小节点为大上下文 |
| `RouterRetriever` | 按查询路由到不同检索器 |

```python
from llama_index.core.retrievers import VectorIndexRetriever

retriever = VectorIndexRetriever(index=index, similarity_top_k=5)
nodes = retriever.retrieve("公司的营收是多少？")
```

[⬆ 返回顶部](#top)

### 3.6 后处理器（Node Postprocessors）

<a id="s36"></a>

后处理器（Node Postprocessor）在**检索之后、生成之前**对 Node 做精加工：

| 后处理器 | 作用 |
|----------|------|
| `SimilarityPostprocessor` | 过滤低于相似度阈值的 Node |
| `KeywordNodePostprocessor` | 按关键词包含/排除 Node |
| `MetadataReplacementPostProcessor` | 用元数据替换 Node 文本（如文件名） |
| `LongContextReorder` | 解决"上下文中间丢失"问题（Lost in the Middle） |
| `LLMRerank` | 用 LLM 对 Top-K 重新排序（见 5.4） |

```python
from llama_index.core.postprocessor import SimilarityPostprocessor

query_engine = index.as_query_engine(
    node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=0.7)]
)
```

后处理器是**低成本、高收益**的质量优化手段。

[⬆ 返回顶部](#top)

### 3.7 引擎（Engines）

<a id="s37"></a>

引擎是 LlamaIndex 的**对外执行入口**，有三种形态：

| 引擎 | 用途 |
|------|------|
| `QueryEngine` | 单轮问答（query 方法） |
| `ChatEngine` | 多轮对话（chat 方法，带记忆） |
| `Agent` | 自主执行多步任务（调用工具） |

```python
# QueryEngine（单轮）
query_engine = index.as_query_engine()
response = query_engine.query("这份文档讲了什么？")

# ChatEngine（多轮）
chat_engine = index.as_chat_engine(chat_mode="condense_question")
response = chat_engine.chat("针对刚才的内容，再详细说说……")
```

引擎可组合 `retriever` + `node_postprocessors` + `response_synthesizer`，实现自定义查询管线。

[⬆ 返回顶部](#top)

---

## 4. 索引类型详解

<a id="s4"></a>

### 4.1 VectorStoreIndex（向量索引）

<a id="s41"></a>

**最常用**的索引。将每个 Node 嵌入为向量，查询时用向量相似度检索 Top-K 节点。

```python
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine(similarity_top_k=3)
```

**适用**：绝大多数 RAG 场景——语义搜索、开放问答、知识库。

**优点**：语义理解强、检索快、支持大规模；
**局限**：对精确术语匹配敏感（需配合 BM25）、依赖嵌入模型质量。

[⬆ 返回顶部](#top)

### 4.2 SummaryIndex（摘要索引）

<a id="s42"></a>

将所有 Node 按顺序存储，检索时**不加筛选**地取出全部（或指定数量）Node，交给 LLM 综合总结。

```python
from llama_index.core import SummaryIndex

index = SummaryIndex.from_documents(documents)
query_engine = index.as_query_engine()
```

**适用**：需要全局总结的小文档（如摘要一份说明书）、需要按顺序阅读的场景。
**局限**：Node 多时 token 成本高，不适合大语料。

[⬆ 返回顶部](#top)

### 4.3 TreeIndex（树索引）

<a id="s43"></a>

以**树形结构**组织 Node：叶节点为原始分块，父节点为子节点的 LLM 摘要，逐层向上构建。

查询时采用"从根到叶"的递归检索：先比较根层，再下钻相关分支，**节省 token**。

```python
from llama_index.core import TreeIndex

index = TreeIndex.from_documents(documents)
query_engine = index.as_query_engine()
```

**适用**：需要快速概括大文档结构、对 token 成本敏感的场景。
**局限**：构建耗时（多次 LLM 调用）、对单点细节查询可能丢失信息。

[⬆ 返回顶部](#top)

### 4.4 KeywordTableIndex（关键词表索引）

<a id="s44"></a>

提取每个 Node 的关键词，建立"关键词 → Node"映射表。查询时**用 LLM 从问题中提取关键词**，再定位相关 Node。

```python
from llama_index.core import KeywordTableIndex

index = KeywordTableIndex.from_documents(documents)
query_engine = index.as_query_engine()
```

**适用**：术语精确、领域封闭的场景（如法规条款、产品规格）。
**局限**：语义泛化能力弱，遇到同义表达易漏检；大语料下关键词表膨胀。

[⬆ 返回顶部](#top)

### 4.5 PropertyGraphIndex（属性图索引）

<a id="s45"></a>

**图索引**：将文档中的实体与关系抽取为属性图（Property Graph），支持 **Text-to-Cypher**、向量检索、关键词检索等多种查询方式。

```python
from llama_index.core import PropertyGraphIndex

index = PropertyGraphIndex.from_documents(documents)
query_engine = index.as_query_engine(
    graph_query_syntax="cypher",  # 或 "duckdb" / "opencypher"
)
```

**适用**：实体关系密集的场景——人物关系、组织架构、产品依赖链、多跳推理问题。
**局限**：构建成本高（依赖 LLM 抽取质量）、图查询门槛较高。

**选型速查表**：

| 场景 | 推荐索引 |
|------|----------|
| 通用 RAG / 知识库问答 | VectorStoreIndex（+ 混合检索） |
| 全局总结、小文档 | SummaryIndex |
| 大文档快速概览、省 token | TreeIndex |
| 精确术语、封闭领域 | KeywordTableIndex |
| 实体关系推理 | PropertyGraphIndex |

[⬆ 返回顶部](#top)

---

## 5. 查询与检索增强

<a id="s5"></a>

### 5.1 混合检索（Hybrid Retrieval）

<a id="s51"></a>

**稠密向量（语义）+ 稀疏关键词（精确）** 融合，是 2026 年 LlamaIndex 的默认推荐方案：解决纯向量检索"同义词匹配弱、术语精确性差"的问题。

```python
from llama_index.core.retrievers import HybridRetriever
from llama_index.core.indices.vector_store.retrievers import VectorIndexRetriever
from llama_index.retrievers.bm25 import BM25Retriever

vector_retriever = VectorIndexRetriever(index=index, similarity_top_k=5)
bm25_retriever = BM25Retriever.from_defaults(docstore=index.docstore, similarity_top_k=5)

hybrid = HybridRetriever(vector_retriever, bm25_retriever)
nodes = hybrid.retrieve("Q2 营收数据")
```

融合策略（RRF / 加权和）会将两类结果合并去重，显著提升召回质量。生产环境建议 **默认开启混合检索**。

[⬆ 返回顶部](#top)

### 5.2 查询变换（Query Transforms）

<a id="s52"></a>

在检索前对用户问题做**改写/拆解**，提升检索命中率。常用变换：

| 变换 | 作用 | 示例场景 |
|------|------|----------|
| `HyDEQueryTransform` | 先让 LLM 生成假设答案，再用答案检索 | 问题太抽象、词汇与文档不一致 |
| `StepDecomposeQueryTransform` | 把复杂问题拆成子问题逐步检索 | "对比 A 和 B 的优缺点" |
| `MultiStepQueryEngine` | 多步迭代检索，逐步补全信息 | 跨多文档的综合问题 |

```python
from llama_index.core.query_engine import MultiStepQueryEngine
from llama_index.core.query_transform import StepDecomposeQueryTransform

step_decompose = StepDecomposeQueryTransform(llm=Settings.llm)
query_engine = MultiStepQueryEngine(query_engine=query_engine, query_transform=step_decompose)
```

**经验**：当检索结果"看起来相关但回答不全"时，优先尝试查询变换。

[⬆ 返回顶部](#top)

### 5.3 子问题查询引擎（SubQuestionQueryEngine）

<a id="s53"></a>

将复杂问题**拆解为多个子问题**，分别路由到**不同的工具/数据源**查询，最后汇总答案：

```python
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.core.tools import QueryEngineTool, ToolMetadata

engine_1 = index_1.as_query_engine()
engine_2 = index_2.as_query_engine()

query_engine = SubQuestionQueryEngine.from_defaults(
    query_engine_tools=[
        QueryEngineTool(query_engine=engine_1, metadata=ToolMetadata(name="财报库", description="公司财报相关")),
        QueryEngineTool(query_engine=engine_2, metadata=ToolMetadata(name="新闻库", description="公司新闻相关")),
    ],
)
response = query_engine.query("2026 年公司业绩如何？相比去年有哪些变化？")
```

**适用**：多数据源、跨文档、需要分而治之的复杂查询。这是 Agent 路由的轻量替代。

[⬆ 返回顶部](#top)

### 5.4 重排序（Reranking）

<a id="s54"></a>

先粗召回（Top-50），再用重排序模型精排（取 Top-5），是**性价比最高的检索质量提升手段**：

```python
from llama_index.core.postprocessor import LLMRerank, SentenceTransformerRerank

# 方案一：LLM 重排（更准，更贵）
query_engine = index.as_query_engine(
    similarity_top_k=20,
    node_postprocessors=[LLMRerank(top_n=5)],
)

# 方案二：交叉编码器重排（更快，推荐）
reranker = SentenceTransformerRerank(model="BAAI/bge-reranker-base", top_n=5)
query_engine = index.as_query_engine(
    similarity_top_k=20,
    node_postprocessors=[reranker],
)
```

| 方案 | 精度 | 速度 | 成本 |
|------|------|------|------|
| 不重排 | 基准 | 最快 | 最低 |
| 交叉编码器重排 | 高 | 快 | 低（本地模型） |
| LLM 重排 | 最高 | 慢 | 高 |

[⬆ 返回顶部](#top)

---

## 6. Agent 与 Workflows

<a id="s6"></a>

### 6.1 Agent 框架

<a id="s61"></a>

Agent 是 LlamaIndex 的**自主执行层**：给定目标，Agent 自行规划步骤、调用工具（检索、计算、API）、观察结果并继续，直到完成任务。

```python
from llama_index.core.agent import FunctionCallingAgentWorker
from llama_index.core.tools import QueryEngineTool, FunctionTool

# 工具 1：检索工具
query_tool = QueryEngineTool.from_defaults(
    query_engine=query_engine, name="knowledge_base", description="公司知识库检索"
)

# 工具 2：函数工具
def calculate_growth(current: float, previous: float) -> float:
    """计算增长率"""
    return (current - previous) / previous * 100

calc_tool = FunctionTool.from_defaults(fn=calculate_growth)

agent = FunctionCallingAgentWorker.from_tools(
    [query_tool, calc_tool], llm=Settings.llm, verbose=True
).as_agent()

response = agent.chat("查询去年与今年的营收，并计算增长率")
```

Agent 类型：
- `FunctionCallingAgent`（OpenAI 等函数调用模型）；
- `ReActAgent`（推理-行动循环，兼容更多模型）；
- `CustomAgent`（自定义循环）。

[⬆ 返回顶部](#top)

### 6.2 多智能体协作（LlamaAgents）

<a id="s62"></a>

2025 年起 LlamaIndex 定位为"多智能体框架"，支持**多个 Agent 分工协作**：

| 协作模式 | 说明 |
|----------|------|
| 编排者-工作者（Orchestrator-Worker） | 主 Agent 拆解任务，分发给专业子 Agent |
| 竞争模式 | 多个 Agent 各持方案，LLM 裁判选择 |
| 流水线模式 | Agent 链式传递，前一输出为后一输入 |

```python
from llama_index.core.agent import AgentRunner
from llama_index.core.orchestrators import AgentOrchestrator

# 定义多个专业 Agent
research_agent = ...   # 研究型
summary_agent = ...    # 总结型
calculator_agent = ... # 计算型

orchestrator = AgentOrchestrator(agents=[research_agent, summary_agent, calculator_agent])
response = orchestrator.run("调研竞品 2026 年策略并输出对比报告")
```

多智能体的价值：每个 Agent 聚焦单一职责，工具集更小、提示更精准、更容易调试。

[⬆ 返回顶部](#top)

### 6.3 事件驱动 Workflows

<a id="s63"></a>

Workflows 是 LlamaIndex 的**生产级编排方案**（替代早期 Pipeline）：步骤订阅事件、消费事件、发出新事件，形成轻量事件流——比 LangGraph 的状态机更灵活、预设更少。

```python
from llama_index.core.workflow import (
    Context, Event, StartEvent, StopEvent,
    Workflow, step,
)

class RetrieverEvent(Event):
    query: str

class MyRAGWorkflow(Workflow):
    @step
    async def retrieve(self, ctx: Context, ev: StartEvent) -> RetrieverEvent:
        nodes = index.as_retriever().retrieve(ev.query)
        ctx.data["nodes"] = nodes
        return RetrieverEvent(query=ev.query)

    @step
    async def synthesize(self, ctx: Context, ev: RetrieverEvent) -> StopEvent:
        response = Settings.llm.complete(
            f"基于以下资料回答：{ctx.data['nodes']}\n问题：{ev.query}"
        )
        return StopEvent(result=str(response))

# 运行
workflow = MyRAGWorkflow()
result = await workflow.run(query="公司 2026 年战略是什么？")
```

**Workflows 特性**：
- 支持异步、并行步骤、循环与条件分支；
- 可视化调试（`draw_all_flows()` 生成流程图）；
- 可被 llama-deploy 打包为独立服务（见 9.3）。

[⬆ 返回顶部](#top)

### 6.4 工具调用与函数集成

<a id="s64"></a>

LlamaIndex 提供统一的 **Tool 抽象**，把任意能力接入 Agent：

| 工具类型 | 用途 |
|----------|------|
| `QueryEngineTool` | 包装查询引擎（数据检索） |
| `FunctionTool` | 包装任意 Python 函数 |
| `RetrieverTool` | 包装检索器 |
| `VectorStoreTool` | 直接操作向量库 |

```python
from llama_index.core.tools import FunctionTool

def send_email(to: str, subject: str, body: str) -> str:
    """发送邮件（示例）"""
    return f"已发送给 {to}"

email_tool = FunctionTool.from_defaults(fn=send_email)
```

> 工具描述（docstring + 参数类型注解）会被 LLM 读取用于决策，**必须写清楚"何时用、怎么用"**，这直接影响 Agent 的工具选择正确率。

[⬆ 返回顶部](#top)

---

## 7. 快速上手

<a id="s7"></a>

### 7.1 环境安装

<a id="s71"></a>

**系统要求**：Python 3.10+（Windows / macOS / Linux）

**方式一：官方全家桶（推荐入门）**——自带 OpenAI、文件读取、内存向量库等常用集成：

```bash
pip install llama-index
```

**方式二：核心 + 按需集成（推荐生产）**——保持依赖精简：

```bash
pip install llama-index-core
pip install llama-index-llms-openai          # LLM
pip install llama-index-embeddings-openai    # 嵌入
pip install llama-index-vector-stores-qdrant # 向量库
pip install llama-index-readers-file         # 文件读取
```

**方式三：本地模型（Ollama）**：

```bash
pip install llama-index-core llama-index-readers-file \
    llama-index-llms-ollama llama-index-embeddings-ollama
```

> 建议在虚拟环境（venv）中安装，避免污染全局 Python。首次使用需要配置 `OPENAI_API_KEY`（或改用本地模型）。

**TypeScript**：

```bash
npm i llamaindex
# 或脚手架
npx create-llama@latest
```

[⬆ 返回顶部](#top)

### 7.2 五步搭建 RAG 问答

<a id="s72"></a>

官方 Starter 示例（LlamaIndex 0.14.x 验证通过），从文档到问答仅需 5 行：

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

documents = SimpleDirectoryReader("data").load_data()   # 1. 读取文档
index = VectorStoreIndex.from_documents(documents)       # 2. 切分+嵌入+建索引
query_engine = index.as_query_engine()                   # 3. 创建查询引擎
response = query_engine.query("这本书的作者成长经历是怎样的？")  # 4. 提问
print(response)                                          # 5. 输出回答
```

**完整带配置版本**（更贴近生产）：

```python
import os
from llama_index.core import Settings, VectorStoreIndex, SimpleDirectoryReader
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

# 0. 全局配置
Settings.llm = OpenAI(model="gpt-4o")
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.chunk_size = 512
Settings.chunk_overlap = 50

# 1-3. 摄取 + 索引 + 引擎
documents = SimpleDirectoryReader("data").load_data()
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine(similarity_top_k=5)

# 4-5. 问答
response = query_engine.query("公司 2026 年的战略重点是什么？")
print(response)
```

**目录结构建议**：

```
my-rag-app/
├── data/            # 原始文档
├── index/           # 持久化索引（可选）
├── app.py           # 主程序
├── requirements.txt
└── .env             # OPENAI_API_KEY=sk-xxx
```

[⬆ 返回顶部](#top)

### 7.3 本地模型接入（Ollama）

<a id="s73"></a>

数据不出内网的方案：**Ollama 本地运行 LLM + 嵌入模型**，LlamaIndex 官方集成包已稳定支持一年以上。

**前置**：安装 [Ollama](https://ollama.com) 并拉取模型：

```bash
ollama pull llama3.2        # LLM
ollama pull nomic-embed-text  # 嵌入
```

**Python 接入**：

```python
from llama_index.core import Settings, VectorStoreIndex, SimpleDirectoryReader
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding

Settings.llm = Ollama(model="llama3.2", request_timeout=60.0)
Settings.embed_model = OllamaEmbedding(model_name="nomic-embed-text")

documents = SimpleDirectoryReader("./docs").load_data()
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()
print(query_engine.query("关键结论是什么？"))
```

**适用**：内网部署、数据合规、无 API 预算的场景。注意本地模型的效果与速度取决于硬件（推荐 16GB+ 显存）。

[⬆ 返回顶部](#top)

### 7.4 TypeScript 版本

<a id="s74"></a>

LlamaIndex.TS（`llamaindex` 0.12.x）提供与 Python 版对齐的核心能力，支持 **Node 18+、Bun、Deno、Cloudflare Workers、Vercel Edge**（ESM-only）：

```typescript
import { VectorStoreIndex, SimpleDirectoryReader } from "llamaindex";

const documents = await new SimpleDirectoryReader("./data").loadData();
const index = await VectorStoreIndex.fromDocuments(documents);
const queryEngine = index.asQueryEngine();

const response = await queryEngine.query({ query: "文档的核心观点是什么？" });
console.log(response.toString());
```

**适用**：全栈项目（前后端同语言）、Serverless/Edge 部署场景。核心概念与 Python 版一致，可平滑迁移。

[⬆ 返回顶部](#top)

---

## 8. 应用场景

<a id="s8"></a>

### 8.1 企业知识库问答

<a id="s81"></a>

**场景**：制度文档、产品手册、FAQ、技术文档的智能问答。

**架构**：

```
内部文档（PDF/Word/网页）
  → SimpleDirectoryReader / 各 Reader
  → 分块 + 嵌入（混合检索：向量 + BM25）
  → 向量库（pgvector / Qdrant）
  → QueryEngine / ChatEngine
  → 员工问答（带引用来源）
```

**要点**：
- 元数据过滤（按部门、文档类型、有效期）保证权限与时效；
- 引用来源（`response.source_nodes`）提升可信度；
- 混合检索 + 重排保证精度。

[⬆ 返回顶部](#top)

### 8.2 文档分析与报告

<a id="s82"></a>

**场景**：财报分析、合同审查、研究报告摘要。

**能力组合**：
- LlamaParse：解析复杂表格、扫描件、图表；
- SummaryIndex：全文总结；
- SubQuestionQueryEngine：跨文档对比（"A 方案与 B 方案差异"）；
- 结构化输出：`PydanticOutputParser` 将结果约束为 JSON 供下游系统使用：

```python
from llama_index.core.output_parsers import PydanticOutputParser
from pydantic import BaseModel

class ContractSummary(BaseModel):
    parties: list[str]
    amount: float
    risks: list[str]

# 查询时指定结构化输出模型
```

[⬆ 返回顶部](#top)

### 8.3 多模态检索

<a id="s83"></a>

0.10 之后多模态检索已成熟（此前为研究级），支持**同一查询管线中同时检索文本与图片**：

- 图片经视觉模型生成描述或嵌入，纳入同一索引；
- 查询"找出含折线图的页面"可同时命中文本与图表节点；
- 配合 LlamaParse 的 OCR 能力处理图表型 PDF。

**适用**：带图文档（产品图册、设计稿、教学材料）、图表型财报。

[⬆ 返回顶部](#top)

### 8.4 智能文档代理

<a id="s84"></a>

2025-2026 的**主推定位**：从"被动问答"升级为"主动执行"的文档代理：

- 用户给出任务（"整理上季度所有客户的合同到期日并生成提醒清单"）；
- Agent 自主检索文档、解析表格、调用工具（写日历、发邮件、更新数据库）；
- 通过 Workflows 编排长流程，llama-deploy 部署为服务。

**示例能力矩阵**：

| 任务 | Agent 行为 |
|------|-----------|
| 合同管理 | 检索合同库 → 提取关键条款 → 生成到期提醒 |
| 报表生成 | 检索数据文档 → 计算指标 → 输出结构化报告 |
| 资料整理 | 多源检索 → 去重 → 生成专题知识包 |

[⬆ 返回顶部](#top)

---

## 9. 商业产品与部署

<a id="s9"></a>

### 9.1 LlamaParse

<a id="s91"></a>

LlamaParse 是 LlamaIndex 的**文档解析 API**（商用，有免费额度），定位"智能文档与 OCR 平台"：

| 能力 | 说明 |
|------|------|
| 格式支持 | 130+ 格式（PDF、DOCX、PPTX、XLSX、扫描件、网页等） |
| OCR | 扫描件、手写、低质量图片的文字识别 |
| 版式理解 | 表格、多栏、页眉页脚、内嵌图表的结构化提取 |
| 输出 | Markdown / 结构化数据，可直接进入索引管线 |
| 免费额度 | 每月 10,000 积分（LlamaCloud 账号） |

```bash
pip install llama-parse
```

```python
from llama_parse import LlamaParse

documents = LlamaParse(result_type="markdown").load_data("scanned.pdf")
```

**价值**：把"解析质量"这个 RAG 的上游瓶颈外包给专业服务——解析错了，后面检索再好也白搭。

[⬆ 返回顶部](#top)

### 9.2 LlamaCloud

<a id="s92"></a>

LlamaCloud 是 LlamaIndex 的**托管 SaaS**（2025-03 与 A 轮融资同期 GA），一站式管理文档解析、索引、检索：

**核心能力**：
- 托管解析 + 索引 + 检索 API；
- 访问控制（Access Control）与审计日志；
- 自动备份；
- 多租户隔离；
- 与开源组件 API 兼容，迁移成本低。

**适合**：不想自建检索基础设施的团队，或作为开源 LlamaIndex 的补充（托管解析与索引 + 自研查询层）。

[⬆ 返回顶部](#top)

### 9.3 llama-deploy 与生产部署

<a id="s93"></a>

**llama-deploy** 将 Workflows/Agent 打包为**生产可用的服务**（HTTP 端点），支撑异步任务、队列、横向扩展：

```bash
pip install llama-deploy
```

```
# 部署流程
Workflow / Agent 定义
  → llama-deploy 打包（含消息队列）
  → 暴露 REST / gRPC 服务
  → 异步执行 + 横向扩容
```

**生产化清单**：

| 环节 | 建议 |
|------|------|
| 依赖锁定 | 锁定 `llama-index-core` 与所用集成包版本（meta 包迭代较快） |
| 向量库 | 生产用 pgvector / Qdrant / Milvus，不要用内存存储 |
| LLM Key 管理 | 环境变量 / 密钥服务，禁止硬编码 |
| 监控 | 检索质量指标、响应延迟、token 消耗（可接 Langfuse/MLflow） |
| 异步化 | 长任务用 llama-deploy 或自建任务队列 |
| 隐私合规 | 内网部署用 Ollama + 本地嵌入 |

[⬆ 返回顶部](#top)

---

## 10. 最佳实践

<a id="s10"></a>

### 10.1 分块策略

<a id="s101"></a>

分块（Chunking）是检索质量的第一决定因素，没有"万能参数"，需要按文档类型调优：

| 文档类型 | 建议 chunk_size | 建议 overlap | 备注 |
|----------|----------------|--------------|------|
| 技术文档/论文 | 512~1024 | 50~100 | 保留完整段落 |
| 对话/邮件 | 256~512 | 30~50 | 按对话轮次分块更好 |
| 表格/结构化 | 不切分 | 0 | 整表作为一个 Node，配元数据 |
| 代码 | 按函数/类分块 | 20~50 | 语义边界优先 |

**进阶技巧**：
1. **按语义边界切分**：用 `MarkdownNodeParser`、`HTMLNodeParser` 按标题/结构切分，优于纯字符切分；
2. **父子分块（Small-to-Big）**：检索小块、返回大块上下文：

```python
from llama_index.core.node_parser import SentenceWindowNodeParser

# 检索窗口化节点，回答时扩展上下文
parser = SentenceWindowNodeParser.from_defaults(
    window_size=3, window_metadata_key="window"
)
```

3. **验证**：对 20~50 条典型问题做检索质量回归，调参要有数据依据。

[⬆ 返回顶部](#top)

### 10.2 元数据设计

<a id="s102"></a>

好的元数据 = 精确过滤 + 丰富上下文 + 来源可信。

**必须包含**：`file_name`、`file_type`、`created_at`、`source_url`（如有）。
**按业务加**：部门、文档类型、版本号、有效期、作者、标签。

**反模式**：
- ❌ 元数据放敏感信息（会被注入 prompt）；
- ❌ 元数据缺失导致"检索到了但无法解释来源"；
- ❌ 用元数据塞大段文本（应放正文）。

**引用输出**：回答时带上 `source_nodes` 的文件名与页码，提升可信度：

```python
response = query_engine.query("问题")
for node in response.source_nodes:
    print(node.metadata.get("file_name"), node.metadata.get("page_label"))
```

[⬆ 返回顶部](#top)

### 10.3 检索质量优化

<a id="s103"></a>

**分层优化路线图**（按性价比排序）：

| 优先级 | 手段 | 预期效果 |
|--------|------|----------|
| 1 | 混合检索（向量 + BM25） | 召回显著提升，成本极低 |
| 2 | 重排（交叉编码器） | Top-K 精度提升明显 |
| 3 | 元数据过滤 | 减少噪声、权限合规 |
| 4 | 查询变换（HyDE/多步） | 解决复杂问题漏检 |
| 5 | 分块调优 | 结构性提升，需测试验证 |
| 6 | 换更强的嵌入模型 | 语义天花板 |
| 7 | 微调嵌入（领域数据） | 领域效果极致，成本高 |

**评估指标**：Hit Rate（命中率）、MRR（平均倒数排名）、回答正确率——建议建立评估集持续回归。

[⬆ 返回顶部](#top)

### 10.4 常见问题与排查

<a id="s104"></a>

| 现象 | 原因 | 排查/解决 |
|------|------|-----------|
| 回答与文档无关 | 检索质量差 | 检查 Top-K 命中率，开混合检索 + 重排 |
| 检索到但答错 | 上下文被截断/提示词不当 | 增大 chunk，检查 response_synthesizer 模式 |
| 回答"我不知道"但文档有 | 元数据过滤过严 | 检查过滤条件；提升相似度阈值 |
| 很慢 | 检索数据量大 / 模型慢 | 向量库索引优化、减小 Top-K、用更小模型 |
| token 消耗高 | 上下文过大 | 精简分块、用 LongContextReorder、控制 Top-K |
| 多轮对话丢失上文 | 聊天模式不当 | 用 `condense_question` 模式或显式传历史 |
| 中文效果差 | 嵌入模型/分块不适配 | 换中文友好嵌入（bge 系列）、按语义分块 |

[⬆ 返回顶部](#top)

---

## 11. 总结与学习资源

<a id="s11"></a>

### 11.1 官方资源

<a id="s111"></a>

| 资源 | 地址 | 说明 |
|------|------|------|
| 官方文档 | https://docs.llamaindex.ai | 入门到进阶完整指南 |
| GitHub | https://github.com/run-llama/llama_index | 源码、Issue、示例 |
| 官网 | https://www.llamaindex.ai | 产品与公告 |
| LlamaCloud | https://cloud.llamaindex.ai | 托管服务控制台 |
| LlamaHub | https://llamahub.ai | 300+ 连接器/工具市场 |
| 博客 | https://blog.llamaindex.ai | 技术文章与最佳实践 |
| Discord | 官方社区 | 活跃问答、最新动态 |

[⬆ 返回顶部](#top)

### 11.2 学习路径建议

<a id="s112"></a>

**入门（1~2 天）**：
1. 按 7.2 节跑通五步 RAG；
2. 替换不同索引类型（第 4 章）理解差异；
3. 接入 LlamaParse 处理一份复杂 PDF。

**进阶（1~2 周）**：
1. 混合检索 + 重排 + 元数据过滤组合上线；
2. 用 Workflows 重写一个查询流程；
3. 给 Agent 接入 2~3 个 FunctionTool 完成真实任务；
4. 建立 50 条评估集做质量回归。

**生产（持续）**：
1. 选型 pgvector/Qdrant 持久化；
2. llama-deploy 部署服务化；
3. 关注 0.14.x 更新日志（未到 1.0，API 有演进）。

**结合本仓库**：可将本指南配套练习脚本放入 `practice/` 目录，按"安装 → 五步 RAG → 混合检索 → Agent"循序渐进；中文场景推荐 bge 系列嵌入 + Ollama 本地模型组合。

---

> 本文档基于 LlamaIndex 0.14.x（2026-08）整理，版本演进较快，关键 API 请以官方文档为准。

[⬆ 返回顶部](#top)
