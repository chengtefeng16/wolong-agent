"""
Meta Direct BSP Provider
直连 Meta Graph API，不经过第三方 BSP。
适合：已拥有自己 Meta App 的技术型客户，或作为 Tech Provider 运营。
"""
from __future__ import annotations

import ssl
import json
import urllib.request
import urllib.parse

from ...config import get_settings
from .interface import BSPProvider, SendResult, WABACredentials


class MetaDirectProvider:
    """
    实现 BSPProvider Protocol，直连 Meta Graph API v20.0。

    Embedded Signup v4 流程：
      前端 → FB.login(scope=whatsapp_business_management,business_management)
           → 用户授权 → callback 拿到 code
      code → POST /auth/token (本服务) → exchange_signup_code() → WABACredentials
    """

    def __init__(self):
        self._settings = get_settings()
        self._ssl_ctx = ssl.create_default_context()
        # Railway 上不需要跳过校验；本地代理可能需要。生产应保持默认（验证）。
        # self._ssl_ctx.check_hostname = False
        # self._ssl_ctx.verify_mode = ssl.CERT_NONE

    def _base_url(self) -> str:
        return f"https://graph.facebook.com/{self._settings.meta_api_version}"

    def _get(self, path: str, params: dict) -> dict:
        url = f"{self._base_url()}{path}?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url)
        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=self._ssl_ctx))
        with opener.open(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _post(self, path: str, payload: dict, token: str) -> dict:
        url = f"{self._base_url()}{path}"
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            url, data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            method="POST",
        )
        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=self._ssl_ctx))
        with opener.open(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))

    async def exchange_signup_code(self, code: str) -> WABACredentials:
        """
        Step 1: 用 code 换 user access token
        Step 2: 换成 system user access token（长期有效）
        Step 3: 查询该用户下的 WABA + 号码
        """
        s = self._settings

        # 1. code → short-lived user token
        token_resp = self._get("/oauth/access_token", {
            "client_id": s.meta_app_id,
            "client_secret": s.meta_app_secret,
            "code": code,
        })
        if "error" in token_resp:
            raise ValueError(f"Token exchange failed: {token_resp['error']}")
        user_token = token_resp["access_token"]

        # 2. 获取该用户下的 WABA 列表
        waba_resp = self._get("/me/whatsapp_business_accounts", {
            "access_token": user_token,
            "fields": "id,name",
        })
        wabas = waba_resp.get("data", [])
        if not wabas:
            raise ValueError("No WhatsApp Business Account found. Please complete Meta Business setup first.")
        waba_id = wabas[0]["id"]  # 取第一个 WABA

        # 3. 获取该 WABA 下的号码
        phones_resp = self._get(f"/{waba_id}/phone_numbers", {
            "access_token": user_token,
            "fields": "id,display_phone_number,verified_name",
        })
        phones = phones_resp.get("data", [])
        if not phones:
            raise ValueError("No phone numbers found in WABA. Please add a phone number first.")
        phone = phones[0]

        # 4. 生成 System User Token（长期有效，不依赖用户会话）
        # 注意：完整的 system user token 流程需要 Business Management API
        # 简化版：直接用 user_token 作为 access_token（适用于测试/MVP）
        # 生产环境应换成 System User Token：
        # https://developers.facebook.com/docs/whatsapp/business-management-api/guides/system-user-access-tokens
        access_token = user_token  # TODO: upgrade to System User Token for production

        return WABACredentials(
            waba_id=waba_id,
            phone_number_id=phone["id"],
            display_phone=phone.get("display_phone_number", ""),
            access_token=access_token,
            provider="meta_direct",
        )

    async def send_text(self, to_phone: str, text: str, credentials: WABACredentials) -> SendResult:
        phone_digits = to_phone.lstrip("+")
        try:
            resp = self._post(
                f"/{credentials.phone_number_id}/messages",
                {
                    "messaging_product": "whatsapp",
                    "to": phone_digits,
                    "type": "text",
                    "text": {"body": text, "preview_url": False},
                },
                token=credentials.access_token,
            )
            wamid = resp.get("messages", [{}])[0].get("id")
            return SendResult(sent=True, wa_message_id=wamid)
        except Exception as e:
            return SendResult(sent=False, error=str(e))

    async def subscribe_webhook(self, waba_id: str, credentials: WABACredentials) -> bool:
        """订阅 messages 字段的 webhook"""
        try:
            resp = self._post(
                f"/{waba_id}/subscribed_apps",
                {},
                token=credentials.access_token,
            )
            return resp.get("success", False)
        except Exception:
            return False


# 全局单例
_provider: MetaDirectProvider | None = None


def get_meta_provider() -> MetaDirectProvider:
    global _provider
    if _provider is None:
        _provider = MetaDirectProvider()
    return _provider
