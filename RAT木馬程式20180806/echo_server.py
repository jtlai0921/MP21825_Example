# Echo server program
import socket
from tools import *

def do_something(b):
    return b

HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 50007              # Arbitrary non-privileged port
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(1)
    while True:
        conn, addr = s.accept()
        with conn:
            print('Connected by', addr)
            while True:
                data = conn.recv(1024)
                if not data: break
                print('receive %d bytes from %s' % (len(data), str(addr)))
                hexdump(data)
                data = do_something(data)
                print('send %d bytes to %s' % (len(data), str(addr)))
                hexdump(data)
                conn.sendall(data)
