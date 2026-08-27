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

**功能测试**（可独立运行的验证脚本，中文注释标注每一步）：

```python
from llama_index.core import Document

# ① 直接用字符串构造 Document（无需真实文件，适合单测）
doc = Document(
    text="LlamaIndex 是一个数据框架。",
    metadata={"file_name": "test.txt", "source": "unit-test"},
)

# ② 断言：文本与元数据正确写入
assert doc.text == "LlamaIndex 是一个数据框架。"
assert doc.metadata["file_name"] == "test.txt"
assert doc.metadata["source"] == "unit-test"
print("✅ Document 构造测试通过：", doc.metadata)
```

> 真实文件读取验证：`SimpleDirectoryReader("data/").load_data()` 需 data/ 目录存在，可用临时目录构造 txt 后断言 `len(documents) >= 1`（见 7.2 节测试）。

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

**功能测试**：

```python
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter

# ① 构造一篇较长的测试文本
doc = Document(text="第一句话。第二句话。第三句话。第四句话。第五句话。")

# ② 按句子切分：chunk_size 设为较小值以产生多个 Node
parser = SentenceSplitter(chunk_size=10, chunk_overlap=0)
nodes = parser.get_nodes_from_documents([doc])

# ③ 断言：Node 数量非空，且每个 Node 保留来源 Document 关联
assert len(nodes) >= 1
assert nodes[0].ref_doc_id == doc.doc_id
print(f"✅ 切分测试通过：共生成 {len(nodes)} 个 Node")
```

> 默认参数为 chunk_size=1024、chunk_overlap=20；调参策略见 10.1 节。

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

**功能测试**：

```python
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.vector_stores import MetadataFilters, MetadataFilter

# ① 构造带元数据的文档并切分
doc = Document(
    text="财务部 Q2 营收报告……",
    metadata={"department": "finance", "year": 2026},
)
parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)
nodes = parser.get_nodes_from_documents([doc])

# ② 断言：节点级元数据继承自文档
assert nodes[0].metadata["department"] == "finance"
assert nodes[0].metadata["year"] == 2026

# ③ 断言：检索过滤条件构造正确（key/value 匹配）
filters = MetadataFilters(filters=[MetadataFilter(key="department", value="finance")])
assert filters.filters[0].key == "department"
assert filters.filters[0].value == "finance"
print("✅ 元数据与过滤条件测试通过")
```

> 过滤条件需配合检索器使用：`index.as_retriever(filters=filters)`。

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

**功能测试**：

```python
from llama_index.core import Settings
from llama_index.core.node_parser import SentenceSplitter

# ① 修改全局配置（项目级默认参数）
Settings.chunk_size = 256
Settings.chunk_overlap = 30

# ② 断言：配置立即生效，且被组件默认读取
assert Settings.chunk_size == 256
assert Settings.chunk_overlap == 30
parser = SentenceSplitter.from_defaults()  # 不传参时读取 Settings 默认值
assert parser.chunk_size == 256
print(f"✅ Settings 测试通过：chunk_size={Settings.chunk_size}, chunk_overlap={Settings.chunk_overlap}")
```

> 注意：检索/生成类操作还需配置 `Settings.llm` 与 `Settings.embed_model`（见 7.2），否则会提示缺省。

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

**功能测试**（涉及安装的插件仅列出命令，不自动执行）：

```bash
# 安装所需插件（按需执行）
pip install llama-index-readers-file      # SimpleDirectoryReader 文件读取扩展
pip install llama-index-readers-notion    # Notion 连接器（示例）
```

```python
# 测试用例：SimpleDirectoryReader 读取临时目录
import os
import tempfile
from llama_index.core import SimpleDirectoryReader

# ① 创建临时目录并写入一个 txt 文件
tmpdir = tempfile.mkdtemp()
with open(os.path.join(tmpdir, "demo.txt"), "w", encoding="utf-8") as f:
    f.write("这是一份测试文档。")

# ② 读取目录并断言解析结果
documents = SimpleDirectoryReader(tmpdir).load_data()
assert len(documents) == 1
assert "测试文档" in documents[0].text
print("✅ 目录读取测试通过：", documents[0].metadata["file_name"])
```

> Notion 等外部连接器需真实 token 才能端到端验证；本地优先用 SimpleDirectoryReader 覆盖读取链路。

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

**功能测试**（涉及安装的插件仅列出命令，不自动执行）：

```bash
pip install llama-parse   # LlamaParse 解析服务 SDK
```

```python
# 测试用例：LlamaParse 初始化与参数校验（真实解析需 LLAMA_CLOUD_API_KEY）
from llama_parse import LlamaParse

# ① 初始化解析器：result_type 支持 markdown / text
parser = LlamaParse(result_type="markdown")
assert parser.result_type == "markdown"
print("✅ LlamaParse 初始化通过（真实解析需 API Key，命令：parser.load_data('scanned.pdf')）")
```

