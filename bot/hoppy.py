"""
hoppy.py — Hoppy Intelligence Core v1
Interface principal do bot no Telegram.

Objetivos desta versão:
- Menu profissional com botões.
- Manter funções de gestão, IA, links e áudio.
- Acrescentar Portal OSINT seguro em modo curadoria.
- Melhorar mensagens de erro e estabilidade no Railway.
"""
import asyncio
import html
import json
import logging
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import anthropic
import gspread
from google.oauth2.service_account import Credentials
from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from handlers.voice_separation import get_separation_handler
from link_analyzer import analyze_link

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("hoppy")

# ── Variáveis de ambiente ──────────────────────────────────
TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "")
CREDENTIALS_JSON = os.environ.get("GOOGLE_CREDENTIALS_JSON", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
GMAIL_USER = os.environ.get("GMAIL_USER", "")
GMAIL_PASS = os.environ.get("GMAIL_APP_PASSWORD", "")
GMAIL_DEST = os.environ.get("GMAIL_DESTINO", "")
ADMIN_IDS = {
    int(x.strip()) for x in os.environ.get("HOPPY_ADMIN_IDS", "").split(",") if x.strip().lstrip("-").isdigit()
}

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

chat_ids = set()

# ── Utilitários ────────────────────────────────────────────
def esc(value) -> str:
    return html.escape(str(value))


def is_admin(update: Update) -> bool:
    if not ADMIN_IDS:
        return True  # modo pessoal: se não configurou admin, libera para o dono que usa o bot
    return bool(update.effective_user and update.effective_user.id in ADMIN_IDS)


def has_google_config() -> bool:
    return bool(SHEET_ID and CREDENTIALS_JSON)


def get_sheet(nome_aba):
    if not has_google_config():
        raise RuntimeError("Google Sheets não configurado. Defina GOOGLE_SHEET_ID e GOOGLE_CREDENTIALS_JSON no Railway.")
    creds_dict = json.loads(CREDENTIALS_JSON)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    try:
        return sheet.worksheet(nome_aba)
    except gspread.WorksheetNotFound:
        return sheet.add_worksheet(title=nome_aba, rows=1000, cols=20)


def garantir_cabecalhos(ws, cabecalhos):
    if not ws.row_values(1):
        ws.append_row(cabecalhos)


async def safe_reply(update: Update, text: str, **kwargs):
    if update.message:
        return await update.message.reply_text(text, parse_mode="HTML", disable_web_page_preview=True, **kwargs)
    if update.callback_query:
        return await update.callback_query.message.reply_text(text, parse_mode="HTML", disable_web_page_preview=True, **kwargs)


def enviar_email(assunto, corpo):
    if not all([GMAIL_USER, GMAIL_PASS, GMAIL_DEST]):
        return False
    try:
        msg = MIMEMultipart()
        msg["From"] = GMAIL_USER
        msg["To"] = GMAIL_DEST
        msg["Subject"] = assunto
        msg.attach(MIMEText(corpo, "plain", "utf-8"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_PASS)
            server.sendmail(GMAIL_USER, GMAIL_DEST, msg.as_string())
        return True
    except Exception as e:
        logger.error("Erro email: %s", e)
        return False


def perguntar_claude(pergunta, contexto_extra=""):
    if not ANTHROPIC_KEY:
        raise ValueError("ANTHROPIC_API_KEY não configurada no Railway.")

    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    system = (
        "Você é o Hoppy Intelligence Core, um assistente operacional de José Batista, "
        "musicoterapeuta, professor de música e criador de uma central modular de inteligência. "
        "Responda em português brasileiro, com clareza, utilidade prática e segurança. "
        "Quando o assunto for OSINT, privacidade ou redes privadas, mantenha foco defensivo, legal e ético."
    )
    if contexto_extra:
        system += f"\n\nContexto interno autorizado:\n{contexto_extra}"

    msg = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1200,
        system=system,
        messages=[{"role": "user", "content": pergunta}],
    )
    return msg.content[0].text


def buscar_contexto_paciente(nome):
    if not has_google_config():
        return ""
    for aba in ["Pacientes", "Alunos"]:
        try:
            ws = get_sheet(aba)
            for r in ws.get_all_records():
                if nome.lower() in str(r.get("Nome", "")).lower():
                    return f"Dados de {r.get('Nome')} ({aba[:-1]}): " + " | ".join(
                        f"{k}: {v}" for k, v in r.items() if v
                    )
        except Exception:
            pass
    return ""

# ── Menus ──────────────────────────────────────────────────
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌍 Radar Global", callback_data="menu_radar"), InlineKeyboardButton("🕵️ Portal OSINT", callback_data="menu_osint")],
        [InlineKeyboardButton("🧠 IA Assistente", callback_data="menu_ia"), InlineKeyboardButton("🎵 Áudio IA", callback_data="menu_audio")],
        [InlineKeyboardButton("🔗 Links", callback_data="menu_links"), InlineKeyboardButton("📊 Painel", callback_data="menu_painel")],
        [InlineKeyboardButton("📚 Gestão", callback_data="menu_gestao"), InlineKeyboardButton("🛡️ Admin", callback_data="menu_admin")],
        [InlineKeyboardButton("❓ Ajuda", callback_data="menu_ajuda")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat:
        chat_ids.add(update.effective_chat.id)
    texto = (
        "🤖 <b>Hoppy Intelligence Core v1</b>\n\n"
        "Central modular para uso diário:\n"
        "🌍 radar/tradução • 🧠 IA • 🎵 áudio • 🔗 links • 🕵️ OSINT seguro • 📊 gestão\n\n"
        "Escolha uma área abaixo ou use /ajuda para ver todos os comandos."
    )
    await safe_reply(update, texto, reply_markup=main_menu())


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    menus = {
        "menu_radar": (
            "🌍 <b>Radar Global</b>\n\n"
            "O tradutor roda em paralelo via Telethon. Use no supergrupo destino:\n"
            "• /status\n• /relatorio\n• /ultimos\n• /ajuda\n\n"
            "Próxima etapa: clusterização, score e resumos IA."
        ),
        "menu_osint": (
            "🕵️ <b>Portal OSINT Seguro</b>\n\n"
            "Base da integração das 20 ferramentas em camadas:\n"
            "• Ahmia / Onion Discovery legal\n"
            "• Shodan defensivo\n"
            "• SpiderFoot como motor OSINT\n"
            "• Grafos estilo Maltego\n"
            "• Curadoria, reputação e risco\n\n"
            "Comandos:\n/osint\n/osint_status\n/buscar_grupos tema"
        ),
        "menu_ia": "🧠 <b>IA Assistente</b>\n\nUse:\n• /ia sua pergunta\n• /ia_paciente Nome - pergunta",
        "menu_audio": "🎵 <b>Áudio IA</b>\n\nUse /separar para iniciar o fluxo de separação de áudio.",
        "menu_links": "🔗 <b>Inteligência de Links</b>\n\nEnvie um link do YouTube ou Instagram e eu faço a análise inicial.",
        "menu_painel": "📊 <b>Painel</b>\n\nUse /painel ou /resumo para ver estado geral.",
        "menu_gestao": (
            "📚 <b>Gestão</b>\n\n"
            "/aluno • /paciente • /agenda • /tarefa • /concluir • /obs • /presenca • /financeiro • /listar"
        ),
        "menu_admin": "🛡️ <b>Admin</b>\n\nUse /admin para status técnico e checklist de segurança.",
        "menu_ajuda": await_text_help(),
    }
    await query.edit_message_text(menus.get(data, "Menu não encontrado."), parse_mode="HTML", reply_markup=main_menu())


def await_text_help():
    return (
        "❓ <b>Comandos do Hoppy</b>\n\n"
        "<b>Interface</b>\n/start — menu principal\n/ajuda — comandos\n/painel — painel geral\n/admin — status técnico\n\n"
        "<b>IA</b>\n/ia pergunta\n/ia_paciente Nome - pergunta\n\n"
        "<b>Gestão</b>\n/aluno • /paciente • /agenda • /tarefa • /concluir • /obs • /presenca • /financeiro • /relatorio • /resumo • /listar • /backup\n\n"
        "<b>Mídia</b>\n/separar — separação de áudio\nEnvie links para análise automática.\n\n"
        "<b>OSINT seguro</b>\n/osint\n/osint_status\n/buscar_grupos tema"
    )


async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_reply(update, await_text_help(), reply_markup=main_menu())


async def painel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    linhas = ["📊 <b>Painel Hoppy Intelligence Core</b>\n"]
    linhas.append(f"🟢 Bot principal: online")
    linhas.append(f"🧠 IA: {'configurada' if ANTHROPIC_KEY else 'não configurada'}")
    linhas.append(f"📄 Google Sheets: {'configurado' if has_google_config() else 'não configurado'}")
    linhas.append(f"📧 Backup email: {'configurado' if all([GMAIL_USER, GMAIL_PASS, GMAIL_DEST]) else 'não configurado'}")
    linhas.append(f"👤 Admin IDs: {'configurados' if ADMIN_IDS else 'modo pessoal/liberado'}")
    linhas.append("\n🌍 Tradutor: roda em thread separada pelo run_all.py")
    linhas.append("🕵️ Portal OSINT: v1 curadoria/roadmap seguro")
    await safe_reply(update, "\n".join(linhas), reply_markup=main_menu())


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await safe_reply(update, "⛔ Acesso admin negado.")
        return
    texto = (
        "🛡️ <b>Admin / Segurança</b>\n\n"
        "Checklist recomendado:\n"
        "• Remover credentials.json do GitHub\n"
        "• Usar GOOGLE_CREDENTIALS_JSON apenas no Railway\n"
        "• Manter TELEGRAM_TOKEN fora do código\n"
        "• Manter TRADUTOR_SESSION_STRING fora do código\n"
        "• Rodar apenas 1 deploy ativo\n"
        "• Configurar HOPPY_ADMIN_IDS para restringir comandos sensíveis\n\n"
        "Use /painel para status geral."
    )
    await safe_reply(update, texto)

# ── Portal OSINT seguro ────────────────────────────────────
async def osint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "🕵️ <b>Portal OSINT Seguro — V1</b>\n\n"
        "Objetivo: integrar as 20 ferramentas como sensores de inteligência, com curadoria e filtros de risco.\n\n"
        "<b>Camada V1:</b>\n"
        "1. Ahmia / Onion Discovery legal\n"
        "2. Shodan defensivo\n"
        "3. SpiderFoot como motor OSINT\n"
        "4. Grafos estilo Maltego\n"
        "5. Busca de grupos/canais públicos do Telegram\n"
        "6. Classificação: tema, idioma, risco, reputação\n\n"
        "Este módulo não automatiza invasão, coleta ilegal, compra/venda ilícita ou acesso a grupos privados."
    )
    await safe_reply(update, texto)


async def osint_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "🕵️ <b>Status OSINT</b>\n\n"
        "Ahmia: planejado\n"
        "Tor/Stem: planejado\n"
        "txtorcon: planejado\n"
        "SpiderFoot: planejado\n"
        "Shodan: planejado\n"
        "Grafo local: planejado\n\n"
        "V1 atual: portal, curadoria, menu e comandos seguros."
    )
    await safe_reply(update, texto)


