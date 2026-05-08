# Hoppy Black-Core (Nível 3X+) - Guia de Implantação

## 1. Visão Geral
O **Hoppy Black-Core** é um ecossistema de inteligência autônomo projetado para orquestração de agentes, anonimato total (via Tor), correlação de dados em grafos (Neo4j) e processamento de linguagem natural local (Ollama).

## 2. Requisitos do Sistema
- **SO:** Linux (Ubuntu 22.04 recomendado)
- **Python:** 3.10 ou superior
- **Docker:** Para rodar Neo4j e Tor (opcional, mas recomendado)
- **Tor:** Instalado e rodando localmente (SocksPort 9050)
- **Neo4j:** Rodando localmente ou em container (bolt://localhost:7687)
- **Ollama:** Instalado e com o modelo `llama3` baixado (`ollama pull llama3`)

## 3. Instalação
1. Clone o repositório ou copie os arquivos para um diretório.
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

## 4. Configuração das APIs
No arquivo `tools.py`, substitua os placeholders pelas suas chaves de API reais:
- `INTELLIGENCE_X_API_KEY`
- `DEHASHED_API_KEY`
- `SHODAN_API_KEY`
- (Adicione outras conforme necessário)

## 5. Execução
Para iniciar o orquestrador:
```bash
uvicorn main:app --reload
```

## 6. Uso
Acesse o endpoint `/run_intelligence` via navegador ou ferramenta de API (Postman/cURL):
```bash
http://localhost:8000/run_intelligence?query=exemplo_de_busca
```

O sistema retornará um relatório completo contendo:
- Dados coletados via Tor.
- Análise de correlação processada no Neo4j.
- Sumarização contextual gerada pela IA local (Ollama).
- Score de risco baseado nos resultados.

## 7. Estrutura do Projeto
- `main.py`: Orquestrador central de agentes (LangGraph + FastAPI).
- `tools.py`: Módulos de integração com ferramentas OSINT e configuração de anonimato.
- `requirements.txt`: Lista de dependências Python.
- `README.md`: Este guia de instruções.

---
**Autor:** Manus AI
**Versão:** 3X+ (Black-Core)
