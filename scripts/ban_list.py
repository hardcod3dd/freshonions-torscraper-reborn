#!/usr/bin/python
from pony.orm import *
from datetime import *
from tor_db import *
import sys
from tabulate import tabulate


@db_session
def list_banned():
    domains = Domain.banned()
    data = [[d.index_url(), d.title] for d in domains]
    print((tabulate(data)))


list_banned()
sys.exit(0)
