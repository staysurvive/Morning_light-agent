from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import BizException
from src.modules.prompt.model import Prompt, PromptVersion
from src.modules.prompt.repository import PromptRepository, PromptVersionRepository
from src.modules.prompt.schema import PromptCreate, PromptUpdate
from src.modules.user.model import User


def _variables_to_json(variables) -> list[dict]:
    return [item.model_dump() for item in variables]


class PromptService:
    def __init__(self, db: AsyncSession):
        self.repo = PromptRepository(db)
        self.version_repo = PromptVersionRepository(db)

    async def create_prompt(self, data: PromptCreate, current_user: User) -> Prompt:
        name = data.name.strip()
        if await self.repo.get_by_name(name):
            raise BizException(code=400, message="Prompt 名称已存在")
        variable_names = [item.name for item in data.variables]
        if len(variable_names) != len(set(variable_names)):
            raise BizException(code=400, message="Prompt 变量名不能重复")
        prompt = Prompt(
            name=name,
            description=data.description.strip() if data.description else None,
            category=data.category.strip(),
            tags=list(dict.fromkeys(tag.strip() for tag in data.tags if tag.strip())),
            content=data.content,
            variables=_variables_to_json(data.variables),
            version="v1.0",
            status="draft",
            creator=current_user,
        )
        return await self.repo.create(prompt)

    async def get_prompt(self, prompt_id: int) -> Prompt:
        prompt = await self.repo.get_by_id(prompt_id)
        if not prompt:
            raise BizException(code=404, message="Prompt 不存在")
        return prompt

    async def search_page(self, offset: int, limit: int, keyword: str | None):
        return await self.repo.search_page(offset, limit, keyword)

    async def update_prompt(self, prompt_id: int, data: PromptUpdate) -> Prompt:
        prompt = await self.get_prompt(prompt_id)
        values = data.model_dump(exclude_unset=True)
        if data.name is not None:
            name = data.name.strip()
            duplicate = await self.repo.get_by_name(name)
            if duplicate and duplicate.id != prompt.id:
                raise BizException(code=400, message="Prompt 名称已存在")
            prompt.name = name
        if "description" in values:
            prompt.description = data.description.strip() if data.description else None
        if data.category is not None:
            prompt.category = data.category.strip()
        if data.tags is not None:
            prompt.tags = list(dict.fromkeys(tag.strip() for tag in data.tags if tag.strip()))
        if data.content is not None:
            prompt.content = data.content
        if data.variables is not None:
            variable_names = [item.name for item in data.variables]
            if len(variable_names) != len(set(variable_names)):
                raise BizException(code=400, message="Prompt 变量名不能重复")
            prompt.variables = _variables_to_json(data.variables)
        if values:
            prompt.status = "draft"
        return await self.repo.update(prompt)

    async def delete_prompt(self, prompt_id: int) -> None:
        if not await self.repo.delete_by_id(prompt_id):
            raise BizException(code=404, message="Prompt 不存在")

    async def publish_prompt(self, prompt_id: int, changelog: str | None, current_user: User) -> Prompt:
        prompt = await self.get_prompt(prompt_id)
        version = await self.version_repo.next_version(prompt_id)
        await self.version_repo.clear_current(prompt_id)
        snapshot = PromptVersion(
            prompt_id=prompt.id,
            version=version,
            content=prompt.content,
            variables=prompt.variables,
            changelog=changelog.strip() if changelog else None,
            is_current=True,
            publisher=current_user,
        )
        await self.version_repo.create(snapshot)
        prompt.version = version
        prompt.status = "published"
        return await self.repo.update(prompt)

    async def list_versions(self, prompt_id: int) -> list[PromptVersion]:
        await self.get_prompt(prompt_id)
        return await self.version_repo.list_for_prompt(prompt_id)

    async def rollback_prompt(self, prompt_id: int, version: str, current_user: User) -> Prompt:
        prompt = await self.get_prompt(prompt_id)
        target = await self.version_repo.get_by_version(prompt_id, version)
        if not target:
            raise BizException(code=404, message="Prompt 版本不存在")
        prompt.content = target.content
        prompt.variables = target.variables
        new_version = await self.version_repo.next_version(prompt_id)
        await self.version_repo.clear_current(prompt_id)
        snapshot = PromptVersion(
            prompt_id=prompt.id,
            version=new_version,
            content=target.content,
            variables=target.variables,
            changelog=f"回滚至 {version}",
            is_current=True,
            publisher=current_user,
        )
        await self.version_repo.create(snapshot)
        prompt.version = new_version
        prompt.status = "published"
        return await self.repo.update(prompt)
