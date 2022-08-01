import sys
from threading import Thread


class ThreadEx(Thread):
    """
    ThreadEx extends Thread with the capability to raise Exceptions,
    which occured in the Thread, in the main Thread.
    See for something similar: https://nedbatchelder.com/blog/200711/rethrowing_exceptions_in_python.html
    """

    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, *, daemon=None):
        super().__init__(group=group, target=target, name=name, args=args, kwargs=kwargs, daemon=daemon)
        self.exceptionInfo = None
    
    def join(self, timeout=None):
        super().join(timeout=timeout)
        if self.exceptionInfo:
            raise self.exceptionInfo[1].with_traceback(self.exceptionInfo[2])
        return
    
    def run(self):
        try:
            if self._target:
                self._target(*self._args, **self._kwargs)
        except:
            self.exceptionInfo = sys.exc_info()
        finally:
            # Avoid a refcycle if the thread is running a function with
            # an argument that has a member that points to the thread.
            del self._target, self._args, self._kwargs
