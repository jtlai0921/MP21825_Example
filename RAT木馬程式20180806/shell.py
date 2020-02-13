import os
import sys
import platform
import subprocess
import shutil
import shlex
import time
import logging
logger = logging.getLogger(__name__)
import baseio
import inout
import tmp
import tools

# https://docs.python.org/3/library/subprocess.html

def exec_shell_command(args, inputData=None, timeout=None):
    shell_flag = False if isinstance(args, (list, tuple)) else True
    kwargs     = {}
    proc       = subprocess.Popen(args, shell=shell_flag,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True)
    try:
        outs, errs = proc.communicate(inputData, timeout)
    except subprocess.TimeoutExpired as e:
        proc.kill()
        outs, errs = proc.communicate()
    return {'stdout': outs, 'stderr': errs}

def get_saveName(source, target=None):
    if not target:
        target = os.getcwd()
    else:
        target = os.path.abspath(target)
    # source
    if os.path.exists(source) and os.path.isdir(source):
        sourcePath = source
        sourceName = None
    else:
        sourcePath = os.path.dirname(source)
        sourceName = os.path.basename(source)
    # target
    if os.path.exists(target) and os.path.isdir(target):
        targetPath = target
        targetName = None
    else:
        targetPath = os.path.dirname(target)
        targetName = os.path.basename(target)
    # merge
    if not targetName:
        targetName = sourceName
        if not targetName:
            raise IsADirectoryError('%s is a dictionary' % target)
    return os.path.join(targetPath, targetName)

def path_split(path):
    result = []
    if path.startswith('\\\\?\\'):
        path = path[4:]
    while True:
        path, tail = os.path.split(path)
        if not tail:
            break
        result.insert(0, tail)
    return result

def save_fileInfo(fileInfo, fileName, tmpFile=False):
    if not isinstance(fileInfo, dict):
        raise TypeError('fileInfo must be dict, not %s' % str(type(fileInfo)))
    if not fileInfo.get('fileContent'):
        raise AttributeError('lose fileContent')
    # file name for output
    if not fileName:
        tmpmgr  = tmp.TMP()
        tempdir = tmpmgr.get_tempdir('SAVED')
        if fileInfo.get('pathList'):
            fileName = os.path.join(tempdir, fileInfo['pathList'][-1])
        elif fileInfo.get('fileName'):
            fileName = os.path.basename(fileInfo['fileName'])
            fileName = os.path.join(tempdir, fileName)
        else:
            fileName = tmpmgr.get_tempname(subdir='SAVED')
    fileName = os.path.abspath(fileName)
    # set file name if target is a directory
    if os.path.exists(fileName):
        if os.path.isdir(fileName):
            if fileInfo.get('pathList'):
                baseName = fileInfo['pathList'][-1]
            elif fileInfo.get('fileName'):
                baseName = os.path.basename(fileInfo['fileName'])
            else:
                baseName = str(time.time())
            fileName = os.path.join(fileName, baseName)
        else:
            raise FileExistsError('%s exists' % fileName)
    # build target directory
    dirName = os.path.dirname(fileName)
    if dirName and not os.path.exists(dirName):
        os.makedirs(dirName)
    # save file
    if isinstance(fileInfo['fileContent'], str):
        with open(fileName, 'w') as fp:
            fp.write(fileInfo['fileContent'])
        return fileName
    elif isinstance(fileInfo['fileContent'], bytes):
        with open(fileName, 'wb') as fp:
            fp.write(fileInfo['fileContent'])
        return fileName
    elif isinstance(fileInfo['fileContent'], inout.INOUT_FILE):
        fileInfo['fileContent'].close()
        if fileInfo['fileContent'].tempFlag:
            logger.error('move file: %s -> %s' % (fileInfo['fileContent'].fileName, fileName))
            try:
                shutil.move(fileInfo['fileContent'].fileName, fileName)
            except Exception as e:
                logger.error('move to %s fails', fileName)
                return None
            fileInfo['fileContent'].fileName = fileName
            fileInfo['fileContent'].tempFlag = False
            return fileName
        else:
            data = fileInfo['fileContent'].read(16384)
            if not data:
                return
            elif isinstance(data, bytes):
                mode = 'wb'
            elif isinstance(data, str):
                mode = 'w'
            else:
                raise TypeError('invalid type: %s' % str(type(data)))
            logger.error('open with mode %s: %s' % (mode, fileName))
            with open(fileName, mode) as fp:
                while data:
                    fp.write(data)
                    data = fileInfo['fileContent'].read(16384)
            return fileName
    else:
        raise TypeError('can\'t save file, type %s' % str(type(fineInfo['fileContent'])))

