## Context

当前项目已经具备数据集生成、预处理、数据校验和 BERT 训练脚本，但历史实现存在三类断点：配置层可能引用参考项目 `04-bert`，`MODEL_PATH` 曾经使用 `.pt` 文件语义，而线上 `predictor.py` 没有真正加载训练后的 tokenizer、分类模型和 `label_mapping.json`。

本 change 的目标是把项目内模型训练与 API 推理做成可运行闭环：训练动作使用当前项目的数据集，训练时准备或复用项目内基础模型目录，生成 HuggingFace 标准模型目录和正式评估报告；线上预测在模型可用时使用 BERT softmax 分类，在模型不可用时明确降级到关键词兜底。

## Goals / Non-Goals

**Goals:**

- 移除对参考项目 `04-bert` 的运行时 fallback，训练和推理都不得从该目录读取模型资源。
- 统一 `MODEL_PATH` 为 HuggingFace 模型目录语义，例如 `backend/models/knowledge_bert`。
- 完整训练动作可以在项目内基础模型目录缺失时，通过 `--base-model-name` 初始化并缓存基础模型到项目内目录。
- 训练完成后产出模型权重、tokenizer、配置、`label_mapping.json` 和正式 `reports/evaluation_report.json`。
- 线上推理加载训练产物，并返回 BERT softmax 置信度和分类结果。
- 模型不可用时保留关键词兜底，并通过 `model_status`、健康检查等字段暴露状态。

**Non-Goals:**

- 不复用参考项目 `04-bert` 的代码、路径或已训练模型。
- 不在 Web 服务启动阶段自动训练模型。
- 不在本次 apply 中实际执行完整训练或下载/初始化基础模型。
- 不重构知识分类体系、数据集生成规则或前端训练页面。

## Decisions

### 决策 1：基础模型目录归属于当前项目

`BERT_PRETRAINED_PATH` 默认指向 `backend/models/bert-base-chinese`。如果该目录已经包含完整 tokenizer、配置和权重，训练脚本直接从该目录加载；如果目录缺失或不完整，dry-run 只报告完整训练时会准备基础模型，不写任何模型文件。

完整训练时，脚本使用 `--base-model-name` 指定的模型名称，默认 `bert-base-chinese`，通过 `transformers.from_pretrained` 初始化 tokenizer 和分类模型，并保存到项目内基础模型目录。这样避免依赖参考目录，同时不要求当前就手工初始化模型。

### 决策 2：训练产物使用 HuggingFace 标准目录

`MODEL_PATH` 指向 `backend/models/knowledge_bert`。训练脚本使用 `save_pretrained` 保存最佳模型和 tokenizer，推理模块使用同一目录执行 `from_pretrained`，并额外读取 `label_mapping.json`。

### 决策 3：训练报告由完整训练流程生成

完整训练结束后覆盖 `reports/evaluation_report.json`，记录训练参数、数据集规模、最佳 dev macro F1、test accuracy、test macro F1、classification_report、基础模型来源、模型目录和标签映射路径。dry-run 不生成或覆盖报告。

### 决策 4：推理模块懒加载模型并明确降级

`predictor.py` 只在 `MODEL_PATH` 目录完整且可加载时标记 `model_loaded=True`，并执行 tokenizer、模型前向计算、softmax、最大概率标签选择。模型缺失或加载失败时返回关键词兜底结果，并暴露 `model_status=keyword_fallback` 与加载错误。

## Risks / Trade-offs

- 完整训练首次执行可能需要网络下载 `bert-base-chinese`，如果网络不可用会失败；dry-run 不会提前下载。
- 首次训练会同时准备基础模型缓存和训练模型，耗时比只训练更长。
- 关键词兜底保证 MVP 可用，但不是正式模型能力；前端和健康检查必须展示模型状态。
- 训练报告只有完整训练完成后才是真实报告，当前占位报告不会被标记为完成任务。

## Migration Plan

1. 更新配置默认值：`MODEL_PATH=backend/models/knowledge_bert`，`BERT_PRETRAINED_PATH=backend/models/bert-base-chinese`。
2. 更新训练脚本：dry-run 只校验，完整训练时自动准备基础模型并保存正式训练产物。
3. 更新推理模块：从 `MODEL_PATH` 目录加载 tokenizer、模型和 `label_mapping.json`。
4. 删除模型占位符文件，避免被误判为可用模型。
5. 由用户后续手动执行完整训练命令，生成模型产物和正式报告。
6. 训练完成后再执行 API smoke test，确认 `model_status=bert`。