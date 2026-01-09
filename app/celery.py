from app import create_app
from app.extensions import celery
from app.celery_utils import init_celery

app = create_app()
init_celery(celery, app)
