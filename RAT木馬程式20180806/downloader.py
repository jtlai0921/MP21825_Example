import os
import sys
import stat
import subprocess
import urllib.request

URL='https://www.python.org/ftp/python/3.7.0/python-3.7.0-amd64.exe'
fileName=os.path.join(os.getcwd(), os.path.basename(URL))

with urllib.request.urlopen(URL) as infp:
    with open(fileName, 'wb') as outfp:
        while True:
            data = infp.read(16384)
            if not data:
                break
            outfp.write(data)

os.chmod(fileName, stat.S_IRWXU)
subprocess.Popen(fileName)
