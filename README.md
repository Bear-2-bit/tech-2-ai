# tech-2-ai

> 一个面向 **AI Application Engineering（AI 应用工程）** 的全栈学习与工程实践项目。  
> 从原生 DeepSeek API 出发，逐步走通 **LLM Engineering → Structured Output → LangChain → Embedding → RAG → Tool Calling → NL2SQL → Agent → LangGraph → Workflow → Evaluation → Tracing** 的完整技术链。

---

## 项目简介

`tech-2-ai` 不是一个单纯的聊天机器人，也不是为了堆叠 AI 框架而设计的 Demo。

它的目标是：

> **用一个真实可运行的前后端项目，系统掌握现代 AI 应用从“模型调用”到“Agent / Workflow / Evaluation / Observability”的完整工程路径。**

项目采用极简前端 + FastAPI 后端，把主要精力集中在 AI 能力本身。

核心原则：

- 先理解机制，再使用框架
- 先走通最小链路，再逐步工程化
- 原生 DeepSeek API → LangChain → LangGraph
- Service 负责业务编排，`ai/` 提供可复用 AI 能力
- 具体 Provider / Vector Store 由 Composition Root 组装
- 不为了“看起来高级”引入无意义的复杂架构
- Evaluation 和 Tracing 是 AI 应用的一等公民
- AI 系统必须拥有安全边界、失败处理和可观测能力

---

## 技术栈

### Frontend

- Vue 3
- Vite
- Axios
- Vue Router

### Backend

- Python
- FastAPI
- Pydantic
- AsyncIO

### LLM / AI

- DeepSeek API
- LangChain
- LangGraph
- Structured Output
- Tool Calling
- Agent
- Workflow

### Retrieval / RAG

- BAAI/bge-small-zh-v1.5
- BAAI/bge-reranker-base
- Qdrant
- Semantic Search
- Query Rewrite
- Rerank
- Citation

### Data / Evaluation / Observability

- SQLite
- NL2SQL
- Golden Dataset
- Custom Evaluation Metrics
- LangSmith
- Application Trace Summary

---

# 核心能力

## 1. Chat

最基础的 LLM 应用链路：

```text
Vue
 ↓
POST /api/chat
 ↓
ChatService
 ↓
LLMProvider
 ↓
DeepSeek
 ↓
Answer
```

该阶段重点解决：

- `messages`
- system / user / assistant
- temperature
- max_tokens
- timeout
- retry
- exception
- token usage
- latency
- streaming
- SSE

项目首先直接理解 DeepSeek API，然后再封装统一 `LLMProvider`。

---

## 2. Structured Output

把自然语言结果转换成可验证的数据结构：

```text
User Input
 ↓
LLM
 ↓
Structured Output
 ↓
Pydantic Validation
 ↓
Typed Result
```

用于：

- 信息提取
- SQL 生成
- Workflow Planner
- Business Analysis Report

核心思想：

> **AI 输出不是“能解析 JSON 就够了”，而是必须满足业务 Schema。**

---

## 3. Semantic Search

实现纯向量检索：

```text
Query
 ↓
Embedding
 ↓
Qdrant
 ↓
Top-K Documents
```

Embedding：

```text
BAAI/bge-small-zh-v1.5
```

主要用于理解：

- Document
- Chunk
- Embedding
- Vector
- Vector Store
- Retriever
- Similarity Search

Search 不负责回答问题，只负责返回相关文档。

---

## 4. Enterprise RAG

完整 RAG 链路：

```text
User Question
      ↓
Query Rewrite
      ↓
Embedding
      ↓
Qdrant Candidate Retrieval
      ↓
CrossEncoder Rerank
      ↓
Top-K Documents
      ↓
Context Construction
      ↓
LLM
      ↓
Answer + Citation
```

当前支持：

- PDF / TXT / Markdown 知识导入
- Chunking
- Embedding
- Qdrant
- Query Rewrite
- Candidate Retrieval
- CrossEncoder Rerank
- Top-K
- Metadata
- Citation
- Grounded Answer

Reranker：

```text
BAAI/bge-reranker-base
```

RAG 会尽量约束模型：

> 只根据知识库内容回答；知识不足时明确说明无法确定。

---

## 5. Tool Calling

项目实现多个 Tool：

```text
calculator
knowledge_search
database_query
```

基本流程：

```text
User
 ↓
LLM
 ↓
Tool Call
 ↓
Python Tool
 ↓
Tool Result
 ↓
ToolMessage
 ↓
LLM
 ↓
Final Answer
```

重点区分：

```text
Tool
≠
ToolCall
≠
ToolMessage
```

