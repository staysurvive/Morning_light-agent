# 辰光 Agent 项目工作手册

> 最后更新：2026-07-20
> 当前阶段：管理平台后端与前端已完成第一轮真实 API 闭环  
> 接口契约：`docs/openapi.json`，共 115 个 OpenAPI operations

## 1. 项目结论

辰光 Agent 是一个基于 FastAPI、React 和 MySQL 的 Agent 管理平台。当前仓库已经不是页面原型：默认前端连接真实后端，账号、密码、验证码、JWT 和 RBAC 都由后端校验，主要管理域已有数据库模型、迁移、服务、权限依赖和前端页面。

当前已经落地的是“管理与治理能力”，包括：

- 用户、角色、权限和登录认证；
- 模型供应商、模型、Prompt 和 Agent 配置管理；
- Agent 发布、版本、回滚和启停状态管理；
- 知识库、文档、分段和本地全文检索测试；
- 工具配置、HTTP 工具测试、启停和测试记录；
- 会话、轮次、链路、标注、导出和统计分析；
- API Key、审计日志、告警、告警规则、系统设置和工作台汇总；
- 前端菜单、路由和操作按钮三级权限控制。

当前尚未落地的是“AI 运行时能力”。不要把配置页面、状态字段或管理接口理解为以下能力已经存在：

- 没有调用模型供应商执行推理；
- 没有 Agent 编排器、任务队列、流式对话或自动运行链路；
- 没有 Embedding 生成、向量数据库或向量/混合检索；
- 没有内置工具或自定义函数执行沙箱；
- API Key 可以签发和管理，但还不能用于接口认证；
- 告警规则可以保存，但没有指标采集、自动评估和通知发送器。

## 2. 仓库结构

```text
Morning_light-agent/
|-- app/                         # React 19 + TypeScript 前端
|   |-- scripts/                 # OpenAPI 覆盖检查
|   `-- src/
|       |-- components/          # 通用组件、权限守卫、分页和弹窗
|       |-- contexts/            # 当前用户与授权上下文
|       |-- layouts/             # 管理台布局和权限过滤导航
|       |-- pages/               # 业务页面
|       `-- services/
|           |-- api/             # 真实 FastAPI 适配器
|           |-- mock/            # 显式启用时使用的前端原型数据
|           `-- types/           # 前端领域类型
|-- src/                         # FastAPI 后端
|   |-- core/                    # 配置、响应、异常、权限、加密、网络安全
|   |-- infra/                   # MySQL、Redis 和 MinIO 基础设施
|   |-- middlewares/             # 请求日志与审计日志
|   |-- modules/                 # 按业务域划分的后端模块
|   `-- scripts/                 # 超级管理员和 OpenAPI 工具
|-- alembic/                     # 数据库迁移
|-- docs/
|   |-- openapi.json             # 前后端唯一静态接口契约
|   `-- PROJECT_GUIDE_FOR_SOL.md  # 本手册和功能变更记录
|-- test/                        # 后端自动化测试
|-- .env.example                 # 后端环境变量模板
`-- requirements.txt             # Python 依赖
```

后端业务模块统一采用以下分层：

