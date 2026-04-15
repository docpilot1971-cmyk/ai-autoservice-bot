"""
Модуль работы с векторным хранилищем ChromaDB.
Поддерживает загрузку документов и векторный поиск.

simplified version for public demo
full version available on request
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

import chromadb

try:
    from .document_processor import DocumentProcessor, SUPPORTED_EXTENSIONS
    from .gigachat_client import GigaChatClient
except ImportError:
    from document_processor import DocumentProcessor, SUPPORTED_EXTENSIONS
    from gigachat_client import GigaChatClient

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Векторное хранилище на основе ChromaDB с GigaChat embeddings.

    simplified version for public demo
    full version available on request
    """

    def __init__(
        self, collection_name: str = "rag_collection", persist_directory: str = "./chroma_db"
    ) -> None:
        self.collection_name = collection_name
        self.persist_directory = persist_directory

        self.client = chromadb.PersistentClient(path=persist_directory)

        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(
                "Коллекция '%s' загружена. Документов: %d",
                collection_name,
                self.collection.count(),
            )
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("Создана новая коллекция '%s'", collection_name)

        self.gigachat_client = GigaChatClient()
        self.processor = DocumentProcessor(
            max_file_size_mb=int(os.getenv("MAX_UPLOAD_SIZE_MB", "25")),
            enable_ocr=os.getenv("ENABLE_OCR", "true").lower() == "true",
        )

    def load_documents(
        self, file_paths: Iterable[str], replace: bool = True
    ) -> Dict[str, Any]:
        """
        Загрузка документов в векторное хранилище.

        simplified version for public demo
        """
        processed = 0
        failed = 0
        total_chunks = 0
        errors: List[Dict[str, str]] = []

        for raw_path in file_paths:
            path = Path(raw_path)

            try:
                doc = self.processor.process_file(str(path))

                if replace:
                    self.collection.delete(where={"file_hash": doc.file_hash})

                docs: List[str] = []
                ids: List[str] = []
                metadatas: List[Dict[str, Any]] = []

                for chunk_idx, chunk in enumerate(doc.chunks):
                    docs.append(chunk)
                    ids.append(f"{doc.file_hash[:12]}_{chunk_idx}")
                    metadatas.append(
                        {
                            "source": doc.source_name,
                            "source_path": doc.source_path,
                            "source_ext": doc.extension,
                            "file_hash": doc.file_hash,
                            "chunk_index": chunk_idx,
                            "updated_at": datetime.now(timezone.utc).isoformat(),
                        }
                    )

                # batch-эмбеддинги для всех чанков
                embeddings = self._create_embeddings(docs) if docs else []

                if docs:
                    self.collection.add(
                        documents=docs,
                        embeddings=embeddings,
                        metadatas=metadatas,
                        ids=ids,
                    )

                processed += 1
                total_chunks += len(doc.chunks)
                logger.info("Загружен %s: %d чанков", doc.source_name, len(doc.chunks))

            except Exception as exc:
                failed += 1
                errors.append({"file": str(path), "error": str(exc)})
                logger.exception("Ошибка обработки %s", path.name)

        return {
            "processed_files": processed,
            "failed_files": failed,
            "total_chunks": total_chunks,
            "errors": errors,
            "collection_count": self.collection.count(),
        }

    def search(
        self, query: str, top_k: int = 3, alpha: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Векторный поиск документов.

        simplified version for public demo
        alpha параметр сохранён для совместимости API но не используется
        full version available on request
        """
        if self.collection.count() == 0:
            return []

        return self._vector_search(query, top_k)

    def _vector_search(self, query: str, top_n: int) -> List[Dict[str, Any]]:
        """Базовый векторный поиск по embeddings."""
        query_embedding = self._create_embedding(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_n, self.collection.count()),
            include=["documents", "distances", "metadatas"],
        )

        docs: List[Dict[str, Any]] = []
        if results.get("documents") and results["documents"][0]:
            for i in range(len(results["documents"][0])):
                distance = results["distances"][0][i] if results.get("distances") else 1.0
                score = 1.0 / (1.0 + max(distance, 0.0))
                docs.append(
                    {
                        "id": results["ids"][0][i],
                        "text": results["documents"][0][i],
                        "distance": distance,
                        "score": score,
                        "metadata": results["metadatas"][0][i]
                        if results.get("metadatas")
                        else None,
                    }
                )
        return docs

    def _create_embedding(self, text: str) -> List[float]:
        """Получить embedding для одного текста."""
        embeddings = self.gigachat_client.get_embeddings([text])
        return embeddings[0]

    def _create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Получить embeddings для списка текстов."""
        return self.gigachat_client.get_embeddings(texts)

    def list_supported_extensions(self) -> List[str]:
        """Список поддерживаемых расширений."""
        return sorted(SUPPORTED_EXTENSIONS)

    def get_collection_stats(self) -> Dict[str, Any]:
        """Статистика коллекции."""
        return {
            "name": self.collection_name,
            "count": self.collection.count(),
            "persist_directory": self.persist_directory,
            "supported_extensions": self.list_supported_extensions(),
        }
