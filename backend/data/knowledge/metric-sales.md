# 销售额口径

> tech-2-ai 合成业务资料 · 版本 v2 · 生效日期 2025-04-01

销售额统计orders.status='completed'且order_date落在统计期内的订单，金额为order_items.quantity乘以unit_price_cents的总和。取消和待完成订单均不计入。金额字段为整数分，展示人民币元时除以100.0。客户或产品维度分析也沿用此口径。

