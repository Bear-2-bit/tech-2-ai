"""Exercise the same API as the UI, without importing or initializing unrelated capabilities."""

import argparse
import json
import time
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("module", choices=["llm", "rag", "nl2sql", "agent", "workflow", "eval", "traces"])
    parser.add_argument("--server", default="http://127.0.0.1:8000")
    parser.add_argument("--engine", choices=["native", "langchain"], default="langchain")
    parser.add_argument("--question", default="查询2026年9月华东已完成订单数量")
    args = parser.parse_args()

    def call(path, body=None):
        request = Request(
            args.server + path,
            data=json.dumps(body).encode() if body is not None else None,
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=190) as response:
            return json.load(response)

    paths = {
        "llm": (f"/api/llm/{args.engine}/chat", {"messages": [{"role": "user", "content": args.question}]}),
        "rag": ("/api/rag/ask", {"query": "机器人A保修期与保修范围是什么？"}),
        "nl2sql": ("/api/nl2sql/query", {"question": args.question}),
        "agent": ("/api/agent/runs", {"query": args.question}),
        "workflow": ("/api/workflow/reports", {"month": "2026-09", "department_id": 1}),
        "eval": ("/api/engineering/evaluations", {"types": ["sql"], "limit": 2}),
        "traces": ("/api/engineering/runs", None),
    }
    result = call(*paths[args.module])
    if isinstance(result, dict) and "run_id" in result and result.get("status") in {"running", "queued"}:
        deadline = time.monotonic() + 920
        while time.monotonic() < deadline:
            result = call(f"/api/engineering/runs/{result.get('run_id') or result['id']}")
            if result["status"] not in {"running", "queued"}:
                break
            time.sleep(1)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
