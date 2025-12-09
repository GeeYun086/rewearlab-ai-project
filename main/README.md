# 중고 의류 재판매 가치 판별 서비스

> Azure 기반 AI 의류 검색 & 재판매 가격 산정 서비스
> Docker 컨테이너 기반 배포, Azure Portal 콘솔 배포 지원

---

## 📋 프로젝트 개요

무신사 트렌드 기반 중고 의류 유사도 검색 및 재판매 가능 여부를 AI로 자동 판별하는 서비스입니다.

### 주요 기능
1. **무신사 상품 크롤링** - 카테고리별 상품 데이터 수집 (상의, 아우터, 바지, 원피스/스커트)
2. **객체 탐지 + 임베딩** - Fashion Object Detection → CLIP 임베딩 → ChromaDB 저장
3. **유사 상품 검색** - 업로드 이미지와 유사한 무신사 상품 Top-K 검색
4. **재판매 정보 생성** - Azure Custom Vision (오염 탐지) + Azure OpenAI (판매 정보 자동 생성)

---

## 🗂️ 프로젝트 구조 (원본 코드 기반)

```
clothing-resale-project/
├── README.md                          # 이 파일
├── ARCHITECTURE.md                    # Azure 아키텍처 문서
│
├── crawler/                           # 무신사 크롤러
│   ├── musinsa_crawler.py            # ✅ 원본 코드 그대로
│   ├── Dockerfile                     # 크롤러 Docker 이미지
│   └── requirements.txt
│
├── embedding/                         # ChromaDB 임베딩 파이프라인
│   ├── musinsa_to_chromadb.py        # ✅ 원본 코드 그대로
│   ├── Dockerfile                     # 임베딩 Docker 이미지
│   └── requirements.txt
│
├── search-app/                        # 유사 상품 검색 앱
│   ├── musinsa_detect.py             # ✅ 원본 검색 앱 (Streamlit)
│   ├── Dockerfile                     # 검색 앱 Docker 이미지
│   └── requirements.txt
│
├── detection-service/                 # Azure Custom Vision 연동
│   ├── detect_defects.py             # 오염/손상 탐지 API
│   ├── Dockerfile
│   └── requirements.txt
│
├── main-app/                          # 통합 메인 앱 (최종 UI)
│   ├── app.py                        # Streamlit 메인 앱
│   ├── Dockerfile
│   └── requirements.txt
│
├── chromadb-server/                   # ChromaDB 서버
│   ├── Dockerfile                     # ChromaDB 서버 Docker 이미지
│   └── docker-compose.yml            # 로컬 테스트용
│
├── docker-compose.yml                 # 전체 서비스 로컬 테스트
│
└── azure-deploy/                      # Azure 배포 스크립트
    ├── deploy-chromadb-vm.sh         # ChromaDB VM 배포
    ├── deploy-crawler.sh             # 크롤러 Container Instance 배포
    ├── deploy-embedding.sh           # 임베딩 Container Instance 배포
    ├── deploy-search-app.sh          # 검색 앱 Container Apps 배포
    └── deploy-main-app.sh            # 메인 앱 Container Apps 배포
```

---

## 🐳 Docker 기반 배포 전략

### 1. **ChromaDB 서버** (Azure VM + Docker)
```bash
# Azure VM에 ChromaDB 서버 배포
docker run -d \
  --name chromadb \
  -p 8000:8000 \
  -v /mnt/chromadb-data:/chroma/data \
  chromadb/chroma:latest
```

### 2. **크롤러** (Azure Container Instances - 스케줄 실행)
```bash
# 매주 1회 실행 (Azure Logic Apps 트리거)
docker build -t crawler:latest ./crawler
docker run crawler:latest
```

### 3. **임베딩 파이프라인** (Azure Container Instances - 수동/스케줄 실행)
```bash
# 크롤링 후 실행
docker build -t embedding:latest ./embedding
docker run \
  -e CHROMADB_HOST=<VM_IP> \
  -v /data:/data \
  embedding:latest
```

### 4. **검색 앱** (Azure Container Apps - 항상 실행)
```bash
# 원본 musinsa_detect.py 기반
docker build -t search-app:latest ./search-app
```

### 5. **메인 앱** (Azure Container Apps - 항상 실행)
```bash
# 통합 UI (검색 + 오염 탐지 + 정보 생성)
docker build -t main-app:latest ./main-app
```

---

## 🚀 빠른 시작 (로컬 테스트)

### 1. 전체 서비스 Docker Compose로 실행
```bash
# 모든 서비스 한 번에 실행
docker-compose up -d

# 서비스 확인
docker-compose ps

# ChromaDB: http://localhost:8000
# 검색 앱: http://localhost:8501
# 메인 앱: http://localhost:8502
```

### 2. 개별 서비스 실행

