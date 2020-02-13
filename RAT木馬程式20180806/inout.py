import io
import os
import time
import platform
import socket
import netdata
import tools
import logging
logger = logging.getLogger(__name__)
from baseio import *
import tmp

class InOutException(Exception):
    pass

class InOutEscape(InOutException):
    pass

class InOutBlockSize(InOutException):
    pass

class InOutUnknownTag(InOutException):
    pass

class InOutUnknownType(InOutException):
    pass

class INOUT_FILE(BaseIO):
    def __init__(self, fileName, tag='c', temp=False):
        logger.debug('create tempfile: %s', fileName)
        self.fileName = fileName
        self.tag      = tag
        self.handle   = None
        self.tempFlag = temp
    def __len__(self):
        if os.path.exists(self.fileName):
            return os.path.getsize(self.fileName)
        return 0
    @classmethod
    def create(self, *args, **kwargs):
        return None
    def read(self, n=0):
        if not self.handle:
            mode        = 'r' if self.tag == 's' else 'rb'
            self.handle = open(self.fileName, mode)
            logger.error('open INOUT_FILE %s for read', self.fileName)
        if not n:
            n = os.path.getsize(self.fileName)
        retval = self.handle.read(n)
        # logger.debug('INOUT_FILE read: %s', retval)
        return retval
    def write(self, d):
        if not self.handle:
            dirname     = os.path.dirname(self.fileName)
            if dirname and not os.path.exists(dirname):
                os.makedirs(dirname)
            logger.error('open INOUT_FILE %s for write', self.fileName)
            self.handle = open(self.fileName, 'wb')
        # logger.debug('INPUT_FILE write: %s %s %s', type(d), type(self.handle), d)
        self.handle.write(d)
    def close(self):
        if self.handle:
            self.handle.close()
            self.handle = None
        return self
    def drop(self):
        if self.tempFlag and self.fileName:
            self.close()
            if os.path.exists(self.fileName):
                logger.debug('remove %s', fileName)
                os.remove(self.fileName)
                self.fileName = None

class INOUT_INT:
    def __init__(self, tag='M'):
        self.tag    = tag
        self.number = 0
    def read(self, n=0):
        return self.number
    def write(self, d):
        length      = len(d)
        incoming    = int.from_bytes(d, 'big')
        self.number = (self.number << length * 8) + incoming
    def close(self):
        return -self.number if self.tag == 'm' else self.number
    def drop(self):
        pass

