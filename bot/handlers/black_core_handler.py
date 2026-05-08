import logging
import os
import requests
from telegram import Update
from telegram.ext import ContextTypes
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("hoppy.black_core")

BLACK_CORE_URL = os.environ.get("BLACK_CORE_URL", "http://127.0.0.1:8000")


async def cmd_intel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Executa uma análise Black-Core."""

    if not context.args:
        await update.message.reply_text(
            "Use assim:\n/intel nginx\n\nExemplo:\n/intel openai.com"
        )
        return

    query = " ".join(context.args)

    processing_msg = await update.message.reply_text(
        f"🕵️ Consultando Black-Core...\n\n"
        f"🎯 Alvo: {query}\n"
        "📡 Acionando agentes OSINT...\n"
        "🧠 Montando relatório executivo..."
    )

    try:
        response = requests.get(
            f"{BLACK_CORE_URL}/run_intelligence",
            params={"query": query},
            timeout=60,
        )

        if response.status_code != 200:
            await processing_msg.edit_text(
                f"❌ Erro no Black-Core.\nStatus HTTP: {response.status_code}"
            )
            return

        data = response.json()
        report = data.get("intelligence_report", {})
        analysis = report.get("analysis", "Nenhuma análise retornada.")

        await processing_msg.edit_text(
            analysis[:4000],
            parse_mode=None,
        )

    except Exception as e:
        logger.error(f"Erro na integração Black-Core: {e}")
        await processing_msg.edit_text(
            "❌ Falha de conexão com o Black-Core.\n\n"
            "Verifique se o FastAPI está rodando em:\n"
            "http://127.0.0.1:8000"
        )


async def cmd_intel_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra o histórico recente do Black-Core."""

    try:
        response = requests.get(
            f"{BLACK_CORE_URL}/intel_history",
            params={"limit": 10},
            timeout=30,
        )

        if response.status_code != 200:
            await update.message.reply_text(
                f"❌ Erro ao consultar histórico.\nStatus HTTP: {response.status_code}"
            )
            return

        data = response.json()
        history = data.get("history", [])

        if not history:
            await update.message.reply_text("📚 Nenhum relatório salvo ainda.")
            return

        texto = "📚 BLACK-CORE MEMORY\n\nÚltimos relatórios salvos:\n\n"

        for item in history:
            texto += (
                f"#{item['id']} — {item['query']}\n"
                f"Tipo: {item['target_type']} | Risco: {item['risk_score']}%\n"
                f"Achados: {item['findings_count']} | Data: {item['created_at']}\n\n"
            )

        texto += "Use: /intel_report ID"

        await update.message.reply_text(texto[:4000])

    except Exception as e:
        logger.error(f"Erro ao consultar histórico Black-Core: {e}")
        await update.message.reply_text(
            "❌ Falha ao conectar ao histórico do Black-Core."
        )


async def cmd_intel_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra um relatório salvo pelo ID."""

    if not context.args:
        await update.message.reply_text("Use assim:\n/intel_report 1")
        return

    report_id = context.args[0]

    try:
        response = requests.get(
            f"{BLACK_CORE_URL}/intel_report/{report_id}",
            timeout=30,
        )

        if response.status_code != 200:
            await update.message.reply_text(
                f"❌ Erro ao buscar relatório.\nStatus HTTP: {response.status_code}"
            )
            return

        data = response.json()

        if not data.get("ok"):
            await update.message.reply_text("❌ Relatório não encontrado.")
            return

        report = data.get("report", {})
        report_text = report.get("report_text", "Relatório vazio.")

        await update.message.reply_text(
            report_text[:4000],
            parse_mode=None,
        )

    except Exception as e:
        logger.error(f"Erro ao buscar relatório Black-Core: {e}")
        await update.message.reply_text(
            "❌ Falha ao conectar ao relatório do Black-Core."
        )


async def cmd_intel_watch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Adiciona alvo ao monitoramento Black-Core."""

    if not context.args:
        await update.message.reply_text("Use assim:\n/intel_watch openai.com")
        return

    target = " ".join(context.args)

    try:
        response = requests.get(
            f"{BLACK_CORE_URL}/intel_watch",
            params={"target": target},
            timeout=30,
        )

        if response.status_code != 200:
            await update.message.reply_text(
                f"❌ Erro ao adicionar monitoramento.\nStatus HTTP: {response.status_code}"
            )
            return

        data = response.json()

        if data.get("ok"):
            await update.message.reply_text(
                "👁️ BLACK-CORE WATCH\n\n"
                "✅ Alvo adicionado ao monitoramento.\n\n"
                f"🎯 Alvo: {data.get('target')}\n"
                f"🧬 Tipo: {data.get('target_type')}"
            )
        else:
            await update.message.reply_text(
                "👁️ BLACK-CORE WATCH\n\n"
                f"⚠️ {data.get('message')}\n\n"
                f"🎯 Alvo: {data.get('target')}\n"
                f"🧬 Tipo: {data.get('target_type')}"
            )

    except Exception as e:
        logger.error(f"Erro no intel_watch: {e}")
        await update.message.reply_text(
            "❌ Falha ao adicionar alvo ao monitoramento."
        )


