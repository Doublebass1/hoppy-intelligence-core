from dotenv import load_dotenv
load_dotenv()
"""tradutor.py — Radar Global / Tradutor multi-grupo do Hoppy Intelligence Core v1."""
import asyncio
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path

from deep_translator import GoogleTranslator
from langdetect import detect
from telethon import TelegramClient, events
from telethon.errors import AuthKeyDuplicatedError
from telethon.sessions import StringSession

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("tradutor")

API_ID = int(os.environ.get("TRADUTOR_API_ID", "0") or 0)
API_HASH = os.environ.get("TRADUTOR_API_HASH", "")
SESSION_STRING = os.environ.get("TRADUTOR_SESSION_STRING", "")
SUPERGRUPO_ID = int(os.environ.get("TRADUTOR_SUPERGRUPO_ID", "0") or 0)
TARGET_LANG = os.environ.get("TRADUTOR_TARGET_LANG", "pt")

if not API_ID:
    raise RuntimeError("TRADUTOR_API_ID não configurado.")
if not API_HASH:
    raise RuntimeError("TRADUTOR_API_HASH não configurado.")
if not SESSION_STRING:
    raise RuntimeError("TRADUTOR_SESSION_STRING não configurado.")
if not SUPERGRUPO_ID:
    raise RuntimeError("TRADUTOR_SUPERGRUPO_ID não configurado.")

GRUPOS_MONITORADOS = {
    -1001289614360: {"nome": "Israel Notícias", "idioma": "Hebraico", "emoji": "🇮🇱"},
    -1001080641057: {"nome": "RT en Español", "idioma": "Espanhol", "emoji": "📺"},
    -1001009749057: {"nome": "HispanTV", "idioma": "Espanhol", "emoji": "📡"},
    -1001140394567: {"nome": "Iran International", "idioma": "Persa/Inglês", "emoji": "🇮🇷"},
    -1001318165547: {"nome": "Gaza Now", "idioma": "Árabe", "emoji": "🇵🇸"},
    -1001318986211: {"nome": "C14 News", "idioma": "Hebraico", "emoji": "📰"},
    -1001143765178: {"nome": "Abu Ali Express", "idioma": "Hebraico", "emoji": "🔔"},
    -1001004171705: {"nome": "Brigadas Al-Qassam", "idioma": "Árabe", "emoji": "⚔️"},
    -1001406113886: {"nome": "Yediot 100 Campo", "idioma": "Hebraico", "emoji": "📡"},
    -1002335255539: {"nome": "Israel Notícias Telegram", "idioma": "Hebraico", "emoji": "🇮🇱"},
    -1001336945221: {"nome": "Iraq News", "idioma": "Árabe", "emoji": "🇮🇶"},
    -1001419583991: {"nome": "Irã Notícias Urgentes", "idioma": "Persa", "emoji": "🚨"},
    -1001172517043: {"nome": "Palestina Hoy", "idioma": "Espanhol", "emoji": "🇵🇸"},
    -1001371192462: {"nome": "Canal Atraheeb", "idioma": "Árabe", "emoji": "📢"},
    -1001491586970: {"nome": "Voz Árabe Online", "idioma": "Hebraico/Árabe", "emoji": "🎙️"},
    -1001737806035: {"nome": "The Chaser News", "idioma": "Chinês", "emoji": "🇨🇳"},
    -1002104533295: {"nome": "Canal Russo", "idioma": "Russo", "emoji": "🇷🇺"},
    -1001366600647: {"nome": "Kosinuse", "idioma": "Persa", "emoji": "🇮🇷"},
    -1001400513817: {"nome": "Promos CS GO (Russo)", "idioma": "Russo", "emoji": "🇷🇺"},
}

# Permite substituir/adicionar grupos via variável JSON opcional.
# Formato: {"-100123": {"nome":"Canal","idioma":"Espanhol","emoji":"📡"}}
try:
    extra = json.loads(os.environ.get("TRADUTOR_GRUPOS_JSON", "{}") or "{}")
    for gid, info in extra.items():
        GRUPOS_MONITORADOS[int(gid)] = info
