"""
Основной RAG pipeline для GigaChat.
Управляет потоком: запрос -> кеш -> поиск -> GigaChat -> ответ -> кеш.

simplified version for public demo
full version available on request
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List

try:
    from .cache import RAGCache
    from .gigachat_client import GigaChatClient
    from .vector_store import VectorStore
except ImportError:
    from cache import RAGCache
    from gigachat_client import GigaChatClient
    from vector_store import VectorStore

logger = logging.getLogger(__name__)

# Загружаем prompt-шаблон из файла
# simplified version for public demo
_PROMPT_TEMPLATE_PATH = Path(__file__).parent / "prompt_template.txt"
if _PROMPT_TEMPLATE_PATH.exists():
    _PROMPT_TEMPLATE = _PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")
else:
    logger.warning("prompt_template.txt не найден, используется встроенный шаблон")
    _PROMPT_TEMPLATE = """Ты AI-ассистент автосервиса. Отвечай кратко и по делу.

Контекст:
{{context}}

Вопрос: {{query}}

Ответ:"""


class RAGPipeline:
    """
    RAG pipeline для GigaChat.

    simplified version for public demo
    full version available on request
    """

    def __init__(
        self,
        collection_name: str = "rag_collection",
        cache_db_path: str = "rag_cache.db",
        data_file: str = "data",
        model: str = "GigaChat",
    ) -> None:
        if not os.getenv("GIGACHAT_AUTH_KEY"):
            raise ValueError("GIGACHAT_AUTH_KEY не установлен")
        if not os.getenv("GIGACHAT_RQUID"):
            raise ValueError("GIGACHAT_RQUID не установлен")

        self.model = model
        self.gigachat_client = GigaChatClient()

        logger.info("Инициализация векторного хранилища...")
        self.vector_store = VectorStore(collection_name=collection_name)

        # Первичная индексация для пустой коллекции
        if self.vector_store.collection.count() == 0:
            initial_files = self._resolve_initial_files(data_file)
            if initial_files:
                logger.info("Первичная загрузка %d файлов...", len(initial_files))
                self.vector_store.load_documents(initial_files, replace=True)

        logger.info("Инициализация кеша...")
        self.cache = RAGCache(db_path=cache_db_path)

        logger.info("RAG Pipeline инициализирован (GigaChat)")

    def ingest_documents(
        self, file_paths: List[str], replace: bool = True, clear_cache: bool = True
    ) -> Dict[str, Any]:
        """Загрузка и индексация документов."""
        stats = self.vector_store.load_documents(file_paths=file_paths, replace=replace)

        if clear_cache and stats.get("processed_files", 0) > 0:
            self.cache.clear()
            stats["cache_cleared"] = True

        return stats

    def _resolve_initial_files(self, data_path: str) -> List[str]:
        """Найти все файлы в data-директории для первичной индексации."""
        path = Path(data_path)

        if path.is_file():
            return [str(path.resolve())]

        if path.is_dir():
            files: List[str] = []
            for ext in self.vector_store.list_supported_extensions():
                files.extend(
                    [str(p.resolve()) for p in path.rglob(f"*{ext}")]
                )
            return sorted(set(files))

        return []

    def _create_prompt(self, query: str, context_docs: List[Dict[str, Any]]) -> str:
        """Создать промпт из контекста и запроса."""
        context_parts = []
        for i, doc in enumerate(context_docs, 1):
            context_parts.append(f"Документ {i}:\n{doc['text']}\n")

        context = "\n".join(context_parts)

        prompt = (
            _PROMPT_TEMPLATE.replace("{{context}}", context)
            .replace("{{query}}", query)
        )
        return prompt

    def _generate_answer(self, prompt: str) -> str:
        """Получить ответ от GigaChat."""
        messages = [
            {
                "role": "system",
                "content": "Ты — полезный AI ассистент, который отвечает на вопросы на основе предоставленного контекста.",
            },
            {"role": "user", "content": prompt},
        ]

        answer = self.gigachat_client.chat_completion(
            messages=messages,
            model=self.model,
            temperature=0.3,
            max_tokens=500,
        )

        return answer.strip()

    def query(self, user_query: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Основной метод: запрос -> кеш -> поиск -> генерация -> ответ.

        simplified version for public demo
        """
        logger.info("Запрос: %s", user_query)

        # Проверка кеша
        if use_cache:
            cached_result = self.cache.get(user_query)
            if cached_result:
                logger.info("Ответ найден в кеше")
                return {
                    "query": user_query,
                    "answer": cached_result["answer"],
                    "from_cache": True,
                    "context_docs": cached_result.get("context"),
                }

        # Поиск документов — top_k=2 для демо
        top_k = 2  # simplified for demo version
        context_docs = self.vector_store.search(user_query, top_k=top_k)
        logger.info("Найдено %d релевантных документов", len(context_docs))

        # Генерация ответа
        prompt = self._create_prompt(user_query, context_docs)
        answer = self._generate_answer(prompt)

        # Сохранение в кеш
        if use_cache:
            context_for_cache = [doc["text"] for doc in context_docs]
            self.cache.set(user_query, answer, context_for_cache)

        return {
            "query": user_query,
            "answer": answer,
            "from_cache": False,
            "context_docs": context_docs,
            "model": self.model,
            "retrieval": "vector",
            "top_k": top_k,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику pipeline."""
        return {
            "vector_store": self.vector_store.get_collection_stats(),
            "cache": self.cache.get_stats(),
            "model": self.model,
        }
