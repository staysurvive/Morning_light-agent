USER_READ = "user_read"
USER_CREATE = "user_create"
USER_DELETE = "user_delete"
USER_ASSIGN_ROLES = "user_assign_roles"

ROLE_READ = "role_read"
ROLE_CREATE = "role_create"
ROLE_UPDATE = "role_update"
ROLE_DELETE = "role_delete"
ROLE_ASSIGN_PERMISSIONS = "role_assign_permissions"

PERMISSION_READ = "permission_read"
PERMISSION_CREATE = "permission_create"
PERMISSION_UPDATE = "permission_update"
PERMISSION_DELETE = "permission_delete"

PROVIDER_READ = "provider_read"
PROVIDER_CREATE = "provider_create"
PROVIDER_UPDATE = "provider_update"
PROVIDER_DELETE = "provider_delete"
PROVIDER_TEST = "provider_test"

MODEL_READ = "model_read"
MODEL_CREATE = "model_create"
MODEL_UPDATE = "model_update"
MODEL_DELETE = "model_delete"

PROMPT_READ = "prompt_read"
PROMPT_CREATE = "prompt_create"
PROMPT_UPDATE = "prompt_update"
PROMPT_DELETE = "prompt_delete"
PROMPT_PUBLISH = "prompt_publish"

AGENT_READ = "agent_read"
AGENT_CREATE = "agent_create"
AGENT_UPDATE = "agent_update"
AGENT_DELETE = "agent_delete"
AGENT_PUBLISH = "agent_publish"
AGENT_START_STOP = "agent_start_stop"

KNOWLEDGE_READ = "knowledge_read"
KNOWLEDGE_CREATE = "knowledge_create"
KNOWLEDGE_UPDATE = "knowledge_update"
KNOWLEDGE_DELETE = "knowledge_delete"
KNOWLEDGE_DOCUMENT_MANAGE = "knowledge_document_manage"
KNOWLEDGE_SEGMENT_UPDATE = "knowledge_segment_update"
KNOWLEDGE_RETRIEVE = "knowledge_retrieve"

TOOL_READ = "tool_read"
TOOL_CREATE = "tool_create"
TOOL_UPDATE = "tool_update"
TOOL_DELETE = "tool_delete"
TOOL_ENABLE = "tool_enable"
TOOL_TEST = "tool_test"

CONVERSATION_READ = "conversation_read"
CONVERSATION_CREATE = "conversation_create"
CONVERSATION_UPDATE = "conversation_update"
CONVERSATION_DELETE = "conversation_delete"
CONVERSATION_EXPORT = "conversation_export"
CONVERSATION_ANNOTATE = "conversation_annotate"

ANALYTICS_READ = "analytics_read"
ANALYTICS_EXPORT = "analytics_export"

API_KEY_READ = "api_key_read"
API_KEY_CREATE = "api_key_create"
API_KEY_UPDATE = "api_key_update"
API_KEY_DELETE = "api_key_delete"
AUDIT_READ = "audit_read"
ALERT_READ = "alert_read"
ALERT_CREATE = "alert_create"
ALERT_UPDATE = "alert_update"
ALERT_DELETE = "alert_delete"
ALERT_HANDLE = "alert_handle"
SETTINGS_READ = "settings_read"
SETTINGS_UPDATE = "settings_update"
DASHBOARD_READ = "dashboard_read"


