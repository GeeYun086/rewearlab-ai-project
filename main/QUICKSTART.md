# 🚀 빠른 시작 가이드

## 1️⃣ 로컬 테스트 (5분)

### 준비물
- Docker Desktop 설치
- 8GB 이상 RAM

### 실행
```bash
# 프로젝트 다운로드 및 압축 해제
tar -xzf clothing-resale-project.tar.gz
cd clothing-resale-project

# 환경 변수 설정 (선택사항)
cp .env.template .env
# .env 파일 편집 (Azure 키 입력)

# Docker Compose로 전체 서비스 실행
docker-compose up -d

# 서비스 확인
docker-compose ps
```

### 접속
- **ChromaDB**: http://localhost:8000
- **임베딩 앱**: http://localhost:8501
- **검색 앱**: http://localhost:8503
- **메인 앱**: http://localhost:8502

### 종료
```bash
docker-compose down
```

---

## 2️⃣ Azure 배포 (30분)

### Step 1: ACR 생성 및 이미지 푸시 (10분)
```bash
# Azure 로그인
az login

# ACR 생성 (Azure Portal에서도 가능)
az acr create \
  --resource-group clothing-resale-rg \
  --name clothingresaleacr \
  --sku Basic

# ACR 로그인
az acr login --name clothingresaleacr

# 이미지 빌드 & 푸시
cd crawler
docker build -t clothingresaleacr.azurecr.io/crawler:latest .
docker push clothingresaleacr.azurecr.io/crawler:latest

cd ../search-app
docker build -t clothingresaleacr.azurecr.io/search-app:latest .
docker push clothingresaleacr.azurecr.io/search-app:latest

cd ../main-app
docker build -t clothingresaleacr.azurecr.io/main-app:latest .
docker push clothingresaleacr.azurecr.io/main-app:latest
```

### Step 2: ChromaDB VM 배포 (10분)
Azure Portal에서:
1. Virtual Machines → Create
2. 이름: `chromadb-vm`
3. Size: `Standard_E4s_v3`
4. OS: Ubuntu 22.04
5. SSH로 접속 후:
```bash
sudo apt-get update && sudo apt-get install -y docker.io
sudo docker run -d --name chromadb -p 8000:8000 chromadb/chroma:latest
```

### Step 3: Container Apps 배포 (10분)
Azure Portal에서:
1. Container Apps → Create
2. 검색 앱:
   - Image: `clothingresaleacr.azurecr.io/search-app:latest`
   - Port: 8501
   - Env: `CHROMADB_HOST=<VM_IP>`
3. 메인 앱:
   - Image: `clothingresaleacr.azurecr.io/main-app:latest`
   - Port: 8502
   - Env: `CHROMADB_HOST=<VM_IP>`

### Step 4: 배포 확인
- 검색 앱 URL 접속
- 메인 앱 URL 접속
- 이미지 업로드 테스트

---

## 3️⃣ 데이터 준비 (1-2시간)

### 크롤링 실행
```bash
# 로컬 실행
cd crawler
python musinsa_crawler.py

# 또는 Docker로 실행
docker run -v $(pwd)/data:/data clothingresaleacr.azurecr.io/crawler:latest
```

### 임베딩 실행
```bash
# Streamlit UI 실행
cd embedding
streamlit run musinsa_to_chromadb.py

# 또는 Docker로 실행
docker run -p 8501:8501 \
  -e CHROMADB_HOST=<VM_IP> \
  -v $(pwd)/data:/data \
  clothingresaleacr.azurecr.io/embedding:latest
```

브라우저에서 http://localhost:8501 접속하여:
1. JSON 파일 경로 입력
2. "🚀 카테고리별 객체 탐지 + 임베딩 시작" 클릭
3. 진행 상황 확인 (약 1-2시간 소요)

---

## 4️⃣ 문제 해결

### ChromaDB 연결 실패
```bash
# VM에서 ChromaDB 상태 확인
docker ps
docker logs chromadb

# 방화벽 포트 확인 (8000 열림)
curl http://localhost:8000/api/v1/heartbeat
```

### 이미지 빌드 실패
```bash
# Docker 로그 확인
docker build -t test . --progress=plain

# 디스크 공간 확인
df -h

# Docker 캐시 정리
docker system prune -a
```

### 모델 다운로드 느림
- 첫 실행 시 Hugging Face 모델 다운로드로 10-30분 소요
- 인터넷 연결 확인
- 재시도 (캐시 활용)

---

## 📞 추가 도움

- **상세 배포 가이드**: `azure-deploy/DEPLOY_GUIDE.md`
- **아키텍처 설명**: `ARCHITECTURE.md`
- **프로젝트 README**: `README.md`