def get_fileInfo(fileName):
    if isinstance(fileName, list):
        fileName = os.path.join(*fileName)
    fullName = os.path.abspath(fileName)
    result   = {
            'fileName':    fullName,
            'pathList':    path_split(fullName),
            'fileSize':    os.path.getsize(fullName),
            'fileMtime':   os.path.getmtime(fullName),
#             'fileMtime':   int(os.path.getmtime(fullName)),
            'fileContent': inout.INOUT_FILE(fullName),
#             'fileContent': open(fullName, 'rb').read(),
            }
    return result

########################
## Parse commands
########################
def parse_put(argv):
    query = {}
    if len(argv) >= 2:
        query['command']  = 'save'
        query['fileInfo'] = get_fileInfo(argv[1])
        if len(argv) >= 3:
            query['fileName'] = argv[2]
            query['pathList'] = path_split(argv[2])
    return query

def parse_get(argv):
    query = {}
    if len(argv) >= 2:
        query['command']  = 'send'
        query['fileName'] = argv[1]
        query['pathList'] = path_split(argv[1])
    return query

########################
## Parse Table
########################

parse_map = {
        'put':      parse_put,
        'upload':   parse_put,
        'get':      parse_get,
        'download': parse_get,
        }

########################
## Post Processing
########################

def post_get(argv, response):
    result   = {}
    if len(argv) > 1:
        source = argv[1]
        target = argv[2] if len(argv) > 2 else None
        fileName = save_fileInfo(response, target)
        if not fileName:
            saveFile = target if target else os.path.basename(source)
            result['stderr'] = 'save %s error' % (saveFile)
        elif not os.path.exists(fileName):
            result['stderr'] = 'save %s fails' % (fileName)
        elif 'fileSize' not in response:
            result['stderr'] = 'not size of %s' % (fileName)
        elif os.path.getsize(fileName) != response['fileSize']:
            result['stderr'] = 'size wrong %s' % (fileName)
    return result


def post_screenshot(argv, response):
    result   = {}
    target   = argv[1] if len(argv) > 1 else None
    fileName = save_fileInfo(response, target)
    if not fileName:
        saveFile = target if target else os.path.basename(source)
        result['stderr'] = 'save %s error' % (saveFile)
    else:
        tools.show_image(fileName)
    return result

########################
## Post Processing Table
########################

post_map = {
        'get':        post_get,
        'download':   post_get,
        'screenshot': post_screenshot,
        }

########################
## Terminal
########################

import baseio
import param



def terminal(addr):
    handle  = param.PARAM(addr)
    prompt  = 'COMMAND'
    command = 'dir'
    while True:
        command = command.strip().replace('\\', '\\\\')
        if not command:
            continue
        argv = shlex.split(command)
        if argv[0] in ['quit', 'exit']:
            handle.write(command)
            print('Good-bye!')
            break
        elif argv[0] in parse_map:
            send_data = parse_map[argv[0]](argv)
        else:
            send_data = command
        if not send_data:
            continue
        # print('send_data:', send_data)
        handle.write(send_data)
        response   = handle.read()
        if not response:
            continue
        elif argv[0] in post_map:
            result = post_map[argv[0]](argv, response)
        else:
            result = response
        prompt     = result.get('cwd', prompt)
        outs       = result.get('stdout', '')
        errs       = result.get('stderr', '')
        exc        = result.get('exception', '')
        err_str = (errs.read() if isinstance(errs, baseio.BaseIO) else errs)
        exc_str = (exc.read()  if isinstance(exc, baseio.BaseIO)  else exc)
        out_str = (outs.read() if isinstance(outs, baseio.BaseIO) else outs)
        print('\n'.join([x for x in [err_str, exc_str, out_str] if x]))
        print('done!')
        command = input('@' + prompt + '> ')

def test_exec():
    retval = exec_shell_command(['ls', '-al'])
    print(retval)

def test_savefile():
    info1 = {
            'fileName': '/tmp/abc.txt',
            'fileContent': inout.INOUT_FILE('/tmp/abc.txt'),
            }
    info2 = {
            'fileName': '/tmp/def.txt',
            'fileContent': inout.INOUT_FILE('/tmp/def.txt', temp=True),
            }
    info1['fileContent'].write(b'abc')
    info2['fileContent'].write(b'def')
    info1['fileContent'].close()
    info2['fileContent'].close()
    save_fileInfo(info1, '/tmp/abc2.txt')
    save_fileInfo(info2, '/tmp/def2.txt')

if __name__ == "__main__":
    host = 'localhost'
    if len(sys.argv) > 1:
        host = sys.argv[1]
    terminal((host, 50007, ))
    # terminal(('192.168.0.149', 50007, ))
    # test_exec()
    # test_savefile()
    # print(get_fileInfo('/tmp/abc.txt'))
    # show_image('c:\\python36-32\\aaa.png')
    # show_image('/tmp/aaa.png')