```text
src/modules/<domain>/
|-- model.py       # SQLAlchemy 持久化模型和关系
|-- repository.py  # 查询、分页和数据库操作
|-- schema.py      # Pydantic 请求/响应 DTO
|-- service.py     # 业务规则、状态转换和安全约束
`-- api.py         # FastAPI 路由、认证、授权和响应包装
```

新增后端业务时应沿用这套边界，不在路由中堆叠查询和业务规则，也不让 Repository 负责 HTTP 语义。

## 3. 当前能力矩阵

| 领域 | 后端能力 | 前端能力 | 当前边界 |
|---|---|---|---|
| 登录与验证码 | Redis 验证码、用户名/密码校验、30 分钟 JWT | 真实验证码、登录、失效 Token 清理 | 无 Refresh Token；退出登录为客户端删除 Token |
| 用户 | 创建、列表、分页搜索、详情、删除、查看/分配角色 | 分页、搜索、创建、详情、删除、分配角色 | 暂无用户资料编辑、启停和改密接口 |
| 角色 | 分页 CRUD、详情、分配权限 | 完整分页 CRUD 和权限分配 | 删除会解除用户关联 |
| 权限 | 分页 CRUD、详情 | 完整分页 CRUD | 删除会解除角色关联 |
| 模型供应商 | 分页 CRUD、详情、连接测试、凭证加密 | 列表、创建、编辑、删除、测试 | 连接测试只验证配置端点，不执行模型推理 |
| 模型 | 分页 CRUD、供应商/关键词筛选、默认模型约束 | 列表、筛选、创建、编辑、删除 | 仅登记元数据和价格，不调用模型 |
| Prompt | 分页 CRUD、发布、版本、回滚 | 编辑器、变量预览、发布、版本和回滚 | 不会自动注入或执行 Agent |
| Agent | 分页 CRUD、发布、版本、回滚、启停 | 完整管理、模型选择和权限按钮 | 启停是配置状态，不代表运行进程已启动 |
| 知识库 | CRUD、MinIO 上传、后台解析、分段、重试、删除、检索测试 | 知识库、文档、分段、状态轮询和检索页面 | 仅词项全文检索；Embedding 字段为预留配置 |
| 工具 | 分页 CRUD、启停、测试、加密配置、执行指标 | 列表、创建/编辑、详情、测试和启停 | 仅 HTTP 工具可测试；内置/自定义工具不执行 |
| 会话 | CRUD、轮次、链路、标注、JSON/文本导出 | 分页列表、详情、链路、标注、导出 | 记录由调用方写入，不负责生成回复 |
| 分析 | 用量、费用、评估、CSV 导出 | 用量、成本和评估页面 | 只聚合已持久化会话；无账单来源时为 0 |
| API Key | 分页、创建、更新、轮换、删除 | 完整管理和一次性明文展示 | 尚未接入请求认证中间件 |
| 审计 | 自动记录认证后的 API 操作、分页筛选 | 分页、模块/状态/日期/关键字筛选、导出 | 不记录请求体；敏感查询参数会脱敏 |
| 告警 | 告警 CRUD、确认/解决、规则 CRUD | 告警查看/处理、规则创建/启停/删除 | 规则不自动评估，也不自动通知 |
| 系统设置 | 读取和更新平台设置 | 真实读取和保存 | SMTP 字段仅保存配置，不发送邮件 |
| 工作台 | 真实会话、Agent、模型、告警和 MinIO 对象汇总 | 真实统计卡片、趋势、排行和资源用量 | 数据取决于已持久化记录和 MinIO 可用性 |

## 4. 接口契约

### 4.1 接口总量

`docs/openapi.json` 由 FastAPI 应用直接导出，当前共 115 个 operations：

| 路由域 | 前缀 | 数量 |
|---|---|---:|
| 健康检查 | `/health` | 1 |
| 验证码 | `/api/v1/captcha` | 2 |
| 登录 | `/api/v1/auth` | 1 |
| 用户 | `/api/v1/users` | 8 |
| 角色 | `/api/v1/roles` | 7 |
| 权限 | `/api/v1/permissions` | 6 |
| 模型供应商 | `/api/v1/providers` | 6 |
| 模型 | `/api/v1/models` | 5 |
| Prompt | `/api/v1/prompts` | 8 |
| Agent | `/api/v1/agents` | 10 |
| 知识库 | `/api/v1/knowledge-bases` | 14 |
| 工具 | `/api/v1/tools` | 8 |
| 会话 | `/api/v1/conversations`、`/api/v1/turns` | 11 |
| 分析 | `/api/v1/analytics` | 4 |
| 系统管理 | `/api/v1/system` | 19 |
| 工作台 | `/api/v1/dashboard` | 5 |

完整路径、参数和 DTO 以 `docs/openapi.json` 或运行时 `/docs` 为准，不在本手册复制第二份容易失真的字段清单。

### 4.2 响应与分页

成功响应统一为：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

分页数据统一放在 `data` 中：

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20
}
```

业务异常使用真实 HTTP 4xx/5xx，同时保留统一响应体。前端 API Client 会在 401 时清理 Token 并跳转登录页；403 会保留登录状态并显示无权限错误。

### 4.3 前端覆盖规则

`app/scripts/check-openapi-coverage.mjs` 会扫描真实 API 适配器并与静态 OpenAPI 对比。当前覆盖为 `115/115`，其中 8 个操作明确属于后端运行记录或管理细节，不由现有管理页面主动发起：

- 创建、更新、删除会话；
- 写入会话轮次；
- 写入链路步骤；
- 写入会话标注；
- API Key 详情；
- 更新告警事件。

这些接口不是遗漏，而是为未来 Agent 运行时、采集器或更细的管理界面保留的真实写入契约。