> 端到端验证：`export LLAMA_CLOUD_API_KEY=...` 后调用 `parser.load_data("./scanned_report.pdf")` 并断言返回非空列表。

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

**功能测试**（涉及安装的插件仅列出命令，不自动执行）：

```bash
pip install llama-index-embeddings-ollama   # Ollama 本地嵌入
```

```python
# 测试用例：嵌入模型连通性与语义相似度（需本地 Ollama 服务及 nomic-embed-text 模型）
import math
from llama_index.embeddings.ollama import OllamaEmbedding

embed_model = OllamaEmbedding(model_name="nomic-embed-text")

# ① 生成三个句子的向量
vec_a = embed_model.get_text_embedding("公司的营收是多少？")
vec_b = embed_model.get_text_embedding("企业 2026 年收入如何？")  # 与 A 语义相近
vec_c = embed_model.get_text_embedding("今天天气很好")            # 与 A 语义无关

# ② 断言：向量维度一致且非空
assert len(vec_a) > 0 and len(vec_a) == len(vec_b) == len(vec_c)

# ③ 简易余弦相似度：相近句子的相似度应高于无关句子
def cos(x, y):
    return sum(i * j for i, j in zip(x, y)) / (
        math.sqrt(sum(i * i for i in x)) * math.sqrt(sum(j * j for j in y)) + 1e-9
    )

assert cos(vec_a, vec_b) > cos(vec_a, vec_c)
print(f"✅ 嵌入测试通过：维度={len(vec_a)}, A-B={cos(vec_a, vec_b):.3f}, A-C={cos(vec_a, vec_c):.3f}")
```

> 若未启动 Ollama 会抛连接异常；离线/无 GPU 场景可换 HuggingFace 嵌入（`llama-index-embeddings-huggingface`）。

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

**功能测试**（涉及安装的插件仅列出命令，不自动执行）：

```bash
pip install llama-index-vector-stores-qdrant qdrant-client
```

```python
# 测试用例：Qdrant 本地模式建索引并检索（无需单独启动服务）
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.embeddings import BaseEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
import qdrant_client

# ① 自定义确定性嵌入：按"苹果/其他"返回固定向量，用于离线验证链路
class FixedEmbedding(BaseEmbedding):
    """固定向量嵌入（仅供测试，不产生真实语义）"""

    def _get_query_embedding(self, query: str) -> list[float]:
        return [1.0, 0.0] if "苹果" in query else [0.0, 1.0]

    def _get_text_embedding(self, text: str) -> list[float]:
        return [1.0, 0.0] if "苹果" in text else [0.0, 1.0]

    async def _aget_query_embedding(self, query: str) -> list[float]:
        return self._get_query_embedding(query)

    async def _aget_text_embedding(self, text: str) -> list[float]:
        return self._get_text_embedding(text)

# ② 用本地路径模式创建 Qdrant 客户端（数据落在 ./qdrant_test_data）
client = qdrant_client.QdrantClient(path="./qdrant_test_data")
vector_store = QdrantVectorStore(client=client, collection_name="test_docs")

# ③ 构建索引并检索
index = VectorStoreIndex.from_documents(
    [Document(text="苹果是一种水果。"), Document(text="香蕉也是一种水果。")],
    vector_store=vector_store,
    embed_model=FixedEmbedding(),
)
nodes = index.as_retriever(similarity_top_k=1).retrieve("苹果")
assert len(nodes) == 1 and "苹果" in nodes[0].text
print(f"✅ Qdrant 检索测试通过：命中「{nodes[0].text}」")
```

> 下文多处测试复用 `FixedEmbedding` 以离线验证链路，可复制本节定义；生产环境请替换为真实嵌入模型（3.3 节）。

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

**功能测试**：

```python
# 测试用例：VectorIndexRetriever 检索（FixedEmbedding 定义见 3.4 节）
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.retrievers import VectorIndexRetriever

index = VectorStoreIndex.from_documents(
    [Document(text="苹果是一种水果。"), Document(text="Python 是一门编程语言。")],
    embed_model=FixedEmbedding(),
)
retriever = VectorIndexRetriever(index=index, similarity_top_k=1)
nodes = retriever.retrieve("苹果")
assert len(nodes) == 1 and "苹果" in nodes[0].text
print(f"✅ 检索器测试通过：召回「{nodes[0].text}」")
```

> 检索器是查询引擎的底层组件，可单独测试召回质量；相似度阈值过滤见 3.6。

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

**功能测试**：

