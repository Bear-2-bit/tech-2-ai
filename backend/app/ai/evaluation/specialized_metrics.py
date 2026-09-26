def hit_at_k(
    retrieved_ids: list[str],
    expected_id: str,
    k: int,
) -> float:
    return 1.0 if expected_id in retrieved_ids[:k] else 0.0


def execution_accuracy(
    actual_rows: list,
    expected_rows: list,
) -> float:
    return 1.0 if actual_rows == expected_rows else 0.0


def tool_selection_accuracy(
    actual_tools: list[str],
    expected_tools: list[str],
) -> float:
    return 1.0 if set(actual_tools) == set(expected_tools) else 0.0


def task_success(
    required_checks: list[bool],
) -> float:
    return 1.0 if all(required_checks) else 0.0

def contains_all_score(
    actual: str,
    expected_terms: list[str],
) -> float:
    if not expected_terms:
        return 1.0

    matched = sum(
        term.lower() in actual.lower()
        for term in expected_terms
    )

    return matched / len(expected_terms)