#!/bin/sh
export PATH=$PATH:/bin/:/sbin/:/usr/bin/:/usr/sbin:/usr/local/bin
DIR=$( cd "$(dirname "$0")" ; pwd -P )
. $DIR/../scripts/env.sh

# Run Elasticsearch migration on startup (safe to run multiple times)
python $SCRIPTDIR/elasticsearch_migrate.py

while true
do
  $SCRIPTDIR/scrape.sh
  sleep 900
done
