FROM python:3.13

ENV PYTHONUNBUFFERED=1
ENV PROJECT_ROOT="/data/app/note_drf"
ENV LOG_DIR="${PROJECT_ROOT}/logs"

# 작업 디렉토리 설정
WORKDIR ${PROJECT_ROOT}

# 애플리케이션 소스 코드 복사
COPY . ${PROJECT_ROOT}

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt update && apt install -y \
    nginx \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Nginx 설정 복사
COPY ./nginx/nginx.conf /etc/nginx/nginx.conf

# 인증서 파일 복사
COPY ./cert/cert.pem /etc/cert/cert.pem
COPY ./cert/privkey.pem /etc/cert/privkey.pem

# 구동 커맨드 실행
RUN chmod +x ./run.sh
CMD ["./run.sh"]
