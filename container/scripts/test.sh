#!/bin/bash

set -euo pipefail

cd "$(dirname "$(readlink -f "$0")")"

DATA_FILE="282023912_90GHz_tonly.g3.gz"
DATA_DIR="data/raw/2025/2025-12"
OUT_FILEPATH="2025/2025-12/282023912_90GHz_tonly_fltd.fits"

OUTDIR_ROOT="data/fits"
mkdir -p ${DATA_DIR}
mkdir -p ${OUTDIR_ROOT}

if [[ ! -f "${DATA_DIR}/${DATA_FILE}" ]]; then
  echo "Downloading raw data file..."
  mc cp taiga-spt3g/testbucket/incoming/${DATA_FILE} ${DATA_DIR}/
else
  echo "Input file \"${DATA_DIR}/${DATA_FILE}\" already exists."
fi
if [[ ! -f "${DATA_DIR}/${DATA_FILE}" ]]; then
  echo "Error downloading raw data file. Aborting..."
  exit 1
fi
if [[ ! -f "${OUTDIR_ROOT}/${OUT_FILEPATH}" ]]; then
  echo "Running g3_worker..."
  g3_worker ${DATA_DIR}/${DATA_FILE} \
    --outdir ${OUTDIR_ROOT} \
    --filter_transient \
    --np 8
  #   --indirect_write \
  #   --indirect_write_path /dev/shm \
else
  echo "Output file \"${OUTDIR_ROOT}/${OUT_FILEPATH}\" already exists."
fi

if [[ -f "${OUTDIR_ROOT}/${OUT_FILEPATH}" ]]; then
  echo "Test passed."
else
  echo "Test failed."
fi
