from celery import Celery

celery_app = Celery(
    'app.celery.celery_app',
    broker='amqp://guest:guest@localhost:5672//')

from app.celery import tasks