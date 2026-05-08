import os
from pathlib import Path

import shodan
from dotenv import load_dotenv


# Caminho exato para: super_bot/bot/.env
BOT_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BOT_DIR / ".env"

load_dotenv(dotenv_path=ENV_FILE)

SHODAN_API_KEY = os.getenv("SHODAN_API_KEY")


def shodan_search(query):
    if not SHODAN_API_KEY:
        return [
            f"Erro Shodan: SHODAN_API_KEY não encontrada no .env. "
            f"Arquivo procurado: {ENV_FILE}"
        ]

    try:
        api = shodan.Shodan(SHODAN_API_KEY)
        results = api.search(query)

        output = []

        for result in results.get("matches", [])[:5]:
            ip = result.get("ip_str", "N/A")
            port = result.get("port", "N/A")
            org = result.get("org", "N/A")
            country = result.get("location", {}).get("country_name", "N/A")
            hostnames = ", ".join(result.get("hostnames", [])) or "N/A"

            output.append(
                f"Shodan: IP {ip} | Porta {port} | Org {org} | País {country} | Hostnames {hostnames}"
            )

        if not output:
            return ["Shodan: nenhum resultado encontrado."]

        return output

    except Exception as e:
        return [f"Erro Shodan: {e}"]