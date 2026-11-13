"""OpenAI-compatible Chat Completions client."""

import logging
import os
from dataclasses import dataclass
from openai import OpenAI, APIConnectionError, APITimeoutError, APIStatusError

logger = logging.getLogger("crj-chat")


@dataclass
class ChatResult:
    content: str
    finish_reason: str  # "stop", "length", or other
    prompt_tokens: int
    completion_tokens: int
    reasoning_tokens: int


def _get_client() -> OpenAI:
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is not set. "
            "Please create a .env file with your API key. See .env.example."
        )
    return OpenAI(base_url=base_url, api_key=api_key, timeout=60.0)


def _get_model() -> str:
    return os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


def _get_max_tokens() -> int:
    try:
        return int(os.environ.get("MAX_TOKENS", "1024"))
    except ValueError:
        return 1024


def _get_reasoning_effort() -> str | None:
    """Get reasoning_effort from env. Returns None if not set."""
    value = os.environ.get("REASONING_EFFORT", "low").strip().lower()
    if value in ("low", "high", "max"):
        return value
    if value in ("none", "off", "disable", ""):
        return None
    return value  # pass through unknown values to let the API decide


def chat(system_prompt: str, messages: list[dict]) -> ChatResult:
    """Send a chat completion request.

    Returns a ChatResult with content, finish_reason, and token counts.
    """
    client = _get_client()
    model = _get_model()
    max_tokens = _get_max_tokens()
    reasoning_effort = _get_reasoning_effort()

    api_messages = [{"role": "system", "content": system_prompt}]

    # Trim conversation history to avoid context overflow.
    char_budget = 60_000
    trimmed = []
    total = 0
    for msg in reversed(messages):
        total += len(msg["content"])
        if total > char_budget:
            break
        trimmed.append(msg)
    trimmed.reverse()
    api_messages.extend(trimmed)

    # Build extra params for reasoning models
    extra_body = {}
    if reasoning_effort:
        extra_body["reasoning_effort"] = reasoning_effort

    try:
        response = client.chat.completions.create(
            model=model,
            messages=api_messages,
            temperature=0.75,
            max_tokens=max_tokens,
            extra_body=extra_body if extra_body else None,
        )
    except APIConnectionError:
        raise ConnectionError("无法连接到 API 服务器，请检查网络和 OPENAI_BASE_URL 配置。")
    except APITimeoutError:
        raise ConnectionError("API 请求超时，请稍后重试。")
    except APIStatusError as e:
        if e.status_code == 401:
            raise ValueError("API Key 无效，请检查 .env 中的 OPENAI_API_KEY。")
        if e.status_code == 429:
            raise ConnectionError("API 请求过于频繁，请稍后重试。")
        raise ConnectionError(f"API 返回错误 ({e.status_code})：{e.message}")

    choice = response.choices[0] if response.choices else None
    if not choice or not choice.message:
        raise ConnectionError("API 返回了空回复，请重试。")

    content = choice.message.content or ""
    content = content.strip()
    finish_reason = choice.finish_reason or "unknown"

    # Extract token usage
    prompt_tokens = 0
    completion_tokens = 0
    reasoning_tokens = 0
    if response.usage:
        prompt_tokens = response.usage.prompt_tokens or 0
        completion_tokens = response.usage.completion_tokens or 0
        # Extract reasoning_tokens from completion_tokens_details
        try:
            details = response.usage.model_dump().get("completion_tokens_details", {})
            if details:
                reasoning_tokens = details.get("reasoning_tokens", 0) or 0
        except Exception:
            pass

    # Diagnostic logging (no secrets, no full content)
    content_tokens = completion_tokens - reasoning_tokens
    logger.info(
        "API: finish=%s, content_len=%d chars, "
        "prompt=%d, completion=%d (reasoning=%d + content=%d), "
        "max_tokens=%d, reasoning_effort=%s",
        finish_reason, len(content),
        prompt_tokens, completion_tokens, reasoning_tokens, content_tokens,
        max_tokens, reasoning_effort or "default",
    )

    if finish_reason == "length":
        logger.warning(
            "TRUNCATED: completion=%d reached max_tokens=%d "
            "(reasoning=%d consumed %d%% of budget). "
            "Content may be incomplete.",
            completion_tokens, max_tokens,
            reasoning_tokens,
            (reasoning_tokens * 100 // max_tokens) if max_tokens else 0,
        )

    if not content:
        raise ConnectionError("API 返回了空回复，请重试。")

    return ChatResult(
        content=content,
        finish_reason=finish_reason,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        reasoning_tokens=reasoning_tokens,
    )
