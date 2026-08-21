# -*- coding: utf-8 -*-
"""
Jinja2 提示词模板可运行示例
================================================

对应文档：practice/jinja2-提示词模板.md
运行方式：
    C:/Users/Administrator/.workbuddy/binaries/python/envs/default/Scripts/python.exe \
        practice/jinja2_prompt_template.py
依赖：jinja2（已安装到受管隔离环境 envs/default 中）

覆盖内容：基础渲染、过滤器、条件分支、循环生成 Few-Shot、
宏复用、模板继承、白空格控制、沙箱渲染与 RAG 提示词实战。
"""

from jinja2 import DictLoader, Environment, Template
from jinja2.sandbox import SandboxedEnvironment  # 沙箱环境在独立子模块中

# =====================================================================
# 一、基础渲染：Environment + 渲染字符串模板
# =====================================================================

print("=" * 70)
print("  1. 基础渲染（变量 + 简单表达式）")
print("=" * 70)

# Environment 是渲染的"运行时"，可统一配置过滤器、白空格策略等
env = Environment(trim_blocks=True, lstrip_blocks=True)

basic_template = env.from_string(
    "你是{{ role }}，请回答下面的问题：\n"
    "问题：{{ question }}\n"
    "{% if max_length %}请将回答控制在 {{ max_length }} 字以内。{% endif %}"
)

prompt = basic_template.render(
    role="资深 Java 架构师",
    question="什么是微服务？",
    max_length=100,
)
print(prompt)
print("-" * 40)
# 不传 max_length：条件指令自动消失（这是简单占位符替换做不到的）
prompt_no_limit = basic_template.render(
    role="产品经理",
    question="本周发布计划是什么？",
)
print(prompt_no_limit)

# =====================================================================
# 二、过滤器：截断 / 拼接 / 默认值（对应文档 3.3）
# =====================================================================

print()
print("=" * 70)
print("  2. 过滤器（truncate / join / default）")
print("=" * 70)

filter_template = env.from_string(
    "检索片段：{{ chunk | truncate(50) }}\n"
    "备选方案：{{ options | join('、') }}\n"
    "输出语言：{{ lang | default('中文', true) }}"
)
print(filter_template.render(
    chunk="这是一段非常非常长的检索内容，包含了大量业务细节……",
    options=["方案A", "方案B", "方案C"],
    lang=None,  # 传 None，default 过滤器兜底为"中文"
))

# =====================================================================
# 三、条件分支 if/elif/else（对应文档 3.4 / 4.2）
# =====================================================================

print()
print("=" * 70)
print("  3. 条件分支：同一模板服务不同详细度")
print("=" * 70)

detail_template = env.from_string(
    "{% if detail_level == 'detailed' %}"
    "请分步说明推理过程，并给出正反两面论证。"
    "{% elif detail_level == 'brief' %}"
    "直接给出结论，不超过三句话。"
    "{% else %}"
    "正常回答即可。"
    "{% endif %}"
)
print(detail_template.render(detail_level="detailed"))
print(detail_template.render(detail_level="brief"))

# =====================================================================
# 四、循环生成 Few-Shot 示例（对应文档 3.5 / 4.1）
# =====================================================================

print()
print("=" * 70)
print("  4. for 循环动态生成 Few-Shot 示例")
print("=" * 70)

few_shot_template = env.from_string(
    "请根据以下示例完成同样的分类任务。\n"
    "{% for ex in examples %}"
    "示例 {{ loop.index }}：输入：{{ ex.input }} → 输出：{{ ex.label }}\n"
    "{% endfor %}"
    "输入：{{ real_input }}\n输出："
)
print(few_shot_template.render(
    examples=[
        {"input": "这家店发货太慢了。", "label": "负面"},
        {"input": "包装结实，客服耐心。", "label": "正面"},
        {"input": "产品不错，价格略贵。", "label": "中性"},
    ],
    real_input="退货流程很简单，但运费要自理。",
))

# =====================================================================
# 五、宏：指令片段复用（对应文档 3.6）
# =====================================================================

