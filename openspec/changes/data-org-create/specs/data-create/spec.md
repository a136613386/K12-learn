## ADDED Requirements

### Requirement: Raw question sources can produce model splits
系统 SHALL 支持从 raw 原始题库文件清洗生成模型训练所需的 processed 数据，作为 `model_dataset.csv` 生成链路之外的真实题库数据来源。

#### Scenario: Build model splits from raw question files
- **WHEN** 开发者执行 raw 题库清洗脚本
- **THEN** 系统从 `data/raw/data_org1.csv` 和 `data/raw/merged_questions_label_id.xlsx` 生成 processed 数据
- **THEN** 输出文件兼容现有 BERT 训练入口读取的 `train.txt`、`dev.txt`、`test.txt` 和 `class.txt`