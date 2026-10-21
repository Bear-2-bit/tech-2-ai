"""Explicitly download models; normal server startup never downloads them."""

import argparse

from app.core.config import get_settings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reranker", action="store_true")
    args = parser.parse_args()
    from sentence_transformers import SentenceTransformer

    settings = get_settings()
    SentenceTransformer(settings.embedding_model_name, device="cpu", local_files_only=False)
    print(f"嵌入模型已准备：{settings.embedding_model_name}")
    if args.reranker:
        from sentence_transformers import CrossEncoder

        CrossEncoder(settings.reranker_model_name, device="cpu", local_files_only=False)
        print(f"重排模型已准备：{settings.reranker_model_name}")


if __name__ == "__main__":
    main()
