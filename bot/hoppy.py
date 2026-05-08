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
        "🕵️ Portal OSINT\n"
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


async def painel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    r = resumo_geral()

    texto = (
        "📊 <b>Painel Hoppy</b>\n\n"
        f"🎵 Pacientes: <b>{r.get('pacientes', 0)}</b>\n"
        f"📚 Alunos: <b>{r.get('alunos', 0)}</b>\n"
        f"✅ Tarefas pendentes: <b>{r.get('tarefas', 0)}</b>\n"
        f"📝 Evoluções: <b>{r.get('evolucoes', 0)}</b>\n"
        f"🗓 Agenda: <b>{r.get('agenda', 0)}</b>\n\n"
        "🟢 Sistema online\n"
        "🧠 Memória SQLite ativa\n"
        "🌐 Tradutor/Radar rodando em background"
    )

    await safe_reply(update, texto, reply_markup=main_keyboard())


async def memoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await painel(update, context)


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await safe_reply(update, "⛔ Acesso negado.")
        return

    texto = (
        "🛡 <b>Admin Hoppy</b>\n\n"
        "✅ Railway online\n"
        "✅ Banco SQLite ativo\n"
        "✅ Bot Telegram ativo\n"
        "✅ Tradutor Telethon ativo\n"
        "✅ Scheduler ativo\n\n"
        "⚠️ Checklist:\n"
        "• TELEGRAM_TOKEN somente no Railway\n"
        "• TRADUTOR_SESSION_STRING somente no Railway\n"
        "• Não subir credentials.json no GitHub\n"
        "• Manter apenas 1 instância do bot rodando"
    )

    await safe_reply(update, texto, reply_markup=main_keyboard())


def parse_nome_obs(texto: str):
    partes = texto.split(" ", 1)
    if len(partes) < 2 or not partes[1].strip():
        return None, None

    conteudo = partes[1].strip()

    if "|" in conteudo:
        nome, obs = conteudo.split("|", 1)
        return nome.strip(), obs.strip()

    return conteudo.strip(), ""


async def cmd_addpaciente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nome, obs = parse_nome_obs(update.message.text)

    if not nome:
        await update.message.reply_text("Use assim:\n/addpaciente Nome | observação")
        return

    add_paciente(nome, obs)

    await update.message.reply_text(
        f"✅ Paciente salvo:\n\n🎵 <b>{nome}</b>\n📝 {obs or 'Sem observação'}",
        parse_mode="HTML",
        reply_markup=main_keyboard()
    )


