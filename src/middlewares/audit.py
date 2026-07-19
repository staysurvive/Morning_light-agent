from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from src.infra.database import AsyncSessionLocal
from src.modules.system.model import AuditLog
from src.modules.user.model import User
from src.modules.utils.jwt_utils import verify_jwt


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        if not path.startswith("/api/v1/") or path.startswith("/api/v1/system/audit-logs"):
            return response
        token = request.headers.get("authorization", "")
        if not token.lower().startswith("bearer "):
            return response
        try:
            user_id = int(verify_jwt(token.split(" ", 1)[1]).get("sub"))
            parts = path.removeprefix("/api/v1/").split("/")
            action = parts[-1] if parts[-1] in {"start", "stop", "publish", "rollback", "test", "enable", "disable", "retry", "acknowledge", "resolve", "rotate"} else {"GET":"read","POST":"create","PUT":"update","PATCH":"update","DELETE":"delete"}.get(request.method,"other")
            async with AsyncSessionLocal() as db:
                user = await db.get(User, user_id)
                if not user:
                    return response
                query = {}
                for key, value in request.query_params.items():
                    lowered = key.lower()
                    query[key] = "***redacted***" if any(part in lowered for part in ("password", "token", "secret", "api_key", "apikey")) else value
                db.add(AuditLog(
                    user_id=user.id, user_name=user.username, action=action,
                    resource=parts[0], resource_name=path,
                    details={"method": request.method, "query": query},
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent", "")[:500],
                    status="success" if response.status_code < 400 else "failed",
                ))
                await db.commit()
        except Exception as exc:
            logger.warning(f"写入审计日志失败: {exc}")
        return response
