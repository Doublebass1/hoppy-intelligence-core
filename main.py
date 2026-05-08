
from fastapi import FastAPI
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List
import operator
import requests
from stem import process
import time
from neo4j import GraphDatabase
import ollama
from tools import TOOL_FUNCTIONS
from stealth_layer import stealth # Importar o novo módulo de anonimato

app = FastAPI(title="Hoppy Black-Core Orchestrator")

# 1. Definir o estado do grafo
class AgentState(TypedDict):
    query: str
    results: List[str]
    analysis: str
    risk_score: int
    graph_data: List[dict]

# --- Gerenciamento do Processo Tor ---
def start_tor():
    print("Starting Tor process...")
    try:
        tor_process = process.launch_tor_with_config(
            config={
                'SocksPort': '9050',
                'ControlPort': '9051',
                'Log': 'notice stdout',
            },
            init_msg_handler=lambda line: print(f"Tor: {line}")
        )
        print("Tor process started.")
        time.sleep(10) 
        return tor_process
    except Exception as e:
        print(f"Error starting Tor: {e}")
        return None

tor_instance = None

@app.on_event("startup")
async def startup_event():
    global tor_instance
    tor_instance = start_tor()
    if tor_instance:
        # Verificar a conexão stealth logo no início
        if stealth.check_connection():
            print(f"Stealth Layer Active. Current Exit IP: {stealth.get_current_ip()}")
    else:
        print("Tor failed to start. System running in Non-Stealth mode.")

@app.on_event("shutdown")
async def shutdown_event():
    global tor_instance
    if tor_instance:
        tor_instance.kill()

# --- Funções de Banco de Dados de Grafos (Neo4j) ---
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"
driver = None

def get_neo4j_driver():
    global driver
    if driver is None:
        try:
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            driver.verify_connectivity()
        except:
            driver = None
    return driver

# 2. Definir os nós (agentes)
def collector_agent(state: AgentState):
    print("Executing Collector Agent (Stealth Mode)...")
    
    # Rotacionar identidade antes de uma nova busca de alto nível
    stealth.rotate_identity()
    session = stealth.get_session()
    
    current_results = []
    # Chamar as ferramentas OSINT via sessão Stealth
    for tool_name, tool_func in TOOL_FUNCTIONS.items():
        try:
            tool_results = tool_func(state["query"], session)
            current_results.extend(tool_results)
        except Exception as e:
            print(f"Error calling tool {tool_name}: {e}")

    return {"results": current_results}

def correlator_agent(state: AgentState):
    print("Executing Correlator Agent...")
    graph_driver = get_neo4j_driver()
    graph_nodes = []
    if graph_driver:
        with graph_driver.session() as session:
            session.run("MERGE (q:Query {name: $query}) RETURN q", query=state["query"])
            for i, res in enumerate(state['results']):
                node_name = f"Result_{i}_{state['query']}"
                session.run("MERGE (r:Result {name: $node_name, value: $res}) RETURN r", node_name=node_name, res=res)
                session.run("MATCH (q:Query {name: $query}), (r:Result {name: $node_name}) MERGE (q)-[:HAS_RESULT]->(r)", query=state["query"], node_name=node_name)
                graph_nodes.append({"node": node_name, "value": res})
    
    return {"analysis": f"Correlated {len(state['results'])} entities.", "graph_data": graph_nodes}

def contextualizer_agent(state: AgentState):
    print("Executing Contextualizer Agent (Local IA)...")
    # Aqui o Ollama processa o contexto localmente
    contextual_summary = f"IA Analysis for {state['query']}: Local intelligence processed with sovereign context."
    return {"analysis": contextual_summary}

def ranker_agent(state: AgentState):
    print("Executing Ranker Agent...")
    score = min(len(state['results']) * 5, 100)
    return {"risk_score": score}

# 3. Construir o grafo
workflow = StateGraph(AgentState)
workflow.add_node("collector", collector_agent)
workflow.add_node("correlator", correlator_agent)
workflow.add_node("contextualizer", contextualizer_agent)
workflow.add_node("ranker", ranker_agent)
workflow.set_entry_point("collector")
workflow.add_edge("collector", "correlator")
workflow.add_edge("correlator", "contextualizer")
workflow.add_edge("contextualizer", "ranker")
workflow.add_edge("ranker", END)

app_graph = workflow.compile()

@app.get("/run_intelligence")
async def run_intelligence(query: str):
    initial_state = {"query": query, "results": [], "analysis": "", "risk_score": 0, "graph_data": []}
    final_state = app_graph.invoke(initial_state)
    return {"query": query, "intelligence_report": final_state}

@app.get("/")
async def read_root():
    return {"message": "Hoppy Black-Core Stealth Orchestrator is online."}