except Exception as e:
    logger.warning("TRADUTOR_GRUPOS_JSON inválido: %s", e)

LOG_FILE = "telegram_tradutor.log"
STATE_FILE = "mensagens_processadas.json"
STATS_FILE = "estatisticas_dia.json"
AUDITORIA_FILE = "auditoria.json"
ULTIMOS_FILE = "ultimos_registros.json"
MAX_IDS = 3000
MAX_AUDITORIA = 150
MAX_ULTIMOS = 250
BUFFER_SECONDS = int(os.environ.get("TRADUTOR_BUFFER_SECONDS", "15") or 15)
MEDIA_DIR = Path("media_temp")
MEDIA_DIR.mkdir(exist_ok=True)

translator = GoogleTranslator(source="auto", target=TARGET_LANG)
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH, auto_reconnect=True, connection_retries=10)

PALAVRAS_URGENCIA = {
    "alta": ["ataque", "explosão", "explosao", "míssil", "missil", "foguete", "feridos", "mortos", "sirene", "terror", "bombardeio", "invasão", "reféns", "massacre", "guerra", "alerta vermelho"],
    "media": ["exército", "exercito", "militar", "operação", "operacao", "defesa", "fronteira", "drone", "protesto", "tensão", "tensao", "sanções"],
}
TEMAS = {
    "Conflito": ["ataque", "míssil", "foguete", "guerra", "bombardeio", "sirene", "drone", "terror"],
    "Política": ["governo", "ministro", "parlamento", "knesset", "eleição", "presidente", "premiê"],
    "Diplomacia": ["onu", "eua", "washington", "embaixada", "acordo", "cessar-fogo", "trégua"],
    "Segurança": ["polícia", "prisão", "ameaça", "alerta", "interceptado"],
    "Mídia": ["vídeo", "video", "imagem", "foto", "filmagem"],
}
TOPICOS_POR_IDIOMA = {"Hebraico": 60, "Hebraico/Árabe": 60, "Árabe": 63, "Persa": 65, "Persa/Inglês": 65, "Espanhol": 66, "Chinês": 67, "Russo": 67}
TOPICO_GERAL = 1


def carregar_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, type(default)) else default
    except Exception:
        return default


def salvar_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("Erro ao salvar %s: %s", path, e)


def hoje_str():
    return datetime.now().strftime("%Y-%m-%d")


def novo_stats():
    return {"data": hoje_str(), "total": 0, "por_grupo": {}, "temas": {}, "urgencias": {}, "resumos": []}

mensagens_processadas = carregar_json(STATE_FILE, [])
auditoria_eventos = carregar_json(AUDITORIA_FILE, [])
ultimos_registros = carregar_json(ULTIMOS_FILE, [])
stats_dia = carregar_json(STATS_FILE, novo_stats())
if stats_dia.get("data") != hoje_str():
    stats_dia = novo_stats()

buffers_por_grupo = {gid: [] for gid in GRUPOS_MONITORADOS}
tasks_buffer = {}


def auditar(tipo, detalhe):
    global auditoria_eventos
    auditoria_eventos.append({"horario": datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "tipo": tipo, "detalhe": detalhe})
    auditoria_eventos = auditoria_eventos[-MAX_AUDITORIA:]
    salvar_json(AUDITORIA_FILE, auditoria_eventos)


def registrar_ultimo(item):
    global ultimos_registros
    ultimos_registros.append(item)
    ultimos_registros = ultimos_registros[-MAX_ULTIMOS:]
    salvar_json(ULTIMOS_FILE, ultimos_registros)


def deve_traduzir(texto):
    if not texto or len(texto.strip()) < 3:
        return False
    try:
        return detect(texto).lower() not in ("pt", "pt-br", "pt_br")
    except Exception:
        return True


def ja_processou(chat_id, msg_id):
    return f"{chat_id}:{msg_id}" in mensagens_processadas


def marcar_processada(chat_id, msg_id):
    global mensagens_processadas
    mensagens_processadas.append(f"{chat_id}:{msg_id}")
    mensagens_processadas = mensagens_processadas[-MAX_IDS:]
    salvar_json(STATE_FILE, mensagens_processadas)