#### 크롤러 실행
```bash
cd crawler
docker build -t musinsa-crawler .
docker run -v $(pwd)/data:/data musinsa-crawler
```

#### 임베딩 실행
```bash
cd embedding
docker build -t musinsa-embedding .
docker run \
  -e CHROMADB_HOST=host.docker.internal \
  -v $(pwd)/data:/data \
  musinsa-embedding
```

#### 검색 앱 실행
```bash
cd search-app
docker build -t musinsa-search .
docker run -p 8501:8501 \
  -e CHROMADB_HOST=host.docker.internal \
  musinsa-search
```

---

## ☁️ Azure 배포 가이드 (콘솔 기반)

### 전제 조건
- Azure 구독 (Free Tier 가능)
- Azure Container Registry (ACR) 생성
- Azure Portal 접근 권한

### Step 1: Azure Container Registry 생성
```bash
# Azure Portal에서 수동 생성
1. Portal → "Container Registries" 검색
2. "+ Create" 클릭
3. Resource Group: clothing-resale-rg
4. Registry Name: clothingresaleacr
5. Location: Korea Central
6. SKU: Basic
```

### Step 2: 로컬에서 이미지 빌드 & ACR 푸시
```bash
# ACR 로그인
az login
az acr login --name clothingresaleacr

# 이미지 빌드 & 푸시
cd crawler
docker build -t clothingresaleacr.azurecr.io/crawler:latest .
docker push clothingresaleacr.azurecr.io/crawler:latest

cd ../embedding
docker build -t clothingresaleacr.azurecr.io/embedding:latest .
docker push clothingresaleacr.azurecr.io/embedding:latest

cd ../search-app
docker build -t clothingresaleacr.azurecr.io/search-app:latest .
docker push clothingresaleacr.azurecr.io/search-app:latest

cd ../main-app
docker build -t clothingresaleacr.azurecr.io/main-app:latest .
docker push clothingresaleacr.azurecr.io/main-app:latest
```

### Step 3: ChromaDB VM 배포 (Azure Portal)
```
1. Portal → "Virtual Machines" → "+ Create"
2. 설정:
   - Name: chromadb-vm
   - Size: Standard_E4s_v3 (4 vCPU, 32GB RAM)
   - OS: Ubuntu 22.04 LTS
   - Disk: Premium SSD 256GB
3. SSH 접속 후:
   sudo apt update && sudo apt install -y docker.io
   sudo docker run -d --name chromadb -p 8000:8000 -v /mnt/chromadb-data:/chroma/data chromadb/chroma:latest
```

### Step 4: Container Apps 배포 (Azure Portal)

#### 검색 앱 배포
```
1. Portal → "Container Apps" → "+ Create"
2. 설정:
   - App name: musinsa-search-app
   - Container image: clothingresaleacr.azurecr.io/search-app:latest
   - CPU: 1 vCPU, Memory: 2GB
   - Ingress: Enabled (External, Port 8501)
   - Environment Variables:
     * CHROMADB_HOST: <VM_Private_IP>
     * CHROMADB_PORT: 8000
3. Review + Create
```

#### 메인 앱 배포
```
1. Portal → "Container Apps" → "+ Create"
2. 설정:
   - App name: clothing-resale-main
   - Container image: clothingresaleacr.azurecr.io/main-app:latest
   - CPU: 1 vCPU, Memory: 2GB
   - Ingress: Enabled (External, Port 8502)
   - Environment Variables:
     * CHROMADB_HOST: <VM_Private_IP>
     * CHROMADB_PORT: 8000
     * AZURE_CUSTOM_VISION_ENDPOINT: <YOUR_ENDPOINT>
     * AZURE_CUSTOM_VISION_KEY: <YOUR_KEY>
     * AZURE_OPENAI_ENDPOINT: <YOUR_ENDPOINT>
     * AZURE_OPENAI_KEY: <YOUR_KEY>
3. Review + Create
```

### Step 5: Container Instances로 크롤러/임베딩 실행
```
1. Portal → "Container Instances" → "+ Create"
2. 크롤러 설정:
   - Name: musinsa-crawler-job
   - Container image: clothingresaleacr.azurecr.io/crawler:latest
   - Restart Policy: Never (일회성 실행)
   - Volumes: Azure Files (크롤링 결과 저장)

3. 임베딩 설정:
   - Name: musinsa-embedding-job
   - Container image: clothingresaleacr.azurecr.io/embedding:latest
   - Environment Variables:
     * CHROMADB_HOST: <VM_Private_IP>
   - Volumes: Azure Files (크롤링 결과 읽기)
```

---

