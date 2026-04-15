"""
Avtoritet Assistant API — FastAPI бэкенд для AI-ассистента автосервиса.
"""

from __future__ import annotations

import hmac
import logging
import os
import re
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------- Пути ----------
# backend/
BACKEND_DIR = Path(__file__).resolve().parent
# Проект (родительская директория backend/)
PROJECT_DIR = BACKEND_DIR.parent
# backend/data/ — файлы базы знаний, кеш, загружаемые документы
DATA_DIR = BACKEND_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ---------- .env ----------
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(PROJECT_DIR / ".env")

# ---------- Логирование ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("avtoritet_api")

# ---------- Импорт assistant_giga ----------
ASSISTANT_DIR = BACKEND_DIR / "assistant_giga"
sys.path.insert(0, str(ASSISTANT_DIR))
from rag_pipeline import RAGPipeline  # noqa: E402

# ---------- Инициализация RAG Pipeline ----------
pipeline = RAGPipeline(
    collection_name="gigachat_rag_collection",
    cache_db_path=str(DATA_DIR / "gigachat_rag_cache.db"),
    data_file=str(DATA_DIR),
    model="GigaChat",
)

app = FastAPI(title="Avtoritet Assistant API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Защищаем TASKS от гонок данных
_TASKS_LOCK = threading.Lock()
TASKS: Dict[str, Dict[str, object]] = {}


# ---------- Pydantic-модели ----------

class ChatRequest(BaseModel):
    """Запрос к чат-ассистенту."""
    query: str
    use_cache: bool = True


class ChatResponse(BaseModel):
    """Ответ чат-ассистента."""
    answer: str
    from_cache: bool
    meta: Dict[str, object]


class UploadResponse(BaseModel):
    """Ответ на загрузку документов."""
    task_id: str
    status: str
    files_saved: List[str]
    message: str


class TaskStatusResponse(BaseModel):
    """Статус задачи индексации."""
    task_id: str
    status: str
    created_at: str
    files: List[str]
    replace: bool
    result: Dict[str, object] | None = None
    error: str | None = None
    started_at: str | None = None
    finished_at: str | None = None


# ---------- Утилиты ----------

def _sanitize_filename(filename: str) -> str:
    """
    Санитизация имени файла: удаление опасных символов для предотвращения
    path traversal и некорректных имён.
    """
    cleaned = re.sub(r"[^a-zA-Zа-яА-Я0-9._-]", "_", filename).strip("._")
    return cleaned or f"upload_{uuid4().hex}.bin"


def _require_admin_token(x_admin_token: str | None) -> None:
    """Проверка ADMIN токена с защитой от timing-attack."""
    expected = os.getenv("ADMIN_UPLOAD_TOKEN", "").strip()
    if not expected:
        return
    if x_admin_token is None:
        raise HTTPException(status_code=401, detail="Неверный ADMIN token")
    if not hmac.compare_digest(x_admin_token, expected):
        raise HTTPException(status_code=401, detail="Неверный ADMIN token")


def _process_ingest_task(task_id: str, file_paths: List[str], replace: bool) -> None:
    """Фоновая задача индексации документов."""
    with _TASKS_LOCK:
        TASKS[task_id]["status"] = "processing"
        TASKS[task_id]["started_at"] = datetime.now(timezone.utc).isoformat()

    try:
        result = pipeline.ingest_documents(
            file_paths=file_paths, replace=replace, clear_cache=True
        )
        with _TASKS_LOCK:
            TASKS[task_id]["status"] = "done"
            TASKS[task_id]["result"] = result
    except Exception as exc:
        logger.exception("Ошибка индексации задачи %s", task_id)
        with _TASKS_LOCK:
            TASKS[task_id]["status"] = "failed"
            TASKS[task_id]["error"] = str(exc)
    finally:
        with _TASKS_LOCK:
            TASKS[task_id]["finished_at"] = datetime.now(timezone.utc).isoformat()


# ---------- Эндпоинты ----------

@app.get("/health", description="Проверка здоровья сервиса")
def health() -> Dict[str, str]:
    """Возвращает статус работоспособности API."""
    return {"status": "ok"}


@app.post("/api/chat/ask", response_model=ChatResponse, description="Задать вопрос AI-ассистенту")
def chat_ask(payload: ChatRequest) -> ChatResponse:
    """
    Принимает вопрос клиента и возвращает ответ от AI-ассистента.

    - **query**: текст вопроса (обязательно)
    - **use_cache**: использовать ли кешированный ответ (по умолчанию True)
    """
    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Поле query обязательно")

    result = pipeline.query(query, use_cache=payload.use_cache)

    return ChatResponse(
        answer=result.get("answer", ""),
        from_cache=result.get("from_cache", False),
        meta={
            "model": result.get("model"),
            "retrieval": result.get("retrieval"),
            "top_k": result.get("top_k"),
        },
    )


@app.post(
    "/api/admin/documents/upload",
    response_model=UploadResponse,
    description="Загрузка документов в базу знаний",
)
async def upload_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    replace: bool = True,
    x_admin_token: str | None = Header(default=None),
) -> UploadResponse:
    """
    Загружает документы в базу знаний ассистента.
    Требуется заголовок X-Admin-Token.
    """
    _require_admin_token(x_admin_token)

    if not files:
        raise HTTPException(status_code=400, detail="Файлы не переданы")

    saved_paths: List[str] = []
    saved_files: List[str] = []

    max_files = int(os.getenv("MAX_UPLOAD_FILES", "20"))
    if len(files) > max_files:
        raise HTTPException(
            status_code=400,
            detail=f"Слишком много файлов в одном запросе. Лимит: {max_files}",
        )

    for upload in files:
        if not upload.filename:
            continue

        safe_name = _sanitize_filename(upload.filename)
        save_path = DATA_DIR / safe_name
        content = await upload.read()
        save_path.write_bytes(content)

        saved_paths.append(str(save_path.resolve()))
        saved_files.append(safe_name)

    if not saved_paths:
        raise HTTPException(status_code=400, detail="Не удалось сохранить файлы")

    task_id = uuid4().hex
    with _TASKS_LOCK:
        TASKS[task_id] = {
            "status": "queued",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "files": saved_files,
            "replace": replace,
        }

    background_tasks.add_task(_process_ingest_task, task_id, saved_paths, replace)

    logger.info("Задача %s: загружено %d файлов", task_id, len(saved_files))

    return UploadResponse(
        task_id=task_id,
        status="queued",
        files_saved=saved_files,
        message="Файлы сохранены. Индексация запущена автоматически.",
    )


@app.get(
    "/api/admin/documents/tasks/{task_id}",
    response_model=TaskStatusResponse,
    description="Получить статус задачи индексации",
)
def get_task_status(
    task_id: str, x_admin_token: str | None = Header(default=None)
) -> TaskStatusResponse:
    """Возвращает статус фоновой задачи индексации документов."""
    _require_admin_token(x_admin_token)

    with _TASKS_LOCK:
        task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    return TaskStatusResponse(task_id=task_id, **task)
