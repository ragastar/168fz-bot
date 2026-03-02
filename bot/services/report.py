import json
import logging

log = logging.getLogger(__name__)

VERDICT_EMOJI = {
    "red": "🔴",
    "yellow": "🟡",
    "green": "🟢",
}

VERDICT_TITLE = {
    "red": "Обнаружены нарушения",
    "yellow": "Есть замечания",
    "green": "Нарушений не обнаружено",
}

SEVERITY_EMOJI = {
    "red": "🔴",
    "yellow": "🟡",
    "green": "🟢",
}

ELEMENT_TYPE_LABEL = {
    "nav": "навигация",
    "button": "кнопка",
    "heading": "заголовок",
    "text": "текст страницы",
    "meta": "мета-данные",
    "img_alt": "описание картинки",
    "title": "заголовок страницы",
    "form": "форма",
    "footer": "подвал сайта",
    "popup": "всплывающее окно",
    "modal": "модальное окно",
    "placeholder": "подсказка в поле ввода",
    "error": "сообщение об ошибке",
    "label": "подпись",
}


def parse_llm_response(raw: str) -> dict | None:
    """Parse JSON from LLM response, stripping markdown fences if present."""
    text = raw.strip()
    if text.startswith("```"):
        # Remove ```json ... ```
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        log.error("Failed to parse LLM JSON: %s", text[:500])
        return None


def format_report(data: dict) -> str:
    """Format parsed JSON into a Telegram HTML report."""
    verdict = data.get("verdict", "yellow")

    if verdict == "no_text":
        return (
            "📷 <b>Результат проверки</b>\n\n"
            "На фото не обнаружено текстовых элементов.\n"
            "Попробуйте отправить фото с видимым текстом (вывеска, меню, ценник)."
        )

    if verdict == "unclear":
        return (
            "📷 <b>Результат проверки</b>\n\n"
            "Не удалось прочитать текст на фото.\n"
            "Попробуйте отправить фото крупнее и с лучшим качеством."
        )

    emoji = VERDICT_EMOJI.get(verdict, "🟡")
    title = VERDICT_TITLE.get(verdict, "Результат проверки")

    parts = [f"{emoji} <b>{title}</b>"]

    # Summary
    if summary := data.get("summary"):
        parts.append(f"\n{summary}")

    # Items
    items = data.get("items", [])
    if items:
        parts.append("\n<b>📋 Найденные элементы:</b>")
        for item in items[:10]:  # Limit to 10
            sev = SEVERITY_EMOJI.get(item.get("severity", "yellow"), "🟡")
            text = _escape(item.get("text", "?"))
            line = f"{sev} <code>{text}</code>"
            # Show where on the page this element is located
            if el_type := item.get("element_type"):
                label = ELEMENT_TYPE_LABEL.get(el_type.lower(), el_type)
                line += f"  [{label}]"
            if item.get("is_trademark"):
                line += " (товарный знак ✓)"
            elif item.get("is_common_term"):
                line += " (общепринятый термин ✓)"
            if issue := item.get("issue"):
                line += f" — {_escape(issue)}"
            if tr := item.get("suggested_translation"):
                line += f"\n   → Перевод: <i>{_escape(tr)}</i>"
            parts.append(line)

    # Fix required
    if fixes := data.get("fix_required"):
        if fixes:
            parts.append("\n<b>🚨 Что нужно исправить:</b>")
            for fix in fixes:
                parts.append(f"• {_escape(fix)}")

    # Fix recommended
    if recs := data.get("fix_recommended"):
        if recs:
            parts.append("\n<b>💡 Стоит уточнить:</b>")
            for rec in recs:
                parts.append(f"• {_escape(rec)}")

    # Financial risk
    if risk := data.get("financial_risk"):
        parts.append(f"\n<b>💰 Финансовый риск:</b>\n{_escape(risk)}")

    # Action plan
    if plan := data.get("action_plan"):
        if plan:
            parts.append("\n<b>📝 План действий:</b>")
            for i, step in enumerate(plan, 1):
                parts.append(f"{i}. {_escape(step)}")

    # Context / calming note
    if context := data.get("context"):
        parts.append(f"\n<b>ℹ️ Контекст:</b>\n<i>{_escape(context)}</i>")

    # Disclaimer
    parts.append(
        "\n⚠️ <i>Это автоматический анализ AI-помощника, а не юридическое заключение. "
        "Для точной оценки рекомендуем консультацию юриста.</i>"
    )

    return "\n".join(parts)


def get_verdict_color(data: dict) -> str | None:
    """Extract verdict color from parsed data."""
    v = data.get("verdict")
    if v in ("red", "yellow", "green"):
        return v
    return None


def _escape(text: str) -> str:
    """Escape HTML special characters."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
