#!/bin/sh

# example script to delete stale user stubs from the local database

# setup environment
source /usr/local/cog/venv/bin/activate
export LD_LIBRARY_PATH=/opt/esgf/python/lib:$LD_LIBRARY_PATH

# reference the COG installation
export COG_INSTALL_DIR=/usr/local/cog/cog_install

# reference the COG configuration
export COG_CONFIG_DIR=/usr/local/cog/cog_config

python $COG_INSTALL_DIR/manage.py sync_users
