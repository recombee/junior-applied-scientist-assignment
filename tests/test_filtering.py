from app.filtering import apply_candidate_filters


def test_apply_candidate_filters_honors_blacklist_and_seen_items():
    scores = {"a": 0.8, "b": 0.9, "c": 0.7, "d": 0.6}

    recommendations = apply_candidate_filters(
        scores,
        top_k=3,
        blacklist=["b"],
        seen_items=["a"],
    )

    assert recommendations == ["c", "d"]


def test_apply_candidate_filters_limits_to_whitelist():
    scores = {"a": 0.8, "b": 0.9, "c": 0.7}

    recommendations = apply_candidate_filters(scores, top_k=5, whitelist=["a", "c"])

    assert recommendations == ["a", "c"]


def test_apply_candidate_filters_blacklist_takes_precedence_over_whitelist():
    scores = {"a": 0.8, "b": 0.9}

    recommendations = apply_candidate_filters(
        scores,
        top_k=5,
        whitelist=["a", "b"],
        blacklist=["b"],
    )

    assert recommendations == ["a"]


def test_apply_candidate_filters_handles_alphanumeric_asins():
    scores = {"006240749X": 0.9, "B08F4GYM8W": 0.8}

    recommendations = apply_candidate_filters(scores, top_k=2)

    assert recommendations == ["006240749X", "B08F4GYM8W"]