## 5. 身份、权限与安全边界

### 5.1 登录链路

1. 前端调用 `GET /api/v1/captcha` 获取验证码标识和图片；
2. 登录提交用户名、密码、验证码标识和验证码；
3. 后端先校验 Redis 验证码，再查用户并校验密码哈希和账号状态；
4. 登录成功更新 `last_login`，签发 30 分钟 HS256 JWT；
5. 前端保存 `localStorage.access_token`，随后通过 `/users/me` 获取角色和权限。

默认前端数据源是真实 API。只有显式设置 `VITE_USE_MOCK=true` 才会使用 Mock，因此不能再通过随便输入账号和密码进入真实系统。

### 5.2 RBAC

115 个操作中只有 4 个公共操作：健康检查、获取验证码、校验验证码和登录。其余 111 个操作都有 Bearer Token 和对应权限依赖。

授权规则：

- `is_superuser=true` 的用户绕过权限码匹配；
- 普通用户从所属角色合并权限集合；
- 后端 `require_permission()` 是最终安全边界；
- 前端使用相同权限码过滤菜单、保护路由并隐藏操作按钮；
- 直接构造前端地址不能绕过后端权限。

权限目录当前有 67 个原子权限，按领域分为：用户、角色、权限、供应商、模型、Prompt、Agent、知识库、工具、会话、分析、API Key、审计、告警、系统设置和工作台。唯一来源是 `src/core/permissions.py`，前端镜像位于 `app/src/services/permissions.ts`。

### 5.3 密钥和外部请求

- 供应商 API Key 使用 `APP_SECRET_KEY` 派生的 Fernet 密钥加密保存，响应只返回是否已配置；
- 工具配置整体加密保存，Authorization、Cookie、API Key、Token 和 Secret 类请求头在响应中显示为 `***configured***`；
- 前端把脱敏占位值提交回来时，后端会保留原密钥，不会用占位符覆盖；
- API Key 仅保存哈希、前缀和后缀，完整明文只在创建或轮换时返回一次；
- 供应商测试和 HTTP 工具测试禁用环境代理和重定向，并拒绝内网、回环、链路本地、多播、保留和未指定地址；
- HTTP 工具限制方法、超时和 1 MB 响应大小。

生产环境必须替换 `.env` 中的 `APP_SECRET_KEY`。修改该值后，已有供应商和工具密文将无法解密。

## 6. 核心业务规则

### 6.1 模型供应商与模型

- 供应商名称唯一，凭证不返回明文；
- 供应商删除会按数据库关系处理所属模型；
- 同一供应商下 `model_id` 唯一；
- 模型保存能力、上下文长度、状态、输入/输出价格、币种和默认标记；
- 同一时间只允许一个默认模型；
- 连接测试只检查配置的 HTTP 端点和凭证响应，不发起推理请求。

### 6.2 Prompt 与 Agent

- Prompt 创建为草稿，发布生成不可变版本快照；
- Prompt 支持变量定义、版本列表和按版本回滚；
- Agent 创建为草稿，必须关联存在的模型；
- Agent 支持 `conversation`、`tool`、`analysis`、`creative`、`workflow` 类型；
- Agent 发布生成版本快照，回滚恢复配置并生成新的当前版本状态；
- 只有符合生命周期约束的 Agent 才能启停；启停仅修改管理状态。

### 6.3 知识库

- 文件保存到 `MINIO_BUCKET` 指定的 MinIO bucket，对象名采用 `knowledge-bases/{知识库ID}/{UUID}.{扩展名}`；
- 应用启动时会检查 bucket，不存在时自动创建；MinIO 不可用不会阻止其他模块启动，但上传功能会返回 503；
- 单文件默认最大 20 MB，可通过 `MAX_DOCUMENT_SIZE_MB` 修改；
- 支持 PDF、DOCX、Markdown、TXT、HTML 和 CSV 文本提取；
- 上传成功先写入 `pending` 文档记录，响应提交后由 FastAPI `BackgroundTasks` 下载对象、解析和分段；
- 前端对 `pending/processing` 文档每 2 秒自动刷新，完成或失败后停止轮询；
- 支持固定长度、句子和段落分段，固定分段校验 overlap 小于 chunk size；
- 文档处理失败会保存错误信息，并支持重试；
- 删除文档或知识库会同时清理数据库记录、关联分段和 MinIO 对象；
- 检索测试基于词项重叠和精确包含加权，只是本地全文检索；
- `embedding_model` 是兼容未来扩展的预留配置；请求 Schema 只接受 `fulltext`，`vector` 和 `hybrid` 会直接校验失败。

