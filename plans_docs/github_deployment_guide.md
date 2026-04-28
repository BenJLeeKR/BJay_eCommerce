# GitHub 기반 배포 시스템 구축 가이드

> **대상**: 현재 이커머스 시스템 (FastAPI + PostgreSQL + Kafka + Elasticsearch + Redis)  
> **목표**: GitHub 저장소 기반 CI/CD 파이프라인 구축 및 프로덕션 배포

---

## 목차

1. [전체 배포 아키텍처](#1-전체-배포-아키텍처)
2. [GitHub 저장소 설정](#2-github-저장소-설정)
3. [GitHub Actions CI/CD](#3-github-actions-cicd)
4. [Docker 이미지 빌드 및 레지스트리](#4-docker-이미지-빌드-및-레지스트리)
5. [배포 대상 서버 구성](#5-배포-대상-서버-구성)
6. [환경 변수 및 시크릿 관리](#6-환경-변수-및-시크릿-관리)
7. [데이터베이스 마이그레이션](#7-데이터베이스-마이그레이션)
8. [무중단 배포 전략](#8-무중단-배포-전략)
9. [모니터링 및 알림](#9-모니터링-및-알림)
10. [첫 배포까지 체크리스트](#10-첫-배포까지-체크리스트)

---

## 1. 전체 배포 아키텍처

```mermaid
flowchart TB
    Dev[개발자: git push] --> GitHub[GitHub Repository]
    GitHub --> GHA[GitHub Actions]
    
    subgraph GHA [CI/CD Pipeline]
        direction TB
        Test[1. 테스트 실행]
        Lint[2. Lint 검사]
        Build[3. Docker 이미지 빌드]
        Push[4. Docker Registry Push]
        Deploy[5. SSH로 서버 배포]
    end
    
    Push --> DockerHub[DockerHub / GHCR]
    Deploy --> Server[Production Server]
    
    subgraph Server [Docker Host]
        direction TB
        App[ecommerce-app]
        PG[(PostgreSQL)]
        ES[(Elasticsearch)]
        Redis[(Redis)]
        Kafka[Kafka]
        ZK[ZooKeeper]
        Nginx[Nginx Reverse Proxy]
    end
    
    DockerHub --> Server
```

---

## 2. GitHub 저장소 설정

### 2.1 저장소 생성

```bash
# 로컬 프로젝트에서 Git 초기화
cd /srv/agent_coder_trae
git init
git checkout -b main

# .gitignore 파일 생성
cat > .gitignore << 'EOF'
__pycache__/
*.py[cod]
*.egg-info/
.env
.venv/
venv/
*.log
.pytest_cache/
.mypy_cache/
.ruff_cache/
dist/
build/
*.db
EOF

# 초기 커밋
git add .
git commit -m "init: e-commerce backend system"

# GitHub 원격 저장소 연결
git remote add origin https://github.com/YOUR_ORG/YOUR_REPO.git
git push -u origin main
```

### 2.2 저장소 구조

```
ecommerce-platform/
├── backend/
│   ├── app/
│   ├── tests/
│   ├── scripts/
│   ├── migrations/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── requirements.txt
│   └── .env.example          # 템플릿 환경 변수
├── .github/
│   └── workflows/
│       ├── ci.yml             # CI 파이프라인
│       └── deploy.yml         # CD 파이프라인
├── nginx/
│   └── default.conf          # Nginx 설정 (옵션)
├── .gitignore
├── README.md
└── docker-compose.prod.yml   # 프로덕션용 compose
```

---

## 3. GitHub Actions CI/CD

### 3.1 CI 파이프라인 (`.github/workflows/ci.yml`)

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: ecommerce_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"
          cache-dependency-path: backend/requirements.txt
      
      - name: Install dependencies
        run: |
          cd backend
          pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Run unit tests
        run: |
          cd backend
          pytest tests/unit/ -v --tb=short
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/ecommerce_test
          SECRET_KEY: test-secret-key
      
      - name: Run integration tests
        run: |
          cd backend
          pytest tests/integration/ -v --tb=short
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/ecommerce_test
          SECRET_KEY: test-secret-key
          AUTO_CREATE_TABLES: "true"
```

### 3.2 CD 파이프라인 (`.github/workflows/deploy.yml`)

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      # 1. Docker 이미지 빌드
      - name: Build Docker image
        run: |
          docker build \
            -t ghcr.io/${{ github.repository }}/app:${{ github.sha }} \
            -t ghcr.io/${{ github.repository }}/app:latest \
            ./backend
      
      # 2. Docker Registry 로그인 (GitHub Container Registry)
      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      # 3. 이미지 Push
      - name: Push Docker image
        run: |
          docker push ghcr.io/${{ github.repository }}/app:${{ github.sha }}
          docker push ghcr.io/${{ github.repository }}/app:latest
      
      # 4. 프로덕션 서버에 배포
      - name: Deploy to production server
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.PROD_HOST }}
          username: ${{ secrets.PROD_USER }}
          key: ${{ secrets.PROD_SSH_KEY }}
          script: |
            cd /opt/ecommerce
            docker compose -f docker-compose.prod.yml pull
            docker compose -f docker-compose.prod.yml up -d --force-recreate app
            docker image prune -f
```

### 3.3 GitHub Secrets 설정

GitHub 저장소 → Settings → Secrets and variables → Actions에서 다음 시크릿을 등록:

| 시크릿 이름 | 설명 |
|------------|------|
| `PROD_HOST` | 프로덕션 서버 IP |
| `PROD_USER` | SSH 접속 사용자명 |
| `PROD_SSH_KEY` | SSH Private Key |
| `DOCKER_USERNAME` | Docker Hub 사용자명 (선택) |
| `DOCKER_PASSWORD` | Docker Hub 토큰 (선택) |

---

## 4. Docker 이미지 빌드 및 레지스트리

### 4.1 Dockerfile (이미 작성됨, `backend/Dockerfile`)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4.2 Docker Registry 옵션

| 옵션 | 장점 | 단점 |
|------|------|------|
| **GitHub Container Registry (GHCR)** | GitHub과 통합, 별도 계정 불필요 | GitHub 저장소 단위 관리 |
| **Docker Hub** | 범용성, 커뮤니티 이미지 활용 | rate limit, 별도 계정 필요 |
| **AWS ECR / GCP Artifact Registry** | 클라우드 통합 | 각 클라우드 계정 필요 |

**추천**: GitHub Container Registry (GHCR) — 추가 계정 없이 GitHub Token만으로 사용 가능

### 4.3 로컬에서 빌드 및 테스트

```bash
# 로컬 빌드
docker build -t ecommerce-app:latest ./backend

# 로컬 실행 (개발용)
docker compose -f backend/docker-compose.yml up -d
```

---

## 5. 배포 대상 서버 구성

### 5.1 서버 요구사항

| 항목 | 최소 사양 | 권장 사양 |
|------|----------|----------|
| CPU | 2 cores | 4 cores |
| RAM | 8 GB | 16 GB |
| Disk | 50 GB SSD | 100 GB SSD |
| OS | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS |
| Docker | 24.0+ | 26.0+ |
| Docker Compose | v2 | v2 |

### 5.2 서버 초기 설정

```bash
# 1. SSH 접속
ssh user@your-server-ip

# 2. Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 3. 배포 디렉토리 생성
sudo mkdir -p /opt/ecommerce
sudo chown $USER:$USER /opt/ecommerce

# 4. GitHub Deploy Key 설정
ssh-keygen -t ed25519 -f ~/.ssh/github_deploy -N ""
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys
# → ~/.ssh/github_deploy의 Private Key를 GitHub Secret(PROD_SSH_KEY)에 등록
```

### 5.3 프로덕션 Docker Compose (`docker-compose.prod.yml`)

```yaml
version: "3.8"

services:
  app:
    image: ghcr.io/YOUR_ORG/YOUR_REPO/app:latest
    container_name: ecommerce-app
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file:
      - .env.production
    depends_on:
      postgresql:
        condition: service_healthy
      kafka:
        condition: service_started
      elasticsearch:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 5s
      retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  postgresql:
    image: postgres:16
    container_name: ecommerce-postgresql
    restart: unless-stopped
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./migrations:/docker-entrypoint-initdb.d    # 초기 SQL
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: ecommerce-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    container_name: ecommerce-zookeeper
    restart: unless-stopped
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000

  kafka:
    image: confluentinc/cp-kafka:latest
    container_name: ecommerce-kafka
    restart: unless-stopped
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    volumes:
      - kafka_data:/var/lib/kafka/data

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.13.2
    container_name: ecommerce-elasticsearch
    restart: unless-stopped
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - ES_JAVA_OPTS=-Xms512m -Xmx512m
    ports:
      - "9200:9200"
    volumes:
      - es_data:/usr/share/elasticsearch/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9200/_cluster/health"]
      interval: 30s
      timeout: 10s
      retries: 5

  nginx:
    image: nginx:alpine
    container_name: ecommerce-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf
      - ./ssl:/etc/nginx/ssl              # SSL 인증서
    depends_on:
      - app

volumes:
  postgres_data:
  redis_data:
  kafka_data:
  es_data:
```

### 5.4 Nginx Reverse Proxy (`nginx/default.conf`)

```nginx
upstream app_backend {
    server app:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    location / {
        proxy_pass http://app_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/v1/ {
        proxy_pass http://app_backend;
        proxy_read_timeout 60s;
    }

    # Swagger UI
    location /docs {
        proxy_pass http://app_backend;
    }
    location /openapi.json {
        proxy_pass http://app_backend;
    }
}
```

---

## 6. 환경 변수 및 시크릿 관리

### 6.1 `.env.production` (프로덕션 환경 변수)

```bash
# Database
DB_USER=ecommerce
DB_PASSWORD=<generate-strong-password>
DB_NAME=ecommerce
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgresql:5432/${DB_NAME}

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# Elasticsearch
ELASTICSEARCH_HOSTS=http://elasticsearch:9200

# Redis
REDIS_URL=redis://redis:6379/0

# JWT
SECRET_KEY=<generate-random-64-char-hex>
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
AUTO_CREATE_TABLES=true
LOG_LEVEL=INFO
ENVIRONMENT=production
```

### 6.2 시크릿 생성 명령어

```bash
# 데이터베이스 비밀번호
openssl rand -base64 32

# JWT Secret Key
openssl rand -hex 64
```

### 6.3 서버에 환경 변수 배포

```bash
# 서버에 .env.production 파일 생성
scp .env.production user@your-server:/opt/ecommerce/.env.production

# 또는 서버에서 직접 작성
ssh user@your-server
nano /opt/ecommerce/.env.production
```

---

## 7. 데이터베이스 마이그레이션

### 7.1 현재 방식: AUTO_CREATE_TABLES

현재 시스템은 `AUTO_CREATE_TABLES=true` 설정 시 `Base.metadata.create_all()`로 테이블을 자동 생성한다.

### 7.2 프로덕션 권장: SQL 마이그레이션

```sql
-- migrations/001_init.sql
CREATE SCHEMA IF NOT EXISTS ecommerce;

-- 모든 테이블 CREATE TABLE 문...
```

### 7.3 마이그레이션 실행 전략

```mermaid
flowchart LR
    Init[1. 초기 SQL 실행] --> Auto[2. AUTO_CREATE_TABLES=true]
    Auto --> Stable[3. 안정화 후 수동 마이그레이션]
    Stable --> Alembic[4. Alembic 도입 고려]
```

**초기 배포**:
1. `migrations/` 디렉토리에 초기 SQL 파일 배치
2. `docker-compose.prod.yml`에서 volumes 매핑으로 자동 실행:
   ```yaml
   volumes:
     - ./migrations:/docker-entrypoint-initdb.d
   ```
3. App 컨테이너의 `AUTO_CREATE_TABLES=true` 유지

**이후 마이그레이션**:
- 변경이 필요할 때마다 새로운 SQL 파일 작성
- Alembic 도입 검토 (장기적)

---

## 8. 무중단 배포 전략

### 8.1 Rolling Update (기본)

```yaml
# docker-compose.prod.yml 에서
deploy:
  replicas: 2
  update_config:
    order: start-first      # 새 컨테이너 먼저 시작
    parallelism: 1          # 1개씩 교체
    delay: 10s              # 10초 간격
```

### 8.2 Blue/Green 배포 (고급)

```mermaid
flowchart LR
    subgraph Blue [현재 버전 - Blue]
        B1[app:1.0.0 - port 8001]
    end
    subgraph Green [신규 버전 - Green]
        G1[app:1.1.0 - port 8002]
    end
    Nginx[Nginx] --> Blue
    Nginx -->|스위치| Green
```

**구현 방법**:
1. Green 컨테이너를 다른 포트로 실행
2. 헬스 체크 통과 확인
3. Nginx upstream 포트 변경하여 트래픽 전환
4. Blue 컨테이너 종료

---

## 9. 모니터링 및 알림

### 9.1 Docker Container 모니터링

```bash
# 서버에서 상태 확인 스크립트
cat > /opt/ecommerce/healthcheck.sh << 'SCRIPT'
#!/bin/bash
cd /opt/ecommerce

# Container 상태 확인
echo "=== Container Status ==="
docker compose ps

# App 헬스 체크
echo "=== App Health ==="
curl -sf http://localhost:8000/api/v1/health && echo " OK" || echo " FAIL"

# ES 상태
echo "=== Elasticsearch ==="
curl -sf http://localhost:9200/_cluster/health | python3 -m json.tool

# Kafka Consumer LAG
echo "=== Kafka Consumer ==="
docker compose exec -T kafka kafka-consumer-groups \
  --bootstrap-server kafka:9092 \
  --group ecommerce-consumer-group \
  --describe 2>/dev/null
SCRIPT
chmod +x /opt/ecommerce/healthcheck.sh

# 크론탭에 등록 (10분마다)
crontab -e
*/10 * * * * /opt/ecommerce/healthcheck.sh >> /var/log/ecommerce-health.log 2>&1
```

### 9.2 GitHub Actions 배포 알림

Slack 알림을 추가하려면:

```yaml
# deploy.yml에 추가
- name: Notify Slack
  uses: slackapi/slack-github-action@v1.26.0
  with:
    payload: |
      {
        "text": "✅ 배포 완료: ${{ github.repository }}@${{ github.sha }}"
      }
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### 9.3 로그 관리

```bash
# Docker 로그 확인
docker compose logs -f --tail=100 app

# 로그 파일로 저장 (json-file driver)
# /var/lib/docker/containers/*/*-json.log

# 프로메테우스 + 그라파나 (고급)
# 별도 docker-compose 모니터링 스택 구성
```

---

## 10. 첫 배포까지 체크리스트

### 10.1 준비 단계

- [ ] GitHub 저장소 생성 및 코드 Push
- [ ] `.gitignore`에 민감 정보 제외 확인
- [ ] `docker-compose.prod.yml` 작성
- [ ] `nginx/default.conf` 작성
- [ ] `.env.example` 작성 (실제 값 없이 템플릿만)
- [ ] SSL 인증서 준비 (Let's Encrypt certbot)

### 10.2 서버 설정

- [ ] 클라우드 VM 생성 (Ubuntu 22.04/24.04)
- [ ] 방화벽 설정 (SSH, HTTP, HTTPS만 허용)
  ```bash
  sudo ufw allow 22/tcp
  sudo ufw allow 80/tcp
  sudo ufw allow 443/tcp
  sudo ufw enable
  ```
- [ ] Docker + Docker Compose 설치
- [ ] 배포 디렉토리 생성 (`/opt/ecommerce`)
- [ ] SSH Deploy Key 생성 및 GitHub 등록

### 10.3 GitHub Actions 설정

- [ ] `ci.yml` 워크플로우 작성
- [ ] `deploy.yml` 워크플로우 작성
- [ ] GitHub Secrets 등록 (PROD_HOST, PROD_USER, PROD_SSH_KEY)
- [ ] CI 통과 확인 (Pull Request → 테스트 실행)

### 10.4 배포 실행

- [ ] 서버에 `.env.production` 파일 생성
- [ ] 서버에 `migrations/` SQL 파일 복사
- [ ] `main` 브랜치에 Push → 자동 배포
- [ ] 헬스 체크 확인: `curl http://your-domain.com/api/v1/health`
- [ ] Swagger UI 확인: `http://your-domain.com/docs`
- [ ] ES 상태 확인: `curl http://your-domain.com:9200/_cluster/health`

### 10.5 배포 후 검증

- [ ] 상품 생성 → ES 인덱싱 파이프라인 테스트
- [ ] Consumer Group LAG=0 확인
- [ ] Docker 로그에 에러 없음 확인
- [ ] HTTPS 정상 동작 확인

### 10.6 전체 배포 흐름도

```mermaid
sequenceDiagram
    participant Dev as 개발자
    participant GH as GitHub
    participant GHA as GitHub Actions
    participant Server as Production Server

    Dev->>GH: git push (main 브랜치)
    GH->>GHA: Webhook 트리거
    GHA->>GHA: 1. pytest 실행
    GHA->>GHA: 2. Docker 이미지 빌드
    GHA->>GH: 3. GitHub Container Registry Push
    GHA->>Server: 4. SSH 접속
    Server->>Server: 5. docker compose pull
    Server->>Server: 6. docker compose up -d
    Server->>Server: 7. healthcheck 확인
    Server-->>GHA: 배포 완료 응답
    GHA-->>Dev: Slack 알림
```

---

## 부록: AWS를 통한 배포 (대안)

### A.1 AWS ECS + ECR 사용

GitHub Actions 대신 AWS CodePipeline을 사용하거나 GitHub Actions에서 ECR/ECS를 직접 호출:

```yaml
# deploy-aws.yml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: ap-northeast-2

- name: Login to Amazon ECR
  id: login-ecr
  uses: aws-actions/amazon-ecr-login@v2

- name: Build and push to ECR
  run: |
    docker build -t $ECR_REPO:${{ github.sha }} ./backend
    docker push $ECR_REPO:${{ github.sha }}

- name: Deploy to ECS
  run: |
    aws ecs update-service \
      --cluster ecommerce-cluster \
      --service ecommerce-app \
      --force-new-deployment
```

### A.2 AWS 서비스 매핑

| 로컬/Docker | AWS 대체 서비스 |
|-------------|---------------|
| PostgreSQL (Container) | Amazon RDS (PostgreSQL) |
| Redis (Container) | Amazon ElastiCache (Redis) |
| Kafka (Container) | Amazon MSK (Managed Kafka) |
| Elasticsearch (Container) | Amazon OpenSearch |
| Nginx (Container) | Application Load Balancer (ALB) |
| Docker Host | AWS ECS / EC2 |
| Docker Registry | Amazon ECR |
| SSL 인증서 | AWS Certificate Manager (ACM) |
| 도메인 | Amazon Route 53 |
| 모니터링 | Amazon CloudWatch |
