from django.db import models
from django.utils.translation import gettext_lazy as _
from uuid import uuid4
import structlog
log = structlog.get_logger()


class DataFile(models.Model):
    class Status(models.TextChoices):
        QUEUED = 'QUEUED', _('queued')
        PROCESSING = 'PROCESSING', _('processing')
        COMPLETE = 'COMPLETE', _('complete')
        FAILED = 'FAILED', _('failed')

    def __str__(self):
        return (f'object_key: {self.object_key}, '
                f'status: {self.status}')

    # Internal UUID
    uuid = models.UUIDField(
        default=uuid4,
        unique=True,
        db_index=True,
        primary_key=True
    )
    status = models.TextField(
        choices=Status.choices,
        default=Status.QUEUED,
        null=False,
    )
    object_key = models.TextField(null=False, blank=False)
    time_ingested = models.DateTimeField(auto_now_add=True, verbose_name='Time ingested')
    time_processed = models.DateTimeField(auto_now=True, verbose_name='Time processed')
    error_msg = models.TextField(null=False, blank=False, default='')
