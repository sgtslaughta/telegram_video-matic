import tempfile, os
from app.hashing import quick_hash


def test_quick_hash_stable_and_distinct():
    def write(data):
        fd, p = tempfile.mkstemp(); os.write(fd, data); os.close(fd); return p
    a = write(b"x" * (3 * 1024 * 1024))   # 3MB of x
    b = write(b"x" * (3 * 1024 * 1024))   # identical
    c = write(b"x" * (3 * 1024 * 1024 - 1))  # different size
    try:
        assert quick_hash(a) == quick_hash(b)      # same content -> same hash
        assert quick_hash(a) != quick_hash(c)      # size differs -> differs
        assert quick_hash(a) is not None
        assert quick_hash("/no/such/file") is None
    finally:
        for p in (a, b, c): os.unlink(p)


def test_quick_hash_small_file():
    fd, p = tempfile.mkstemp(); os.write(fd, b"hello"); os.close(fd)
    try:
        assert quick_hash(p) == quick_hash(p)
    finally:
        os.unlink(p)
