# CACCH AI Platform 文档中心

`cacch-ai-platform` 是企业级 **AI 能力平台**，不只做知识库问答，而是沉淀可复用的模型接入、编排、数据与运营能力，支撑多类 AI 业务场景。

## 平台一句话

统一接入大模型与向量能力，按业务装配多种智能体/应用：**知识问答、通用助手、Agent 编排、内容生成、文档智能等**。

## 能力地图（总览）

| 能力域 | 说明 | 文档状态 | 入口 |
| :--- | :--- | :---: | :--- |
| **平台共性** | 定位、共享底座、App 挂载、网关治理、数据面 ACL/OSS、Agent 安全、观测评测门禁 | ✅ 可执行 | [platform/](./platform/README.md) |
| **RAG 知识问答** | 多源入库、检索增强对话、引用溯源（首期落地重点） | ✅ 可执行 | [rag-agent/](./rag-agent/README.md) |
| **通用对话助手** | 无知识库/弱知识库的多轮对话、角色与系统指令 | 📋 规划 | [chat-assistant/](./chat-assistant/README.md) |
| **Agent 编排** | 工具调用、多步骤任务、流程编排 | 📋 规划 | [agent-orchestration/](./agent-orchestration/README.md) |
| **内容生成** | 文案/报告/摘要/改写等生成类场景 | 📋 规划 | [content-generation/](./content-generation/README.md) |
| **文档智能** | 抽取、分类、比对、结构化输出（可与 RAG 共用解析） | 📋 规划 | [doc-intelligence/](./doc-intelligence/README.md) |

> 图例：✅ 文档可照着落地 · 📋 已定方向、分册待充实

## 推荐阅读顺序

1. [平台定位与能力地图](./platform/00-平台定位与能力地图.md) — 先建立「平台 ≠ 单一问答」共识  
2. [共享基础能力](./platform/01-共享基础能力.md) — 各业务域必须复用的底座  
3. 平台治理补齐（与主流对齐）：[02](./platform/02-应用与能力挂载模型.md) → [03](./platform/03-LLM网关治理.md) → [04](./platform/04-数据面约定-ACL与对象存储.md) → [05](./platform/05-Agent工具安全与HITL基线.md) → [06](./platform/06-可观测评测与反馈门禁.md)  
4. 按当前迭代选择能力域文档（首期建议 [rag-agent](./rag-agent/README.md)）  

## 仓库与命名

- 仓库：`cacch-ai-platform`
- 源码根包：`app/`；发布包名：`cacch_ai_xxx`
- 服务名：`cacch-ai-领域-service`（如 `cacch-ai-rag-service`、`cacch-ai-agent-service`）
- 原则：**共享底座一次建设，业务能力按域扩展**，避免每个场景复制一套 LLM/鉴权/日志

## 与「智能体」的关系

| 概念 | 在本平台中的含义 |
| :--- | :--- |
| AI 平台 | 多能力共存的工程与产品载体 |
| 能力域 | RAG / 助手 / Agent / 生成 / 文档智能等可独立迭代的模块 |
| 智能体应用 | 某一能力域上的具体产品形态（对话页、API、批任务等） |

RAG 对话是**首期重点能力域**，不是平台的全部范围。

## 维护约定

- 平台级约定写在 `docs/platform/`  
- 某能力域的搭建步骤写在对应子目录  
- 新增 AI 需求：先更新能力地图，再开子目录与 README，避免继续堆进 RAG 分册  
