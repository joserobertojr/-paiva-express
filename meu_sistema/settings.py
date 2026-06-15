"""
Configurações do projeto Paiva / Boss Barbearia.
Suporta desenvolvimento local (SQLite) e produção (PostgreSQL, WhiteNoise, Gunicorn).
Variáveis sensíveis são lidas do arquivo .env via python-decouple.
"""
from pathlib import Path
from decouple import config, Csv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# ─────────────────────────────────────────────────────────────
# SEGURANÇA — lidos do .env em produção
# ─────────────────────────────────────────────────────────────
SECRET_KEY = config('SECRET_KEY', default='django-insecure-k16nu_vzwy)0(ax#q$o$^2!q908ae8rb0lkkfeg4!%79nzb6oj')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# ─────────────────────────────────────────────────────────────
# APPS
# ─────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rh',
    'barbearia',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',       # ← WhiteNoise logo após SecurityMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'meu_sistema.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'barbearia.context_processors.notificacoes_barbearia',
            ],
        },
    },
]

WSGI_APPLICATION = 'meu_sistema.wsgi.application'

# ─────────────────────────────────────────────────────────────
# BANCO DE DADOS
# Em produção: DATABASE_URL=postgres://user:pwd@host:5432/db
# Em dev local: SQLite (padrão abaixo)
# ─────────────────────────────────────────────────────────────
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

# ─────────────────────────────────────────────────────────────
# AUTENTICAÇÃO
# ─────────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_REDIRECT_URL = 'hub'
LOGOUT_REDIRECT_URL = 'hub'
LOGIN_URL = 'login'

# ─────────────────────────────────────────────────────────────
# INTERNACIONALIZAÇÃO
# ─────────────────────────────────────────────────────────────
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# ─────────────────────────────────────────────────────────────
# ARQUIVOS ESTÁTICOS — WhiteNoise serve os estáticos em produção
# sem precisar de Nginx/CDN para projetos pequenos.
# ─────────────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'          # onde collectstatic deposita os arquivos
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ─────────────────────────────────────────────────────────────
# MEDIA (uploads de usuário)
# ─────────────────────────────────────────────────────────────
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ─────────────────────────────────────────────────────────────
# SEGURANÇA ADICIONAL — ativadas automaticamente quando DEBUG=False
# ─────────────────────────────────────────────────────────────
if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000          # 1 ano de HSTS
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True              # Redireciona HTTP → HTTPS
    SESSION_COOKIE_SECURE = True            # Cookie de sessão só via HTTPS
    CSRF_COOKIE_SECURE = True               # Cookie CSRF só via HTTPS
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─────────────────────────────────────────────────────────────
# BOSS BARBEARIA — contato
# ─────────────────────────────────────────────────────────────
BARBEARIA_WHATSAPP = config('BARBEARIA_WHATSAPP', default='5583999999999')  # formato: 55DDD9XXXXXXXX
