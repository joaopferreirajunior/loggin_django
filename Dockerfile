# ============================
# Dockerfile - Django App
# ============================
FROM python:3.11-slim

# Impede geração de bytecodes (.pyc)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Define diretório de trabalho
WORKDIR /app

# Instala dependências de sistema
RUN apt-get update && apt-get install -y \
    build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copia dependências Python e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o projeto inteiro
COPY . .

# 🔥 Remove bytecodes antigos (garante build limpo)
RUN find . -name "*.pyc" -delete && find . -name "__pycache__" -type d -exec rm -rf {} +

# Expõe a porta do Django
EXPOSE 8000

# Comando padrão
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