print("=" * 70)
print("  5. 宏（macro）：统一格式化信息来源")
print("=" * 70)

macro_template = env.from_string(
    "{% macro format_source(source) -%}\n"
    "【来源】{{ source.title }}（{{ source.url }}）\n"
    "{%- endmacro %}\n"
    "参考资料：\n"
    "{{ format_source(source_a) }}\n"
    "{{ format_source(source_b) }}"
)
print(macro_template.render(
    source_a={"title": "报销制度 V3", "url": "https://wiki.internal/finance/expense"},
    source_b={"title": "差旅标准", "url": "https://wiki.internal/finance/travel"},
))

# =====================================================================
# 六、模板继承：基础提示词 + 场景扩展（对应文档 3.7）
# =====================================================================

print()
print("=" * 70)
print("  6. 模板继承（基模板定义公共结构，子模板只写差异）")
print("=" * 70)

# 用 DictLoader 在内存中提供两个"文件"：base 基模板 + qa 子模板
loader = DictLoader({
    "base_prompt.j2": (
        "你是{{ role }}。\n"
        "{% block content %}{% endblock %}"
        "{% if constraints %}注意：{{ constraints }}。{% endif %}"
    ),
    "qa_prompt.j2": (
        '{% extends "base_prompt.j2" %}'
        "{% block content %}问题：{{ question }}\n{% endblock %}"
    ),
})
inherit_env = Environment(loader=loader, trim_blocks=True, lstrip_blocks=True)

qa = inherit_env.get_template("qa_prompt.j2")
print(qa.render(
    role="知识库助手",
    question="报销单提交后多久到账？",
    constraints="只依据公司制度回答，不要编造",
))

# =====================================================================
# 七、沙箱渲染：处理不可信模板时的安全执行（对应文档 6）
# =====================================================================

print("=" * 70)
print("  7. 沙箱渲染（SandboxedEnvironment 防止危险属性访问）")
print("=" * 70)

sandbox = SandboxedEnvironment(trim_blocks=True, lstrip_blocks=True)
# 恶意模板尝试访问 Python 内建对象 __class__ / __subclasses__ 链
malicious = "{{ ''.__class__.__mro__[1].__subclasses__() }}"
try:
    sandbox.from_string(malicious).render()
    print("（未拦截？说明沙箱配置有误）")
except Exception as e:
    print(f"已拦截恶意模板访问: {type(e).__name__}: {e}")

# =====================================================================
# 八、实战：RAG 问答提示词（检索片段数量不定 + 长度控制）
# =====================================================================

print()
print("=" * 70)
print("  8. 实战：RAG 问答提示词（循环拼接检索片段）")
print("=" * 70)

rag_template = env.from_string(
    "请仅依据以下资料回答，不要编造：\n"
    "{% for chunk in retrieved_chunks[:3] %}"   # 只取前 3 段，避免提示词超限
    "[片段 {{ loop.index }}] {{ chunk | truncate(200) }}\n"
    "{% endfor %}\n"
    "问题：{{ question }}\n"
    "{% if need_source %}回答时请标注引用的片段编号。{% endif %}"
)

print(rag_template.render(
    retrieved_chunks=[
        "报销流程：提交发票 → 主管审批 → 财务复核 → 打款，全流程约 3 个工作日。",
        "差旅标准：一线城市住宿上限 500 元/晚，二线城市 350 元/晚。",
        "报销时限：费用发生后 30 天内必须提交，逾期需特殊审批。",
        "（这段因为超出前 3 段，不会被渲染）",
    ],
    question="住宿报销标准是多少？",
    need_source=True,
))

# =====================================================================
# 九、模板语法速查：直接在代码中定义（Template 快捷方式）
# =====================================================================

print()
print("=" * 70)
print("  9. 快捷方式：Template('...') 一步到位")
print("=" * 70)

quick = Template("系统：{{ system }}\n用户：{{ user }}")
print(quick.render(system="你是翻译助手", user="把这段话翻译成英文"))