同时明确：

```text
Tool Calling
≠
Agent
```

---

## 6. NL2SQL

把自然语言问题转换成 SQLite 查询：

```text
Natural Language
      ↓
Database Schema
      ↓
LLM Structured Output
      ↓
SQL Validation
      ↓
Read-only Execution
      ↓
SQL Result
```

当前核心安全策略：

- 只允许 `SELECT`
- 禁止 `INSERT`
- 禁止 `UPDATE`
- 禁止 `DELETE`
- 禁止 `DROP`
- 禁止 `ALTER`
- 禁止 `CREATE`
- 单条 SQL
- 限制最大返回行数
- SQLite Read-only 思路

示例问题：

```text
哪个部门销售额最高？
```

系统会：

1. 读取数据库 Schema
2. 生成 SQL
3. 校验 SQL
4. 执行只读查询
5. 返回 columns / rows / row_count

---

## 7. Agent

Agent 基于 LangChain `create_agent` 构建，并通过 Tool 完成自主决策。

```text
User Goal
   ↓
Agent
   ↓
Reason / Decide
   ↓
Select Tool
   ↓
Execute Tool
   ↓
Observe Result
   ↓
Continue or Stop
   ↓
Final Answer
```

当前 Tool：

```text
calculator
knowledge_search
database_query
```

并设置：

- Tool Call Limit
- Recursion Limit
- Runtime Error Handling

架构上进一步拆分：

```text
AgentService
    ↓
AgentRuntime
    ↓
LangChain Agent
    ↓
Tools
```

其中：

```text
AgentService
= 业务使用方式

AgentRuntime
= Agent 执行引擎
```

---

## 8. LangGraph

项目通过独立 Demo 和真实 Workflow 理解 LangGraph：

- State
- Node
- Edge
- Conditional Edge
- ToolNode
- MessagesState
- Loop
- Checkpoint
- `thread_id`
- Human-in-the-loop
- `interrupt`
- `Command(resume=...)`

重点理解：

> `create_agent` 背后本身就运行在 LangGraph Runtime 上。

---

## 9. Business Analysis Workflow

项目实现了一个综合型经营分析 Workflow。

```text
                  ┌──────────────┐
                  │    Planner   │
                  └──────┬───────┘
                         │
             ┌───────────┴───────────┐
             ↓                       ↓
        SQL Analysis             RAG Analysis
             ↓                       ↓
             └───────────┬───────────┘
                         ↓
                    Synthesis
                         ↓
                Structured Report
```

Planner 会把用户问题拆分为：

```text
sql_question
rag_question
```

然后并行执行：

- SQLite 数据分析
- 企业知识库检索

LangGraph Join 会等待两个分支都完成后再进入 Synthesis。

最终输出：

```text
title
summary
key_findings
recommendations
```

这一部分将：

```text
NL2SQL
+
RAG
+
Structured Output
+
LangGraph
```

组合成一个真正的 AI Workflow。

---

## 10. Evaluation

AI 系统不能只依靠“感觉不错”。

项目建立：

```text
Golden Dataset
+
Actual Output
+
Expected Output
+
Metric
+
Eval Runner
```

当前覆盖：

- RAG Hit@K
- NL2SQL Execution Accuracy
- Tool Selection Accuracy
- Agent Task Success
- Workflow Component Evaluation
- Workflow End-to-End Evaluation

Evaluation Service 支持逐 Case 执行：

```text
Case 1
Case 2
Case 3
...
```

单个 Case 失败不会让整个评估任务直接崩溃。

核心思想：

> **Evaluation 回答的是：AI 系统到底有多好。**

---

## 11. Tracing / Observability

项目使用 LangSmith 对复杂 AI Workflow 进行追踪。

典型 Trace：

```text
business_analysis
│
├── planner
├── sql
├── rag
└── synthesis
```

可观察：

- Input
- Output
- Latency
- Token Usage
- Metadata
- Error
- Nested Runs

项目同时维护轻量级本地 Trace Summary：

```text
trace_id
langsmith_trace_id
name
status
started_at
latency_ms
input_tokens
output_tokens
total_tokens
input_preview
error
```

LangSmith：

```text
负责详细 Trace Tree
```

本地 `/traces`：

```text
负责 Workbench 快速查看摘要
```

核心区别：

```text
Evaluation
= 系统表现怎么样？

Tracing
= 为什么会这样？
```

---

# 页面

前端目前提供以下 Workbench 页面：

