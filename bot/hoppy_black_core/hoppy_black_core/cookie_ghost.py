
import json
import logging
import os

logger = logging.getLogger("hoppy.ghost")

class CookieGhost:
    def __init__(self, storage_path="sessions/"):
        self.storage_path = storage_path
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)

    def save_session(self, name, cookies_dict):
        """Salva uma sessão de cookies capturada."""
        file_path = os.path.join(self.storage_path, f"{name}.json")
        try:
            with open(file_path, 'w') as f:
                json.dump(cookies_dict, f)
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar sessão {name}: {e}")
            return False

    def load_session(self, name):
        """Carrega uma sessão de cookies para uso imediato."""
        file_path = os.path.join(self.storage_path, f"{name}.json")
        if not os.path.exists(file_path):
            return None
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar sessão {name}: {e}")
            return None

    def inject_cookies_to_session(self, session, name):
        """Injeta cookies salvos em uma sessão aiohttp ou requests."""
        cookies = self.load_session(name)
        if cookies:
            session.cookies.update(cookies)
            return True
        return False

ghost = CookieGhost()
