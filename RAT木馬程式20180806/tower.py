import socket
import logging
logger = logging.getLogger(__name__)
import baseio
import tools

SERVER_MODE        = True
CLIENT_MODE        = False

#############################
## configure
#############################

CONFIG_BLOCKSIZE   = dict(code=0x01, size=1)

#############################
## communication procedure
#############################

PROCODE            = lambda n: ('[' + n + ']')
IS_PROCODE         = lambda n: (n.startswith('[') and n.endswith(']'))

SESSION_CONFIG     = PROCODE('%')
SESSION_MESSAGE    = PROCODE('#')
SESSION_CHECK      = PROCODE('?')
SESSION_ROGER      = PROCODE('!')
SESSION_OVER       = PROCODE('@')

SESSION_BLOCKSIZE  = 16384
SESSION_MAXBLOCK   = 1 << 20
PROCODE_LENGTH     = len(SESSION_MESSAGE)

if SESSION_BLOCKSIZE > SESSION_MAXBLOCK:
    # you can't set SESSION_BLOCKSIZE larger then 2^20 = 1MB
    raise ValueError('Invalid size of BLOCKSIZE: %d', SESSION_BLOCKSIZE)

#############################
## Exceptions
#############################

class TowerException(Exception):
    pass

class TowerWaitToken(TowerException):
    pass

class TowerNoToken(TowerException):
    pass

class TowerHasToken(TowerException):
    pass

class TowerInvalidCode(TowerException):
    pass

#############################
## class
#############################

class IOBuffer:
    def __init__(self):
        self.buffer = []
        self.length = 0
    def __len__(self):
        return self.length
    def append(self, s):
        self.buffer.append(s)
        self.length += len(s)
    def pop(self):
        if not self.buffer:
            return None
        s = self.buffer.pop(0)
        self.length -= len(s)
        return s
    def read(self, n):
        result = []
        size   = 0
        while self.buffer:
            l = len(self.buffer[0])
            if size + l > n:
                break
            s = self.pop()
            result.append(s)
            size += len(s)
        if size < n and self.buffer:
            l = n - size
            s, self.buffer[0] = self.buffer[0][:l], self.buffer[0][l:]
            self.length -= l
            result.append(s)
            size += l
        return b''.join(result)

class Tower_v1(baseio.SocketIO):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bufsize_len = 3
        self.read_buffer = IOBuffer()
    def read_procode(self):
        retval = super().read(PROCODE_LENGTH).decode('utf-8')
        if not IS_PROCODE(retval):
            raise TowerInvalidCode('invalid label: %s' % str(retval))
        return retval
    def write_procode(self, procode):
        super().write(procode.encode('utf-8'))
    def read_bufsize(self):
        b = super().read(self.bufsize_len)
        return int.from_bytes(b, 'big')
    def write_bufsize(self, n):
        b = n.to_bytes(self.bufsize_len,  'big')
        super().write(b)
    def read(self, n):
        while len(self.read_buffer) < n:
            procode = self.read_procode()
            if procode == SESSION_MESSAGE:
                msgsize = self.read_bufsize()
                message = super().read(msgsize)
                self.read_buffer.append(message)
            else:
                raise TowerInvalidCode(procode)
        result = self.read_buffer.read(n)
        if len(result) == n:
            return result
        raise Exception('size unmatched %d %d' % (n, len(result)))
    def write(self, b):
        self.write_procode(SESSION_MESSAGE)
        self.write_bufsize(len(b))
        super().write(b)
    def close(self):
        return super().close()

class Tower(baseio.SocketIO):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bufsize_len = 3
        self.read_buffer = IOBuffer()
        self.server_mode = False
        self.token       = True
    def read_procode(self):
        retval = super().read(PROCODE_LENGTH)
        if not retval:
            return None
        retval = retval.decode('utf-8')
        if not IS_PROCODE(retval):
            raise TowerInvalidCode('Invalid code: \'%s\'' % str(retval))
        return retval
    def write_procode(self, procode):
        super().write(procode.encode('utf-8'))
    def read_bufsize(self):
        b = super().read(self.bufsize_len)
        return int.from_bytes(b, 'big')
    def write_bufsize(self, n):
        b = n.to_bytes(self.bufsize_len,  'big')
        super().write(b)
    def read_session(self):
        procode = self.read_procode()
        if not procode:
            message = None
        elif procode == SESSION_OVER:
            # print('read SESSION_OVER')
            message = None
        elif procode == SESSION_MESSAGE:
            msgsize = self.read_bufsize()
            message = super().read(msgsize)
            # print('read_session SESSION_MESSAGE:', message)
        else:
            raise TowerInvalidCode(procode)
        return procode, message
    def read(self, n):
        send_token_flag = False
        if self.token:
            self.write_procode(SESSION_OVER)
            self.token = False
            send_token_flag = True
        while not self.token and len(self.read_buffer) < n:
            procode, message = self.read_session()
            if not procode:
                return None
            elif procode == SESSION_OVER:
                # print('read SESSION_OVER')
                self.token = True
                if send_token_flag:
                    return None
            elif procode == SESSION_MESSAGE:
                # print('read SESSION_MESSAGE:', message)
                self.read_buffer.append(message)
                send_token_flag = False
        result = self.read_buffer.read(n)
        if len(result) == n:
            return result
        raise Exception('size unmatched %d %d' % (n, len(result)))
    def write(self, b):
        while not self.token:
            # raise Exception('Try to write without token')
            procode, message = self.read_session()
            if procode == SESSION_OVER:
                self.token = True
            elif procode == SESSION_MESSAGE:
                self.read_buffer.append(message)
        # print('write SESSION_MESSAGE:', b)
        self.write_procode(SESSION_MESSAGE)
        self.write_bufsize(len(b))
        super().write(b)
    def close(self):
        return super().close()

class TowerServer(Tower):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.server_mode = True
        self.token       = False
    @classmethod
    def create(cls, *args, **kwargs):
        if isinstance(kwargs.get('server'), socket.socket):
            print('tower server mode')
            return cls(kwargs['server'])
        return None

baseio.Register(Tower)
baseio.Register(TowerServer)


