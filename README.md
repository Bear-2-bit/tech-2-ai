# tech-2-ai

一个从原生模型机制走向完整业务应用的全栈 AI 工程学习项目。业务主线是**机器人企业销售与售后运营**，数据为可复现的合成演示数据，不代表真实企业业绩。

Vue 3 + FastAPI。原生 SDK 只用于 LLM 对照教学；后续模型调用使用 LangChain，月报编排使用 LangGraph。

## 六个模块

| 页面 | 功能 | 代码 |
| --- | --- | --- |
| `/llm` | 原生/框架 × 普通/流式/结构化输出 | `backend/app/modules/llm` |
| `/rag` | 知识入库 → 检索实验 → 有引用的回答 | `backend/app/modules/rag` |
| `/nl2sql` | 了解业务 Schema，自然语言生成安全只读 SQL | `backend/app/modules/nl2sql` |
| `/agent` | 有会话、有证据、有预算的问题调查助手 | `backend/app/modules/agent` |
| `/workflow` | 固定口径、固定步骤的月度经营复盘 | `backend/app/modules/workflow` |
| `/engineering` | 评估、执行追踪、脱敏日志 | `backend/app/modules/engineering` |

Agent 适合“先查总量，再根据结果下钻”的开放调查；Workflow 适合固定月份和范围的标准报告。二者复用知识检索和安全查询能力。

## 快速启动（Windows / PowerShell）

需要 Python 3.13 和符合 Vite 8 要求的 Node.js。本项目不要求 Docker；默认使用 Qdrant 本地持久化模式。

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

已有 `.env` 时保留原文件，不执行覆盖。编辑 `DEEPSEEK_API_KEY`；无密钥仍可启动后端、浏览 Schema 和运行记录。

```powershell
# 初始化关联业务数据；原 business.db 会自动备份到 data/backups
python -m scripts.seed

# 显式准备嵌入模型；日常启动不会自动下载模型
python -m scripts.prepare_models
# 需要重排时再准备第二个模型
python -m scripts.prepare_models --reranker

# 单进程启动，默认本地 Qdrant 模式不能使用多个 worker
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

另一个终端启动前端：

```powershell
cd frontend
npm ci
npm run dev
```

打开 `http://localhost:5173`；API 文档为 `http://127.0.0.1:8000/docs`。

进入 RAG → 知识管理，点击“导入项目示例知识”。项目包含 28 份产品、政策、口径、流程和案例资料。任务进度与失败原因可在页面查看；重复导入会去重。

## 配置

唯一配置入口是 `backend/app/core/config.py` 的 Pydantic Settings，读取系统环境变量和 `backend/.env`，环境变量优先。应用没有 `load_dotenv()`；`python-dotenv` 仍可能作为 Pydantic Settings 的间接依赖安装。

| 配置 | 默认 / 作用 |
| --- | --- |
| `DEEPSEEK_API_KEY` | 模型请求时才校验，不阻止本地功能启动 |
| `DEEPSEEK_MODEL` | `deepseek-flash`，可按账户支持的模型修改 |
| `LLM_TIMEOUT_SECONDS` | 单次模型请求 45 秒 |
| `LLM_MAX_RETRIES` | SDK 网络重试 1 次；原生结构修正最多 2 次 |
| `OPERATION_TIMEOUT_SECONDS` | 普通任务总预算 180 秒 |
| `MODEL_LOCAL_FILES_ONLY` | `true`，未缓存时给出准备提示 |
| `QDRANT_MODE` | `local` 或 `server` |
| `QDRANT_LOCAL_PATH` | 默认 `backend/data/qdrant` |
| `QDRANT_URL` | server 模式默认 `http://127.0.0.1:6333` |
| `QDRANT_COLLECTION_NAME` | 新索引 `tech2ai_documents_v2`，不覆盖旧集合 |
| `LANGSMITH_TRACING` | 默认关闭；开启时显式传入配置 |
| `MAX_JOBS` | 后台并发上限 4；不提供无限排队 |

如需 Qdrant 服务模式，将 `QDRANT_MODE=server`，再启动自有 Qdrant 服务。嵌入模型变更需要重新入库；维度不同应使用新的集合名，不自动清空旧集合。

## 数据与指标

`business.db` 有 departments、customers、products、orders、order_items、refunds、service_tickets、sales_targets 八张表，固定随机种子为 20260930，覆盖 2025-04 至 2026-09。

