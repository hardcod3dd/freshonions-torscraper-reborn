#!/bin/sh
DIR=$( cd "$(dirname "$0")" ; pwd -P )
. $DIR/env.sh
LIST=`mktemp`
LIST2=`mktemp`
TEMP=`mktemp`

# Original v2 source (nzxj65x32vh2fkhk.onion) is defunct.
# Replace the URL below with an active v3 paste/list onion if available.
# $SCRIPTDIR/tor_extract_from_url.sh 'http://<v3-paste-onion>/all' > $LIST

$SCRIPTDIR/purify.sh $LIST > $LIST2
NUMBER=`wc -l $LIST2 | tr -s ' ' | cut -f 1 -d ' '`
echo "Harvested $NUMBER onion links..."
$SCRIPTDIR/push_list.sh $LIST2
rm $LIST $LIST2 $TEMP
