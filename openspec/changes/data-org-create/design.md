## Context

`data/raw/data_org1.csv` 已修复为 UTF-8 CSV，`data/raw/merged_questions_label_id.xlsx` 是带有题目与标签关系的 Excel 原始数据。当前项目已有 `data/processed/class.txt`，其中固定包含 15 个知识分类，且训练脚本、推理标签映射和前端展示都依赖这 15 个分类的顺序。

本 change 的目标是创建一条独立、可重复执行的数据清洗链路，将 `data_org1.csv` 和 `merged_questions_label_id.xlsx` 中的问题文本、选项、答案解析和标签识别为统一训练样本，并输出到 `data/processed/train.txt`、`dev.txt`、`test.txt`。`class.txt` 不允许根据 raw 数据重新推导分类体系。

## Goals / Non-Goals

**Goals:**

- 读取 `data/raw/data_org1.csv` 和 `data/raw/merged_questions_label_id.xlsx`。
- 自动处理 CSV 编码、Excel 读取、字段名差异和空值。
- 准确识别问题文本和标签 ID，必要时合并题干、选项、答案解析形成模型输入文本。
- 以当前 `data/processed/class.txt` 为唯一分类标准，保持 15 个分类名称和顺序不变。
- 将源数据标签规范化为当前训练标签 ID 范围 `0..14`。
- 过滤无题目、无标签、标签非法、重复或明显异常的数据。
- 按标签分层切分为 `train.txt`、`dev.txt`、`test.txt`。
- 输出清洗报告，便于检查有效样本数、过滤原因和标签分布。

**Non-Goals:**

- 不修改 raw 源文件内容。
- 不重新定义知识点体系。
- 不从 raw 文件生成新的 `class.txt` 分类列表。
- 不在本 change 中训练 BERT 模型。
- 不把缺失标签的数据通过模型自动猜测标签。

## Decisions

### 决策 1：建立专用脚本而不是复用生成样本脚本

新增脚本建议命名为 `backend/scripts/preprocess_data_org.py`。它只负责 raw 真实题库清洗，不和 `generate_model_dataset.py` 的生成样本逻辑混在一起，避免真实数据和模板生成数据互相污染。

### 决策 2：`class.txt` 作为不可变分类标准

脚本启动时必须读取当前 `data/processed/class.txt`，校验其恰好包含 15 个非空分类。清洗输出中的标签 ID 必须落在 `0..14`，并且含义与 `class.txt` 的行号一致。脚本不得按 raw 数据中的知识点名称重新排序、重命名或扩展分类。

### 决策 3：统一输出 `text\tlabel_id`

模型训练脚本当前读取 `data/processed/*.txt` 的 `text\tlabel_id` 格式，因此清洗后的输出继续使用该格式。`text` 应优先包含题干；若存在选项、答案或解析，可按固定顺序拼接，提升分类上下文完整性。

### 决策 4：源标签需要规范化到当前 15 类

`data_org1.csv` 优先使用 `knowledge_points_id` 字段。该字段如果是 `1..15` 的知识点序号，应转换为训练标签 `0..14`。`merged_questions_label_id.xlsx` 优先使用 `label_id` 字段；若字段值已经在 `0..14`，则直接使用。任何无法明确映射到当前 15 类的样本都必须过滤并写入报告。

### 决策 5：分层切分保证各标签覆盖

数据切分采用按 `label_id` 分组后的分层切分，默认比例建议为 `train=80%`、`dev=10%`、`test=10%`。每个标签样本较少时，脚本必须尽量保证 dev/test 至少保留样本，同时不得生成空训练集。

### 决策 6：报告优先可审计

报告应包含源文件、读取行数、有效行数、去重数量、过滤原因、每个标签的样本数、train/dev/test 数量、class.txt 校验结果和输出路径。报告格式可以是 `.txt` 或 `.json`，但字段必须稳定，便于后续排查。

## Risks / Trade-offs

- [Risk] 两个源文件字段不完全一致 -> 通过字段映射表处理，并在报告中记录实际识别到的字段。
- [Risk] raw 标签 ID 起始值与训练标签 ID 不一致 -> 针对源文件制定显式规范化规则，统一输出 `0..14`。
- [Risk] 同一题在两个源文件重复出现 -> 使用规范化文本和标签组合去重，报告记录去重数量。
- [Risk] Excel 中多行文本、全角空格或不可见字符影响模型输入 -> 清洗时统一空白字符，保留必要语义为普通空格。
- [Risk] raw 文件包含当前 15 类之外的标签 -> 过滤该样本并在报告中记录。

## Migration Plan

1. 新增 raw 数据清洗脚本。
2. 读取并校验当前 `data/processed/class.txt`，确认 15 个分类不变。
3. 实现字段映射、文本规范化、标签校验和去重。
4. 实现分层切分并写入 `data/processed/train.txt`、`dev.txt`、`test.txt`。
5. 原样保留或原样写回 `data/processed/class.txt`。
6. 生成清洗报告。
7. 运行脚本并验证输出文件格式与训练脚本兼容。