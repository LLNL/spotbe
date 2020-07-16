#!/bin/bash

user_in_spotdev()
{
    if id -nG $1 | grep -qw spotdev; then
        echo "Yes"
    else
        echo "No"
    fi
}

if [ $# -ne 1 ]; then
    echo "Usage: $0 <path-to-cali-dir>"
    exit 1
fi

CALI_DIR=$1
CALI_FILES=$(echo `ls ${CALI_DIR}`)

## run spot.py to update variables in multi template notebook
MULTI_JUPYTER_NB=$(./spot.py --ci_testing multi_jupyter ${CALI_DIR} "${CALI_FILES}")
OUTFILE=$(echo ${MULTI_JUPYTER_NB} | rev | cut -d "." -f 2- | rev).nbconvert.ipynb

echo -e "CI Testing for Multi Jupyter:"
echo -e "    Running As: ${USER}"
echo -e "    Member of spotdev?: $(user_in_spotdev ${USER})"
echo -e "    Input Multi Jupyter Notebook:"
echo -e "        ${MULTI_JUPYTER_NB}"
echo -e "    Output Multi Jupyter Notebook:"
echo -e "        ${OUTFILE}"
echo -e "    Directory of Cali Files:"
echo -e "        ${CALI_DIR}"

echo -e ""

# run notebook programmatically from command line
jupyter nbconvert \
    --to notebook \
    --execute \
    --ExecutePreprocessor.timeout=60 \
    --output ${OUTFILE} \
    ${MULTI_JUPYTER_NB}

err=$?

echo -e ""
if [ ${err} -eq 0 ]; then
    echo -e "SUCCESS $0"
else
    echo -e "FAILURE $0"
fi

#
