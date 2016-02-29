from hashlib import sha256
import time
import random
from struct import pack, unpack

s = "d9c83f66419bf169a781c68e7a63d079cb5f855436789ec2a7a8586904d3e18a20a3e622e673dee9dff570ebaadcbb7c6ec9a49795438028edd1facf5e83e9bf000000000000002c14374fcb26781500000000000000000000"
blob = s.decode("hex")
blob = blob[:80]
h = lambda n: calc_hash(blob, n)

def calc_hash(blob, nonce):
    inp = blob + pack('>Q', long(nonce)) + '\x00'
    out = sha256(inp).hexdigest()
    return long(out, 16) % (2**32)

if __name__ == "__main__":
    pass