| Route | 功能 |
|---|---|
| `/chat` | LLM Chat |
| `/extract` | Structured Extraction |
| `/search` | Semantic Search |
| `/rag` | Enterprise RAG |
| `/sql` | NL2SQL |
| `/agent` | Agent |
| `/workflow` | Business Analysis Workflow |
| `/eval` | Evaluation |
| `/traces` | Trace Summary |

`App.vue` 提供基础导航，因此无需手动输入 URL。

---

# API

主要 API：

| Endpoint | Description |
|---|---|
| `POST /api/chat` | LLM Chat |
| `POST /api/extraction` | Structured Extraction |
| `POST /api/search` | Semantic Search |
| `POST /api/rag` | RAG Query |
| `POST /api/sql` | NL2SQL |
| `POST /api/agent` | Agent |
| `POST /api/workflow` | Business Analysis Workflow |
| `POST /api/eval` | Evaluation |
| `GET /api/traces` | Trace Summary |

FastAPI Swagger：

```text
http://127.0.0.1:8000/docs
```

---

# 项目架构

整体分层：

```text
Frontend
   ↓
Axios
   ↓
FastAPI Router
   ↓
Pydantic Schema
   ↓
Service
   ↓
AI Infrastructure
   ↓
LLM / Vector DB / Database / Tools
```

Backend 核心职责：

```text
Router
→ HTTP

Schema
→ 输入输出合同

Service
→ Use Case / 业务编排

ai/
→ 可复用 AI 能力

dependencies.py
→ Composition Root

core/
→ Config / Exception / 基础工程能力
```

---

# Backend Dependency Direction

推荐依赖方向：

```text
main.py
   ↓
api/
   ↓
dependencies.py
   ↓
services/
   ↓
ai/
   ↓
External Systems
```

其中：

```text
schemas/
core/
```

属于共享基础层。

组件不应该反向 import：

```text
app.dependencies
```

所有具体实现都在 Composition Root 中组装。

---

# Dependency Injection

例如：

```text
RAGService
```

不应该关心：

```text
必须是 DeepSeek
必须是 Qdrant
```

而应该依赖：

```text
BaseChatModel
VectorStore
```

具体实现由：

```text
dependencies.py
```

决定。

因此架构可以表达为：

```text
RAGService
    ↓
BaseChatModel
    ↑
ChatDeepSeek


RAGService
    ↓
VectorStore
    ↑
QdrantVectorStore
```

核心原则：

> **业务代码依赖能力，不依赖具体厂商。**

---

# Lazy Initialization

重量级对象通过 `@lru_cache` 延迟创建，例如：

- LLM Model
- Embedding
- Vector Store
- Reranker
- SQL Service
- RAG Service
- Agent Runtime
- Workflow
- Evaluation Service
- Trace Store

避免：

```text
启动一个普通 Chat API
↓
却初始化所有 Embedding / Reranker / Qdrant / Workflow
```

这可以降低：

- 启动成本
- 模型加载成本
- 无关组件故障传播
- 模块耦合

---

# 项目目录

核心目录结构：

```text
tech-2-ai/
│
├── backend/
│   │
│   ├── app/
│   │   ├── main.py
│   │   ├── dependencies.py
│   │   │
│   │   ├── api/
│   │   │   ├── chat.py
│   │   │   ├── extraction.py
│   │   │   ├── search.py
│   │   │   ├── rag.py
│   │   │   ├── sql.py
│   │   │   ├── agent.py
│   │   │   ├── workflow.py
│   │   │   ├── eval.py
│   │   │   └── traces.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── chat.py
│   │   │   ├── extraction.py
│   │   │   ├── search.py
│   │   │   ├── rag.py
│   │   │   ├── sql.py
│   │   │   ├── agent.py
│   │   │   ├── workflow.py
│   │   │   ├── eval.py
│   │   │   └── trace.py
│   │   │
│   │   ├── services/
│   │   │   ├── chat_service.py
│   │   │   ├── extraction_service.py
│   │   │   ├── search_service.py
│   │   │   ├── rag_service.py
│   │   │   ├── knowledge_ingestion_service.py
│   │   │   ├── sql_service.py
│   │   │   ├── agent_service.py
│   │   │   ├── workflow_service.py
│   │   │   └── eval_service.py
│   │   │
│   │   ├── ai/
│   │   │   ├── providers/
│   │   │   ├── retrieval/
│   │   │   ├── sql/
│   │   │   ├── tools/
│   │   │   ├── agent/
│   │   │   ├── workflows/
│   │   │   ├── evaluation/
│   │   │   ├── tracing/
│   │   │   ├── embeddings.py
│   │   │   └── vector_store.py
│   │   │
│   │   └── core/
│   │       ├── config.py
│   │       └── exceptions.py
│   │
│   └── data/
│       ├── business.db
│       └── eval/
│           └── golden_cases.json
│
└── frontend/
    └── src/
        ├── api/
        ├── router/
        ├── views/
        ├── App.vue
        └── main.js
```

