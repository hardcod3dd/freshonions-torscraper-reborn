#!/bin/sh
DIR=$( cd "$(dirname "$0")" ; pwd -P )
. $DIR/env.sh
curl -L --socks5-hostname $SOCKS_PROXY $1 | grep -E -o '[0-9a-zA-Z]+\.onion'
