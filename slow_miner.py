from bisect import bisect_left
from hashlib import sha256 as H
from lib import *
from struct import pack, unpack
import json
import math
import random
import requests
import sys
import time
import urllib2

NODE_URL = "http://6857coin.csail.mit.edu:8080"

def solve_block(b):
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


def add_block(h, contents):
    add_block_request = {"header": h, "block": contents}
    print "Sending block to server..."
    print json.dumps(add_block_request)
    r = requests.post(NODE_URL + "/add", data=json.dumps(add_block_request))
    return r


def rand_nonce(diff):
    """Returns a random int in [0, 2**diff)"""
    return random.randint(0, 2**diff - 1)

if __name__ == "__main__":
    a = [random.randint(0, 2**42) for _ in range(100)]
    main()
    
