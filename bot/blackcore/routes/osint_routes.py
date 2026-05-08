from fastapi import APIRouter

from blackcore.agents.osint_agent import run_osint, detect_target_type
from blackcore.agents.report_agent import build_report
from blackcore.agents.memory_agent import (
    save_intelligence_report,
    list_recent_reports,
    get_report_by_id,
)
from blackcore.agents.watch_agent import (
    add_watch_target,
    list_watch_targets,
    remove_watch_target,
    update_watch_snapshot,
    get_last_report_id_by_query,
)

router = APIRouter()


def calculate_risk_score(results):
    score = 10

    joined = " ".join(results).lower()

    if "erro shodan" not in joined and "shodan:" in joined:
        score += 15

    if "porta" in joined or "port" in joined:
        score += 15

    if "txt:" in joined:
        score += 5

    if "mx:" in joined:
        score += 5

    if "whois:" in joined:
        score += 5

    if "access denied" in joined:
        score -= 5

    if "não foi possível" in joined:
        score -= 5

    return max(0, min(score, 100))


@router.get("/")
async def root():
    return {
        "status": "online",
        "core": "Hoppy Black-Core",
        "mode": "agentic",
    }


@router.get("/run_intelligence")
async def run_intelligence(query: str):
    osint_data = run_osint(query)

    results = osint_data["results"]
    target_type = osint_data["target_type"]

    risk_score = calculate_risk_score(results)

    report_text = build_report(
        query=query,
        target_type=target_type,
        results=results,
        risk_score=risk_score,
    )

    save_intelligence_report(
        query=query,
        target_type=target_type,
        risk_score=risk_score,
        report_text=report_text,
        findings_count=len(results),
    )

    return {
        "intelligence_report": {
            "analysis": report_text,
            "risk_score": risk_score,
            "graph_data": results,
            "target_type": target_type,
            "saved": True,
        }
    }


@router.get("/intel_history")
async def intel_history(limit: int = 10):
    rows = list_recent_reports(limit=limit)

    history = []

    for row in rows:
        report_id, query, target_type, risk_score, findings_count, created_at = row

        history.append(
            {
                "id": report_id,
                "query": query,
                "target_type": target_type,
                "risk_score": risk_score,
                "findings_count": findings_count,
                "created_at": created_at,
            }
        )

    return {"history": history}


@router.get("/intel_report/{report_id}")
async def intel_report(report_id: int):
    row = get_report_by_id(report_id)

    if not row:
        return {
            "ok": False,
            "error": "Relatório não encontrado.",
        }

    report_id, query, target_type, risk_score, findings_count, report_text, created_at = row

    return {
        "ok": True,
        "report": {
            "id": report_id,
            "query": query,
            "target_type": target_type,
            "risk_score": risk_score,
            "findings_count": findings_count,
            "report_text": report_text,
            "created_at": created_at,
        },
    }


@router.get("/intel_watch")
async def intel_watch(target: str):
    target_type = detect_target_type(target)

    result = add_watch_target(
        target=target,
        target_type=target_type,
    )

    return {
        "ok": result["ok"],
        "message": result["message"],
        "target": target,
        "target_type": target_type,
    }


@router.get("/intel_watchlist")
async def intel_watchlist():
    rows = list_watch_targets()

    watchlist = []

    for row in rows:
        (
            item_id,
            target,
            target_type,
            last_risk_score,
            last_findings_count,
            last_report_id,
            status,
            created_at,
            updated_at,
        ) = row

        watchlist.append(
            {
                "id": item_id,
                "target": target,
                "target_type": target_type,
                "last_risk_score": last_risk_score,
                "last_findings_count": last_findings_count,
                "last_report_id": last_report_id,
                "status": status,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )

    return {"watchlist": watchlist}


@router.get("/intel_unwatch")
async def intel_unwatch(target_id: int):
    removed = remove_watch_target(target_id)

    return {
        "ok": removed,
        "message": "Alvo removido do monitoramento." if removed else "Alvo não encontrado.",
        "target_id": target_id,
    }


@router.get("/intel_watch_run")
async def intel_watch_run():
    rows = list_watch_targets(include_inactive=False)

    if not rows:
        return {
            "ok": True,
            "message": "Nenhum alvo ativo para monitorar.",
            "results": [],
        }

    execution_results = []

    for row in rows:
        (
            item_id,
            target,
            target_type,
            last_risk_score,
            last_findings_count,
            last_report_id,
            status,
            created_at,
            updated_at,
        ) = row

        osint_data = run_osint(target)

        results = osint_data["results"]
        detected_type = osint_data["target_type"]

        risk_score = calculate_risk_score(results)

        report_text = build_report(
            query=target,
            target_type=detected_type,
            results=results,
            risk_score=risk_score,
        )

        save_intelligence_report(
            query=target,
            target_type=detected_type,
            risk_score=risk_score,
            report_text=report_text,
            findings_count=len(results),
        )

        report_id = get_last_report_id_by_query(target)

        update_watch_snapshot(
            target=target,
            risk_score=risk_score,
            findings_count=len(results),
            report_id=report_id,
        )

        risk_change = risk_score - int(last_risk_score or 0)
        findings_change = len(results) - int(last_findings_count or 0)

        execution_results.append(
            {
                "id": item_id,
                "target": target,
                "target_type": detected_type,
                "old_risk_score": last_risk_score,
                "new_risk_score": risk_score,
                "risk_change": risk_change,
                "old_findings_count": last_findings_count,
                "new_findings_count": len(results),
                "findings_change": findings_change,
                "report_id": report_id,
            }
        )

    return {
        "ok": True,
        "message": "Monitoramento executado.",
        "results": execution_results,
    }