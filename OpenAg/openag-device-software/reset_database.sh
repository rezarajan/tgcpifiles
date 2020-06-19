#!/bin/bash

RUNTIME_MODE="DEVELOPMENT"
LOG_LEVEL="DEBUG"
echo RUNTIME_MODE: $RUNTIME_MODE
echo LOG_LEVEL:  $LOG_LEVEL

# Get project root
echo "Getting project root..."
PROJECT_ROOT=`pwd`
echo PROJECT_ROOT: $PROJECT_ROOT

# Clearing Database Files
rm -rf $PROJECT_ROOT/data/config/device.txt

# Resetting Database

source $PROJECT_ROOT/venv/bin/activate
bash $PROJECT_ROOT/scripts/database/migrate_database.sh
bash $PROJECT_ROOT/scripts/database/create_project_users.sh
bash $PROJECT_ROOT/scripts/install/collect_static_files.sh


