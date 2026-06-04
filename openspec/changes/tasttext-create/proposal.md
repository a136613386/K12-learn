## Why

当前 BERT 微调链路训练慢、依赖重，并且在本地训练中已经出现准确率坍缩到多数类的情况。MVP 的错题知识点归类主要依赖题干、选项中的生物学概念和关键词，适合增加一个轻量 FastText 训练链路，用于快速得到可部署、可评估、可与 BERT 对比的分类模型。

## What Changes

- 新增 FastText 模型训练能力，基于现有 `data/processed/train.txt`、`dev.txt`、`test.txt` 和 `class.txt` 完成训练。
- 增加 FastText 专用数据处理，将 `题干：{stem} 选项：{options}\t{label_id}` 转换为 FastText 需要的 `__label__{label_id} 分词文本` 格式。
- 增加中文分词/切分处理，至少支持字符级切分，并允许后续扩展 jieba 分词或术语词典。
- 增加 FastText 训练、验证集调参、测试集评估和正式报告输出。
- 增加 FastText 与 BERT 的评估对比报告，比较训练耗时、推理耗时、accuracy、macro F1、模型文件大小和依赖复杂度。
- 不破坏当前 BERT 训练脚本、模型目录语义和 API 兜底机制；FastText 作为独立训练链路新增。

## Capabilities

### New Capabilities

- `fasttext-training`: 覆盖 FastText 数据预处理、中文分词、模型训练、模型评估、产物保存和报告生成。

### Modified Capabilities

- `model-training-inference`: 补充模型训练评估对比能力，使系统能够并行保留 BERT 与 FastText 的训练结果并生成可比较报告。

## Impact

- 影响后端脚本：新增 FastText 数据预处理、训练和评估脚本，建议放在 `backend/scripts`。
- 影响数据目录：读取 `data/processed/train.txt`、`dev.txt`、`test.txt`、`class.txt`，生成 FastText 中间训练文件。
- 影响模型目录：新增 FastText 模型产物目录，例如 `backend/models/fasttext_knowledge/`。
- 影响报告目录：新增 FastText 评估报告和 BERT/FastText 对比报告，例如 `reports/fasttext_evaluation_report.json`、`reports/model_comparison_report.json`。
- 影响依赖：可能新增 `fasttext-wheel` 或等价可安装 FastText Python 包；如 Windows 安装受限，需要提供明确错误和替代方案说明。
