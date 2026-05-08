"""run_all.py — inicia Hoppy principal + Tradutor em paralelo.

No Railway, use: web: python bot/run_all.py
O Hoppy fica na thread principal; o Tradutor roda em thread separada com seu próprio event loop.
"""
import asyncio
import logging
import threading
import traceback

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)


def iniciar_tradutor_thread():
    try:
        logger.info("🌐 Iniciando Bot Tradutor...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        from tradutor import main as tradutor_main
        logger.info("✅ Bot Tradutor importado com sucesso")
        loop.run_until_complete(tradutor_main())
    except Exception:
        logger.error("❌ Bot Tradutor caiu:")
        logger.error(traceback.format_exc())


def main():
    tradutor_thread = threading.Thread(
        target=iniciar_tradutor_thread,
        name="Thread-Tradutor",
        daemon=True,
    )
    tradutor_thread.start()
    logger.info("✅ Bot Tradutor iniciado em background")

    try:
        logger.info("🤖 Iniciando Hoppy Intelligence Core...")
        from hoppy import main as hoppy_main
        hoppy_main()
    except Exception:
        logger.error("❌ Hoppy Intelligence Core caiu:")
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    main()
