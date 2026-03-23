#!/bin/sh
export PATH=$PATH:/bin/:/sbin/:/usr/bin/:/usr/sbin:/usr/local/bin
DIR=$( cd "$(dirname "$0")" ; pwd -P )
. $DIR/../scripts/env.sh

# Run Elasticsearch migration on startup (safe to run multiple times)
python $SCRIPTDIR/elasticsearch_migrate.py

# Portscan every 6 hours in background
(while true; do $SCRIPTDIR/portscan_up.sh; sleep 21600; done) &

# SSH fingerprints twice a day in background
(while true; do $SCRIPTDIR/update_fingerprints.sh; sleep 43200; done) &

# Harvest new onions every 6 hours in background
(while true; do $SCRIPTDIR/harvest.sh; sleep 21600; done) &

while true
do
  $SCRIPTDIR/scrape.sh
  sleep 60
done
