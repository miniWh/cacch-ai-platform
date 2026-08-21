"""
提示词模板（Prompt Templates）可运行代码示例
================================================

对应文档：practice/提示词模板.md
运行方式：python practice/prompt_template_examples.py
依赖：仅使用 Python 标准库，无需安装第三方包

文档中介绍的每个模板框架（RTF / CRISPE / CO-STAR / 角色 / Few-Shot / 思维链）
以及 4 个实战模板（内容总结 / SQL 生成 / RAG 问答 / 代码审查），
在下方均有对应的函数实现与调用演示。

其中 call_llm() 会真正发起 HTTP 网络请求，调用 OpenAI 兼容的 chat completions
接口；接口地址与密钥通过环境变量 LLM_BASE_URL / LLM_API_KEY / LLM_MODEL
传入，未配置时自动降级为本地模拟输出，保证脚本无网络、无密钥也能运行。
"""

import json
import os
import re
import urllib.error
import urllib.request

# =====================================================================
# 一、通用模板渲染器（对应文档第 5 章：模板变量与占位符）
# =====================================================================

# 匹配双花括号占位符，如 {{role}}、{{user_name}}
PLACEHOLDER_PATTERN = re.compile(r"\{\{(\w+)\}\}")


def render(template: str, **variables) -> str:
    """
    将模板中的 {{占位符}} 替换为实际变量值。

    :param template:  含 {{占位符}} 的提示词模板
    :param variables: 以关键字参数传入的变量值
    :return:          渲染后的完整提示词
    :raises KeyError: 有必填占位符未提供变量时，抛出异常（变量先校验，见第 7 章最佳实践第 6 条）
    """
    # 第一步：校验模板中所有占位符是否都有对应变量，缺一不可
    required = set(PLACEHOLDER_PATTERN.findall(template))
    provided = set(variables.keys())
    missing = required - provided
    if missing:
        raise KeyError(f"模板缺少必填变量: {sorted(missing)}")

    # 第二步：执行替换（逐个替换，避免 str.format 与 JSON 花括号冲突）
    def _replace(match: re.Match) -> str:
        return str(variables[match.group(1)])

    return PLACEHOLDER_PATTERN.sub(_replace, template)


# =====================================================================
# 二、经典模板框架（对应文档第 4 章）
# =====================================================================

def rtf_prompt(role: str, task: str, output_format: str) -> str:
    """
    4.3 RTF 三段式：最简洁的通用模板
    Role（角色）+ Task（任务）+ Format（格式）
    """
    template = (
        "Role（角色）：你是{{role}}\n"
        "Task（任务）：请{{task}}\n"
        "Format（格式）：请以{{output_format}}输出"
    )
    return render(template, role=role, task=task, output_format=output_format)


def crispe_prompt(role: str, background: str, task: str,
                  style: str, n: int) -> str:
    """
    4.1 CRISPE 框架：
    Capacity(角色) / Insight(背景) / Statement(任务)
    Personality(风格) / Experiment(多方案实验)
    """
    template = (
        "扮演{{role}}。\n"
        "背景：{{background}}。\n"
        "任务：{{task}}。\n"
        "风格：{{style}}。\n"
        "请给出{{n}}种方案，并比较各自的优缺点，最后推荐一个。"
    )
    return render(template, role=role, background=background,
                  task=task, style=style, n=n)


def costar_prompt(background: str, objective: str, style: str,
                  tone: str, audience: str, response: str) -> str:
    """
    4.2 CO-STAR 框架（新加坡 GovTech 提出）：
    Context(背景) / Objective(目标) / Style(风格)
    Tone(语气) / Audience(受众) / Response(输出格式)
    """
    template = (
        "# CONTEXT\n{{background}}\n\n"
        "# OBJECTIVE\n{{objective}}\n\n"
        "# STYLE\n{{style}}\n\n"
        "# TONE\n{{tone}}\n\n"
        "# AUDIENCE\n{{audience}}\n\n"
        "# RESPONSE\n{{response}}"
    )
    return render(template, background=background, objective=objective,
                  style=style, tone=tone, audience=audience, response=response)


