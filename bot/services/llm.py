import base64
import logging

from openai import AsyncOpenAI

from bot.config import settings

log = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    global _client
    if not settings.openrouter_api_key:
        raise RuntimeError("OPENROUTER_API_KEY не задан в .env")
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )
    return _client


async def analyze_text(system_prompt: str, user_text: str) -> str:
    client = get_client()
    response = await client.chat.completions.create(
        model=settings.openrouter_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        temperature=0.3,
        max_tokens=2000,
    )
    return response.choices[0].message.content


async def analyze_image(system_prompt: str, image_bytes: bytes, caption: str | None = None) -> str:
    client = get_client()
    b64 = base64.b64encode(image_bytes).decode()
    content = []
    if caption:
        content.append({"type": "text", "text": caption})
    content.append({
        "type": "image_url",
        "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
    })
    response = await client.chat.completions.create(
        model=settings.openrouter_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ],
        temperature=0.3,
        max_tokens=2000,
    )
    return response.choices[0].message.content
