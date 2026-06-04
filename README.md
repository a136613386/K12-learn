# K12-learn

K12-learn 是面向高中生物错题归类与同类强化练习的 MVP。用户输入一道错题，系统预测对应知识分类，并返回同一分类下的强化题及答案。

## 业务流程

```text
用户输入错题
  -> BERT/兜底逻辑预测知识分类
  -> 查询知识分类信息
  -> 返回同类强化题 5 条
  -> 记录预测与推荐结果
```

## 环境配置

复制 `.env.example` 为 `.env`，并按本地环境调整：

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=123456
DB_NAME=k12-learn

REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
REDIS_TTL_SECONDS=86400

MODEL_PATH=backend/models/knowledge_bert
BERT_PRETRAINED_PATH=backend/models/bert-base-chinese
CLASS_PATH=data/processed/class.txt
DATA_DIR=data/processed
```

`BERT_PRETRAINED_PATH` 必须是当前项目内路径或显式配置的非参考路径，不要配置到 `D:\xuweiqun\py_project\work_heima\大模型三阶段\01_投满分\04-bert`。

## 后端启动

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

后端默认地址：`http://127.0.0.1:8000`

## 前端启动

```powershell
cd frontend
npm install
npm run dev
```

前端默认地址：`http://127.0.0.1:5173`

## 初始化数据库和题库

```powershell
python backend\scripts\init_db.py
python backend\scripts\seed_question_bank.py
```

`seed_question_bank.py` 会为 15 个知识分类生成题库数据，用于同类强化题推荐。

## 生成与预处理模型数据集

```powershell
python backend\scripts\generate_model_dataset.py
python backend\scripts\preprocess_model_dataset.py
python backend\scripts\validate_data.py
```

关键产物：

```text
data/raw/model_dataset.csv
data/processed/train.txt
data/processed/dev.txt
data/processed/test.txt
data/processed/class.txt
reports/model_dataset_distribution.txt
reports/preprocess_report.txt
```

## BERT 训练

先执行 dry-run，确认数据、依赖和路径配置正常。dry-run 不会下载模型、不会训练、不会覆盖报告。

```powershell
python backend\scripts\train_bert.py --dry-run
```

完整训练命令：

```powershell
python backend\scripts\train_bert.py --epochs 1 --batch-size 8 --max-length 128 --base-model-name bert-base-chinese
```

如果 `backend/models/bert-base-chinese` 还没有完整基础模型，完整训练时会使用 `--base-model-name` 初始化，并缓存到该项目内目录；随后训练知识分类模型并保存到 `backend/models/knowledge_bert`。

训练完成后的关键产物：

```text
backend/models/bert-base-chinese/
backend/models/knowledge_bert/
backend/models/knowledge_bert/label_mapping.json
reports/evaluation_report.json
```

## FastText 训练与模型对比

FastText 是轻量文本分类链路，使用当前 `data/processed/train.txt`、`dev.txt`、`test.txt` 和 `class.txt`，不会修改 BERT 训练入口。

```powershell
python backend\scripts\preprocess_fasttext_dataset.py
python backend\scripts\train_fasttext.py --preprocess --epoch 25 --lr 0.5 --word-ngrams 2 --min-count 1 --dim 100
python backend\scripts\compare_models.py
```

关键产物：

```text
data/fasttext/train.txt
data/fasttext/dev.txt
data/fasttext/test.txt
backend/models/fasttext_knowledge/model.bin
backend/models/fasttext_knowledge/label_mapping.json
backend/models/fasttext_knowledge/tokenization_config.json
reports/fasttext_preprocess_report.json
reports/fasttext_evaluation_report.json
reports/model_comparison_report.json
```

## API

错题归类与强化题推荐：

```http
POST /api/v1/wrong-questions/classify-and-recommend
```

请求示例：

```json
{
  "text": "豌豆杂交实验中 F1 自交后 F2 出现 3:1 的性状分离比，说明什么遗传规律？"
}
```

其他接口：

```text
POST /api/v1/predict/knowledge-point
GET /api/v1/knowledge-points
GET /api/v1/wrong-questions/recent?limit=10
GET /api/v1/stats/overview
GET /api/v1/health
```

`GET /api/v1/health` 会返回 `model_loaded`、`model_status` 和 `model_load_error`，用于判断当前是否正在使用真实 BERT 模型。

## 目录说明

```text
backend/                 Flask 后端
  app/                   API、service、repository、ML 模块
  scripts/               数据、训练、初始化脚本
database/init.sql        MySQL 表结构
data/raw/                原始模型数据集
data/processed/          训练/验证/测试数据
frontend/                Vue 前端
reports/                 数据处理和模型评估报告
openspec/changes/        OpenSpec change 文档
```
