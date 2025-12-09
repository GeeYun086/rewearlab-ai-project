# Azure 기반 아키텍처 설계

## 📐 전체 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Azure Cloud Platform                              │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                   Container Registry (ACR)                        │   │
│  │  - clothingresaleacr.azurecr.io                                  │   │
│  │  - 이미지: crawler, embedding, search-app, main-app             │   │
│  └────────────────┬────────────────────────────────────────────────┘   │
│                   │                                                       │
│                   ↓                                                       │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │              Container Apps Environment (clothing-env)            │  │
│  │                                                                    │  │
│  │  ┌────────────────────┐          ┌────────────────────┐          │  │
│  │  │   검색 앱          │          │   메인 앱          │          │  │
│  │  │   (search-app)     │          │   (main-app)       │          │  │
│  │  │   Port: 8501       │          │   Port: 8502       │          │  │
│  │  │   Auto-scale: 1-3  │          │   Auto-scale: 1-3  │          │  │
│  │  └─────────┬──────────┘          └─────────┬──────────┘          │  │
│  └────────────┼─────────────────────────────────┼───────────────────┘  │
│               │                                 │                        │
│               └─────────────┬───────────────────┘                        │
│                             ↓                                            │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │              Virtual Machine (chromadb-vm)                        │  │
│  │              Standard_E4s_v3 (4 vCPU, 32GB RAM)                  │  │
│  │                                                                    │  │
│  │  ┌────────────────────────────────────────────────────────────┐  │  │
│  │  │  Docker Container: ChromaDB Server                         │  │  │
│  │  │  Port: 8000                                                 │  │  │
│  │  │  Volume: /mnt/chromadb-data                                │  │  │
│  │  │  Collections: pants, top, outer, dress_skirts              │  │  │
│  │  └────────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                             ↑                                            │
│               ┌─────────────┴───────────────┐                            │
│               │                             │                            │
│  ┌────────────┴──────────┐    ┌────────────┴──────────┐                │
│  │  Container Instances   │    │  Container Instances   │                │
│  │  (크롤러)              │    │  (임베딩)              │                │
│  │  - 주 1회 실행         │    │  - 크롤링 후 실행      │                │
│  │  - Restart: Never      │    │  - Restart: Never      │                │
│  └────────────────────────┘    └────────────────────────┘                │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     Azure Storage Account                        │   │
│  │  - File Share: musinsa-data (크롤링 데이터 저장)                │   │
│  │  - Blob Storage: 사용자 업로드 이미지 (선택사항)               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │              Azure Cognitive Services (선택사항)                │   │
│  │  - Custom Vision: 오염/손상 탐지                                │   │
│  │  - OpenAI: 판매 정보 자동 생성                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 데이터 흐름도

### ETL 파이프라인 (주간 실행)

```
┌──────────────┐
│  Container   │
│  Instance    │
│  (Crawler)   │
└──────┬───────┘
       │ 1. 무신사 크롤링
       │    (Selenium)
       ↓
┌──────────────┐
│ Azure Files  │
│ musinsa-data │
│ (JSON 저장)  │
└──────┬───────┘
       │ 2. JSON 파일 읽기
       ↓
┌──────────────┐
│  Container   │
│  Instance    │
│  (Embedding) │
└──────┬───────┘
       │ 3. Object Detection
       │    + CLIP 임베딩
       ↓
┌──────────────┐
│  ChromaDB    │
│  on VM       │
│  (벡터 저장) │
└──────────────┘
```

### 사용자 요청 흐름

```
┌──────────────┐
│   사용자      │
└──────┬───────┘
       │ 1. 이미지 업로드
       ↓
┌──────────────┐
│  Container   │
│  Apps        │
│  (Main App)  │
└──────┬───────┘
       │ 2. 오염 탐지
       │    (Custom Vision)
       ↓
┌──────────────┐
│ Azure Custom │
│   Vision     │
└──────┬───────┘
       │ 3. 결과 반환
       │    (is_resellable)
       ↓
┌──────────────┐
│  Main App    │
└──────┬───────┘
       │ 4. 객체 탐지
       │    (Fashion Detection)
       ↓
┌──────────────┐
│  Main App    │
│  (CLIP 임베딩)│
└──────┬───────┘
       │ 5. 유사도 검색
       ↓
┌──────────────┐
│  ChromaDB    │
│  (Vector DB) │
└──────┬───────┘
       │ 6. Top-K 결과
       ↓
┌──────────────┐
│  Main App    │
│  (LLM 생성)  │
└──────┬───────┘
       │ 7. 최종 결과
       ↓
┌──────────────┐
│   사용자      │
└──────────────┘
```

