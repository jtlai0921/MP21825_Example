import time
import threading
import logging
logger = logging.getLogger(__name__)

class threadManager:
    def __init__(self):
        self.lock    = threading.Lock()
        self.manager = threading.Thread(target=self.refresh_forever)
        self.threads = []
        self.timeout = 0.01
        self.refresh_interval = 0.1
        self.manager.start()
    def add(self, p):
        self.lock.acquire()
        self.threads.append(p)
        self.lock.release()
    def refresh(self):
        self.lock.acquire()
        self.threads, threads = [], self.threads
        self.lock.release()
        for p in threads:
            p.join(self.timeout)
            if p.is_alive():
                self.add(p)
    def refresh_forever(self):
        while True:
            self.refresh()
            time.sleep(self.refresh_interval)

class myThread(threading.Thread):
    Manager = None
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.__class__.Manager:
            self.__class__.Manager = threadManager()
    def start(self):
        super().start()
        if self.__class__.Manager:
            self.__class__.Manager.add(self)
    def join(self, timeout=None):
        pass



def test_demo():
    import random

    def demo(n):
        for i in range(n):
            print(n, '-', i)
            time.sleep(0.1)

    for i in range(1000):
        n = random.randint(0, 100)
        p = myThread(target=demo, args=(n,))
        p.start()

if __name__ == '__main__':
    test_demo()
