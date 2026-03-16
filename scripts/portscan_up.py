#!/usr/bin/python
from pony.orm import *
from datetime import *
from tor_db import *
import portscanner
import sys


@db_session
def get_domains():
    hostlist = []
    domains = select(d for d in Domain if d.is_up == True and d.portscanned_at == NEVER)
    for domain in domains:
        hostlist.append(domain.host)
    return list(set(hostlist))


p = portscanner.PortScanner(get_domains())
sys.exit(0)
