# Narrative Nexus — App Container
# FastAPI server + frontend static serving
# No GPU required (REQ-108)

FROM python:3.12-slim

WORKDIR /app

# Install FastAPI and scheduler deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY dist/ ./dist/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
