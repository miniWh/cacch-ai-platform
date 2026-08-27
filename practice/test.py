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