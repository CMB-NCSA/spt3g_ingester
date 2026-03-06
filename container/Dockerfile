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

# TODO: Reference SPT3G_SOFTWARE_REF
# ARG SPT3G_SOFTWARE_REF=8f48ad262
COPY src/spt3g_software.8f48ad262 /opt/spt/spt3g_software
WORKDIR /opt/spt/spt3g_software
RUN CMAKE_BUILD_PARALLEL_LEVEL=12 pip install -v .

# Install spt3g_ingest
COPY src/spt3g_ingest /opt/spt/spt3g_ingest
WORKDIR /opt/spt/spt3g_ingest
RUN pip install .

# Create non-root user
ARG UID=1000
ARG USERNAME=spt
RUN useradd --create-home --shell /bin/bash ${USERNAME} --uid ${UID}
USER ${USERNAME}
WORKDIR /home/spt

# Install MinIO client config
RUN mkdir .mc
COPY container/mc/config.json /root/.mc/config.json
