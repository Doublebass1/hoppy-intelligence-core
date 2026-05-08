"""link_analyzer.py — Análise leve de links sem travar o event loop."""
import asyncio
import html
import yt_dlp


def esc(v) -> str:
    return html.escape(str(v))

async def analyze_link(url: str) -> str:
    url = (url or "").strip()
    if "youtube.com" in url or "youtu.be" in url:
        return await analyze_youtube(url)
    if "instagram.com" in url:
        return await analyze_instagram(url)
    return "🔗 No momento, analiso links do YouTube e Instagram."


def _extract_youtube(url: str):
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "skip_download": True,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

async def analyze_youtube(url: str) -> str:
    try:
        info = await asyncio.to_thread(_extract_youtube, url)
        title = info.get("title", "Título não disponível")
        channel = info.get("channel") or info.get("uploader") or "Canal não disponível"
        view_count = info.get("view_count") or 0
        like_count = info.get("like_count") or 0
        duration = info.get("duration") or 0
        description = info.get("description") or ""
        minutes, seconds = divmod(int(duration), 60)
        hours, minutes = divmod(minutes, 60)
        duration_str = f"{hours}h {minutes}m {seconds}s" if hours else f"{minutes}m {seconds}s"
        desc_preview = description[:500].replace("\n", " ") + ("..." if len(description) > 500 else "")
        return (
            "🎬 <b>Análise do YouTube</b>\n\n"
            f"<b>Título:</b> {esc(title)}\n"
            f"<b>Canal:</b> {esc(channel)}\n"
            f"<b>Duração:</b> {esc(duration_str)}\n"
            f"<b>Visualizações:</b> {view_count:,}\n"
            f"<b>Likes:</b> {like_count:,}\n\n"
            f"<b>Descrição:</b>\n{esc(desc_preview)}"
        )
    except Exception as e:
        return f"❌ Erro ao analisar o vídeo: {esc(e)}"

async def analyze_instagram(url: str) -> str:
    return (
        "📸 <b>Link do Instagram recebido</b>\n\n"
        "Nesta V1 eu reconheço o link. A extração avançada será plugada depois com cuidado, "
        "porque Instagram costuma bloquear automações sem autenticação."
    )