RBAC_PERMISSION_CATALOG = (
    (USER_READ, "查看用户", "查看用户列表、详情和角色"),
    (USER_CREATE, "创建用户", "创建平台用户"),
    (USER_DELETE, "删除用户", "删除平台用户"),
    (USER_ASSIGN_ROLES, "分配用户角色", "调整用户拥有的角色"),
    (ROLE_READ, "查看角色", "查看角色列表、详情和权限"),
    (ROLE_CREATE, "创建角色", "创建平台角色"),
    (ROLE_UPDATE, "更新角色", "修改角色名称和描述"),
    (ROLE_DELETE, "删除角色", "删除平台角色"),
    (ROLE_ASSIGN_PERMISSIONS, "分配角色权限", "调整角色拥有的权限"),
    (PERMISSION_READ, "查看权限", "查看权限列表和详情"),
    (PERMISSION_CREATE, "创建权限", "创建权限定义"),
    (PERMISSION_UPDATE, "更新权限", "修改权限名称和描述"),
    (PERMISSION_DELETE, "删除权限", "删除权限定义"),
    (PROVIDER_READ, "查看模型供应商", "查看模型供应商配置"),
    (PROVIDER_CREATE, "创建模型供应商", "创建模型供应商配置"),
    (PROVIDER_UPDATE, "更新模型供应商", "修改模型供应商配置"),
    (PROVIDER_DELETE, "删除模型供应商", "删除供应商及其模型"),
    (PROVIDER_TEST, "测试供应商连接", "测试供应商端点和凭证"),
    (MODEL_READ, "查看模型", "查看模型配置"),
    (MODEL_CREATE, "创建模型", "登记模型配置"),
    (MODEL_UPDATE, "更新模型", "修改模型配置"),
    (MODEL_DELETE, "删除模型", "删除模型配置"),
    (PROMPT_READ, "查看 Prompt", "查看 Prompt 和版本"),
    (PROMPT_CREATE, "创建 Prompt", "创建 Prompt 草稿"),
    (PROMPT_UPDATE, "更新 Prompt", "修改 Prompt 草稿"),
    (PROMPT_DELETE, "删除 Prompt", "删除 Prompt 和版本"),
    (PROMPT_PUBLISH, "发布 Prompt", "发布或回滚 Prompt 版本"),
    (AGENT_READ, "查看 Agent", "查看 Agent 配置和版本"),
    (AGENT_CREATE, "创建 Agent", "创建 Agent 草稿"),
    (AGENT_UPDATE, "更新 Agent", "修改 Agent 配置"),
    (AGENT_DELETE, "删除 Agent", "删除 Agent 和版本"),
    (AGENT_PUBLISH, "发布 Agent", "发布或回滚 Agent 版本"),
    (AGENT_START_STOP, "启停 Agent", "启动或停止已发布 Agent"),
    (KNOWLEDGE_READ, "查看知识库", "查看知识库、文档和分段"),
    (KNOWLEDGE_CREATE, "创建知识库", "创建知识库配置"),
    (KNOWLEDGE_UPDATE, "更新知识库", "修改知识库和分段配置"),
    (KNOWLEDGE_DELETE, "删除知识库", "删除知识库及其文件"),
    (KNOWLEDGE_DOCUMENT_MANAGE, "管理知识库文档", "上传、重试和删除文档"),
    (KNOWLEDGE_SEGMENT_UPDATE, "更新知识库分段", "编辑文档分段内容"),
    (KNOWLEDGE_RETRIEVE, "测试知识检索", "执行知识库本地检索测试"),
    (TOOL_READ, "查看工具", "查看工具配置和指标"),
    (TOOL_CREATE, "创建工具", "登记工具配置"),
    (TOOL_UPDATE, "更新工具", "修改工具配置"),
    (TOOL_DELETE, "删除工具", "删除工具及其测试记录"),
    (TOOL_ENABLE, "启停工具", "启用或停用工具"),
    (TOOL_TEST, "测试工具", "验证工具配置或测试 HTTP 工具"),
    (CONVERSATION_READ, "查看会话", "查看会话、轮次和链路"),
    (CONVERSATION_CREATE, "记录会话", "创建会话并写入轮次和链路"),
    (CONVERSATION_UPDATE, "更新会话", "结束会话或更新运行结果"),
    (CONVERSATION_DELETE, "删除会话", "删除会话及其完整记录"),
    (CONVERSATION_EXPORT, "导出会话", "导出会话 JSON 或文本"),
    (CONVERSATION_ANNOTATE, "标注会话", "新增或更新会话人工标注"),
    (ANALYTICS_READ, "查看分析", "查看真实会话聚合分析"),
    (ANALYTICS_EXPORT, "导出分析", "导出分析 CSV 报表"),
    (API_KEY_READ, "查看 API Key", "查看 API Key 元数据"),
    (API_KEY_CREATE, "创建 API Key", "签发 API Key"),
    (API_KEY_UPDATE, "更新 API Key", "修改或轮换 API Key"),
    (API_KEY_DELETE, "删除 API Key", "撤销并删除 API Key"),
    (AUDIT_READ, "查看审计日志", "查看平台操作审计"),
    (ALERT_READ, "查看告警", "查看告警和规则"),
    (ALERT_CREATE, "创建告警", "创建告警事件和规则"),
    (ALERT_UPDATE, "更新告警", "修改告警事件和规则"),
    (ALERT_DELETE, "删除告警", "删除告警事件和规则"),
    (ALERT_HANDLE, "处理告警", "确认或解决告警"),
    (SETTINGS_READ, "查看系统设置", "查看平台系统设置"),
    (SETTINGS_UPDATE, "更新系统设置", "修改平台系统设置"),
    (DASHBOARD_READ, "查看工作台", "查看平台真实汇总数据"),
)
