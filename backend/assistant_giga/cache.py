"""
Модуль кеширования для RAG ассистента.
Использует SQLite для хранения пар вопрос-ответ с временными метками.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, Generator, List, Optional

logger = logging.getLogger(__name__)

# TTL кеша в днях (по умолчанию 7 дней)
_CACHE_TTL_DAYS = int(os.getenv("CACHE_TTL_DAYS", "7"))


class RAGCache:
    """Кеш для хранения результатов RAG запросов."""

    # Ключевые маркеры предметной области сайта (автосервис/мотосервис).
    TOPIC_KEYWORDS = [
        # RU
        "авто",
        "автомоб",
        "автосервис",
        "ремонт",
        "диагност",
        "двигател",
        "мотор",
        "кпп",
        "коробк",
        "ходов",
        "подвес",
        "тормоз",
        "рул",
        "сцеплен",
        "электрик",
        "генератор",
        "стартер",
        "кондиционер",
        "фреон",
        "мото",
        "мотоцикл",
        "запчаст",
        "детал",
        "то",
        "обслуживан",
        "volkswagen",
        "skoda",
        "audi",
        "bmw",
        "mercedes",
        "hyundai",
        "kia",
        "toyota",
        "nissan",
        "subaru",
        "geely",
        "changan",
        # EN
        "car",
        "auto",
        "repair",
        "engine",
        "gearbox",
        "suspension",
        "diagnostic",
        "service",
        "motorcycle",
        "air conditioning",
        "ac",
    ]

    def __init__(self, db_path: str = "rag_cache.db") -> None:
        """
        Инициализация кеша.

        Args:
            db_path: путь к файлу базы данных SQLite
        """
        self.db_path = db_path
        self._init_db()
        self._cleanup_expired()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Контекстный менеджер для безопасной работы с SQLite."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Создание таблицы кеша, если она не существует."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    query_hash TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    context TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """
            )
            conn.commit()

    def _cleanup_expired(self) -> None:
        """Удаление записей с истёкшим TTL."""
        cutoff = datetime.now() - timedelta(days=_CACHE_TTL_DAYS)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM cache WHERE expires_at IS NOT NULL AND expires_at < ?",
                (cutoff.isoformat(),),
            )
            deleted = cursor.rowcount
            conn.commit()
        if deleted > 0:
            logger.info("Удалено %d устаревших записей кеша", deleted)

    def _get_query_hash(self, query: str) -> str:
        """
        Вычисление хеша запроса для использования как ключ кеша.

        Args:
            query: текст запроса

        Returns:
            SHA-256 хеш запроса
        """
        normalized_query = " ".join(query.lower().strip().split())
        return hashlib.sha256(normalized_query.encode()).hexdigest()

    def _is_site_topic(self, text: str) -> bool:
        """Проверка, относится ли текст к тематике сайта."""
        if not text:
            return False
        normalized = " ".join(text.lower().strip().split())
        return any(keyword in normalized for keyword in self.TOPIC_KEYWORDS)

    def _filter_topic_context(
        self, context: Optional[List[str]]
    ) -> Optional[List[str]]:
        """Оставляет только тематические элементы контекста."""
        if not context:
            return None
        filtered = [
            item for item in context if isinstance(item, str) and self._is_site_topic(item)
        ]
        return filtered or None

    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Получение ответа из кеша.

        Args:
            query: текст запроса

        Returns:
            Словарь с ответом и метаданными, или None если не найдено
        """
        query_hash = self._get_query_hash(query)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT query, answer, context, created_at
                FROM cache
                WHERE query_hash = ?
                  AND (expires_at IS NULL OR expires_at > ?)
            """,
                (query_hash, datetime.now().isoformat()),
            )
            result = cursor.fetchone()

        if result:
            return {
                "query": result[0],
                "answer": result[1],
                "context": json.loads(result[2]) if result[2] else None,
                "created_at": result[3],
                "from_cache": True,
            }

        return None

    def set(self, query: str, answer: str, context: Optional[List[str]] = None) -> bool:
        """
        Сохранение ответа в кеш.

        Args:
            query: текст запроса
            answer: текст ответа
            context: список документов, использованных как контекст

        Returns:
            True, если запись сохранена; False, если запрос/контекст вне тематики сайта
        """
        if not self._is_site_topic(query):
            return False

        filtered_context = self._filter_topic_context(context)
        if context and not filtered_context:
            return False

        query_hash = self._get_query_hash(query)
        context_json = json.dumps(filtered_context) if filtered_context else None
        expires_at = (datetime.now() + timedelta(days=_CACHE_TTL_DAYS)).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO cache
                    (query_hash, query, answer, context, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    query_hash,
                    query,
                    answer,
                    context_json,
                    datetime.now().isoformat(),
                    expires_at,
                ),
            )
            conn.commit()
        return True

    def clear(self) -> None:
        """Очистка всего кеша."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cache")
            conn.commit()

    def get_stats(self) -> Dict[str, Any]:
        """
        Получение статистики кеша.

        Returns:
            Словарь со статистикой
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM cache")
            count = cursor.fetchone()[0]

            cursor.execute("SELECT MIN(created_at), MAX(created_at) FROM cache")
            dates = cursor.fetchone()

            db_size_mb = (
                os.path.getsize(self.db_path) / (1024 * 1024)
                if os.path.exists(self.db_path)
                else 0
            )

        return {
            "total_entries": count,
            "oldest_entry": dates[0] if dates[0] else None,
            "newest_entry": dates[1] if dates[1] else None,
            "db_size_mb": db_size_mb,
            "ttl_days": _CACHE_TTL_DAYS,
        }


if __name__ == "__main__":
    # Тестирование кеша
    logging.basicConfig(level=logging.INFO)
    cache = RAGCache("test_cache.db")

    saved = cache.set(
        query="Сколько стоит диагностика двигателя?",
        answer="Стоимость диагностики зависит от марки авто и сложности неисправности.",
        context=["Диагностика двигателя, тормозной системы и подвески выполняется по записи."],
    )
    print("Сохранение в кеш:", saved)

    result = cache.get("Сколько стоит диагностика двигателя?")
    print("Результат из кеша:", result)

    stats = cache.get_stats()
    print("Статистика кеша:", stats)

    import os as _os

    if _os.path.exists("test_cache.db"):
        _os.remove("test_cache.db")
