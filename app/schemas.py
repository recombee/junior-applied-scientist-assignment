from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.config import Settings


class RequestValidationError(ValueError):
    pass


@dataclass(frozen=True)
class RecommendationRequest:
    user_id: str | None
    interaction_history: list[str]
    top_k: int
    whitelist: list[str] | None
    blacklist: list[str] | None

    @classmethod
    def from_payload(
        cls,
        payload: Any,
        settings: Settings,
    ) -> "RecommendationRequest":
        if not isinstance(payload, dict):
            raise RequestValidationError("Request body must be a JSON object")

        top_k = _coerce_top_k(payload.get("top_k", settings.default_top_k), settings)
        user_id = _coerce_optional_id(payload.get("user_id"), "user_id")
        interaction_history = _coerce_item_list(
            payload.get("interaction_history", []),
            "interaction_history",
        )
        whitelist = _coerce_optional_item_list(payload.get("whitelist"), "whitelist")
        blacklist = _coerce_optional_item_list(payload.get("blacklist"), "blacklist")

        if user_id is None and not interaction_history:
            raise RequestValidationError("Provide either user_id or interaction_history")

        return cls(
            user_id=user_id,
            interaction_history=interaction_history,
            top_k=top_k,
            whitelist=whitelist,
            blacklist=blacklist,
        )


def _coerce_top_k(value: Any, settings: Settings) -> int:
    try:
        top_k = int(value)
    except (TypeError, ValueError) as exc:
        raise RequestValidationError("top_k must be an integer") from exc
    if top_k < 1:
        raise RequestValidationError("top_k must be at least 1")
    if top_k > settings.max_top_k:
        raise RequestValidationError(f"top_k must be at most {settings.max_top_k}")
    return top_k


def _coerce_optional_id(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise RequestValidationError(f"{field_name} must be a string ID")
    return str(value)


def _coerce_optional_item_list(value: Any, field_name: str) -> list[str] | None:
    if value is None:
        return None
    return _coerce_item_list(value, field_name)


def _coerce_item_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list):
        raise RequestValidationError(f"{field_name} must be a list of item IDs")
    ids: list[str] = []
    for item_id in value:
        if isinstance(item_id, bool) or not isinstance(item_id, (str, int)):
            raise RequestValidationError(f"{field_name} must contain only string item IDs")
        ids.append(str(item_id))
    return ids