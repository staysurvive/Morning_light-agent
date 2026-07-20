import asyncio

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.infra.minio_client import ensure_bucket_exists
from src.core.config import get_settings
from src.middlewares.logging import LoggingMiddleware
from src.core.exceptions import register_exception_handlers
from src.core.logger import setup_logger, logger
from src.infra.database import engine
from src.modules.user.api import router as user_router
from src.modules.captcha.api import router as captcha_router
from src.modules.auth.api import router as auth_router
from src.modules.permission.api import router as permission_router
from src.modules.role.api import router as role_router
from src.modules.provider.api import router as provider_router
from src.modules.model.api import router as model_router
from src.modules.prompt.api import router as prompt_router
from src.modules.agent.api import router as agent_router
from src.modules.knowledge.api import router as knowledge_router
from src.modules.tool.api import router as tool_router
from src.modules.conversation.api import router as conversation_router
from src.modules.analytics.api import router as analytics_router
from src.modules.system.api import router as system_router
from src.modules.dashboard.api import router as dashboard_router
from src.middlewares.audit import AuditMiddleware

# 使用上下文管理器感知项目的生命周期  （主要是项目的启动和停止）
from contextlib import asynccontextmanager
@asynccontextmanager
async def  lifespan(app: FastAPI):
    # 项目启动时执行
    setup_logger()  # 配置日志记录器
    setting = get_settings()
    logger.info(f"项目{setting.APP_NAME} 启动,环境：{setting.APP_ENV}")
    # 确保minio桶的存在
    try:
        await asyncio.to_thread(ensure_bucket_exists)
    except Exception as e:
        logger.error(f"minio 桶创建失败，文件上传功能无法使用:{e}")
    yield
    # 项目停止时执行
    # 关闭数据库连接池
    await engine.dispose()
    logger.info(f"项目{setting.APP_NAME} 停止,环境：{setting.APP_ENV}")


def create_app() -> FastAPI:
    settings = get_settings()
    # 创建 应用
    app = FastAPI(title="辰光Agent", version="1.0.0", debug=settings.APP_DEBUG, lifespan=lifespan)
  
    # 注册中间件
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(AuditMiddleware)
    # 注册跨域中间件
    app.add_middleware(CORSMiddleware,allow_origins=["*"],
                       allow_credentials=True,
                       allow_methods=["*"],
                       allow_headers=["*"],
                       )

    # 注册异常处理器
    register_exception_handlers(app)
    
    # 注册路由
    app.include_router(user_router,prefix="/api/v1")  # 注册用户路由 ，前缀为 /api/v1/users
    app.include_router(captcha_router,prefix="/api/v1")  # 注册验证码路由 ，前缀为 /api/v1/
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(permission_router, prefix="/api/v1")
    app.include_router(role_router, prefix="/api/v1")
    app.include_router(provider_router, prefix="/api/v1")
    app.include_router(model_router, prefix="/api/v1")
    app.include_router(prompt_router, prefix="/api/v1")
    app.include_router(agent_router, prefix="/api/v1")
    app.include_router(knowledge_router, prefix="/api/v1")
    app.include_router(tool_router, prefix="/api/v1")
    app.include_router(conversation_router, prefix="/api/v1")
    app.include_router(analytics_router, prefix="/api/v1")
    app.include_router(system_router, prefix="/api/v1")
    app.include_router(dashboard_router, prefix="/api/v1")
    return app

app = create_app()

# 健康检查路由，能访问通，就代表应用启动成功
@app.get("/health")
async def root():
    # Prometheus规范约束，返回的状态必须为“ok”，表示系统处于健康状态
    return {"status": "ok"}
