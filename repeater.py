from hashlib import sha256 as H
from lib import *
from struct import pack, unpack
import json
import requests
import subprocess
import sys
import time
import urllib2

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
        u'difficulty': 38,
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


if __name__ == "__main__":
    main()