async def buscar_grupos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    termo = " ".join(context.args).strip()
    if not termo:
        await safe_reply(update, "🔎 Uso: /buscar_grupos tema\nEx: /buscar_grupos musicoterapia")
        return
    texto = (
        f"🔎 <b>Busca de grupos públicos</b>\n\nTema: <b>{esc(termo)}</b>\n\n"
        "V1 segura: vou transformar isso em um módulo que encontra e organiza canais/grupos públicos por tema, "
        "com favoritos, reputação, idioma e relatório.\n\n"
        "Próxima implementação: conectores públicos + curadoria manual + banco de favoritos."
    )
    await safe_reply(update, texto)

# ── Gestão / Sheets ────────────────────────────────────────
async def aluno(update, context):
    try:
        texto = " ".join(context.args)
        if not texto:
            await safe_reply(update, "📚 Uso: /aluno Nome - Localidade - Dia - Horário - Nascimento")
            return
        partes = [p.strip() for p in texto.split("-")]
        if len(partes) < 4:
            await safe_reply(update, "⚠️ Use: /aluno Nome - Localidade - Dia - Horário")
            return
        nome, local, dia, hora = partes[0], partes[1], partes[2], partes[3]
        nasc = partes[4] if len(partes) > 4 else ""
        ws = get_sheet("Alunos")
        garantir_cabecalhos(ws, ["Data Cadastro", "Nome", "Localidade", "Dia", "Horário", "Nascimento", "Observações"])
        ws.append_row([datetime.now().strftime("%d/%m/%Y"), nome, local, dia, hora, nasc, ""])
        await safe_reply(update, f"✅ <b>Aluno registrado!</b>\n👤 {esc(nome)}\n📍 {esc(local)}\n📅 {esc(dia)} às {esc(hora)}")
    except Exception as e:
        await safe_reply(update, f"⚠️ Erro ao registrar aluno: {esc(e)}")


