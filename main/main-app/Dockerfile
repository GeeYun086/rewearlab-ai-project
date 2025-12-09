FROM python:3.10-slim

WORKDIR /app

# 1. 시스템 패키지 (거의 안 바뀜)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 2. Python 의존성 (가끔 바뀜)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. 모델 다운로드 (안 바뀜)
RUN python -c "from transformers import AutoImageProcessor, AutoModelForObjectDetection; \
    AutoImageProcessor.from_pretrained('yainage90/fashion-object-detection'); \
    AutoModelForObjectDetection.from_pretrained('yainage90/fashion-object-detection')"

# 4. FashionCLIP 모델 미리 다운로드 (추가!)
RUN python -c "import open_clip; \
    open_clip.create_model_and_transforms('hf-hub:Marqo/marqo-fashionSigLIP')"

# 5. 앱 파일은 맨 마지막에! (자주 바뀜)
COPY app.py .

EXPOSE 8502

HEALTHCHECK CMD curl --fail http://localhost:8502/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", "--server.port=8502", "--server.address=0.0.0.0"]