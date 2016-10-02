#!/usr/bin/env bash
WWW_DIR=$(pwd)

if [ -d $WWW_DIR/.env ]; then
    echo ''
else
    virtualenv --system-site-packages --python=$(which python2.7) $WWW_DIR/.env
fi

# Prepare environment
source $WWW_DIR/.env/bin/activate
pip install -r $WWW_DIR/requirements.txt

# Exit virtual environment
deactivate
