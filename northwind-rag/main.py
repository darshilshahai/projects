from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router
from app.rag import rerank as rerank_module
from app.rag import store as store_module
from app.rag.rerank import Reranker
from app.rag.store import Store


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load models once, at startup — not per request.
    store_module.store = Store()
    rerank_module.reranker = Reranker()
    yield


app = FastAPI(title="Northwind RAG", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

app.include_router(router)
