from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.base_repository import BaseRepository
from src.modules.system.model import AlertRule, ApiAccessKey, AuditLog, SystemAlert, SystemSetting


class ApiKeyRepository(BaseRepository[ApiAccessKey]):
    def __init__(self, db: AsyncSession): super().__init__(ApiAccessKey, db)

    async def get_by_name(self, name: str):
        return await self.db.scalar(select(ApiAccessKey).where(ApiAccessKey.name == name))

    async def search_page(self, offset: int, limit: int, status: str | None, keyword: str | None):
        stmt = select(ApiAccessKey)
        if status:
            if status == "expired":
                stmt = stmt.where(ApiAccessKey.status == "active", ApiAccessKey.expires_at <= datetime.now())
            elif status == "active":
                stmt = stmt.where(
                    ApiAccessKey.status == "active",
                    or_(ApiAccessKey.expires_at.is_(None), ApiAccessKey.expires_at > datetime.now()),
                )
            else:
                stmt = stmt.where(ApiAccessKey.status == status)
        if keyword:
            stmt = stmt.where(ApiAccessKey.name.like(f"%{keyword}%"))
        total = await self.db.scalar(select(func.count()).select_from(stmt.subquery()))
        result = await self.db.execute(stmt.order_by(ApiAccessKey.id.desc()).offset(offset).limit(limit))
        return list(result.scalars().all()), int(total or 0)


class AuditRepository(BaseRepository[AuditLog]):
    def __init__(self, db: AsyncSession): super().__init__(AuditLog, db)

    async def search_page(self, offset, limit, user_id, action, resource, status, keyword, start_at, end_at):
        stmt = select(AuditLog)
        if user_id is not None: stmt = stmt.where(AuditLog.user_id == user_id)
        if action: stmt = stmt.where(AuditLog.action.like(f"%{action}%"))
        if resource: stmt = stmt.where(AuditLog.resource == resource)
        if status: stmt = stmt.where(AuditLog.status == status)
        if keyword:
            pattern = f"%{keyword}%"
            stmt = stmt.where(or_(
                AuditLog.user_name.like(pattern),
                AuditLog.resource_name.like(pattern),
                AuditLog.action.like(pattern),
            ))
        if start_at: stmt = stmt.where(AuditLog.timestamp >= start_at)
        if end_at: stmt = stmt.where(AuditLog.timestamp < end_at)
        total = await self.db.scalar(select(func.count()).select_from(stmt.subquery()))
        result = await self.db.execute(stmt.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit))
        return list(result.scalars().all()), int(total or 0)


class AlertRepository(BaseRepository[SystemAlert]):
    def __init__(self, db: AsyncSession): super().__init__(SystemAlert, db)

    async def list_filtered(self, status: str | None, severity: str | None, limit: int = 100):
        stmt = select(SystemAlert)
        if status: stmt = stmt.where(SystemAlert.status == status)
        if severity: stmt = stmt.where(SystemAlert.severity == severity)
        result = await self.db.execute(stmt.order_by(SystemAlert.last_occurred_at.desc()).limit(limit))
        return list(result.scalars().all())


class AlertRuleRepository(BaseRepository[AlertRule]):
    def __init__(self, db: AsyncSession): super().__init__(AlertRule, db)

    async def get_by_name(self, name: str):
        return await self.db.scalar(select(AlertRule).where(AlertRule.name == name))


class SettingRepository(BaseRepository[SystemSetting]):
    def __init__(self, db: AsyncSession): super().__init__(SystemSetting, db)

    async def get_main(self):
        return await self.db.scalar(select(SystemSetting).where(SystemSetting.setting_key == "main"))
