from functools import lru_cache
from threading import RLock

from app.core.config import get_settings
from app.core.errors import AppError

_lock = RLock()
_resources: dict[str, object] = {}


def _once(key: str, factory):
    with _lock:
        if key not in _resources:
            _resources[key] = factory()
        return _resources[key]


def api_key() -> str:
    key = get_settings().deepseek_api_key
    if not key or not key.get_secret_value().strip():
        raise AppError("请在 backend/.env 配置 DEEPSEEK_API_KEY。", "configuration", 503)
    return key.get_secret_value()


@lru_cache
def get_model():
    from langchain_deepseek import ChatDeepSeek

    settings = get_settings()
    return ChatDeepSeek(
        model=settings.deepseek_model,
        api_key=api_key(),
        api_base=settings.deepseek_base_url,
        temperature=0,
        max_tokens=2400,
        timeout=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries,
        extra_body={"thinking": {"type": "disabled"}},
    )


def model_config() -> dict:
    from langchain_core.callbacks import BaseCallbackHandler

    from app.core.store import get_store
    from app.core.telemetry import current_run

    class UsageRecorder(BaseCallbackHandler):
        def on_llm_end(self, response, **kwargs):
            identifier = current_run.get()
            if not identifier:
                return
            usage = (response.llm_output or {}).get("token_usage")
            if usage:
                get_store().usage(identifier, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))
                return
            for generation in response.generations:
                for item in generation:
                    value = getattr(getattr(item, "message", None), "usage_metadata", None)
                    if value:
                        get_store().usage(identifier, value["input_tokens"], value["output_tokens"])

    return {"callbacks": [UsageRecorder()]}


def get_embeddings():
    def create():
        from langchain_huggingface import HuggingFaceEmbeddings

        settings = get_settings()
        try:
            return HuggingFaceEmbeddings(
                model_name=settings.embedding_model_name,
                model_kwargs={"device": "cpu", "local_files_only": settings.model_local_files_only},
                encode_kwargs={"normalize_embeddings": True},
            )
        except Exception as exc:
            raise AppError(
                "嵌入模型未就绪，请先运行 scripts/prepare_models.py。", "embedding_unavailable", 503
            ) from exc

    return _once("embeddings", create)


def get_reranker():
    def create():
        from sentence_transformers import CrossEncoder

        settings = get_settings()
        try:
            return CrossEncoder(
                settings.reranker_model_name, max_length=512, local_files_only=settings.model_local_files_only
            )
        except Exception as exc:
            raise AppError("重排模型未就绪，请先运行模型准备脚本，或关闭重排。", "reranker_unavailable", 503) from exc

    return _once("reranker", create)


def get_qdrant():
    def create():
        from qdrant_client import QdrantClient

        settings = get_settings()
        if settings.qdrant_mode == "local":
            return QdrantClient(path=str(settings.qdrant_local_path))
        return QdrantClient(url=settings.qdrant_url, timeout=8)

    return _once("qdrant", create)


async def close_resources():
    for resource in list(_resources.values()):
        close = getattr(resource, "close", None)
        if close:
            close()
    _resources.clear()
    if get_model.cache_info().currsize:
        model = get_model()
        client = getattr(model, "root_async_client", None)
        if client:
            await client.close()
        sync_client = getattr(model, "root_client", None)
        if sync_client:
            sync_client.close()
        get_model.cache_clear()


def loaded_resources() -> list[str]:
    return sorted(_resources)