def role_prompt(profession: str, years: str, domain: str,
                task: str, constraints: str) -> str:
    """4.4 角色模板：通过角色设定提升输出专业性"""
    template = (
        "你是一位资深的{{profession}}，拥有{{years}}年{{domain}}领域经验。\n"
        "现在请从专业角度出发，{{task}}。\n"
        "在回答时请注意：{{constraints}}。"
    )
    return render(template, profession=profession, years=years,
                  domain=domain, task=task, constraints=constraints)


def few_shot_prompt(examples: list[tuple[str, str]], real_input: str) -> str:
    """
    4.5 Few-Shot 示例模板：
    通过 1~3 组「输入 → 期望输出」样例示范响应模式，适合分类/抽取/改写任务。

    :param examples: [(输入1, 输出1), (输入2, 输出2), ...]
    :param real_input: 本次真正待处理的输入
    """
    # 动态拼接示例块（示例数量建议控制在 1~3 个，见第 7 章最佳实践第 4 条）
    example_blocks = []
    for i, (inp, out) in enumerate(examples, start=1):
        example_blocks.append(f"示例 {i}：\n输入：{inp}\n输出：{out}")

    template = (
        "请根据以下示例完成同样的任务。\n\n"
        "{{examples}}\n\n"
        "现在轮到你了：\n"
        "输入：{{real_input}}\n"
        "输出："
    )
    return render(template,
                  examples="\n\n".join(example_blocks),
                  real_input=real_input)


def cot_prompt(question: str) -> str:
    """4.6 思维链（Chain-of-Thought）模板：引导模型逐步推理，提升复杂任务正确率"""
    template = (
        "请逐步思考并回答以下问题：\n"
        "问题：{{question}}\n\n"
        "步骤要求：\n"
        "1. 先列出已知条件；\n"
        "2. 分析问题与已知条件的关系；\n"
        "3. 分步推导得出结论；\n"
        "4. 最后用一句话总结答案。"
    )
    return render(template, question=question)


# =====================================================================
# 三、实战场景模板（对应文档第 6 章）
# =====================================================================

def summarize_prompt(document: str) -> str:
    """示例 A：内容总结模板"""
    template = (
        "你是一位资深编辑，擅长提炼信息核心。\n\n"
        "请阅读以下材料，输出一份 200 字以内的中文摘要。\n\n"
        "【材料】\n{{document}}\n\n"
        "【要求】\n"
        "- 保留关键数据与结论；\n"
        "- 不添加材料之外的信息；\n"
        "- 使用 Markdown 段落格式，不要使用列表。"
    )
    return render(template, document=document)


def sql_prompt(schema: str, requirement: str) -> str:
    """示例 B：SQL 生成模板（表结构与业务需求分离，用【】分隔符区分指令与数据）"""
    template = (
        "你是精通 PostgreSQL 的数据库专家。\n\n"
        "【表结构】\n{{schema}}\n\n"
        "【业务需求】\n{{requirement}}\n\n"
        "请生成一条满足需求的 SQL 查询语句，并：\n"
        "- 只输出 SQL，不要额外解释；\n"
        "- 使用合适的索引列过滤；\n"
        "- 如需多表关联，请说明关联字段。"
    )
    return render(template, schema=schema, requirement=requirement)


def rag_prompt(retrieved_context: str, question: str) -> str:
    """
    示例 C：RAG 问答模板（生产常用）
    关键点：负面约束明确——资料中没有就直说，禁止编造（防幻觉）
    """
    template = (
        "你是企业知识库助手。请仅基于以下资料回答用户问题。\n"
        "如果资料中没有相关信息，请直接回答“资料库中未找到相关内容”，不要编造。\n\n"
        "【资料】\n{{retrieved_context}}\n\n"
        "【问题】\n{{question}}\n\n"
        "【要求】\n"
        "回答时标注信息来源片段，控制在 150 字以内。"
    )
    return render(template, retrieved_context=retrieved_context, question=question)


