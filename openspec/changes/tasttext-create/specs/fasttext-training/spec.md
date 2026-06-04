## ADDED Requirements

### Requirement: FastText dataset preprocessing
系统 SHALL 从现有 `data/processed/train.txt`、`data/processed/dev.txt`、`data/processed/test.txt` 和 `data/processed/class.txt` 生成 FastText 可训练数据，并 MUST 保持原始 processed 文件不被破坏。

#### Scenario: Convert processed splits to FastText format
- **WHEN** 开发者执行 FastText 数据预处理脚本
- **THEN** 系统读取 `train.txt`、`dev.txt`、`test.txt` 中的 `text\tlabel_id` 数据
- **THEN** 系统输出 FastText 格式行：`__label__{label_id} {tokenized_text}`
- **THEN** 系统保留 `class.txt` 的 15 个分类名称和顺序不变

#### Scenario: Reject invalid processed data
- **WHEN** 任一 processed 样本缺少文本、标签不是整数或标签不在 `0..14`
- **THEN** 系统终止 FastText 预处理流程
- **THEN** 系统输出明确错误，指出文件名、行号和失败原因

### Requirement: Chinese tokenization for FastText
系统 SHALL 为中文题目文本提供稳定的分词/切分策略，使 FastText 能有效学习生物学术语、题干和选项中的分类信号。

#### Scenario: Character level tokenization is available
- **WHEN** FastText 预处理脚本处理中文文本
- **THEN** 系统至少支持字符级切分，将中文连续文本转换为 FastText 可学习的 token 序列
- **THEN** 系统保留英文、数字、遗传符号和常见生物学缩写的可读性

#### Scenario: Tokenization mode is recorded
- **WHEN** FastText 预处理完成
- **THEN** 系统在报告中记录本次使用的分词模式
- **THEN** 系统记录输入样本数、输出样本数和过滤数量

### Requirement: FastText model training
系统 SHALL 使用 FastText 算法基于处理后的 train/dev/test 数据训练 15 类知识点分类模型。

#### Scenario: Train FastText classifier
- **WHEN** FastText 训练脚本被执行且依赖可用
- **THEN** 系统使用 FastText train 数据训练监督分类模型
- **THEN** 系统使用 dev 数据评估并选择训练参数或记录 dev 指标
- **THEN** 系统将模型保存到项目内 FastText 模型目录

#### Scenario: FastText dependency unavailable
- **WHEN** FastText Python 依赖不可用或当前平台无法加载 FastText
- **THEN** 系统输出明确错误，说明缺失依赖和建议安装方式
- **THEN** 系统不会生成空模型或伪造评估报告

### Requirement: FastText evaluation report
系统 SHALL 在 FastText 训练完成后生成正式评估报告，报告 MUST 包含训练参数、数据规模、accuracy、macro F1、classification_report、模型路径和分词模式。

#### Scenario: Evaluate on dev and test splits
- **WHEN** FastText 模型训练完成
- **THEN** 系统在 dev 数据上计算 accuracy 和 macro F1
- **THEN** 系统在 test 数据上计算 accuracy、macro F1 和 classification_report
- **THEN** 系统将结果写入 `reports/fasttext_evaluation_report.json`

#### Scenario: Report contains reproducibility fields
- **WHEN** 开发者查看 FastText 评估报告
- **THEN** 报告包含训练参数，例如 epoch、learning rate、wordNgrams、minCount 或等价 FastText 参数
- **THEN** 报告包含 train/dev/test 样本数、标签数量、模型文件路径和数据预处理文件路径

### Requirement: FastText inference compatibility artifact
系统 SHALL 保存 FastText 推理所需的模型、标签映射和分词配置，使后续 API 接入时可以加载同一套产物。

#### Scenario: Save complete FastText artifacts
- **WHEN** FastText 训练成功完成
- **THEN** 系统保存 FastText 模型文件
- **THEN** 系统保存 `label_mapping.json`
- **THEN** 系统保存或记录分词配置，保证训练与推理使用一致处理方式