```python
# 测试用例：SimilarityPostprocessor 相似度过滤
from llama_index.core.schema import NodeWithScore, TextNode
from llama_index.core.postprocessor import SimilarityPostprocessor

# ① 构造一组带分数的假检索结果
fake_nodes = [
    NodeWithScore(node=TextNode(text="相关文档"), score=0.9),
    NodeWithScore(node=TextNode(text="不相关文档"), score=0.5),
]

# ② 应用过滤：低于阈值的节点被剔除
processor = SimilarityPostprocessor(similarity_cutoff=0.7)
filtered = processor.postprocess_nodes(fake_nodes)
assert len(filtered) == 1 and filtered[0].node.text == "相关文档"
print("✅ 后处理器测试通过：过滤后保留", len(filtered), "个节点")
```

> 后处理器在检索后、生成前执行，可与 LLMRerank 组合使用（见 5.4）。

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

**功能测试**：

```python
# 测试用例：QueryEngine 与 ChatEngine 构建（需配置 Settings.llm）
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.core.llms.mock import MockLLM

Settings.llm = MockLLM()  # 无真实 Key 时用假 LLM 走通链路
index = VectorStoreIndex.from_documents(
    [Document(text="测试文档内容。")], embed_model=FixedEmbedding()
)

# ① QueryEngine：单轮问答，返回带来源的响应对象
query_engine = index.as_query_engine()
response = query_engine.query("测试问题")
assert response is not None and len(response.source_nodes) >= 1

# ② ChatEngine：多轮对话（condense_question 模式自动压缩历史）
chat_engine = index.as_chat_engine(chat_mode="condense_question")
reply = chat_engine.chat("继续说说")
assert reply is not None
print(f"✅ 引擎测试通过：QueryEngine={str(response)[:20]}... ChatEngine 就绪")
```

> MockLLM 仅验证链路；生产请配置真实模型（`llama-index-llms-openai`）。

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

**功能测试**：

```python
# 测试用例：VectorStoreIndex 构建 + Top-K 检索（FixedEmbedding 见 3.4）
from llama_index.core import Document, VectorStoreIndex

index = VectorStoreIndex.from_documents(
    [
        Document(text="苹果是一种水果。"),
        Document(text="Java 是一门编程语言。"),
        Document(text="香蕉是热带水果。"),
    ],
    embed_model=FixedEmbedding(),
)
# 验证 Top-K 语义：固定嵌入下"苹果"应命中含"苹果"的节点
nodes = index.as_retriever(similarity_top_k=3).retrieve("苹果")
assert any("苹果" in n.text for n in nodes)
print(f"✅ VectorStoreIndex 测试通过：Top-3 命中 {len(nodes)} 个节点")
```

> 相似度检索依赖嵌入质量；精确术语场景建议叠加 BM25（5.1 节）。

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

**功能测试**：

```python
# 测试用例：SummaryIndex 顺序取回全部 Node（无需嵌入模型）
from llama_index.core import Document, SummaryIndex

index = SummaryIndex.from_documents([
    Document(text="第一段内容：介绍背景。"),
    Document(text="第二段内容：说明方案。"),
])
nodes = index.as_retriever().retrieve("任意问题")
assert len(nodes) == 2  # 不加筛选，全部返回
print(f"✅ SummaryIndex 测试通过：顺序返回 {len(nodes)} 个节点")
```

> 适合小文档全局总结；Node 多时 token 成本高。

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

**功能测试**：

```python
# 测试用例：TreeIndex 构建与检索（树构建需 LLM，用 MockLLM 验证链路）
from llama_index.core import Document, TreeIndex, Settings
from llama_index.core.llms.mock import MockLLM

Settings.llm = MockLLM()
index = TreeIndex.from_documents([
    Document(text="第一部分：项目背景与目标。"),
    Document(text="第二部分：实施方案与计划。"),
])
nodes = index.as_retriever().retrieve("项目")
assert len(nodes) >= 1
print(f"✅ TreeIndex 测试通过：检索到 {len(nodes)} 个节点")
```

> 真实使用中树构建会多次调用 LLM 生成摘要，耗时与 token 成本较高。

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

**功能测试**：

```python
# 测试用例：KeywordTableIndex 关键词检索（关键词提取需 LLM，用 MockLLM）
from llama_index.core import Document, KeywordTableIndex, Settings
from llama_index.core.llms.mock import MockLLM

Settings.llm = MockLLM()
index = KeywordTableIndex.from_documents([
    Document(text="合同法第一百条：违约责任。"),
    Document(text="劳动法关于试用期的规定。"),
])
nodes = index.as_retriever().retrieve("违约责任")
assert len(nodes) >= 1
print(f"✅ KeywordTableIndex 测试通过：检索到 {len(nodes)} 个节点")
```

> 适合封闭领域精确术语；同义表达可能漏检，需配合向量检索。

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

**功能测试**：

