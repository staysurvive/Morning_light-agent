from datetime import date, datetime, time, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.base_schema import PageResult, ResponseSchema
from src.core.deps import require_permission
from src.core.permissions import (
    ALERT_CREATE, ALERT_DELETE, ALERT_HANDLE, ALERT_READ, ALERT_UPDATE,
    API_KEY_CREATE, API_KEY_DELETE, API_KEY_READ, API_KEY_UPDATE,
    AUDIT_READ, SETTINGS_READ, SETTINGS_UPDATE,
)
from src.infra.database import get_db
from src.modules.system.schema import (
    AlertCreate, AlertRead, AlertRuleCreate, AlertRuleRead, AlertRuleUpdate, AlertUpdate,
    ApiKeyCreate, ApiKeyCreated, ApiKeyRead, ApiKeyUpdate, AuditLogRead,
    SystemSettingsRead, SystemSettingsUpdate,
)
from src.modules.system.service import SystemService
from src.modules.user.model import User

router = APIRouter(prefix="/system", tags=["System"])


def get_system_service(db: AsyncSession = Depends(get_db, scope="function")) -> SystemService:
    return SystemService(db)


@router.get("/api-keys", response_model=ResponseSchema[PageResult[ApiKeyRead]], dependencies=[Depends(require_permission(API_KEY_READ))])
async def list_api_keys(page:int=Query(1,ge=1), page_size:int=Query(20,ge=1,le=100), status:str|None=None, keyword:str|None=None, service:SystemService=Depends(get_system_service)):
    items,total=await service.api_keys.search_page((page-1)*page_size,page_size,status,keyword)
    return ResponseSchema(data=PageResult(items=[ApiKeyRead.model_validate(service.serialize_api_key(i)) for i in items],total=total,page=page,page_size=page_size))


@router.post("/api-keys", response_model=ResponseSchema[ApiKeyCreated])
async def create_api_key(data:ApiKeyCreate,current_user:User=Depends(require_permission(API_KEY_CREATE)),service:SystemService=Depends(get_system_service)):
    item,key=await service.create_api_key(data,current_user); return ResponseSchema(data=ApiKeyCreated.model_validate(service.serialize_api_key(item,key)))


@router.get("/api-keys/{key_id}", response_model=ResponseSchema[ApiKeyRead], dependencies=[Depends(require_permission(API_KEY_READ))])
async def get_api_key(key_id:int,service:SystemService=Depends(get_system_service)):
    return ResponseSchema(data=ApiKeyRead.model_validate(service.serialize_api_key(await service.get_api_key(key_id))))


@router.put("/api-keys/{key_id}", response_model=ResponseSchema[ApiKeyRead], dependencies=[Depends(require_permission(API_KEY_UPDATE))])
async def update_api_key(key_id:int,data:ApiKeyUpdate,service:SystemService=Depends(get_system_service)):
    return ResponseSchema(data=ApiKeyRead.model_validate(service.serialize_api_key(await service.update_api_key(key_id,data))))


@router.post("/api-keys/{key_id}/rotate", response_model=ResponseSchema[ApiKeyCreated], dependencies=[Depends(require_permission(API_KEY_UPDATE))])
async def rotate_api_key(key_id:int,service:SystemService=Depends(get_system_service)):
    item,key=await service.rotate_api_key(key_id); return ResponseSchema(data=ApiKeyCreated.model_validate(service.serialize_api_key(item,key)))


@router.delete("/api-keys/{key_id}", response_model=ResponseSchema[None], dependencies=[Depends(require_permission(API_KEY_DELETE))])
async def delete_api_key(key_id:int,service:SystemService=Depends(get_system_service)):
    await service.delete_api_key(key_id); return ResponseSchema(data=None)


@router.get("/audit-logs", response_model=ResponseSchema[PageResult[AuditLogRead]], dependencies=[Depends(require_permission(AUDIT_READ))])
async def list_audit_logs(page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),user_id:int|None=Query(None,ge=1),action:str|None=None,resource:str|None=None,status:Literal['success','failed']|None=None,keyword:str|None=None,start_date:date|None=None,end_date:date|None=None,service:SystemService=Depends(get_system_service)):
    start_at=datetime.combine(start_date,time.min) if start_date else None; end_at=datetime.combine(end_date+timedelta(days=1),time.min) if end_date else None
    items,total=await service.audit.search_page((page-1)*page_size,page_size,user_id,action,resource,status,keyword,start_at,end_at)
    return ResponseSchema(data=PageResult(items=[AuditLogRead.model_validate(service.serialize_audit(i)) for i in items],total=total,page=page,page_size=page_size))


