from hashlib import sha256
import time
from struct import pack, unpack

def h(blob, nonce):
    out = sha256(blob + pack('>Q', long(nonce)) + '\x00').hexdigest()
    return int(out, 16) & 0x3ffffffffff


def main():
    s = "cfe09524a097e362b1cdcd71d2f4a740de234a495eb927924eaceed3687ae79220a3e622e673dee9dff570ebaadcbb7c6ec9a49795438028edd1facf5e83e9bf000000000000002a1436b0b238876a00"
    blob = s.decode("hex")

    x = long(1566780545989)

    IT = 2**10

    start = time.time()
    for _ in range(IT):
        x = h(blob, x)
    end = time.time()

    print("end: {}".format(x))
    print("{} ns/iter".format(round((end - start)*(1000**3) / IT)))

    # N = 2**22
    # start = time.time()
    # pre = [0] * N
    # for i in range(N):
    #     pre[i] = h(blob, i)
    # end = time.time()
    #
    # print "allocated & filled {}; took {} s".format(len(pre), end - start)
    #
    # input()


if __name__ == "__main__":
    main()
