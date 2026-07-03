from __future__ import annotations

from collections.abc import Iterable, Mapping


ScoredItems = Mapping[str, float] | Iterable[tuple[str, float]]


def apply_candidate_filters(
    scored_items: ScoredItems,
    *,
    top_k: int,
    whitelist: list[str] | None = None,
    blacklist: list[str] | None = None,
    seen_items: list[str] | None = None,
) -> list[str]:
    whitelist_set = set(whitelist) if whitelist is not None else None
    blocked = set(blacklist or []) | set(seen_items or [])

    normalized_scores = scored_items.items() if isinstance(scored_items, Mapping) else scored_items
    filtered: list[tuple[str, float]] = []

    for item_id, score in normalized_scores:
        if item_id in blocked:
            continue
        if whitelist_set is not None and item_id not in whitelist_set:
            continue
        filtered.append((item_id, float(score)))

    filtered.sort(key=lambda item_score: item_score[1], reverse=True)
    return [item_id for item_id, _ in filtered[:top_k]]