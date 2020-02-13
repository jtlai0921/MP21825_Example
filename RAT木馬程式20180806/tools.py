import logging
logger = logging.getLogger(__name__)

def hexdump(b, step=16, sep=4, decimal=False, silent=False):
    output = ''
    for i in range(0, len(b), step):
        sub = b[i: i + step]
        output  = '%08x ' % i
        output += '%08d ' % i if decimal else ''
        output += '| '
        stage2  = ' '.join(['%02X' % c for c in sub])
        stage2 += '   ' * (step - len(sub))
        output += ' '.join([stage2[j: j + sep * 3] for j in range(0, len(stage2), sep * 3)])
        output += ' '
        output += '| '
        output += ''.join([chr(c) if 0x20 <= c < 0x7F else '.' for c in sub])
        if not silent:
            print(output)
    return output

def hexdump2(b, step=16, sep=8):
    offset = 0
    if isinstance(b, bytes):
        pass
    elif isinstance(b, str):
        b = b.encode(encoding)
    else:
        raise NotImplememtedError('hexdump(\'%s\') is not implemented' % str(type(b)))
    for i in range(0, len(b), step):
        b_substr     = b[i:i+step]
        b_substr_len = len(b_substr)
        # output = '%08x  ' % offset
        output = '%08d  ' % (offset)
        for j in range(step):
            output += '%02X ' % b_substr[j] if j < b_substr_len else '   '
            output += ' ' if (j + 1) % sep == 0 else ''
        for c in b_substr:
            output += chr(c) if 0x20 <= c < 0x7F else '.'
        print(output)
        offset += step
    
# import matplotlib.pyplot as plt
# from PIL import Image
# def show_image(fileName, title='PIL image shower'):
#     img=Image.open(fileName)
#     plt.figure(title)
#     plt.imshow(img)
#     plt.show()
# logger.error('show_image: Pillow')
#
#     logger.error('import PIL failed')

import os
import platform
import subprocess
def show_image(fileName, title=''):
    viewers = {
            'Windows': [
                'C:\\Windows\\System32\\mspaint.exe',
                'C:\\Program Files\\internet explorer\\iexplore.exe',
                'C:\\Program Files (x86)\\internet explorer\\iexplore.exe',
                ],
            'Linux': [
                '/usr/bin/google-chrome',
                ],
            }
    for viewer in viewers.get(platform.system(), []):
        if os.path.exists(viewer):
            proc = subprocess.Popen([viewer, fileName])
            proc.wait()
            break
# logger.error('show_image: browser')


if __name__ == '__main__':
    message = b'Hello, World!\nHello, Python!'
    hexdump(message)
