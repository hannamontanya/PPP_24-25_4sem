from celery import Celery
import redislite

# Spin up a redis server, backed with an rdb file at /tmp/redis_example.rdb
RDB_PATH = '/tmp/redis_example.rdb'
redis_connection =  redislite.Redis(RDB_PATH)

# The celery broker string to use our redislite server
CELERY_BROKER = 'redis+socket://' + redis_connection.socket_file

celapp = Celery('tasks', backend=CELERY_BROKER, broker=CELERY_BROKER)
celapp.conf.imports = [
    'app.services.tasks',
]