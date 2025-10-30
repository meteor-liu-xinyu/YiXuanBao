from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# ⭐ 优先从环境变量读取配置文件路径
env_file_path = os.getenv('ENV_FILE')

if env_file_path:
    # Docker 或显式指定配置文件
    env_file = Path(env_file_path)
    load_dotenv(env_file)
    print(f"✅ 加载指定配置: {env_file}")
else:
    # 本地开发：默认加载 backend/.env
    env_file = BASE_DIR / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ 加载开发配置: {env_file}")
    else:
        print("⚠️ 未找到开发环境配置文件 backend/.env")

# ⭐ 自动检测环境类型
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')  # development, production, staging
IS_PRODUCTION = ENVIRONMENT == 'production'
IS_DEVELOPMENT = ENVIRONMENT == 'development'

print(f"🚀 当前运行环境: {ENVIRONMENT}")

# Security
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-fallback-key-change-in-production')

# ⭐ 根据环境自动设置 DEBUG
if IS_PRODUCTION:
    DEBUG = False
    print("⚙️ 生产模式: DEBUG=False")
else:
    DEBUG = os.getenv('DEBUG', 'True').lower() in ('1', 'true', 'yes')
    print(f"⚙️ 开发模式: DEBUG={DEBUG}")

# ⭐ ALLOWED_HOSTS 根据环境自动配置
if IS_DEVELOPMENT:
    ALLOWED_HOSTS = ['*']  # 开发环境允许所有
    print("⚙️ 开发模式: ALLOWED_HOSTS=['*']")
else:
    # 生产环境从环境变量读取
    _allowed = os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost')
    ALLOWED_HOSTS = [h.strip() for h in _allowed.split(',') if h.strip()]
    print(f"⚙️ 生产模式: ALLOWED_HOSTS={ALLOWED_HOSTS}")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    'rest_framework',
    'corsheaders',

    # my apps
    'accounts.apps.AccountsConfig',
    'hospital.apps.HospitalConfig',
    'recommend',
]

AUTH_USER_MODEL = 'accounts.User'

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"

# Database configuration from environment variables
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'yxbao_db'),
        'USER': os.getenv('DB_USER', 'meteor'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {'charset': 'utf8mb4'},
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "zh-hans"  # 改为中文
TIME_ZONE = "Asia/Shanghai"  # 改为中国时区
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',  # ⭐ 允许未认证用户访问
    )
}

# ⭐ CORS 配置 - 根据环境自动选择
if IS_DEVELOPMENT:
    # 开发环境：允许所有源
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOWED_ORIGINS = []
    print("⚙️ 开发模式: CORS_ALLOW_ALL_ORIGINS=True")
else:
    # 生产环境：只允许指定源
    CORS_ALLOW_ALL_ORIGINS = False
    _cors = os.getenv('CORS_ALLOWED_ORIGINS', 'http://8.137.164.174')
    CORS_ALLOWED_ORIGINS = [c.strip() for c in _cors.split(',') if c.strip()]
    print(f"⚙️ 生产模式: CORS_ALLOWED_ORIGINS={CORS_ALLOWED_ORIGINS}")

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# ⭐ CSRF 配置 - 根据环境自动选择
if IS_DEVELOPMENT:
    # 开发环境：宽松的 CSRF 设置
    CSRF_TRUSTED_ORIGINS = [
        'http://localhost:5173',
        'http://localhost:8080',
        'http://localhost',
        'http://127.0.0.1',
    ]
else:
    # 生产环境：从环境变量读取
    _csrf = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://8.137.164.174')
    CSRF_TRUSTED_ORIGINS = [u.strip() for u in _csrf.split(',') if u.strip()]

print(f"⚙️ CSRF_TRUSTED_ORIGINS={CSRF_TRUSTED_ORIGINS}")

# ⭐ Cookie 配置 - 根据环境自动选择
if IS_PRODUCTION:
    # 生产环境：安全的 Cookie 设置（如果使用 HTTPS）
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() in ('1', 'true', 'yes')
    CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'False').lower() in ('1', 'true', 'yes')
    SESSION_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = False  # JS 需要读取
else:
    # 开发环境：宽松的 Cookie 设置
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = False

CSRF_COOKIE_NAME = "csrftoken"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ⭐ 日志配置
if DEBUG:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
            },
        },
        'root': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    }