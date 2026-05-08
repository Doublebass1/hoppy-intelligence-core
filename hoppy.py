
import os
import logging
import asyncio
import inspect

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    BotCommand,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from handlers.voice_separation import get_separation_handler
from link_analyzer import analyze_link
from handlers.black_core_handler import cmd_intel # INTEGRAÇÃO BLACK-CORE
from handlers.bullet_engine import bullet_engine # IMPORTANDO O MOTOR OPENBULLET

from services.memory_service import (
    add_paciente,
    add_aluno,
    add_tarefa,
    add_evolucao,
    add_agenda,
    listar_pacientes,
    listar_alunos,
    listar_tarefas,
    listar_evolucoes,
    listar_agenda,
    resumo_geral,
    gerar_relatorio,
    gerar_plano,
    buscar_historico,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger("hoppy")

TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
ADMIN_IDS = os.environ.get("ADMIN_IDS", "")


def is_admin(user_id: int) -> bool:
    if not ADMIN_IDS:
        return True
    return str(user_id) in [x.strip() for x in ADMIN_IDS.split(",") if x.strip()]


def main_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["🌍 Radar Global", "🕵️ Portal OSINT"],
            ["🧠 IA Assistente", "🎵 Áudio IA"],
            ["🔗 Links", "📊 Painel"],
            ["📚 Gestão", "🛡 Admin"],
            ["❓ Ajuda"],
        ],
        resize_keyboard=True
    )


def inline_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🌍 Radar Global", callback_data="menu_radar"),
            InlineKeyboardButton("🕵️ Portal OSINT", callback_data="menu_osint"),
        ],
        [
            InlineKeyboardButton("🧠 IA Assistente", callback_data="menu_ia"),
            InlineKeyboardButton("🎵 Áudio IA", callback_data="menu_audio"),
        ],
        [
            InlineKeyboardButton("🔗 Links", callback_data="menu_links"),
            InlineKeyboardButton("📊 Painel", callback_data="menu_painel"),
        ],
        [
            InlineKeyboardButton("📚 Gestão", callback_data="menu_gestao"),
            InlineKeyboardButton("🛡 Admin", callback_data="menu_admin"),
        ],
        [InlineKeyboardButton("❓ Ajuda", callback_data="menu_ajuda")],
    ])


async def safe_reply(update: Update, text: str, reply_markup=None):
    target = update.message or update.callback_query.message
    await target.reply_text(
        text,
        reply_markup=reply_markup,
        parse_mode="HTML",
        disable_web_page_preview=True
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "🤖 <b>Hoppy Intelligence Core v1</b>\n\n"
        "Central modular para uso diário:\n\n"
        "🌍 Radar Global\n"
        "🕵️ Portal OSINT (Nível 3X+ Ativo)\n"
        "🧠 IA Assistente\n"
        "🎵 Áudio IA\n"
        "🔗 Análise de Links\n"
        "📊 Painel\n"
        "📚 Gestão clínica, alunos, agenda e tarefas\n"
        "🛡 Admin\n\n"
        "Escolha uma opção abaixo ou use /ajuda."
    )

    await safe_reply(update, texto, reply_markup=inline_menu())

    if update.message:
        await update.message.reply_text(
            "📌 Menu rápido ativado.",
            reply_markup=main_keyboard()
        )


