from app.ai.evaluation.metrics import contains_expected
from app.ai.evaluation.models import EvalCase, EvalResult


def run_case(
    case: EvalCase,
    actual: str,
) -> EvalResult:
    passed, score = contains_expected(
        actual=actual,
        expected=case.expected,
    )

    return EvalResult(
        case_id=case.id,
        passed=passed,
        score=score,
        actual=actual,
        expected=case.expected,
    )


def main():
    cases = [
        EvalCase(
            id="sales-001",
            input="哪个部门销售额最高？",
            expected="华东",
        ),
        EvalCase(
            id="sales-002",
            input="哪个部门销售额最低？",
            expected="华北",
        ),
    ]

    actual_outputs = [
        "根据销售数据，华东部门销售额最高。",
        "销售额最低的是华北部门。",
    ]

    results = []

    for case, actual in zip(
        cases,
        actual_outputs,
    ):
        result = run_case(
            case,
            actual,
        )

        results.append(result)

        print(
            case.id,
            "PASS" if result.passed else "FAIL",
            result.score,
        )

    accuracy = sum(
        result.score for result in results
    ) / len(results)

    print("\nAccuracy:", accuracy)


if __name__ == "__main__":
    main()