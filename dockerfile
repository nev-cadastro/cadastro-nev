FROM python:3.11-slim  # ← Use Python 3.11 (mais estável)

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar requirements primeiro
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o resto da aplicação
COPY . .

# Criar diretórios necessários
RUN mkdir -p data static/uploads

# Porta
EXPOSE 5000

# Comando para rodar
CMD ["gunicorn", "--bind", "0.0.0.0:${PORT:-5000}", "main:app"]