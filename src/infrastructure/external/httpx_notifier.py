import httpx

from src.domain.user.entities import User


class HttpxExternalNotifier:
    def __init__(self, webhook_url: str, timeout: float = 5.0) -> None:
        self._webhook_url = webhook_url
        self._timeout = timeout

    async def notify_user_registered(self, user: User) -> None:
        payload = {
            "event": "user.registered",
            "user_id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(self._webhook_url, json=payload)
            response.raise_for_status()
