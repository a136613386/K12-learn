## Context

当前项目已经具备 `data/processed/train.txt`、`dev.txt`、`test.txt` 和 `class.txt` 数据入口，数据格式为 `text\tlabel_id`，其中训练文本已经优化为 `题干：{stem} 选项：{options}`。BERT 训练链路虽然具备完整结构，但本地训练慢、依赖重，并且最近训练出现全量预测多数类的坍缩现象。

FastText 更适合当前 MVP 的轻量文本分类目标：15 个高中生物知识点分类主要依赖题干和选项里的术语、概念和题型信号。新增 FastText 链路应独立于 BERT，不改变现有 BERT 训练、模型目录和 API 行为。

## Goals / Non-Goals

**Goals:**

- 从现有 processed 数据生成 FastText 专用训练、验证、测试文件。
- 实现中文文本分词/切分，保证 FastText 能学习中文题干和选项中的分类特征。
- 训练 FastText 监督分类模型，并保存模型产物、标签映射和分词配置。
- 在 dev/test 上计算 accuracy、macro F1 和 classification_report。
- 生成正式 FastText 评估报告，并支持和 BERT 报告进行对比。
- 保持当前 BERT 链路可继续独立运行。

**Non-Goals:**

- 不在本 change 中替换线上 API 的默认推理模型。
- 不删除 BERT 训练代码或 BERT 模型目录。
- 不重新定义 15 个知识分类或修改 `class.txt`。
- 不在 FastText 数据集中加入答案和解析作为主训练输入。

## Decisions

### 决策 1：FastText 作为独立训练链路

新增脚本建议命名为 `backend/scripts/train_fasttext.py`，必要时配套 `backend/scripts/preprocess_fasttext_dataset.py` 和 `backend/scripts/compare_models.py`。FastText 读取 processed 数据，输出到独立目录，例如 `backend/models/fasttext_knowledge/`。

备选方案是把 FastText 逻辑塞进 `train_bert.py`。该方案会让 BERT 与 FastText 参数、依赖、报告字段混在一起，不利于排查和对比。

### 决策 2：训练输入使用题干和选项，不使用答案解析

FastText 输入沿用当前优化结论：`题干：{stem} 选项：{options}`。答案和解析不进入主训练文本，因为用户线上输入通常只有错题题干和选项，不会带官方解析；加入解析会造成训练/推理分布不一致。

### 决策 3：默认使用字符级切分

中文 FastText 不能直接依赖空格分词。默认采用字符级切分，英文、数字、遗传符号和常见生物学缩写尽量保留连续 token。这样不依赖 jieba 词典，Windows 本地更稳定，也能通过 n-gram 学到“红绿色盲”“半保留复制”“噬菌体”等模式。

后续可扩展 jieba 或领域词典，但该能力不是 MVP 的前置条件。

### 决策 4：报告字段对齐 BERT

FastText 评估报告使用 JSON，字段与 BERT 报告尽量对齐：

- `training_args`
- `train_count`
- `dev_count`
- `test_count`
- `label_count`
- `dev_accuracy`
- `dev_macro_f1`
- `test_accuracy`
- `test_macro_f1`
- `classification_report`
- `model_path`
- `label_mapping_path`
- `tokenization`
- `train_elapsed_seconds`
- `avg_inference_ms`

这样 `compare_models.py` 可以稳定读取 BERT 与 FastText 报告并生成对比结论。

### 决策 5：FastText 依赖失败必须显式报错

Windows 环境安装 `fasttext` 可能失败，因此实现时应优先考虑 `fasttext-wheel` 或明确记录安装建议。依赖不可用时脚本必须失败并给出原因，不能生成占位模型或占位报告。

## Risks / Trade-offs

- [Risk] FastText 语义理解能力弱于 BERT -> 通过使用题干+选项、字符 n-gram 和 macro F1 评估控制风险。
- [Risk] 少数类样本仍可能表现较差 -> 报告必须输出 per-class classification_report，便于定位需要补数据的分类。
- [Risk] 字符级切分导致文本变长 -> FastText 训练快，可接受；必要时限制最大字符数并在报告中记录截断策略。
- [Risk] Windows FastText 依赖安装不稳定 -> 使用独立脚本和显式依赖检查，不影响 BERT 与现有 API。
- [Risk] BERT 报告缺失或仍是占位报告 -> 对比报告必须标记 BERT 不可用，不能用占位指标。

## Migration Plan

1. 新增 FastText 数据预处理脚本，读取 processed 数据并生成 FastText 格式文件。
2. 新增 FastText 训练脚本，完成训练、dev 评估、test 评估和模型保存。
3. 新增评估报告生成逻辑，输出 `reports/fasttext_evaluation_report.json`。
4. 新增模型对比脚本，输出 `reports/model_comparison_report.json`。
5. 运行 FastText 训练和评估，检查 macro F1、分类报告和模型文件。
6. 保留 BERT 原有链路，后续再决定是否把 API 默认推理切换到 FastText。

## Open Questions

- 是否要求 FastText 后续接入 API 推理作为默认模型，还是仅作为训练对比模型？
- Windows 环境中最终采用 `fasttext-wheel` 还是其他兼容包，需要以本机安装结果为准。
- 是否需要为少数类增加过采样或 class weight 等补偿策略，取决于首轮 FastText test macro F1。