def nome_autor(sender):
    if not sender:
        return "Desconhecido"
    nome = " ".join(p for p in [getattr(sender, "first_name", None), getattr(sender, "last_name", None)] if p).strip()
    return nome or (f"@{getattr(sender, 'username', '')}" if getattr(sender, "username", None) else "Desconhecido")


def nome_tipo_midia(msg):
    if not msg.media:
        return None
    if getattr(msg, "photo", None): return "📷 Foto"
    if getattr(msg, "video", None): return "🎥 Vídeo"
    if getattr(msg, "voice", None): return "🎤 Áudio"
    if getattr(msg, "document", None): return "📄 Documento"
    if getattr(msg, "sticker", None): return "🎭 Sticker"
    return "📎 Mídia"


def link_mensagem(chat_id, msg_id):
    s = str(chat_id)
    return f"https://t.me/c/{s[4:]}/{msg_id}" if s.startswith("-100") else None


def classificar_urgencia(texto):
    t = (texto or "").lower()
    if any(p in t for p in PALAVRAS_URGENCIA["alta"]): return "alta"
    if any(p in t for p in PALAVRAS_URGENCIA["media"]): return "media"
    return "baixa"


def emoji_urgencia(nivel):
    return {"alta": "🚨", "media": "⚠️", "baixa": "🔵"}.get(nivel, "🔵")


def classificar_tema(texto, midia_tipo=None):
    t = (texto or "").lower()
    scores = {tema: sum(1 for p in pals if p in t) for tema, pals in TEMAS.items()}
    scores = {k: v for k, v in scores.items() if v}
    return max(scores, key=scores.get) if scores else ("Mídia" if midia_tipo else "Geral")


def resumo_1_linha(texto, tema=None):
    texto = (texto or "").strip().replace("\n", " ")
    if not texto:
        return f"Atualização de {tema}." if tema else "Atualização recebida."
    primeira = re.split(r"(?<=[.!?])\s+", texto)[0][:180]
    return primeira + ("..." if len(primeira) >= 180 else "")


def atualizar_estatisticas(grupo_id, tema, urgencia, resumo):
    global stats_dia
    if stats_dia.get("data") != hoje_str():
        stats_dia = novo_stats()
    stats_dia["total"] = stats_dia.get("total", 0) + 1
    nome_grupo = GRUPOS_MONITORADOS.get(grupo_id, {}).get("nome", str(grupo_id))
    stats_dia.setdefault("por_grupo", {})[nome_grupo] = stats_dia.setdefault("por_grupo", {}).get(nome_grupo, 0) + 1
    stats_dia.setdefault("temas", {})[tema] = stats_dia.setdefault("temas", {}).get(tema, 0) + 1
    stats_dia.setdefault("urgencias", {})[urgencia] = stats_dia.setdefault("urgencias", {}).get(urgencia, 0) + 1
    stats_dia.setdefault("resumos", []).append({"horario": datetime.now().strftime("%H:%M"), "grupo": nome_grupo, "tema": tema, "urgencia": urgencia, "texto": resumo})
    stats_dia["resumos"] = stats_dia["resumos"][-150:]
    salvar_json(STATS_FILE, stats_dia)


def obter_topico_por_idioma(grupo_id):
    idioma = GRUPOS_MONITORADOS.get(grupo_id, {}).get("idioma", "")
    return TOPICOS_POR_IDIOMA.get(idioma, TOPICO_GERAL)

async def enviar_para_topico(grupo_id, texto, arquivo=None, caption=None):
    thread_id = obter_topico_por_idioma(grupo_id)
    try:
        if arquivo and Path(arquivo).exists():
            await client.send_file(SUPERGRUPO_ID, str(arquivo), caption=(caption or "")[:1024], reply_to=thread_id)
        else:
            for parte in [texto[i:i+4000] for i in range(0, len(texto), 4000)]:
                if parte.strip():
                    await client.send_message(SUPERGRUPO_ID, parte, reply_to=thread_id, parse_mode="markdown")
    except Exception as e:
        logger.error("Erro ao enviar tópico %s: %s", thread_id, e)
        auditar("erro_envio_topico", str(e))

