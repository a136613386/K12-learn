## MODIFIED Requirements

### Requirement: BERT training and inference boundaries
系统 SHALL 将 BERT 训练脚本与在线推理模块解耦，训练负责基于项目内数据和项目内基础模型路径生成模型与评估报告，推理负责加载已保存模型并输出分类结果；系统 MUST NOT 在训练或推理运行时依赖参考项目 `04-bert` 目录作为模型资源来源。

#### Scenario: Training script generates model artifact
- **WHEN** 开发者运行训练脚本并提供 `train.txt`、`dev.txt`、`test.txt`、`class.txt` 和项目内基础 BERT 模型目录
- **THEN** 系统训练知识点分类模型并保存最佳模型文件
- **THEN** 系统输出 accuracy、macro F1 和 classification_report
- **THEN** 系统不会从参考项目 `04-bert` 目录加载基础模型、已训练模型或训练代码

#### Scenario: Inference module loads saved model
- **WHEN** Flask 服务启动在线推理能力
- **THEN** 系统只加载已保存模型、tokenizer 和标签文件
- **THEN** 系统不会在 Web 服务启动过程中执行训练流程
- **THEN** 系统不会从参考项目 `04-bert` 目录加载模型资源
