from langchain_core.documents import (
    Document,
)

from langchain_qdrant import (
    QdrantVectorStore,
)

from qdrant_client import (
    QdrantClient,
)

from app.ai.embeddings import (
    create_embeddings,
)

from app.core.config import settings


def create_vector_store(
    documents: list[Document],
    force_recreate: bool = False,
) -> QdrantVectorStore:

    embeddings = create_embeddings()

    return QdrantVectorStore.from_documents(
        documents=documents,

        embedding=embeddings,

        url=settings.qdrant_url,

        collection_name=(
            settings.qdrant_collection_name
        ),

        force_recreate=force_recreate,
    )


def get_vector_store(
) -> QdrantVectorStore:

    embeddings = create_embeddings()

    client = QdrantClient(
        url=settings.qdrant_url,
    )

    return QdrantVectorStore(
        client=client,

        collection_name=(
            settings.qdrant_collection_name
        ),

        embedding=embeddings,
    )