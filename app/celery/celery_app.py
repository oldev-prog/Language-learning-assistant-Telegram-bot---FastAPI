from celery import Celery

celery_app = Celery(
    'app.background_tasks.celery.celery_app',
    broker='amqp://guest:guest@localhost:5672//',
    backend='redis://localhost:6379/0',)

