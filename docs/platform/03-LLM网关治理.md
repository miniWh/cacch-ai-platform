# 03 · LLM 网关治理

> **执行状态**：⬜ 未开始 | 🟦 进行中 | ✅ 已完成 | ⏸️ 暂停 | ❌ 阻塞  
> **当前状态**：⬜  
> **适用范围**：平台共用（所有调用大模型的能力域）  
> **负责人**：_（选填）_  
> **更新日期**：_（选填）_  
> **阻塞项**：无

### 本章验收
- [ ] 已区分「SDK 适配」与「网关治理」两层职责
- [ ] model_profile（模型配置档）字段已定
- [ ] 限流 / 超时 / 重试 / 降级策略有书面默认值
- [ ] 审计字段能随请求贯通到日志或表
- [ ] 内容安全策略（过/不过/仅记录）已拍板

---

## 1. 两层职责（避免只做 SDK 封装）

| 层 | 职责 | 例子 |
| :--- | :--- | :--- |
| **Provider Adapter** | 对接豆包/千问/OpenAI 等协议差异 | 签名、流式解析、错误码映射 |
| **LLM Gateway** | 面向平台的治理与路由 | 选模型、限流、降级、熔断、审计、配额 |

业务域（RAG/Agent/生成）**只依赖 Gateway 接口**，不直接 new 厂商 SDK。

```text
App / Manager
    → LLM Gateway（profile、限流、降级、审计）
        → Provider Adapter（doubao / qwen / openai）
```

---

## 2. Model Profile（模型配置档）

| 字段 | 说明 |
| :--- | :--- |
| profile_id | 如 `default_chat`、`rag_chat`、`agent_chat`、`embed_default` |
| provider | doubao / qwen / openai / ... |
| model | 具体模型名 |
| base_url | 可选 |
| temperature / max_tokens | 默认生成参数 |
| timeout_ms | 读超时 |
| retry | 次数与退避 |
| fallback_profile_id | 失败时切换的备用档 |
| rpm / tpm 限额 | 每分钟请求/Token（可按 app 覆盖） |
| enable_content_safety | 是否过审 |

Embedding 使用独立 profile（维度变更规则见 RAG 域）。

---

## 3. 路由

| 策略 | 说明 | 建议阶段 |
| :--- | :--- | :---: |
| **静态绑定** | App / 能力域写死 profile_id | MVP ✅ |
| **按场景路由** | rag_chat → A 模型；generation → B 模型 | P1 |
| **按租户/应用覆盖** | 企业版用私有部署模型 | P2 |
| **负载/成本路由** | 低优先级走便宜模型 | P3 可选 |

路由输入建议带：`app_id`、`capability`、`user_id`、`priority`。

---

## 4. 限流、超时、重试、熔断、降级

### 4.1 默认策略（可改，但必须有默认）

| 项 | 默认建议 |
| :--- | :--- |
| 读超时 | 60s（流式：首包 15s + 空闲 30s，按实现微调） |
| 重试 | 幂等读请求最多 2 次；指数退避；**写类工具调用不盲目重试** |
| 限流 | 按 `app_id` + 全局两级；超限返回明确业务码 |
| 熔断 | 某 provider 连续错误率超阈值 → 开路 N 秒 |
| 降级 | 切 `fallback_profile`；若无备用 → 返回可展示错误（禁止空响应） |

### 4.2 流式特殊要求

- 已向下游开始推 SSE 后，降级策略受限：优先结束当前流并 `error` 事件，避免「半截答案无说明」  
- Gateway 层统一注入 `request_id`，前后端可对账  

---

## 5. 配额与成本

| 维度 | 用途 |
| :--- | :--- |
| 按 app | 防止单一应用打爆额度 |
| 按 user（可选） | 防刷 |
| 按日/月 Token | 预算告警 |

最低实现：日志统计 Token；进阶：落库日聚合 + 告警。  
计费账单可后置，但 **Token 计量字段要从 Day 1 打点**。

---

## 6. 审计字段（请求贯通）

每次 LLM / Embedding 调用建议具备：

| 字段 | 说明 |
| :--- | :--- |
| request_id | 全链路 ID |
| app_id / session_id | 来源应用与会话 |
| user_id | 调用者（可匿名哈希） |
| profile_id / provider / model | 实际命中模型 |
| capability | rag / agent / generation / ... |
| prompt_tokens / completion_tokens | 用量 |
| latency_ms | 耗时 |
| status / error_code | 成功或错误分类 |
| safety_result | 内容安全结果（若启用） |

禁止在审计日志中落完整 API Key；Prompt 原文按合规策略脱敏或采样存储。

---

## 7. 内容安全

| 模式 | 说明 | 建议 |
| :--- | :--- | :--- |
| off | 不调用安审 | 仅本地开发 |
| log_only | 调用但只记录 | 试运行 |
| enforce | 拦截违规输入/输出 | 生产默认方向 |

输入审与输出审可分开；Agent 工具参数在执行前额外校验（见 05）。

---

## 8. Gateway 对外接口（示意）

```text
chat(messages, profile_id, meta) -> ChatResult
chat_stream(messages, profile_id, meta) -> Iterator[Token]
embed_batch(texts, profile_id, meta) -> List[Vector]
```

`meta` 至少含：`request_id, app_id, user_id, capability`。

---

## 下一步

- 数据面与文件/ACL：[04-数据面约定-ACL与对象存储.md](./04-数据面约定-ACL与对象存储.md)  
- 观测与评测门禁会消费本章审计字段：[06-可观测评测与反馈门禁.md](./06-可观测评测与反馈门禁.md)  
