## 1. 依赖与目录准备

- [x] 1.1 确认 FastText Python 依赖方案，优先验证 `fasttext-wheel` 或当前环境可安装的等价包。
- [x] 1.2 更新 `backend/requirements.txt`，加入 FastText 训练所需依赖并保留 BERT 现有依赖。
- [x] 1.3 定义 FastText 模型目录，例如 `backend/models/fasttext_knowledge/`。
- [x] 1.4 定义 FastText 中间数据目录，例如 `data/fasttext/`，用于保存转换后的 train/dev/test 文件。

## 2. FastText 数据预处理

- [x] 2.1 新增 FastText 数据预处理脚本，读取 `data/processed/train.txt`、`dev.txt`、`test.txt` 和 `class.txt`。
- [x] 2.2 校验 processed 文件每行必须为 `text\tlabel_id`，并校验 `label_id` 位于 `0..14`。
- [x] 2.3 实现中文字符级分词/切分函数，保留英文、数字、遗传符号和常见缩写。
- [x] 2.4 将样本转换为 FastText 监督训练格式：`__label__{label_id} {tokenized_text}`。
- [x] 2.5 输出 FastText train/dev/test 中间文件，并生成预处理报告。
- [x] 2.6 确保预处理流程不修改 `data/processed/class.txt` 和原始 processed 三份数据。

## 3. FastText 模型训练

- [x] 3.1 新增 `backend/scripts/train_fasttext.py` 训练入口，支持配置 epoch、lr、wordNgrams、minCount 等参数。
- [x] 3.2 在训练开始前执行依赖检查，FastText 不可用时输出明确安装建议。
- [x] 3.3 使用 FastText train 数据训练监督分类模型。
- [x] 3.4 使用 dev 数据计算 accuracy 和 macro F1，并记录 dev 指标。
- [x] 3.5 将训练后的 FastText 模型保存到项目内模型目录。
- [x] 3.6 保存 `label_mapping.json` 和分词配置，保证后续推理可复现。

## 4. 评估与报告

- [x] 4.1 使用 test 数据对 FastText 模型进行最终评估。
- [x] 4.2 计算 test accuracy、test macro F1 和 classification_report。
- [x] 4.3 统计模型文件大小、训练耗时和平均单条推理耗时。
- [x] 4.4 生成 `reports/fasttext_evaluation_report.json`，记录训练参数、数据规模、指标、模型路径和分词模式。
- [x] 4.5 确保 FastText 依赖或训练失败时不会生成占位模型或伪造报告。

## 5. BERT 与 FastText 对比

- [x] 5.1 新增模型对比脚本，读取 BERT 与 FastText 评估报告。
- [x] 5.2 当 BERT 报告缺失或仍是占位报告时，在对比报告中标记 BERT 指标不可用。
- [x] 5.3 生成 `reports/model_comparison_report.json`，比较 accuracy、macro F1、训练耗时、推理耗时、模型大小和依赖复杂度。
- [x] 5.4 在 README 或项目文档中补充 FastText 训练、评估和对比命令。

## 6. 验证

- [x] 6.1 运行 FastText 数据预处理脚本，确认中间数据文件生成成功。
- [x] 6.2 运行 FastText 训练脚本，确认模型、标签映射和分词配置生成成功。
- [x] 6.3 检查 FastText 评估报告，确认包含 accuracy、macro F1 和 classification_report。
- [x] 6.4 运行模型对比脚本，确认对比报告生成成功。
- [x] 6.5 运行现有 BERT dry-run 或数据校验脚本，确认新增 FastText 链路没有破坏现有训练入口。
- [x] 6.6 运行 `openspec validate tasttext-create --no-color`，确认 change 通过验证。

## 7. 在线混合推理兜底链路

- [x] 7.1 在当前 change 中增加 BERT 优先、FastText 兜底的 OpenSpec 需求描述。
- [x] 7.2 增加 FastText 在线推理加载逻辑，读取项目内 `backend/models/fasttext_knowledge/model.bin`。
- [x] 7.3 增加 `BERT_CONFIDENCE_THRESHOLD=0.8` 配置，BERT 置信度低于阈值时自动切换 FastText。
- [x] 7.4 后端分类 API 返回 `model_status`、`fallback_reason`、`bert_confidence`、`fasttext_confidence` 等链路信息。
- [x] 7.5 健康检查 API 返回 BERT 与 FastText 各自加载状态。
- [x] 7.6 前端以中文展示当前采用模型、兜底原因和 BERT/FastText 服务状态。
- [x] 7.7 运行后端编译、前端构建和 `openspec validate tasttext-create --no-color` 验证。
