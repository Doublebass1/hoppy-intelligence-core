"""Fluxo /separar — preparado para integração futura com motor gratuito/local."""
import logging
import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

logger = logging.getLogger(__name__)
AGUARDANDO_ENTRADA = 1

YOUTUBE_RE = re.compile(r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+", re.IGNORECASE)

async def separar_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎵 *Áudio IA — Separação de stems*\n\n"
        "Envie um link do YouTube ou um arquivo de áudio.\n\n"
        "Status atual: fluxo preparado. A separação real será plugada na próxima etapa com motor gratuito/local quando possível.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Enviar link", callback_data="sep_link"), InlineKeyboardButton("🎧 Enviar arquivo", callback_data="sep_file")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="sep_cancel")],
        ]),
    )
    return AGUARDANDO_ENTRADA

async def separar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "sep_cancel":
        await query.edit_message_text("Processo de separação cancelado.")
        return ConversationHandler.END
    await query.edit_message_text("Ok. Agora envie o link do YouTube ou o arquivo de áudio.")
    return AGUARDANDO_ENTRADA

async def receber_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_link = (update.message.text or "").strip()
    if not YOUTUBE_RE.match(user_link):
        await update.message.reply_text("⚠️ Envie um link válido do YouTube ou envie um arquivo de áudio.")
        return AGUARDANDO_ENTRADA
    await update.message.reply_text(
        "✅ Link recebido.\n\n"
        "🚧 A separação real ainda não foi ativada nesta V1.\n"
        "Próxima etapa recomendada: integrar Demucs local/off-grid ou uma fila de processamento gratuita.",
    )
    return ConversationHandler.END

async def receber_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not (update.message.audio or update.message.voice or update.message.document):
        await update.message.reply_text("⚠️ Envie um arquivo de áudio válido ou uma mensagem de voz.")
        return AGUARDANDO_ENTRADA
    await update.message.reply_text(
        "✅ Arquivo recebido.\n\n"
        "🚧 A separação real ainda não foi ativada nesta V1.\n"
        "Próxima etapa: motor local com Demucs/Spleeter quando definirmos o ambiente ideal.",
    )
    return ConversationHandler.END

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Processo cancelado.")
    return ConversationHandler.END


def get_separation_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("separar", separar_comando)],
        states={
            AGUARDANDO_ENTRADA: [
                CallbackQueryHandler(separar_callback, pattern="^sep_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receber_link),
                MessageHandler(filters.AUDIO | filters.VOICE | filters.Document.ALL, receber_audio),
            ]
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
        per_message=False,
    )
