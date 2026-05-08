# 📖 Guia para Iniciantes (Windows 10)

Siga estes passos simples no seu computador para preparar o bot.

## Passo 1: Preparar os arquivos
1. Baixe e extraia o arquivo `.zip` que eu te enviei.
2. Coloque a pasta `hoppy_black_core` dentro da pasta onde está o código do seu bot.
3. Entre na pasta `hoppy_black_core` e **copie** o arquivo `instalar_omega_windows.bat` para a pasta principal do seu bot (onde fica o seu `run_all.py`).

## Passo 2: Rodar o instalador
1. Clique duas vezes no arquivo `instalar_omega_windows.bat`.
2. Uma tela preta vai aparecer e organizar todos os arquivos automaticamente. 
3. Quando terminar, pressione qualquer tecla para fechar.

## Passo 3: Enviar para o Railway
Agora que os arquivos estão organizados:
1. Faça o upload de tudo para o seu GitHub ou direto no Railway (conforme você já faz hoje).
2. O Railway vai detectar os novos arquivos e iniciar a instalação.

## Passo 4: Configurar as Variáveis no Railway
Vá no painel do Railway, aba **Variables**, e adicione:
- `INTELLIGENCE_X_API_KEY`
- `DEHASHED_API_KEY`
- `DEHASHED_EMAIL`
- `SHODAN_API_KEY`
- `ADMIN_CHAT_ID` (Seu ID do Telegram)
- `BLACK_CORE_URL` = `http://localhost:8000`

---

### 🕵️ Dicas para Windows:
- **Python:** Certifique-se de que você tem o Python instalado no seu Windows se for testar localmente.
- **Tor:** Para as funções de Deep Web funcionarem no seu PC, você precisaria do Tor Expert Bundle instalado, mas no Railway isso é configurado automaticamente.

Seu bot agora está pronto para a Soberania Neural!