---

## 🧩 컴포넌트 상세 설명

### 1. Azure Container Registry (ACR)

**역할**: Docker 이미지 중앙 저장소

**구성**:
- **이름**: clothingresaleacr
- **SKU**: Basic ($5/월)
- **저장 이미지**:
  - `crawler:latest` (500MB)
  - `embedding:latest` (2GB)
  - `search-app:latest` (2GB)
  - `main-app:latest` (2GB)

**비용**: $5/월 + 스토리지 ($0.10/GB/월)

---

### 2. ChromaDB Virtual Machine

**역할**: 벡터 데이터베이스 서버

**사양**:
- **VM 크기**: Standard_E4s_v3
  - 4 vCPU
  - 32GB RAM
  - Premium SSD 256GB
- **OS**: Ubuntu 22.04 LTS
- **Docker 컨테이너**: chromadb/chroma:latest

**네트워킹**:
- **Public IP**: 접근 제어용
- **Private IP**: Container Apps 연결
- **NSG 규칙**:
  - Inbound: SSH (22), ChromaDB (8000)
  - Outbound: All

**데이터 저장**:
- `/mnt/chromadb-data`: 벡터 DB 데이터
- **컬렉션**:
  - `pants`: 바지 (약 100개)
  - `top`: 상의 (약 100개)
  - `outer`: 아우터 (약 100개)
  - `dress_skirts`: 원피스/스커트 (약 100개)

**비용**: $180/월

---

### 3. Container Apps - 검색 앱

**역할**: 원본 musinsa_detect.py 실행 (유사 상품 검색)

**구성**:
- **이미지**: clothingresaleacr.azurecr.io/search-app:latest
- **CPU/Memory**: 1 vCPU, 2GB RAM
- **포트**: 8501
- **Ingress**: External (HTTPS)
- **Auto-scaling**:
  - Min replicas: 1
  - Max replicas: 3
  - Scale rule: HTTP requests

**환경 변수**:
```env
CHROMADB_HOST=<VM_PRIVATE_IP>
CHROMADB_PORT=8000
```

**비용**: $30/월 (항상 실행)

---

### 4. Container Apps - 메인 앱

**역할**: 통합 UI (오염 탐지 + 검색 + 정보 생성)

**구성**:
- **이미지**: clothingresaleacr.azurecr.io/main-app:latest
- **CPU/Memory**: 1 vCPU, 2GB RAM
- **포트**: 8502
- **Ingress**: External (HTTPS)
- **Auto-scaling**:
  - Min replicas: 1
  - Max replicas: 3

**환경 변수**:
```env
CHROMADB_HOST=<VM_PRIVATE_IP>
CHROMADB_PORT=8000
AZURE_CUSTOM_VISION_ENDPOINT=<ENDPOINT>
AZURE_CUSTOM_VISION_KEY=<KEY>
AZURE_CUSTOM_VISION_PROJECT_ID=<PROJECT_ID>
```

**비용**: $30/월 (항상 실행)

---

### 5. Container Instances - 크롤러

**역할**: 주간 무신사 데이터 크롤링

**구성**:
- **이미지**: clothingresaleacr.azurecr.io/crawler:latest
- **CPU/Memory**: 2 vCPU, 4GB RAM
- **Restart policy**: Never (일회성 실행)
- **Volume**: Azure Files (musinsa-data)

**실행 주기**:
- 주 1회 (Azure Logic Apps 트리거)
- 실행 시간: 약 1시간

**출력**:
- `/data/musinsa_all_products.json`
- `/data/musinsa_바지.json`
- `/data/musinsa_상의.json`
- `/data/musinsa_아우터.json`
- `/data/musinsa_원피스_스커트.json`

**비용**: $5/월 (주 1회 × 1시간)

---

### 6. Container Instances - 임베딩

**역할**: 크롤링 데이터 → ChromaDB 임베딩

**구성**:
- **이미지**: clothingresaleacr.azurecr.io/embedding:latest
- **CPU/Memory**: 2 vCPU, 8GB RAM (GPU 권장)
- **Restart policy**: Never
- **Volume**: Azure Files (musinsa-data)

**환경 변수**:
```env
CHROMADB_HOST=<VM_PRIVATE_IP>
CHROMADB_PORT=8000
```

**실행 주기**:
- 크롤러 완료 후 수동 실행
- 실행 시간: 약 2시간 (400개 상품 기준)

