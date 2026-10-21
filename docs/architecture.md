# 架构与责任

这是一个单用户、单进程的模块化全栈应用。学习路径保留在 LLM 模块，业务模块统一采用框架调用。

## 依赖方向

`main.py → modules/*/router.py → 本模块业务 → resources/core`。
Agent 和 Workflow 可调用 RAG 与 NL2SQL；这两个基础模块不反向依赖调用者。
评估调用业务模块；业务只依赖 core 中的追踪与存储，不导入评估实现。

各模块不强制使用同样数量的文件；没有业务作用的透传 Service、Manager、Repository 不创建。

## 资源生命周期

配置由 get_settings() 缓存读取。路由导入不创建模型客户端、不连接 Qdrant、不导入 Torch。
Embedding、Reranker、Qdrant 在 resources.py 中按需初始化，使用锁保护首次并发创建。
本地推理与文件解析在线程执行，SQL 自带 SQLite 执行预算。应用关闭时取消任务并关闭已创建客户端。

LangChain 使用现成模型与结构化输出接口；不再为业务重复包装一套 Provider 抽象。native.py 保留原生机制用于教学对照。

## 任务、追踪与日志

后台任务返回 run_id，运行树在 app.db 中保存。任务与节点使用同一记录结构，通过 parent_id 关联。
request_id 进入运行元数据；Token 从实际模型回调记录并汇总到父运行，未知值保持 NULL。
根运行耗时使用墙钟时间，不能累加并行子节点耗时。

事件不包含原始请求正文或密钥。业务结果、Agent 会话和证据在本地数据库保存，因其包含用户输入，真实数据接入应按实际部署要求管理访问和保留期。

## 文档状态

processing → ready；新版本发布时，旧 ready → superseded。
失败新版本 → error，不影响此前 ready。删除时所有版本先变为 deleting，清理后变为 deleted。
processing/deleting 的同名文档不能再次写入。重复内容、配置和元数据返回已有版本。

Chunk ID 为基于版本与片段序号的稳定 UUID。检索只允许当前模型对应的已发布版本；指定 as_of 时，按生效范围选择适用版本。不同模型切换时需重新入库，维度变更使用新集合。
文档元数据与向量没有跨库事务，通过状态发布、幂等 ID、失败清理和重试维持一致。

## SQL 边界

SQLGlot 验证单条 SELECT/CTE/集合查询，限制业务表及数据库限定名；SQLite 只读 URI、authorizer 和 progress handler 构成执行边界。
Schema 读取使用独立只读连接并始终关闭。金额按整数分累计，明确订单日期与退款日期的差异。

## Agent 与 Workflow

Agent 使用 LangChain create_agent 和工具调用上限，中间 SQL、文档与计算证据留存；结构化结论必须引用实际证据。会话最多 12 轮，同会话禁止并发调查。

Workflow 使用 LangGraph 并行读取确定性指标与知识，再合成报告。核心 KPI 不交给模型临时定义。报告最多修正一次，无政策依据、非法引用或数字异常均标记 incomplete。

当前未引入多租户、任意写库工具、外部消息发送、多 Agent、分布式队列或微服务。
