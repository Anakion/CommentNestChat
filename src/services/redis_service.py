import redis.asyncio as redis


class RedisService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )

    async def store_captcha(self, session_id: str, captcha_text: str, expire_seconds: int = 300):
        await self.redis_client.setex(f"captcha:{session_id}", expire_seconds, captcha_text)

    async def get_captcha(self, session_id: str) -> str:
        return await self.redis_client.get(f"captcha:{session_id}")

    async def delete_captcha(self, session_id: str):
        """Удаляет CAPTCHA из Redis"""
        key = f"captcha:{session_id}"
        result = await self.redis_client.delete(key)
        return result > 0  # True если ключ был удалён


