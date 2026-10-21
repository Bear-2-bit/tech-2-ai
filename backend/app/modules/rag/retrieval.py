import asyncio

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.telemetry import set_outcome, span
from app.modules.rag.ingestion import list_documents, vector_store
from app.modules.rag.schemas import SearchRequest
from app.resources import get_model, get_reranker, model_config


def eligible_versions(request: SearchRequest) -> list[str]:
    chosen = {}
    for row in list_documents():
        meta = row["metadata"]
        if row["status"] not in ({"ready", "superseded"} if request.as_of else {"ready"}):
            continue
        if meta.get("embedding_model") != get_settings().embedding_model_name:
            continue
        if request.category and meta.get("category") != request.category:
            continue
        if request.product_code and meta.get("product_code") not in {request.product_code, None, ""}:
            continue
        if request.as_of:
            as_of = request.as_of.isoformat()
            if meta.get("effective_from", "0001-01-01") > as_of:
                continue
            if meta.get("effective_to") and meta["effective_to"] < as_of:
                continue
        previous = chosen.get(row["document_id"])
        if previous is None or row["version"] > previous["version"]:
            chosen[row["document_id"]] = row
    return [row["id"] for row in chosen.values()]


def _search(request: SearchRequest, query: str, versions: list[str]) -> list[dict]:
    from qdrant_client.models import FieldCondition, Filter, MatchAny

    candidates = vector_store().similarity_search_with_score(
        query,
        k=min(request.top_k * 4, 50) if request.rerank else request.top_k,
        filter=Filter(must=[FieldCondition(key="metadata.version_id", match=MatchAny(any=versions))]),
    )
    if request.rerank and candidates:
        scores = get_reranker().predict(
            [(query, doc.page_content) for doc, _ in candidates], show_progress_bar=False
        )
        candidates = sorted(
            zip([doc for doc, _ in candidates], map(float, scores), strict=True),
            key=lambda pair: pair[1],
            reverse=True,
        )
    return [
        {
            "id": doc.metadata["chunk_id"],
            "content": doc.page_content,
            "metadata": doc.metadata,
            "score": float(score),
            "score_type": "reranker" if request.rerank else "cosine",
        }
        for doc, score in candidates[: request.top_k]
    ]


async def search(request: SearchRequest) -> dict:
    with span("rag", "rag.search", {"top_k": request.top_k, "rerank": request.rerank}) as run_id:
        versions = await asyncio.to_thread(eligible_versions, request)
        if not versions:
            set_outcome("incomplete")
            return {
                "query": request.query,
                "rewritten_query": request.query,
                "documents": [],
                "status": "knowledge_empty",
                "run_id": run_id,
            }
        rewritten = request.query
        if request.rewrite:
            with span("rag", "rag.rewrite"):
                message = await get_model().ainvoke(
                    [
                        (
                            "system",
                            "把问题改写为独立的知识检索查询，保持原意与限定条件，只返回查询，不回答。",
                        ),
                        ("human", request.query),
                    ],
                    config=model_config(),
                )
                rewritten = message.content.strip() or request.query
        try:
            documents = await asyncio.to_thread(_search, request, rewritten, versions)
        except AppError:
            raise
        except Exception as exc:
            raise AppError("知识检索失败，请检查索引与模型状态。", "retrieval_unavailable", 503) from exc
        return {
            "query": request.query,
            "rewritten_query": rewritten,
            "documents": documents,
            "status": "ready",
            "run_id": run_id,
        }
