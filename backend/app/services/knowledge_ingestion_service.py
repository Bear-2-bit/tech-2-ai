from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.schemas.rag import KnowledgeIngestionResponse


class KnowledgeIngestionService:
    def __init__(self, vector_store: QdrantVectorStore):
        self.vector_store = vector_store

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=80,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""],
        )

    def ingest_file(self, file_path: Path, original_filename: str) -> KnowledgeIngestionResponse:
        loader = self._create_loader(file_path)

        documents = loader.load()

        for document in documents:
            document.metadata["source"] = original_filename
            document.metadata["filename"] = original_filename
            document.metadata["file_type"] = file_path.suffix.lower().lstrip(".")

        chunks = self.text_splitter.split_documents(documents)

        for index, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = index

        self.vector_store.add_documents(chunks)

        return KnowledgeIngestionResponse(
            filename=original_filename,
            document_count=len(documents),
            chunk_count=len(chunks),
        )

    def _create_loader(self, file_path: Path):
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            return PyPDFLoader(str(file_path))

        if suffix in {".txt", ".md"}:
            return TextLoader(str(file_path), encoding="utf-8")

        raise ValueError(f"Unsupported file type: {suffix}")