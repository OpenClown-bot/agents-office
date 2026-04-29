from __future__ import annotations

import asyncio

import httpx
import structlog

from smm_autopilot.llm.providers import GLMProvider, LLMResponse, QwenProvider
from smm_autopilot.llm.usage import UsageTracker

logger = structlog.get_logger()

_MAX_RETRIES = 2
_BACKOFF_SECONDS = 10.0


class LLMClient:
    def __init__(
        self,
        glm_provider: GLMProvider,
        qwen_provider: QwenProvider,
        usage: UsageTracker,
    ) -> None:
        self._glm = glm_provider
        self._qwen = qwen_provider
        self._usage = usage

    async def classify(self, system_prompt: str, user_content: str) -> LLMResponse | None:
        if await self._usage.is_budget_exceeded():
            logger.warning("llm_budget_exceeded_degrading_to_keyword_only")
            return None

        async with httpx.AsyncClient() as client:
            for attempt in range(_MAX_RETRIES + 1):
                try:
                    response = await self._glm.call(client, system_prompt, user_content)
                    await self._usage.record_call(response.total_tokens)
                    return response
                except Exception as exc:
                    await self._usage.record_error()
                    logger.warning(
                        "glm_call_failed",
                        attempt=attempt + 1,
                        error=str(exc),
                    )
                    if attempt < _MAX_RETRIES:
                        await asyncio.sleep(_BACKOFF_SECONDS)

            for attempt in range(_MAX_RETRIES + 1):
                try:
                    response = await self._qwen.call(client, system_prompt, user_content)
                    await self._usage.record_call(response.total_tokens)
                    return response
                except Exception as exc:
                    await self._usage.record_error()
                    logger.warning(
                        "qwen_call_failed",
                        attempt=attempt + 1,
                        error=str(exc),
                    )
                    if attempt < _MAX_RETRIES:
                        await asyncio.sleep(_BACKOFF_SECONDS)

        logger.warning("all_llm_providers_failed")
        return None
