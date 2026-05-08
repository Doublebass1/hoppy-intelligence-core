
import logging
from bs4 import BeautifulSoup
from stealth_layer import stealth

logger = logging.getLogger("hoppy.scraper")

class OnionScraper:
    def __init__(self):
        self.stealth = stealth

    async def scrape_onion(self, url):
        """Entra em um site .onion e extrai o conteúdo principal."""
        if not url.endswith(".onion") and ".onion/" not in url:
            return "Erro: URL não pertence à rede Tor."

        logger.info(f"🕵️ Iniciando raspagem stealth em: {url}")
        
        # Rotaciona identidade para garantir anonimato
        self.stealth.rotate_identity()
        session = self.stealth.get_session()

        try:
            response = session.get(url, timeout=45)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remover scripts e estilos
                for script in soup(["script", "style"]):
                    script.extract()

                text = soup.get_text(separator=' ')
                # Limpar espaços em branco
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                clean_text = '\n'.join(chunk for chunk in chunks if chunk)

                return {
                    "title": soup.title.string if soup.title else "Sem título",
                    "content": clean_text[:5000], # Limite para o Telegram
                    "status": "Sucesso"
                }
            else:
                return f"Erro: Status Code {response.status_code}"
        except Exception as e:
            logger.error(f"Falha ao raspar site Onion: {e}")
            return f"Erro de Conexão: {e}"

scraper = OnionScraper()
