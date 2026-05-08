
import logging
import os
import requests
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger("hoppy.black_core")

# URL do serviço Black-Core (rodando localmente ou em outro serviço no Railway)
BLACK_CORE_URL = os.environ.get("BLACK_CORE_URL", "http://localhost:8000")

async def cmd_intel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para o comando /intel."""
    user_id = update.effective_user.id
    
    # Verificar se o usuário forneceu uma query
    if not context.args:
        await update.message.reply_text(
            "🔍 <b>Portal de Inteligência Black-Core</b>\n\n"
            "Use: <code>/intel <alvo_ou_termo></code>\n"
            "Exemplo: <code>/intel 'domain.onion'</code>",
            parse_mode="HTML"
        )
        return

    query = " ".join(context.args)
    processing_msg = await update.message.reply_text(
        f"🕵️ <b>Iniciando Protocolo Black-Core...</b>\n"
        f"Alvo: <code>{query}</code>\n\n"
        "📡 Orquestrando agentes...\n"
        "🔐 Estabelecendo conexão Stealth via Tor...\n"
        "🧠 Correlacionando dados em grafos...",
        parse_mode="HTML"
    )

    try:
        # Fazer a requisição para o orquestrador Black-Core
        response = requests.get(f"{BLACK_CORE_URL}/run_intelligence", params={"query": query}, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            report = data.get("intelligence_report", {})
            
            # Formatar o relatório para o Telegram
            analysis = report.get("analysis", "Nenhuma análise gerada.")
            risk_score = report.get("risk_score", 0)
            
            # Definir emoji de risco
            risk_emoji = "🟢"
            if risk_score > 70: risk_emoji = "🚨"
            elif risk_score > 30: risk_emoji = "⚠️"

            texto_final = (
                f"🛡 <b>Relatório de Inteligência Black-Core</b>\n\n"
                f"🎯 <b>Alvo:</b> <code>{query}</code>\n"
                f"📊 <b>Nível de Risco:</b> {risk_emoji} {risk_score}%\n\n"
                f"📝 <b>Análise Contextual (IA Local):</b>\n{analysis}\n\n"
                f"🔗 <b>Entidades Correlacionadas:</b> {len(report.get('graph_data', []))} nós no grafo.\n\n"
                f"✅ <i>Protocolo concluído com soberania neural.</i>"
            )
            
            await processing_msg.edit_text(texto_final, parse_mode="HTML")
        else:
            await processing_msg.edit_text("❌ <b>Erro no Core:</b> O serviço de inteligência não respondeu corretamente.")

    except Exception as e:
        logger.error(f"Erro na integração Black-Core: {e}")
        await processing_msg.edit_text("❌ <b>Falha Crítica:</b> Não foi possível conectar ao Hoppy Black-Core. Verifique se o serviço está online.")
