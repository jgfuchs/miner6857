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
            print "Added successfully ({})".format(hash_block_to_hex(new_header))
        else:
            print "Failed to add: {}, {}".format(r.status_code, r.text)

        print "\n"

if __name__ == "__main__":
    main()
    
