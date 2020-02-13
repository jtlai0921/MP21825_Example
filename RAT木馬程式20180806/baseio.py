import io
import os
import time
import platform
import socket
import netdata
import tools
import logging
logger = logging.getLogger(__name__)
import collections
import abc

class BaseMeta(abc.ABCMeta):
    def __instancecheck__(cls, instance):
        if hasattr(instance, 'io_obj'):
            retval = super().__instancecheck__(instance.io_obj)
            if retval:
                return True
        return super().__instancecheck__(instance)

##############################
## IO classses
##############################

class BaseIO(metaclass=BaseMeta):
    def __init__(self, obj, *args, **kwargs):
        self.handle = obj
    def __len__(self):
        return 0
    @classmethod
    @abc.abstractmethod
    def create(cls, *args, **kwargs):
        return cls(*args, **kwargs)
    @abc.abstractmethod
    def read(self, n):
        pass
    @abc.abstractmethod
    def write(self, b):
        pass
    @abc.abstractmethod
    def close(self):
        pass
    def cntl(self, *args, **kwargs):
        pass

class FileIO(BaseIO):
    def __init__(self, fp):
        self.handle = fp
    @classmethod
    def create(cls, obj, *args, **kwargs):
        if isinstance(obj, io.IOBase):
            return cls(obj)
        return None
    def read(self, n):
        return self.handle.read(n)  if self.handle else None
    def write(self, b):
        return self.handle.write(b) if self.handle else None
    def close(self):
        if self.handle:
            self.handle.close()
            self.handle = None

class SocketIO(BaseIO):
    def __init__(self, sockfd):
        self.handle = sockfd
    @classmethod
    def create(cls, obj, *args, **kwargs):
        if isinstance(obj, socket.socket):
            return cls(obj)
        if isinstance(obj, tuple) and len(obj) == 2:
            sockfd = socket.socket(*args, **kwargs)
            sockfd.connect(obj)
            return cls(sockfd)
        return None
    def read(self, n):
        if not isinstance(n, int):
            raise TypeError('parameter should be int but \'%s\'' % (str(type(n))))
        b = b''
        while len(b) < n:
            logger.debug("receiving %d", n - len(b))
            d = self.handle.recv(n - len(b))
            if not d:
                break
            b += d
        logger.debug("%s", tools.hexdump(b, silent=True))
        # tools.hexdump(b)
        return b
    def write(self, b):
        d = self.handle.sendall(b)
        # tools.hexdump(b)
        return d
    def close(self):
        self.handle.shutdown(socket.SHUT_RDWR)
        self.handle.close()

class MemIO(BaseIO):
    def __init__(self, s=None):
        self.data = s
        self.head = 0
    def __len__(self):
        return len(self.data) - self.head
    @classmethod
    def create(cls, obj, *args, **kwargs):
        return cls(obj) if isinstance(obj, (str, bytes)) else None
    def read(self, n):
        if self.data is None:
            return None
        retval     = self.data[self.head:self.head + n]
        self.head += n
        return retval
    def write(self, s):
        if self.data is None:
            self.data = b'' if isinstance(s, bytes) else ''
        self.data += s
    def close(self):
        self.head = 0
        return self.data

##############################
## CreateIO and Register
##############################

# CreateIO version 1

def CreateIO_v1(obj=None, *args, **kwargs):
    """obj:
         socket.socket -> SocketIO
         (host, port)  -> SocketIO
         io.IOBase     -> FileIO
         str           -> MemIO
         bytes         -> MemIO
       kwargs:
         fileName      -> FileIO
    """
    # socket
    if isinstance(obj, socket.socket):
        return SocketIO(obj)
    if isinstance(obj, tuple) and len(obj) == 2:
        sockfd = socket.socket(*args, **kwargs)
        sockfd.connect(obj)
        return SocketIO(sockfd)
    # file
    if isinstance(obj, io.IOBase):
        return FileIO(obj)
    # str and bytes
    if isinstance(obj, (str, bytes)):
        return MemIO(obj)
    raise NotImplementedError('type \'%s\' not implemented' % str(type(obj)))

def Register_v1(*args, **kwargs):
    raise NotImplementedError('not implemented in version 1')

# CreateIO version 2

io_class = []

def CreateIO_v2(*args, **kwargs):
    for iocls in reversed(io_class):
        obj = iocls.create(*args, **kwargs)
        if obj is not None:
            return obj
    raise NotImplementedError('CreateIO: error:\nargs: %s\nkwargs: %s' % (str(args), str(kwargs)))

def Register_v2(iocls):
    io_class.append(iocls)

# CreateIO version 3

class CreateIO_v3:
    io_class = []
    def __init__(self, *args, **kwargs):
        self.io_obj = None
        for iocls in reversed(self.io_class):
            obj = iocls.create(*args, **kwargs)
            if obj is not None:
                self.io_obj = obj
                return
        raise NotImplementedError('CreateIO: error:\nargs: %s\nkwargs: %s' % (str(args), str(kwargs)))
    def __getattr__(self, name):
        return getattr(self.io_obj, name)
    def __instancecheck__(self, instance):
        return isinstance(instance, type(self.io_obj))
    def __subclasscheck__(self, instance):
        return isinstance(instance, type(self.io_obj))
    @classmethod
    def register(cls, iocls):
        if issubclass(iocls, BaseIO):
            cls.io_class.append(iocls)
            return
        raise AttributeError('class \'%s\' has no attribute \'create\'' % str(type(iocls)))

def Register_v3(iocls):
    CreateIO_v3.register(iocls)


# CreateIO = CreateIO_v1
# Register = Register_v1
# CreateIO = CreateIO_v2
# Register = Register_v2

class CreateIO(CreateIO_v3):
    pass

Register = Register_v3

# default IO classes

Register(MemIO)
Register(SocketIO)
Register(FileIO)

##############################
## Other tools
##############################

def is_binary(handle):
    if type(handle) in [
            socket.socket,
            io.BytesIO,
            io.BufferedReader,
            io.BufferedWriter,
            io.BufferedRandom,
            io.BufferedRWPair, ]:
        return True
    return False
def is_text(handle):
    if type(handle) in [io.StringIO, io.TextIOWrapper]:
        return True
    return False

##############################
## Testing
##############################

def test_socketio():
    addr = ('localhost', 50007)
    handle = CreateIO(addr)
    handle.write(b'12345')
    print(handle.read(5))
    # should be False
    print(isinstance(handle, MemIO))
    # should be True
    print(isinstance(handle, SocketIO))
    # should be True
    print(isinstance(handle, FileIO))
    # should be False
    print(isinstance(handle, BaseIO))

if __name__ == '__main__':
    test_socketio()
