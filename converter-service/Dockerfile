FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 libgomp1 tesseract-ocr tesseract-ocr-ara tesseract-ocr-eng && rm -rf /var/lib/apt/lists/*
COPY converter-service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && pip install --no-cache-dir -r requirements.txt
COPY converter-service /app/converter-service
COPY dist /app/dist
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser
ENV HF_HOME=/home/appuser/.cache/huggingface
EXPOSE 8000
CMD ["uvicorn", "app:app", "--app-dir", "/app/converter-service", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
