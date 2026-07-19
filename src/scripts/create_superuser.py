import argparse
import asyncio
from getpass import getpass

from src.infra.database import AsyncSessionLocal
from src.modules.user.schema import UserCreate
from src.modules.user.service import UserService


async def create_superuser(username: str, email: str, password: str) -> None:
    async with AsyncSessionLocal() as db:
        service = UserService(db)
        if await service.repo.get_by_username(username):
            raise ValueError(f"用户 {username} 已存在")
        user = await service.create_user(
            UserCreate(username=username, email=email, password=password)
        )
        user.is_superuser = True
        await db.commit()
        print(f"已创建超级管理员：{user.username}（ID {user.id}）")


def main() -> None:
    parser = argparse.ArgumentParser(description="创建首个超级管理员")
    parser.add_argument("--username", required=True)
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    password = getpass("初始密码：")
    confirmation = getpass("确认密码：")
    if not password or password != confirmation:
        raise SystemExit("两次密码不一致或密码为空")
    asyncio.run(create_superuser(args.username, args.email, password))


if __name__ == "__main__":
    main()
