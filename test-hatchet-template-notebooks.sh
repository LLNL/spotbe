#!/bin/bash

if [ $# -ne 1 ]; then
    echo "Usage: $0 <cali-file>"
    exit 1
fi

CALI_FILE=$1

# run spot.py to update variables in template notebook
JUPYTER_NB=$(./spot.py --ci_testing jupyter ${CALI_FILE})
OUTFILE=$(echo ${JUPYTER_NB} | rev | cut -d "." -f 2- | rev).nbconvert.ipynb

echo -e "CI Testing for Jupyter:"
echo -e "    Input Jupyter Notebook:"
echo -e "        ${JUPYTER_NB}"
echo -e "    Output Jupyter Notebook:"
echo -e "        ${OUTFILE}"
echo -e "    Cali File:"
echo -e "        ${CALI_FILE}"

# run notebook programmatically from command line
jupyter nbconvert \
    --to notebook \
    --execute \
    --ExecutePreprocessor.timeout=60 \
    ${JUPYTER_NB}

err=$?
if [ ${err} -eq 0 ]; then
    echo -e "SUCCESS $0"
else
    echo -e "FAILURE $0"
fi

#