```python
# 测试用例：PropertyGraphIndex 图索引构建与检索（需 LLM 抽取实体关系）
from llama_index.core import Document, PropertyGraphIndex, Settings
from llama_index.core.llms.mock import MockLLM

Settings.llm = MockLLM()
index = PropertyGraphIndex.from_documents([
    Document(text="张三任职于泰禾公司，职位是 Java 开发。"),
])
nodes = index.as_retriever(include_text=True).retrieve("张三")
assert len(nodes) >= 1
print(f"✅ PropertyGraphIndex 测试通过：检索到 {len(nodes)} 个节点")
```

> 属性图支持 Text-to-Cypher 等图查询；如需 Neo4j 等外部图库，安装对应 `llama-index-graph-stores-*` 插件。

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

**功能测试**（涉及安装的插件仅列出命令，不自动执行）：

```bash
pip install llama-index-retrievers-bm25   # BM25 稀疏检索
```

```python
# 测试用例：混合检索（向量 + BM25 融合，FixedEmbedding 见 3.4）
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.core.llms.mock import MockLLM
from llama_index.core.indices.vector_store.retrievers import VectorIndexRetriever
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.retrievers import HybridRetriever

Settings.llm = MockLLM()
docs = [
    Document(text="公司 2026 年 Q2 营收 1.2 亿元。"),
    Document(text="公司发布了新一代产品。"),
]
index = VectorStoreIndex.from_documents(docs, embed_model=FixedEmbedding())

vector_retriever = VectorIndexRetriever(index=index, similarity_top_k=2)
bm25_retriever = BM25Retriever.from_defaults(docstore=index.docstore, similarity_top_k=2)
hybrid = HybridRetriever(vector_retriever, bm25_retriever)

# 精确术语"营收"由 BM25 兜底召回
nodes = hybrid.retrieve("营收 1.2 亿元")
assert len(nodes) >= 1 and any("营收" in n.text for n in nodes)
print(f"✅ 混合检索测试通过：召回 {len(nodes)} 个节点")
```

> 生产环境建议默认开启混合检索；融合算法默认为 RRF。

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

**功能测试**：

```python
# 测试用例：MultiStepQueryEngine 查询变换管线构建
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.core.llms.mock import MockLLM
from llama_index.core.query_engine import MultiStepQueryEngine
from llama_index.core.query_transform import StepDecomposeQueryTransform

Settings.llm = MockLLM()
index = VectorStoreIndex.from_documents(
    [Document(text="2026 年营收增长 20%。")], embed_model=FixedEmbedding()
)

# ① 构建多步查询引擎（内部会先拆解子问题再逐步检索）
step_decompose = StepDecomposeQueryTransform(llm=Settings.llm, verbose=True)
multi_qe = MultiStepQueryEngine(
    query_engine=index.as_query_engine(), query_transform=step_decompose
)

# ② 断言：管线构建成功且可执行（MockLLM 下返回非空结果）
response = multi_qe.query("营收变化情况")
assert response is not None
print(f"✅ 查询变换测试通过：{str(response)[:30]}")
```

> 真实效果依赖 LLM 拆解质量；"检索相关但答不全"时优先尝试。

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

**功能测试**：

```python
# 测试用例：SubQuestionQueryEngine 多数据源路由
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.core.llms.mock import MockLLM
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.core.tools import QueryEngineTool, ToolMetadata

Settings.llm = MockLLM()

# ① 构建两个独立知识库索引
index_finance = VectorStoreIndex.from_documents(
    [Document(text="2026 年营收 1.2 亿元。")], embed_model=FixedEmbedding()
)
index_news = VectorStoreIndex.from_documents(
    [Document(text="公司发布新一代产品。")], embed_model=FixedEmbedding()
)

# ② 包装为带描述的查询工具（Agent 依据描述路由）
tools = [
    QueryEngineTool(
        query_engine=index_finance.as_query_engine(),
        metadata=ToolMetadata(name="财报库", description="公司财报相关"),
    ),
    QueryEngineTool(
        query_engine=index_news.as_query_engine(),
        metadata=ToolMetadata(name="新闻库", description="公司新闻相关"),
    ),
]
query_engine = SubQuestionQueryEngine.from_defaults(query_engine_tools=tools)
response = query_engine.query("业绩如何？发布了什么产品？")
assert response is not None
print(f"✅ 子问题查询测试通过：{str(response)[:40]}")
```

> 每个子问题按描述路由到对应数据源，最后汇总；适合多库对比场景。

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

**功能测试**（涉及安装的插件仅列出命令，不自动执行）：

```bash
# 交叉编码器重排需额外安装（首次运行会下载模型权重）
pip install sentence-transformers llama-index-postprocessor-sentence-transformers-rerank
```

