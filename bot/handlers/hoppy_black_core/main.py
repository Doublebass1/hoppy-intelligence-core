
from fastapi import FastAPI
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List
import operator
import requests
from stem import process
import time
from neo4j import GraphDatabase
import ollama
from tools import TOOL_FUNCTIONS, setup_tor_session # Importar TOOL_FUNCTIONS e setup_tor_session do tools.py

app = FastAPI(title="Hoppy Black-Core Orchestrator")

# 1. Definir o estado do grafo
class AgentState(TypedDict):
    query: str
    results: List[str]
    analysis: str
    risk_score: int
    graph_data: List[dict] # Para armazenar dados do grafo

# --- Funções de Anonimato (Tor) ---
# setup_tor_session agora vem de tools.py

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
        time.sleep(10) # Dar um tempo para o Tor iniciar completamente
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
        print("Tor is ready.")
    else:
        print("Tor failed to start. Proceeding without Tor proxy.")

@app.on_event("shutdown")
async def shutdown_event():
    global tor_instance
    if tor_instance:
        print("Shutting down Tor process...")
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
            print("Neo4j driver created and connected.")
        except Exception as e:
            print(f"Error connecting to Neo4j: {e}")
            driver = None
    return driver

@app.on_event("shutdown")
async def close_neo4j_driver():
    global driver
    if driver:
        print("Closing Neo4j driver...")
        driver.close()

# 2. Definir os nós (agentes)
def collector_agent(state: AgentState):
    print("Executing Collector Agent...")
    global tor_instance
    current_results = []
    session = None

    if tor_instance:
        session = setup_tor_session()
        try:
            response = session.get("https://check.torproject.org/")
            if "Congratulations. This browser is configured to use Tor." in response.text:
                print("Collector Agent: Successfully connected via Tor.")
            else:
                print("Collector Agent: Tor connection failed, using direct connection.")
                session = requests.session() # Usar sessão direta se Tor falhar
        except requests.exceptions.RequestException as e:
            print(f"Collector Agent: Request via Tor failed: {e}, using direct connection.")
            session = requests.session() # Usar sessão direta se Tor falhar
    else:
        print("Collector Agent: Tor not running, using direct connection.")
        session = requests.session()

    # Chamar as ferramentas OSINT
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
            for i, res in enumerate(state["results"]):
                node_name = f"Result_{i}_{state["query"]}"
                session.run("MERGE (r:Result {name: $node_name, value: $res}) RETURN r", node_name=node_name, res=res)
                session.run("MATCH (q:Query {name: $query}), (r:Result {name: $node_name}) MERGE (q)-[:HAS_RESULT]->(r)", query=state["query"], node_name=node_name)
                graph_nodes.append({"node": node_name, "value": res})
        print("Correlator Agent: Data simulated in Neo4j.")
    else:
        print("Correlator Agent: Neo4j driver not available. Skipping graph operations.")

    correlated_analysis = f"Correlating: {", ".join(state["results"])}. Graph data processed: {len(graph_nodes)} nodes."
    return {"analysis": correlated_analysis, "graph_data": graph_nodes}

def contextualizer_agent(state: AgentState):
    print("Executing Contextualizer Agent...")
    try:
        # Simulação de chamada ao Ollama para contextualização
        # Para que isso funcione, você precisa ter o Ollama rodando localmente e um modelo baixado (ex: ollama pull llama3)
        # response = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': f'Contextualize this analysis: {state["analysis"]}'}])
        # contextual_summary = response['message']['content']
        contextual_summary = f"Contextualizing with Ollama (simulated): {state["analysis"]}. This is a high-level summary with local AI insights."
        print("Contextualizer Agent: Contextualized with Ollama (simulated).")
    except Exception as e:
        print(f"Contextualizer Agent: Error with Ollama (simulated): {e}. Using fallback summary.")
        contextual_summary = f"Contextualizing (fallback): {state["analysis"]}. This is a high-level summary."

    return {"analysis": contextual_summary}

def ranker_agent(state: AgentState):
    print("Executing Ranker Agent...")
    score = len(state["results"]) * 10 # Exemplo simples de pontuação
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

# 4. Compilar o grafo
app_graph = workflow.compile()

@app.get("/run_intelligence")
async def run_intelligence(query: str):
    initial_state = {"query": query, "results": [], "analysis": "", "risk_score": 0, "graph_data": []}
    final_state = app_graph.invoke(initial_state)
    return {"query": query, "intelligence_report": final_state}

@app.get("/")
async def read_root():
    return {"message": "Hoppy Black-Core Orchestrator is running! Use /run_intelligence?query=<your_query>"}

