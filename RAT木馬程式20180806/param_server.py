# PARAM server program
import socket
from tools import *
import param

HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 50007              # Arbitrary non-privileged port
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(1)
    while True:
        conn, addr = s.accept()
        with conn:
            print('Connected by', addr)
            handle = param.PARAM(server=conn)
            while True:
                data = handle.read()
                if not data: break
                print('receive from %s' % (str(addr)))
                print(data)
                print('send back to %s' % (str(addr)))
                handle.write(data)
