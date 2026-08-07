# 05 · Agent 工具安全与 HITL 基线

> **执行状态**：⬜ 未开始 | 🟦 进行中 | ✅ 已完成 | ⏸️ 暂停 | ❌ 阻塞  
> **当前状态**：⬜  
> **适用范围**：平台硬约束（实现可在 P3，**标准现在就定**）  
> **负责人**：_（选填）_  
> **更新日期**：_（选填）_  
> **阻塞项**：无

### 本章验收
- [ ] 团队确认：未满足本文基线的 Agent **不得**对生产开放写操作工具
- [ ] 工具分级（读/写/高危）与默认 HITL 策略已书面确认
- [ ] 审计字段与拒绝原因码已约定
- [ ] [agent-orchestration](../agent-orchestration/README.md) 已链接本文为安全前置

> 本章是**安全基线**，不是完整 Agent 实现手册。编排细节仍在 Agent 能力域补充。

---

## 1. 为什么必须提前定

Agent 一旦具备「调 API / 改数据」能力，风险从「答错」升级为「做错」。  
主流平台均要求：**工具白名单、参数校验、权限沙箱、审计、人工确认（HITL）**。

即使 Agent 域排在 P3，**不允许「先上线再补安全」**。

---

## 2. 工具注册与白名单

### 2.1 注册信息（每个工具必填）

| 字段 | 说明 |
| :--- | :--- |
| tool_id | 稳定 ID，如 `kb_search`、`order_query` |
| name / description | 给模型看的说明（需防注入：描述由平台管控，不由终端用户随意改生产配置） |
| risk_level | `read` / `write` / `critical` |
| input_schema | JSON Schema，执行前校验 |
| timeout_ms | 单次调用超时 |
| allowed_apps | 可挂载的 App 列表（或标签） |
| require_hitl | 是否默认需要人工确认 |
| executor | 内置函数 / HTTP / RPC |

### 2.2 白名单原则

- 模型**只能**调用当前 App bindings 内的工具  
- 禁止「任意 URL 转发」类万能 HTTP 工具进入生产（若需要，必须 URL 允许列表 + 方法限制）  
- 新工具上线走评审：风险等级、HITL、审计  

---

## 3. 参数校验与沙箱

| 控制点 | 要求 |
| :--- | :--- |
| Schema 校验 | 缺字段/类型错误 → 拒绝执行，回传模型可理解的错误 |
| 范围约束 | ID、金额、时间窗等业务边界在执行器内二次校验 |
| 权限 | 以**用户身份**执行（user_id / token），禁止升权为服务超级账号乱调 |
| 网络 | 出站域名白名单；禁内网任意穿透（除非专批） |
| 机密 | 工具不得回传密钥；日志脱敏 |
| 幂等 | 写操作带 idempotency_key，防重试双写 |

---

## 4. 风险分级与默认 HITL

| risk_level | 示例 | 默认策略 |
| :--- | :--- | :--- |
| **read** | 知识库检索、订单查询 | 可自动执行；审计留痕 |
| **write** | 创建工单、更新状态 | **HITL：展示参数，人确认后再执行** |
| **critical** | 付款、删数、权限变更 | **强制 HITL + 双人/管理员策略（可配置）**；默认可禁用 |

HITL 最小交互：

```text
Agent 提议调用 tool(args)
  → 前端展示：工具名、参数摘要、风险等级
  → 用户：批准 / 拒绝 / 修改参数（若允许）
  → 批准后执行 → 结果回灌 Agent 继续
```

超时未确认：任务挂起或失败，不得默认批准。

---

## 5. 将 RAG 检索工具化时的约束

`kb_search` 通常为 `read`：

- 必须传入 App 允许的 `kb_ids`，并套用 [04 ACL](./04-数据面约定-ACL与对象存储.md)  
- 检索结果进 Prompt 前做长度与敏感截断  
- 不得通过工具参数绕过 ACL（忽略用户身份查全库）  

---

## 6. 审计与拒绝码

每次工具调用记录：

`request_id, app_id, user_id, tool_id, risk_level, args_digest, hitl_decision, status, latency_ms, error_code`

建议错误码：

| code | 含义 |
| :--- | :--- |
| TOOL_NOT_ALLOWED | 非白名单或未挂载 |
| TOOL_SCHEMA_INVALID | 参数不合规 |
| TOOL_HITL_REQUIRED | 等待人工确认 |
| TOOL_HITL_DENIED | 人工拒绝 |
| TOOL_TIMEOUT | 超时 |
| TOOL_FORBIDDEN | 权限不足 |

---

## 7. 上线门禁（Agent 写能力）

生产开放 `write` / `critical` 前必须全部满足：

- [ ] 工具均已注册且风险分级正确  
- [ ] HITL 链路在预发验证通过  
- [ ] 审计可查询到试跑记录  
- [ ] 出站与权限沙箱已配置  
- [ ] 回滚开关：可一键禁用某工具或整 App Agent  

未达标时：Agent **仅允许 read 工具**（含 kb_search）。

---

## 相关文档

- 能力域规划：[../agent-orchestration/README.md](../agent-orchestration/README.md)  
- App 挂载工具：[02-应用与能力挂载模型.md](./02-应用与能力挂载模型.md)  
- 观测门禁：[06-可观测评测与反馈门禁.md](./06-可观测评测与反馈门禁.md)  
