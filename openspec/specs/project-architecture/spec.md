# project-architecture Specification

## Purpose
TBD - created by archiving change architect-create. Update Purpose after archive.
## Requirements
### Requirement: Layered backend scaffold
系统 SHALL 提供分层的 Flask 后端架构，至少包含 API 路由、业务服务、数据访问、模型推理、配置加载、脚本和测试入口。

#### Scenario: Backend directories are created
- **WHEN** 开发者查看后端工程目录
- **THEN** 系统存在用于 API、service、repository、ML、config、scripts 和 tests 的清晰目录或模块
- **THEN** HTTP 路由中不直接实现模型训练逻辑或数据库细节

#### Scenario: Backend service can start with configuration
- **WHEN** 开发者按 README 配置 `.env` 并启动 Flask 服务
- **THEN** 系统读取环境变量中的 MySQL、Redis、模型路径和服务端口配置
- **THEN** 系统不会从业务代码中硬编码数据库或 Redis 连接参数

### Requirement: MVP backend APIs for frontend display
系统 SHALL 提供 Vue 前端展示所需的后端 API，包括预测、知识点列表、最近预测记录、统计概览和健康检查。

#### Scenario: Prediction API returns display fields
- **WHEN** 前端调用 `POST /api/v1/predict/knowledge-point` 并传入题目文本
- **THEN** 系统返回知识点 ID、知识点名称、置信度、预测耗时、缓存命中状态、重要程度、难度和核心要求
- **THEN** 系统将成功预测记录写入 MySQL

#### Scenario: Frontend support APIs return unified JSON
- **WHEN** 前端调用知识点列表、最近预测记录、统计概览或健康检查接口
- **THEN** 系统返回统一 JSON 结构，包含 `code`、`message` 和 `data`
- **THEN** 系统在参数错误或依赖不可用时返回明确错误信息

### Requirement: Vue prediction workspace
系统 SHALL 提供 Vue 前端基础页面，用于输入题目、展示预测结果、展示耗时、展示缓存命中状态和查看最近预测记录。

#### Scenario: User completes prediction from page
- **WHEN** 用户在 Vue 页面输入高中生物题目并点击预测
- **THEN** 页面展示加载状态并调用预测 API
- **THEN** 预测成功后页面展示知识模块、置信度、耗时、缓存命中状态、重要程度、难度和核心要求

#### Scenario: Page handles prediction error
- **WHEN** 预测 API 返回错误或网络异常
- **THEN** 页面展示错误提示
- **THEN** 页面保留用户已输入的题目文本

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

### Requirement: Data and cache persistence scaffold
系统 SHALL 提供 MySQL 初始化结构和 Redis 缓存约定，支撑知识点、题目、预测记录和重复预测缓存。

#### Scenario: Database schema supports MVP records
- **WHEN** 开发者执行数据库初始化脚本
- **THEN** 系统创建知识点、题目和预测记录相关表
- **THEN** 知识点表包含排序、重要程度、难度和核心要求字段
- **THEN** 预测记录表包含输入文本、预测标签、置信度、耗时、缓存命中状态和创建时间字段

#### Scenario: Redis cache degrades safely
- **WHEN** Redis 可用且相同文本重复预测
- **THEN** 系统优先返回缓存预测结果并标记缓存命中
- **WHEN** Redis 不可用
- **THEN** 系统继续执行模型预测并记录可诊断日志

### Requirement: Chinese comments for non-obvious code
系统 SHALL 在架构骨架和后续实现中，对非自解释的配置、模型加载、缓存降级、数据库初始化和业务编排使用简洁中文注释。

#### Scenario: Complex implementation includes Chinese comments
- **WHEN** 开发者查看模型加载、配置回退、缓存降级或数据库初始化代码
- **THEN** 相关复杂逻辑旁存在简洁中文注释说明意图
- **THEN** 简单变量赋值和显而易见的函数调用不会堆叠无意义注释

