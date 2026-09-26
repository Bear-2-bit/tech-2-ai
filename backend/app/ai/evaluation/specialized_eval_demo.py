from app.ai.evaluation.specialized_metrics import (
    execution_accuracy,
    hit_at_k,
    task_success,
    tool_selection_accuracy,
)


def main():
    rag_score = hit_at_k(
        retrieved_ids=[
            "employee_handbook.pdf",
            "refund_policy.pdf",
            "product_manual.pdf",
        ],
        expected_id="refund_policy.pdf",
        k=3,
    )

    sql_score = execution_accuracy(
        actual_rows=[
            ["华东", 270000.0],
        ],
        expected_rows=[
            ["华东", 270000.0],
        ],
    )

    tool_score = tool_selection_accuracy(
        actual_tools=[
            "database_query",
            "calculator",
        ],
        expected_tools=[
            "database_query",
            "calculator",
        ],
    )

    workflow_score = task_success([
        rag_score == 1.0,
        sql_score == 1.0,
        tool_score == 1.0,
    ])

    print("RAG Hit@3:", rag_score)
    print("SQL Execution Accuracy:", sql_score)
    print("Tool Selection Accuracy:", tool_score)
    print("Workflow Success:", workflow_score)


if __name__ == "__main__":
    main()