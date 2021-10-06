#!/bin/bash

# don't deploy hatchet or caliper.

# Deploy FE
cp -r /usr/global/web-pages/lc/www/spot/dcvis/* /usr/global/web-pages/lc/www/spot2/

# Deploy BE
cp /usr/gapps/spot/dev/*.py /usr/gapps/spot/live/

# set permissions
sp