async def enviar_buffer_grupo(grupo_id):
    await asyncio.sleep(BUFFER_SECONDS)
    itens = buffers_por_grupo.get(grupo_id, [])
    if not itens:
        tasks_buffer.pop(grupo_id, None)
        return
    info = GRUPOS_MONITORADOS.get(grupo_id, {})
    cabecalho = f"{info.get('emoji','📢')} *{info.get('nome', grupo_id)}* | {info.get('idioma','?')}\n🕒 {datetime.now().strftime('%d/%m/%Y %H:%M')} | 📦 {len(itens)} mensagem(ns)\n{'─'*30}\n\n"
    await enviar_para_topico(grupo_id, cabecalho + "\n\n─────────────\n\n".join(item["texto"] for item in itens if item.get("texto")))
    for item in itens:
        if item.get("arquivo"):
            try:
                await enviar_para_topico(grupo_id, "", arquivo=item["arquivo"], caption=item.get("caption", ""))
            finally:
                try:
                    Path(item["arquivo"]).unlink(missing_ok=True)
                except Exception:
                    pass
    auditar("buffer_enviado", f"grupo={info.get('nome')} itens={len(itens)}")
    buffers_por_grupo[grupo_id] = []
    tasks_buffer.pop(grupo_id, None)

@client.on(events.NewMessage(chats=list(GRUPOS_MONITORADOS.keys())))
async def handler(event):
    try:
        chat_id, msg_id, msg = event.chat_id, event.message.id, event.message
        texto, midia = msg.message or "", nome_tipo_midia(msg)
        if ja_processou(chat_id, msg_id):
            return
        sender = await event.get_sender()
        autor = nome_autor(sender)
        horario = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        traducao = ""
        if texto.strip() and deve_traduzir(texto.strip()):
            try:
                traducao = await asyncio.to_thread(translator.translate, texto.strip())
            except Exception as e:
                logger.warning("Erro tradução: %s", e)
        base = traducao or texto
        urgencia = classificar_urgencia(base)
        tema = classificar_tema(base, midia)
        resumo = resumo_1_linha(base, tema)
        info = GRUPOS_MONITORADOS.get(chat_id, {})
        atualizar_estatisticas(chat_id, tema, urgencia, resumo)
        registrar_ultimo({"horario": horario, "grupo": info.get("nome", str(chat_id)), "urgencia": urgencia, "tema": tema, "resumo": resumo, "traducao": traducao, "timestamp": datetime.now().isoformat()})
        bloco = f"{emoji_urgencia(urgencia)} *{urgencia.upper()}*\n📌 Tema: {tema}\n💬 Resumo: {resumo}\n\n👤 Autor: {autor}\n🕒 {horario}\n🆔 msg#{msg_id}\n"
        if midia: bloco += f"📎 {midia}\n"
        link = link_mensagem(chat_id, msg_id)
        if link: bloco += f"🔗 [Ver original]({link})\n"
        if texto.strip():
            bloco += f"\n📝 *Original:*\n{texto.strip()[:1200]}\n"
            if traducao: bloco += f"\n🇧🇷 *Tradução:*\n{traducao[:1200]}"
        arquivo = None
        if midia:
            try:
                path = await client.download_media(msg, file=str(MEDIA_DIR / f"{chat_id}_{msg_id}"))
                arquivo = str(path) if path else None
            except Exception:
                pass
        buffers_por_grupo.setdefault(chat_id, []).append({"texto": bloco, "arquivo": arquivo, "caption": f"{emoji_urgencia(urgencia)} {urgencia.upper()} | {tema}\n{resumo}"})
        marcar_processada(chat_id, msg_id)
        auditar("processada", f"grupo={info.get('nome')} msg={msg_id} urg={urgencia}")
        task = tasks_buffer.get(chat_id)
        if task and not task.done():
            task.cancel()
        tasks_buffer[chat_id] = asyncio.create_task(enviar_buffer_grupo(chat_id))
        if urgencia == "alta":
            await client.send_message(SUPERGRUPO_ID, f"🚨 *ALERTA URGENTE — {info.get('nome','')}*\n\n{resumo}\n\n🕒 {horario}", reply_to=obter_topico_por_idioma(chat_id), parse_mode="markdown")
    except Exception as e:
        logger.exception("Erro no handler: %s", e)
        auditar("erro_handler", str(e))

