FROM python:3.10-slim

WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 임베딩 스크립트 복사
COPY musinsa_to_chromadb.py .

# 데이터 디렉토리 생성
RUN mkdir -p /data /musinsa_cropped_images

# Streamlit 포트 노출
EXPOSE 8501

# 실행
CMD ["streamlit", "run", "musinsa_to_chromadb.py", "--server.port=8501", "--server.address=0.0.0.0"]
