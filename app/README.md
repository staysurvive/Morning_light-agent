# 辰光Agent平台

AI Agent 管理平台前端，默认连接仓库中的 FastAPI 后端，提供配置、版本、知识文档、工具、会话和系统治理页面。

## 技术栈

React 19 + TypeScript + Vite + Shadcn UI + Tailwind CSS + React Router

## 快速开始

```powershell
cd D:\Morning_light-agent\app
npm ci
npm run dev
```

## 功能模块

| 模块 | 路由 | 说明 |
|------|------|------|
| 工作台 | `/` | 全局数据大盘、告警、资源用量 |
| Agent管理 | `/agents` | Agent CRUD、版本、发布、回滚和启停状态 |
| 模型管理 | `/models` | 模型供应商、连接测试和模型元数据 |
| Prompt管理 | `/prompts` | Prompt 编辑器、变量预览、发布、版本和回滚 |
| 知识库 | `/knowledge` | 知识库、文档、分段和本地全文检索测试 |
| 工具管理 | `/tools` | 工具配置、HTTP 测试、启停和测试指标 |
| 对话日志 | `/conversations` | 对话记录、链路追踪、人工标注 |
| 数据统计 | `/analytics` | 调用量、Token消耗、费用、效果评估 |
| 系统管理 | `/system` | 用户、角色、权限、API Key、审计、告警和设置 |

## Mock/API 切换

默认连接 `http://127.0.0.1:8000/api/v1`，账号、密码和验证码均由后端校验：

```powershell
npm run dev

# 仅在纯前端原型开发时显式启用 Mock
$env:VITE_USE_MOCK = 'true'
npm run dev
```

Mock 演示账号只用于显式启用的前端原型模式。真实模式的账号、密码和验证码全部由后端校验。完整运行说明、真实能力边界与功能变更记录见 `..\docs\PROJECT_GUIDE_FOR_SOL.md`。

## 设计文档

详细设计文档在 `docs/` 目录：

- [00-架构总览](docs/00-架构总览.md) — 系统架构、路由、技术栈、数据服务层设计
- [01-工作台](docs/01-工作台.md) — Dashboard数据大盘
- [02-Agent管理](docs/02-Agent管理.md) — Agent全生命周期管理
- [03-模型管理](docs/03-模型管理.md) — 模型和供应商管理
- [04-Prompt管理](docs/04-Prompt管理.md) — Prompt工程化管理
- [05-知识库管理](docs/05-知识库管理.md) — RAG知识库全流程
- [06-工具管理](docs/06-工具管理.md) — 工具注册和编排
- [07-对话日志](docs/07-对话日志.md) — 对话记录和链路追踪
- [08-数据统计](docs/08-数据统计.md) — 用量、费用、效果评估
- [09-系统管理](docs/09-系统管理.md) — 用户、角色、安全、审计
- [10-API接口规范](docs/10-API接口规范.md) — 接口定义、Mock层设计、切换方案
