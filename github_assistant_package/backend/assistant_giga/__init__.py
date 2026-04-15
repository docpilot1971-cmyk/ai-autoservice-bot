"""
AI-ассистент для сервисного центра «Авторитет» — RAG на базе GigaChat.

Пакет содержит все компоненты RAG-пайплайна:
- RAGPipeline   — основной оркестратор (кеш → поиск → генерация)
- GigaChatClient — клиент к GigaChat API (авторизация, чат, эмбеддинги)
- VectorStore    — гибридный поиск (ChromaDB + BM25)
- DocumentProcessor — загрузка и чанкинг документов
- RAGCache       — SQLite кеш с TTL
"""

__all__ = [
    "RAGPipeline",
    "GigaChatClient",
    "VectorStore",
    "DocumentProcessor",
    "RAGCache",
]

from .rag_pipeline import RAGPipeline
from .gigachat_client import GigaChatClient
from .vector_store import VectorStore
from .document_processor import DocumentProcessor
from .cache import RAGCache
