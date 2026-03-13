from django.core.management.base import BaseCommand
import structlog
log = structlog.get_logger()
from project.models import DataFile


class Command(BaseCommand):
    help = "Reset failed tasks"

    def handle(self, *args, **options):
        show_all()
        reset_failed()


def show_all():
    log.info('''Show all DataFile objects:''')
    for df in DataFile.objects.all():
        log.info(f'''status: {df.status}, path: {df.object_key}''')

    qs = DataFile.objects.filter(status=DataFile.Status.QUEUED)
    # for df in qs:
    #     log.info(f'''status: {df.status}, path: {df.object_key}''')
    log.info(f'''Number of queued files: {len(qs)}''')

    qs = DataFile.objects.filter(status=DataFile.Status.PROCESSING)
    # for df in qs:
    #     log.info(f'''status: {df.status}, path: {df.object_key}''')
    log.info(f'''Number of files processing: {len(qs)}''')

    qs = DataFile.objects.filter(status=DataFile.Status.COMPLETE)
    # for df in qs:
    #     log.info(f'''status: {df.status}, path: {df.object_key}''')
    log.info(f'''Number of completed files: {len(qs)}''')


def reset_failed():
    qs = DataFile.objects.filter(status=DataFile.Status.FAILED)
    for df in qs:
        # log.info(f'''status: {df.status}, path: {df.object_key}''')
        log.warning(f'''"{df.object_key}" has failed. Reseting status to QUEUED.''')
        df.status = DataFile.Status.QUEUED
        df.save()
    log.info(f'''Number of failed files: {len(qs)}''')
