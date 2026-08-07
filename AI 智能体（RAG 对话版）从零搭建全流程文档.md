# AI智能体（RAG对话版）从零搭建全流程文档
## 一、项目目标与范围
### 1.1 核心目标
从零搭建一套可落地的检索增强型（RAG）AI智能体，实现**多源数据采集 → 清洗切片 → 向量存储 → 语义检索 → 大模型问答 → 前端交互**的完整闭环，支持用户通过Web对话页面基于内部知识库精准提问。

### 1.2 覆盖能力
- **多源数据接入**：在线网站内容爬取、本地文档解析、业务数据库同步
- **向量知识库管理**：自动化切片、向量化、增量更新、版本管理
- **智能问答交互**：语义召回、上下文拼接、大模型生成、对话记忆
- **Web可视化页面**：对话输入、结果展示、引用来源标注

## 二、前期准备工作
### 2.1 技术栈选型
| 层级 | 技术选型 | 说明 |
| :--- | :--- | :--- |
| 开发语言 | Python 3.10+ | 适配AI生态全部组件 |
| Web框架 | FastAPI + Uvicorn | 高性能异步接口，适配对话流式输出 |
| 大模型 | 字节豆包/通义千问/OpenAI API | 负责生成回答，Embedding模型负责向量化 |
| 向量数据库 | Milvus / PGVector | 存储向量与元数据，支持相似度检索 |
| 关系型数据库 | MySQL 8.0 / PostgreSQL | 存储对话记录、知识库元数据、用户信息 |
| 文档解析 | LangChain / Unstructured / PDFPlumber | 支持PDF、Word、Excel、TXT等格式 |
| 网站爬取 | BeautifulSoup4 + Requests / Crawlee | 定向爬取公开网页内容 |
| 前端页面 | Vue 3 + Element Plus | 快速搭建对话交互界面 |
| 工程管理 | Poetry / PDM | 依赖管理与虚拟环境隔离 |

### 2.2 环境与资源准备
1. **开发环境**：Python 3.10+、Node.js 16+、Docker（用于一键部署中间件）
2. **中间件环境**（Docker快速启动）：
   - 向量数据库：Milvus Standalone 或 PostgreSQL + pgvector 插件
   - 关系型数据库：MySQL 8.0
   - 可选缓存：Redis 7.x（缓存对话上下文、高频问题）
3. **API资源**：申请大模型API Key与Embedding模型API Key，提前验证单接口可用性
4. **数据源准备**：
   - 目标网站URL清单与爬取规则
   - 本地文档目录与格式范围
   - 业务数据库的连接信息与待同步表结构

### 2.3 规范前置约定
- 命名规范：模块名统一为 `cacch_ai_xxx`，服务命名遵循 `cacch-ai-领域-service`
- 代码分层：严格遵循 `common → dao → core → service → manager → rag → web` 单向依赖
- 数据分层：数据库模型(Model)、传输对象(DTO)、业务实体分离，禁止跨层混用
- 接口规范：统一RESTful返回体，对话接口支持SSE流式输出

## 三、整体架构与工程结构
### 3.1 核心业务流程
```
用户提问 → 前端发送请求 → 提问向量化 → 向量库相似度检索 → 召回相关片段
    → 拼接Prompt模板 + 上下文 → 调用大模型生成回答 → 流式返回前端
    → 保存对话记录 → 页面展示回答与引用来源
```

数据入库流程：
```
多源数据采集 → 文本清洗 → 语义切片 → 批量向量化 → 写入向量库+元数据入库
```

### 3.2 工程目录结构
```
cacch-ai-agent/
├── pyproject.toml                # 项目依赖与配置
├── .env                          # 环境变量（API密钥、数据库连接）
├── app/
│   ├── common/                   # 公共基础模块
│   │   ├── exceptions.py         # 统一异常定义
│   │   ├── dto.py                # 通用DTO、返回体
│   │   ├── utils.py              # 工具函数
│   │   └── constants.py          # 常量、枚举
│   ├── dao/                      # 数据持久层
│   │   ├── database.py           # 关系型数据库连接与会话
│   │   ├── vector_db.py          # 向量数据库连接封装
│   │   ├── models/               # ORM数据模型
│   │   └── repositories/         # 数据访问封装
│   ├── core/                     # AI核心能力层
│   │   ├── llm/                  # 大模型适配层
│   │   │   ├── base.py           # 统一抽象接口
│   │   │   └── doubao.py         # 具体厂商实现
│   │   ├── embedding/            # 向量嵌入适配层
│   │   └── prompt/               # Prompt模板管理
│   ├── rag/                      # RAG专项模块
│   │   ├── loader/               # 数据加载器（文件/网站/数据库）
│   │   ├── splitter/             # 文本切片器
│   │   ├── pipeline/             # 入库流水线
│   │   └── retriever/            # 检索器（召回+重排）
│   ├── service/                  # 单业务域逻辑
│   │   ├── knowledge_service.py  # 知识库管理
│   │   └── chat_service.py       # 对话记录管理
│   ├── manager/                  # 业务编排层
│   │   └── chat_manager.py       # 对话全流程编排
│   └── web/                      # Web入口层
│       ├── api/                  # 接口路由
│       ├── config.py             # 配置加载
│       └── main.py               # 启动入口
└── web-frontend/                 # 前端对话页面
    ├── src/
    └── package.json
```

