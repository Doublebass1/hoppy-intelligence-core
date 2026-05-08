
import os
import logging
import requests

logger = logging.getLogger("hoppy.intel")

class IntelModules:
    def __init__(self, session=None):
        self.session = session or requests.Session()
        self.intelx_key = os.environ.get("INTELLIGENCE_X_API_KEY")
        self.dehashed_key = os.environ.get("DEHASHED_API_KEY")
        self.dehashed_email = os.environ.get("DEHASHED_EMAIL")
        self.shodan_key = os.environ.get("SHODAN_API_KEY")

    def search_intelx(self, query):
        """Busca vazamentos e documentos na Deep Web via Intelligence X."""
        if not self.intelx_key: return "IntelX API Key missing."
        url = f"https://2.intelx.io/phonebook/search?k={self.intelx_key}"
        data = {"term": query, "maxresults": 10}
        try:
            # Primeiro cria a busca
            resp = self.session.post(url, json=data, timeout=20)
            id = resp.json().get("id")
            # Depois pega os resultados
            results_url = f"https://2.intelx.io/phonebook/search/result?k={self.intelx_key}&id={id}"
            results = self.session.get(results_url, timeout=20).json()
            return results.get("selectors", [])
        except Exception as e:
            return f"IntelX Error: {e}"

    def search_dehashed(self, query):
        """Busca credenciais vazadas via DeHashed."""
        if not self.dehashed_key or not self.dehashed_email: return "DeHashed credentials missing."
        url = f"https://api.dehashed.com/light/search?query={query}"
        try:
            resp = self.session.get(url, auth=(self.dehashed_email, self.dehashed_key), headers={"Accept": "application/json"})
            return resp.json().get("entries", [])
        except Exception as e:
            return f"DeHashed Error: {e}"

    def search_shodan(self, ip):
        """Analisa infraestrutura de um IP via Shodan."""
        if not self.shodan_key: return "Shodan API Key missing."
        url = f"https://api.shodan.io/shodan/host/{ip}?key={self.shodan_key}"
        try:
            resp = self.session.get(url, timeout=20).json()
            return {
                "ports": resp.get("ports", []),
                "os": resp.get("os", "N/A"),
                "vulns": resp.get("vulns", []),
                "org": resp.get("org", "N/A")
            }
        except Exception as e:
            return f"Shodan Error: {e}"

    def run_all_intel(self, target):
        """Executa a varredura completa em todas as bases."""
        report = {
            "leaks": self.search_intelx(target),
            "credentials": self.search_dehashed(target),
            "infrastructure": {}
        }
        # Se o alvo parecer um IP, roda Shodan
        if target.replace(".", "").isdigit():
            report["infrastructure"] = self.search_shodan(target)
            
        return report
