# 📖 Guia para Iniciantes: Instalando o Protocolo Omega

Não se preocupe se você não entende de código. Siga estes passos simples para transformar seu bot.

## Passo 1: Subir os arquivos para o seu Projeto
1. Baixe o arquivo `.zip` que eu te enviei.
2. Extraia a pasta `hoppy_black_core` para dentro da pasta principal do seu bot (onde fica o seu `run_all.py`).
3. Envie essas alterações para o seu GitHub (ou faça o upload direto no Railway).

## Passo 2: Rodar o Instalador Automático
No painel do Railway, vá na aba **"Terminal"** ou **"Console"** e digite este comando:
```bash
bash hoppy_black_core/install_omega.sh
```
*Este comando vai organizar todos os arquivos sozinhos para você, como se fosse um passe de mágica.*

## Passo 3: Configurar suas "Chaves" (Variables)
No Railway, clique na aba **Variables** e adicione estas linhas (clique em "New Variable"):

| Nome da Variável | O que colocar |
| :--- | :--- |
| `INTELLIGENCE_X_API_KEY` | Sua chave do IntelX |
| `DEHASHED_API_KEY` | Sua chave do DeHashed |
| `DEHASHED_EMAIL` | Seu e-mail do DeHashed |
| `SHODAN_API_KEY` | Sua chave do Shodan |
| `ADMIN_CHAT_ID` | Seu ID do Telegram |
| `BLACK_CORE_URL` | `http://localhost:8000` |

## Passo 4: Reiniciar
Clique no botão **"Deploy"** ou **"Restart"** no Railway. 

---

## 🕵️ Como usar agora?
Seu bot ganhou superpoderes. Tente digitar estes comandos no chat do Telegram:
1. `/start` - Você verá o novo menu.
2. `/intel google.com` - Para ver a inteligência agêntica em ação.
3. `/monitorar seu_nome` - Para o Sentinel começar a te vigiar.

**Dúvidas Comuns:**
*   *Onde vejo meu ID do Telegram?* Procure pelo bot `@userinfobot` no Telegram.
*   *E se o bot não ligar?* Verifique se você colocou o Token do Telegram corretamente nas Variables.
