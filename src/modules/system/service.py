import hashlib
import secrets
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.core.exceptions import BizException
from src.modules.permission.model import Permission
from src.modules.system.model import AlertRule, ApiAccessKey, SystemAlert, SystemSetting
from src.modules.system.repository import AlertRepository, AlertRuleRepository, ApiKeyRepository, AuditRepository, SettingRepository
from src.modules.system.schema import (
    AlertCreate, AlertRuleCreate, AlertRuleUpdate, AlertUpdate, ApiKeyCreate, ApiKeyUpdate, SystemSettingsUpdate,
)
from src.modules.user.model import User


class SystemService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.api_keys = ApiKeyRepository(db)
        self.audit = AuditRepository(db)
        self.alerts = AlertRepository(db)
        self.rules = AlertRuleRepository(db)
        self.settings = SettingRepository(db)

    def _hash_key(self, key: str) -> str:
        return hashlib.sha256(f"{get_settings().APP_SECRET_KEY}:{key}".encode()).hexdigest()

    async def _validate_permissions(self, codes: list[str]) -> list[str]:
        unique = list(dict.fromkeys(code.strip() for code in codes if code.strip()))
        if not unique:
            return []
        existing = set((await self.db.execute(select(Permission.code).where(Permission.code.in_(unique)))).scalars())
        missing = [code for code in unique if code not in existing]
        if missing:
            raise BizException(code=400, message=f"权限码不存在：{', '.join(missing)}")
        return unique

    def serialize_api_key(self, item: ApiAccessKey, plaintext: str | None = None):
        return {
            "id": item.id, "name": item.name, "key": plaintext or item.masked_key,
            "permissions": item.permissions, "status": item.effective_status,
            "rateLimit": item.rate_limit, "usageCount": item.usage_count,
            "lastUsedAt": item.last_used_at, "expiresAt": item.expires_at,
            "createdBy": item.created_by, "createdAt": item.created_at,
        }

    async def create_api_key(self, data: ApiKeyCreate, current_user: User):
        name = data.name.strip()
        if await self.api_keys.get_by_name(name):
            raise BizException(code=400, message="API Key 名称已存在")
        if data.expires_at and data.expires_at.replace(tzinfo=None) <= datetime.now():
            raise BizException(code=400, message="过期时间必须晚于当前时间")
        permissions = await self._validate_permissions(data.permissions)
        plaintext = f"sk-ml-{secrets.token_urlsafe(32)}"
        item = await self.api_keys.create(ApiAccessKey(
            name=name, key_prefix=plaintext[:10], key_suffix=plaintext[-6:],
            secret_hash=self._hash_key(plaintext), permissions=permissions,
            rate_limit=data.rate_limit, expires_at=data.expires_at.replace(tzinfo=None) if data.expires_at else None,
            creator=current_user,
        ))
        return item, plaintext

    async def get_api_key(self, key_id: int):
        item = await self.api_keys.get_by_id(key_id)
        if not item: raise BizException(code=404, message="API Key 不存在")
        return item

    async def update_api_key(self, key_id: int, data: ApiKeyUpdate):
        item = await self.get_api_key(key_id)
        values = data.model_dump(exclude_unset=True)
        if data.name is not None:
            name = data.name.strip(); duplicate = await self.api_keys.get_by_name(name)
            if duplicate and duplicate.id != item.id: raise BizException(code=400, message="API Key 名称已存在")
            item.name = name
        if data.permissions is not None: item.permissions = await self._validate_permissions(data.permissions)
        if data.status is not None: item.status = data.status
        if data.rate_limit is not None: item.rate_limit = data.rate_limit
        if "expires_at" in values:
            if data.expires_at and data.expires_at.replace(tzinfo=None) <= datetime.now():
                raise BizException(code=400, message="过期时间必须晚于当前时间")
            item.expires_at = data.expires_at.replace(tzinfo=None) if data.expires_at else None
        return await self.api_keys.update(item)

    async def rotate_api_key(self, key_id: int):
        item = await self.get_api_key(key_id)
        plaintext = f"sk-ml-{secrets.token_urlsafe(32)}"
        item.key_prefix, item.key_suffix = plaintext[:10], plaintext[-6:]
        item.secret_hash = self._hash_key(plaintext)
        item.status = "active"
        item.usage_count = 0
        item.last_used_at = None
        await self.api_keys.update(item)
        return item, plaintext

    async def delete_api_key(self, key_id: int):
        if not await self.api_keys.delete_by_id(key_id): raise BizException(code=404, message="API Key 不存在")

    def serialize_audit(self, item):
        return {
            "id": item.id, "userId": str(item.user_id) if item.user_id else "anonymous",
            "userName": item.user_name, "action": item.action, "resource": item.resource,
            "resourceName": item.resource_name, "details": item.details,
            "ip": item.ip_address or "", "userAgent": item.user_agent or "",
            "status": item.status, "timestamp": item.timestamp,
        }

    async def get_alert(self, alert_id: int):
        item = await self.alerts.get_by_id(alert_id)
        if not item: raise BizException(code=404, message="系统告警不存在")
        return item

    def serialize_alert(self, item):
        return {
            "id": item.id, "type": item.type, "title": item.title, "message": item.message,
            "source": item.source, "severity": item.severity, "status": item.status,
            "count": item.count, "firstOccurredAt": item.first_occurred_at,
            "lastOccurredAt": item.last_occurred_at, "acknowledgedBy": item.acknowledged_by,
            "acknowledgedAt": item.acknowledged_at, "resolvedAt": item.resolved_at,
        }

    async def create_alert(self, data: AlertCreate):
        occurred = data.occurred_at.replace(tzinfo=None) if data.occurred_at else datetime.now()
        return await self.alerts.create(SystemAlert(
            type=data.type, title=data.title.strip(), message=data.message.strip(), source=data.source.strip(),
            severity=data.severity, status="active", count=data.count,
            first_occurred_at=occurred, last_occurred_at=occurred,
        ))

    async def update_alert(self, alert_id: int, data: AlertUpdate):
        item = await self.get_alert(alert_id)
        for key, value in data.model_dump(exclude_unset=True).items(): setattr(item, key, value.strip() if isinstance(value, str) else value)
        item.last_occurred_at = datetime.now()
        return await self.alerts.update(item)

    async def handle_alert(self, alert_id: int, action: str, current_user: User):
        item = await self.get_alert(alert_id)
        if action == "acknowledge":
            if item.status == "resolved": raise BizException(code=400, message="已解决告警不能重新确认")
            item.status, item.acknowledger, item.acknowledged_at = "acknowledged", current_user, datetime.now()
        else:
            item.status, item.resolved_at = "resolved", datetime.now()
            if not item.acknowledged_at:
                item.acknowledger, item.acknowledged_at = current_user, datetime.now()
        return await self.alerts.update(item)

    async def get_rule(self, rule_id: int):
        item = await self.rules.get_by_id(rule_id)
        if not item: raise BizException(code=404, message="告警规则不存在")
        return item

    def serialize_rule(self, item):
        return {"id": item.id, "name": item.name, "description": item.description, "condition": item.condition,
                "notifications": item.notifications, "status": item.status, "createdBy": item.created_by,
                "createdAt": item.created_at, "updatedAt": item.updated_at}

    async def create_rule(self, data: AlertRuleCreate, current_user: User):
        name = data.name.strip()
        if await self.rules.get_by_name(name): raise BizException(code=400, message="告警规则名称已存在")
        return await self.rules.create(AlertRule(name=name, description=data.description, condition=data.condition.model_dump(), notifications=data.notifications, creator=current_user))

    async def update_rule(self, rule_id: int, data: AlertRuleUpdate):
        item = await self.get_rule(rule_id)
        values = data.model_dump(exclude_unset=True)
        if data.name is not None:
            name=data.name.strip(); duplicate=await self.rules.get_by_name(name)
            if duplicate and duplicate.id != item.id: raise BizException(code=400, message="告警规则名称已存在")
            item.name=name
        if "description" in values: item.description=data.description.strip() if data.description else None
        if data.condition is not None: item.condition=data.condition.model_dump()
        if data.notifications is not None: item.notifications=data.notifications
        if data.status is not None: item.status=data.status
        return await self.rules.update(item)

    async def get_settings(self):
        item = await self.settings.get_main()
        if not item: item = await self.settings.create(SystemSetting(setting_key="main"))
        return item

    def serialize_settings(self, item):
        return {"systemName": item.system_name, "systemDescription": item.system_description,
                "defaultLanguage": item.default_language, "defaultModel": item.default_model,
                "defaultTemperature": item.default_temperature, "defaultMaxTokens": item.default_max_tokens,
                "smtpServer": item.smtp_server, "smtpPort": item.smtp_port, "senderEmail": item.sender_email}

    async def update_settings(self, data: SystemSettingsUpdate, current_user: User):
        item = await self.get_settings()
        mapping = {"systemName":"system_name", "systemDescription":"system_description", "defaultLanguage":"default_language",
                   "defaultModel":"default_model", "defaultTemperature":"default_temperature", "defaultMaxTokens":"default_max_tokens",
                   "smtpServer":"smtp_server", "smtpPort":"smtp_port", "senderEmail":"sender_email"}
        for key,value in data.model_dump(exclude_unset=True).items(): setattr(item,mapping[key],value.strip() if isinstance(value,str) else value)
        item.updater=current_user
        return await self.settings.update(item)
