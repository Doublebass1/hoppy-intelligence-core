# Hoppy Intelligence Core v1

Primeira versão profissionalizada do Hoppy.

## O que mudou

- Menu principal com botões.
- Comandos do bot registrados no Telegram.
- Portal OSINT seguro inicial.
- `run_all.py` ajustado para manter Hoppy na thread principal e Tradutor em background.
- `tradutor.py` sem sessão local `.session`; exige `TRADUTOR_SESSION_STRING`.
- `link_analyzer.py` agora usa `asyncio.to_thread` para não travar o polling.
- `voice_separation.py` corrigido (`AGUARDANDO_ENTRADA`) e preparado para integração futura.
- Arquivos sensíveis removidos do pacote.

## Atenção de segurança

O projeto anterior continha `credentials.json`, token em script e API hash em exemplos. Rotacione essas chaves se elas estiverem em GitHub público.

Não suba para o GitHub:

- `credentials.json`
- `.env`
- `*.session`
- `TRADUTOR_SESSION_STRING`
- `TELEGRAM_TOKEN`

## Railway

Procfile:

```txt
web: python bot/run_all.py
```

## Comandos principais

- `/start` — menu principal
- `/ajuda` — comandos
- `/painel` — status geral
- `/admin` — checklist de segurança
- `/ia` — IA geral
- `/ia_paciente` — IA com contexto
- `/separar` — fluxo de áudio
- `/osint` — Portal OSINT seguro
- `/buscar_grupos tema` — preparação do buscador de grupos públicos

## Roadmap OSINT das 20 ferramentas

V1 inclui a base de interface/curadoria. As integrações técnicas serão por camadas:

1. Ahmia / Onion Discovery legal
2. Stem / Tor status
3. txtorcon / stack async Tor
4. SpiderFoot / motor OSINT
5. Shodan / defesa e superfície exposta
6. Grafo local estilo Maltego
7. Intelligence X / APIs OSINT autorizadas
8. Demais redes: I2P, Nym, Lokinet, Cwtch e Gosling em fases futuras

O foco é defensivo, legal e de curadoria: não há automação de invasão, coleta ilegal ou acesso a grupos privados.