class INOUT:
    escape_tag       = '\\'
    block_single_tag = '-'
    block_head_tag   = '+'
    block_end_tag    = '.'
    max_block        = 1024 * 1024 * 64
    max_block        = 4096
    send_block       = 4096
    unpack_map = {
            'B': netdata.unpack_number,
            'b': netdata.unpack_number,
            'H': netdata.unpack_number,
            'h': netdata.unpack_number,
            'L': netdata.unpack_number,
            'l': netdata.unpack_number,
            'Q': netdata.unpack_number,
            'q': netdata.unpack_number,
            'd': netdata.unpack_float,
            's': netdata.unpack_block,
            'c': netdata.unpack_block,
            'M': netdata.unpack_block,
            'm': netdata.unpack_block,
            'U': netdata.unpack_bignumber,
            'u': netdata.unpack_bignumber,
            }
    def __init__(self, obj=None, *args, **kwargs):
        self.handle  = CreateIO(obj, *args, **kwargs)
        self.tmp     = tmp.TMP()
    def create_output_handle(self, tag, size):
        if size > self.send_block:
            fileName = self.tmp.get_tempname(subdir='INOUT')
            if tag in ['M', 'm']:
                return INOUT_INT(fileName, tag)
            return INOUT_FILE(fileName, tag, temp=True)
        return MemIO()
    def _read_low_level(self, n):
        retval = self.handle.read(n)
        retval = bytes([i ^ 0xCC for i in retval])
        return retval
    def _write_low_level(self, d):
        d = bytes([i ^ 0xCC for i in d])
        self.handle.write(d)
    def _get_bytes(self):
        result      = b''
        while True:
            b       = self._read_low_level(1)
            if b is None:
                break
            result += b
            if b[0] & 0x80 == 0:
                break
        return result
    def read_tag(self):
        tag = self.handle.read(1)
        if isinstance(tag, bytes):
            tag = tag.decode('utf-8')
        return tag
    def write_tag(self, tag):
        if isinstance(tag, str):
            tag = tag.encode('utf-8')
        self.handle.write(tag)
    def write_escape(self):
        self.write_tag(self.escape_tag)
    def read(self):
        logger.debug('start reading')
        escape      = False
        logger.debug('reading tag')
        tag         = self.read_tag()
        logger.debug('got tag: %s', tag)
        if tag     == self.escape_tag:
            escape  = True
            tag     = self.read_tag()
            logger.debug('got tag: %s', tag)
        if tag not in self.unpack_map:
            raise InOutUnknownTag(tag)
        unpack_func = self.unpack_map[tag]
        size        = netdata.num_size_map.get(tag, -1)
        logger.debug('tag size: %d', size)

        if size > 0:
            n_bytes = self._read_low_level(size)
            logger.debug('read number: %s', str(n_bytes))
            return netdata.unpack_number(tag, n_bytes)
        elif tag in ['U', 'u']:
            n_bytes = self._get_bytes()
            logger.debug('read number: %s', str(nbytes))
            return netdata.unpack_bignumber(tag, n_bytes)

        numlen_tag  = self.read_tag()
        logger.debug('read numlen_tag %s', numlen_tag)
        if numlen_tag not in netdata.num_size_map:
            raise InOutUnknownTag(numlen_tag)
        numlen_size   = netdata.num_size_map.get(numlen_tag)
        numlen_bytes  = self._read_low_level(numlen_size)
        logger.debug('read numlen_bytes %s', str(numlen_bytes))
        size          = netdata.unpack_number(numlen_tag, numlen_bytes)
        logger.debug('read size: %d', size)
        output_handle = self.create_output_handle(tag, size)
        loop_flag     = False
        while True:
            block_tag      = self.read_tag()
            if block_tag   == self.block_end_tag:
                logger.debug('got end tag')
                break
            elif block_tag == self.block_head_tag:
                logger.debug('got head tag')
                loop_flag      = True
                numlen_tag2    = self.read_tag()
                numlen_size2   = netdata.num_size_map.get(numlen_tag2)
                numlen_bytes2  = self._read_low_level(numlen_size2)
                block_size     = netdata.unpack_number(numlen_tag2, numlen_bytes2)
            elif block_tag == self.block_single_tag and not loop_flag:
                logger.debug('got single tag')
                block_size = size
            else:
                raise InOutUnknownTag(block_tag)
            if block_size > self.max_block:
                raise InOutBlockSize(block_size)
            logger.debug('read: %d', block_size)
            b              = self._read_low_level(block_size)
            logger.debug('save to:', str(b))
            output_handle.write(b)
            if not loop_flag:
                logger.debug('got exit single')
                break
        data        = output_handle.close()
        if isinstance(data, bytes):
            data    = unpack_func(tag, data)
        if escape:
            raise InOutEscape(data)
        return data
    def write(self, obj):
        # print('INOUT write:', type(obj), obj)
        n_bytes = None
        if isinstance(obj, int):
            tag, obj_bytes = netdata.pack_number(obj)
            if tag:
                logger.debug('write number tag and value')
                self.write_tag(tag)
                self._write_low_level(obj_bytes)
                return
        if isinstance(obj, float):
            logger.debug('write float tag and value')
            tag, obj_bytes = netdata.pack_float(obj)
            self.write_tag(tag)
            self._write_low_level(obj_bytes)
            return
        if isinstance(obj, (str, bytes, int)):
            logger.debug('build small tag and value')
            tag, obj_bytes = netdata.pack_block(obj)
            input_handle   = MemIO(obj_bytes)
        elif isinstance(obj, INOUT_FILE):
            logger.debug('build INOUT_FILE tag and value')
            tag, obj_bytes = 'c', obj
            input_handle   = obj
        else:
            raise InOutUnknownType(obj)
        logger.debug('start_write')
        size                 = len(obj_bytes)
        size_tag, size_bytes = netdata.pack_number(size)
        if not size_tag:
            size_tag, size_bytes = netdata.pack_bignumber(obj)
            if not size_tag:
                raise ValueError('pack len error: %d' % len(obj_bytes))
        logger.debug('write tag: %s', tag)
        self.write_tag(tag)
        logger.debug('write size tag: %s', size_tag)
        self.write_tag(size_tag)
        logger.debug('write size bytes: %s', str(size_bytes))
        self._write_low_level(size_bytes)
        if size <= self.send_block:
            b = input_handle.read(size)
            logger.debug('write single tag: %s', self.block_single_tag)
            self.write_tag(self.block_single_tag)
            logger.debug('write_data:', str(b))
            self._write_low_level(b)
            logger.debug('return')
            return
        logger.debug('enter while loop')
        while True:
            b = input_handle.read(self.send_block)
            if not b:
                break
            logger.debug('write head tag: %s', self.block_head_tag)
            self.write_tag(self.block_head_tag)
            size_tag2, size_bytes2 = netdata.pack_number(len(b))
            logger.debug('write size2 tag: %s', size_tag2)
            self.write_tag(size_tag2)
            logger.debug('write size2 tag: %s', str(size_tag2))
            self._write_low_level(size_bytes2)
            logger.debug('write data piece')
            self._write_low_level(b)
        logger.debug('write end tag')
        self.write_tag(self.block_end_tag)
        return
    def close(self):
        self.handle.close()

