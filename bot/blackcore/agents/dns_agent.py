import socket
import dns.resolver
import whois


def dns_lookup(query: str):
    results = []

    clean_query = query.strip().replace("https://", "").replace("http://", "").split("/")[0]

    try:
        ip = socket.gethostbyname(clean_query)
        results.append(f"DNS: {clean_query} resolve para IP {ip}")
    except Exception as e:
        results.append(f"DNS: não foi possível resolver {clean_query} ({e})")

    record_types = ["A", "AAAA", "MX", "NS", "TXT"]

    for record_type in record_types:
        try:
            answers = dns.resolver.resolve(clean_query, record_type)
            for answer in answers:
                results.append(f"{record_type}: {answer}")
        except Exception:
            pass

    return results


def whois_lookup(query: str):
    results = []

    clean_query = query.strip().replace("https://", "").replace("http://", "").split("/")[0]

    try:
        data = whois.whois(clean_query)

        registrar = data.registrar or "N/A"
        creation_date = data.creation_date or "N/A"
        expiration_date = data.expiration_date or "N/A"
        name_servers = data.name_servers or []

        results.append(f"WHOIS: Registrador: {registrar}")
        results.append(f"WHOIS: Criado em: {creation_date}")
        results.append(f"WHOIS: Expira em: {expiration_date}")

        if name_servers:
            results.append(f"WHOIS: Name servers: {', '.join(map(str, name_servers[:5]))}")

    except Exception as e:
        results.append(f"WHOIS: erro ao consultar {clean_query} ({e})")

    return results


def run_dns_intel(query: str):
    results = []

    results.extend(dns_lookup(query))
    results.extend(whois_lookup(query))

    return results