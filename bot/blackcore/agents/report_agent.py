def classify_items(results):
    grouped = {
        "duckduckgo": [],
        "dns": [],
        "whois": [],
        "shodan": [],
        "other": [],
    }

    for item in results:
        item_str = str(item)

        lower = item_str.lower()

        if lower.startswith("duckduckgo"):
            grouped["duckduckgo"].append(item_str)
        elif lower.startswith("dns") or lower.startswith("a:") or lower.startswith("aaaa:") or lower.startswith("mx:") or lower.startswith("ns:") or lower.startswith("txt:"):
            grouped["dns"].append(item_str)
        elif lower.startswith("whois"):
            grouped["whois"].append(item_str)
        elif lower.startswith("shodan") or "erro shodan" in lower:
            grouped["shodan"].append(item_str)
        else:
            grouped["other"].append(item_str)

    return grouped


def build_executive_summary(query, target_type, results, risk_score):
    total = len(results)

    if risk_score >= 70:
        level = "alto"
    elif risk_score >= 35:
        level = "moderado"
    else:
        level = "baixo"

    return (
        f"O alvo '{query}' foi analisado como tipo '{target_type}'. "
        f"Foram encontrados {total} itens de inteligência em múltiplas fontes. "
        f"O risco estimado é {level}, com score de {risk_score}%."
    )


def build_recommendations(target_type, risk_score, grouped):
    recommendations = []

    if target_type == "domain":
        recommendations.append("Verificar exposição pública de DNS, MX, TXT e serviços associados.")
        recommendations.append("Revisar registros TXT sensíveis e integrações de terceiros.")
        recommendations.append("Monitorar mudanças futuras em DNS e WHOIS.")

    elif target_type == "ip":
        recommendations.append("Verificar portas expostas e reputação do IP.")
        recommendations.append("Confirmar se os serviços publicados são intencionais.")
        recommendations.append("Monitorar alterações de banners e infraestrutura.")

    else:
        recommendations.append("Refinar a busca usando domínio, IP, e-mail ou nome de organização.")
        recommendations.append("Cruzar o termo com fontes adicionais para reduzir ruído.")

    if grouped.get("shodan"):
        if any("erro shodan" in item.lower() for item in grouped["shodan"]):
            recommendations.append("Corrigir ou validar a chave da API Shodan para ampliar a análise técnica.")

    if risk_score >= 70:
        recommendations.append("Priorizar revisão imediata dos achados críticos.")
    elif risk_score >= 35:
        recommendations.append("Manter monitoramento periódico do alvo.")
    else:
        recommendations.append("Nenhuma ação urgente identificada nesta etapa.")

    return recommendations


def build_report(query, target_type, results, risk_score):
    grouped = classify_items(results)

    summary = build_executive_summary(
        query=query,
        target_type=target_type,
        results=results,
        risk_score=risk_score,
    )

    recommendations = build_recommendations(
        target_type=target_type,
        risk_score=risk_score,
        grouped=grouped,
    )

    risk_emoji = "🟢"
    if risk_score >= 70:
        risk_emoji = "🚨"
    elif risk_score >= 35:
        risk_emoji = "⚠️"

    report = []
    report.append("🛡️ BLACK-CORE INTELLIGENCE REPORT")
    report.append("")
    report.append(f"🎯 Alvo: {query}")
    report.append(f"🧬 Tipo detectado: {target_type}")
    report.append(f"📊 Risco: {risk_emoji} {risk_score}%")
    report.append("")
    report.append("🧠 Resumo executivo:")
    report.append(summary)
    report.append("")

    sources = []

    if grouped["duckduckgo"]:
        sources.append("DuckDuckGo")
    if grouped["dns"]:
        sources.append("DNS")
    if grouped["whois"]:
        sources.append("WHOIS")
    if grouped["shodan"]:
        sources.append("Shodan")
    if grouped["other"]:
        sources.append("Outros")

    report.append("📡 Fontes consultadas:")
    for source in sources:
        report.append(f"• {source}")

    report.append("")
    report.append("📌 Principais achados:")

    max_items_per_group = 4

    for label, key in [
        ("DuckDuckGo", "duckduckgo"),
        ("DNS", "dns"),
        ("WHOIS", "whois"),
        ("Shodan", "shodan"),
        ("Outros", "other"),
    ]:
        items = grouped.get(key, [])

        if not items:
            continue

        report.append("")
        report.append(f"🔎 {label}:")

        for item in items[:max_items_per_group]:
            clean_item = item.replace("DuckDuckGo: ", "")
            clean_item = clean_item.replace("Shodan: ", "")
            report.append(f"• {clean_item[:350]}")

        if len(items) > max_items_per_group:
            report.append(f"• ...mais {len(items) - max_items_per_group} achados ocultados para resumir.")

    report.append("")
    report.append("✅ Recomendações:")
    for rec in recommendations:
        report.append(f"• {rec}")

    return "\n".join(report)