## 四、分步搭建执行步骤
### 阶段一：基础工程与环境初始化
**目标**：搭建可运行的基础项目骨架，连通全部中间件

#### 步骤1：初始化Python工程
1. 使用Poetry创建项目，配置Python版本与基础依赖
2. 按照上述目录结构创建包与空文件，建立分层骨架
3. 配置环境变量文件`.env`，统一管理所有密钥与连接信息
4. 封装配置加载类，支持多环境(dev/test/prod)切换

#### 步骤2：数据库与中间件连通
1. 编写关系型数据库连接类，创建ORM基类，验证数据库连接
2. 封装向量数据库连接客户端，实现集合/索引创建、基础增删改查
3. 编写数据库初始化脚本，自动创建知识库表、对话记录表、文档表等核心表
4. 封装Redis连接（可选），用于缓存与会话管理

#### 步骤3：大模型能力接入
1. 定义大模型统一抽象接口：聊天接口、流式聊天接口、Embedding接口
2. 实现对应厂商的SDK适配，封装请求参数、错误处理、重试机制
3. 编写单元测试，验证单轮对话、流式输出、向量生成功能正常

### 阶段二：多源数据接入与入库流水线
**目标**：实现三类数据源的自动采集、清洗、切片、向量化、入库

#### 步骤4：本地文件解析接入
1. 基于文档解析组件，实现PDF、Word、TXT、Markdown等格式的文本提取
2. 统一清洗规则：去除多余空白、特殊字符、页眉页脚噪声
3. 定义文档元数据规范：文件名、来源、分类、创建时间、唯一ID

#### 步骤5：在线网站内容爬取接入
1. 实现单页面爬虫：输入URL → 提取正文文本 → 清洗HTML标签
2. 支持批量URL列表爬取，配置爬取间隔、请求头、失败重试
3. 可选：实现整站深度爬取，限制域名范围与爬取深度
4. 网页元数据：URL、标题、抓取时间、所属分类

#### 步骤6：业务数据库同步接入
1. 配置目标数据库连接，支持定时同步与手动触发同步
2. 定义字段映射规则：指定哪些字段拼接为文本、哪些作为元数据
3. 支持增量同步：按更新时间字段只同步变更数据
4. 数据转换：行数据 → 结构化文本片段 → 标准化清洗

#### 步骤7：文本切片与向量化入库
1. 实现语义切片器：按固定长度+重叠字符切片，避免语义断裂
2. 批量向量化：调用Embedding接口生成向量，支持批量并发处理
3. 向量入库：将向量+元数据写入向量数据库，同步将文档元数据写入关系库
4. 封装入库流水线：统一入口 `ingest_pipeline(source_type, source_data)`，三类数据源复用同一套切片+入库逻辑
5. 实现增量更新与删除能力，保证知识库数据一致性

### 阶段三：RAG检索与对话智能体核心
**目标**：实现精准召回，完成检索+大模型生成的完整问答能力

#### 步骤8：语义检索器开发
1. 基础向量检索：用户提问向量化 → 相似度Top-K召回
2. 检索增强：支持关键词过滤、元数据过滤（按分类、来源、时间范围）
3. 可选：实现多路召回（向量检索+关键词检索）+ 重排序，提升准确率
4. 封装统一检索接口：输入查询文本+检索参数 → 返回片段列表+相似度分

#### 步骤9：Prompt工程与对话编排
1. 设计RAG问答Prompt模板：系统指令 + 检索上下文 + 用户问题
2. 实现上下文窗口管理：自动截断超长文本，保证Token在限制范围内
3. 对话记忆管理：保存历史对话，支持多轮上下文带入
4. 引用来源标注：将召回片段的来源信息随回答一并返回，支持溯源

#### 步骤10：对话全流程编排
1. 在Manager层实现完整对话链路：
   接收问题 → 检索知识库 → 组装Prompt → 调用大模型 → 返回结果 → 保存记录
2. 支持流式输出（SSE），逐字返回回答内容，提升交互体验
3. 增加异常兜底：检索无结果时返回通用回复，大模型调用失败时降级处理

### 阶段四：Web接口与前端页面
**目标**：提供可交互的对话页面，完成端到端闭环

