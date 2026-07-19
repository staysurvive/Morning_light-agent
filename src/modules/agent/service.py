from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import BizException
from src.modules.agent.model import Agent, AgentVersion
from src.modules.agent.repository import AgentRepository, AgentVersionRepository
from src.modules.agent.schema import AgentCreate, AgentUpdate
from src.modules.model.repository import ModelRepository
from src.modules.user.model import User


class AgentService:
    def __init__(self, db: AsyncSession):
        self.repo = AgentRepository(db)
        self.version_repo = AgentVersionRepository(db)
        self.model_repo = ModelRepository(db)

    async def _validate_model(self, model_id: int | None) -> None:
        if model_id is not None and not await self.model_repo.get_by_id(model_id):
            raise BizException(code=400, message="模型不存在")

    async def create_agent(self, data: AgentCreate, current_user: User) -> Agent:
        name = data.name.strip()
        if await self.repo.get_by_name(name):
            raise BizException(code=400, message="Agent 名称已存在")
        await self._validate_model(data.model_id)
        return await self.repo.create(Agent(
            name=name,
            description=data.description.strip() if data.description else None,
            type=data.type,
            status="draft",
            model_id=data.model_id,
            config=data.config,
            version="v0.1",
            creator=current_user,
        ))

    async def get_agent(self, agent_id: int) -> Agent:
        agent = await self.repo.get_by_id(agent_id)
        if not agent:
            raise BizException(code=404, message="Agent 不存在")
        return agent

    async def search_page(self, offset: int, limit: int, keyword: str | None):
        return await self.repo.search_page(offset, limit, keyword)

    async def update_agent(self, agent_id: int, data: AgentUpdate) -> Agent:
        agent = await self.get_agent(agent_id)
        values = data.model_dump(exclude_unset=True)
        if data.name is not None:
            name = data.name.strip()
            duplicate = await self.repo.get_by_name(name)
            if duplicate and duplicate.id != agent.id:
                raise BizException(code=400, message="Agent 名称已存在")
            agent.name = name
        if "description" in values:
            agent.description = data.description.strip() if data.description else None
        if data.type is not None:
            agent.type = data.type
        if "model_id" in values:
            await self._validate_model(data.model_id)
            agent.model_id = data.model_id
        if data.config is not None:
            agent.config = data.config
        if values:
            agent.status = "draft"
        return await self.repo.update(agent)

    async def delete_agent(self, agent_id: int) -> None:
        if not await self.repo.delete_by_id(agent_id):
            raise BizException(code=404, message="Agent 不存在")

    async def publish_agent(self, agent_id: int, changelog: str | None, current_user: User) -> Agent:
        agent = await self.get_agent(agent_id)
        if agent.model_id is None:
            raise BizException(code=400, message="发布前必须配置模型")
        version = await self.version_repo.next_version(agent_id)
        await self.version_repo.clear_current(agent_id)
        await self.version_repo.create(AgentVersion(
            agent_id=agent.id,
            version=version,
            name=agent.name,
            description=agent.description,
            type=agent.type,
            model_id=agent.model_id,
            config=agent.config,
            changelog=changelog.strip() if changelog else None,
            is_current=True,
            publisher=current_user,
        ))
        agent.version = version
        agent.status = "inactive"
        return await self.repo.update(agent)

    async def list_versions(self, agent_id: int) -> list[AgentVersion]:
        await self.get_agent(agent_id)
        return await self.version_repo.list_for_agent(agent_id)

    async def rollback_agent(self, agent_id: int, version: str, current_user: User) -> Agent:
        agent = await self.get_agent(agent_id)
        target = await self.version_repo.get_by_version(agent_id, version)
        if not target:
            raise BizException(code=404, message="Agent 版本不存在")
        await self._validate_model(target.model_id)
        agent.name = target.name
        agent.description = target.description
        agent.type = target.type
        agent.model_id = target.model_id
        agent.config = target.config
        new_version = await self.version_repo.next_version(agent_id)
        await self.version_repo.clear_current(agent_id)
        await self.version_repo.create(AgentVersion(
            agent_id=agent.id,
            version=new_version,
            name=target.name,
            description=target.description,
            type=target.type,
            model_id=target.model_id,
            config=target.config,
            changelog=f"回滚至 {version}",
            is_current=True,
            publisher=current_user,
        ))
        agent.version = new_version
        agent.status = "inactive"
        return await self.repo.update(agent)

    async def start_agent(self, agent_id: int) -> Agent:
        agent = await self.get_agent(agent_id)
        if agent.status == "active":
            return agent
        if agent.status == "draft" or not await self.version_repo.get_by_version(agent_id, agent.version):
            raise BizException(code=400, message="请先发布 Agent 再启动")
        if agent.model_id is None:
            raise BizException(code=400, message="Agent 未配置模型")
        agent.status = "active"
        return await self.repo.update(agent)

    async def stop_agent(self, agent_id: int) -> Agent:
        agent = await self.get_agent(agent_id)
        if agent.status == "draft":
            raise BizException(code=400, message="草稿 Agent 无需停止")
        agent.status = "inactive"
        return await self.repo.update(agent)