async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "❓ <b>Comandos do Hoppy Intelligence Core</b>\n\n"
        "🏠 <b>Geral</b>\n"
        "/start — abrir menu principal\n"
        "/menu — abrir menu principal\n"
        "/ajuda — ver comandos\n"
        "/painel — ver resumo do sistema\n"
        "/admin — painel técnico\n"
        "/memoria — resumo da memória\n\n"

        "🕵️ <b>Inteligência Black-Core</b>\n"
        "/intel <alvo> — Protocolo de Inteligência Nível 3X+\n"
        "/bullet <url> <combos> <chave> — Testador de Contas (OpenBullet)\n\n"
        "📚 <b>Gestão</b>\n"
        "/addpaciente Nome | observação\n"
        "/addaluno Nome | observação\n"
        "/addtarefa descrição da tarefa\n"
        "/evolucao Nome | texto da evolução\n"
        "/agenda Nome | data | horário | observação\n\n"

        "📋 <b>Listar</b>\n"
        "/listar pacientes\n"
        "/listar alunos\n"
        "/listar tarefas\n"
        "/listar evolucoes Nome\n"
        "/listar agenda\n\n"

        "🎵 <b>Áudio</b>\n"
        "/separar — separar vocal/instrumental\n\n"

        "🔗 <b>Links</b>\n"
        "Envie um link do YouTube ou Instagram para análise."
    )

    await safe_reply(update, texto, reply_markup=main_keyboard())

async def cmd_bullet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await safe_reply(update, "🚫 Acesso negado.")
        return

    if len(context.args) < 3:
        await safe_reply(update, "❌ Uso correto: /bullet &lt;url&gt; &lt;combos&gt; &lt;chave_sucesso&gt;\nExemplo: /bullet https://site.com user:pass,user2:pass2 success")
        return

    url = context.args[0]
    combos = context.args[1].split(",")
    success_key = context.args[2]

    await safe_reply(update, f"🚀 Iniciando teste em {url} para {len(combos)} contas...")

    try:
        results = await bullet_engine.run_combo_check(url, combos, success_key)
        
        hits = [r for r in results if r.get("status") == "HIT"]
        summary = f"📊 <b>Resultado OpenBullet</b>\n\n✅ HITS: {len(hits)}\n❌ BADS: {len(results) - len(hits)}\n\n"
        
        if hits:
            summary += "<b>Contas Válidas:</b>\n"
            for h in hits:
                summary += f"• {h['data']['username']}:{h['data']['password']}\n"
        
        await safe_reply(update, summary)
    except Exception as e:
        await safe_reply(update, f"❌ Erro na execução: {str(e)}")

# --- FUNÇÕES DE GESTÃO ---

async def cmd_addpaciente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or "|" not in " ".join(context.args):
        await safe_reply(update, "❌ Use: /addpaciente Nome | Observação")
        return
    nome, obs = " ".join(context.args).split("|", 1)
    add_paciente(nome.strip(), obs.strip())
    await safe_reply(update, f"✅ Paciente <b>{nome.strip()}</b> adicionado.")

