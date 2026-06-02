# K12-learn

K12-learn 是一个面向高中生物必修2《遗传与进化》的知识点分类 MVP。当前版本提供 Flask 后端、Vue 前端、BERT 训练/推理骨架、MySQL 表结构、Redis 缓存约定和基础演示页面。

## 项目结构

```text
backend/                 Flask 后端
  app/
    api/                 API 路由
    services/            业务服务
    repositories/        MySQL 数据访问
    cache/               Redis 缓存
    ml/                  模型标签与推理骨架
  scripts/               数据校验、训练、初始化、冒烟脚本
  tests/                 后端测试
database/init.sql        MySQL 初始化 SQL
data/processed/          训练数据样例与 class.txt
frontend/                Vue 3 + Vite 前端
docs/PRD-MVP.md          MVP 产品需求文档
openspec/changes/        OpenSpec 变更
```

## 环境配置

复制 `.env.example` 为 `.env` 后按需调整。

```env
DB_HOST=192.168.218.150
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
DB_NAME=doc_pro

REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
```

## 后端启动

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

后端默认地址：

```text
http://127.0.0.1:8000
```

## 前端启动

```powershell
cd frontend
npm install
npm run dev
```

前端默认地址：

```text
http://127.0.0.1:5173
```

## 数据库初始化

先确认 `.env` 中 MySQL 配置可连接，再执行：

```powershell
cd backend
python scripts/init_db.py
```

## 数据与训练

训练数据格式：

```text
题目文本\t知识点标签ID
```

校验样例数据：

```powershell
cd backend
python scripts/validate_data.py
```

训练骨架：

```powershell
cd backend
python scripts/train_bert.py
```

当前训练脚本是骨架，已预留 BERT 接入点，后续需要补充真实 `torch/transformers` 训练循环。

## API 示例

预测接口：

```http
POST /api/v1/predict/knowledge-point
```

请求：

```json
{
  "text": "豌豆高茎与矮茎杂交，F1 全为高茎，F2 中高茎与矮茎的比例约为 3:1。该现象体现了什么遗传规律？"
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "knowledge_point_id": 0,
    "knowledge_point_name": "孟德尔遗传定律",
    "confidence": 0.92,
    "elapsed_ms": 185.3,
    "cache_hit": false,
    "importance": 5,
    "difficulty": 4,
    "core_requirement": "会判断显隐性、分离比、基因型和表现型"
  }
}
```

其他展示接口：

```text
GET /api/v1/knowledge-points
GET /api/v1/predictions/recent?limit=10
GET /api/v1/stats/overview
GET /api/v1/health
```

后端冒烟脚本：

```powershell
cd backend
python scripts/api_smoke.py
```
