###############################################################################
FROM python:3.13 AS deps

# Install MinIO CLI client
RUN curl https://dl.min.io/client/mc/release/linux-amd64/mc \
    -o /usr/local/bin/mc && \
    chmod +x /usr/local/bin/mc

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -yq \
        cmake \
        libz-dev \
        libbz2-dev \
        liblzma-dev \
        libflac-dev \
        libnetcdf-dev \
        libfftw3-dev \
        libgsl0-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    hdf5tools \
    scipy \
    h5py

ARG SPT3G_SOFTWARE_PARALLELISM="4"
ARG SPT3G_SOFTWARE_REF="8f48ad2"
COPY src/spt3g_software.${SPT3G_SOFTWARE_REF} /opt/spt/spt3g_software
WORKDIR /opt/spt/spt3g_software
RUN CMAKE_BUILD_PARALLEL_LEVEL=$SPT3G_SOFTWARE_PARALLELISM pip install -v .

# Install spt3g_ingest
ARG SPT3G_INGEST_REF="6d1558b"
RUN git clone https://github.com/CMB-NCSA/spt3g_ingest.git /opt/spt/spt3g_ingest \
    && cd /opt/spt/spt3g_ingest \
    && git checkout $SPT3G_INGEST_REF \
    && pip install .

# TODO: Move up to consolidate with previous pip install when list is finalized
RUN pip install --no-cache-dir \
    "django>=6.0,<6.1" \
    django_celery_results \
    django-celery-beat \
    flower \
    psycopg[binary] \
    structlog \
    valkey \
    watchdog

RUN pip install --no-cache-dir \
    redis

# Create non-root user
ARG UID=1000
ARG USERNAME=spt
ARG APP_ROOT_DIR=/opt
RUN useradd --create-home --shell /bin/bash ${USERNAME} --uid ${UID}

## Create application base directory
RUN mkdir -p ${APP_ROOT_DIR} && chown ${UID} -R ${APP_ROOT_DIR}
USER ${USERNAME}

# Install MinIO client config
WORKDIR /home/${USERNAME}
RUN mkdir .mc
COPY container/mc/config.json /root/.mc/config.json

COPY --chown=${USERNAME}:${USERNAME} ./ingest ${APP_ROOT_DIR}/ingest
WORKDIR ${APP_ROOT_DIR}/ingest
