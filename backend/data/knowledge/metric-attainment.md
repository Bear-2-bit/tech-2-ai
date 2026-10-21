# 目标达成率口径

> tech-2-ai 合成业务资料 · 版本 v2 · 生效日期 2025-04-01

sales_targets按department_id和month记录月度目标，metric_key='net_sales'。达成率为净销售额除以净销售目标。汇总多个部门时先汇总实际和目标，再计算比例，不平均各部门百分比。没有目标或目标为零时返回空值。

