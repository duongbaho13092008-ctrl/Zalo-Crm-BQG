FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd -m bqg && mkdir -p du-lieu kho-canh nhac-nen && chown -R bqg /app
USER bqg
EXPOSE 8501 8686
CMD ["streamlit", "run", "webui/app.py", "--server.address", "0.0.0.0"]