def code_review_prompt(language: str, code: str) -> str:
    """示例 D：代码审查模板"""
    template = (
        "你是一位经验丰富的 {{language}} 开发工程师。\n\n"
        "请审查以下代码，输出审查意见：\n"
        "1. 严重问题（Bug / 安全隐患）；\n"
        "2. 潜在风险（性能 / 并发 / 边界条件）；\n"
        "3. 可读性建议。\n\n"
        "【代码】\n{{code}}"
    )
    return render(template, language=language, code=code)


# =====================================================================
# 四、接入真实大模型 API（真正发起 HTTP 网络请求）
# =====================================================================

def call_llm(prompt: str, system: str = "你是一位资深编辑。",
             temperature: float = 0.2) -> str:
    """
    真正发起 HTTP 网络请求，调用 OpenAI 兼容的 chat completions 接口。

    使用 Python 标准库 urllib，无需安装 openai / requests 等第三方包。

    配置（通过环境变量传入，避免在代码中硬编码密钥）：
      LLM_BASE_URL  接口根地址，如 https://api.deepseek.com/v1
      LLM_API_KEY   API 密钥，如 sk-xxxx
      LLM_MODEL     模型名，如 deepseek-chat（未设置时默认 gpt-3.5-turbo）

    未配置 LLM_BASE_URL / LLM_API_KEY 时，自动降级为本地模拟输出，
    保证脚本无网络、无密钥也能运行。

    :param prompt:      渲染后的用户提示词（user 消息内容）
    :param system:      固定的角色指令（system 消息内容）
    :param temperature: 采样温度，抽取/总结类任务建议 0~0.3（见文档第 7 章第 8 条）
    :return:            模型回复文本；失败时返回带前缀的错误信息
    """
    base_url = os.environ.get("LLM_BASE_URL", "").strip()
    api_key = os.environ.get("LLM_API_KEY", "").strip()
    model = os.environ.get("LLM_MODEL", "gpt-3.5-turbo").strip()

    # 未配置密钥/地址：降级为本地模拟，并提示如何配置
    if not base_url or not api_key:
        return (
            "[本地模拟模式] 未配置环境变量 LLM_BASE_URL / LLM_API_KEY，已跳过网络请求。\n"
            "配置示例（bash / Git Bash）：\n"
            "  export LLM_BASE_URL=https://api.deepseek.com/v1\n"
            "  export LLM_API_KEY=sk-xxxx\n"
            "  export LLM_MODEL=deepseek-chat\n"
            "配置示例（PowerShell）：\n"
            "  $env:LLM_BASE_URL='https://api.deepseek.com/v1'\n"
            "  $env:LLM_API_KEY='sk-xxxx'\n"
            "  $env:LLM_MODEL='deepseek-chat'"
        )

    # 拼接 chat completions 接口地址（兼容地址末尾是否带斜杠）
    url = base_url.rstrip("/") + "/chat/completions"

    # 组装请求体：system 放固定角色指令，user 放渲染后的动态内容
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    # 设置请求头：JSON 内容类型 + Bearer Token 鉴权
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {api_key}",
    }
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    # 真正发起网络请求，并分类处理各类异常（网络超时、HTTP 错误、解析失败）
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
        result = json.loads(body)
        # 提取模型回复文本
        return result["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        # 服务端返回非 2xx，读取错误详情便于排查
        err_body = e.read().decode("utf-8", errors="replace")
        return f"[HTTP {e.code}] {err_body}"
    except urllib.error.URLError as e:
        # 网络层错误（DNS 解析、连接超时、SSL 握手等）
        return f"[网络错误] {e.reason}"
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        # 响应结构不符合预期
        return f"[解析失败] {type(e).__name__}: {e}"


# =====================================================================
# 五、演示入口：逐个框架/场景输出渲染结果
# =====================================================================

def _banner(title: str) -> None:
    """打印分节标题，便于阅读控制台输出"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def main() -> None:
    # ---------- RTF 三段式 ----------
    _banner("4.3 RTF 三段式模板")
    print(rtf_prompt(
        role="资深 Java 架构师",
        task="评审以下微服务拆分方案的合理性",
        output_format="Markdown 表格",
    ))

    # ---------- CRISPE ----------
    _banner("4.1 CRISPE 模板")
    print(crispe_prompt(
        role="产品顾问",
        background="公司计划上线内部知识库问答功能，预算有限，团队 5 人",
        task="设计技术选型方案",
        style="务实、面向工程落地",
        n=3,
    ))

    # ---------- CO-STAR ----------
    _banner("4.2 CO-STAR 模板")
    print(costar_prompt(
        background="公司新采购了一批检测设备，需要向全员发布使用通知",
        objective="撰写一份设备使用规范通知",
        style="正式公文",
        tone="严谨、专业",
        audience="全体实验室员工",
        response="300 字以内的 Markdown 段落",
    ))

    # ---------- 角色模板 ----------
    _banner("4.4 角色模板")
    print(role_prompt(
        profession="数据库管理员",
        years="10",
        domain="PostgreSQL 性能调优",
        task="分析慢 SQL 的可能原因",
        constraints="不要编造不存在的参数，给出的建议需注明适用版本",
    ))

    # ---------- Few-Shot 示例模板 ----------
    _banner("4.5 Few-Shot 示例模板（情感分类任务）")
    print(few_shot_prompt(
        examples=[
            ("这家店的响应速度太慢了，等了三天才发货。", "负面"),
            ("包装很结实，客服也很耐心，五星好评！", "正面"),
        ],
        real_input="产品不错，就是价格稍微贵了一点。",
    ))

    # ---------- 思维链模板 ----------
    _banner("4.6 思维链（CoT）模板")
    print(cot_prompt(
        question="某农药厂 3 月产量 1200 吨，4 月比 3 月增产 15%，5 月比 4 月减产 10%，5 月产量是多少吨？"
    ))

    # ---------- 实战 A：内容总结 ----------
    _banner("实战示例 A：内容总结模板")
    print(summarize_prompt(
        document="2026 年第二季度，公司华东区销售额达 3200 万元，同比增长 18%，"
                 "主要增长来自新客户渠道；但华南区销售额下滑 6%，原因待查。"
    ))

    # ---------- 实战 B：SQL 生成 ----------
    _banner("实战示例 B：SQL 生成模板")
    print(sql_prompt(
        schema="t_sales_order(id, order_no, customer_id, amount, status, created_at)\n"
               "t_customer(id, name, region)",
        requirement="查询 2026 年华东区销售额排名前 10 的客户及其订单总金额",
    ))

    # ---------- 实战 C：RAG 问答 ----------
    _banner("实战示例 C：RAG 问答模板")
    print(rag_prompt(
        retrieved_context="[片段1] 报销流程：提交发票 → 主管审批 → 财务复核 → 打款。\n"
                          "[片段2] 差旅标准：一线城市住宿上限 500 元/晚。",
        question="报销单提交后多久能到账？",
    ))

    # ---------- 实战 D：代码审查 ----------
    _banner("实战示例 D：代码审查模板")
    print(code_review_prompt(
        language="Python",
        code="def get_user(uid):\n"
             "    return db.query(f\"SELECT * FROM users WHERE id = {uid}\").first()",
    ))

    # ---------- 真实调用大模型（HTTP 网络请求）----------
    _banner("调用 LLM（call_llm，真实网络请求）")
    prompt = summarize_prompt(
        document="2026 年第二季度，公司华东区销售额达 3200 万元，同比增长 18%，"
                 "主要增长来自新客户渠道；但华南区销售额下滑 6%，原因待查。"
    )
    print(call_llm(prompt))

    # ---------- 异常演示：变量缺失 ----------
    _banner("变量校验：缺少必填变量时抛出异常")
    try:
        # 故意漏传 document 变量，render() 会拦截并给出明确提示
        render("请总结以下材料：{{document}}")
    except KeyError as e:
        print(f"已按预期拦截: KeyError: {e}")


if __name__ == "__main__":
    main()
