from __future__ import annotations

import re
import unicodedata


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFC", text)
    return re.sub(r"\s+", " ", normalized.strip().lower())


def _extract_words(text: str) -> set[str]:
    normalized = _normalize(text)
    words = re.findall(r"[\w]+", normalized, re.UNICODE)
    return set(w for w in words if len(w) >= 2)


def _source_span_overlap(
    variant_text: str,
    source_title: str,
    source_body: str,
    min_overlap: int = 1,
) -> bool:
    variant_words = _extract_words(variant_text)
    source_words = _extract_words(f"{source_title} {source_body}")
    overlap = variant_words & source_words
    return len(overlap) >= min_overlap


def _has_citation(text: str, citations: list[str]) -> bool:
    text_lower = text.lower()
    for url in citations:
        if url and url.lower() in text_lower:
            return True
    return False


def validate_attribution(
    variant_a_text: str,
    variant_b_text: str,
    source_title: str,
    source_body: str,
    citations: list[str],
) -> bool:
    def _variant_ok(text: str) -> bool:
        if _has_citation(text, citations):
            return True
        return _source_span_overlap(text, source_title, source_body)
    return _variant_ok(variant_a_text) and _variant_ok(variant_b_text)