```python
# 测试用例：LLMRerank 重排（用 MockLLM 验证管线；真实打分需真实模型）
from llama_index.core import Settings
from llama_index.core.llms.mock import MockLLM
from llama_index.core.postprocessor import LLMRerank
from llama_index.core.schema import NodeWithScore, TextNode

Settings.llm = MockLLM()

# ① 构造 5 条粗召回结果（分数由高到低）
fake_nodes = [
    NodeWithScore(node=TextNode(text=f"候选文档{i}"), score=0.9 - i * 0.1)
    for i in range(5)
]

# ② 重排：压缩到 top_n 条
reranker = LLMRerank(top_n=2)
out = reranker.postprocess_nodes(fake_nodes, query_str="测试问题")
assert len(out) <= 2
print(f"✅ 重排测试通过：5 条压缩为 {len(out)} 条")
```

> 交叉编码器方案（`SentenceTransformerRerank(model="BAAI/bge-reranker-base")`）更快、成本低，生产推荐。

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

**功能测试**：

```python
# 测试用例：ReActAgent 工具调用（MockLLM 验证链路，真实推理需函数调用模型）
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import FunctionTool
from llama_index.core.llms.mock import MockLLM

def add(a: int, b: int) -> int:
    """两数相加"""
    return a + b

# ① 构造 Agent：携带一个函数工具
agent = ReActAgent.from_tools(
    [FunctionTool.from_defaults(fn=add)], llm=MockLLM(), verbose=True
)

# ② 断言：对话链路可执行并返回响应
resp = agent.chat("1 加 2 等于多少？")
assert resp is not None
print(f"✅ Agent 测试通过：{resp}")
```

> FunctionCallingAgent 需 OpenAI 等函数调用模型；ReActAgent 兼容更广。

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

**功能测试**：

```python
# 测试用例：多智能体分工构建验证（协作效果依赖真实 LLM）
from llama_index.core.agent import FunctionCallingAgentWorker
from llama_index.core.tools import FunctionTool
from llama_index.core.llms.mock import MockLLM

def search(query: str) -> str:
    """模拟检索资料"""
    return f"关于「{query}」的资料"

def summarize(text: str) -> str:
    """模拟总结"""
    return f"总结：{text[:20]}"

# ① 两个专业 Agent：检索型 + 总结型，各自只持单一工具
research_agent = FunctionCallingAgentWorker.from_tools(
    [FunctionTool.from_defaults(fn=search)], llm=MockLLM()
).as_agent()
summary_agent = FunctionCallingAgentWorker.from_tools(
    [FunctionTool.from_defaults(fn=summarize)], llm=MockLLM()
).as_agent()

# ② 断言：两个 Agent 均可独立响应（分工协作基础）
assert research_agent.chat("竞品策略") is not None
assert summary_agent.chat("总结一下") is not None
print("✅ 多智能体构建测试通过：检索 Agent 与总结 Agent 均已就绪")
```

> 生产环境用 AgentWorkflow/编排器组合多个 Agent 实现编排者-工作者模式。

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

**功能测试**：

```python
# 测试用例：事件驱动 Workflow（纯逻辑，无需 LLM/嵌入）
import asyncio
from llama_index.core.workflow import Event, StartEvent, StopEvent, Workflow, step

class AddEvent(Event):
    """自定义事件：携带两个操作数"""
    x: int
    y: int

class CalcWorkflow(Workflow):
    @step
    async def add(self, ev: StartEvent) -> AddEvent:
        """步骤 1：接收启动事件，发出 AddEvent"""
        return AddEvent(x=ev.x, y=ev.y)

    @step
    async def multiply(self, ev: AddEvent) -> StopEvent:
        """步骤 2：消费 AddEvent，计算结果并结束"""
        return StopEvent(result=(ev.x + ev.y) * 2)

async def main():
    wf = CalcWorkflow()
    result = await wf.run(x=1, y=2)   # (1+2)*2 = 6
    assert result == 6
    print(f"✅ Workflow 测试通过：result={result}")

asyncio.run(main())
```

> 步骤通过事件解耦，支持并行/循环/条件分支；`draw_all_flows()` 可输出流程图。

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

**功能测试**：

```python
# 测试用例：FunctionTool 包装与元数据提取
from llama_index.core.tools import FunctionTool

def send_email(to: str, subject: str, body: str) -> str:
    """发送邮件（示例实现，仅返回调用记录）"""
    return f"已发送给 {to}，主题：{subject}"

tool = FunctionTool.from_defaults(fn=send_email)

# ① 断言：名称与描述（docstring）被自动提取，供 LLM 决策
assert tool.metadata.name == "send_email"
assert "发送邮件" in tool.metadata.description

# ② 断言：底层函数可直接调用
result = tool.fn("zhang@example.com", "测试", "内容")
assert "zhang@example.com" in result
print(f"✅ FunctionTool 测试通过：{result}")
```

> 工具描述决定 Agent 选工具的准确率，docstring 务必写清"何时用、怎么用"。

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

**安装验证**（仅列出命令，不自动执行）：

