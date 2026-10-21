# tech-2-ai

基于 Vue 3、FastAPI、LangChain 和 LangGraph 的 AI 应用工作台，业务主线为机器人企业销售与售后运营。

## 功能

| 页面 | 内容 |
| --- | --- |
| `/llm` | 原生 SDK 与 LangChain 的普通、流式、结构化输出 |
| `/rag` | 知识管理、文档入库、检索和引用回答 |
| `/nl2sql` | 自然语言查询业务数据库，展示 SQL 与结果 |
| `/agent` | 支持连续追问和证据追溯的业务调查 |
| `/workflow` | 固定指标口径的月度经营复盘 |
| `/engineering` | AI 评估、调用追踪和运行日志 |

## 目录

```text
backend/
  app/
    core/          配置、错误处理、存储、日志与任务
    modules/       六个功能模块，各自包含路由和业务代码
    main.py        应用入口
    resources.py   模型与向量库资源的按需初始化
  data/
    business.db    业务数据
    app.db         文档版本、会话、运行与评估记录
    knowledge/     知识材料及上传原件
    eval/          评估功能使用的数据集
    qdrant/        本地向量索引
  scripts/         数据初始化、模型准备
frontend/
  src/
    api/           后端接口调用
    components/    公共界面组件
    composables/   请求与后台任务状态
    router/        页面路由
    views/         六个模块的页面
```

业务数据库与知识材料均为合成演示数据，覆盖 2025-04 至 2026-09。金额使用整数分；销售按完成订单日期统计，退款按退款完成日期统计。

## 启动

需要 Python 3.13 和满足 Vite 8 要求的 Node.js。

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

首次配置时复制 `.env.example` 为 `.env`，填写 `DEEPSEEK_API_KEY`。已有 `.env` 时保留原文件。

```powershell
# 首次初始化；已有业务数据库时无需重复执行
python -m scripts.seed

# 首次准备本地嵌入模型；使用重排时增加 --reranker
python -m scripts.prepare_models

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

另开终端启动前端：

```powershell
cd frontend
npm ci
npm run dev
```

页面：`http://localhost:5173`。API 文档：`http://127.0.0.1:8000/docs`。

在 RAG 页点击“导入项目示例知识”即可导入内置资料。默认使用 Qdrant 本地持久化模式，后端按单进程启动；需要独立 Qdrant 服务时设置 `QDRANT_MODE=server` 和 `QDRANT_URL`。

配置统一由 `backend/app/core/config.py` 读取。模型只在使用时加载，日常启动不下载模型。初始化数据库前应停止后端，旧数据库会自动备份。

## 维护

运行依赖在 `backend/requirements.in` 声明，`requirements.txt` 保存锁定版本。可安装 `requirements-dev.txt` 使用 Ruff 和 pip-tools。

```powershell
# backend 目录
ruff format app scripts
ruff check app scripts
pip-compile requirements.in --output-file requirements.txt

# frontend 目录
npm run format
npm run format:check
npm run build
```

代码采用 110 列格式化，短调用保持紧凑，长参数和模板按结构换行。`data/eval/golden_cases.json` 属于评估功能的运行数据，通过工程页面执行。
