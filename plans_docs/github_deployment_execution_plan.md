# GitHub 배포 실행 계획

> **목표**: 현재 이커머스 시스템(FastAPI + PostgreSQL + Kafka + Elasticsearch + Redis)을 GitHub Actions 기반 CI/CD로 프로덕션 배포
> **참조**: [`plans/github_deployment_guide.md`](plans/github_deployment_guide.md) — 전체 아키텍처 및 상세 설명
> **수행 모드**: Code mode (파일 생성) + 직접 실행 (서버 설정/GitHub 설정)

---

## 현재 상태 (사전 분석 결과)

| 항목 | 상태 | 비고 |
|------|------|------|
| `.gitignore` | ❌ 없음 | 생성 필요 |
| `.github/workflows/` | ❌ 없음 | `ci.yml` + `deploy.yml` 생성 필요 |
| `docker-compose.prod.yml` | ❌ 없음 | 생성 필요 |
| `nginx/default.conf` | ❌ 없음 | 생성 필요 |
| `backend/Dockerfile` | ✅ 있음 | 수정 불필요 |
| `backend/docker-compose.yml` | ✅ 있음 | 개발용, 프로덕션과 분리 |
| `backend/.env.example` | ✅ 있음 | 템플릿 유지 |
| `backend/.env` | ✅ 있음 | 개발용, 프로덕션 별도 필요 |
| `backend/requirements.txt` | ✅ 있음 | elasticsearch 포함 |
| `backend/migrations/` | ⚠️ 1개만 있음 | 초기화 SQL 별도 필요 |
| `README.md` | ❌ 없음 | 선택사항 |
| Git 초기화 | ❌ 미완료 | `git init` 필요 |
| GitHub 저장소 | ❌ 미생성 | 사용자 직접 생성 |

---

## Phase 1: 배포 인프라 파일 생성 (Code mode 실행)

### 1.1 `.gitignore` 생성
- Python 표준 gitignore (`.env`, `__pycache__/`, `*.pyc`, `.venv/`, `*.log`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `dist/`, `build/`, `*.db`)
- 루트 디렉토리에 생성

### 1.2 `.github/workflows/ci.yml` 생성
- **트리거**: `push` (main, develop), `pull_request` (main)
- **서비스 컨테이너**: PostgreSQL 16 (테스트 DB)
- **단계**: `checkout` → `setup-python@v5` (3.11, cache pip) → `pip install -r requirements.txt` → `pytest tests/unit/ -v --tb=short` → `pytest tests/integration/ -v --tb=short`
- **환경 변수**: `DATABASE_URL`, `SECRET_KEY`, `AUTO_CREATE_TABLES=true`

### 1.3 `.github/workflows/deploy.yml` 생성
- **트리거**: `push` (main)
- **단계**: `checkout` → `docker build -t ghcr.io/${{ github.repository }}/app:${{ github.sha }}` → `docker/login-action@v3` (GHCR) → `docker push` → `appleboy/ssh-action@v1.0.3` (SSH 접속 → pull → up -d --force-recreate)
- **GitHub Secrets 필요**: `PROD_HOST`, `PROD_USER`, `PROD_SSH_KEY`

### 1.4 `docker-compose.prod.yml` 생성
- **서비스**:
  - `app`: ghcr.io 이미지 pull, env_file(.env.production), healthcheck, depends_on(postgresql, kafka, elasticsearch), logging(json-file, max 10MB)
  - `postgresql`: postgres:16, volumes(postgres_data, ./migrations:/docker-entrypoint-initdb.d), healthcheck(pg_isready)
  - `redis`: redis:7-alpine, AOF 모드
  - `zookeeper`: confluentinc/cp-zookeeper
  - `kafka`: confluentinc/cp-kafka, depends_on(zookeeper)
  - `elasticsearch`: elasticsearch:8.13.4, single-node, security disabled, healthcheck
  - `nginx`: nginx:alpine, ports(80, 443), volumes(nginx.conf, ssl), depends_on(app)
- **볼륨**: postgres_data, redis_data, kafka_data, es_data

### 1.5 `nginx/default.conf` 생성
- upstream app_backend → app:8000
- server block 1: port 80 → 301 redirect to HTTPS
- server block 2: port 443 → SSL termination → proxy_pass
- SSL 인증서 경로: `/etc/nginx/ssl/cert.pem`, `/etc/nginx/ssl/key.pem`
- location: `/` (general proxy), `/api/v1/` (timeout 60s), `/docs`, `/openapi.json`