### 6.4 工具

- 工具类型为 `builtin`、`http_api`、`custom_function`；
- HTTP 工具配置校验 URL、方法、请求头和 100~15000 毫秒超时；
- HTTP 工具测试支持 GET 查询参数和其他方法的 JSON Body；
- 每次测试写入执行记录，并刷新 7 日调用量、成功率和平均延迟；
- 内置工具与自定义函数目前只保存配置，测试会明确返回“没有执行沙箱”。

### 6.5 会话、分析和工作台

- 会话保存 Agent、用户和模型快照，资源删除后历史记录仍可读；
- 轮次保存角色、内容、Token 和工具调用元数据；
- 链路保存 LLM、检索或工具步骤的输入、输出、耗时和 Token；
- 标注支持 1~5 分、标签和备注；
- 分析从会话、Token、成本和标注记录实时聚合，不填充演示值；
- 工具、存储等没有独立账单来源时，成本报表返回 0；
- 工作台统计今日调用、Token、成本、Agent 状态、7 日趋势、排行、告警和 MinIO 文档对象同步情况。

## 7. 本地运行

### 7.1 后端

前置条件：Python、MySQL、Redis 和 MinIO 可用。仓库没有可依赖的 Docker Compose，这些服务需要自行启动或连接已有实例。

```powershell
cd D:\Morning_light-agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

编辑 `.env`，至少填写 MySQL、Redis、MinIO 和随机的 `APP_SECRET_KEY`。MinIO 配置包括 `MINIO_ENDPOINT`、`MINIO_ACCESS_KEY`、`MINIO_SECRET_KEY`、`MINIO_BUCKET` 和 `MINIO_SECURE`，然后执行：

```powershell
alembic upgrade head
python -m src.scripts.create_superuser --username admin --email admin@example.com
uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```

`create_superuser` 只创建不存在的新账号，并在终端交互读取两次密码，不会把密码写入命令历史。已有账号改密目前没有管理 API，不能重复运行该命令覆盖。

验证地址：

- 健康检查：`http://127.0.0.1:8000/health`
- Swagger：`http://127.0.0.1:8000/docs`
- OpenAPI：`http://127.0.0.1:8000/openapi.json`

### 7.2 前端

```powershell
cd D:\Morning_light-agent\app
npm ci
npm run dev
```

默认 API 地址为 `http://127.0.0.1:8000/api/v1`。需要覆盖时：

```powershell
$env:VITE_API_BASE = 'http://127.0.0.1:8000/api/v1'
npm run dev
```

只有纯前端原型开发才显式启用 Mock：

```powershell
$env:VITE_USE_MOCK = 'true'
npm run dev
```

关闭前端或后端时，在对应终端按 `Ctrl+C`。截至本手册更新时，前端开发服务器保持关闭，后端运行于 `127.0.0.1:8000`。

## 8. 数据库迁移

当前数据库迁移头为 `2d31a8c7f4e2`。主要业务迁移顺序：

```text
66b777046b3a  seed_rbac_permissions
829d7f3aeaf8  resource_management_core
bc34539ac5b8  agent_management
c6e99bac6d31  knowledge_management
eb155c4d538b  tool_management
ac8541d68b17  conversation_analytics
1ef7a711510b  system_management_dashboard
2d31a8c7f4e2  knowledge_minio_model
```

开发规则：

1. 修改 SQLAlchemy Model 后必须新增 Alembic 迁移；
2. 运行 `alembic upgrade head`；
3. 运行 `alembic check`，结果必须是 `No new upgrade operations detected.`；
4. 不手工修改生产数据库来代替迁移；
5. 删除策略、外键级联和历史数据保留必须在 Service 与迁移中同时明确。

## 9. OpenAPI 与前后端协作

后端路由或 Schema 变化后执行：

```powershell
cd D:\Morning_light-agent
python -m src.scripts.export_openapi

cd app
npm run check:openapi
```

`docs/openapi.json` 不应手工编辑。前端对接顺序固定为：

1. 后端完成 Model、Repository、Schema、Service、API 和迁移；
2. 导出 OpenAPI；
3. 在 `app/src/services/api/` 增加真实适配器；
4. 在领域 Service 中保留 Mock/API 选择，但默认真实 API；
5. 页面只依赖领域 Service，不直接拼 HTTP；
6. 同步菜单权限、路由权限和操作按钮权限；
7. 运行 OpenAPI 覆盖、构建、lint 和后端测试；
8. 在本手册第 12 节追加功能记录和剩余限制。