> 项目中可能仍保留部分阶段性 Demo / 历史实现，用于记录学习过程；它们不是最终运行主链的一部分。

---

# 快速启动

## 1. Clone

```bash
git clone <your-repository-url>
cd tech-2-ai
```

---

## 2. Backend

进入后端：

```powershell
cd backend
```

创建虚拟环境：

```powershell
python -m venv .venv
```

激活：

```powershell
.\.venv\Scripts\Activate.ps1
```

安装依赖：

```powershell
pip install -r requirements.txt
```

启动：

```powershell
fastapi dev .\app\main.py
```

Backend：

```text
http://127.0.0.1:8000
```

Swagger：

```text
http://127.0.0.1:8000/docs
```

---

## 3. Qdrant

本地推荐通过 Docker 启动：

```bash
docker run -d \
  --name tech2ai-qdrant \
  -p 6333:6333 \
  qdrant/qdrant
```

访问：

```text
http://127.0.0.1:6333
```

如果已经存在 Qdrant 容器：

```bash
docker start tech2ai-qdrant
```

---

## 4. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend：

```text
http://localhost:5173
```

---

# Environment Variables

在：

```text
backend/.env
```

创建配置：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key

LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=tech-2-ai
LANGSMITH_TRACING=false
```

默认基础配置由：

```text
app/core/config.py
```

管理，例如：

```text
DEEPSEEK_BASE_URL
DEEPSEEK_MODEL
FRONTEND_ORIGIN
LLM_TIMEOUT_SECONDS
LLM_MAX_RETRIES
EMBEDDING_MODEL_NAME
RERANKER_MODEL_NAME
QDRANT_URL
QDRANT_COLLECTION_NAME
```

---

# LangSmith Tracing

默认建议：

```env
LANGSMITH_TRACING=false
```

需要临时开启时，在 PowerShell：

```powershell
$env:LANGSMITH_TRACING="true"
```

然后重新启动 Backend。

关闭当前终端环境变量：

```powershell
Remove-Item Env:LANGSMITH_TRACING
```

项目采用：

```text
.env
↓
load_dotenv
↓
os.environ
↓
LangSmith SDK
```

而应用配置主要通过：

```text
.env
↓
Pydantic Settings
↓
settings
```

管理。

---

# Database

项目当前使用：

```text
backend/data/business.db
```

作为 NL2SQL 示例数据库。

数据库主要用于：

- Schema Awareness
- SQL Generation
- Read-only Query
- SQL Evaluation
- Agent database tool
- Workflow structured-data branch

它不是整个项目的业务 CRUD 数据库。

---

# Evaluation Dataset

Golden Dataset：

```text
backend/data/eval/golden_cases.json
```

用于：

- SQL Evaluation
- Agent Evaluation
- Workflow Evaluation

后续可继续扩展：

- RAG Cases
- Tool Cases
- Citation Cases
- Regression Cases

---

# Engineering Principles

这个项目特别强调以下工程原则：

```text
Probabilistic Model
        ↓
Deterministic Engineering System
```

LLM 本身具有不确定性。

真正可靠的 AI Application 必须在外围建立：

- Schema
- Validation
- Retry
- Timeout
- Exception
- Tool Boundary
- SQL Safety
- Workflow Control
- Evaluation
- Tracing
- Logging
- Configuration
- Dependency Injection

因此：

> **AI 应用工程不是“调用一次模型 API”，而是围绕概率模型构建可控制、可验证、可观察的软件系统。**

---

# Demo vs Production Code

项目在学习过程中保留过大量 Demo。

Demo 的目标：

```text
证明 Happy Path 可以工作
```

工程代码需要进一步考虑：

```text
异常
超时
重试
安全
依赖注入
Lazy Init
Validation
Failure Isolation
Observability
Evaluation
```

当前项目定位更准确地说是：

> **AI Application Engineering Workbench / 工程化学习型技术原型**

它已经具备较完整的 AI 应用工程骨架，但不等于可以未经改造直接作为大规模生产系统上线。

---

# Learning Roadmap

项目按照以下顺序完成：

```text
Phase 0
Architecture Design
    ↓
Phase 1
DeepSeek Fundamentals
    ↓
Phase 2
LLM Engineering
    ↓
Phase 3
Structured Output
    ↓
Phase 4
LangChain
    ↓
Phase 5
Embedding + Semantic Search
    ↓
Phase 6
Enterprise RAG
    ↓
