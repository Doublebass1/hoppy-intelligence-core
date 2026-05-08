
@echo off
title Instalador Hoppy Black-Core Omega (Windows)
echo 🚀 Iniciando Organizacao Automatica: Protocolo Omega
echo ---------------------------------------------------

:: 1. Criar pastas
echo 📁 Criando pastas do sistema...
if not exist "bot\handlers" mkdir "bot\handlers"
if not exist "sessions" mkdir "sessions"
if not exist "database" mkdir "database"

:: 2. Mover arquivos
echo 🚚 Movendo arquivos para os locais corretos...

:: Backup do main original se existir
if exist "main.py" (
    echo 💾 Criando backup do main.py antigo...
    copy main.py main_backup.py
)

:: Copiar novos arquivos do Core
copy /y "hoppy_black_core\main.py" "."
copy /y "hoppy_black_core\stealth_layer.py" "."
copy /y "hoppy_black_core\intel_modules.py" "."
copy /y "hoppy_black_core\onion_scraper.py" "."
copy /y "hoppy_black_core\sentinel_service.py" "."
copy /y "hoppy_black_core\bullet_engine.py" "."
copy /y "hoppy_black_core\cookie_ghost.py" "."
copy /y "hoppy_black_core\hydra_module.py" "."
copy /y "hoppy_black_core\tools.py" "."

:: Copiar Handlers e Bot Modificado
copy /y "hoppy_black_core\black_core_handler.py" "bot\handlers\"
copy /y "hoppy_black_core\hoppy_modified.py" "bot\hoppy.py"
copy /y "hoppy_black_core\run_all_modified.py" "bot\run_all.py"

echo ---------------------------------------------------
echo ✅ TUDO PRONTO NO SEU WINDOWS!
echo ---------------------------------------------------
echo Agora voce pode enviar esses arquivos para o Railway.
echo Nao esqueca de configurar as Variables no painel do Railway!
echo ---------------------------------------------------
pause
