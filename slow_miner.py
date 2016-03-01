import urllib2
import json
from hashlib import sha256 as H
import time
from struct import pack, unpack
import random
import requests
import sys
import math
from bisect import bisect_left

NODE_URL = "http://6857coin.csail.mit.edu:8080"

"""
    This is a bare-bones miner compatible with 857coin, minus the final proof of
    work check. We have left lots of opportunities for optimization. Partial
    credit will be awarded for successfully mining any block that appends to
    a tree rooted at the genesis block. Full credit will be awarded for mining
    a block that adds to the main chan. Note that the faster you solve the proof
    of work, the better your chances are of landing in the main chain.

    Feel free to modify this code in any way, or reimplement it in a different
    language or on specialized hardware.

    Good luck!
"""


def solve_block(b):
    """
    Iterate over random nonce triples until a valid proof of work is found
    for the block

    Expects a block dictionary `b` with difficulty, version, parentid,
    timestamp, and root (a hash of the block data).

    """
    d = b["difficulty"]
    mod2d = 2**d - 1L

    blob = pack_block(b)

    def F(nonce):
        return int(get_hash(blob, nonce), 16) & mod2d

    result = find_3collisions(F, 2**d)
    if result != None:
        b['nonces'] = list(result)
        print b
        return True
    else:
        print "No 3-collisions found"
        return False


def get_hash(blob, nonce):
    return H(blob + pack('>Q', long(nonce)) + '\x00').hexdigest()


def find_3collisions(F, N):
    Na = 2**24
    Nb = 2**28

    print "Building {} table...".format(Na)
    img = [None] * Na
    pr1 = [None] * Na
    pr2 = [None] * Na

    a = random.randint(0, N - 1)
    for i in xrange(Na):
        img[i] = F(a)
        pr1[i] = a

        a += 1

    print "Sorting, setting..."
    img, pr1 = map(list, zip(*sorted(zip(img, pr1))))
    imgset = set(img)

    print "Searching..."
    pairs = 0
    start_time = time.time()

    a = random.randint(0, N - 1)
    for i in xrange(1, Nb):
        b = F(a)
        if b in imgset:
            j = index(img, b)
            if j >= 0 and a != pr1[j]:
                pairs += 1
                if pr2[j] == None:
                    pr2[j] = a
                elif pr2[j] != a:
                    print "\nFOUND COLLISION: {}".format((pr1[j], pr2[j], a))
                    return (pr1[j], pr2[j], a)
        a += 1

        if i & 0xFFFFF == 0:
            print "{}".format(i / 1000000),
            sys.stdout.flush()

    print
    return None


def index(a, x):
    i = bisect_left(a, x)
    if i != len(a) and a[i] == x:
        return i
    return -1


def main():
    """
    Repeatedly request next block parameters from the server, then solve a block
    containing our team name.

    We will construct a block dictionary and pass this around to solving and
    submission functions.
    """
    block_contents = "jfuchs,mmgong,hcg"
    while True:
        #   Next block's parent, version, difficulty
        next_header = get_next()
        #   Construct a block with our name in the contents that appends to the
        #   head of the main chain
        new_block = make_block(next_header, block_contents)
        #   Solve the POW
        print "\nSolving block..."
        print new_block

        if solve_block(new_block):
            #   Send to the server
            # add_block(new_block, block_contents)
            with open("results.py", "a") as f:
                f.write(str(new_block))
                f.write("\n\n")


def get_next():
    """
       Parse JSON of the next block info
           difficulty      uint64
           parentid        HexString
           version         single byte
    """
    return json.loads(urllib2.urlopen(NODE_URL + "/next").read())


def add_block(h, contents):
    """
       Send JSON of solved block to server.
       Note that the header and block contents are separated.
            header:
                difficulty      uint64
                parentid        HexString
                root            HexString
                timestampe      uint64
                version         single byte
            block:          string
    """
    add_block_request = {"header": h, "block": contents}
    print "Sending block to server..."
    print json.dumps(add_block_request)
    r = requests.post(NODE_URL + "/add", data=json.dumps(add_block_request))
    return r


def pack_block(b):
    """Return a binary blob of the info in block b"""
    packed_data = []
    packed_data.extend(b["parentid"].decode('hex'))
    packed_data.extend(b["root"].decode('hex'))
    packed_data.extend(pack('>Q', long(b["difficulty"])))
    packed_data.extend(pack('>Q', long(b["timestamp"])))
    # packed_data.extend(pack('>Q', long(0)))
    # packed_data.append(chr(b["version"]))
    if len(packed_data) != (89 - 8 - 1):
        print "invalid length of packed data"
    return ''.join(packed_data)


def hash_to_hex(data):
    """Returns the hex-encoded hash of a byte string."""
    h = H()
    h.update(data)
    return h.digest().encode('hex')


def make_block(next_info, contents):
    """
    Constructs a block from /next header information `next_info` and sepcified
    contents.
    """
    block = {
        "version": next_info["version"],
        #   for now, root is hash of block contents (team name)
        "root": hash_to_hex(contents),
        "parentid": next_info["parentid"],
        #   nanoseconds since unix epoch
        "timestamp": long((time.time() + 10 * 60 * 60) * 1000 * 1000 * 1000),
        "difficulty": next_info["difficulty"]
    }
    return block


def rand_nonce(diff):
    """
    Returns a random int in [0, 2**diff)
    """
    return random.randint(0, 2**diff - 1)

if __name__ == "__main__":
    a = [random.randint(0, 2**42) for _ in range(100)]

    main()
