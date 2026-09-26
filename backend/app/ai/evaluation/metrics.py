def contains_expected(
    actual: str,
    expected: str,
) -> tuple[bool, float]:
    passed = expected.lower() in actual.lower()

    return passed, 1.0 if passed else 0.0