Phase 7
Tool Calling
    ↓
Phase 8
NL2SQL
    ↓
Phase 9
Agent
    ↓
Phase 10
LangGraph
    ↓
Phase 11
Workflow
    ↓
Phase 12
Evaluation
    ↓
Phase 13
Tracing / Observability
    ↓
Phase 14
Final Refactor
```

---

# Current Status

```text
Phase 0   Architecture               ✅
Phase 1   DeepSeek Fundamentals      ✅
Phase 2   LLM Engineering            ✅
Phase 3   Structured Output          ✅
Phase 4   LangChain                  ✅
Phase 5   Embedding + Search         ✅
Phase 6   Enterprise RAG             ✅
Phase 7   Tool Calling               ✅
Phase 8   NL2SQL                     ✅
Phase 9   Agent                      ✅
Phase 10  LangGraph                  ✅
Phase 11  Workflow                   ✅
Phase 12  Evaluation                 ✅
Phase 13  Tracing / Observability    ✅
Phase 14  Final Refactor             ✅
```

主技术链已经完整走通。

当前仍存在少量非阻塞型技术债，例如：

- 部分历史 Demo 尚未全部迁移到独立 `examples/`
- Extraction 历史实现仍有进一步收口空间
- 当前 UI 以功能调试为主
- 尚未针对大规模并发和正式生产环境进行系统压测

---

# What This Project Is Not

为了保持学习重点，项目刻意没有投入大量精力在：

- 用户注册
- JWT
- RBAC
- 复杂 CRUD
- 微服务
- Kubernetes
- 复杂 UI Design System
- 大规模业务数据库建模

这些并不是不重要，而是它们不属于本项目的核心目标。

`tech-2-ai` 的主角始终是：

```text
AI Application Engineering
```

---

# Security Notes

请勿提交：

```text
.env
API Key
LangSmith Key
真实生产数据库
敏感企业资料
```

`.gitignore` 至少应该包含：

```gitignore
.venv/
.env
__pycache__/
*.py[cod]
```

NL2SQL 即使有 Prompt 限制，也不应该只依赖 LLM 自觉。

正式系统还应继续加强：

- SQL Parser
- AST Validation
- Database Read-only Account
- Query Timeout
- Row Limit
- Table / Column Allowlist
- Tool Allowlist
- Authentication
- Authorization
- Rate Limit

---

# Future Directions

这个项目已经完成主学习使命，后续更推荐“深化已有能力”，而不是继续无限堆框架。

值得继续深入的方向：

```text
RAG Quality
→ Hybrid Search / Rerank / Query Understanding

Agent Reliability
→ State / Memory / HITL / Guardrails

Evaluation
→ Larger Golden Dataset / Regression Eval

Observability
→ Trace + Metrics + Cost + Quality

Backend
→ Concurrency / Queue / Cache / Production Deployment

Frontend
→ Better AI Debugging Workbench

Architecture
→ Provider / Runtime / Workflow Abstraction
```

---

# Final Architecture View

```text
                         ┌──────────────────┐
                         │      Vue 3       │
                         │ AI Workbench UI  │
                         └────────┬─────────┘
                                  │
                                Axios
                                  │
                         ┌────────▼─────────┐
                         │     FastAPI      │
                         │      Router      │
                         └────────┬─────────┘
                                  │
                         ┌────────▼─────────┐
                         │     Schemas      │
                         │    Pydantic      │
                         └────────┬─────────┘
                                  │
                         ┌────────▼─────────┐
                         │     Services     │
                         │ Business / UseCase│
                         └────────┬─────────┘
                                  │
           ┌──────────────────────┼──────────────────────┐
           │                      │                      │
           ▼                      ▼                      ▼
        LLM / Agent          RAG / Retrieval         NL2SQL
           │                      │                      │
           ▼                      ▼                      ▼
       DeepSeek                 Qdrant                 SQLite
           │                      │                      │
           └──────────────────────┼──────────────────────┘
                                  │
                                  ▼
                           LangGraph Workflow
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
               Evaluation                  Tracing
                                              │
                                           LangSmith
```

---

# Summary

`tech-2-ai` 最终想回答的不是：

> “如何调用一个大模型？”

而是：

> **如何把 LLM、RAG、Tool、SQL、Agent、Workflow、Evaluation 和 Tracing 组合成一个真正的软件系统？**

整个项目最终形成：

```text
LLM
+
Structured Output
+
RAG
+
Tools
+
NL2SQL
+
Agent
+
LangGraph
+
Workflow
+
Evaluation
+
Observability
+
Software Engineering
```

这就是 `tech-2-ai`。