#### 步骤11：后端API接口开发
1. 对话接口：`POST /api/chat`，支持流式与非流式两种模式
2. 知识库管理接口：文档上传、URL提交、数据库同步任务触发、知识库列表查询
3. 对话历史接口：查询会话列表、单会话详情、删除会话
4. 统一全局异常处理、参数校验、跨域配置

#### 步骤12：前端对话页面开发
1. 搭建Vue3项目，引入Element Plus组件库
2. 实现对话主界面：左侧会话列表、右侧对话消息区、底部输入框
3. 对接流式接口，实现打字机效果逐字展示回答
4. 展示引用来源：回答下方显示参考片段、来源文件/URL，支持点击跳转
5. 新增知识库管理页面：支持上传文件、提交网址、查看同步状态

### 阶段五：联调测试与效果优化
#### 步骤13：全链路联调
1. 测试三类数据源入库流程，验证向量数据与元数据正确性
2. 测试单轮问答、多轮对话、流式输出、引用展示全部功能
3. 异常场景验证：网络异常、大模型报错、空检索结果兜底

#### 步骤14：RAG效果调优
1. 优化切片策略：调整切片长度、重叠字符数，匹配业务文档特性
2. 优化检索效果：调整Top-K数量，测试不同Embedding模型
3. 优化Prompt：补充领域指令，规范回答格式，减少幻觉
4. 建立测试问题集，量化评估召回准确率与回答质量

## 五、核心代码示例
### 5.1 向量入库流水线核心逻辑
```python
# app/rag/pipeline/ingest_pipeline.py
from app.rag.loader import FileLoader, WebLoader, DatabaseLoader
from app.rag.splitter import SemanticSplitter
from app.core.embedding import EmbeddingClient
from app.dao.vector_db import VectorDB
from app.dao.repositories import KnowledgeDocRepository

class IngestPipeline:
    def __init__(self):
        self.splitter = SemanticSplitter(chunk_size=500, chunk_overlap=50)
        self.embedding = EmbeddingClient()
        self.vector_db = VectorDB()
        self.doc_repo = KnowledgeDocRepository()

    def run(self, source_type: str, source_data: dict):
        # 1. 根据来源类型加载文本
        if source_type == "file":
            loader = FileLoader()
        elif source_type == "web":
            loader = WebLoader()
        elif source_type == "database":
            loader = DatabaseLoader()
        else:
            raise ValueError(f"不支持的数据源类型: {source_type}")

        documents = loader.load(source_data)

        # 2. 文本切片
        chunks = self.splitter.split(documents)

        # 3. 批量向量化
        texts = [chunk.content for chunk in chunks]
        vectors = self.embedding.embed_batch(texts)

        # 4. 写入向量库 + 元数据入库
        self.vector_db.insert_chunks(chunks, vectors)
        self.doc_repo.batch_save_meta(chunks)
```

### 5.2 对话编排核心逻辑
```python
# app/manager/chat_manager.py
from app.rag.retriever import VectorRetriever
from app.core.llm import LLMClient
from app.core.prompt import RAG_CHAT_PROMPT
from app.service.chat_service import ChatService

class ChatManager:
    def __init__(self):
        self.retriever = VectorRetriever(top_k=4)
        self.llm = LLMClient()
        self.chat_service = ChatService()

    def chat_stream(self, session_id: str, query: str):
        # 1. 检索相关片段
        chunks = self.retriever.search(query)
        context = "\n---\n".join([c.content for c in chunks])

        # 2. 获取历史对话
        history = self.chat_service.get_history(session_id)

        # 3. 组装Prompt
        prompt = RAG_CHAT_PROMPT.format(context=context, question=query)

        # 4. 流式调用大模型
        for token in self.llm.chat_stream(prompt, history):
            yield token

        # 5. 异步保存对话记录
        self.chat_service.save_record(session_id, query, answer_full, chunks)
```

## 六、部署与上线
### 6.1 后端部署
1. 打包Python项目，使用Docker镜像封装运行环境
2. 使用Docker Compose一键编排应用、MySQL、向量数据库、Redis
3. 配置Nginx反向代理，支持HTTPS与接口限流

### 6.2 前端部署
1. 前端项目打包为静态资源
2. 部署到Nginx静态目录，配置路由与接口代理

### 6.3 监控与运维
1. 增加接口日志与错误告警
2. 监控大模型Token消耗与接口响应耗时
3. 定期备份向量库与业务数据库

## 七、后续演进方向
1. **智能体能力增强**：接入工具调用、多步骤任务规划、Agent流程编排
2. **知识库增强**：支持图片OCR、表格解析、知识图谱融合检索
3. **架构演进**：按领域拆分微服务，RAG独立为 `cacch-ai-rag-service`
4. **运营能力**：增加问答反馈、热门问题统计、知识库质量评估
5. **性能优化**：向量检索缓存、问答对缓存、批量异步入库