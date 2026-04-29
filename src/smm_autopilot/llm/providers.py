from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
import structlog

logger = structlog.get_logger()

GLM_API_BASE = "https://open.bigmodel.cn/api/paas/v4"
QWEN_API_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"

GLM_MODEL = "glm-4-flash"
QWEN_MODEL = "qwen-turbo"


@dataclass
class LLMResponse:
    content: str
    total_tokens: int


class GLMProvider:
    def __init__(self, api_key: str, timeout: float = 30.0) -> None:
        self._api_key = api_key
        self._timeout = timeout

    async def call(
        self,
        client: httpx.AsyncClient,
        system_prompt: str,
        user_content: str,
    ) -> LLMResponse:
        payload: dict[str, Any] = {
            "model": GLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.0,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        resp = await client.post(
            f"{GLM_API_BASE}/chat/completions",
            json=payload,
            headers=headers,
            timeout=self._timeout,
        )
        resp.raise_for_status()
        body = resp.json()
        content = body["choices"][0]["message"]["content"]
        total_tokens = body.get("usage", {}).get("total_tokens", 0)
        logger.debug("glm_call_success", total_tokens=total_tokens)
        return LLMResponse(content=content, total_tokens=total_tokens)


class QwenProvider:
    def __init__(self, api_key: str, timeout: float = 30.0) -> None:
        self._api_key = api_key
        self._timeout = timeout

    async def call(
        self,
        client: httpx.AsyncClient,
        system_prompt: str,
        user_content: str,
    ) -> LLMResponse:
        payload: dict[str, Any] = {
            "model": QWEN_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.0,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        resp = await client.post(
            f"{QWEN_API_BASE}/chat/completions",
            json=payload,
            headers=headers,
            timeout=self._timeout,
        )
        resp.raise_for_status()
        body = resp.json()
        content = body["choices"][0]["message"]["content"]
        total_tokens = body.get("usage", {}).get("total_tokens", 0)
        logger.debug("qwen_call_success", total_tokens=total_tokens)
        return LLMResponse(content=content, total_tokens=total_tokens)
