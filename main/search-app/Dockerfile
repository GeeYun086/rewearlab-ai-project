FROM python:3.10-slim

WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Object Detection 모델만 미리 다운로드
RUN python -c "from transformers import AutoImageProcessor, AutoModelForObjectDetection; \
    AutoImageProcessor.from_pretrained('yainage90/fashion-object-detection'); \
    AutoModelForObjectDetection.from_pretrained('yainage90/fashion-object-detection')"

# FashionCLIP은 런타임에 자동 다운로드

# 검색 앱 스크립트 복사
COPY musinsa_detect.py .

# Streamlit 포트 노출
EXPOSE 8501

# 헬스체크
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# 실행
CMD ["streamlit", "run", "musinsa_detect.py", "--server.port=8501", "--server.address=0.0.0.0"]