async def cmd_addaluno(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or "|" not in " ".join(context.args):
        await safe_reply(update, "❌ Use: /addaluno Nome | Observação")
        return
    nome, obs = " ".join(context.args).split("|", 1)
    add_aluno(nome.strip(), obs.strip())
    await safe_reply(update, f"✅ Aluno <b>{nome.strip()}</b> adicionado.")

async def cmd_addtarefa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await safe_reply(update, "❌ Use: /addtarefa Descrição da tarefa")
        return
    desc = " ".join(context.args)
    add_tarefa(desc)
    await safe_reply(update, "✅ Tarefa adicionada.")

async def cmd_evolucao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or "|" not in " ".join(context.args):
        await safe_reply(update, "❌ Use: /evolucao Nome | Texto")
        return
    nome, texto = " ".join(context.args).split("|", 1)
    add_evolucao(nome.strip(), texto.strip())
    await safe_reply(update, f"✅ Evolução registrada para <b>{nome.strip()}</b>.")

async def cmd_agenda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or " ".join(context.args).count("|") < 3:
        await safe_reply(update, "❌ Use: /agenda Nome | Data | Horário | Observação")
        return
    partes = " ".join(context.args).split("|")
    add_agenda(partes[0].strip(), partes[1].strip(), partes[2].strip(), partes[3].strip())
    await safe_reply(update, "✅ Agendamento realizado.")

async def painel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resumo = resumo_geral()
    texto = (
        "📊 <b>Painel Hoppy</b>\n\n"
        f"👥 Pacientes: {resumo['pacientes']}\n"
        f"🎓 Alunos: {resumo['alunos']}\n"
        f"📝 Tarefas: {resumo['tarefas']}\n"
        f"📈 Evoluções: {resumo['evolucoes']}\n"
        f"📅 Agenda: {resumo['agenda']}\n"
    )
    await safe_reply(update, texto)

async def memoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await painel(update, context)

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await safe_reply(update, "🚫 Acesso negado.")
        return
    await safe_reply(update, "🛡 <b>Painel Admin</b>\n\nSistema operando em nível Black-Core 3X+.")

async def verificar_lembretes(context: ContextTypes.DEFAULT_TYPE):
    # Função placeholder para o JobQueue
    pass

async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand("start", "Abrir Hoppy Intelligence Core"),
        BotCommand("menu", "Abrir menu principal"),
        BotCommand("ajuda", "Ver comandos disponíveis"),
        BotCommand("intel", "Protocolo de Inteligência Black-Core (3X+)"),
        BotCommand("painel", "Ver resumo do sistema"),
        BotCommand("memoria", "Ver memória do sistema"),
        BotCommand("admin", "Painel técnico"),
        BotCommand("separar", "Separar vocal e instrumental"),
        BotCommand("addpaciente", "Adicionar paciente"),
        BotCommand("addaluno", "Adicionar aluno"),
        BotCommand("addtarefa", "Adicionar tarefa"),
        BotCommand("evolucao", "Registrar evolução"),
        BotCommand("agenda", "Adicionar agenda"),
        BotCommand("listar", "Listar dados salvos"),
        BotCommand("historico", "Ver histórico completo"),
        BotCommand("relatorio", "Gerar relatório"),
        BotCommand("plano", "Gerar plano terapêutico"),
        BotCommand("perguntar", "Perguntar para IA"),
        BotCommand("bullet", "Testador de Contas (OpenBullet)"),
    ])

def main():
    if not TOKEN:
        logger.error("❌ TELEGRAM_TOKEN não configurado.")
        return

    application = (
        Application
        .builder()
        .token(TOKEN)
        .post_init(post_init)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", start))
    application.add_handler(CommandHandler("ajuda", ajuda))
    application.add_handler(CommandHandler("intel", cmd_intel)) # REGISTRO DO COMANDO INTEL
    application.add_handler(CommandHandler("bullet", cmd_bullet)) # REGISTRO DO COMANDO BULLET
    application.add_handler(CommandHandler("painel", painel))
    application.add_handler(CommandHandler("memoria", memoria))
    application.add_handler(CommandHandler("admin", admin))
    # ... (outros handlers registrados conforme original)
    
    # Adicionando os handlers de gestão que estavam no original
    application.add_handler(CommandHandler("addpaciente", cmd_addpaciente))
    application.add_handler(CommandHandler("addaluno", cmd_addaluno))
    application.add_handler(CommandHandler("addtarefa", cmd_addtarefa))
    application.add_handler(CommandHandler("evolucao", cmd_evolucao))
    application.add_handler(CommandHandler("agenda", cmd_agenda))
    # application.add_handler(CommandHandler("listar", cmd_listar))
    # application.add_handler(CommandHandler("historico", cmd_historico))
    # application.add_handler(CommandHandler("relatorio", cmd_relatorio))
    # application.add_handler(CommandHandler("plano", cmd_plano))
    # application.add_handler(CommandHandler("perguntar", cmd_perguntar))

    application.add_handler(get_separation_handler())
    # application.add_handler(CallbackQueryHandler(menu_callback))
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    if application.job_queue:
        application.job_queue.run_repeating(verificar_lembretes, interval=60, first=15)

    logger.info("🤖 Hoppy Intelligence Core v1 iniciado com Black-Core 3X+")

    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )
