# Point Shower — Operations Platform

> 환자 맞춤 구강 케어 트레이의 디자인부터 생산·정산까지 전체 운영을 통합한 플랫폼.

## 구성

- **랜딩 / 운영 허브** — `/`
- **ERP 콘솔** — `/erp.html` (4-역할: 치과 / 기공소 / 그래피 / 관리자)
- **환자용 브로셔** — `/point-shower-patient.html`
- **환자 포털** — `/erp-portal.html`
- **3D 조립 모드 (STL Viewer)** — `/point-shower/stl_viewer.html`
- **시연 점검** — `/DEMO_CHECKLIST.html`
- **운영 문서 뷰어** — `/docs.html`
- **커뮤니티** — `/point-shower-community/`

## 기술 스택

- **백엔드**: Django 5.1 (정적 파일 서빙 전용, DB 없음)
- **정적 파일**: WhiteNoise (압축 + 캐시)
- **WSGI**: gunicorn
- **3D**: Three.js + STLLoader (CDN)
- **폰트**: Pretendard Variable
- **배포**: Railway (Nixpacks)

## 로컬 개발

```bash
# 1. 가상환경
python3 -m venv .venv
source .venv/bin/activate

# 2. 의존성
pip install -r requirements.txt

# 3. 환경변수
cp .env.example .env
# .env 편집하여 DJANGO_SECRET_KEY 설정

# 4. 정적 자산 수집
python manage.py collectstatic --noinput

# 5. 개발 서버
python manage.py runserver 0.0.0.0:8000
```

브라우저: http://localhost:8000

## 프로덕션 빌드 (로컬 검증)

```bash
DJANGO_DEBUG=False python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2
```

## Railway 배포

이 프로젝트는 Railway 에 자동 배포되도록 구성되어 있습니다.

```bash
# 최초 1회
railway login
railway link  # 또는 railway init

# 배포
git push  # GitHub 연동 시 자동
# 또는
railway up
```

설정해야 할 환경변수 (Railway dashboard):

- `DJANGO_SECRET_KEY` — `python -c "import secrets; print(secrets.token_urlsafe(50))"` 결과
- `DJANGO_DEBUG` — `False`

## 디렉토리 구조

```
pointshower/
├── manage.py
├── config/                # Django 프로젝트
│   ├── settings.py        # WhiteNoise + 보안 헤더 + Railway 호환
│   ├── urls.py            # /healthz 헬스체크
│   ├── wsgi.py
│   └── asgi.py
├── public/                # 정적 자산 (WhiteNoise 가 root 에서 서빙)
│   ├── index.html
│   ├── erp.html           # 메인 ERP (203KB)
│   ├── point-shower-patient.html
│   ├── ... (16+ HTML)
│   ├── assets/
│   │   └── design-system.css
│   ├── samples/           # STL 샘플 8종 + 인라인 데이터
│   ├── point-shower-community/
│   └── point-shower/      # 3D 조립 viewer
├── requirements.txt
├── Procfile
├── railway.json
├── runtime.txt
└── README.md
```

## 헬스체크

Railway 가 사용하는 endpoint: `GET /healthz` → `{"status":"ok","service":"pointshower"}`

## 라이선스

© 2026 Point Shower × Graphy. All rights reserved.
