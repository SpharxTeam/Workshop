# CVAT 自定义配置
import os

# 基础配置
DEBUG = False
ALLOWED_HOSTS = ['*']

# 数据库配置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': os.environ.get('CVAT_POSTGRES_HOST', 'cvat_db'),
        'PORT': os.environ.get('CVAT_POSTGRES_PORT', '5432'),
        'NAME': os.environ.get('CVAT_POSTGRES_DBNAME', 'cvat'),
        'USER': os.environ.get('CVAT_POSTGRES_USER', 'root'),
        'PASSWORD': os.environ.get('CVAT_POSTGRES_PASSWORD', ''),
    }
}

# Redis配置
REDIS_HOST = os.environ.get('CVAT_REDIS_HOST', 'cvat_redis')
REDIS_PORT = os.environ.get('CVAT_REDIS_PORT', '6379')

# 媒体文件配置
MEDIA_DATA_ROOT = '/home/django/data'
MEDIA_SHARE_ROOT = '/home/django/share'
MEDIA_ROOT = MEDIA_DATA_ROOT
MEDIA_URL = '/data/'

# 日志配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '[%(asctime)s] %(levelname)s %(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'cvat': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Spharx特有配置
SPHARX_CONFIG = {
    'auto_annotation_enabled': True,
    'default_confidence_threshold': 0.8,
    'supported_categories': ['furniture', 'vehicle', 'electronic'],
    'export_formats': ['coco', 'yolo', 'voc'],
}