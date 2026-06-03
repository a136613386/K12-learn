## 1. 源文件读取

- [x] 1.1 新增 `backend/scripts/preprocess_data_org.py`，定义 raw 输入路径和 processed 输出路径。
- [x] 1.2 实现 `data/raw/data_org1.csv` 的 UTF-8 CSV 读取，读取失败时给出明确错误。
- [x] 1.3 实现 `data/raw/merged_questions_label_id.xlsx` 的 Excel 读取，读取失败时给出明确错误。
- [x] 1.4 增加源文件存在性校验，不存在时终止流程并输出缺失路径。

## 2. 分类标准与标签识别

- [x] 2.1 读取当前 `data/processed/class.txt`，校验恰好包含 15 个非空分类。
- [x] 2.2 确保清洗脚本不会根据 raw 文件重写、重排、重命名或新增 `class.txt` 分类。
- [x] 2.3 为 `data_org1.csv` 实现字段映射：`question`、`option`、`answer`、`analysis`、`knowledge_points_id`。
- [x] 2.4 为 `merged_questions_label_id.xlsx` 实现字段映射：`stem`、`options`、`answer`、`answer_detail`、`label_id`。
- [x] 2.5 实现标签 ID 规范化，将源标签映射到当前 `class.txt` 行号范围 `0..14`。
- [x] 2.6 过滤空标签、非整数标签、无法映射到 `0..14` 的非法标签。

## 3. 文本清洗与样本合并

- [x] 3.1 实现文本规范化，处理多余空白、换行、全角空格和常见字段前缀。
- [x] 3.2 将题干、选项、答案和解析按固定顺序拼接为训练文本。
- [x] 3.3 过滤空题干、空训练文本和明显异常文本。
- [x] 3.4 对两个源文件合并后的样本按规范化文本和标签去重。

## 4. 数据切分与输出

- [x] 4.1 实现按 label_id 分组的分层切分，默认比例为 train/dev/test = 80/10/10。
- [x] 4.2 写入 `data/processed/train.txt`，每行格式为 `text\tlabel_id`，label_id 必须在 `0..14`。
- [x] 4.3 写入 `data/processed/dev.txt`，每行格式为 `text\tlabel_id`，label_id 必须在 `0..14`。
- [x] 4.4 写入 `data/processed/test.txt`，每行格式为 `text\tlabel_id`，label_id 必须在 `0..14`。
- [x] 4.5 验证 `data/processed/class.txt` 在脚本执行前后内容完全一致。

## 5. 清洗报告与验证

- [x] 5.1 生成清洗报告，记录源文件行数、有效行数、过滤原因、去重数量、标签分布、切分数量和 class.txt 校验结果。
- [x] 5.2 运行 raw 数据清洗脚本，确认 processed 文件生成成功。
- [x] 5.3 运行现有数据校验脚本，确认 `train.txt`、`dev.txt`、`test.txt` 和 `class.txt` 格式可用。
- [x] 5.4 抽样检查 processed 文件，确认问题文本和标签对应关系准确，且分类仍为当前 15 类。
- [x] 5.5 运行 OpenSpec 校验，确认 `data-org-create` change 通过验证。