```bash
# 验证安装是否成功
python -c "import llama_index; print('llama-index', llama_index.__version__)"
python -c "from llama_index.core import VectorStoreIndex; print('core 导入 OK')"
```

```python
# 测试用例：安装完整性检查
import llama_index

# 断言：主包可导入且带版本号
assert hasattr(llama_index, "__version__")
print(f"✅ 安装验证通过：llama-index {llama_index.__version__}")
```

> 若 `import llama_index` 失败，说明未安装或 venv 选错；用 `python -m pip install llama-index` 修复。

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

**功能测试**（端到端全链路，无外部依赖版本）：

```python
# 测试用例：五步 RAG（临时文件 + MockLLM + FixedEmbedding，离线可跑）
import os
import tempfile
from llama_index.core import Settings, VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.llms.mock import MockLLM

# ① 准备测试文档（临时目录）
tmpdir = tempfile.mkdtemp()
with open(os.path.join(tmpdir, "test.txt"), "w", encoding="utf-8") as f:
    f.write("作者是一名 Java 后端工程师。")

# ② 全局配置：假 LLM + 固定嵌入（FixedEmbedding 定义见 3.4 节）
Settings.llm = MockLLM()
Settings.embed_model = FixedEmbedding()

# ③ 五步链路：读取 → 索引 → 引擎 → 提问 → 输出
documents = SimpleDirectoryReader(tmpdir).load_data()   # 1. 读取文档
index = VectorStoreIndex.from_documents(documents)       # 2. 切分+嵌入+建索引
query_engine = index.as_query_engine()                   # 3. 创建查询引擎
response = query_engine.query("作者职业是什么？")          # 4. 提问

# ④ 断言：有回答且有引用来源
assert response is not None
assert len(response.source_nodes) >= 1
print(f"✅ 五步 RAG 测试通过：{response}（来源 {len(response.source_nodes)} 条）")
```

> 换成真实环境：把 MockLLM 换成 `OpenAI(model="gpt-4o")`、FixedEmbedding 换成 `OpenAIEmbedding`，并设置 `OPENAI_API_KEY`。

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

**功能测试**（前置命令仅列出，不自动执行）：

```bash
# 前置准备
ollama pull llama3.2          # LLM 模型
ollama pull nomic-embed-text  # 嵌入模型
pip install llama-index-llms-ollama llama-index-embeddings-ollama
```

```python
# 测试用例：Ollama 连通性探测（需本地已启动 Ollama 服务）
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding

llm = Ollama(model="llama3.2", request_timeout=60.0)
embed_model = OllamaEmbedding(model_name="nomic-embed-text")

# ① LLM 连通性：能返回非空回复
resp = llm.complete("用一句话介绍自己")
assert resp is not None and len(str(resp)) > 0

# ② 嵌入连通性：能返回非空向量
vec = embed_model.get_text_embedding("测试")
assert len(vec) > 0
print(f"✅ Ollama 测试通过：回复={str(resp)[:20]}... 嵌入维度={len(vec)}")
```

> 报错 `Connection refused` 说明 Ollama 未启动；`model not found` 说明未执行 `ollama pull`。

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

**功能测试**（TypeScript，需 Node 18+）：

```bash
# 安装（不自动执行）
npm i llamaindex
```

```typescript
// 测试用例：TS 版 RAG 链路（./data 目录需存在至少一个 txt/pdf 文件）
import { VectorStoreIndex, SimpleDirectoryReader } from "llamaindex";

// ① 读取目录文档
const documents = await new SimpleDirectoryReader("./data").loadData();
// ② 构建索引
const index = await VectorStoreIndex.fromDocuments(documents);
// ③ 创建查询引擎并提问
const queryEngine = index.asQueryEngine();
const response = await queryEngine.query({ query: "文档的核心观点是什么？" });
// ④ 断言：返回非空结果
if (response.toString().length === 0) throw new Error("查询结果为空");
console.log(`✅ TS 查询通过：${response.toString()}`);
```

> 运行：`npx tsx test.ts`；默认使用 OpenAI 模型，需设置 `OPENAI_API_KEY`。

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

**功能测试**：

```python
# 测试用例：知识库问答（元数据过滤 + 引用来源，FixedEmbedding 见 3.4）
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.core.llms.mock import MockLLM
from llama_index.core.vector_stores import MetadataFilters, MetadataFilter

Settings.llm = MockLLM()
# ① 构造带部门元数据的制度文档
doc = Document(
    text="报销流程：先提交申请单，再审批。",
    metadata={"department": "finance", "doc_type": "制度"},
)
index = VectorStoreIndex.from_documents([doc], embed_model=FixedEmbedding())

# ② 按元数据过滤检索：只查 finance 部门
retriever = index.as_retriever(
    similarity_top_k=5,
    filters=MetadataFilters(filters=[MetadataFilter(key="department", value="finance")]),
)
nodes = retriever.retrieve("报销流程")
assert len(nodes) >= 1 and nodes[0].metadata["department"] == "finance"
print(f"✅ 知识库问答测试通过：来源={nodes[0].metadata.get('doc_type')}")
```

