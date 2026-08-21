# Jinja2 提示词模板进阶指南

<a id="top"></a>

> 面向 AI 应用开发者的 Jinja2 提示词模板进阶知识，介绍它相比普通 `{{占位符}}` 替换强在哪里、核心语法、提示词工程中的典型用法与安全注意事项。

---

## 目录

- [1. 什么是 Jinja2 提示词模板](#s1)
- [2. 为什么用 Jinja2 写提示词](#s2)
- [3. 核心语法速览](#s3)
  - [3.1 四种块语法](#s31)
  - [3.2 变量、属性与赋值](#s32)
  - [3.3 常用过滤器](#s33)
  - [3.4 条件分支](#s34)
  - [3.5 循环与 loop 变量](#s35)
  - [3.6 宏：指令片段复用](#s36)
  - [3.7 模板继承：基础提示词 + 场景扩展](#s37)
  - [3.8 白空格控制](#s38)
- [4. 提示词工程中的典型用法](#s4)
  - [4.1 动态 Few-Shot 示例](#s41)
  - [4.2 条件裁剪指令](#s42)
  - [4.3 RAG 检索片段拼接](#s43)
  - [4.4 系统提示 / 用户提示拆分](#s44)
- [5. 真实生态中的应用](#s5)
- [6. 安全注意事项](#s6)
- [7. 与简单占位符替换的对比](#s7)
- [8. 配套可运行示例](#s8)

---

## 1. 什么是 Jinja2 提示词模板

<a id="s1"></a>

**Jinja2** 是 Python 生态中应用最广的模板引擎之一（Flask、Ansible、SaltStack 等均使用它），它的核心能力是：**在纯文本模板中嵌入"变量、表达式、过滤器与控制流"，渲染时动态生成文本**。

**Jinja2 提示词模板**，就是把这个引擎用于生成发给大模型的提示词。与上一节文档里的 `{{占位符}}` 简单替换不同，Jinja2 允许在提示词里写**条件分支、循环、函数调用**，让同一份模板能够根据输入动态裁剪内容。

一个最小示例：

```jinja
你是{{ role }}，请回答下面的问题：
问题：{{ question }}
{% if max_length %}请将回答控制在 {{ max_length }} 字以内。{% endif %}
```

- 传入 `role="资深 Java 架构师"`、`question="什么是微服务？"`、`max_length=100`，渲染出完整提示词；
- 不传 `max_length`，最后一行条件指令自动消失。

> 提示：Jinja2 是"渲染期求值"，它只负责**生成提示词文本**，不负责调用模型。两者是清晰的先后关系。

[⬆ 返回顶部](#top)

---

## 2. 为什么用 Jinja2 写提示词

<a id="s2"></a>

| 能力 | 简单 `{{占位符}}` | Jinja2 | 典型收益 |
|------|:---:|:---:|---------|
| 变量替换 | ✅ | ✅ | 动态填充输入 |
| 条件分支 | ❌ | ✅ | 按需裁剪指令，提示词更精简 |
| 循环 | ❌ | ✅ | 自动拼接 Few-Shot 示例、检索片段 |
| 过滤器 | ❌ | ✅ | 长度截断、列表拼接、默认值、去空白 |
| 宏 / 函数 | ❌ | ✅ | 指令片段复用，一处修改全局生效 |
| 模板继承 | ❌ | ✅ | 基础提示词 + 场景扩展，消除重复 |
| 白空格控制 | ❌ | ✅ | 渲染结果整洁，无多余空行 |
| 沙箱执行 | ❌ | ✅ | 渲染不受信任输入时更安全 |

一句话总结：**Jinja2 让提示词从"填表"升级为"程序"**——同一个模板可以适应多种输入形态，这也是各大 LLM 框架默认采用 Jinja2 的原因。

[⬆ 返回顶部](#top)

---

## 3. 核心语法速览

<a id="s3"></a>

### 3.1 四种块语法

<a id="s31"></a>

| 语法 | 作用 | 示例 |
|------|------|------|
| `{{ 表达式 }}` | 输出变量或表达式结果 | `{{ user_name }}`、`{{ 1 + 2 }}` |
| `{% 语句 %}` | 控制流（if / for / macro 等） | `{% if x > 0 %}...{% endif %}` |
| `{# 注释 #}` | 注释，渲染时删除 | `{# 这是内部注释 #}` |
| `# 行语句` | 可选行级语句（需开启） | `# for item in items` |

> 行语句需在 `Environment(line_statement_prefix="#")` 中开启；注释 `{# ... #}` 不会进入渲染结果，适合写模板维护说明。

[⬆ 返回顶部](#top)

### 3.2 变量、属性与赋值

<a id="s32"></a>

```jinja
{{ user.name }}          {# 点号取属性（dict 也能用，先查属性后查键） #}
{{ users[0] }}           {# 下标取值 #}
{{ config["model"] }}    {# 字典取值 #}

{% set greeting = "您好" %}        {# 赋值，当前作用域内可用 #}
{% set ns = namespace(total=0) %}  {# for 循环内累计计数用 namespace #}
```

变量不存在时，Jinja2 默认渲染为空字符串（配合 `default` 过滤器更稳妥）；显式 undefined 报错需要 `Environment(undefined=StrictUndefined)` 开启，适合在调试/测试阶段使用。

[⬆ 返回顶部](#top)

### 3.3 常用过滤器

<a id="s33"></a>

```jinja
{{ text | truncate(200) }}        {# 超长截断，防止提示词超限 #}
{{ items | join("、") }}          {# 列表拼成顿号分隔文本 #}
{{ lines | length }}              {# 计算长度 #}
{{ value | default("未提供", true) }}  {# 空值兜底（true 表示 None/空值也兜底） #}
{{ name | upper }}                {# 转大写 #}
{{ json_data | tojson }}          {# 对象转 JSON 字符串，常用于要求模型输出 JSON 的场景 #}
```

> 提示词渲染默认**不转义**（autoescape 默认关闭），因此注入模板的内容会原样输出——这既是便利（无需 `|safe`），也是风险（见第 6 章）。

[⬆ 返回顶部](#top)

### 3.4 条件分支

<a id="s34"></a>

```jinja
{% if answer_language %}
请用 {{ answer_language }} 回答。
{% elif need_examples %}
请给出具体示例。
{% else %}
直接回答即可。
{% endif %}
```

[⬆ 返回顶部](#top)

### 3.5 循环与 loop 变量

<a id="s35"></a>

循环是 Few-Shot 示例与 RAG 检索片段生成的利器：

```jinja
{% for item in few_shot_examples %}
示例 {{ loop.index }}：
输入：{{ item.input }}
输出：{{ item.output }}
{% endfor %}
```

循环体内自动注入 `loop` 变量，常用字段：

| 变量 | 含义 |
|------|------|
| `loop.index` | 当前序号，从 1 开始 |
| `loop.index0` | 当前序号，从 0 开始 |
| `loop.first` / `loop.last` | 是否首 / 尾元素，可做分隔处理 |
| `loop.length` | 序列长度（提前得知总数） |

[⬆ 返回顶部](#top)

### 3.6 宏：指令片段复用

<a id="s36"></a>

```jinja
{% macro format_source(source) -%}
【来源】{{ source.title }}（{{ source.url }}）
{%- endmacro %}

{{ format_source(source_a) }}
{{ format_source(source_b) }}
```

[⬆ 返回顶部](#top)

### 3.7 模板继承：基础提示词 + 场景扩展

<a id="s37"></a>

`base_prompt.j2`（基模板，定义公共结构）：

```jinja
你是 {{ role }}。
{% block content %}{% endblock %}
{% if constraints %}注意：{{ constraints }}。{% endif %}
```

`qa_prompt.j2`（子模板，只写差异部分）：

```jinja
{% extends "base_prompt.j2" %}
{% block content %}
问题：{{ question }}
{% endblock %}
```

[⬆ 返回顶部](#top)

### 3.8 白空格控制

<a id="s38"></a>

Jinja2 默认会保留语句块周围空白，导致提示词中出现多余空行。三种控制方式：

- **块边界加减号**：`{%- ... -%}`、`{{- ... -}}` 吞掉一侧空白（`-` 在左侧吞掉前面空白，在右侧吞掉后面空白）；
- **环境参数**：`trim_blocks=True`（语句后换行被吞）、`lstrip_blocks=True`（语句前空白被吞）；
- **两者配合**：生产环境建议同时开启 `trim_blocks` + `lstrip_blocks`，模板可写得更规整。

对比示例：

```jinja
{# 默认渲染：每个语句块前后留空行 #}
{% for item in items %}
- {{ item }}
{% endfor %}

{# 加减号：输出紧凑无空行 #}
{% for item in items -%}
- {{ item }}
{%- endfor %}
```

[⬆ 返回顶部](#top)

---

## 4. 提示词工程中的典型用法

<a id="s4"></a>

### 4.1 动态 Few-Shot 示例

<a id="s41"></a>

用一个 `examples` 列表，循环生成任意数量的示例块：

```jinja
请根据以下示例完成同样的分类任务。
{% for ex in examples %}
输入：{{ ex.input }}
输出：{{ ex.label }}
{% endfor %}
输入：{{ real_input }}
输出：
```

[⬆ 返回顶部](#top)

### 4.2 条件裁剪指令

<a id="s42"></a>

同一份模板同时服务"简洁版"与"详细版"：

```jinja
{% if detail_level == "detailed" %}
请分步说明推理过程，并给出正反两面论证。
{% else %}
直接给出结论。
{% endif %}
```

[⬆ 返回顶部](#top)

### 4.3 RAG 检索片段拼接

<a id="s43"></a>

检索结果数量不定，用循环 + 长度控制：

```jinja
请仅依据以下资料回答，不要编造：
{% for chunk in retrieved_chunks[:3] %}
[片段 {{ loop.index }}] {{ chunk | truncate(500) }}
{% endfor %}
问题：{{ question }}
```

[⬆ 返回顶部](#top)

### 4.4 系统提示 / 用户提示拆分

<a id="s44"></a>

把固定角色指令放在系统提示，动态内容放用户提示（大模型对 system 与 user 分段更敏感）：

```jinja
{# system.j2：固定角色与规则 #}
你是 {{ role }}。你只依据给定资料回答，不要编造。

{# user.j2：每次变化的业务内容 #}
问题：{{ question }}
资料：{{ context }}
```

```python
messages = [
    {"role": "system", "content": system_template.render(role="知识库助手")},
    {"role": "user", "content": user_template.render(question=q, context=ctx)},
]
```

[⬆ 返回顶部](#top)

---

## 5. 真实生态中的应用

<a id="s5"></a>

| 项目 | 用在哪里 |
|------|---------|
| **Hugging Face / vLLM** | 模型的 `chat_template` 即 Jinja2 模板，负责把 messages 列表渲染成模型输入格式（`<|im_start|>`、`<|user|>` 等） |
| **LlamaIndex** | 大量内置提示词模板基于 Jinja2，支持自定义 `PromptTemplate` |
| **LangChain** | `PromptTemplate(template=..., template_format="jinja2")` 直接支持 |
| **Ollama / 各类网关** | 常见 OpenAI 兼容网关内部用 Jinja2 做消息格式转换 |

这也是为什么理解 Jinja2 对"调试模型输出格式异常"特别有用——很多乱码/多余标记问题，根源就在 chat_template 渲染。

[⬆ 返回顶部](#top)

---

## 6. 安全注意事项

<a id="s6"></a>

提示词是**不可信输入注入模板的入口**，需要注意：

1. **不要拼接用户输入到模板本身**：用户输入永远作为"数据"传入渲染，而不是作为"模板代码"；否则用户可写入 `{% ... %}` 控制你的提示词（提示注入）。
   ```python
   # 错误：用户输入被当作模板代码解析
   Template("请忽略" + user_input).render()

   # 正确：用户输入只作为数据传入
   Template("请回答：{{ question }}").render(question=user_input)
   ```
2. **沙箱渲染不可信模板**：如果模板本身来自外部（如模型仓库下载的 chat_template），用 `SandboxedEnvironment` 渲染，禁用任意 Python 属性访问：
   ```python
   from jinja2.sandbox import SandboxedEnvironment
   env = SandboxedEnvironment(trim_blocks=True, lstrip_blocks=True)
   ```
3. **控制上下文暴露面**：只向模板传入渲染所需的最小变量集，不要塞入 `os`、`open` 等危险对象。
4. **长度与内容校验**：`truncate` 截断防止提示词超限；对用户输入做换行/分隔符转义，防止破坏指令结构。
5. **渲染结果抽查**：关键路径记录渲染后的提示词（脱敏），便于排查格式异常与注入攻击。

[⬆ 返回顶部](#top)

---

## 7. 与简单占位符替换的对比

<a id="s7"></a>

| 维度 | 上一节的 `render()`（正则替换） | Jinja2 |
|------|--------------------------------|--------|
| 实现依赖 | 标准库即可 | 需安装 `jinja2` 包 |
| 变量替换 | ✅ | ✅ |
| 条件 / 循环 | ❌ 需在 Python 侧手工拼 | ✅ 模板内完成 |
| 过滤器 / 默认值 | ❌ | ✅ |
| 复用（宏 / 继承） | ❌ | ✅ |
| 渲染安全性 | 需自行转义 | 沙箱 + 可控上下文 |
| 适用场景 | 简单固定结构的模板 | 复杂、多形态、需动态裁剪的提示词 |

**选型建议**：模板结构固定、变量少 → 简单替换足够；模板需要分支、循环、复用或来自外部 → 用 Jinja2。

[⬆ 返回顶部](#top)

---

## 8. 配套可运行示例

<a id="s8"></a>

本目录下的 `jinja2_prompt_template.py` 演示了本节全部核心语法，运行方式：

```bash
# 使用已安装 jinja2 的隔离环境
C:/Users/Administrator/.workbuddy/binaries/python/envs/default/Scripts/python.exe \
    practice/jinja2_prompt_template.py
```

示例覆盖：基础渲染、过滤器、if/elif/else、for 循环生成 Few-Shot、宏复用、模板继承（基模板 + 子模板）、白空格控制、沙箱渲染与 RAG 提示词实战。

实际项目中模板通常以文件形式管理，用 `FileSystemLoader` 加载：

```python
from jinja2 import Environment, FileSystemLoader

env = Environment(
    loader=FileSystemLoader("practice/"),   # 模板目录
    trim_blocks=True,
    lstrip_blocks=True,
)
tpl = env.get_template("qa_prompt.j2")      # 支持 extends / include
print(tpl.render(role="知识库助手", question="报销单多久到账？"))
```

> 工程建议：为模板中的每个变量维护一份"变量契约"（名称 / 类型 / 必填 / 示例），并与模板一起纳入 Git 版本管理。

[⬆ 返回顶部](#top)