@client.on(events.NewMessage(chats=[SUPERGRUPO_ID], pattern=r"^/status$"))
async def cmd_status(event):
    await event.respond(f"✅ *Radar Global Online*\n\n🌐 Grupos monitorados: *{len(GRUPOS_MONITORADOS)}*\n📊 Mensagens hoje: *{stats_dia.get('total',0)}*\n📦 Buffers ativos: *{sum(1 for v in buffers_por_grupo.values() if v)}*", parse_mode="markdown")

@client.on(events.NewMessage(chats=[SUPERGRUPO_ID], pattern=r"^/relatorio$"))
async def cmd_relatorio(event):
    txt = f"📰 *Relatório — {datetime.now().strftime('%d/%m/%Y')}*\n\n📊 Total: *{stats_dia.get('total',0)}*\n\n"
    if stats_dia.get("por_grupo"):
        txt += "🌐 *Por grupo:*\n" + "".join(f"• {g}: {q}\n" for g, q in sorted(stats_dia["por_grupo"].items(), key=lambda x: -x[1])[:10])
    if stats_dia.get("temas"):
        txt += "\n🏷️ *Temas:*\n" + "".join(f"• {t}: {q}\n" for t, q in sorted(stats_dia["temas"].items(), key=lambda x: -x[1])[:8])
    await event.respond(txt[:4000], parse_mode="markdown")

@client.on(events.NewMessage(chats=[SUPERGRUPO_ID], pattern=r"^/ultimos$"))
async def cmd_ultimos(event):
    if not ultimos_registros:
        await event.respond("Nenhum registro ainda.")
        return
    txt = "🕘 *Últimas traduções:*\n\n"
    for r in ultimos_registros[-10:]:
        txt += f"{emoji_urgencia(r.get('urgencia','baixa'))} *{r.get('grupo','')}* | {r.get('horario','')}\n{r.get('resumo','')[:140]}\n\n"
    await event.respond(txt[:4000], parse_mode="markdown")

@client.on(events.NewMessage(chats=[SUPERGRUPO_ID], pattern=r"^/ajuda$"))
async def cmd_ajuda(event):
    await event.respond("🤖 *Comandos do Radar Global:*\n\n/status\n/relatorio\n/ultimos\n/ajuda", parse_mode="markdown")

async def tarefa_relatorio_diario():
    ultima = None
    while True:
        try:
            agora = datetime.now()
            hoje = agora.strftime("%Y-%m-%d")
            if agora.hour == 20 and agora.minute == 0 and ultima != hoje:
                await client.send_message(SUPERGRUPO_ID, f"📰 *Boletim Diário*\n\nTotal: {stats_dia.get('total',0)}", parse_mode="markdown")
                ultima = hoje
                await asyncio.sleep(61)
            if stats_dia.get("data") != hoje_str():
                globals()["stats_dia"] = novo_stats()
                salvar_json(STATS_FILE, globals()["stats_dia"])
        except Exception as e:
            logger.exception("Erro relatório diário: %s", e)
        await asyncio.sleep(20)

async def iniciar_bot():
    await client.start()
    asyncio.create_task(tarefa_relatorio_diario())
    logger.info("Super Tradutor / Radar Global iniciado — monitorando %s grupos.", len(GRUPOS_MONITORADOS))
    auditar("startup", f"Bot iniciado com {len(GRUPOS_MONITORADOS)} grupos.")
    await client.run_until_disconnected()

async def main():
    try:
        await iniciar_bot()
    except AuthKeyDuplicatedError:
        logger.error("Sessão duplicada detectada. Gere nova TRADUTOR_SESSION_STRING e use apenas uma instância.")
    except Exception as e:
        logger.exception("Erro fatal no Tradutor: %s", e)
        auditar("erro_fatal", str(e))

if __name__ == "__main__":
    asyncio.run(main())