async def paciente(update, context):
    try:
        texto = " ".join(context.args)
        if not texto:
            await safe_reply(update, "🎵 Uso: /paciente Nome - Diagnóstico - Dia - Horário - Nascimento")
            return
        partes = [p.strip() for p in texto.split("-")]
        if len(partes) < 4:
            await safe_reply(update, "⚠️ Use: /paciente Nome - Diagnóstico - Dia - Horário")
            return
        nome, diag, dia, hora = partes[0], partes[1], partes[2], partes[3]
        nasc = partes[4] if len(partes) > 4 else ""
        ws = get_sheet("Pacientes")
        garantir_cabecalhos(ws, ["Data Cadastro", "Nome", "Diagnóstico", "Dia", "Horário", "Nascimento", "Observações"])
        ws.append_row([datetime.now().strftime("%d/%m/%Y"), nome, diag, dia, hora, nasc, ""])
        await safe_reply(update, f"✅ <b>Paciente registrado!</b>\n👤 {esc(nome)}\n🏥 {esc(diag)}\n📅 {esc(dia)} às {esc(hora)}")
    except Exception as e:
        await safe_reply(update, f"⚠️ Erro ao registrar paciente: {esc(e)}")


async def agenda(update, context):
    try:
        texto = " ".join(context.args)
        if not texto:
            await safe_reply(update, "📅 Uso: /agenda Descrição - DD/MM/AAAA - HH:MM")
            return
        partes = [p.strip() for p in texto.split("-")]
        if len(partes) < 3:
            await safe_reply(update, "⚠️ Use: /agenda Descrição - DD/MM/AAAA - HH:MM")
            return
        ws = get_sheet("Agenda")
        garantir_cabecalhos(ws, ["Registrado em", "Descrição", "Data", "Horário", "Status"])
        ws.append_row([datetime.now().strftime("%d/%m/%Y %H:%M"), partes[0], partes[1], partes[2], "Pendente"])
        await safe_reply(update, f"✅ <b>Agendado!</b>\n📌 {esc(partes[0])}\n📅 {esc(partes[1])} às {esc(partes[2])}")
    except Exception as e:
        await safe_reply(update, f"⚠️ Erro na agenda: {esc(e)}")


