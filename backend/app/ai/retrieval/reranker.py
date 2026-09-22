from langchain_core.documents import Document
from sentence_transformers import CrossEncoder


class Reranker:
    def __init__(self, model_name: str):
        self.model = CrossEncoder(model_name, max_length=512)

    def rerank(
        self,
        query: str,
        documents: list[Document],
        top_k: int,
    ) -> list[tuple[Document, float]]:
        if not documents:
            return []

        pairs = [(query, document.page_content) for document in documents]

        scores = self.model.predict(pairs, show_progress_bar=False)

        ranked = sorted(
            zip(documents, scores),
            key=lambda item: float(item[1]),
            reverse=True,
        )

        return [
            (document, float(score))
            for document, score in ranked[:top_k]
        ]