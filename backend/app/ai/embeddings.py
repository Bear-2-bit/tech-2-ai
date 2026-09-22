from langchain_huggingface import (
    HuggingFaceEmbeddings,
)

from app.core.config import settings


def create_embeddings(
) -> HuggingFaceEmbeddings:

    return HuggingFaceEmbeddings(
        model_name=(
            settings.embedding_model_name
        ),

        model_kwargs={
            "device": "cpu",
        },

        encode_kwargs={
            "normalize_embeddings": True,
        },
    )