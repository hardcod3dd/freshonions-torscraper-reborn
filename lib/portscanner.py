import os
import random
import threading
from datetime import datetime

from tor_db import *
import socks

TOR_PROXY_HOST = os.environ["TOR_PROXY_HOST"]
TOR_PROXY_PORT = int(os.environ["TOR_PROXY_PORT"])
MAX_TOTAL_CONNECTIONS = 16
SOCKET_TIMEOUT = 10

PORTS = {
    8333: "bitcoin",
    9051: "bitcoin-control",
    9333: "litecoin",
    22556: "dogecoin",
    6697: "irc",
    6667: "irc",
    143: "imap",
    110: "pop3",
    119: "nntp",
    22: "ssh",
    2222: "ssh?",
    23: "telnet",
    25: "smtp",
    80: "http",
    443: "https",
    21: "ftp",
    5900: "vnc",
    27017: "mongodb",
    9200: "elasticsearch",
    3128: "squid-proxy?",
    8080: "proxy?",
    8118: "proxy?",
    8000: "proxy?",
    9878: "richochet",
    666: "hail satan!",
    31337: "eleet",
    1337: "eleet",
    69: "good times",
    6969: "double the fun",
    1234: "patterns rule",
    12345: "patterns rule",
    3306: "MySQL",
    5432: "PostgreSQL",
}


def get_service_name(port):
    return PORTS.get(port)


@db_session
def _init_host(hostname):
    domain = Domain.find_by_host(hostname)
    if not domain:
        return
    domain.portscanned_at = datetime.now()
    domain.open_ports.clear()


@db_session
def _save_open_port(hostname, port):
    domain = Domain.find_by_host(hostname)
    if domain:
        domain.open_ports.create(port=port)


def _scan_host(hostname):
    _init_host(hostname)
    port_list = list(PORTS.keys())
    random.shuffle(port_list)
    for port in port_list:
        try:
            s = socks.socksocket()
            s.settimeout(SOCKET_TIMEOUT)
            s.set_proxy(proxy_type=socks.SOCKS5, addr=TOR_PROXY_HOST, port=TOR_PROXY_PORT)
            s.connect((hostname, port))
            s.close()
            print("Found open port %s:%d" % (hostname, port))
            _save_open_port(hostname, port)
        except Exception:
            pass


class PortScanner:
    def __init__(self, hosts):
        semaphore = threading.Semaphore(MAX_TOTAL_CONNECTIONS)
        threads = []

        def scan(hostname):
            with semaphore:
                _scan_host(hostname)

        for hostname in hosts:
            t = threading.Thread(target=scan, args=(hostname,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()