async def tarefa(update, context):
    try:
        texto = " ".join(context.args).strip()
        if not texto:
            await safe_reply(update, "✅ Uso: /tarefa Descrição")
            return
        ws = get_sheet("Tarefas")
        garantir_cabecalhos(ws, ["Data", "Tarefa", "Status"])
        ws.append_row([datetime.now().strftime("%d/%m/%Y"), texto, "Pendente"])
        await safe_reply(update, f"✅ <b>Tarefa adicionada!</b>\n📝 {esc(texto)}")
    except Exception as e:
        await safe_reply(update, f"⚠️ Erro na tarefa: {esc(e)}")


async def concluir(update, context):
    try:
        texto = " ".join(context.args).strip()
        if not texto:
            await safe_reply(update, "✔️ Uso: /concluir Parte do nome da tarefa")
            return
        ws = get_sheet("Tarefas")
        for i, r in enumerate(ws.get_all_records(), start=2):
            if texto.lower() in str(r.get("Tarefa", "")).lower() and r.get("Status") == "Pendente":
                ws.update_cell(i, 3, "Concluída")
                await safe_reply(update, f"✔️ <b>Concluída!</b>\n📝 {esc(r.get('Tarefa'))}")
                return
        await safe_reply(update, "⚠️ Tarefa pendente não encontrada.")
    except Exception as e:
        await safe_reply(update, f"⚠️ Erro ao concluir: {esc(e)}")


