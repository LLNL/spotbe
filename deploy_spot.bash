#!/bin/bash

if [ $# -ne 1 ]; then
    echo -e ""
    echo -e "USAGE
    $0 <test-status>

DESCRIPTION
    Deploys Spot from dev to live, if and only if the checks on the Jupyter
    notebooks pass for a user that is a member of spotdev (and has
    permissions to deploy Spot). One of the prerequisites of running this
    script is to run the Jupyter notebook checks with a user that does not
    belong to spotdev.  This needs to be done outside of this deployment
    script.

REQUIREMENT
    Have you run both scripts in deployment-scripts/ with a user that is not a
    member of spotdev? If not, please start a new shell with this user, and
    execute both scripts before trying to deploy Spot:

    $ ./deployment-scripts/test-hatchet-template-notebook.sh dev <cali-file>
    $ ./deployment-scripts/test-multi-hatchet-template-notebook.sh dev <path-to-cali-dir>

    If both of these succeed, then issue the following to proceed with the
    deployment:

    $ $0 passed"
    echo -e ""

    exit 1
fi

OTHER_USER_TEST_SUCCESS=$1
echo -e "Dev template notebooks passed with user not in spotdev group"
echo -e "Continuing with deployment..."

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
echo -e "Test live template notebooks with known data and current user..."

# Test live jupyter notebook.
./deployment-scripts/test-hatchet-template-notebook.sh \
    live \
    ${CALI_FILE}
ERR=$?
if [ ${ERR} -eq 1 ]; then
    exit 1
fi

# Test live multi jupyter notebook.
./deployment-scripts/test-multi-hatchet-template-notebook.sh \
    live \
    ${CALI_DIR}
ERR=$?
if [ ${ERR} -eq 1 ]; then
    exit 1
fi
##############################################################################

echo -e ""
echo -e "Now please test live template notebooks with user not in spotdev group
to verify Spot deployment."
echo -e ""
