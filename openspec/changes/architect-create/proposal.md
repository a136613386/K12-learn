## Why

当前 `k12-learn` 仓库还没有可执行的工程骨架，PRD 已明确 MVP 需要 Flask 后端、Vue 前端、BERT 模型训练/推理、MySQL、Redis 和基础展示页面。需要先通过架构变更统一目录、模块边界、接口能力和配置方式，避免后续开发直接堆叠脚本导致难以维护。

## What Changes

- 新增项目架构骨架能力，覆盖后端、前端、模型、数据、配置、脚本和测试目录。
- 明确 Flask 后端按 API、service、repository、ML 推理、配置分层。
- 明确 Vue 前端提供预测工作台、预测结果展示、耗时展示、最近记录、知识点列表和基础统计展示。
- 明确 BERT 训练与推理模块边界，训练脚本和在线推理服务解耦。
- 明确 MySQL/Redis 通过 `.env` 或环境变量读取配置，避免业务代码硬编码。
- 明确需要给前端提供预测、知识点列表、最近预测记录、统计概览和健康检查 API。
- 明确项目中必要的非自解释代码注释使用中文，注释保持简洁，不写空泛说明。

## Capabilities

### New Capabilities

- `project-architecture`: 定义 K12-learn MVP 的项目架构搭建能力，包括 Flask 后端、Vue 前端、BERT 模型模块、MySQL/Redis 配置、前端展示 API 和中文注释约束。

### Modified Capabilities

无。

## Impact

- 影响仓库目录结构、依赖声明、配置加载方式、后端接口模块、前端页面模块、模型训练/推理模块和 README 运行说明。
- 需要新增 Flask、Vue、PyTorch/Transformers、MySQL、Redis 相关依赖管理。
- 需要新增数据库初始化 SQL、样例数据目录、模型文件目录约定和测试入口。
- 后续实现应以该架构为基础，不直接照搬参考项目中的全局加载和硬编码路径方式。
