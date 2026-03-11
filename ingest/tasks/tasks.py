from celery import shared_task
from django.conf import settings
from celery import shared_task
from spt3g_ingest.ingstools import g3worker
from project.models import DataFile
from project.object_store import ObjectStore
import os
from time import sleep
import structlog
log = structlog.get_logger()


@shared_task(name="g3_worker")
def g3_worker(uuid):
    log.info(f'''Querying job "{uuid}"...''')
    df = DataFile.objects.get(uuid=uuid)
    # Set status to processing
    df.status = DataFile.Status.PROCESSING
    df.save()
    s3 = ObjectStore()
    log.info(f'''Launching ingest job for "{df.object_key}" ("{df.status}")...''')
    try:
        # TODO: ensure this file path is unique
        local_file_path = f'/data/raw/{df.object_key}'
        s3.download_object(
            path=os.path.join(
                settings.S3_CONFIG['base_path'],
                df.object_key.strip('/'),
            ),
            file_path=local_file_path,
        )
        assert os.path.exists(local_file_path)
        infile_list_path = os.path.join('/tmp', os.path.basename(local_file_path))
        with open(infile_list_path, 'w') as infile_list:
            infile_list.writelines([local_file_path])
        g3w = g3worker(**{
            'files': [infile_list_path],
            'outdir': '/data/fits',
            'clobber': False,
            'compress': 'GZIP_2',
            'filter_transient': True,
            'filter_transient_coadd': False,
            'passthrough': False,
            'coadds': None,
            'preload_coadds': False,
            'band': ["90GHz", "150GHz", "220GHz"],
            'polarized': False,
            'compute_snr_annulus': False,
            'mask_filter': False,
            'field_name': None,
            'ignore_season': None,
            'ingest': False,
            'replace': False,
            'tablename': 'g3fileinfo',
            'dbname': '/dummy/dblib/spt3g_archive.db',
            'stage': False,
            'stage_path': None,
            'indirect_write': False,
            'indirect_write_path': None,
            'output_filetypes': ['FITS'],
            'loglevel': 'INFO',
            'log_format_date': '%Y-%m-%d %H:%M:%S',
            'log_format': '[%(asctime)s.%(msecs)03d][%(levelname)s][%(name)s][%(funcName)s] %(message)s',
            'run_dbname': '/dummy/dblib/spt3g_runs.db',
            'run_tablename': 'g3runinfo',
            'run_check': False,
            'run_insert': False,
            'np': 1,
            'ntheads': 1,
        })
        g3w.run_files()
        # Set status to complete
        df.status = DataFile.Status.COMPLETE
        df.save()
    except Exception as err:
        log.error(f'Error processing file: {err}')
        df.status = DataFile.Status.FAILED
        df.save()
    finally:
        try:
            os.remove(infile_list_path)
            os.remove(local_file_path)
        except FileNotFoundError:
            pass


def scan_incoming():
    from project.object_store import ObjectStore
    s3 = ObjectStore()
    object_keys = s3.list_directory('incoming')
    # log.info(json.dumps(object_keys, indent=2))
    dfs = DataFile.objects.all()
    for object_key in object_keys:
        if not dfs.filter(object_key=object_key).exists():
            log.info(f'Creating new DataFile object for "{object_key}"')
            DataFile.objects.create(object_key=object_key)


def view_files():
    log.info('''Show all DataFile objects:''')
    for df in DataFile.objects.all():
        log.info(f'''status: {df.status}, path: {df.object_key}''')


def launch_jobs():
    for df in DataFile.objects.filter(status=DataFile.Status.QUEUED):
        g3_worker.delay(df.uuid)
        # Artificially reduce job launch rate for testing purposes
        sleep(1)


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
        scan_incoming()
        view_files()
        launch_jobs()


@shared_task()
def query_raw_data():
    QueryRawData().run_task()


periodic_tasks = [
    QueryRawData(task_func='query_raw_data'),
]
