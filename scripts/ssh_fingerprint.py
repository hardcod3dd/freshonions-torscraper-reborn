#!/usr/bin/python
import socks
import paramiko
import hashlib
import base64
import sys
import os

if len(sys.argv) != 2:
    print("Usage: %s <ip>" % sys.argv[0])
    quit()

try:
    mySocket = socks.socksocket()
    mySocket.set_proxy(
        proxy_type=socks.SOCKS5,
        addr=os.environ.get("TOR_PROXY_HOST"),
        port=os.environ.get("TOR_PROXY_PORT"),
    )
    mySocket.connect((sys.argv[1], 22))
except:
    print("Error opening socket")
    quit()

try:
    myTransport = paramiko.Transport(mySocket)
    myTransport.start_client()
    sshKey = myTransport.get_remote_server_key()
except paramiko.SSHException:
    print("SSH error")
    quit()

myTransport.close()
mySocket.close()


printableType = sshKey.get_name()
printableKey = base64.encodebytes(sshKey.__str__()).replace("\n", "")
sshFingerprint = hashlib.md5(sshKey.__str__()).hexdigest()
printableFingerprint = ":".join(
    a + b for a, b in zip(sshFingerprint[::2], sshFingerprint[1::2])
)
print((printableType + " " + printableKey))