#######################################

def test_socket():
    addr = ('localhost', 50007)
    handle = SocketIO(addr)
    handle.write(b'abcde')
    retval = handle.read(5)
    print(retval)

def test_socket2():
    handle = CreateIO(('localhost', 50007,))
    handle.write(b'12345')
    retval = handle.read(2)
    print(retval)
    retval = handle.read(3)
    print(retval)

def test_memio():
    handle = MemIO('This is a string.')
    retval = handle.read(2)
    print(retval)
    retval = handle.read(10)
    print(retval)
    handle.write('xxxxxxxxxxxx')
    retval = handle.read(20)
    print(retval)

def test_tempio():
    handle = TempIO('tempfile')
    handle.write(b'12345')
    handle.close()
    s = handle.read(5)
    print(s)

def test_inout():
    handle = INOUT(('localhost', 50007,))
    handle.write(5201314)
    handle.write(-12345678900000000000000000000000000000000)
    handle.write('This is a str.')
    handle.write(b'This is a bytes.')
    handle.write(b'This is a bytes!' * 100)
    retval = handle.read()
    print(retval)
    retval = handle.read()
    print(retval)
    retval = handle.read()
    print(retval)
    retval = handle.read()
    print(retval)
    retval = handle.read()
    print(retval)
    handle.close()
    return

def test_inout_int(n):
    tag, d = netdata.pack_block(n)
    ii = INOUT_INT(tag)
    for i in range(0, len(d), 6):
        b = d[i: i+6]
        print(b)
        ii.write(b)
    i2 = ii.close()
    print(n)
    print(i2)

#

def test_unsized():
    handle = CreateIO(('localhost', 50007,))
    print(handle.handle)
    handle.write(b'1234567890')
    print(handle.read(10))
    handle.write(b'1234567890' * 1000)
    print(handle.read(10000))

def test_inout_write_large_data():
    handle = INOUT(('localhost', 50007,))
    handle.write(1234567890)
    handle.write(1234567890000000000000000000000000000000000000)
    handle.write(b'1234' * 100)
    handle.write('1234' * 100)
    handle.write(b'1234' * 100000)
    handle.write('1234' * 100000)
    data = []
    for i in range(6):
        data.append(handle.read())
    print(data[0])
    print(data[1])
    print(len(data[2]), type(data[2]))
    print(len(data[3]), type(data[3]))
    print(len(data[4]), type(data[4]))
    print(len(data[5]), type(data[5]))

def test_tempdir():
    handle = INOUT(('localhost', 50007,))
    print(handle.tmp.get_tempdir)
    handle.tmp.set_tempdir('/tmp/abc')
    print(handle.get_tempdir)
#

def test_token():
    token = '@'
    handle = INOUT(('localhost', 50007,))
    for i in range(100):
        handle.write(i)
        retval = handle.read()
        print('receive:', retval)

def test_inout_int():
    n = 10983410
    test_inout_int(n)
    test_inout_int(-n)
    n = 1098341038471038471710983247019823741098347019238740194372
    test_inout_int(n)
    test_inout_int(-n)

if __name__ == "__main__":
    test_inout_write_large_data()
