## ADDED Requirements

### Requirement: Model comparison report
系统 SHALL 支持在 BERT 与 FastText 训练产物都存在时生成模型对比报告，用于判断 MVP 当前应使用哪条训练链路。

#### Scenario: Compare BERT and FastText reports
- **WHEN** `reports/evaluation_report.json` 和 `reports/fasttext_evaluation_report.json` 都存在且包含真实评估指标
- **THEN** 系统读取两份报告中的 accuracy、macro F1、训练参数、数据规模和模型路径
- **THEN** 系统生成 `reports/model_comparison_report.json`
- **THEN** 对比报告包含 BERT 与 FastText 的 test accuracy、test macro F1、训练耗时、推理耗时和模型文件大小

#### Scenario: BERT report is missing or placeholder
- **WHEN** BERT 评估报告不存在、被删除或仍是占位报告
- **THEN** 系统仍可生成只包含 FastText 实测结果的对比报告
- **THEN** 系统在报告中明确标记 BERT 指标不可用，而不是使用占位指标参与比较

#### Scenario: FastText report is missing
- **WHEN** FastText 评估报告不存在
- **THEN** 系统输出明确错误，说明需要先运行 FastText 训练评估
- **THEN** 系统不会生成误导性的空对比报告

### Requirement: Hybrid BERT FastText inference fallback
系统 SHALL 在在线错题归类链路中默认使用项目内 BERT 模型；当 BERT 不可用，或 BERT softmax 置信度低于 `BERT_CONFIDENCE_THRESHOLD` 默认 `0.8` 时，系统 MUST 自动使用项目内 FastText 模型作为兜底分类器。

#### Scenario: BERT confidence is high enough
- **WHEN** BERT 模型成功加载，并且对当前题目的 softmax 置信度大于或等于 `0.8`
- **THEN** 系统返回 BERT 的标签、置信度和 `model_status=bert`
- **THEN** 系统不会调用 FastText 覆盖该结果

#### Scenario: BERT is unavailable
- **WHEN** BERT 模型目录缺失、文件不完整或加载失败
- **THEN** 系统调用 FastText 模型完成分类
- **THEN** 结果返回 `model_status=fasttext_fallback` 和 `fallback_reason=bert_unavailable`

#### Scenario: BERT confidence is below threshold
- **WHEN** BERT 模型成功加载，但当前题目的 softmax 置信度低于 `0.8`
- **THEN** 系统调用 FastText 模型完成兜底分类
- **THEN** 结果返回 `model_status=fasttext_fallback`、`fallback_reason=bert_confidence_below_threshold` 和 BERT/FastText 置信度字段

#### Scenario: BERT and FastText are unavailable
- **WHEN** BERT 与 FastText 都不可用
- **THEN** 系统允许使用关键词兜底作为最后降级路径
- **THEN** 结果 MUST 明确返回 `model_status=keyword_fallback`

#### Scenario: Frontend displays inference chain in Chinese
- **WHEN** 前端收到分类结果或健康检查结果
- **THEN** 前端使用中文展示 BERT、FastText、关键词兜底状态
- **THEN** 当前分类结果 MUST 展示最终采用的模型和兜底原因
