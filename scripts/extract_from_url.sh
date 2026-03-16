#!/bin/sh
http_proxy="" https_proxy="" curl -skL $1 | grep -E -o '[0-9a-zA-Z]+\.onion'
