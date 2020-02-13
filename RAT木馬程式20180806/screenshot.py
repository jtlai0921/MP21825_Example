import io
import logging
logger = logging.getLogger(__name__)
try:
    import wx
    def screenshot_grab(fileName):
        app = wx.App()  # Need to create an App instance before doing anything
        screen = wx.ScreenDC()
        size = screen.GetSize()
        bmp = wx.Bitmap(size[0], size[1])
        mem = wx.MemoryDC(bmp)
        mem.Blit(0, 0, size[0], size[1], screen, 0, 0)
        del mem  # Release bitmap
        bmp.SaveFile(fileName, wx.BITMAP_TYPE_PNG)
        return fileName
    screenshot_module = 'wx'
    logger.error('screenshot grabber: wxPython')
except:
    try:
        import pyscreenshot as ImageGrab
        def screenshot_grab(fileName=None):
            image = ImageGrab.grab()
            if fileName:
                image.save(fileName)
                return fileName
            else:
                with io.BytesIO() as fp:
                    image.save(fp, 'PNG')
                    fp.seek(0)
                    return fp.read()
        screenshot_module = 'pyscreenshot'
        logger.error('screenshot grabber: pyscreenshot')
    except:
        def screenshot_grab(fileName=None):
            return None
        screenshot_module = None
        logger.error('screenshot grabber: failed')

if __name__ == '__main__':
    image = screenshot_grab('screenshot.png')
