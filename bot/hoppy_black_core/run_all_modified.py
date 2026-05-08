
"""
run_all.py — Inicializador principal do Hoppy Intelligence Core (Versão Black-Core 3X+)
Executa:
1. Banco de dados SQLite
2. Bot Tradutor em thread separada
3. Hoppy Black-Core Orchestrator (FastAPI) em thread separada
4. Hoppy Assistant na thread principal
"""

import asyncio
import logging
import threading
import traceback
import os

try:
    from database.db import init_db
except Exception:
    init_db = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger(__name__)

def iniciar_banco():
    """Inicializa o banco de dados local."""
    if init_db is None:
        logger.warning("⚠️ Banco de dados não encontrado. Continuando sem SQLite.")
        return
    try:
        init_db()
        logger.info("✅ Banco de dados inicializado com sucesso.")
    except Exception:
        logger.error("❌ Erro ao inicializar banco de dados:")
        logger.error(traceback.format_exc())

def iniciar_tradutor_thread():
    """Inicia o Tradutor Telethon em uma thread separada."""
    try:
        logger.info("🌐 Iniciando Bot Tradutor...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        from tradutor import main as tradutor_main
        logger.info("✅ Bot Tradutor importado com sucesso.")
        loop.run_until_complete(tradutor_main())
    except Exception:
        logger.error("❌ Bot Tradutor caiu:")
        logger.error(traceback.format_exc())

def iniciar_black_core_thread():
    """Inicia o Orquestrador Black-Core (FastAPI) em uma thread separada."""
    try:
        logger.info("🕵️ Iniciando Orquestrador Black-Core (Stealth API)...")
        import uvicorn
        from main import app # Certifique-se de que o main.py do Black-Core esteja na raiz ou no PYTHONPATH
        
        # Roda o servidor FastAPI na porta 8000
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    except Exception:
        logger.error("❌ Orquestrador Black-Core caiu:")
        logger.error(traceback.format_exc())

def iniciar_hoppy():
    """Inicia o Hoppy Assistant principal."""
    try:
        logger.info("🤖 Iniciando Hoppy Intelligence Core...")
        from hoppy import main as hoppy_main
        hoppy_main()
    except Exception:
        logger.error("❌ Hoppy Intelligence Core caiu:")
        logger.error(traceback.format_exc())

def main():
    """Função principal do sistema."""
    logger.info("🚀 Inicializando Hoppy Intelligence Core X (Soberania Neural)...")

    iniciar_banco()

    # Thread 1: Bot Tradutor
    threading.Thread(
        target=iniciar_tradutor_thread,
        name="Thread-Tradutor",
        daemon=True
    ).start()
    logger.info("✅ Bot Tradutor iniciado em background.")

    # Thread 2: Black-Core Orchestrator (NOVIDADE 3X+)
    threading.Thread(
        target=iniciar_black_core_thread,
        name="Thread-BlackCore",
        daemon=True
    ).start()
    logger.info("✅ Orquestrador Black-Core iniciado em background na porta 8000.")

    # Thread Principal: Hoppy Assistant
    iniciar_hoppy()

if __name__ == "__main__":
    main()
