#!/bin/bash

DIR=/usr/gapps/spot/
DEV=$DIR"dev/"
LIVE=$DIR"live/"
HATCHET=$LIVE"hatchet/"
CALIPER=$LIVE"caliper/"

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

