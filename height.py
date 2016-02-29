#!/usr/bin/python3
import requests
import sys
import json

if len(sys.argv) != 2:
    print("Usage: {} <block ID>".format(sys.argv[0]))
    sys.exit(1)

i = sys.argv[1]
h = 0

while True:
    r = requests.get("http://6857coin.csail.mit.edu:8080/block/{}".format(i))
    try:
        b = json.loads(r.text)
        h += 1
        i = b["header"]["parentid"]
    except:
        break

print("{}".format(h))