async def obs(update, context):
    try:
        texto = " ".join(context.args)
        if not texto or "-" not in texto:
            await safe_reply(update, "📝 Uso: /obs Nome - Observação")
            return
        nome, observacao = [p.strip() for p in texto.split("-", 1)]
        atualizado = False
        for aba in ["Alunos", "Pacientes"]:
            ws = get_sheet(aba)
            for i, r in enumerate(ws.get_all_records(), start=2):
                if nome.lower() in str(r.get("Nome", "")).lower():
                    obs_atual = str(r.get("Observações", ""))
                    nova = f"{datetime.now().strftime('%d/%m/%Y')}: {observacao}"
                    ws.update_cell(i, 7, (obs_atual + " | " + nova).strip(" | "))
                    await safe_reply(update, f"📝 <b>Observação salva!</b>\n👤 {esc(r.get('Nome'))}\n💬 {esc(observacao)}")
                    atualizado = True
                    break
            if atualizado:
                break
        if not atualizado:
            ws = get_sheet("Observações")
            garantir_cabecalhos(ws, ["Data", "Nome", "Observação"])
            ws.append_row([datetime.now().strftime("%d/%m/%Y"), nome, observacao])
            await safe_reply(update, f"📝 <b>Observação salva!</b>\n👤 {esc(nome)}")
    except Exception as e:
        await safe_reply(update, f"⚠️ Erro em observação: {esc(e)}")


async def presenca(update, context):
    try:
        texto = " ".join(context.args)
        if not texto or "-" not in texto:
            await safe_reply(update, "👤 Uso: /presenca Nome - presente/falta")
            return
        nome, status = [p.strip() for p in texto.split("-", 1)]
        ws = get_sheet("Presença")
        garantir_cabecalhos(ws, ["Data", "Nome", "Status", "Observação"])
        ws.append_row([datetime.now().strftime("%d/%m/%Y"), nome, status.capitalize(), ""])
        emoji = "✅" if "presente" in status.lower() else "❌"
        await safe_reply(update, f"{emoji} <b>Presença registrada!</b>\n👤 {esc(nome)} — {esc(status.capitalize())}")
    except Exception as e:
        await safe_reply(update, f"⚠️ Erro em presença: {esc(e)}")


