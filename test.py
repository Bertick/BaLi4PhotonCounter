import time
import multiprocessing as mp
import threading as th


# def worker():
#     time.sleep(10)
#
#
# def proc_killer(pp: mp.Process):
#     pp.terminate()

def timeout_handle():
    raise TimeoutError()


class MyProc(mp.Process):
    def __init__(self, secs):
        super(MyProc, self).__init__(name='The finder outer')

        self._timeout = secs
        self._control_thread = None

    def _new_ctrl_thread(self):
        return th.Timer(self._timeout, function=timeout_handle)

    def run(self):
        # start the timeout control thread
        if self._control_thread is None:
            self._control_thread = self._new_ctrl_thread()
        self._control_thread.start()
        # exec the problematic task
        try:
            time.sleep(10)
        except TimeoutError:
            print(f'{time.ctime()}\tAn exception occurred!')
        else:
            # if the function returned correctly stop the timer
            self._control_thread.cancel()
            self._control_thread.join()
            self._control_thread = None

if __name__ == '__main__':
    # proc = mp.Process(name='The Finder-Outer', target=worker)
    # timouter = th.Timer(interval=4, function=proc_killer, kwargs={'pp': proc})

    proc = MyProc(2)

    print(time.ctime())
    proc.start()

    proc.join()
    print(time.ctime())
