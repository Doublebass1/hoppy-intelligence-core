
# Usar uma imagem base oficial do Python
FROM python:3.11-slim

# Definir o diretório de trabalho no container
WORKDIR /app

# Instalar dependências do sistema necessárias (opcional, dependendo do bot)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar o arquivo de requisitos para o container
COPY requirements.txt .

# Instalar as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código do bot para o container
COPY . .

# Comando para rodar o bot (ajuste conforme necessário, ex: main.py ou run_all.py)
CMD ["python", "run_all.py"]
