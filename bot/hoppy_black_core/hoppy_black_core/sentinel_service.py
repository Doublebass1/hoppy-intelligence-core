
import asyncio
import logging
import os
from intel_modules import IntelModules
from stealth_layer import stealth

logger = logging.getLogger("hoppy.sentinel")

class SentinelService:
    def __init__(self, bot_app=None):
        self.bot_app = bot_app
        self.intel = IntelModules(session=stealth.get_session())
        self.watch_list = [] # Lista de termos para monitorar
        self.is_running = False
        self.admin_chat_id = os.environ.get("ADMIN_CHAT_ID")

    def add_target(self, term):
        if term not in self.watch_list:
            self.watch_list.append(term)
            return True
        return False

    async def run_monitoring_cycle(self):
        """Ciclo de monitoramento contínuo."""
        self.is_running = True
        logger.info("🚨 Sentinel Service: Iniciando monitoramento 24/7...")

        while self.is_running:
            for term in self.watch_list:
                logger.info(f"🔍 Sentinel: Verificando novas ameaças para '{term}'...")
                
                # Busca em bases de vazamento
                results = self.intel.search_intelx(term)
                
                if results and isinstance(results, list) and len(results) > 0:
                    # Se encontrou algo novo, alerta o admin no Telegram
                    message = (
                        f"🚨 <b>ALERTA SENTINEL: Nova Ameaça Detectada!</b>\n\n"
                        f"🎯 <b>Termo:</b> <code>{term}</code>\n"
                        f"📂 <b>Fonte:</b> Intelligence X / Deep Web\n"
                        f"📄 <b>Detalhes:</b> {len(results)} novos seletores encontrados."
                    )
                    
                    if self.bot_app and self.admin_chat_id:
                        await self.bot_app.bot.send_message(
                            chat_id=self.admin_chat_id,
                            text=message,
                            parse_mode="HTML"
                        )
                
                # Espera entre termos para não sobrecarregar as APIs
                await asyncio.sleep(60)

            # Espera 1 hora para o próximo ciclo completo
            await asyncio.sleep(3600)

    def stop(self):
        self.is_running = False