> 生产架构：Reader → 分块嵌入 → pgvector/Qdrant → QueryEngine，回答携带 `response.source_nodes` 引用。

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

**功能测试**：

```python
# 测试用例：PydanticOutputParser 结构化解析（无需 LLM 即可验证）
from llama_index.core.output_parsers import PydanticOutputParser
from pydantic import BaseModel

class ContractSummary(BaseModel):
    """合同摘要结构：签约方 / 金额 / 风险点"""
    parties: list[str]
    amount: float
    risks: list[str]

# ① 构造解析器
parser = PydanticOutputParser(output_cls=ContractSummary)

# ② 模拟 LLM 返回的 JSON 文本，断言解析为 Pydantic 对象
json_text = '{"parties": ["甲方", "乙方"], "amount": 100.5, "risks": ["付款延迟"]}'
obj = parser.parse(json_text)
assert obj.amount == 100.5 and len(obj.parties) == 2 and len(obj.risks) == 1
print(f"✅ 结构化输出测试通过：{obj}")
```

> 与 LLM 组合：`response = query_engine.query(..., output_cls=ContractSummary)` 直接返回对象。

[⬆ 返回顶部](#top)

### 8.3 多模态检索

<a id="s83"></a>

0.10 之后多模态检索已成熟（此前为研究级），支持**同一查询管线中同时检索文本与图片**：

- 图片经视觉模型生成描述或嵌入，纳入同一索引；
- 查询"找出含折线图的页面"可同时命中文本与图表节点；
- 配合 LlamaParse 的 OCR 能力处理图表型 PDF。

**适用**：带图文档（产品图册、设计稿、教学材料）、图表型财报。

**功能测试**：

```python
# 测试用例：多模态检索骨架（图片经视觉模型生成文本后入索引）
# 依赖：llama-index-multi-modal-llms-openai / ollama 视觉模型（按需安装，不自动执行）
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.core.llms.mock import MockLLM

Settings.llm = MockLLM()
# ① 图片由视觉模型生成描述文本（此处用占位文本模拟）
image_caption = "图表：2026 年 Q2 营收 1.2 亿元，同比 +20%。"
index = VectorStoreIndex.from_documents(
    [Document(text=image_caption, metadata={"type": "chart"})],
    embed_model=FixedEmbedding(),
)
# ② 查询命中图表描述节点
nodes = index.as_retriever(similarity_top_k=1).retrieve("营收折线图")
assert len(nodes) >= 1 and nodes[0].metadata.get("type") == "chart"
print(f"✅ 多模态检索骨架测试通过：命中图表节点（{len(nodes)} 条）")
```

> 真实实现：视觉模型（如 OpenAI gpt-4o / Ollama llava）生成图片描述 → 与文本统一入索引。

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

**功能测试**：

```python
# 测试用例：智能文档代理（文档检索 + 工具执行的组合）
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import FunctionTool, QueryEngineTool
from llama_index.core.llms.mock import MockLLM

Settings.llm = MockLLM()

# ① 合同库索引
index = VectorStoreIndex.from_documents(
    [Document(text="合同 A：与乙方签约，到期日 2026-12-31。")],
    embed_model=FixedEmbedding(),
)
query_tool = QueryEngineTool.from_defaults(
    query_engine=index.as_query_engine(),
    name="contract_db",
    description="合同库检索：查到期日、条款",
)

# ② 提醒工具：写日历/发邮件的模拟实现
def create_reminder(title: str, due_date: str) -> str:
    """创建到期提醒（模拟）"""
    return f"已创建提醒：{title} @ {due_date}"

remind_tool = FunctionTool.from_defaults(fn=create_reminder)

# ③ 组合成代理：检索合同 → 生成提醒
agent = ReActAgent.from_tools(
    [query_tool, remind_tool], llm=MockLLM(), verbose=True
)
resp = agent.chat("查询合同 A 的到期日并创建提醒")
assert resp is not None
print(f"✅ 文档代理测试通过：{resp}")
```

> 生产环境以 Workflows 编排长流程，并通过 llama-deploy 部署为服务（见 9.3）。

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

**功能测试**（涉及安装的插件仅列出命令，不自动执行）：

```bash
pip install llama-parse
```

```python
# 测试用例：LlamaParse 初始化与参数校验（真实解析需 LLAMA_CLOUD_API_KEY）
from llama_parse import LlamaParse

parser = LlamaParse(result_type="markdown")
assert parser.result_type == "markdown"
print("✅ LlamaParse 初始化通过；真实解析：parser.load_data('scanned.pdf')")
```

> 免费额度每月 10,000 积分；解析结果（Markdown）可直接进入索引管线。

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

**功能测试**（涉及安装的插件仅列出命令，不自动执行）：

```bash
pip install llama-cloud
```

```python
# 测试用例：LlamaCloud 客户端初始化（需 LLAMA_CLOUD_API_KEY）
# 真实调用：上传文档 → 托管解析/索引 → 返回可查询的索引对象
try:
    from llama_cloud import LlamaCloud  # 或新版 SDK 对应入口
    client = LlamaCloud(api_key="YOUR_API_KEY")
    assert client is not None
    print("✅ LlamaCloud 客户端初始化通过（真实调用需有效 API Key）")
except ImportError:
    print("⚠️ 未安装 llama-cloud，执行 pip install llama-cloud 后重试")
```

> LlamaCloud 为托管 SaaS；生产可将其作为"托管解析+索引"层，查询层自建。

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

**功能测试**（涉及安装的插件仅列出命令，不自动执行）：

```bash
pip install llama-deploy
```

```python
# 测试用例：llama-deploy 可用性检查（仅验证安装，不执行真实部署）
import subprocess

result = subprocess.run(
    ["llama-deploy", "--help"], capture_output=True, text=True
)
assert result.returncode == 0, "llama-deploy 未安装或不在 PATH"
print("✅ llama-deploy 已安装可用")
```

> 真实部署：把 Workflow 写入 `deployment.py`，执行 `llama-deploy deploy` 暴露 REST 服务。

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

**功能测试**：

```python
# 测试用例：SentenceWindowNodeParser 窗口化分块（Small-to-Big 基础）
from llama_index.core import Document
from llama_index.core.node_parser import SentenceWindowNodeParser

parser = SentenceWindowNodeParser.from_defaults(
    window_size=2,           # 每个节点前后各取 2 句作为上下文窗口
    window_metadata_key="window",
)
nodes = parser.get_nodes_from_documents([
    Document(text="第一句。第二句。第三句。第四句。"),
])

# 断言：每个节点都携带扩展后的窗口上下文元数据
assert len(nodes) >= 1
assert all("window" in n.metadata for n in nodes)
print(f"✅ 窗口分块测试通过：共 {len(nodes)} 个节点，均含 window 元数据")
```

> 配套检索：`SentenceWindowNodeParser` 节点配合 `MetadataReplacementPostProcessor` 在回答时展开窗口。

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

**功能测试**：

```python
# 测试用例：引用来源输出（FixedEmbedding 见 3.4）
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.core.llms.mock import MockLLM

Settings.llm = MockLLM()
doc = Document(
    text="2026 年 Q2 营收 1.2 亿元。",
    metadata={"file_name": "q2.pdf", "page_label": "3"},
)
index = VectorStoreIndex.from_documents([doc], embed_model=FixedEmbedding())
response = index.as_query_engine().query("营收多少？")

# 断言：回答携带可追溯来源（文件名 + 页码）
assert len(response.source_nodes) >= 1
src = response.source_nodes[0].metadata
assert src.get("file_name") == "q2.pdf" and src.get("page_label") == "3"
print(f"✅ 引用来源测试通过：{src.get('file_name')} 第 {src.get('page_label')} 页")
```

> 引用输出是知识库可信度的关键；元数据应避免放敏感信息。

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

**功能测试**（评估指标计算，无需 LLM）：

```python
# 测试用例：Hit Rate 与 MRR 评估指标计算
def hit_rate(ground_truths: list[str], retrieved: list[list[str]]) -> float:
    """计算 Hit Rate：每个问题只要召回集合含正确答案即命中"""
    hits = sum(1 for gt, rs in zip(ground_truths, retrieved) if gt in rs)
    return hits / len(ground_truths)

def mrr(ground_truths: list[str], retrieved: list[list[str]]) -> float:
    """计算 MRR：正确答案排名的倒数均值"""
    total = 0.0
    for gt, rs in zip(ground_truths, retrieved):
        for rank, r in enumerate(rs, start=1):
            if r == gt:
                total += 1 / rank
                break
    return total / len(ground_truths)

# 模拟评估集：3 个问题，每个取 Top-3 检索结果
ground_truths = ["A", "B", "C"]
retrieved = [["A", "X", "Y"], ["Z", "B", "W"], ["Q", "W", "C"]]

assert hit_rate(ground_truths, retrieved) == 1.0    # 全部命中
assert abs(mrr(ground_truths, retrieved) - (1 + 0.5 + 1 / 3) / 3) < 1e-6
print(f"✅ 评估指标测试通过：Hit Rate={hit_rate(ground_truths, retrieved):.2f}, MRR={mrr(ground_truths, retrieved):.3f}")
```

> 建立 50+ 条评估集持续回归，是检索质量优化的数据依据。

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
