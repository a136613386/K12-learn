## Why

当前 raw 目录中已有 `data_org1.csv` 和 `merged_questions_label_id.xlsx` 两份原始题目/标签数据，但它们还没有形成稳定的数据清洗入口，无法保证后续 BERT 训练使用的问题文本与知识标签一一对应。该 change 需要建立一条可重复执行的数据清洗与切分链路，把 raw 源数据转成 `data/processed` 下的训练、验证、测试数据。

## What Changes

- 新增原始数据清洗能力，对 `data/raw/data_org1.csv` 和 `data/raw/merged_questions_label_id.xlsx` 进行读取、编码处理、字段标准化、空值过滤、重复数据处理和标签校验。
- 统一识别题目文本与标签字段，输出适合模型训练的 `text\tlabel_id` 格式数据。
- 将清洗后的样本按标签分层切分为 `train.txt`、`dev.txt` 和 `test.txt`，并生成 `class.txt`。
- 生成清洗报告，记录源文件、原始行数、有效行数、过滤原因、标签分布、切分数量和输出路径。
- 保留源文件不变，不直接修改 raw 数据。

## Capabilities

### New Capabilities
- `data-org-create`: 覆盖 raw 原始题目数据清洗、标签识别、训练集切分和 processed 产物生成的行为要求。

### Modified Capabilities
- `data-create`: 补充模型数据来源，明确可以从 raw 原始题库文件清洗生成训练/验证/测试数据。

## Impact

- 影响数据脚本：新增或调整 `backend/scripts` 下的数据清洗脚本。
- 影响数据目录：读取 `data/raw/data_org1.csv`、`data/raw/merged_questions_label_id.xlsx`，写入 `data/processed/train.txt`、`dev.txt`、`test.txt`、`class.txt`。
- 影响报告目录：新增清洗处理报告，例如 `reports/data_org_preprocess_report.txt` 或 JSON 报告。
- 影响模型训练：后续 `train_bert.py` 将可以直接使用清洗后的 processed 数据。