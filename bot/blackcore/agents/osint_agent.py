import requests

from blackcore.agents.shodan_agent import shodan_search
from blackcore.agents.dns_agent import run_dns_intel


def search_duckduckgo(query):
    try:
        url = f"https://api.duckduckgo.com/?q={query}&format=json"

        response = requests.get(url, timeout=20)
        data = response.json()

        resultados = []

        abstract = data.get("AbstractText")

        if abstract:
            resultados.append(f"DuckDuckGo: {abstract}")

        for item in data.get("RelatedTopics", [])[:5]:
            if isinstance(item, dict):
                text = item.get("Text")
                if text:
                    resultados.append(f"DuckDuckGo: {text}")

        if not resultados:
            resultados.append("DuckDuckGo: nenhum resumo relevante encontrado.")

        return resultados

    except Exception as e:
        return [f"Erro DuckDuckGo: {e}"]


def detect_target_type(query: str):
    q = query.strip().lower()

    if q.replace(".", "").isdigit() and q.count(".") == 3:
        return "ip"

    if "." in q and " " not in q:
        return "domain"

    return "keyword"


def run_osint(query):
    resultados = []

    target_type = detect_target_type(query)

    resultados.append(f"Tipo detectado: {target_type}")

    resultados.extend(search_duckduckgo(query))

    if target_type in ["domain", "ip"]:
        resultados.extend(run_dns_intel(query))

    resultados.extend(shodan_search(query))

    return {
        "query": query,
        "target_type": target_type,
        "results": resultados,
    }