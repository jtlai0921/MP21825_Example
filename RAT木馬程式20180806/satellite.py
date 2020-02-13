import os
import io
import re
import json
import time
import platform
import subprocess
import logging
logger = logging.getLogger(__name__)

def show_satellite():
    URLs = [
            'https://www.cwb.gov.tw/V7/observe/satellite/Sat_T.htm',
            'https://www.cwb.gov.tw/V7/observe/satellite/Sat_W.htm',
            'https://www.cwb.gov.tw/V7/observe/satellite/Sat_EA.htm',
            'https://www.cwb.gov.tw/V7/observe/satellite/Sat_T.htm',
            'https://www.cwb.gov.tw/V7/observe/satellite/Sat_TrueT.htm',
            ]
    try:
        browsers = {
                'Windows': [
                    'C:\\Program Files\\internet explorer\\iexplore.exe',
                    'C:\\Program Files (x86)\\internet explorer\\iexplore.exe',
                    ],
                'Linux': [
                    '/usr/bin/google-chrome',
                    ],
                }
        procs   = []
        browser = None
        for v in browsers.get(platform.system(), []):
            if os.path.exists(v):
                browser = v
                break
        if not browser:
            print('browser not found')
            return False
        for URL in URLs:
            print(URL)
            proc = subprocess.Popen([browser, URL])
            procs.append(proc)
        # for proc in procs:
        #     proc.wait()
        return True
    except Exception as e:
        print('Exception:', str(e))
        return False

if __name__ == '__main__':
    show_satellite()
