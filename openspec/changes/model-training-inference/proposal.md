## Why

当前项目已经具备数据集生成、预处理和 BERT 训练脚本雏形，但模型路径仍可能回退到参考目录 `04-bert`，线上预测也没有真正加载训练后的 BERT 模型。这个 change 需要把“项目内自有基础模型路径、完整训练、正式评估报告、API 推理”串成可验证闭环，避免继续依赖占位符和关键词兜底作为主流程。

## What Changes

- 移除对参考目录 `D:\xuweiqun\py_project\work_heima\大模型三阶段\01_投满分\04-bert` 的路径依赖，基础 BERT 模型必须来自项目内自有路径或显式配置路径。
- 将 `MODEL_PATH` 从 `.pt` 文件语义修正为 HuggingFace `save_pretrained` 目录语义，默认指向项目内训练模型目录。
- 跑通完整训练流程，生成真实模型产物，包括模型权重、tokenizer、配置文件和 `label_mapping.json`。
- 让 `predictor.py` 真正加载 tokenizer、训练后的分类模型和标签映射，API 预测返回 BERT softmax 分类结果。
- 生成正式评估报告，记录训练参数、数据集规模、accuracy、macro F1、classification_report、模型路径和标签映射信息。
- 清理或替换项目中的模型占位符和占位报告，避免占位文件被误认为可用模型或真实评估结果。

## Capabilities

### New Capabilities
- `model-training-inference`: 覆盖项目内 BERT 模型路径、训练产物、评估报告、线上推理加载和占位符处理的行为要求。

### Modified Capabilities
- `project-architecture`: 明确模型训练与推理属于后端机器学习子系统，且不得依赖参考项目目录作为运行时资源。

## Impact

- 影响后端配置：`.env`、`.env.example`、`backend/app/config.py` 中的 `MODEL_PATH` 和 `BERT_PRETRAINED_PATH` 语义。
- 影响训练脚本：`backend/scripts/train_bert.py` 的训练参数记录、模型保存目录、报告内容和占位符处理。
- 影响推理代码：`backend/app/ml/predictor.py` 需要从关键词兜底主流程切换为真实 BERT softmax 推理。
- 影响模型产物目录：`backend/models/bert-base-chinese/`、`backend/models/knowledge_bert/` 或等价项目内路径。
- 影响报告目录：`reports/evaluation_report.json` 必须成为真实训练评估报告。
- 影响依赖校验：需要确认 `torch`、`transformers`、`scikit-learn` 可用于训练与推理。
