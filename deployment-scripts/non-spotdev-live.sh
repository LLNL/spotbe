#!/bin/bash

echo -e "Test live template notebooks with known data and non spotdev user..."
CALI_DIR=/usr/gapps/spot/datasets/lulesh_new
CALI_FILE=${CALI_DIR}/190716-140428166192.cali

# Test live single jupyter notebook.
./test-hatchet-template-notebook.sh \
    live \
    ${CALI_FILE}
ERR=$?
if [ ${ERR} -eq 1 ]; then
    exit 1
fi

# Test live multi jupyter notebook.
./test-multi-hatchet-template-notebook.sh \
    live \
    ${CALI_DIR}
ERR=$?
if [ ${ERR} -eq 1 ]; then
    exit 1
fi

#
