#!/bin/bash

DIR=/usr/gapps/spot/
DEV=$DIR"dev/"
LIVE=$DIR"live/"
HATCHET=$LIVE"hatchet/"
CALIPER=$LIVE"caliper/"

##############################################################################
# Test spot dev single and multi jupyter notebooks with known cali data.
# Terminate deploy_spot.bash script if one of the notebooks fails. Fix bugs and
# re-test before trying to deploy. Otherwise continue through deployment
# process.
echo -e "Test dev template notebooks with known data..."
CALI_DIR=/usr/gapps/spot/datasets/lulesh_new
CALI_FILE=${CALI_DIR}/190716-140428166192.cali

# Test dev single jupyter notebook.
./test-hatchet-template-notebooks.sh \
    dev \
    ${CALI_FILE}
ERR=$?
if [ ${ERR} -eq 1 ]; then
    exit 1

# Test dev multi jupyter notebook.
./test-multi-hatchet-template-notebooks.sh \
    dev \
    ${CALI_DIR}
ERR=$?
if [ ${ERR} -eq 1 ]; then
    exit 1
##############################################################################

echo 'DEV      = '$DEV
echo 'LIVE     = '$LIVE
echo 'HATCHET  = '$HATCHET
echo 'CALIPER  = '$CALIPER
echo '-----------------------------------'

cd $LIVE

ls $HATCHET
ls $CALIPER

exit

asdf
sleep 10000
echo 'Now deploying...'

git fetch;
git reset --hard origin/develop;
chmod -R 755 web;
cat web/js/Environment.js

# now copy hatchet to live
cp -r $DEV"hatchet/*" $HATCHET

# now copy caliper to live
cp -r $DEV"caliper/*" $CALIPER

cd $DIR
./setperm.sh

##############################################################################
# Now that spot dev has been pushed to live, test spot live single and multi
# jupyter notebooks with known cali data.
# Terminate deploy_spot.bash script if one of the notebooks fails. Fix bugs if
# necessary.
echo -e "Test live template notebooks with known data..."

# Test live jupyter notebook.
./test-hatchet-template-notebooks.sh \
    live \
    ${CALI_FILE}
ERR=$?
if [ ${ERR} -eq 1 ]; then
    exit 1

# Test live multi jupyter notebook.
./test-multi-hatchet-template-notebooks.sh \
    live \
    ${CALI_DIR}
ERR=$?
if [ ${ERR} -eq 1 ]; then
    exit 1
##############################################################################