**처리 과정**:
1. JSON 파일 로드
2. Fashion Object Detection (yainage90 모델)
3. CLIP 임베딩 (Marqo/marqo-fashionSigLIP)
4. ChromaDB 저장

**비용**: $10/월 (주 1회 × 2시간)

---

### 7. Azure Storage Account

**역할**: 크롤링 데이터 및 이미지 저장

**구성**:
- **File Share**: musinsa-data
  - 크롤링 JSON 파일
  - 크롭된 이미지 (선택사항)
- **Blob Storage**: 사용자 업로드 이미지 (선택사항)

**비용**: $20/월 (100GB 기준)

---

### 8. Azure Cognitive Services (선택사항)

#### Custom Vision
- **역할**: 의류 오염/손상 탐지
- **SKU**: Standard S0
- **비용**: $50/월 (1,000건 기준)

#### OpenAI
- **역할**: 판매 정보 자동 생성
- **모델**: GPT-4o
- **비용**: $50/월 (1,000건 기준)

---

## 💰 예상 비용 (월별)

| 리소스 | 구성 | 월 비용 |
|--------|------|---------|
| **ChromaDB VM** | Standard_E4s_v3 (항상 실행) | $180 |
| **Container Apps (검색)** | 1 vCPU, 2GB (항상 실행) | $30 |
| **Container Apps (메인)** | 1 vCPU, 2GB (항상 실행) | $30 |
| **Container Instances (크롤러)** | 주 1회 실행 (1시간) | $5 |
| **Container Instances (임베딩)** | 주 1회 실행 (2시간) | $10 |
| **Container Registry** | Basic + 스토리지 | $5 |
| **Storage Account** | 100GB Files + Blob | $20 |
| **Azure Custom Vision** | Standard S0 (선택) | $50 |
| **Azure OpenAI** | GPT-4o (선택) | $50 |
| **총 예상 비용** | | **$380/월** |

### 비용 최적화 옵션

1. **VM 종료 스케줄**: 야간/주말에 ChromaDB VM 종료 → $90/월 절감
2. **Container Apps Idle**: Min replicas = 0 → $40/월 절감
3. **GPU 미사용**: CPU로 임베딩 (느리지만 저렴) → $5/월 절감
4. **Custom Vision 제외**: 오염 탐지 미사용 → $50/월 절감

**최소 구성 비용**: $180/월 (VM + 검색 앱만 실행)

---

## 🔐 보안 고려사항

### 1. 네트워크 보안
- **NSG (Network Security Group)**: VM 포트 제한
- **Private Endpoint**: ChromaDB를 VNet 내부로 제한 (권장)
- **SSL/TLS**: Container Apps는 기본 HTTPS 제공

### 2. 인증 및 권한
- **Managed Identity**: Container Apps → ACR 인증
- **Key Vault**: API 키 및 시크릿 관리 (권장)
- **RBAC**: Resource Group 수준 권한 관리

### 3. 데이터 보호
- **Encryption at Rest**: Azure Storage 기본 암호화
- **Encryption in Transit**: HTTPS 강제
- **Backup**: ChromaDB 데이터 정기 백업

---

## 📊 모니터링 및 로깅

### Azure Monitor
- **Metrics**: CPU, Memory, Network
- **Alerts**: 비정상 상태 알림
- **Log Analytics**: 중앙 로그 저장소

### Application Insights
- **성능 추적**: 요청 응답 시간
- **에러 추적**: 예외 및 실패 로그
- **사용량 분석**: 사용자 행동 패턴

---

## 🚀 확장 전략

### 단기 (1-3개월)
- [ ] Azure Logic Apps로 크롤러 자동 스케줄링
- [ ] Azure Functions로 경량 API 추가
- [ ] Azure Monitor 대시보드 구성

### 중기 (3-6개월)
- [ ] GPU VM으로 임베딩 성능 향상
- [ ] Redis Cache로 검색 결과 캐싱
- [ ] Azure CDN으로 이미지 전송 최적화

### 장기 (6개월+)
- [ ] Kubernetes (AKS)로 마이그레이션
- [ ] Azure AI Search로 하이브리드 검색
- [ ] Multi-region 배포

---

## 📚 참고 자료

- [Azure Container Apps 문서](https://learn.microsoft.com/ko-kr/azure/container-apps/)
- [Azure Container Registry 문서](https://learn.microsoft.com/ko-kr/azure/container-registry/)
- [ChromaDB 공식 문서](https://docs.trychroma.com/)
- [CLIP 모델 설명](https://openai.com/research/clip)
