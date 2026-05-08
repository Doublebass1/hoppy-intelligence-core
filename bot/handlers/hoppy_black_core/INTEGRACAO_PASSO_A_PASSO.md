# Guia de Integração: Hoppy Black-Core ao seu Bot

Este guia explica como inserir o **Protocolo Black-Core (Nível 3X+)** no seu bot atual que já roda no Railway.

## Passo 1: Preparar o Ambiente no Railway

Como seu bot já está no Railway, você tem duas opções para rodar o Black-Core:
1.  **Mesmo Serviço:** Adicionar as dependências do Black-Core ao seu `requirements.txt` e rodar junto com o bot.
2.  **Serviço Separado (Recomendado):** Criar um novo serviço no Railway apenas para o Black-Core (API) e conectar o bot a ele.

### Variáveis de Ambiente Necessárias no Railway:
Adicione estas variáveis no painel **Variables** do seu projeto:
- `BLACK_CORE_URL`: URL onde o serviço Black-Core estará rodando (ex: `http://localhost:8000`).
- `INTELLIGENCE_X_API_KEY`: Sua chave do IntelX.
- `DEHASHED_API_KEY`: Sua chave do DeHashed.
- `SHODAN_API_KEY`: Sua chave do Shodan.

## Passo 2: Inserir o Código de Integração

1.  **Copie o arquivo** `black_core_handler.py` (que eu gerei) para dentro da pasta `bot/handlers/` ou onde você guarda seus handlers.
2.  **Abra o seu arquivo `hoppy.py`** e faça as seguintes alterações:

### No topo do `hoppy.py`:
```python
from handlers.black_core_handler import cmd_intel  # Importe o novo handler
```

### No `post_init` (linha ~642):
Adicione o comando à lista do menu:
```python
BotCommand("intel", "Protocolo de Inteligência Black-Core (Nível 3X+)"),
```

### No `main()` (linha ~680):
Registre o comando no dispatcher:
```python
application.add_handler(CommandHandler("intel", cmd_intel))
```

## Passo 3: Atualizar o Menu Visual (Opcional)

Se quiser que o botão "🕵️ Portal OSINT" chame a inteligência Black-Core, altere a função `menu_callback` ou `handle_text` para disparar o processo.

## Passo 4: Rodar o Orquestrador

Se você for rodar tudo junto, altere seu `run_all.py` para iniciar o processo do FastAPI do Black-Core em uma nova thread, similar ao que você faz com o Tradutor:

```python
def iniciar_black_core():
    import uvicorn
    from main import app
    uvicorn.run(app, host="0.0.0.0", port=8000)

# No main() do run_all.py:
threading.Thread(target=iniciar_black_core, daemon=True).start()
```

---

## Resumo da Operação
Agora, ao digitar `/intel alvo.onion` no seu bot, o fluxo será:
1.  O bot recebe o comando.
2.  Envia para o **Black-Core Orchestrator**.
3.  O orquestrador ativa o **Tor**, consulta as **20+ ferramentas**, correlaciona no **Neo4j** e resume com a **IA Local**.
4.  O bot devolve o relatório de elite para você no Telegram.

**Pronto! Seu bot agora possui Soberania Neural Nível 3X+.**
