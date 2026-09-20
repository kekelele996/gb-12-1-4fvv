"""本地/测试用设置：用 SQLite 替代 PostgreSQL，关闭外部存储依赖。

用法：DJANGO_SETTINGS_MODULE=config.settings_local
"""
from .settings import *  # noqa: F401,F403

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_db.sqlite3',  # noqa: F405
    }
}

# 本地测试邮件落内存即可
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