### 1.6 초기 마이그레이션 SQL 생성 (`migrations/001_init.sql`)
- `Create SCHEMA IF NOT EXISTS ecommerce;`
- `CREATE TABLE IF NOT EXISTS ecommerce.brand (...)` — 모든 도메인 테이블
- `CREATE TABLE IF NOT EXISTS ecommerce.category (...)`
- ... (11개 도메인 전체 44개 테이블)
- 인덱스, 외래키, 제약조건 포함
- **참고**: `reference_docs/` 디렉토리의 SQL 파일들 + `combined.sql` 참조

### 1.7 (선택) `README.md` 생성
- 프로젝트 개요, 기술 스택, 로컬 실행 방법, API 문서 링크

---

## Phase 2: Git 초기화 및 GitHub Push (직접 실행)

```bash
# 1. Git 초기화
cd /srv/agent_coder_trae
git init
git checkout -b main

# 2. 초기 커밋
git add .
git commit -m "init: e-commerce backend system with CI/CD"

# 3. GitHub 저장소 생성 (직접 https://github.com/new)
#    - 저장소명: ecommerce-platform (또는 원하는 이름)
#    - Public 또는 Private 선택

# 4. 원격 저장소 연결 및 Push
git remote add origin https://github.com/YOUR_ORG/ecommerce-platform.git
git push -u origin main
```

---

## Phase 3: 프로덕션 서버 설정 (직접 실행)

### 3.1 클라우드 VM 생성
- **권장**: Ubuntu 22.04/24.04 LTS, 4 vCPU, 16GB RAM, 100GB SSD
- **방화벽**: SSH(22), HTTP(80), HTTPS(443) 만 허용
  ```bash
  sudo ufw allow 22/tcp
  sudo ufw allow 80/tcp
  sudo ufw allow 443/tcp
  sudo ufw enable
  ```

### 3.2 Docker 설치
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# 로그아웃 후 재접속
```

### 3.3 배포 디렉토리 생성
```bash
sudo mkdir -p /opt/ecommerce
sudo chown $USER:$USER /opt/ecommerce
```

### 3.4 SSH Deploy Key 생성
```bash
ssh-keygen -t ed25519 -f ~/.ssh/github_deploy -N ""
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys
# Private Key (~/.ssh/github_deploy) 내용을 GitHub Secret에 등록
```

### 3.5 SSL 인증서 발급 (Let's Encrypt)
```bash
# 도메인이 서버 IP에 연결된 상태에서 실행
sudo apt install -y certbot
sudo certbot certonly --standalone -d your-domain.com
# 발급된 인증서: /etc/letsencrypt/live/your-domain.com/{fullchain.pem,privkey.pem}
# → /opt/ecommerce/ssl/ 로 복사 또는 docker volume 매핑
```

### 3.6 `.env.production` 생성
```bash
nano /opt/ecommerce/.env.production
```
```
DB_USER=ecommerce
DB_PASSWORD=<openssl rand -base64 32>
DB_NAME=ecommerce
DATABASE_URL=postgresql://ecommerce:<PASSWORD>@postgresql:5432/ecommerce
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
ELASTICSEARCH_HOSTS=http://elasticsearch:9200
REDIS_URL=redis://redis:6379/0
SECRET_KEY=<openssl rand -hex 64>
ACCESS_TOKEN_EXPIRE_MINUTES=30
AUTO_CREATE_TABLES=true
LOG_LEVEL=INFO
ENVIRONMENT=production
```

---

## Phase 4: GitHub Actions Secrets 등록 (직접 실행)

GitHub 저장소 → Settings → Secrets and variables → Actions → New repository secret

| Secret 이름 | 값 |
|------------|-----|
| `PROD_HOST` | 프로덕션 서버 공인 IP |
| `PROD_SSH_KEY` | `~/.ssh/github_deploy` Private Key 전체 내용 |
| `PROD_USER` | SSH 접속 사용자명 (ec2-user, ubuntu, opc 등) |

---

## Phase 5: 첫 배포 실행 및 검증 (직접 실행)

### 5.1 서버에 파일 배포 (첫 1회만)
```bash
scp docker-compose.prod.yml user@server:/opt/ecommerce/
scp -r nginx/ user@server:/opt/ecommerce/
scp -r backend/migrations/ user@server:/opt/ecommerce/
scp -r ssl/ user@server:/opt/ecommerce/    # Let's Encrypt 인증서
```

### 5.2 GitHub Push → 자동 배포
```bash
git add .
git commit -m "feat: add CI/CD pipeline and production config"
git push origin main
```

### 5.3 배포 검증
```bash
# 헬스 체크
curl http://your-domain.com/api/v1/health

