# Compilar desde la raíz del repositorio:
# docker build -f standalone/Dockerfile -t hawks-documentos-v3 .
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends libreoffice-writer fonts-dejavu-core && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py document_quality.py ./
COPY templates ./templates
COPY standalone ./standalone
# En laboratorio: bloquear despliegues que rompan generación, seguridad o formato Liz.
RUN python -m unittest discover -s standalone/tests -v
ENV TEMPLATE_DIR=/app/templates
EXPOSE 10000
CMD ["uvicorn","standalone.main:app","--host","0.0.0.0","--port","10000"]
