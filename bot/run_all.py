import threading
import logging
import time
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger(__name__)


def iniciar_blackcore():
    try:
        logger.info("🕵️ Iniciando Black-Core API...")

        import uvicorn

        uvicorn.run(
            "blackcore.main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )

    except Exception:
        logger.exception("❌ Black-Core caiu:")


def iniciar_hoppy_supervisor():
    while True:
        try:
            logger.info("🤖 Iniciando Hoppy Intelligence Core...")

            from hoppy import main as hoppy_main

            hoppy_main()

            logger.warning(
                "⚠️ Hoppy encerrou sem erro. Reiniciando em 5 segundos..."
            )

        except KeyboardInterrupt:
            logger.info("🛑 Encerramento manual detectado.")
            break

        except Exception:
            logger.exception("❌ Hoppy Intelligence Core caiu:")

        time.sleep(5)


if __name__ == "__main__":
    logger.info("🚀 Inicializando Hoppy Intelligence Core...")

    blackcore_thread = threading.Thread(
        target=iniciar_blackcore,
        daemon=True
    )

    blackcore_thread.start()
    logger.info("✅ Black-Core iniciado.")

    iniciar_hoppy_supervisor()