@router.get("/alerts", response_model=ResponseSchema[list[AlertRead]], dependencies=[Depends(require_permission(ALERT_READ))])
async def list_alerts(status:str|None=None,severity:str|None=None,service:SystemService=Depends(get_system_service)):
    return ResponseSchema(data=[AlertRead.model_validate(service.serialize_alert(i)) for i in await service.alerts.list_filtered(status,severity)])


@router.post("/alerts", response_model=ResponseSchema[AlertRead], dependencies=[Depends(require_permission(ALERT_CREATE))])
async def create_alert(data:AlertCreate,service:SystemService=Depends(get_system_service)):
    return ResponseSchema(data=AlertRead.model_validate(service.serialize_alert(await service.create_alert(data))))


@router.put("/alerts/{alert_id}", response_model=ResponseSchema[AlertRead], dependencies=[Depends(require_permission(ALERT_UPDATE))])
async def update_alert(alert_id:int,data:AlertUpdate,service:SystemService=Depends(get_system_service)):
    return ResponseSchema(data=AlertRead.model_validate(service.serialize_alert(await service.update_alert(alert_id,data))))


@router.post("/alerts/{alert_id}/acknowledge", response_model=ResponseSchema[AlertRead])
async def acknowledge_alert(alert_id:int,current_user:User=Depends(require_permission(ALERT_HANDLE)),service:SystemService=Depends(get_system_service)):
    return ResponseSchema(data=AlertRead.model_validate(service.serialize_alert(await service.handle_alert(alert_id,'acknowledge',current_user))))


@router.post("/alerts/{alert_id}/resolve", response_model=ResponseSchema[AlertRead])
async def resolve_alert(alert_id:int,current_user:User=Depends(require_permission(ALERT_HANDLE)),service:SystemService=Depends(get_system_service)):
    return ResponseSchema(data=AlertRead.model_validate(service.serialize_alert(await service.handle_alert(alert_id,'resolve',current_user))))


@router.delete("/alerts/{alert_id}", response_model=ResponseSchema[None], dependencies=[Depends(require_permission(ALERT_DELETE))])
async def delete_alert(alert_id:int,service:SystemService=Depends(get_system_service)):
    if not await service.alerts.delete_by_id(alert_id):
        from src.core.exceptions import BizException
        raise BizException(code=404,message='系统告警不存在')
    return ResponseSchema(data=None)


@router.get("/alert-rules", response_model=ResponseSchema[list[AlertRuleRead]], dependencies=[Depends(require_permission(ALERT_READ))])
async def list_rules(service:SystemService=Depends(get_system_service)):
    return ResponseSchema(data=[AlertRuleRead.model_validate(service.serialize_rule(i)) for i in await service.rules.get_all()])


@router.post("/alert-rules", response_model=ResponseSchema[AlertRuleRead])
async def create_rule(data:AlertRuleCreate,current_user:User=Depends(require_permission(ALERT_CREATE)),service:SystemService=Depends(get_system_service)):
    return ResponseSchema(data=AlertRuleRead.model_validate(service.serialize_rule(await service.create_rule(data,current_user))))


@router.put("/alert-rules/{rule_id}", response_model=ResponseSchema[AlertRuleRead], dependencies=[Depends(require_permission(ALERT_UPDATE))])
async def update_rule(rule_id:int,data:AlertRuleUpdate,service:SystemService=Depends(get_system_service)):
    return ResponseSchema(data=AlertRuleRead.model_validate(service.serialize_rule(await service.update_rule(rule_id,data))))


@router.delete("/alert-rules/{rule_id}", response_model=ResponseSchema[None], dependencies=[Depends(require_permission(ALERT_DELETE))])
async def delete_rule(rule_id:int,service:SystemService=Depends(get_system_service)):
    if not await service.rules.delete_by_id(rule_id):
        from src.core.exceptions import BizException
        raise BizException(code=404,message='告警规则不存在')
    return ResponseSchema(data=None)


@router.get("/settings", response_model=ResponseSchema[SystemSettingsRead], dependencies=[Depends(require_permission(SETTINGS_READ))])
async def get_settings(service:SystemService=Depends(get_system_service)):
    return ResponseSchema(data=SystemSettingsRead.model_validate(service.serialize_settings(await service.get_settings())))


@router.put("/settings", response_model=ResponseSchema[SystemSettingsRead])
async def update_settings(data:SystemSettingsUpdate,current_user:User=Depends(require_permission(SETTINGS_UPDATE)),service:SystemService=Depends(get_system_service)):
    return ResponseSchema(data=SystemSettingsRead.model_validate(service.serialize_settings(await service.update_settings(data,current_user))))
