# 学习入口

从 backend 目录运行，先启动后端。例子通过公开 API 调用正式业务，不复制另一套实现。

```powershell
python -m examples.run llm --engine native --question "解释流式输出"
python -m examples.run llm --engine langchain --question "解释结构化输出"
python -m examples.run rag
python -m examples.run nl2sql
python -m examples.run agent
python -m examples.run workflow
python -m examples.run eval
python -m examples.run traces
```

原生普通、流式和手写校验见 `app/modules/llm/native.py`；框架对照见 `langchain.py`。
入库、检索、回答见 `app/modules/rag/`；只读 SQL 执行见 `app/modules/nl2sql/database.py`。
Agent 工具循环见 `app/modules/agent/service.py`；固定步骤的图见 `app/modules/workflow/graph.py`。

旧阶段示例已移出运行主链。本次升级前的源码与示例保存在本地 `data/backups/pre-upgrade-*.zip`，Git 历史亦可查阅。
