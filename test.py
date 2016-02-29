from hashlib import sha256
import time
import random
from struct import pack, unpack

s = "cfe09524a097e362b1cdcd71d2f4a740de234a495eb927924eaceed3687ae79220a3e622e673dee9dff570ebaadcbb7c6ec9a49795438028edd1facf5e83e9bf000000000000002a1436b0b238876a00000000000000000000"
blob = s.decode("hex")
blob = blob[:80]
h = lambda n: calc_hash(blob, n)

def calc_hash(blob, nonce):
    inp = blob + pack('>Q', long(nonce)) + '\x00'
    out = sha256(inp).hexdigest()
    return long(out, 16) % (2**36)

if __name__ == "__main__":
    pass
