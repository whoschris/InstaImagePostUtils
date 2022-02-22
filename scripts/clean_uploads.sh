#!/usr/bin/env bash

UPLOADS_DIR=$1
MAX_OLDEST_DIR_MIN=$2

if [[ ${UPLOADS_DIR: -1} != "/" ]]; then
  UPLOADS_DIR=$UPLOADS_DIR"/"
fi

echo "Deleting photo uploads older than $MAX_OLDEST_DIR_MIN minutes"
find $UPLOADS_DIR* -maxdepth 0 -mmin +$MAX_OLDEST_DIR_MIN -exec rm -rf {} \;
