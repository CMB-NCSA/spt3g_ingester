from django.core.management.base import BaseCommand
import structlog
from tasks.tasks import query_raw_data
log = structlog.get_logger()


class Command(BaseCommand):
    help = "Test script"

    def handle(self, *args, **options):
        query_raw_data.delay()
