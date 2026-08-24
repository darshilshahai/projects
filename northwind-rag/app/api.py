from fastapi import APIRouter, HTTPException, UploadFile

from app.models import (
    AskRequest,
    AskResponse,
    DocumentsListResponse,
    DocumentTextRequest,
    DocumentUploadResponse,
)
from app.rag import store as store_module
from app.rag.ingest import ingest_file, ingest_text
from app.rag.pipeline import ask

router = APIRouter(prefix="/api")


@router.get("/health")
def health():
    if store_module.store is None:
        raise HTTPException(status_code=503, detail="Store not initialized")
    return {"status": "ok", "chunks": store_module.store.count()}


@router.post("/ask", response_model=AskResponse)
def ask_question(req: AskRequest):
    try:
        return ask(req.question.strip())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/documents", response_model=DocumentsListResponse)
def list_documents():
    if store_module.store is None:
        raise HTTPException(status_code=503, detail="Store not initialized")
    return {
        "documents": store_module.store.list_sources(),
        "total_chunks": store_module.store.count(),
    }


@router.post("/documents/text", response_model=DocumentUploadResponse)
def upload_document_text(req: DocumentTextRequest):
    try:
        return ingest_text(req.title.strip(), req.text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document_file(file: UploadFile):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    data = await file.read()
    try:
        return ingest_file(file.filename, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