## 📊 Azure 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────────┐
│                     Azure Cloud                                  │
│                                                                   │
│  ┌──────────────────┐     ┌──────────────────┐                  │
│  │  Container       │     │  Container       │                  │
│  │  Registry (ACR)  │────▶│  Apps            │                  │
│  │                  │     │  (검색 앱)       │◀──┐              │
│  └──────────────────┘     └──────────────────┘   │              │
│                                                    │              │
│  ┌──────────────────┐     ┌──────────────────┐   │              │
│  │  Container       │     │  VM (Ubuntu)     │   │              │
│  │  Instances       │     │                  │   │              │
│  │  (크롤러/임베딩) │────▶│  ChromaDB Server │◀──┤              │
│  └──────────────────┘     │  (Docker)        │   │              │
│                            └──────────────────┘   │              │
│                                                    │              │
│  ┌──────────────────┐     ┌──────────────────┐   │              │
│  │  Azure           │     │  Container       │   │              │
│  │  Custom Vision   │────▶│  Apps            │───┘              │
│  │  (오염 탐지)     │     │  (메인 앱)       │                  │
│  └──────────────────┘     └──────────────────┘                  │
│                                                                   │
│  ┌──────────────────┐                                            │
│  │  Azure OpenAI    │                                            │
│  │  (GPT-4o)        │                                            │
│  └──────────────────┘                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 💰 예상 비용 (월별)

| 리소스 | 구성 | 월 비용 |
|--------|------|---------|
| **ChromaDB VM** | Standard_E4s_v3 (4 vCPU, 32GB RAM) | $180 |
| **Container Apps (검색)** | 1 vCPU, 2GB (항상 실행) | $30 |
| **Container Apps (메인)** | 1 vCPU, 2GB (항상 실행) | $30 |
| **Container Instances (크롤러)** | 주 1회 실행 (1시간) | $5 |
| **Container Instances (임베딩)** | 주 1회 실행 (2시간) | $10 |
| **Azure Custom Vision** | Standard S0 (1,000건/월) | $50 |
| **Azure OpenAI** | GPT-4o (1,000건/월) | $50 |
| **Azure Container Registry** | Basic | $5 |
| **Azure Files** | 100GB (데이터 저장) | $20 |
| **총 예상 비용** | | **$380/월** |

---

## 🔧 원본 코드 설명

### 1. `musinsa_crawler.py`
- **기능**: 무신사 상품 크롤링 (Selenium)
- **카테고리**: 상의, 아우터, 바지, 원피스/스커트
- **출력**: JSON 파일 (상품ID, 브랜드, 제품명, 가격, 이미지URL 등)
- **원본 유지**: ✅ 100% 그대로 사용

### 2. `musinsa_to_chromadb.py`
- **기능**: 
  1. JSON 데이터 로드
  2. Fashion Object Detection (yainage90 모델)
  3. 크롭된 이미지를 FashionCLIP으로 임베딩
  4. ChromaDB에 저장 (카테고리별 컬렉션)
- **특징**: Streamlit UI 포함 (진행 상황 실시간 표시)
- **원본 유지**: ✅ 100% 그대로 사용

### 3. `musinsa_detect.py`
- **기능**: 
  1. 이미지 업로드
  2. Fashion Object Detection (의류 영역 감지)
  3. ChromaDB에서 유사 상품 검색
  4. 결과 표시 (유사도 점수 포함)
- **특징**: Streamlit 기반 웹 앱
- **원본 유지**: ✅ 100% 그대로 사용

---

## 🎯 다음 단계

### Phase 1: 로컬 테스트
- [ ] Docker Compose로 전체 서비스 실행
- [ ] 크롤러 → 임베딩 → 검색 파이프라인 검증

### Phase 2: Azure 배포
- [ ] ChromaDB VM 설정
- [ ] ACR에 이미지 푸시
- [ ] Container Apps 배포 (검색 앱)
- [ ] Container Apps 배포 (메인 앱)

### Phase 3: 통합 & 자동화
- [ ] Azure Logic Apps로 크롤러 스케줄링
- [ ] Azure Monitor로 모니터링 설정
- [ ] Azure Key Vault로 시크릿 관리

---

## 📞 문의

- **작성자**: Sumin
- **프로젝트**: Sookmyung Women's University 졸업 프로젝트
- **기술 스택**: Azure, Docker, Streamlit, ChromaDB, CLIP, Object Detection

---

## 📝 참고 사항

- 원본 코드(`musinsa_crawler.py`, `musinsa_to_chromadb.py`, `musinsa_detect.py`)는 수정 없이 그대로 사용
- Docker 이미지 빌드 시 모델 다운로드로 인해 시간이 걸릴 수 있음 (최초 1회)
- ChromaDB 데이터는 Azure Files 또는 VM 디스크에 영구 저장 필요
- 무신사 크롤링은 로봇 탐지를 우회하므로 주의 필요 (법적 리스크 고려)
