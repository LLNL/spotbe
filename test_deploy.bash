!/bin/bash

echo -e "Test dev template notebooks with known data and current user..."
CALI_DIR=/usr/gapps/spot/datasets/lulesh_new
CALI_FILE=${CALI_DIR}/190716-140428166192.cali

# Test dev single jupyter notebook.
./deployment-scripts/test-hatchet-template-notebook.sh \
    dev \
    ${CALI_FILE}
ERR=$?
if [ ${ERR} -eq 1 ]; then
    exit 1
fi

# Test dev multi jupyter notebook.
./deployment-scripts/test-multi-hatchet-template-notebook.sh \
    dev \
    ${CALI_DIR}
ERR=$?
if [ ${ERR} -eq 1 ]; then
    exit 1
fi

