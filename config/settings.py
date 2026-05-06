"""
FixOn — Django settings (production-ready static site).

이 프로젝트는 정적 HTML/CSS/JS/STL 자산을 Django + WhiteNoise 로 서빙합니다.
DB / admin / auth 등은 사용하지 않습니다.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# Core
# ============================================================
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "fixon-dev-only-replace-in-production-with-50chars-random-key!!",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() == "true"

# Railway 자동 도메인 + 사용자 지정 도메인 모두 허용
ALLOWED_HOSTS = ["*"]

# Railway 의 *.up.railway.app 와 사용자 도메인을 CSRF Trusted 로 등록
CSRF_TRUSTED_ORIGINS = [
    "https://*.up.railway.app",
    "https://*.railway.app",
]
_extra_origin = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
if _extra_origin:
    CSRF_TRUSTED_ORIGINS.append(f"https://{_extra_origin}")

# ============================================================
# Apps & Middleware
# ============================================================
INSTALLED_APPS = [
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise 는 SecurityMiddleware 바로 다음에 위치해야 합니다
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": []},
    },
]

# ============================================================
# Static files
# ----
# Django 내부 static (관리되는 STATIC_URL=/static/ 경로) 와
# 정적 사이트 컨텐츠 (public/ 의 모든 HTML/CSS/JS/STL — 루트 URL 에 직접 서빙)
# 두 가지를 분리합니다. 후자는 WhiteNoise 의 WHITENOISE_ROOT 기능을 사용합니다.
# ============================================================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# WhiteNoise 가 public/ 디렉토리를 루트 URL 에서 서빙 (index.html 자동 포함)
WHITENOISE_ROOT = BASE_DIR / "public"
WHITENOISE_INDEX_FILE = True
WHITENOISE_AUTOREFRESH = DEBUG
WHITENOISE_USE_FINDERS = DEBUG
WHITENOISE_MIMETYPES = {
    ".webmanifest": "application/manifest+json",
    ".stl": "model/stl",
    ".stp": "model/step",
    ".step": "model/step",
}

# 압축 + immutable cache
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

# ============================================================
# Misc
# ============================================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

# Security headers (Railway terminates TLS, mark requests secure via X-Forwarded-Proto)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "SAMEORIGIN"

# Logging — Railway 콘솔로 stdout
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
