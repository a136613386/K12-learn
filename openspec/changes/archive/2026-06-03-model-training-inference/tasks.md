## 1. 配置与路径语义

- [x] 1.1 更新 `backend/app/config.py`，移除 `04-bert` fallback，默认基础模型目录为项目内路径。
- [x] 1.2 更新 `.env`、`.env.example` 和 README，使 `MODEL_PATH` 指向 `backend/models/knowledge_bert` 目录。
- [x] 1.3 增加路径校验：拒绝参考目录；完整训练时通过 `--base-model-name` 自动准备基础模型。

## 2. 训练脚本与正式报告

- [x] 2.1 调整 `backend/scripts/train_bert.py`，训练保存目录直接使用 `settings.model_path`。
- [x] 2.2 正式训练报告记录训练参数、数据规模、dev 指标、test 指标、classification_report 和路径信息。
- [x] 2.3 保留 `--dry-run` 只做校验，不创建或覆盖模型产物和正式报告。
- [ ] 2.4 执行完整训练，生成 `backend/models/knowledge_bert/` 下的模型权重、tokenizer、配置和 `label_mapping.json`。

## 3. 线上 BERT 推理接入

- [x] 3.1 重构 `backend/app/ml/predictor.py`，加载 tokenizer、分类模型和 `label_mapping.json`。
- [x] 3.2 实现真实 BERT 推理：文本编码、前向计算、softmax、标签选择和置信度返回。
- [x] 3.3 修复模型可用性判断，只在模型目录完整且可加载时标记 BERT 已加载。
- [x] 3.4 保留关键词兜底，并通过状态字段和健康检查暴露当前是否使用真实 BERT。

## 4. 占位符与文档清理

- [x] 4.1 删除 `knowledge_bert.placeholder.json`，确保它不参与模型加载或可用性判断。
- [ ] 4.2 用完整训练生成的正式 `reports/evaluation_report.json` 替换占位评估报告。
- [x] 4.3 更新 README 中的训练、模型路径、报告路径和基础模型准备说明。

## 5. 验证

- [x] 5.1 运行数据校验和训练 dry-run，确认数据、依赖和项目内模型路径检查通过。
- [ ] 5.2 检查完整训练后的模型目录，确认存在可加载模型权重、tokenizer、配置和 `label_mapping.json`。
- [ ] 5.3 检查正式评估报告，确认包含训练参数、accuracy、macro F1 和 classification_report。
- [ ] 5.4 运行后端 API smoke test，确认模型可用时返回真实 BERT softmax 分类结果。
- [x] 5.5 运行 OpenSpec 校验，确认 `model-training-inference` change 通过验证。