async def cmd_addaluno(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nome, obs = parse_nome_obs(update.message.text)

    if not nome:
        await update.message.reply_text("Use assim:\n/addaluno Nome | observação")
        return

    add_aluno(nome, obs)

    await update.message.reply_text(
        f"✅ Aluno salvo:\n\n📚 <b>{nome}</b>\n📝 {obs or 'Sem observação'}",
        parse_mode="HTML",
        reply_markup=main_keyboard()
    )


async def cmd_addtarefa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    partes = update.message.text.split(" ", 1)

    if len(partes) < 2 or not partes[1].strip():
        await update.message.reply_text("Use assim:\n/addtarefa descrição da tarefa")
        return

    tarefa = partes[1].strip()
    user_id = update.effective_user.id

    add_tarefa(user_id, tarefa)

    await update.message.reply_text(
        f"✅ Tarefa salva:\n\n📌 {tarefa}",
        reply_markup=main_keyboard()
    )


async def cmd_evolucao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nome, texto = parse_nome_obs(update.message.text)

    if not nome or not texto:
        await update.message.reply_text(
            "Use assim:\n/evolucao Nome | texto da evolução\n\n"
            "Exemplo:\n/evolucao João | respondeu bem aos estímulos sonoros"
        )
        return

    add_evolucao(nome, texto)

    await update.message.reply_text(
        f"✅ Evolução salva:\n\n👤 <b>{nome}</b>\n📝 {texto}",
        parse_mode="HTML",
        reply_markup=main_keyboard()
    )


def parse_agenda(texto: str):
    partes = texto.split(" ", 1)
    if len(partes) < 2:
        return None

    campos = [x.strip() for x in partes[1].split("|")]

    if len(campos) < 3:
        return None

    nome = campos[0]
    data = campos[1]
    horario = campos[2]
    observacao = campos[3] if len(campos) >= 4 else ""

    return nome, data, horario, observacao


async def cmd_agenda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dados = parse_agenda(update.message.text)

    if not dados:
        await update.message.reply_text(
            "Use assim:\n/agenda Nome | data | horário | observação\n\n"
            "Exemplo:\n/agenda João | 10/05 | 14:00 | sessão de musicoterapia"
        )
        return

    nome, data, horario, observacao = dados
    add_agenda(nome, data, horario, observacao)

    await update.message.reply_text(
        f"✅ Agenda salva:\n\n👤 <b>{nome}</b>\n📅 {data}\n🕒 {horario}\n📝 {observacao or 'Sem observação'}",
        parse_mode="HTML",
        reply_markup=main_keyboard()
    )


async def cmd_listar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Use:\n"
            "/listar pacientes\n"
            "/listar alunos\n"
            "/listar tarefas\n"
            "/listar evolucoes Nome\n"
            "/listar agenda"
        )
        return

    tipo = context.args[0].lower()

    if tipo in ["paciente", "pacientes"]:
        dados = listar_pacientes()
        if not dados:
            await update.message.reply_text("Nenhum paciente cadastrado.")
            return

        texto = "🎵 <b>Pacientes cadastrados</b>\n\n"
        for i, nome, obs in dados:
            texto += f"#{i} — <b>{nome}</b>\n📝 {obs or 'Sem observação'}\n\n"

    elif tipo in ["aluno", "alunos"]:
        dados = listar_alunos()
        if not dados:
            await update.message.reply_text("Nenhum aluno cadastrado.")
            return

        texto = "📚 <b>Alunos cadastrados</b>\n\n"
        for i, nome, obs in dados:
            texto += f"#{i} — <b>{nome}</b>\n📝 {obs or 'Sem observação'}\n\n"

    elif tipo in ["tarefa", "tarefas"]:
        dados = listar_tarefas()
        if not dados:
            await update.message.reply_text("Nenhuma tarefa cadastrada.")
            return

        texto = "✅ <b>Tarefas cadastradas</b>\n\n"
        for i, tarefa, status in dados:
            texto += f"#{i} — {tarefa}\n📌 Status: {status}\n\n"

    elif tipo in ["evolucao", "evolucoes", "evoluções"]:
        if len(context.args) < 2:
            await update.message.reply_text("Use assim:\n/listar evolucoes Nome")
            return

        nome = " ".join(context.args[1:])
        dados = listar_evolucoes(nome)

        if not dados:
            await update.message.reply_text(f"Nenhuma evolução encontrada para {nome}.")
            return

        texto = f"📝 <b>Evoluções de {nome}</b>\n\n"
        for i, evo, data in dados:
            texto += f"#{i} — {data}\n{evo}\n\n"

    elif tipo == "agenda":
        dados = listar_agenda()

        if not dados:
            await update.message.reply_text("Agenda vazia.")
            return

        texto = "🗓 <b>Agenda cadastrada</b>\n\n"
        for i, nome, data, horario, obs in dados:
            texto += f"#{i} — <b>{nome}</b>\n📅 {data} às {horario}\n📝 {obs or 'Sem observação'}\n\n"

    else:
        texto = "Tipo inválido. Use: pacientes, alunos, tarefas, evolucoes ou agenda."

    await update.message.reply_text(
        texto[:4000],
        parse_mode="HTML",
        reply_markup=main_keyboard()
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    respostas = {
        "menu_radar": (
            "🌍 <b>Radar Global</b>\n\n"
            "Central de monitoramento e tradução.\n\n"
            "• Tradutor automático ativo\n"
            "• 19 grupos monitorados\n"
            "• Classificação por tema e urgência\n\n"
            "Próximo módulo: feeds, clusters e alertas IA."
        ),
        "menu_osint": (
            "🕵️ <b>Portal OSINT</b>\n\n"
            "Módulo de inteligência aberta e curadoria.\n\n"
            "Base futura:\n"
            "• Telegram Discovery\n"
            "• Ahmia\n"
            "• Shodan\n"
            "• SpiderFoot\n"
            "• Grafos estilo Maltego\n\n"
            "Uso permitido: pesquisa ética, fontes públicas e análise defensiva."
        ),
        "menu_ia": (
            "🧠 <b>IA Assistente</b>\n\n"
            "Em breve:\n"
            "• memória contextual\n"
            "• resumos\n"
            "• relatórios\n"
            "• análise clínica\n"
            "• suporte à gestão"
        ),
        "menu_audio": (
            "🎵 <b>Áudio IA</b>\n\n"
            "Use /separar para iniciar.\n\n"
            "Próximos recursos:\n"
            "• BPM\n"
            "• tonalidade\n"
            "• transcrição\n"
            "• análise musical"
        ),
        "menu_links": (
            "🔗 <b>Links</b>\n\n"
            "Envie um link do YouTube ou Instagram para análise automática."
        ),
        "menu_gestao": (
            "📚 <b>Gestão</b>\n\n"
            "/addpaciente Nome | observação\n"
            "/addaluno Nome | observação\n"
            "/addtarefa descrição\n"
            "/evolucao Nome | texto da evolução\n"
            "/agenda Nome | data | horário | observação\n"
            "/listar pacientes\n"
            "/listar evolucoes Nome\n"
            "/listar agenda"
        ),
    }

    if data == "menu_painel":
        await painel(update, context)
        return

    if data == "menu_admin":
        await admin(update, context)
        return

    if data == "menu_ajuda":
        await ajuda(update, context)
        return

    texto = respostas.get(data, "Opção em desenvolvimento.")

    await query.message.reply_text(
        texto,
        parse_mode="HTML",
        reply_markup=main_keyboard(),
        disable_web_page_preview=True
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message or not message.text:
        return

    text = message.text.strip()

    botoes = {
        "🌍 radar global": "menu_radar",
        "🕵️ portal osint": "menu_osint",
        "🧠 ia assistente": "menu_ia",
        "🎵 áudio ia": "menu_audio",
        "🔗 links": "menu_links",
        "📊 painel": "menu_painel",
        "📚 gestão": "menu_gestao",
        "🛡 admin": "menu_admin",
        "❓ ajuda": "menu_ajuda",
    }

    if text.lower() in botoes:
        data = botoes[text.lower()]
        if data == "menu_painel":
            await painel(update, context)
        elif data == "menu_admin":
            await admin(update, context)
        elif data == "menu_ajuda":
            await ajuda(update, context)
        else:
            await update.message.reply_text(
                "Use os botões do menu ou /ajuda para ver os comandos.",
                reply_markup=inline_menu()
            )
        return

    if "http" not in text:
        return

    processing_msg = await message.reply_text("🔍 Analisando o link, aguarde...")

    try:
        if inspect.iscoroutinefunction(analyze_link):
            analysis = await analyze_link(text)
        else:
            analysis = await asyncio.to_thread(analyze_link, text)

        await processing_msg.edit_text(
            str(analysis)[:4000],
            disable_web_page_preview=True
        )

    except Exception as e:
        logger.exception(f"Erro ao analisar link: {e}")
        await processing_msg.edit_text(
            "❌ Erro ao analisar o link. Tente novamente mais tarde."
        )


async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand("start", "Abrir Hoppy Intelligence Core"),
        BotCommand("menu", "Abrir menu principal"),
        BotCommand("ajuda", "Ver comandos disponíveis"),
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
    ])


async def verificar_lembretes(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Verificação periódica executada.")


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
    application.add_handler(CommandHandler("painel", painel))
    application.add_handler(CommandHandler("memoria", memoria))
    application.add_handler(CommandHandler("admin", admin))

    application.add_handler(CommandHandler("addpaciente", cmd_addpaciente))
    application.add_handler(CommandHandler("addaluno", cmd_addaluno))
    application.add_handler(CommandHandler("addtarefa", cmd_addtarefa))
    application.add_handler(CommandHandler("evolucao", cmd_evolucao))
    application.add_handler(CommandHandler("agenda", cmd_agenda))
    application.add_handler(CommandHandler("listar", cmd_listar))

    application.add_handler(get_separation_handler())

    application.add_handler(CallbackQueryHandler(menu_callback))

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
    )

    if application.job_queue:
        application.job_queue.run_repeating(verificar_lembretes, interval=60, first=15)

    logger.info("🤖 Hoppy Intelligence Core v1 iniciado")

    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()