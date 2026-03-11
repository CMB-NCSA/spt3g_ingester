# SPT3G raw data ingest service

This repo contains the source code and deployment configuration for the automated SPT3G raw data ingestion service. The application is designed to be run by Kubernetes and leverages the Django framework and Celery task queue system to asynchronously and concurrently run data processing jobs.

Raw data from the South Pole Telescope (SPT) is periodically and manually uploaded to an S3-compatible object storage bucket. This raw data repo is periodically polled by a Celery Beat task, launching jobs to convert new raw data files to FITS format.

When an incoming file has been processed, it is moved from `/incoming` to `/processed`.

## Local development

To run the application in Docker Compose, run

```bash
docker compose -f container/docker-compose.yaml up -d --build
```

To completely destroy the deployment and all persistent data, run

```bash
docker compose -f container/docker-compose.yaml down --remove-orphans --volumes
```

A convenient method for efficient code iteration is to write and invoke test functions in `ingest/project/management/commands/test.py` that can be executed within the running Django environment like so:

```bash
docker exec -it spt3g-ingest-celery-beat-1 python manage.py test 
```
