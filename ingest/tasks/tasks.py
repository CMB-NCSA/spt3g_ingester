import structlog
import os
from time import sleep
from django.conf import settings
from celery import shared_task
from celery import shared_task
from spt3g_ingest.ingstools import g3worker
from spt3g_ingest.ingstools import FILETYPE_SUFFIX
from project.models import DataFile
from project.object_store import ObjectStore
log = structlog.get_logger()


@shared_task(name="g3_worker")
def g3_worker(uuid):
    log.info(f'''Querying DataFile object "{uuid}"...''')
    df = DataFile.objects.get(uuid=uuid)
    # Set status to processing
    df.status = DataFile.Status.PROCESSING
    df.save()
    s3 = ObjectStore()
    log.info(f'''Launching ingest job for "{df.object_key}" ("{df.status}")...''')
    local_raw_filepath = f'/tmp/raw/{df.object_key}'
    try:
        infile_list_path = os.path.join('/tmp', os.path.basename(local_raw_filepath))
        with open(infile_list_path, 'w') as infile_list:
            infile_list.writelines([local_raw_filepath])
        config = {
            'files': [infile_list_path],
            'outdir': '/tmp/fits',
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
            'loglevel': 'DEBUG',
            'log_format_date': '%Y-%m-%d %H:%M:%S',
            'log_format': '[%(asctime)s.%(msecs)03d][%(levelname)s][%(name)s][%(funcName)s] %(message)s',
            'run_dbname': '/dummy/dblib/spt3g_runs.db',
            'run_tablename': 'g3runinfo',
            'run_check': False,
            'run_insert': False,
            'np': 1,
            'ntheads': 1,
        }
        if not os.path.exists(local_raw_filepath):
            log.info(f'''Missing raw data file "{local_raw_filepath}". Downloading...''')
            s3.download_object(
                path=os.path.join(
                    settings.S3_CONFIG['base_path'],
                    df.object_key.strip('/'),
                ),
                file_path=local_raw_filepath,
            )
        assert os.path.exists(local_raw_filepath)
        g3w = g3worker(**config)
        # Generate the FITS output file path and destination object key
        g3w.precook_g3file(local_raw_filepath)
        fits_filepath = get_output_filepath(g3w, local_raw_filepath)
        fits_object_key = os.path.join(
            settings.S3_CONFIG['base_path'],
            fits_filepath.replace('/tmp/fits/', 'fits/'),
        )
        # If the object already exists, skip the processing
        if not s3.object_exists(path=fits_object_key):
            # If the FITS file already exists locally but was not uploaded for some reason,
            # skip processing and upload it.
            if not os.path.exists(fits_filepath):
                # raise Exception('artificial error')
                g3w.run_files()
            # Upload FITS file to S3 bucket
            s3.put_object(
                file_path=fits_filepath,
                path=fits_object_key.strip('/'),
            )
        # Set status to complete
        df.status = DataFile.Status.COMPLETE
        df.save()
    except Exception as err:
        log.error(f'Error processing file: {err}')
        df.status = DataFile.Status.FAILED
        df.save()
    finally:
        try:
            os.remove(local_raw_filepath)
            os.remove(fits_filepath)
            os.remove(infile_list_path)
        except FileNotFoundError:
            pass


def get_output_filepath(g3w, local_raw_filepath):
    if g3w.config.passthrough:
        suffix = FILETYPE_SUFFIX['passthrough']
    elif g3w.config.filter_transient:
        suffix = FILETYPE_SUFFIX['filtered']
    elif g3w.config.filter_transient_coadd:
        suffix = FILETYPE_SUFFIX['coaddfiltered']
    fits_filepath = g3w.set_outname(local_raw_filepath, suffix=suffix, filetype='FITS')
    log.debug(f'fits_filepath: {fits_filepath}')
    return fits_filepath


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