金额使用整数分。销售按完成订单日期统计，退款按退款完成日期统计，净销售额等于本期销售额减本期退款。关联两个一对多数据源前必须分别聚合，避免重复求和。详情可在 NL2SQL 页面和 `backend/data/knowledge/metric-*.md` 查看。

```powershell
# 另外生成一个可手工核对的小样例，不替换正式演示数据
python -m scripts.seed --fixture --output data/business-small.db
```

存储责任：

| 存储 | 内容 |
| --- | --- |
| `data/business.db` | 业务事实，NL2SQL 只读 |
| `data/app.db` | 文档元数据、会话、运行、评估结果 |
| `data/knowledge/*.md` | 随仓库提供的知识材料 |
| `data/knowledge/originals` | 上传原件的不可变版本 |
| `data/qdrant` | 本地向量索引，可改为服务模式 |

原件、索引和元数据的备份应配套保存。删除文档会先使所有版本停止检索，再删除向量和原件；失败后可重试。新版本只有全部写入成功才发布，旧版本仍可用于按生效日期检索。

## API

| 模块 | 主要接口 |
| --- | --- |
| LLM | `POST /api/llm/{native,langchain}/{chat,stream,extract}` |
| RAG | `GET /api/rag/status`、`GET/POST /api/rag/documents`、`DELETE /api/rag/documents/{document_id}` |
| RAG | `POST /api/rag/search`、`POST /api/rag/ask`、`POST /api/rag/seed` |
| NL2SQL | `GET /api/nl2sql/schema`、`POST /api/nl2sql/query` |
| Agent | `GET/POST /api/agent/sessions`、`POST /api/agent/runs` |
| Workflow | `GET/POST /api/workflow/reports` |
| Engineering | `GET /api/engineering/runs`、`GET /api/engineering/runs/{id}` |
| Engineering | `POST /api/engineering/runs/{id}/cancel`、`GET /api/engineering/logs` |
| Engineering | `GET /api/engineering/evaluations/cases`、`POST /api/engineering/evaluations` |

入库、Agent、月报和评估返回 HTTP 202 与 `run_id`，通过统一运行接口获取进度及结果。它们为单进程任务，重启后未结束任务标记 interrupted，需要重新提交；不承诺跨进程恢复执行。评估总预算 900 秒，每个用例最多 120 秒，已完成用例即时持久化。

流式接口使用 POST SSE，事件为 delta、done、error。客户端只有收到 done 才认定完整结束；停止按钮会取消请求。后台入库取消需要等待当前本地批处理退出，未完成版本不会发布。

旧前端地址 `/chat`、`/extract`、`/search`、`/sql`、`/eval`、`/traces` 有跳转；后端旧 API 已合并，外部调用者需迁移。

## 验证与开发

```powershell
cd backend
python -m pip install -r requirements-dev.txt
python -m pytest -q
ruff check app scripts tests
ruff format --check app scripts tests

# 使用真实配置，调用少量模型与本地知识能力，输出脱敏结果
python -m scripts.smoke --rag --business
```

Qdrant 本地模式下，运行真实冒烟脚本前先停止后端，避免两个进程同时占用同一个索引目录；通过页面/API 验证时无需停止。初始化业务数据库也应在后端停止时执行。

```powershell
cd frontend
npm test
npm run format:check
npm run build
```

自动化测试使用临时 SQLite、Qdrant 内存模式与测试模型，不需要密钥、不下载模型、不调用外部 API。真实冒烟脚本单独运行，会消耗少量 API 用量；测试通过与模型质量评估是两件事。

评估集有 48 条：24 SQL、12 检索、4 LLM、4 Agent、4 Workflow。默认每次只执行所选类型前 5 条。SQL 比较执行结果而非 SQL 字符串；RAG 检查真实来源命中；Agent 分别检查状态、工具和证据；月报检查数字与引用。引用 ID 有效不等于语义支持已被自动证明，复杂结论仍需人工抽检。

依赖只编辑 `backend/requirements.in`，使用 `pip-compile requirements.in --output-file requirements.txt` 更新锁定结果；开发工具在 `requirements-dev.txt`。后端 Ruff、前端 Prettier 均采用 120 列，短参数和短调用尽量一行。

更多设计与迁移说明见 [docs/architecture.md](docs/architecture.md) 和 [docs/upgrade.md](docs/upgrade.md)，本轮实际验收见 [docs/verification.md](docs/verification.md)。
