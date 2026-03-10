from celery import shared_task
from django.conf import settings
from celery import shared_task
import structlog
log = structlog.get_logger()


@shared_task(name="g3_worker")
def g3_worker(config):
    log.info('Running g3_worker...')


################################################################################
# Periodic tasks
#
class QueryRawData():

    @property
    def task_name(self):
        return "Query raw data"

    @property
    def task_handle(self):
        return self.task_func

    @property
    def task_frequency_seconds(self):
        return settings.QUERY_RAW_DATA_INTERVAL

    @property
    def task_initially_enabled(self):
        return True

    def __init__(self, task_func='') -> None:
        self.task_func = task_func

    def run_task(self):
        log.info(f'Running periodic task "{self.task_name}"...')


@shared_task()
def query_raw_data():
    QueryRawData().run_task()


periodic_tasks = [
    QueryRawData(task_func='query_raw_data'),
]