async def cmd_intel_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lista alvos monitorados."""

    try:
        response = requests.get(
            f"{BLACK_CORE_URL}/intel_watchlist",
            timeout=30,
        )

        if response.status_code != 200:
            await update.message.reply_text(
                f"❌ Erro ao consultar watchlist.\nStatus HTTP: {response.status_code}"
            )
            return

        data = response.json()
        watchlist = data.get("watchlist", [])

        if not watchlist:
            await update.message.reply_text(
                "👁️ BLACK-CORE WATCHLIST\n\nNenhum alvo monitorado ainda."
            )
            return

        texto = "👁️ BLACK-CORE WATCHLIST\n\n"

        for item in watchlist:
            status_emoji = "✅" if item["status"] == "active" else "⛔"

            texto += (
                f"{status_emoji} #{item['id']} — {item['target']}\n"
                f"Tipo: {item['target_type']} | Status: {item['status']}\n"
                f"Último risco: {item['last_risk_score']}%\n"
                f"Achados: {item['last_findings_count']}\n"
                f"Atualizado: {item['updated_at']}\n\n"
            )

        texto += "Para remover:\n/intel_unwatch ID"

        await update.message.reply_text(texto[:4000])

    except Exception as e:
        logger.error(f"Erro no intel_watchlist: {e}")
        await update.message.reply_text("❌ Falha ao consultar watchlist.")


async def cmd_intel_unwatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove alvo do monitoramento."""

    if not context.args:
        await update.message.reply_text("Use assim:\n/intel_unwatch 1")
        return

    try:
        target_id = int(context.args[0])

        response = requests.get(
            f"{BLACK_CORE_URL}/intel_unwatch",
            params={"target_id": target_id},
            timeout=30,
        )

        if response.status_code != 200:
            await update.message.reply_text(
                f"❌ Erro ao remover alvo.\nStatus HTTP: {response.status_code}"
            )
            return

        data = response.json()

        if data.get("ok"):
            await update.message.reply_text(
                f"✅ Alvo #{target_id} removido do monitoramento."
            )
        else:
            await update.message.reply_text(
                f"⚠️ Não encontrei o alvo #{target_id}."
            )

    except ValueError:
        await update.message.reply_text(
            "❌ ID inválido. Use assim:\n/intel_unwatch 1"
        )

    except Exception as e:
        logger.error(f"Erro no intel_unwatch: {e}")
        await update.message.reply_text(
            "❌ Falha ao remover alvo do monitoramento."
        )


async def cmd_intel_watch_run(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Executa manualmente o monitoramento dos alvos ativos."""

    processing_msg = await update.message.reply_text(
        "👁️ BLACK-CORE WATCH RUN\n\n"
        "📡 Executando monitoramento dos alvos ativos...\n"
        "🧠 Gerando novos relatórios..."
    )

    try:
        response = requests.get(
            f"{BLACK_CORE_URL}/intel_watch_run",
            timeout=180,
        )

        if response.status_code != 200:
            await processing_msg.edit_text(
                f"❌ Erro ao executar Watch Runner.\nStatus HTTP: {response.status_code}"
            )
            return

        data = response.json()
        results = data.get("results", [])

        if not results:
            await processing_msg.edit_text(
                "👁️ BLACK-CORE WATCH RUN\n\n"
                "Nenhum alvo ativo para monitorar."
            )
            return

        texto = "👁️ BLACK-CORE WATCH RUN\n\n"
        texto += "✅ Monitoramento executado.\n\n"

        for item in results:
            risk_change = item.get("risk_change", 0)
            findings_change = item.get("findings_change", 0)

            risk_symbol = "➖"
            if risk_change > 0:
                risk_symbol = "🔺"
            elif risk_change < 0:
                risk_symbol = "🔻"

            findings_symbol = "➖"
            if findings_change > 0:
                findings_symbol = "🔺"
            elif findings_change < 0:
                findings_symbol = "🔻"

            texto += (
                f"🎯 #{item.get('id')} — {item.get('target')}\n"
                f"Tipo: {item.get('target_type')}\n"
                f"Risco: {item.get('old_risk_score')}% → {item.get('new_risk_score')}% {risk_symbol}\n"
                f"Achados: {item.get('old_findings_count')} → {item.get('new_findings_count')} {findings_symbol}\n"
                f"Relatório: /intel_report {item.get('report_id')}\n\n"
            )

        await processing_msg.edit_text(texto[:4000])

    except Exception as e:
        logger.error(f"Erro no intel_watch_run: {e}")
        await processing_msg.edit_text("❌ Falha ao executar Watch Runner.")