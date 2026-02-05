FROM python:3.11-slim

# Evita perguntas durante a instalação
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro (cache mais eficiente)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar o resto da aplicação
COPY . .

# Criar diretório para dados
RUN mkdir -p data static/uploads

# Expor porta
EXPOSE 5000

# Comando para rodar
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "main:app"]