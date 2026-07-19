import asyncio
import ipaddress
import socket
from urllib.parse import urlparse

from src.core.exceptions import BizException


async def assert_public_http_target(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise BizException(code=400, message="目标必须是有效的 HTTP(S) 地址")
    try:
        addresses = await asyncio.get_running_loop().run_in_executor(
            None,
            lambda: socket.getaddrinfo(
                parsed.hostname,
                parsed.port or (443 if parsed.scheme == "https" else 80),
                type=socket.SOCK_STREAM,
            ),
        )
    except socket.gaierror as exc:
        raise BizException(code=400, message="目标域名无法解析") from exc
    for address in {item[4][0] for item in addresses}:
        ip = ipaddress.ip_address(address)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
            raise BizException(code=400, message="禁止访问内网、回环或保留地址")
