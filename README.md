# noteDRF
Django 풀스택으로 개발된 기존 note 프로젝트를 FE / BE 분리 구현

> 프로젝트 관련 패키지 설치
```
$ pip3 install -r requirements.txt
```

> Django 모델 -> 데이터베이스 마이그레이션
```
(venv)$ python3 manage.py makemigrations --settings=config.settings.development
(venv)$ python3 manage.py migrate --settings=config.settings.development
```

>프로젝트 구성을 위한 필수 DB 데이터 로드
```
(venv)$ python3 manage.py loaddata note/data_auth.json --settings=config.settings.development
```

> 프로젝트 SuperUser 생성
```
(venv)$ python3 manage.py creatsuperuser --settings=config.settings.development
```

> 개발 환경 실행 명령어
```
(venv)$ python3 manage.py runserver --settings=config.settings.development
```


> 패키지 목록 조회 방법
```
$ pip3 freeze > requirements.txt
```

> 프로젝트 구성을 위한 필수 DB 데이터 백업 방법
```
(venv)$ python3 manage.py dumpdata auth -o note/data_auth.json --settings=config.settings.development
```

> 데이터베이스 테이블 -> Django 모델 마이그레이션 방법
- 가급적이면 Django 모델 -> 데이터베이스 테이블 마이그레이션 방식을 추천
- DB에서 테이블을 생성/수정/삭제한 경우 models_tmp.py로 생성 후 models.py에 필요한 class를 추가
- Django Model에서 관리되기 위해서는 마이그레이션된 코드의 class Meta에서 managed = False 라인 삭제가 필요함
```
(venv)$ python3 manage.py inspectdb > note/models_tmp.py --settings=config.settings.development
```