from django.apps import AppConfig

class MessagesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'messages'
    label = 'station_messages'
    verbose_name = '站内消息'
