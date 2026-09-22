"""
BSP Provider 抽象接口。
实现类：MetaDirectProvider（直连 Meta Graph API）
可切换至：TwilioProvider、Dialog360Provider
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class WABACredentials:
    """从 Embedded Signup 回调中提取的凭证"""
    waba_id: str
    phone_number_id: str
    display_phone: str
    access_token: str          # system user token（加密前的明文）
    provider: str = "meta_direct"


@dataclass
class SendResult:
    sent: bool
    wa_message_id: str | None = None
    error: str | None = None


@runtime_checkable
class BSPProvider(Protocol):
    """所有 BSP 必须实现的接口"""

    async def exchange_signup_code(self, code: str) -> WABACredentials:
        """
        把 Embedded Signup 返回的一次性 code 换成 WABACredentials。
        Meta Direct: 调用 GET /oauth/access_token，再查 WABA + 号码
        """
        ...

    async def send_text(
        self,
        to_phone: str,
        text: str,
        credentials: WABACredentials,
    ) -> SendResult:
        """向客户发送文本消息"""
        ...

    async def subscribe_webhook(
        self,
        waba_id: str,
        credentials: WABACredentials,
    ) -> bool:
        """订阅 WABA 的 messages webhook"""
        ...
