# SPT3G raw data ingest service

This repo contains the source code and deployment configuration for the automated SPT3G raw data ingestion service. The application is designed to be run by Kubernetes and leverages the Django framework and Celery task queue system to asynchronously and concurrently run data processing jobs.

Raw data from the South Pole Telescope (SPT) is periodically and manually uploaded to an S3-compatible object storage bucket. This raw data repo is periodically polled by a Celery Beat task, launching jobs to convert new raw data files to FITS format.

When an incoming file has been processed, it is moved from `/incoming` to `/processed`.

## Local development

### Application deployment control

To run the application in Docker Compose, run

```bash
docker compose -f container/docker-compose.yaml up -d --build
```

To completely destroy the deployment and all persistent data, run

```bash
docker compose -f container/docker-compose.yaml down --remove-orphans --volumes
```

### Configuration option overrides

Configuration options are primarily set by environment variables. These should be overridden in a `container/.env` file. Secrets such as object storage system credentials should also be defined in that file.

⚠️ By default, Celery Beat launches in a "suspended" state to prevent periodic tasks from automatically spawning workloads. Set `SUSPEND_CELERY_BEAT=false` to enable Celery Beat to trigger periodic tasks.

### Code development

A convenient method for efficient code iteration is to write and invoke test functions in `ingest/project/management/commands/test.py` that can be executed within the running Django environment like so:

```bash
docker exec -it spt3g-ingest-celery-beat-1 python manage.py test 
```

### Resource limits

Depending on your computing resources, you may want to adjust the Celery worker concurrency and resource limits to avoid crashing your development machine or having Celery workers killed when exceeding limits. Override the default values in a `container/.env` file similar to this example:

```bash
CELERY_WORKER_LIMIT_CPUS = 8.0
CELERY_WORKER_LIMIT_MEMORY = 16G
CELERY_CONCURRENCY = 4
```

### Migrations

After modifying a Django model, generate a migration script by setting the environment variable `MAKE_MIGRATIONS=true` and starting the Celery Beat service:

```bash
docker compose -f container/docker-compose.yaml up -d --build celery-beat
```

After the script is generated, reset the `MAKE_MIGRATIONS` to false and restart the full application.
