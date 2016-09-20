from hashlib import sha256 as H
from struct import pack, unpack

def hash_to_hex(data):
    """Returns the hex-encoded hash of a byte string."""
    h = H()
    h.update(data)
    return h.digest().encode('hex')


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


def add_block(b):
    """Send JSON of solved block to server."""
    r = requests.post(NODE_URL + "/add", data=json.dumps(b))
    return r


def make_block(next_info, contents):
    block = {
        "version": next_info["version"],
        "root": hash_to_hex(contents),
        "parentid": next_info["parentid"],
        # give ourselves 40 minutes
        "timestamp": long((time.time() + 40 * 60) * (1000**3)),
        "difficulty": next_info["difficulty"]
    }
    return block


def get_next():
    """Parse JSON of the next block info"""
    return json.loads(urllib2.urlopen(NODE_URL + "/next").read())

