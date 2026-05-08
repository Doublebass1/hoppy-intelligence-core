
#!/bin/bash

echo "🚀 Iniciando Instalação Automática: Hoppy Black-Core Protocolo Omega"
echo "-------------------------------------------------------------------"

# 1. Criar estrutura de pastas se não existir
echo "📁 Criando pastas do sistema..."
mkdir -p bot/handlers
mkdir -p sessions
mkdir -p database

# 2. Mover arquivos para os locais corretos
echo "🚚 Organizando arquivos..."

# Arquivos da Raiz
[ -f main.py ] && mv main.py main_backup.py
cp hoppy_black_core/main.py .
cp hoppy_black_core/stealth_layer.py .
cp hoppy_black_core/intel_modules.py .
cp hoppy_black_core/onion_scraper.py .
cp hoppy_black_core/sentinel_service.py .
cp hoppy_black_core/bullet_engine.py .
cp hoppy_black_core/cookie_ghost.py .
cp hoppy_black_core/hydra_module.py .
cp hoppy_black_core/tools.py .

# Handlers e Bot
cp hoppy_black_core/black_core_handler.py bot/handlers/
cp hoppy_black_core/hoppy_modified.py bot/hoppy.py
cp hoppy_black_core/run_all_modified.py bot/run_all.py

# 3. Instalar dependências
echo "📦 Instalando bibliotecas necessárias..."
pip install -r hoppy_black_core/requirements.txt

echo "-------------------------------------------------------------------"
echo "✅ INSTALAÇÃO CONCLUÍDA COM SUCESSO!"
echo "-------------------------------------------------------------------"
echo "Próximos passos:"
echo "1. Configure suas APIs no painel 'Variables' do Railway."
echo "2. Reinicie o serviço no Railway."
echo "3. Digite /start no seu bot e aproveite o Nível 4X+!"
