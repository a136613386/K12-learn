## ADDED Requirements

### Requirement: Raw source files are loaded safely
系统 SHALL 从 `data/raw/data_org1.csv` 和 `data/raw/merged_questions_label_id.xlsx` 读取原始题库数据，并正确处理 CSV 编码、Excel 单元格文本、多行内容和空值。

#### Scenario: Load raw CSV and Excel files
- **WHEN** 开发者执行 raw 数据清洗脚本
- **THEN** 系统读取 `data/raw/data_org1.csv`
- **THEN** 系统读取 `data/raw/merged_questions_label_id.xlsx`
- **THEN** 系统不会修改 raw 源文件

#### Scenario: Missing raw source file
- **WHEN** 任一必需 raw 源文件不存在
- **THEN** 系统终止清洗流程
- **THEN** 系统返回明确错误，指出缺失的源文件路径

### Requirement: Existing class file is the canonical label set
系统 SHALL 使用当前 `data/processed/class.txt` 作为唯一分类标准，并 MUST 保持其中 15 个分类名称和顺序不变。

#### Scenario: Class file is validated before preprocessing
- **WHEN** raw 数据清洗脚本启动
- **THEN** 系统读取当前 `data/processed/class.txt`
- **THEN** 系统校验该文件恰好包含 15 个非空分类
- **THEN** 系统以行号 `0..14` 作为训练标签 ID 映射

#### Scenario: Class file remains unchanged after preprocessing
- **WHEN** raw 数据清洗脚本执行完成
- **THEN** `data/processed/class.txt` 的 15 个分类名称和顺序与执行前完全一致
- **THEN** 系统不会从 raw 文件重新生成、重命名、重排或新增分类

### Requirement: Question text and label are identified accurately
系统 SHALL 从原始数据中准确识别题目文本和标签 ID，并将题干、选项、答案和解析按稳定规则组合为模型输入文本。

#### Scenario: Identify fields from data_org1
- **WHEN** `data_org1.csv` 包含 `question`、`option`、`answer`、`analysis` 和 `knowledge_points_id` 字段
- **THEN** 系统使用这些字段生成训练文本
- **THEN** 系统将 `knowledge_points_id` 规范化为当前 `class.txt` 对应的训练标签 ID

#### Scenario: Identify fields from merged questions
- **WHEN** `merged_questions_label_id.xlsx` 包含 `stem`、`options`、`answer`、`answer_detail` 和 `label_id` 字段
- **THEN** 系统使用这些字段生成训练文本
- **THEN** 系统将 `label_id` 规范化为当前 `class.txt` 对应的训练标签 ID

#### Scenario: Invalid label row is rejected
- **WHEN** 某一行标签为空、不是整数或无法映射到 `0..14`
- **THEN** 系统不会将该行写入训练样本
- **THEN** 系统在清洗报告中记录过滤原因和数量

### Requirement: Cleaned samples are normalized and deduplicated
系统 SHALL 对题目文本进行清洗、规范化和去重，避免空文本、重复样本和明显异常样本进入模型训练集。

#### Scenario: Normalize text fields
- **WHEN** 题目字段包含多余空白、换行、全角空格或字段前缀
- **THEN** 系统将其规范化为适合模型训练的单行文本
- **THEN** 系统保留题干、选项、答案和解析中的有效语义信息

#### Scenario: Deduplicate samples
- **WHEN** 两个源文件中存在相同或规范化后相同的问题文本和标签
- **THEN** 系统只保留一条训练样本
- **THEN** 系统在清洗报告中记录去重数量

### Requirement: Processed train dev test files are generated
系统 SHALL 将清洗后的样本按标签分层切分，并生成 `data/processed/train.txt`、`data/processed/dev.txt` 和 `data/processed/test.txt`。

#### Scenario: Generate processed split files
- **WHEN** raw 数据清洗成功完成
- **THEN** 系统写入 `data/processed/train.txt`
- **THEN** 系统写入 `data/processed/dev.txt`
- **THEN** 系统写入 `data/processed/test.txt`
- **THEN** 每一行均为 `text\tlabel_id` 格式
- **THEN** 每个 `label_id` 均在 `0..14` 范围内

#### Scenario: Split files match canonical class mapping
- **WHEN** processed 数据生成完成
- **THEN** `train.txt`、`dev.txt` 和 `test.txt` 中的标签 ID 均按当前 `class.txt` 行号解释
- **THEN** 输出数据不会产生第 16 类或其他额外分类

### Requirement: Cleaning report is generated
系统 SHALL 在清洗完成后生成报告，记录源文件、读取行数、有效样本数、过滤原因、标签分布、切分数量、`class.txt` 校验结果和输出路径。

#### Scenario: Report contains audit fields
- **WHEN** raw 数据清洗脚本执行完成
- **THEN** 系统生成清洗报告
- **THEN** 报告包含每个源文件的读取行数和有效行数
- **THEN** 报告包含 train/dev/test 的样本数和每个标签的样本数
- **THEN** 报告说明 `class.txt` 已校验且分类数量为 15