## 10. 当前质量基线

2026-07-20 最终实测：

| 检查 | 结果 |
|---|---|
| `python -m pytest -q` | 通过，32 passed |
| `alembic current` | `2d31a8c7f4e2 (head)` |
| `alembic check` | 通过，无模型/迁移差异 |
| `npm run check:openapi` | 通过，115/115，8 个明确后端专用操作 |
| `npm run build` | 通过，TypeScript 与 Vite 生产构建成功 |
| `npm run lint` | 0 errors，21 个 React Hook 依赖警告 |
| `GET /health` | HTTP 200，`status=ok` |
| 真实 RBAC 检查 | 无权限用户访问供应商接口得到 HTTP 403 |
| 真实 SSRF 检查 | 私网供应商目标得到 HTTP 400 |
| 真实密钥检查 | 工具头脱敏，提交占位值后原密钥仍保留 |
| 真实审计检查 | `keyword` 后端筛选返回匹配记录 |
| MinIO 对象检查 | bucket 创建、上传、下载校验和删除闭环通过 |
| 知识库 MinIO 联调 | 临时知识库上传、后台解析、分段、状态更新和级联清理通过 |

当前质量提示：

- 前端构建产物主 JS 约 643 KB，Vite 提示大于 500 KB，后续可按路由懒加载拆包；
- 21 个 Hook 依赖警告不阻断构建，但后续修改相关加载逻辑时应逐页收敛；
- 尚无前端组件测试和端到端测试；当前环境的企业策略阻止浏览器访问 localhost，因此本轮使用构建和真实 HTTP 联调验证。
- 知识文档解析当前使用 FastAPI 进程内 `BackgroundTasks`，服务重启时未完成任务不会自动恢复；生产环境应迁移到持久化任务队列。

## 11. 已知限制与下一阶段

以下事项不应在当前版本中宣称已经完成：

1. 模型推理网关、流式响应、重试、限流、熔断和供应商适配；
2. Agent 执行器、任务调度、Prompt/知识库/工具运行时装配；
3. 向量化任务、向量数据库、语义检索和混合检索；
4. 自定义代码沙箱和内置工具执行框架；
5. API Key 请求认证和使用量计数；
6. 告警指标采集、规则自动评估和邮件/Webhook 通知；
7. 用户资料更新、账号启停、修改密码、密码找回和 Refresh Token；
8. 前端自动化测试、路由拆包和生产 CORS 白名单。

推荐下一阶段顺序：先实现模型推理网关，再实现最小 Agent 对话运行链路；之后把会话写入、知识检索和工具调用接到运行时。只有这些链路真正产生数据后，工作台和分析模块才会从“管理与采集底座”升级为完整运行平台。

## 12. 功能变更记录

### 2026-07-19：身份、用户与 RBAC

- 登录改为真实后端校验账号、密码和 Redis 验证码；
- 完成用户创建、查询、分页搜索、详情、删除和角色分配；
- 完成角色和权限的分页 CRUD、详情和角色权限分配；
- 删除用户、角色和权限时清理关联表；
- 增加 67 个领域权限码，并在后端接口、前端菜单、路由和按钮统一执行；
- `BizException` 改为返回真实 HTTP 401/403/404 等状态；
- 数据库依赖使用函数作用域，保证响应前提交事务。

### 2026-07-19：模型供应商、模型与 Prompt

- 新增供应商分页 CRUD、详情、连接测试和加密凭证；
- 新增模型分页 CRUD、供应商/关键词筛选、能力、上下文、状态、价格、币种和默认模型规则；
- 新增 Prompt 分页 CRUD、变量、发布、版本和回滚；
- 完成对应前端真实 API、表单、分页、删除确认、发布和版本页面；
- 修正模型价格字段为真实币种语义；
- Prompt 编辑页发布操作增加 `prompt_publish` 权限守卫。

### 2026-07-19：Agent 管理

- 新增 Agent 分页 CRUD、详情、发布、版本、回滚和启停；
- Agent 表单接入真实模型并要求选择模型；
- 前端移除没有后端能力的测试和监控入口；
- 修正成功率重复乘以 100 的显示错误；
- 明确 Agent 启停只表示管理状态，不宣称存在运行进程。