# Swagger UI
curl http://your-domain.com/docs

# Docker 컨테이너 상태
ssh user@server "cd /opt/ecommerce && docker compose -f docker-compose.prod.yml ps"

# 로그 확인
ssh user@server "cd /opt/ecommerce && docker compose -f docker-compose.prod.yml logs app --tail=50"

# ES 상태
curl http://your-domain.com:9200/_cluster/health

# Consumer Group LAG
ssh user@server 'docker compose -f /opt/ecommerce/docker-compose.prod.yml exec -T kafka kafka-consumer-groups --bootstrap-server kafka:9092 --group ecommerce-consumer-group --describe'
```

### 5.4 엔드투엔드 테스트
```bash
# 1. 상품 생성 (로그인 후)
curl -X POST https://your-domain.com/api/v1/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"name":"테스트 상품","price":10000}'

# 2. ES 인덱싱 확인
curl https://your-domain.com/api/v1/search/products

# 3. 주문 생성 → Kafka 파이프라인 동작 확인
```

---

## Phase 6: 모니터링 및 운영 체계 구성 (Code mode + 직접 실행)

### 6.1 헬스 체크 스크립트 (`/opt/ecommerce/healthcheck.sh`)
```bash
#!/bin/bash
cd /opt/ecommerce
echo "=== Container Status ==="
docker compose ps
echo "=== App Health ==="
curl -sf http://localhost:8000/api/v1/health && echo " OK" || echo " FAIL"
echo "=== Elasticsearch ==="
curl -sf http://localhost:9200/_cluster/health | python3 -m json.tool
```

### 6.2 크론탭 등록 (10분마다)
```bash
*/10 * * * * /opt/ecommerce/healthcheck.sh >> /var/log/ecommerce-health.log 2>&1
```

### 6.3 (선택) Slack 알림 추가
- `deploy.yml`에 `slackapi/slack-github-action` 추가
- `SLACK_WEBHOOK_URL` GitHub Secret 등록

### 6.4 (선택) Sentry APM 연동
- `sentry-sdk` 패키지 추가
- FastAPI middleware 설정
- `SENTRY_DSN` 환경 변수 추가

---

## 의사 결정 사항

| 항목 | 결정 | 이유 |
|------|------|------|
| Docker Registry | **GitHub Container Registry (GHCR)** | GitHub Token만으로 사용 가능, 추가 계정 불필요 |
| DB 마이그레이션 | **초기: AUTO_CREATE_TABLES=true** | 현재 시스템이 이 방식에 최적화됨 |
| | **장기: SQL 마이그레이션 도입** | 변경 이력 관리 필요시 |
| 무중단 배포 | **초기: 기존 컨테이너 교체 (down-time 5~10초)** | Blue/Green은 복잡도 대비 효과 미미 |
| | **장기: docker-compose replicas=2** | 트래픽 증가시 |
| SSL 인증서 | **Let's Encrypt (certbot)** | 무료, 자동 갱신 가능 |
| 환경 변수 | **서버 내 `.env.production` 파일** | GitHub Secrets에 넣기엔 항목이 너무 많음 |

---

## 파일 생성 목록 요약 (Code mode 수행)

| # | 파일 | 설명 |
|---|------|------|
| 1 | `.gitignore` | Python + Docker gitignore |
| 2 | `.github/workflows/ci.yml` | CI 파이프라인 |
| 3 | `.github/workflows/deploy.yml` | CD 파이프라인 |
| 4 | `docker-compose.prod.yml` | 프로덕션 Docker Compose |
| 5 | `nginx/default.conf` | Nginx Reverse Proxy 설정 |
| 6 | `migrations/001_init.sql` | 초기 DB 스키마 |
| 7 | (선택) `README.md` | 프로젝트 문서 |
| 8 | (선택) `ssl/README.md` | SSL 인증서 안내 |
