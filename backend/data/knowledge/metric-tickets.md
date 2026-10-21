# 售后指标口径

> tech-2-ai 合成业务资料 · 版本 v2 · 生效日期 2025-04-01

月度售后新增工单数按service_tickets.opened_at统计，包括open和resolved。未关闭工单需单独筛选status='open'。产品工单通过product_id关联产品，部门通过order_id关联订单；新增量和当前存量属于不同口径，应分别描述。