### 2026-07-19：知识库

- 新增知识库 CRUD、配置更新、文档上传/解析/重试/删除、分段查询/编辑和检索测试；
- 文档保存到本地受控目录，限制 20 MB，支持文本、PDF 和 DOCX；
- 删除时同时清理本地文件，解析失败保留错误信息；
- 实现基于词项的全文检索并记录命中次数；
- 前端只提供全文检索策略，Embedding 模型标识明确标为预留配置；
- 后端请求 Schema 同样只接受 `fulltext`，防止原始 API 误报向量或混合检索能力；
- 不再把分段数量描述为向量数量。

### 2026-07-19：工具

- 新增工具分页 CRUD、详情、启停、测试和执行指标；
- 工具配置加密，敏感请求头响应脱敏，编辑脱敏配置时保留旧密钥；
- HTTP 工具增加方法、超时、响应大小、SSRF 和重定向限制；
- 内置与自定义工具只保存配置，测试明确返回没有执行沙箱；
- 完成前端创建/编辑、详情、测试、列表和权限按钮。

### 2026-07-19：会话与分析

- 新增会话 CRUD、轮次、链路、标注和 JSON/文本导出；
- 新增用量、成本、评估聚合和 CSV 导出；
- 分析只使用持久化会话数据，删除前端演示值回退和除零问题；
- 前端完成会话分页、详情导航、链路、标注、导出及三类分析页面。

### 2026-07-19：系统治理与工作台

- 新增 API Key 分页、创建、更新、轮换和删除，明文只显示一次；
- 新增认证后 API 操作审计，排除请求体并脱敏敏感查询参数；
- 新增审计分页、模块、状态、日期和后端关键字筛选；
- 新增告警事件 CRUD、确认/解决和告警规则 CRUD；
- 新增系统设置读取/更新；
- 新增工作台统计、趋势、Agent 排行、告警和资源用量；
- 前端系统菜单按权限展示，API Key、审计、告警、系统设置和工作台全部连接真实接口。

### 2026-07-19：前后端收口与说明书重写

- 重新导出 115 个 OpenAPI operations，加入可重复执行的 `src/scripts/export_openapi.py`；
- OpenAPI 覆盖检查通过 115/115，并保留 8 个明确的后端专用操作；
- 删除会假装保存密码和偏好的旧账户设置页面及入口，旧 `/settings` 重定向到真实个人资料页；
- 完成私网目标阻断、工具密钥保留、审计关键字和 HTTP 403 的真实接口验证；
- 后端测试 32 passed，迁移无差异，前端构建通过，lint 0 错误；
- 重写本手册的能力矩阵、接口统计、运行方式、安全边界、质量基线和已知限制。

### 2026-07-20：知识库新模型与 MinIO 存储

- 按新模型把 `KnowledgeDocument/KnowledgeSegment` 重命名为 `Document/Segment`，数据库表迁移为 `documents/segments`；
- 知识库和文档创建者由用户外键快照调整为用户名字符串，历史创建者在迁移时完成回填；
- 文档字段从本地 `storage_path/file_size_bytes` 调整为 `minio_path/file_size`，分段不再持久化可派生的关键词数组；
- 新增 MinIO 客户端适配器、bucket 自动创建、对象上传、下载、删除和资源用量统计；
- 文档上传后使用 FastAPI `BackgroundTasks` 执行 MinIO 下载、文本解析、分段写入和状态统计，失败会持久化错误信息；
- 重试复用后台解析任务，删除文档或知识库会同步删除 MinIO 对象；
- 前端 DTO 和 Mock 改用 `minio_path`，上传/重试后自动轮询 `pending/processing` 状态；
- 新增迁移 `2d31a8c7f4e2`，数据库已升级且 `alembic check` 无差异；
- MinIO 对象往返测试及知识库上传、解析、分段、删除完整联调通过，临时对象和数据库记录均已清理；
- 当前仍只支持全文检索，Embedding 模型字段仍为预留配置；后台解析任务尚未迁移到持久化队列。

### 后续记录模板

每次新增、修改或删除功能时，在本节追加：

```text
### YYYY-MM-DD：功能名称

- 后端：路由、Schema、业务规则、权限和迁移；
- 前端：页面、服务、权限守卫和交互；
- 数据：新增表、字段、级联和兼容策略；
- 验证：pytest、alembic check、OpenAPI、build、lint、真实接口；
- 限制：本次没有实现或仍需外部基础设施的能力。
```