async def financeiro(update, context):
    try:
        texto = " ".join(context.args)
        if not texto:
            await safe_reply(update, "💰 Uso: /financeiro entrada/saida - Descrição - Valor")
            return
        partes = [p.strip() for p in texto.split("-")]
        if len(partes) < 3:
            await safe_reply(update, "⚠️ Use: /financeiro entrada/saida - Descrição - Valor")
            return
        ws = get_sheet("Financeiro")
        garantir_cabecalhos(ws, ["Data", "Mês", "Tipo", "Descrição", "Valor (R$)"])
        ws.append_row([datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%m/%Y"), partes[0].capitalize(), parts_desc := partes[1], partes[2]])
        await safe_reply(update, f"💰 <b>Registrado!</b>\n{esc(partes[0].capitalize())} | {esc(parts_desc)} | R$ {esc(partes[2])}")
    except Exception as e:
        await safe_reply(update, f"⚠️ Erro financeiro: {esc(e)}")


MESES = {"janeiro": "01", "fevereiro": "02", "março": "03", "abril": "04", "maio": "05", "junho": "06", "julho": "07", "agosto": "08", "setembro": "09", "outubro": "10", "novembro": "11", "dezembro": "12"}


async def relatorio(update, context):
    try:
        texto = " ".join(context.args).strip().lower()
        ano = datetime.now().strftime("%Y")
        mes_num = datetime.now().strftime("%m") if not texto else MESES.get(texto, texto.split("/")[0].zfill(2))
        if "/" in texto:
            p = texto.split("/")
            ano = p[1] if len(p) > 1 else ano
        filtro = f"{mes_num}/{ano}"
        ws = get_sheet("Financeiro")
        registros = [r for r in ws.get_all_records() if str(r.get("Mês", "")).strip() == filtro]
        if not registros:
            await safe_reply(update, f"📊 Nenhum registro em {esc(filtro)}.")
            return
        ent = sum(float(str(r.get("Valor (R$)", 0)).replace(",", ".")) for r in registros if "entrada" in str(r.get("Tipo", "")).lower())
        sai = sum(float(str(r.get("Valor (R$)", 0)).replace(",", ".")) for r in registros if "saida" in str(r.get("Tipo", "")).lower())
        await safe_reply(update, f"💵 <b>Relatório {esc(filtro)}</b>\n\n📈 Entradas: R$ {ent:.2f}\n📉 Saídas: R$ {sai:.2f}\n📊 Saldo: R$ {(ent-sai):.2f}")
    except Exception as e:
        await safe_reply(update, f"⚠️ Erro no relatório: {esc(e)}")


async def resumo(update, context):
    await painel(update, context)


async def listar(update, context):
    try:
        args = context.args
        if not args:
            await safe_reply(update, "📋 Uso: /listar alunos|pacientes|agenda|tarefas|financeiro|presenca [filtro]")
            return
        area = args[0].lower()
        filtro = " ".join(args[1:]).lower()
        mapa = {"alunos": "Alunos", "pacientes": "Pacientes", "agenda": "Agenda", "tarefas": "Tarefas", "financeiro": "Financeiro", "presenca": "Presença"}
        if area not in mapa:
            await safe_reply(update, "⚠️ Áreas: alunos, pacientes, agenda, tarefas, financeiro, presenca")
            return
        ws = get_sheet(mapa[area])
        registros = ws.get_all_records()
        if filtro:
            registros = [r for r in registros if any(filtro in str(v).lower() for v in r.values())]
        if not registros:
            await safe_reply(update, f"📋 Nenhum registro em <b>{esc(mapa[area])}</b>.")
            return
        texto = f"📋 <b>{esc(mapa[area])}</b> ({len(registros[-10:])} últimos):\n\n"
        for r in registros[-10:]:
            vals = " | ".join(esc(v) for v in list(r.values())[:4] if v)
            texto += f"• {vals}\n"
        await safe_reply(update, texto[:4000])
    except Exception as e:
        await safe_reply(update, f"⚠️ Erro ao listar: {esc(e)}")


async def ia(update, context):
    texto = " ".join(context.args).strip()
    if not texto:
        await safe_reply(update, "🤖 Uso: /ia sua pergunta")
        return
    msg = await safe_reply(update, "🤖 Consultando a IA...")
    try:
        resposta = await asyncio.to_thread(perguntar_claude, texto)
        await msg.edit_text(f"🤖 <b>Hoppy IA:</b>\n\n{esc(resposta)}", parse_mode="HTML")
    except Exception as e:
        await msg.edit_text(f"⚠️ Erro na IA: {esc(e)}", parse_mode="HTML")


async def ia_paciente(update, context):
    texto = " ".join(context.args).strip()
    if not texto or "-" not in texto:
        await safe_reply(update, "🧠 Uso: /ia_paciente Nome - Pergunta")
        return
    nome, pergunta = [p.strip() for p in texto.split("-", 1)]
    msg = await safe_reply(update, f"🧠 Buscando contexto de <b>{esc(nome)}</b> e consultando a IA...")
    try:
        contexto = await asyncio.to_thread(buscar_contexto_paciente, nome)
        resposta = await asyncio.to_thread(perguntar_claude, pergunta, contexto)
        await msg.edit_text(f"🧠 <b>Hoppy IA — {esc(nome)}:</b>\n\n{esc(resposta)}", parse_mode="HTML")
    except Exception as e:
        await msg.edit_text(f"⚠️ Erro na IA: {esc(e)}", parse_mode="HTML")


async def backup(update, context):
    await safe_reply(update, "📧 Gerando backup...")
    try:
        hoje = datetime.now().strftime("%d/%m/%Y")
        corpo = f"Backup do Hoppy Assistant — {hoje}\n\n"
        for aba in ["Alunos", "Pacientes", "Agenda", "Tarefas", "Financeiro", "Presença"]:
            try:
                ws = get_sheet(aba)
                registros = ws.get_all_records()
                corpo += f"\n=== {aba} ({len(registros)} registros) ===\n"
                for r in registros[-20:]:
                    corpo += " | ".join(str(v) for v in r.values() if v) + "\n"
            except Exception:
                pass
        ok = await asyncio.to_thread(enviar_email, f"Backup Hoppy Bot — {hoje}", corpo)
        await safe_reply(update, f"{'✅ Backup enviado!' if ok else '⚠️ Erro ao enviar email. Verifique as configurações.'}")
    except Exception as e:
        await safe_reply(update, f"⚠️ Erro: {esc(e)}")

# ── Links ──────────────────────────────────────────────────
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return
    text = message.text.strip()
    if "http" not in text:
        return
    processing_msg = await message.reply_text("🔍 Analisando o link...")
    try:
        analysis = await analyze_link(text)
        await processing_msg.edit_text(analysis, parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        logger.exception("Erro ao analisar link")
        await processing_msg.edit_text(f"❌ Erro ao analisar o link: {esc(e)}", parse_mode="HTML")

# ── Jobs leves ─────────────────────────────────────────────
async def verificar_lembretes(context):
    if not chat_ids or not has_google_config():
        return
    try:
        ws = get_sheet("Agenda")
        agora = datetime.now()
        for r in ws.get_all_records():
            if r.get("Status") != "Pendente":
                continue
            try:
                hora_str = str(r.get("Horário", "")).strip().replace("h", ":00")
                if ":" not in hora_str:
                    hora_str = hora_str.zfill(2) + ":00"
                dt = datetime.strptime(f"{r.get('Data')} {hora_str}", "%d/%m/%Y %H:%M")
                diff = (dt - agora).total_seconds()
                if 1740 <= diff <= 1860:
                    for cid in chat_ids:
                        await context.bot.send_message(chat_id=cid, text=f"🔔 Lembrete em 30 min!\n📌 {r.get('Descrição')}\n⏰ {r.get('Horário')}")
            except Exception:
                continue
    except Exception as e:
        logger.error("Erro lembrete: %s", e)


async def post_init(app: Application):
    await app.bot.set_my_commands([
        BotCommand("start", "Abrir menu principal"),
        BotCommand("ajuda", "Ver comandos"),
        BotCommand("painel", "Status geral"),
        BotCommand("ia", "Perguntar à IA"),
        BotCommand("ia_paciente", "IA com contexto de aluno/paciente"),
        BotCommand("separar", "Separar áudio"),
        BotCommand("osint", "Portal OSINT seguro"),
        BotCommand("buscar_grupos", "Buscar grupos públicos por tema"),
        BotCommand("admin", "Painel admin"),
    ])


def main():
    if not TOKEN:
        raise RuntimeError("TELEGRAM_TOKEN não configurado no Railway.")

    app = Application.builder().token(TOKEN).post_init(post_init).build()

    commands = [
        ("start", start), ("ajuda", ajuda), ("painel", painel), ("admin", admin),
        ("osint", osint), ("osint_status", osint_status), ("buscar_grupos", buscar_grupos),
        ("aluno", aluno), ("paciente", paciente), ("agenda", agenda), ("tarefa", tarefa),
        ("concluir", concluir), ("obs", obs), ("presenca", presenca), ("financeiro", financeiro),
        ("relatorio", relatorio), ("resumo", resumo), ("listar", listar),
        ("ia", ia), ("ia_paciente", ia_paciente), ("backup", backup),
    ]
    for name, fn in commands:
        app.add_handler(CommandHandler(name, fn))

    app.add_handler(get_separation_handler())
    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^menu_"))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"https?://") & ~filters.COMMAND, handle_link))

    if app.job_queue:
        app.job_queue.run_repeating(verificar_lembretes, interval=60, first=15)

    logger.info("🤖 Hoppy Intelligence Core v1 iniciado")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
