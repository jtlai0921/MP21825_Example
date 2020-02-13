import sys
import io
import struct

#######################
# common
#######################

def byte_length(n):
    return (n.bit_length() + 7) >> 3

int_size_list = [
        ('B', 1),
        ('H', 2),
        ('L', 4),
        ('Q', 8),
        ]
neg_size_list = [
        ('b', 1),
        ('h', 2),
        ('l', 4),
        ('q', 8),
        ]
float_size_list = [
        ('d', 8),
        ('f', 4),
        ]

def number2tag_size(n):
    n, num_size_list = (n, int_size_list) if n >= 0 else (-n, neg_size_list)
    n_size           = byte_length(n)
    for tag, tag_size in num_size_list:
        if tag_size >= n_size:
            return tag, tag_size
    return None, None

def pack_number(n):
    if not isinstance(n, int):
        return None, None
    n2, num_size_list = (n, int_size_list) if n >= 0 else (-n, neg_size_list)
    n_size           = byte_length(n2)
    for tag, tag_size in num_size_list:
        if tag_size >= n_size:
            return tag, struct.pack('!' + tag, n2)
    return None, None

int_size_map = dict(int_size_list)
neg_size_map = dict(neg_size_list)
num_size_map = dict(int_size_list + neg_size_list + float_size_list)

def unpack_number(tag, n_bytes):
    if tag not in num_size_map:
        return None
    retval_tuple = struct.unpack('!' + tag, n_bytes)
    data = retval_tuple[0] if len(retval_tuple) == 1 else None
    if tag in neg_size_map:
        data = -data
    return data

def pack_float(n):
    if not isinstance(n, float):
        return None, None
    tag = 'd'
    return (tag, struct.pack('!' + tag, n))

def unpack_float(tag, n_bytes):
    if tag not in ['f', 'd']:
        return None
    retval_tuple = struct.unpack('!' + tag, n_bytes)
    data = retval_tuple[0] if len(retval_tuple) == 1 else None
    return data

def pack_bignumber(n):
    tag, n = ('U', n) if n >= 0 else ('u', -n)
    n_bytes = b''
    while n:
        b   = n & 0x7F
        n >>= 7
        b2  = b + (0x80 if n else 0)
        n_bytes += bytes([b2])
    return tag, n_bytes

def unpack_bignumber(tag, n_bytes):
    exp = 0
    n   = 0
    for b in n_bytes:
        n   += (b & 0x7F) << exp
        exp += 7
        if b & 0x80 == 0:
            break
    return n if tag == 'U' else -n if tag == 'u' else None

pack_block_tag = {
        str:   (lambda n: 's'),
        bytes: (lambda n: 'c'),
        int:   (lambda n: ('M' if n >= 0 else 'm'))
        }

pack_block_encoder = {
        str:   (lambda n: n.encode('utf-8')),
        bytes: (lambda n: n),
        int:   (lambda n: ((n).to_bytes(byte_length(n),  'big')) if n >= 0 \
                    else ((-n).to_bytes(byte_length(-n), 'big')))
        }

unpack_block_map = {
        's': lambda n: n.decode('utf-8'),
        'c': lambda n: n,
        'M': lambda n: (int.from_bytes(n, 'big')),
        'm': lambda n: (-int.from_bytes(n, 'big')),
        }

def pack_block(s):
    tag  = pack_block_tag.get(type(s),     (None,lambda n: None,))
    func = pack_block_encoder.get(type(s), (None,lambda n: None,))
    return tag(s), func(s)

def unpack_block(tag, n_bytes):
    func = unpack_block_map.get(tag, lambda n: None)
    return func(n_bytes)


#################
# test programs
#################

import tools

def test_unpack():
    tag, data_bytes = pack_number(-10000)
    tag, size = number2tag_size(-10000)
    print(tag, size)
    print(len(data_bytes))
    tools.hexdump(data_bytes)
    m = unpack_number(tag, data_bytes)
    print(m)

def test_bignumber():
    tag, n_bytes = pack_number(167763901443)
    print(tag, n_bytes)
    print(unpack_number(tag, n_bytes))
    tag, n_bytes = pack_bignumber(167763901443000000000000000000)
    print(tag, n_bytes)
    print(unpack_bignumber(tag, n_bytes))
    tag, n_bytes = pack_number(-167763901443)
    print(tag, n_bytes)
    print(unpack_number(tag, n_bytes))
    tag, n_bytes = pack_bignumber(-167763901443000000000000000000)
    print(tag, n_bytes)
    print(unpack_bignumber(tag, n_bytes))

def test_pack_block():
    data = 'Hello, World! Hello, Python!'
    tag, f = pack_block(data)
    print(tag, f)
    data = unpack_block(tag, f)
    print(data)
    data = b'Hello, World! Hello, Python!'
    tag, f = pack_block(data)
    print(tag, f)
    data = unpack_block(tag, f)
    print(data)
    data = 12341234123413
    print(data)
    tag, f = pack_block(data)
    print(tag, f)
    data = unpack_block(tag, f)
    print(data)
    data = -12341234123413
    print(data)
    tag, f = pack_block(data)
    print(tag, f)
    data = unpack_block(tag, f)
    print(data)

def test_pack_float():
    data = 3.14159265359
    print(data)
    tag, f = pack_float(data)
    print(tag, f)
    data = unpack_float(tag, f)
    print(data)
    data = -3.14159265359
    print(data)
    tag, f = pack_float(data)
    print(tag, f)
    data = unpack_float(tag, f)
    print(data)

if __name__ == '__main__':
    test_pack_float()
