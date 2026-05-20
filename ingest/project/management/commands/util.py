"""
This module contains functions designed to be invoked as arguments to the `dev`
custom Django management command. See the `dev.py` module docstring for usage instructions.
"""
import structlog
log = structlog.get_logger()
from project.models import DataFile
from tasks.tasks import query_raw_data


def run_ingest():
    # Test the periodic task that discovers and processes new raw data files
    query_raw_data.delay()


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


def reset_failed(include_processing=False):
    show_all()
    if include_processing:
        qs = DataFile.objects.filter(status__in=[DataFile.Status.FAILED, DataFile.Status.PROCESSING])
    else:
        qs = DataFile.objects.filter(status=DataFile.Status.FAILED)
    for df in qs:
        # log.info(f'''status: {df.status}, path: {df.object_key}''')
        log.warning(f'''Reseting status of "{df.object_key}" to QUEUED.''')
        df.status = DataFile.Status.QUEUED
        df.save()
    log.info(f'''Number of reset files: {len(qs)}''')


def s3_test():
    from project.object_store import ObjectStore
    s3 = ObjectStore()
    test_filepath = '/tmp/testfile'
    # with open(test_filepath, 'w') as fp:
    #     fp.write('Testing S3 multipart upload.')
    test_key = 'test/testfile'
    s3.download_object(
        path='incoming/282023912_90GHz_tonly.g3.gz',
        file_path=test_filepath,
    )
    s3.put_object(
        file_path=test_filepath,
        path=test_key,
    )
