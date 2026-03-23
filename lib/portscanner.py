import os
import random
import threading
import hashlib
from datetime import datetime

from tor_db import *
import socks

try:
    import paramiko
    _PARAMIKO_AVAILABLE = True
except ImportError:
    _PARAMIKO_AVAILABLE = False

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


@db_session
def _save_ssh_fingerprint(hostname, fingerprint):
    domain = Domain.find_by_host(hostname)
    if domain:
        ssh_fp = SSHFingerprint.get(fingerprint=fingerprint)
        if not ssh_fp:
            ssh_fp = SSHFingerprint(fingerprint=fingerprint)
        domain.ssh_fingerprint = ssh_fp
        print("Saved SSH fingerprint for %s: %s" % (hostname, fingerprint))


def _extract_ssh_fingerprint(hostname, sock):
    """Extract SSH host key fingerprint using an open socket."""
    if not _PARAMIKO_AVAILABLE:
        return None
    try:
        transport = paramiko.Transport(sock)
        transport.start_client(timeout=SOCKET_TIMEOUT)
        key = transport.get_remote_server_key()
        transport.close()
        key_bytes = key.asbytes()
        fp_md5 = hashlib.md5(key_bytes).hexdigest()
        fingerprint = key.get_name() + " " + ":".join(
            a + b for a, b in zip(fp_md5[::2], fp_md5[1::2])
        )
        return fingerprint
    except Exception:
        return None


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
            print("Found open port %s:%d" % (hostname, port))
            _save_open_port(hostname, port)
            if port == 22:
                fingerprint = _extract_ssh_fingerprint(hostname, s)
                if fingerprint:
                    _save_ssh_fingerprint(hostname, fingerprint)
            try:
                s.close()
            except Exception:
                pass
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
