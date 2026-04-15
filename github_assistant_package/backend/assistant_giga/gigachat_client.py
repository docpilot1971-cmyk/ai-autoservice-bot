"""
Клиент для работы с GigaChat API от Сбера.
Управляет авторизацией и запросами к API.

simplified version for public demo
full version available on request
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class GigaChatClient:
    """
    Клиент для работы с GigaChat API.

    simplified version for public demo
    full version available on request
    """

    def __init__(
        self,
        auth_key: Optional[str] = None,
        rq_uid: Optional[str] = None,
    ) -> None:
        self.auth_key = auth_key or os.getenv("GIGACHAT_AUTH_KEY")
        self.rq_uid = rq_uid or os.getenv("GIGACHAT_RQUID")

        if not self.auth_key:
            raise ValueError("GIGACHAT_AUTH_KEY не установлен")
        if not self.rq_uid:
            raise ValueError("GIGACHAT_RQUID не установлен")

        self.oauth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        self.api_url = "https://gigachat.devices.sberbank.ru/api/v1"

        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

        # Получаем токен при инициализации
        self._refresh_token()

    def _refresh_token(self) -> None:
        """Получение нового access token."""
        payload = {"scope": "GIGACHAT_API_PERS"}
        headers: Dict[str, str] = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": self.rq_uid,
            "Authorization": f"Basic {self.auth_key}",
        }

        response = requests.post(
            self.oauth_url,
            headers=headers,
            data=payload,
        )
        response.raise_for_status()

        data = response.json()
        self.access_token = data["access_token"]
        # Токен действует 30 минут
        self.token_expires_at = datetime.now() + timedelta(minutes=29)

        logger.info("GigaChat access token получен")

    def _ensure_token_valid(self) -> None:
        """Проверка валидности токена и обновление при необходимости."""
        if (
            not self.access_token
            or self.token_expires_at is None
            or datetime.now() >= self.token_expires_at
        ):
            self._refresh_token()

    def _get_headers(self) -> Dict[str, str]:
        """Получение заголовков для запросов."""
        self._ensure_token_valid()
        assert self.access_token is not None
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "GigaChat",
        temperature: float = 0.3,
        max_tokens: int = 500,
    ) -> str:
        """
        Отправка запроса к чат-модели GigaChat.

        Args:
            messages: список сообщений
            model: название модели
            temperature: температура генерации
            max_tokens: максимальное количество токенов

        Returns:
            текст ответа от модели
        """
        url = f"{self.api_url}/chat/completions"

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        response = requests.post(
            url,
            headers=self._get_headers(),
            json=payload,
        )
        response.raise_for_status()

        data = response.json()
        return data["choices"][0]["message"]["content"]

    def get_embeddings(
        self, texts: List[str], model: str = "Embeddings"
    ) -> List[List[float]]:
        """
        Получение векторных представлений текстов.

        simplified version for public demo
        """
        url = f"{self.api_url}/embeddings"

        payload = {
            "model": model,
            "input": texts,
        }

        response = requests.post(
            url,
            headers=self._get_headers(),
            json=payload,
        )
        response.raise_for_status()

        data = response.json()
        return [item["embedding"] for item in data["data"]]
