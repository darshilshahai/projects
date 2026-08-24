from app.rag import rerank as rerank_module
from app.rag import store as store_module
from app.rag.pipeline import ask
from app.rag.rerank import Reranker
from app.rag.store import Store

store_module.store = Store()
rerank_module.reranker = Reranker()

result = ask("What is the company's policy on office pets?")
print("refused_by:", result["refused_by"])
