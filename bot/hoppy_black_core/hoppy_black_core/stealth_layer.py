
import logging
import random
import time
import requests
from stem import Signal
from stem.control import Controller

logger = logging.getLogger("hoppy.stealth")

# Lista de User-Agents comuns para mimetismo
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/119.0",
]

class StealthLayer:
    def __init__(self, tor_password=None, socks_port=9050, control_port=9051):
        self.socks_port = socks_port
        self.control_port = control_port
        self.tor_password = tor_password
        self.proxies = {
            'http': f'socks5h://localhost:{socks_port}',
            'https': f'socks5h://localhost:{socks_port}'
        }

    def get_session(self):
        """Retorna uma sessão requests configurada com Tor e User-Agent aleatório."""
        session = requests.Session()
        session.proxies = self.proxies
        session.headers.update({'User-Agent': random.choice(USER_AGENTS)})
        return session

    def rotate_identity(self):
        """Solicita um novo circuito Tor (Nova Identidade)."""
        try:
            with Controller.from_port(port=self.control_port) as controller:
                if self.tor_password:
                    controller.authenticate(password=self.tor_password)
                else:
                    controller.authenticate()  # Tenta autenticação padrão
                
                controller.signal(Signal.NEWNYM)
                logger.info("🔄 Stealth Layer: Identidade Tor rotacionada com sucesso.")
                time.sleep(controller.get_newnym_wait()) # Espera o tempo necessário para o novo circuito
        except Exception as e:
            logger.error(f"❌ Erro ao rotacionar identidade Tor: {e}")

    def check_connection(self):
        """Verifica se a conexão está realmente passando pelo Tor."""
        session = self.get_session()
        try:
            response = session.get("https://check.torproject.org/", timeout=15)
            if "Congratulations. This browser is configured to use Tor." in response.text:
                logger.info("✅ Stealth Layer: Conexão Tor verificada e ativa.")
                return True
            else:
                logger.warning("⚠️ Stealth Layer: Conexão ativa, mas NÃO detectada como Tor.")
                return False
        except Exception as e:
            logger.error(f"❌ Stealth Layer: Falha ao verificar conexão Tor: {e}")
            return False

    def get_current_ip(self):
        """Retorna o IP externo atual (útil para logs de auditoria interna)."""
        session = self.get_session()
        try:
            return session.get("https://api.ipify.org", timeout=10).text
        except:
            return "Desconhecido"

# Instância global para uso no sistema
stealth = StealthLayer()
