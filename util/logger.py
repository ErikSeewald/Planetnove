from datetime import datetime
from collections import deque
import inspect


class Logger:
    """
    Console logger with debug information that remembers logs in a deque.
    """

    logs: deque

    def __init__(self):
        self.logs = deque()

    def log(self, message: str):
        """
        Logs the given message to the console along with additional debug information.
        The log is also saved in a deque.
        """

        now = datetime.now()
        frame = inspect.currentframe().f_back
        caller = frame.f_code.co_name

        log = f"{now.hour}:{now.minute}:{now.second} - {caller} (line {frame.f_lineno}): {message}"
        self.logs.appendleft(log)
        print(log, flush=True)
