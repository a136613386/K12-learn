# model-training-inference Specification

## Purpose
TBD - created by archiving change model-training-inference. Update Purpose after archive.
## Requirements
### Requirement: Project-owned BERT base model path
系统 SHALL 使用项目内自有基础 BERT 模型路径或显式配置的非参考路径初始化 tokenizer 和分类模型，并 MUST NOT 自动回退到参考项目 `04-bert` 目录。

#### Scenario: Default base model path is project-owned
- **WHEN** 未显式设置 `BERT_PRETRAINED_PATH`
- **THEN** 系统使用项目内默认路径作为基础 BERT 模型目录
- **THEN** 系统不会读取 `D:\xuweiqun\py_project\work_heima\大模型三阶段\01_投满分\04-bert` 下的任何模型资源

#### Scenario: Missing project base model is prepared during training
- **WHEN** 项目内基础 BERT 模型目录不存在或缺少必要 tokenizer/model 配置文件
- **THEN** dry-run 只报告训练时将通过 `--base-model-name` 准备基础模型，不生成任何模型文件
- **THEN** 完整训练动作使用 `--base-model-name` 初始化基础模型并缓存到项目内基础模型目录
- **THEN** 系统仍不会读取参考项目 `04-bert` 目录

### Requirement: Model path uses saved model directory semantics
系统 SHALL 将 `MODEL_PATH` 解释为 HuggingFace `save_pretrained` 模型目录，而不是单个 `.pt` 文件。

#### Scenario: Training writes to model directory
- **WHEN** 开发者执行完整 BERT 训练流程
- **THEN** 系统将最佳模型保存到 `MODEL_PATH` 指向的目录
- **THEN** 该目录包含可被 `from_pretrained` 加载的模型配置、权重、tokenizer 文件和 `label_mapping.json`

#### Scenario: Inference reads from same model directory
- **WHEN** 后端推理模块初始化模型
- **THEN** 系统从 `MODEL_PATH` 指向的同一目录读取 tokenizer、分类模型和 `label_mapping.json`
- **THEN** 系统不会要求存在 `knowledge_bert.pt` 文件才能判断模型可用

### Requirement: Full training produces real model artifacts
系统 SHALL 通过项目内训练脚本完成数据加载、模型创建、训练、验证集选择最佳模型、测试集评估和模型产物保存。

#### Scenario: Complete training run succeeds
- **WHEN** `train.txt`、`dev.txt`、`test.txt` 和 `class.txt` 可用
- **THEN** 训练脚本创建知识分类模型并执行至少一个 epoch 的训练
- **THEN** 训练脚本基于 dev macro F1 保存最佳模型
- **THEN** 训练脚本在 test 数据集上评估最终模型

#### Scenario: Dry run does not create artifacts
- **WHEN** 开发者使用 `--dry-run` 执行训练脚本
- **THEN** 系统只校验数据、依赖和路径配置
- **THEN** 系统不会生成或覆盖模型权重、tokenizer 文件或正式评估报告

### Requirement: Formal evaluation report
系统 SHALL 在完整训练完成后生成正式评估报告，报告 MUST 包含训练参数、数据集规模、标签数量、最佳 dev 指标、test accuracy、test macro F1、classification_report、模型目录和基础模型路径。

#### Scenario: Evaluation report replaces placeholder report
- **WHEN** 完整训练流程成功结束
- **THEN** `reports/evaluation_report.json` 包含真实训练产生的指标字段
- **THEN** 报告不再声明自己是训练骨架报告或占位报告

#### Scenario: Report captures training parameters
- **WHEN** 开发者查看 `reports/evaluation_report.json`
- **THEN** 报告包含 `epochs`、`batch_size`、`max_length`、`learning_rate` 或等价训练参数
- **THEN** 报告包含 `train_count`、`dev_count`、`test_count` 和 `label_count`

### Requirement: API inference uses BERT softmax predictions
系统 SHALL 在训练模型可用时通过 BERT tokenizer、分类模型和 softmax 概率生成知识分类预测结果。

#### Scenario: Predictor loads trained model
- **WHEN** `MODEL_PATH` 指向的模型目录包含完整训练产物
- **THEN** 推理模块加载 tokenizer、分类模型和 `label_mapping.json`
- **THEN** `predictor.py` 的模型预测路径不再直接返回关键词兜底结果

#### Scenario: Prediction returns softmax confidence
- **WHEN** API 收到题目文本并且训练模型已加载
- **THEN** 系统对题目文本执行 tokenizer 编码和模型前向计算
- **THEN** 系统使用 softmax 最大概率作为置信度
- **THEN** 系统返回与最大概率索引对应的知识分类标签

#### Scenario: Model unavailable degrades explicitly
- **WHEN** 模型目录不存在或模型加载失败
- **THEN** 系统可以使用关键词兜底预测维持 MVP 可用性
- **THEN** 系统必须能明确暴露模型未加载状态，避免将兜底结果误认为真实 BERT 结果

### Requirement: Placeholder artifacts are not treated as real model outputs
系统 SHALL 清理、替换或隔离模型占位符和占位评估报告，且 MUST NOT 将占位符文件作为真实模型、tokenizer、标签映射或正式评估报告使用。

#### Scenario: Placeholder model file does not mark model loaded
- **WHEN** `backend/models` 下只存在 `knowledge_bert.placeholder.json` 或等价说明文件
- **THEN** 推理模块判断训练模型不可用
- **THEN** 系统不会尝试把该占位符作为模型权重加载

#### Scenario: Placeholder report is replaced after training
- **WHEN** 完整训练流程成功生成正式报告
- **THEN** 旧的占位评估报告被替换为真实评估 JSON
- **THEN** 报告内容可用于判断本次训练的模型质量

