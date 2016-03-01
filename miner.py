import urllib2
import json
from hashlib import sha256 as H
import time
from struct import pack, unpack
import requests
import sys
import subprocess

NODE_URL = "http://6857coin.csail.mit.edu:8080"

debug_log = open("debug.log", "w")


def calc_nonces(b):
    hexdata = pack_block(b).encode("hex")
    tries = 0
    while True:
        tries += 1
        pipe = subprocess.Popen(["./target/release/miner", hexdata],
                                stdout=subprocess.PIPE, stderr=debug_log)
        out, err = pipe.communicate()
        nonces = [int(n) for n in out.split()]
        if len(nonces) == 3:
            print "Solved!!  ({} tries)".format(tries)
            sys.stdout.flush()
            return nonces


def main():
    block_contents = "jfuchs,mmgong,hcg"
    while True:
        next_header = get_next()
        new_header = make_block(next_header, block_contents)

        print "Solving block:"
        print new_header

        new_header["nonces"] = calc_nonces(new_header)

        block = {"header": new_header, "block": block_contents}
        r = add_block(block)

        if r.status_code == 200:
            print "Added successfully ({})".format(hash_block_to_hex(header))
        else:
            print "Failed to add: {}, {}".format(r.status_code, r.text)

        print "\n"


def get_next():
    """Parse JSON of the next block info"""
    return json.loads(urllib2.urlopen(NODE_URL + "/next").read())


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
        raise Exception("invalid length of packed data")
    return ''.join(packed_data)


def make_block(next_info, contents):
    """
    Constructs a block from /next header information `next_info` and sepcified
    contents.
    """
    block = {
        "version": next_info["version"],
        "root": hash_to_hex(contents),
        "parentid": next_info["parentid"],
        # give ourselves 40 minutes
        "timestamp": long((time.time() + 40 * 60) * (1000**3)),
        "difficulty": next_info["difficulty"]
    }
    return block

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
