# Note Backend

Django REST Framework(DRF) 기반의 풀스택 `note` 프로젝트에서 백엔드(BE) 역할을 담당하는 레포지토리입니다. 

## 🚀 Tech Stack

- **Framework**: Django 4.1, Django REST Framework
- **Database**: MySQL
- **Authentication**: JWT (JSON Web Token) via `djangorestframework-simplejwt`
- **Security**: AES-256-CBC 기반 중요 데이터(계좌번호, 시리얼, 노트 내용 등) 양방향 암복호화
- **Deployment**: Docker, Docker Compose, Nginx, Gunicorn

## 🎯 Key Features

- **사용자 관리 및 권한 (RBAC)**: 관리자(Admin)와 일반 사용자(User) 권한 분리
- **보안 데이터 관리**: AES 암호화를 적용한 안전한 데이터 저장 (`BankAccount`, `Note`, `Serial` 등)
- **감사 로그 (Audit Log)**: 시스템 내 주요 데이터 생성/수정/삭제 이벤트 및 사용자 로그인/관리 활동 자동 기록
- **API 기능**:
  - `Dashboard`: 주요 데이터 통계 제공
  - `BankAccount`: 암호화된 계좌번호 관리
  - `GuestBook`: 방명록 및 축의금 데이터 관리
  - `Note`: 암호화된 개인 노트 관리
  - `Serial`: 소프트웨어 시리얼 넘버 관리
  - `Lotto`: 로또 번호 자동 생성 유틸리티

---

## 🛠️ Getting Started (Local Development)

### 1. 패키지 설치
```bash
$ pip3 install -r requirements.txt
```

### 2. 환경 변수 설정
프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 다음 값을 채웁니다.
```env
SECRET_KEY=your_django_secret_key
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=your_db_port
AES_KEY=32_byte_hex_string_for_encryption
AES_KEY_IV=16_byte_hex_string_for_iv
```

### 3. 데이터베이스 마이그레이션
```bash
$ python3 manage.py makemigrations --settings=config.settings.development
$ python3 manage.py migrate --settings=config.settings.development
```

### 4. 초기 필수 데이터 로드 및 SuperUser 생성
```bash
# 기본 권한 데이터 로드
$ python3 manage.py loaddata api/data_auth.json --settings=config.settings.development

# 관리자 계정 생성
$ python3 manage.py createsuperuser --settings=config.settings.development
```

### 5. 로컬 서버 실행
```bash
$ python3 manage.py runserver --settings=config.settings.development
```

---

## 🐳 Docker Deployment

### 1. 인증서 준비
`cert/` 디렉토리에 Nginx용 SSL 인증서 파일을 배치합니다.
- `cert/cert.pem`
- `cert/privkey.pem`

### 2. 빌드 및 실행
```bash
$ docker-compose up -d --build
```
> 컨테이너 구동 시 `config.settings.production` 설정이 적용되며, 내장된 Nginx 및 Gunicorn을 통해 서비스됩니다.

---

## 💡 Utilities & Commands

**패키지 목록 백업**
```bash
$ pip3 freeze > requirements.txt
```

**권한 데이터 백업 (auth 앱 데이터 추출)**
```bash
$ python3 manage.py dumpdata auth -o api/data_auth.json --settings=config.settings.development
```
