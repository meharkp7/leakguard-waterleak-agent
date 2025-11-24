FROM python:3.11-slim

WORKDIR /workspace

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
ENV MODEL_PATH=/workspace/models/waterleak_best.pkl

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]