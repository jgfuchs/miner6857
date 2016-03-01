import urllib2
import json
from hashlib import sha256 as H
import time
from struct import pack, unpack
import requests
import sys
import subprocess

NODE_URL = "http://6857coin.csail.mit.edu:8080"


def calc_nonces(b):
    hexdata = pack_block(b).encode('hex')
    tries = 0
    while True:
        tries += 1
        pipe = subprocess.Popen(['./target/release/miner', hexdata],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = pipe.communicate()
        nonces = [int(n) for n in out.split()]
        if len(nonces) == 3:
            print "solved ({}).".format(tries),
            sys.stdout.flush()
            return nonces


def main():
    block_contents = "jfuchs,mmgong,hcg"

    header0 = {
        u'timestamp': 0,
        u'difficulty': 32,
        u'version': 0,
        u'parentid': u'169740d5c4711f3cbbde6b9bfbbe8b3d236879d849d1c137660fce9e7884cae7',  # genesis
        u'nonces': [0, 0, 0],
        u'root': hash_to_hex(block_contents)
    }

    header = dict(header0)

    resets = 0
    count = 0

    while True:
        print "{}|{}: New block... ".format(resets, count),
        sys.stdout.flush()

        header['timestamp'] = long(time.time() * (1000**3))
        header['nonces'] = calc_nonces(header)

        block = {"header": header, "block": block_contents}
        r = add_block(block)
        lastid = hash_block_to_hex(header)

        if r.status_code == 200:
            print "Added successfully ({})".format(lastid)
            header['parentid'] = hash_block_to_hex(header)
            count += 1
        else:
            print "Server error: {}, {}\n".format(r.status_code, r.text)
            header = dict(header0)
            resets += 1


def add_block(b):
    """Send JSON of solved block to server."""
    r = requests.post(NODE_URL + "/add", data=json.dumps(b))
    return r


def pack_block(b):
    """Return a binary blob of the info in block b"""
    packed_data = []
    packed_data.extend(b["parentid"].decode('hex'))
    packed_data.extend(b["root"].decode('hex'))
    packed_data.extend(pack('>Q', long(b["difficulty"])))
    packed_data.extend(pack('>Q', long(b["timestamp"])))
    packed_data.extend(pack('>Q', long(0)))
    packed_data.append(chr(b["version"]))
    if len(packed_data) != 89:
        print "invalid length of packed data"
    return ''.join(packed_data)


def hash_block_to_hex(b):
    """Computes the hex-encoded hash of a block header."""
    packed_data = []
    packed_data.extend(b["parentid"].decode('hex'))
    packed_data.extend(b["root"].decode('hex'))
    packed_data.extend(pack('>Q', long(b["difficulty"])))
    packed_data.extend(pack('>Q', long(b["timestamp"])))
    for n in b["nonces"]:
        packed_data.extend(pack('>Q', long(n)))
    packed_data.append(chr(b["version"]))
    if len(packed_data) != 105:
        print "invalid length of packed data"
    h = H()
    h.update(''.join(packed_data))
    b["hash"] = h.digest().encode('hex')
    return b["hash"]


def hash_to_hex(data):
    """Returns the hex-encoded hash of a byte string."""
    h = H()
    h.update(data)
    return h.digest().encode('hex')


if __name__ == "__main__":
    main()
