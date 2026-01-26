# Dockerfile para Integrado Omnicanal
FROM python:3.11-slim

# Metadatos
LABEL maintainer="Integrado Team"
LABEL description="Sistema Multiagente Omnicanal con CrewAI"
LABEL version="1.0.0"

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Crear directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de configuración
COPY pyproject.toml ./
COPY README.md ./

# Instalar dependencias de Python
RUN pip install --upgrade pip && \
    pip install crewai[tools]>=0.203.1,<1.0.0 && \
    pip install -e .

# Copiar código fuente
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY examples/ ./examples/
COPY docs/ ./docs/

# Crear directorios necesarios
RUN mkdir -p temp_audio logs data

# Configurar permisos
RUN chmod +x scripts/start_server.py

# Puerto expuesto
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando por defecto
CMD ["python", "scripts/start_server.py"]






